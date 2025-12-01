from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import re
import requests
import json
from datetime import datetime
from supabase import create_client
from pydantic import BaseModel
from twilio.rest import Client

# Twilio
TWILIO_SID   = os.environ.get("TWILIO_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")

app = FastAPI(title="Hunter Pro", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

SERPER_KEYS = [k.strip() for k in os.environ.get("SERPER_KEYS", "").split(",") if k.strip()]
key_index = 0

# ========== النماذج ==========
class HuntRequest(BaseModel):
    intent_sentence: str
    city: str
    user_id: str = "admin"

class WhatsAppRequest(BaseModel):
    phone_number: str
    message: str
    user_id: str

class AddLeadRequest(BaseModel):
    phone_number: str
    full_name: str = ""
    source: str = "Manual"
    quality: str = "جيد ⭐"
    notes: str = ""
    user_id: str

class ShareRequest(BaseModel):
    phone: str
    shared_with: list[str] = []
    is_public: bool = False
    user_id: str

class AddUserRequest(BaseModel):
    username: str
    password: str
    role: str
    can_hunt: bool
    can_campaign: bool
    can_share: bool
    can_see_all_data: bool
    is_admin: bool

# ========== الأدوات ==========
def get_key(): global key_index; return SERPER_KEYS[key_index % len(SERPER_KEYS)] if SERPER_KEYS else None
def analyze_quality(text):
    text = text.lower()
    if any(w in text for w in ["للبيع", "for sale", "سمسار", "broker"]): return "رفض"
    if any(w in text for w in ["مطلوب", "محتاج", "عايز", "wanted"]): return "ممتاز 🔥"
    return "جيد ⭐"

def save_lead(phone, keyword, quality, user_id):
    try:
        supabase.table("leads").upsert({
            "phone_number": phone, "source": f"Hunter: {keyword}",
            "quality": quality, "status": "NEW", "user_id": user_id
        }, on_conflict="phone_number").execute()
        return True
    except: return False

def run_search(intent: str, city: str, user_id: str):
    key = get_key()
    if not key: return
    query = f'"{intent}" "{city}"'
    payload = json.dumps({"q": query, "num": 10, "gl": "eg", "hl": "ar"})
    headers = {"X-API-KEY": key, "Content-Type": "application/json"}
    try:
        res = requests.post("https://google.serper.dev/search", headers=headers, data=payload, timeout=30)
        if res.status_code == 200:
            results = res.json().get("organic", [])
            for r in results:
                content = f"{r.get('title', '')} {r.get('snippet', '')}"
                quality = analyze_quality(content)
                phones = re.findall(r'(01[0125][0-9]{8})', content)
                for phone in phones: save_lead(phone, intent, quality, user_id)
    except: pass

# ========== Endpoints ==========
@app.get("/")
def home(): return {"message": "Hunter Pro is running ✅"}

@app.post("/hunt")
async def hunt(req: HuntRequest, bg: BackgroundTasks):
    bg.add_task(run_search, req.intent_sentence, req.city, req.user_id)
    return {"status": "started", "search": req.intent_sentence, "city": req.city}

@app.get("/leads")
def get_leads(user_id: str = "admin", see_all: bool = False):
    try:
        user = supabase.table("users").select("can_see_all_data", "is_admin").eq("username", user_id).execute()
        if user.data and (user.data[0]["can_see_all_data"] or user.data[0]["is_admin"]):
            rows = supabase.table("leads").select("*").order("created_at", desc=True).execute()
        else:
            rows = supabase.table("leads").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return {"success": True, "leads": rows.data}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/send-whatsapp")
async def send_whatsapp(req: WhatsAppRequest):
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        message = client.messages.create(
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            body=req.message,
            to=f"whatsapp:{req.phone_number}"
        )
        return {"success": True, "message": "تم الإرسال", "sid": message.sid}
    except Exception as e:
        return {"success": False, "error": str(e)}

# إضافة عميل خارجي
@app.post("/add-lead")
def add_lead(req: AddLeadRequest):
    try:
        supabase.table("leads").insert(req.dict()).execute()
        return {"success": True, "message": "تم الإضافة"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# نظام المشاركة (داخلي / خارجي)
@app.post("/share-lead")
def share_lead(req: ShareRequest):
    try:
        if req.is_public:
            share_link = f"{API_URL}/public/lead/{req.phone}"
            supabase.table("leads").update({"is_public": True}).eq("phone_number", req.phone).eq("user_id", req.user_id).execute()
            return {"success": True, "share_link": share_link}
        supabase.table("leads").update({"shared_with": req.shared_with}).eq("phone_number", req.phone).eq("user_id", req.user_id).execute()
        return {"success": True, "message": f"تمت المشاركة مع {req.shared_with}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/public/lead/{phone}")
def public_lead(phone: str):
    try:
        row = supabase.table("leads").select("*").eq("phone_number", phone).eq("is_public", True).execute()
        if row.data: return {"success": True, "lead": row.data[0]}
        else: return {"success": False, "message": "غير مسموح بالمشاهدة"}
    except: return {"success": False, "message": "خطأ في البيانات"}

# إدارة اليوزرز
@app.get("/admin-stats")
def admin_stats():
    try:
        total_users = supabase.table("users").select("id", count="exact").execute().count or 0
        total_leads = supabase.table("leads").select("id", count="exact").execute().count or 0
        total_messages = supabase.table("campaign_logs").select("id", count="exact").execute().count or 0
        return {"total_users": total_users, "total_leads": total_leads, "total_messages": total_messages}
    except: return {"total_users": 0, "total_leads": 0, "total_messages": 0}

@app.get("/last-events")
def last_events():
    try:
        events = supabase.table("events").select("*").order("created_at", desc=True).limit(10).execute()
        return {"events": events.data}
    except: return {"events": []}

@app.post("/add-user")
def add_user(req: AddUserRequest):
    try:
        supabase.table("users").insert(req.dict()).execute()
        return {"success": True, "message": "تم الإضافة"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/delete-user")
def delete_user(username: str):
    try:
        supabase.table("users").delete().eq("username", username).execute()
        return {"success": True, "message": "تم الحذف"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/update-permissions")
def update_permissions(req: dict):
    try:
        supabase.table("users").update({
            "can_hunt": req["can_hunt"],
            "can_campaign": req["can_campaign"],
            "can_share": req["can_share"],
            "can_see_all_data": req["can_see_all_data"],
            "is_admin": req["is_admin"]
        }).eq("username", req["username"]).execute()
        return {"success": True, "message": "تم التحديث"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# صحة التطبيق
@app.get("/health")
def health_check():
    return {"status": "running", "timestamp": datetime.now().isoformat()}
