import os
import json
import re
import requests
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from supabase import create_client
from langchain_groq import ChatGroq

# --- الإعدادات ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# جلب المفاتيح وتنظيفها
SERPER_KEYS_RAW = os.environ.get("SERPER_KEYS") or os.environ.get("SERPER_API_KEY") or ""
SERPER_KEYS = [k.strip().replace('"', '') for k in SERPER_KEYS_RAW.split(',') if k.strip()]

print(f"--- Hunter V31 (The Miser 💰) --- Keys: {len(SERPER_KEYS)}")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    llm = ChatGroq(model="llama3-70b-8192", temperature=0.3, api_key=GROQ_API_KEY)
    print("✅ System Armed!")
except:
    supabase = None
    llm = None

app = FastAPI()

class HuntRequest(BaseModel):
    intent_sentence: str
    city: str
    time_filter: str = "qdr:m"
    user_id: str = "admin"

# --- إدارة المفاتيح ---
key_index = 0
def get_active_key():
    global key_index
    if not SERPER_KEYS: return None
    k = SERPER_KEYS[key_index]
    key_index = (key_index + 1) % len(SERPER_KEYS)
    return k

# --- تقييم الجودة ---
def judge_lead(text):
    text = text.lower()
    if any(x in text for x in ["مطلوب", "شراء", "كاش", "buy", "urgent", "محتاج"]): return "Excellent 🔥"
    if any(x in text for x in ["سعر", "تفاصيل", "price", "details"]): return "Very Good ⭐"
    if any(x in text for x in ["للبيع", "sale", "offer"]): return "Competitor ❌"
    return "Good ✅"

# --- الحفظ ---
def save_lead(phone, email, keyword, link, quality, user_id):
    if quality == "Competitor ❌": return False # وفر مساحة في الداتابيس
    
    data = {"source": f"Hunter: {keyword}", "status": "NEW", "notes": f"Link: {link}", "quality": quality, "user_id": user_id}
    saved = False
    
    if phone:
        data["phone_number"] = phone
        if email: data["email"] = email
        try:
            supabase.table("leads").upsert(data, on_conflict="phone_number").execute()
            print(f"   ✅ SAVED: {phone} ({quality})")
            saved = True
        except: pass
    return saved

# --- المحرك الاقتصادي (The Miser Engine) ---
def run_hydra_process(intent: str, main_city: str, time_filter: str, user_id: str):
    if not SERPER_KEYS: 
        print("❌ NO KEYS")
        return

    # 1. تقسيم المناطق (عشان نجيب كمية)
    if "القاهرة" in main_city:
        sub_cities = ["التجمع", "المعادي", "مدينة نصر", "مصر الجديدة", "الزمالك"]
    elif "الجيزة" in main_city:
        sub_cities = ["أكتوبر", "الشيخ زايد", "الهرم", "فيصل"]
    else:
        sub_cities = [main_city]
    
    print(f"🌍 Targeting: {sub_cities}")
    total_found = 0

    for area in sub_cities:
        # 2. دمج المواقع (لتوفير التوكنز)
        # بدل 3 استعلامات، خليناهم واحد بس مجمع
        # (يا جوجل هاتلي من فيسبوك أو انستجرام أو أوليكس في نفس الوقت)
        search_query = f'(site:facebook.com OR site:instagram.com OR site:olx.com.eg) "{intent}" "{area}" "010"'
        
        # 3. حلقة التكرار الذكية (Smart Loop)
        # هنطلب 100 نتيجة في الصفحة الواحدة (أقصى حاجة بـ 1 توكن)
        for start_page in range(0, 200, 100): # 0, 100 (صفحتين بس كفاية)
            
            api_key = get_active_key()
            if not api_key: break
            
            # إعداد الطلب الاقتصادي
            payload = json.dumps({
                "q": search_query,
                "num": 100,      # هات 100 مرة واحدة (نفس السعر)
                "start": start_page,
                "tbs": time_filter,
                "gl": "eg",
                "hl": "ar"
            })
            
            headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
            
            try:
                print(f"🚀 Scanning {area} (Offset {start_page})...")
                response = requests.post("https://google.serper.dev/search", headers=headers, data=payload)
                results = response.json().get("organic", [])
                
                # 4. صمام الأمان (Stop Loss)
                # لو الصفحة دي فاضية، أو فيها أقل من 5 نتايج، وقف بحث في المنطقة دي فوراً
                # ومتصرفش توكن على الصفحة اللي بعدها
                if not results or len(results) < 3:
                    print(f"   ⚠️ Low results ({len(results)}), skipping next pages to save tokens.")
                    break 

                print(f"   -> Found {len(results)} raw items.")

                for res in results:
                    snippet = str(res.get('title', '')) + " " + str(res.get('snippet', ''))
                    quality = judge_lead(snippet)
                    
                    phones = re.findall(r'(01[0125][0-9 \-]{8,15})', snippet)
                    for raw in phones:
                        clean = raw.replace(" ", "").replace("-", "")
                        if len(clean) == 11:
                            if save_lead(clean, None, intent, res.get('link'), quality, user_id):
                                total_found += 1
                                
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
                break # لو حصل خطأ، وقف عشان منحرقش على الفاضي

    print(f"🏁 Operation Finished. Total Fresh Leads: {total_found}")

# --- Endpoints ---
@app.post("/start_hunt")
async def start_hunt(req: HuntRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_hydra_process, req.intent_sentence, req.city, req.time_filter, req.user_id)
    return {"status": "Started"}

@app.get("/")
def home(): return {"status": "Brain V31 Online"}

@app.post("/analyze_intent")
async def analyze_intent(req: ChatRequest): return {"action": "PROCEED", "intent": "INTERESTED"}

@app.post("/chat")
async def chat(req: ChatRequest):
    return {"response": "اهلا"}
    
