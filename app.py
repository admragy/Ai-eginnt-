from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# 1. تهيئة التطبيق
app = FastAPI()

# 2. إعدادات CORS (ضرورية للسماح بالاتصال من أي مكان)
origins = ["*"] # يفضل تحديد الدومين الخاص بك في التطبيقات الحقيقية

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. مسار الاختبار (للتأكد من أن التطبيق يعمل)
@app.get("/")
def read_root():
    return {"message": "Hunter Backend is Running Successfully!"}

# 4. مسار Hunter (هنا يتم وضع لوجيك البحث والإرسال)
# @app.post("/hunter/search")
# def run_hunter_search(data: dict):
#     # ضع كود البحث هنا (Google Search, ScrapingBee, Supabase)
#     return {"status": "Processing search request", "data_received": data}

# إذا كنت تريد تشغيله محلياً (غير ضروري لـ Render)
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
