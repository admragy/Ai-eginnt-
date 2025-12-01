import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_URL = "https://brilliox.ragyexp.repl.co"  # رابط الـ Backend

st.set_page_config(page_title="Hunter Pro CRM", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = "admin"

st.title("🎯 Hunter Pro - لوحة العميل")

# ✅ إحصائيات سريعة
res = requests.get(f"{API_URL}/admin-stats", params={"user_id": st.session_state.user})
if res.status_code == 200:
    data = res.json()
    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي العملاء", data.get("total_leads", 0))
    col2.metric("إجمالي الرسائل", data.get("total_messages", 0))
    col3.metric("إجمالي اليوزرز", data.get("total_users", 0))
else:
    st.error("❌ فشل تحميل الإحصائيات")

# ✅ بحث سريع
st.subheader("🔍 بحث سريع")
with st.form("quick_search"):
    intent = st.text_input("نية البحث", placeholder="مثال: شقة في التجمع")
    city = st.selectbox("المدينة", ["القاهرة", "الجيزة", "الإسكندرية"])
    if st.form_submit_button("ابدأ البحث"):
        if intent:
            res = requests.post(f"{API_URL}/hunt", json={"intent_sentence": intent, "city": city, "user_id": st.session_state.user})
            if res.status_code == 200:
                st.success("✅ تم بدء البحث")
            else:
                st.error("❌ فشل بدء البحث")

# ✅ عرض العملاء
st.subheader("👥 العملاء المحتملين")
res = requests.get(f"{API_URL}/leads", params={"user_id": st.session_state.user})
if res.status_code == 200:
    data = res.json().get("leads", [])
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df[['phone_number', 'quality', 'status', 'created_at']], use_container_width=True)
    else:
        st.info("لا يوجد عملاء حتى الآن")
else:
    st.error("❌ فشل تحميل البيانات")

# ✅ إضافة عميل خارجي
st.subheader("➕ إضافة عميل جديد")
with st.form("add_lead"):
    phone = st.text_input("رقم الهاتف", placeholder="01xxxxxxxxx")
    name = st.text_input("الاسم (اختياري)", placeholder="أحمد محمد")
    source = st.text_input("المصدر (اختياري)", placeholder="Facebook")
    quality = st.selectbox("الجودة", ["ممتاز 🔥", "جيد ⭐", "رفض"])
    notes = st.text_area("ملاحظات (اختياري)", placeholder="عايز شقة في التجمع")

    if st.form_submit_button("حفظ العميل"):
        if phone:
            res = requests.post(f"{API_URL}/add-lead", json={
                "phone_number": phone,
                "full_name": name,
                "source": source,
                "quality": quality,
                "notes": notes,
                "user_id": st.session_state.user
            })
            if res.status_code == 200:
                st.success("✅ تم إضافة العميل بنجاح!")
                st.balloons()
            else:
                st.error("❌ فشل الحفظ")
        else:
            st.warning("أدخل رقم الهاتف")

# ✅ إرسال واتساب
st.subheader("📤 إرسال رسالة واتساب")
phone = st.text_input("رقم الهاتف (مثال: +201012345678)", placeholder="+201012345678")
message = st.text_area("نص الرسالة", placeholder="مرحباً، لدينا عرض حصري لك...")
if st.button("إرسال"):
    if phone and message:
        res = requests.post(f"{API_URL}/send-whatsapp", json={"phone_number": phone, "message": message, "user_id": st.session_state.user})
        if res.status_code == 200:
            st.success("✅ تم إرسال الرسالة!")
        else:
            st.error("❌ فشل الإرسال")

# ✅ مشاركة العميل (داخلي / خارجي)
st.subheader("🔗 مشاركة العميل")
selected_phone = st.selectbox("اختر عميل للمشاركة", df['phone_number'].tolist())
share_type = st.radio("نوع المشاركة", ["داخلي (يوزر محدد)", "خارجي (رابط عام)"])

if share_type == "داخلي (يوزر محدد)":
    target_user = st.text_input("اسم المستخدم", placeholder="manager")
    if st.button("مشاركة داخلية"):
        res = requests.post(f"{API_URL}/share-lead", json={"phone": selected_phone, "shared_with": [target_user], "user_id": st.session_state.user})
        if res.status_code == 200:
            st.success(f"✅ تمت المشاركة مع {target_user}")
        else:
            st.error("❌ فشل المشاركة")

elif share_type == "خارجي (رابط عام)":
    if st.button("إنشاء رابط مشاركة"):
        res = requests.post(f"{API_URL}/share-lead", json={"phone": selected_phone, "is_public": True, "user_id": st.session_state.user})
        if res.status_code == 200:
            link = res.json().get("share_link")
            st.success("✅ تم إنشاء الرابط!")
            st.code(link, language=None)
        else:
            st.error("❌ فشل إنشاء الرابط")

# ✅ فيدباك فوري داخل الجدول
st.subheader("📊 حالة المشاركة")
res = requests.get(f"{API_URL}/lead-share-status", params={"phone": selected_phone})
if res.status_code == 200:
    data = res.json()
    share_status = data.get("share_status", "غير مشارك")
    share_date = data.get("share_date", "")
    share_by = data.get("share_by", "")

    col1, col2, col3 = st.columns(3)
    col1.metric("حالة المشاركة", share_status)
    col2.metric("وقت المشاركة", share_date or "—")
    col3.metric("شاركه", share_by or "—")

    if share_status != "غير مشارك":
        if st.button("إلغاء المشاركة"):
            cancel_res = requests.post(f"{API_URL}/cancel-share", json={"phone": selected_phone, "user_id": st.session_state.user})
            if cancel_res.status_code == 200:
                st.success("✅ تم إلغاء المشاركة")
                st.rerun()
else:
    st.error("❌ فشل تحميل بيانات المشاركة")

# ✅ آخر 10 أحداث (إشعارات فورية)
st.subheader("🔔 آخر 10 أحداث")
res = requests.get(f"{API_URL}/last-events")
if res.status_code == 200:
    events = res.json().get("events", [])
    if events:
        df_events = pd.DataFrame(events)
        st.dataframe(df_events[['timestamp', 'event', 'details']], use_container_width=True)
    else:
        st.info("لا توجد أحداث جديدة")
else:
    st.error("❌ فشل تحميل الأحداث")

# ✅ زر تحديث (إشعار فوري جديد)
if st.button("🔄 تحديث"):
    st.rerun()
