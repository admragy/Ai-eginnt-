import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_URL = "https://brilliox.ragyexp.repl.co"  # نفس الرابط

st.set_page_config(page_title="Hunter Pro - لوحة الإدارة", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = "admin"

st.title("🔐 لوحة إدارة Hunter Pro")

# ✅ إضافة يوزر جديد
with st.expander("➕ إضافة يوزر جديد"):
    with st.form("add_user"):
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        role = st.selectbox("الدور", ["admin", "manager", "user"])
        can_hunt = st.checkbox("يمكنه البحث", value=True)
        can_campaign = st.checkbox("يمكنه الحملات", value=False)
        can_share = st.checkbox("يمكنه المشاركة", value=False)
        can_see_all_data = st.checkbox("يمكنه مشاهدة كل الداتا", value=False)
        is_admin = st.checkbox("هل هو Admin؟", value=False)

        if st.form_submit_button("إضافة يوزر"):
            if username and password:
                res = requests.post(f"{API_URL}/add-user", json={
                    "username": username,
                    "password": password,
                    "role": role,
                    "can_hunt": can_hunt,
                    "can_campaign": can_campaign,
                    "can_share": can_share,
                    "can_see_all_data": can_see_all_data,
                    "is_admin": is_admin
                })
                if res.status_code == 200:
                    st.success(f"✅ تم إضافة اليوزر {username}")
                    st.balloons()
                else:
                    st.error("❌ فشل الإضافة")
            else:
                st.warning("أكمل البيانات")

# ✅ حذف يوزر
with st.expander("🗑️ حذف يوزر"):
    target_user = st.text_input("اسم اليوزر للحذف", placeholder="user123")
    if st.button("حذف يوزر"):
        if target_user:
            res = requests.post(f"{API_URL}/delete-user", json={"username": target_user})
            if res.status_code == 200:
                st.success(f"✅ تم حذف اليوزر {target_user}")
            else:
                st.error("❌ فشل الحذف")

# ✅ تغيير صلاحيات يوزر
with st.expander("⚙️ تغيير صلاحيات يوزر"):
    user_to_edit = st.text_input("اسم اليوزر", placeholder="user123")
    new_can_hunt = st.checkbox("يمكنه البحث")
    new_can_campaign = st.checkbox("يمكنه الحملات")
    new_can_share = st.checkbox("يمكنه المشاركة")
    new_can_see_all_data = st.checkbox("يمكنه مشاهدة كل الداتا")
    new_is_admin = st.checkbox("هل هو Admin؟")

    if st.button("تحديث الصلاحيات"):
        res = requests.post(f"{API_URL}/update-permissions", json={
            "username": user_to_edit,
            "can_hunt": new_can_hunt,
            "can_campaign": new_can_campaign,
            "can_share": new_can_share,
            "can_see_all_data": new_can_see_all_data,
            "is_admin": new_is_admin
        })
        if res.status_code == 200:
            st.success(f"✅ تم تحديث صلاحيات {user_to_edit}")
        else:
            st.error("❌ فشل التحديث")

# ✅ إحصائيات الإدارة
st.subheader("📊 إحصائيات الإدارة")
res = requests.get(f"{API_URL}/admin-stats")
if res.status_code == 200:
    data = res.json()
    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي اليوزرز", data.get("total_users", 0))
    col2.metric("إجمالي العملاء", data.get("total_leads", 0))
    col3.metric("إجمالي الرسائل", data.get("total_messages", 0))
else:
    st.error("❌ فشل تحميل الإحصائيات")

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
