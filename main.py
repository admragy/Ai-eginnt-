from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import requests
import re
import time
from datetime import datetime
from supabase import create_client
from pydantic import BaseModel

app = FastAPI(title="Hunter Pro System", version="1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# اتصال قاعدة البيانات
try:
    supabase = create_client(
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_KEY")
    )
    DB_STATUS = True
    print("✅ Connected to Supabase!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    supabase = None
    DB_STATUS = False

# نماذج البيانات
class HuntRequest(BaseModel):
    intent_sentence: str
    city: str
    user_id: str = "admin"

class LoginRequest(BaseModel):
    username: str
    password: str

# نظام البحث
SERPER_KEYS = os.environ.get("SERPER_KEYS", "").split(",")
key_index = 0

def get_active_key():
    global key_index
    if not SERPER_KEYS: return None
    key = SERPER_KEYS[key_index]
    key_index = (key_index + 1) % len(SERPER_KEYS)
    return key

def analyze_quality(text):
    text = text.lower()
    
    blacklist = ["للبيع", "for sale", "متاح الان", "احجز الان", "سمسار", "وسيط"]
    for word in blacklist:
        if word in text:
            return "رفض"

    whitelist = ["مطلوب", "محتاج", "عايز", "أبحث", "شراء", "كاش", "wanted", "buying"]
    for word in whitelist:
        if word in text:
            return "ممتاز 🔥"

    return "جيد ⭐"

def save_lead(phone, keyword, link, quality, user_id):
    if quality == "رفض" or not phone:
        return False
        
    try:
        data = {
            "phone_number": phone,
            "source": f"Hunter: {keyword}",
            "quality": quality,
            "status": "NEW",
            "user_id": user_id
        }
        
        result = supabase.table("leads").upsert(data, on_conflict="phone_number").execute()
        print(f"💎 LEAD SAVED: {phone}")
        return True
    except Exception as e:
        print(f"❌ SAVE ERROR: {e}")
        return False

def run_search(intent: str, city: str, user_id: str):
    if not SERPER_KEYS:
        print("❌ No API keys")
        return
    
    api_key = get_active_key()
    if not api_key:
        return
    
    search_query = f'"{intent}" "{city}" "010"'
    
    payload = json.dumps({
        "q": search_query,
        "num": 10,
        "gl": "eg", 
        "hl": "ar"
    })
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"🔍 Searching: {intent} in {city}")
        response = requests.post("https://google.serper.dev/search", headers=headers, data=payload, timeout=30)
        
        if response.status_code == 200:
            results = response.json().get("organic", [])
            found_count = 0
            
            for res in results:
                content = f"{res.get('title', '')} {res.get('snippet', '')}"
                quality = analyze_quality(content)
                
                if quality != "رفض":
                    phones = re.findall(r'(01[0125][0-9]{8})', content)
                    for phone in phones:
                        if save_lead(phone, intent, res.get('link'), quality, user_id):
                            found_count += 1
            
            print(f"✅ Found {found_count} leads")
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Search error: {e}")

# المسارات الأساسية
@app.get("/")
def home():
    return {
        "message": "🚀 Hunter Pro System - Working!",
        "status": "running",
        "database": "connected" if DB_STATUS else "disconnected",
        "version": "1.0"
    }

@app.post("/hunt")
async def start_hunt(req: HuntRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_search, req.intent_sentence, req.city, req.user_id)
    return {
        "status": "started", 
        "message": f"بحث開始: {req.intent_sentence} في {req.city}",
        "user": req.user_id
    }

@app.post("/login")
async def login(req: LoginRequest):
    return {
        "success": True,
        "user": {
            "username": req.username,
            "role": "admin"
        }
    }

@app.get("/leads")
async def get_leads(user_id: str = "admin"):
    try:
        if not DB_STATUS:
            return {"success": False, "error": "Database disconnected"}
            
        result = supabase.table("leads").select("*").eq("user_id", user_id).limit(20).execute()
        return {
            "success": True,
            "leads": result.data,
            "count": len(result.data)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected" if DB_STATUS else "disconnected", 
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
