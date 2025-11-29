import os
import json
import re
import requests
import time
import streamlit as st
from langchain_groq import ChatGroq

# --- الإعدادات ---
try:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or st.secrets["GROQ_API_KEY"]
    # جلب مفاتيح Serper المتعددة
    SERPER_KEYS_RAW = os.environ.get("SERPER_KEYS") or st.secrets.get("SERPER_KEYS") or ""
    SERPER_KEYS = [k.strip().replace('"', '') for k in SERPER_KEYS_RAW.split(',') if k.strip()]
    
    llm = ChatGroq(model="llama3-70b-8192", temperature=0.3, api_key=GROQ_API_KEY)
except:
    llm = None
    SERPER_KEYS = []

# --- إدارة المفاتيح (Rotation) ---
key_index = 0
def get_active_key():
    global key_index
    if not SERPER_KEYS: return None
    k = SERPER_KEYS[key_index]
    key_index = (key_index + 1) % len(SERPER_KEYS)
    return k

# --- 1. المترجم العكسي (لغة الزبون) ---
def reverse_engineer_intent(user_sentence):
    if "مطلوب" in user_sentence or "أبحث" in user_sentence: return [user_sentence]
    prompt = f"""حول جملة البائع: "{user_sentence}" إلى 3 جمل يكتبها الزبون للبحث عنه. 
    مثال: "أنا سباك" -> "مطلوب سباك, عندي تسريب". الرد قائمة بفاصلة فقط."""
    try:
        res = llm.invoke(prompt).content
        return [k.strip() for k in res.split(',') if k.strip()]
    except: return [user_sentence]

# --- 2. تقييم الجودة ---
def judge_lead(text):
    text = text.lower()
    if any(x in text for x in ["مطلوب", "شراء", "كاش", "urgent", "محتاج"]): return "Excellent 🔥"
    if any(x in text for x in ["سعر", "تفاصيل", "price"]): return "Very Good ⭐"
    if any(x in text for x in ["للبيع", "sale", "offer"]): return "Competitor ❌"
    return "Good ✅"

# --- 3. المحرك الرئيسي (The Vacuum) ---
def run_hunter(intent, city, time_filter, user_id, db_client):
    if not SERPER_KEYS or not db_client: return 0
    
    targets = reverse_engineer_intent(intent)
    areas = [city] # يمكن توسيعها بتقسيم المناطق
    if "القاهرة" in city: areas = ["التجمع", "المعادي", "مدينة نصر", "وسط البلد"]
    
    total = 0
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    steps = len(targets) * len(areas)
    current_step = 0
    
    for t in targets:
        for area in areas:
            queries = [
                f'site:facebook.com "{t}" "{area}" "010"',
                f'site:olx.com.eg "{t}" "{area}" "010"',
                f'"{t}" "{area}" "010"'
            ]
            
            for q in queries:
                api_key = get_active_key()
                if not api_key: break
                
                # طلب 100 نتيجة (توفير توكن)
                payload = json.dumps({"q": q, "num": 100, "tbs": time_filter, "gl": "eg", "hl": "ar"})
                headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
                
                try:
                    status_text.text(f"🕵️‍♂️ بحث عن: {t} في {area}...")
                    response = requests.post("https://google.serper.dev/search", headers=headers, data=payload)
                    results = response.json().get("organic", [])
                    
                    for res in results:
                        snippet = str(res.get('title')) + " " + str(res.get('snippet'))
                        quality = judge_lead(snippet)
                        if quality == "Competitor ❌": continue

                        phones = re.findall(r'(01[0125][0-9 \-]{8,15})', snippet)
                        for raw in phones:
                            clean = raw.replace(" ", "").replace("-", "")
                            if len(clean) == 11:
                                try:
                                    db_client.table("leads").upsert({
                                        "phone_number": clean,
                                        "source": f"Hunter: {t}",
                                        "status": "NEW",
                                        "notes": f"Link: {res.get('link')}",
                                        "quality": quality,
                                        "user_id": user_id
                                    }, on_conflict="phone_number").execute()
                                    total += 1
                                except: pass
                except: pass
            
            current_step += 1
            progress_bar.progress(min(current_step / steps, 1.0))
            
    status_text.empty()
    progress_bar.empty()
    return total
