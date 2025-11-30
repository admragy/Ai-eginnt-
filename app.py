from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import os
import json
import requests
import re
import time
import random
from datetime import datetime, timedelta
from supabase import create_client
from pydantic import BaseModel
from typing import List, Optional

# إعدادات التطبيق
app = FastAPI(
    title="Hunter Pro System",
    description="نظام متكامل للبحث عن العملاء وإدارة الحملات",
    version="4.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# إعدادات الأمان
security = HTTPBearer()
SERPER_KEYS = [k.strip() for k in os.environ.get("SERPER_KEYS", "").split(",") if k.strip()]
key_index = 0

# اتصال قاعدة البيانات
try:
    supabase = create_client(
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_KEY")
    )
    DB_STATUS = True
    print("✅ Connected to Supabase successfully!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    supabase = None
    DB_STATUS = False

# نماذج البيانات
class HuntRequest(BaseModel):
    intent_sentence: str
    city: str
    time_filter: str = "qdr:m"
    user_id: str = "admin"
    max_results: int = 50

class LoginRequest(BaseModel):
    username: str
    password: str

class WhatsAppRequest(BaseModel):
    phone_number: str
    message: str
    user_id: str

class CampaignRequest(BaseModel):
    campaign_name: str
    message_template: str
    target_quality: List[str]
    created_by: str

# نظام إدارة المفاتيح
def get_active_key():
    global key_index
    if not SERPER_KEYS:
        return None
    key = SERPER_KEYS[key_index]
    key_index = (key_index + 1) % len(SERPER_KEYS)
    return key

# نظام التأخير الآمن
request_count = 0
last_reset = time.time()

def safe_request_delay():
    global request_count, last_reset
    if time.time() - last_reset > 60:
        request_count = 0
        last_reset = time.time()
    
    request_count += 1
    
    if request_count > 30:
        time.sleep(3.0)
    elif request_count > 20:
        time.sleep(2.0)
    elif request_count > 10:
        time.sleep(1.5)
    else:
        time.sleep(1.0)

# نظام تحليل الجودة المتقدم
def analyze_quality(text):
    text = text.lower()
    
    # القائمة السوداء - ارمي فوراً
    blacklist = ["للبيع", "for sale", "متاح الان", "احجز الان", "تواصل معنا", 
                 "امتلك", "فرصة", "offer", "discount", "خصم", "عرض", "بيع",
                 "مشروع جديد", "تسهيلات", "تقدم وساهم", "استثمر"]
    
    for word in blacklist:
        if word in text:
            return "رفض"

    # القائمة البيضاء - خد فوراً
    whitelist = ["مطلوب", "محتاج", "عايز", "أبحث", "شراء", "كاش", "نقدي",
                 "wanted", "buying", "looking for", "need", "مستعد", "بدور",
                 "ابحث", "محتاجة", "عاوز", "عاوزه", "محتاجه"]
    
    for word in whitelist:
        if word in text:
            return "ممتاز 🔥"

    # المحايد - خد بحذر
    neutral = ["سعر", "تفاصيل", "price", "details", "بكام", "تكلفة", "تكلف",
               "معلومات", "info", "استفسار", "استشارة", "رأيك", "نصيحة"]
    
    for word in neutral:
        if word in text:
            return "جيد ⭐"
            
    return "رفض"

# حفظ العميل المحتمل
def save_lead(phone, keyword, link, quality, user_id):
    if quality == "رفض" or not phone:
        return False
        
    try:
        data = {
            "phone_number": phone,
            "source": f"Hunter: {keyword}",
            "quality": quality,
            "status": "NEW",
            "user_id": user_id,
            "notes": f"المصدر: {link}"
        }
        
        result = supabase.table("leads").upsert(data, on_conflict="phone_number").execute()
        print(f"💎 LEAD SAVED: {phone} | {quality}")
        return True
    except Exception as e:
        print(f"❌ SAVE ERROR: {e}")
        return False

# المحرك الرئيسي للبحث
def run_hunt_process(intent: str, city: str, time_filter: str, user_id: str, max_results: int = 50):
    if not SERPER_KEYS:
        print("❌ No API keys available")
        return
    
    search_intent = f"مطلوب {intent}" if "شقة" in intent and "مطلوب" not in intent else intent
    
    print(f"🦅 HUNT STARTED: {search_intent} in {city}")
    
    # استراتيجيات البحث
    search_strategies = [
        f'"{search_intent}" "{city}" "010"',
        f'"{search_intent}" "{city}" "011"',
        f'"{search_intent}" "{city}" "012"',
        f'"{search_intent}" "{city}" "015"',
        f'site:facebook.com "{search_intent}" "{city}"',
        f'site:olx.com.eg "{search_intent}" "{city}"'
    ]
    
    total_found = 0
    domains_checked = 0
    start_time = time.time()
    
    for strategy in search_strategies[:3]:  # خذ أول 3 استراتيجيات فقط
        if total_found >= max_results:
            break
            
        api_key = get_active_key()
        if not api_key:
            continue
            
        safe_request_delay()
            
        payload = json.dumps({
            "q": strategy,
            "num": 20,
            "tbs": time_filter,
            "gl": "eg",
            "hl": "ar"
        })
        
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            print(f"🔍 Searching: {strategy[:60]}...")
            response = requests.post("https://google.serper.dev/search", 
                                   headers=headers, data=payload, timeout=30)
            
            if response.status_code == 429:
                print("⚠️ Rate limit warning - slowing down...")
                time.sleep(10)
                continue
            elif response.status_code != 200:
                print(f"🔴 API Error: {response.status_code}")
                continue
                
            results = response.json().get("organic", [])
            domains_checked += len(results)
            
            for res in results:
                title = res.get('title', '')
                snippet = res.get('snippet', '')
                content = f"{title} {snippet}"
                
                quality = analyze_quality(content)
                
                if quality != "رفض":
                    phones = re.findall(r'(01[0125][0-9]{8})', content)
                    for phone in phones[:2]:
                        if save_lead(phone, intent, res.get('link'), quality, user_id):
                            total_found += 1
                            if total_found >= max_results:
                                break
                
                if total_found >= max_results:
                    break
                    
            time.sleep(2)
            
        except requests.exceptions.Timeout:
            print("⏰ Request timeout - continuing...")
            continue
        except Exception as e:
            print(f"🔴 Search error: {e}")
            continue

    duration = int(time.time() - start_time)
    
    # حفظ سجل البحث
    try:
        log_data = {
            "user_id": user_id,
            "search_query": intent,
            "city": city,
            "results_count": total_found,
            "domains_checked": domains_checked,
            "duration": duration
        }
        supabase.table("hunt_logs").insert(log_data).execute()
    except Exception as e:
        print(f"❌ Failed to save hunt log: {e}")

    print(f"✅ HUNT COMPLETED: {total_found} leads in {duration}s")

# المسارات الرئيسية
@app.get("/")
def home():
    return {
        "message": "🚀 Hunter Pro System - Ready for Action!",
        "version": "4.0",
        "database": "connected" if DB_STATUS else "disconnected",
        "endpoints": {
            "search": "/hunt",
            "leads": "/leads",
            "whatsapp": "/send-whatsapp",
            "stats": "/stats"
        }
    }

@app.post("/hunt")
async def start_hunt(req: HuntRequest, background_tasks: BackgroundTasks):
    """بدء عملية البحث عن العملاء"""
    background_tasks.add_task(
        run_hunt_process, 
        req.intent_sentence, 
        req.city, 
        req.time_filter, 
        req.user_id,
        req.max_results
    )
    return {
        "status": "started",
        "message": "بدأ البحث عن العملاء المحتملين",
        "search": req.intent_sentence,
        "city": req.city,
        "user": req.user_id
    }

@app.post("/login")
async def login(req: LoginRequest):
    """تسجيل الدخول"""
    try:
        result = supabase.table("users").select("*").eq("username", req.username).eq("password", req.password).execute()
        
        if result.data and result.data[0]['is_active']:
            user = result.data[0]
            return {
                "success": True,
                "user": {
                    "username": user['username'],
                    "role": user['role'],
                    "permissions": {
                        "can_hunt": user.get('can_hunt', True),
                        "can_campaign": user.get('can_campaign', False),
                        "can_share": user.get('can_share', False)
                    }
                }
            }
    except Exception as e:
        print(f"Login error: {e}")
    
    return {"success": False, "error": "بيانات الدخول غير صحيحة"}

@app.get("/leads")
async def get_leads(
    user_id: str = "admin",
    quality: str = None,
    status: str = None,
    limit: int = 100,
    offset: int = 0
):
    """الحصول على العملاء المحتملين"""
    try:
        query = supabase.table("leads").select("*").eq("user_id", user_id)
        
        if quality:
            query = query.eq("quality", quality)
        if status:
            query = query.eq("status", status)
            
        result = query.order("created_at", desc=True).limit(limit).execute()
        
        return {
            "success": True,
            "leads": result.data,
            "total": len(result.data)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/stats")
async def get_stats(user_id: str = "admin"):
    """إحصائيات النظام"""
    try:
        # إحصائيات العملاء
        leads_stats = supabase.table("leads").select("quality, status").eq("user_id", user_id).execute()
        
        quality_count = {"ممتاز 🔥": 0, "جيد ⭐": 0, "رفض": 0}
        status_count = {"NEW": 0, "CONTACTED": 0, "CONVERTED": 0, "FAILED": 0}
        
        for lead in leads_stats.data:
            quality = lead.get('quality')
            status = lead.get('status')
            
            if quality in quality_count:
                quality_count[quality] += 1
            if status in status_count:
                status_count[status] += 1
        
        # إحصائيات البحث
        hunt_stats = supabase.table("hunt_logs").select("results_count").eq("user_id", user_id).execute()
        total_searches = len(hunt_stats.data)
        total_leads_found = sum(log['results_count'] for log in hunt_stats.data if log['results_count'])
        
        return {
            "success": True,
            "stats": {
                "total_leads": sum(quality_count.values()),
                "quality_distribution": quality_count,
                "status_distribution": status_count,
                "total_searches": total_searches,
                "total_leads_found": total_leads_found,
                "success_rate": round((total_leads_found / (total_searches * 50)) * 100, 2) if total_searches > 0 else 0
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/send-whatsapp")
async def send_whatsapp(req: WhatsAppRequest):
    """إرسال رسالة واتساب"""
    try:
        # هنا سيتم دمج كود Twilio لاحقاً
        print(f"📱 WhatsApp message to {req.phone_number}: {req.message}")
        
        return {
            "success": True,
            "message": "تم إرسال الرسالة بنجاح",
            "phone": req.phone_number
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/health")
def health_check():
    """فحص صحة النظام"""
    db_status = "healthy" if DB_STATUS else "unhealthy"
    return {
        "status": "running",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "version": "4.0"
    }

# للتشغيل المحلي
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
