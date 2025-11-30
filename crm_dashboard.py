import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import supabase

def setup_page():
    st.set_page_config(
        page_title="Hunter Pro CRM",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #1f77b4;
        }
        </style>
    """, unsafe_allow_html=True)

def login_section():
    st.sidebar.title("🔐 تسجيل الدخول")
    
    with st.sidebar.form("login_form"):
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        submit = st.form_submit_button("دخول")
        
        if submit:
            try:
                result = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
                
                if result.data and result.data[0]['is_active']:
                    user = result.data[0]
                    st.session_state.user = {
                        'username': user['username'],
                        'role': user['role'],
                        'permissions': {
                            'can_hunt': user.get('can_hunt', True),
                            'can_campaign': user.get('can_campaign', False),
                            'can_share': user.get('can_share', False)
                        }
                    }
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.sidebar.error("بيانات الدخول غير صحيحة")
            except Exception as e:
                st.sidebar.error(f"خطأ في الاتصال: {e}")

def main_dashboard():
    st.markdown('<h1 class="main-header">🎯 لوحة تحكم Hunter Pro</h1>', unsafe_allow_html=True)
    
    # الإحصائيات السريعة
    st.subheader("📊 الإحصائيات السريعة")
    quick_stats = get_quick_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("إجمالي العملاء", quick_stats['total_leads'])
    with col2:
        st.metric("عملاء جدد", quick_stats['new_leads'])
    with col3:
        st.metric("عملاء ممتازين", quick_stats['excellent_leads'])
    with col4:
        st.metric("معدل النجاح", f"{quick_stats['success_rate']}%")
    
    # المخططات
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 توزيع الجودة")
        quality_fig = create_quality_chart(quick_stats['quality_distribution'])
        st.plotly_chart(quality_fig, use_container_width=True)
    
    with col2:
        st.subheader("🕒 النشاط اليومي")
        activity_fig = create_activity_chart()
        st.plotly_chart(activity_fig, use_container_width=True)
    
    # البحث السريع
    st.subheader("🔍 بحث سريع عن عملاء")
    with st.form("quick_search_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_intent = st.text_input("نية البحث", placeholder="مثال: مطلوب شقة في التجمع")
        with col2:
            search_city = st.selectbox("المدينة", ["القاهرة", "الجيزة", "الإسكندرية", "المنصورة", "أسيوط"])
        with col3:
            search_quality = st.selectbox("الجودة المستهدفة", ["الكل", "ممتاز 🔥", "جيد ⭐"])
        
        if st.form_submit_button("بدء البحث السريع"):
            if search_intent and search_city:
                st.success(f"بدأ البحث عن: {search_intent} في {search_city}")
                # سيتم دمج استدعاء API البحث هنا
            else:
                st.error("يرجى إدخال نية البحث وتحديد المدينة")

def leads_management():
    st.subheader("👥 إدارة العملاء المحتملين")
    
    # أشرطة الفلترة
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        quality_filter = st.selectbox("جودة العملاء", ["الكل", "ممتاز 🔥", "جيد ⭐", "رفض"])
    with col2:
        status_filter = st.selectbox("حالة العميل", ["الكل", "NEW", "CONTACTED", "CONVERTED", "FAILED"])
    with col3:
        source_filter = st.selectbox("المصدر", ["الكل", "Facebook", "OLX", "Opensooq", "Google"])
    with col4:
        date_filter = st.selectbox("الفترة", ["اليوم", "أسبوع", "شهر", "الكل"])
    
    try:
        # جلب البيانات مع الفلترة
        query = supabase.table("leads").select("*").eq("user_id", st.session_state.user['username'])
        
        if quality_filter != "الكل":
            query = query.eq("quality", quality_filter)
        if status_filter != "الكل":
            query = query.eq("status", status_filter)
        
        leads_data = query.order("created_at", desc=True).limit(200).execute()
        
        if leads_data.data:
            df = pd.DataFrame(leads_data.data)
            
            # عرض البيانات
            st.dataframe(
                df[['phone_number', 'quality', 'status', 'source', 'created_at']],
                use_container_width=True,
                height=400
            )
            
            # إجراءات جماعية
            st.subheader("الإجراءات الجماعية")
            selected_indices = st.multiselect("اختر العملاء:", df.index.tolist())
            bulk_action = st.selectbox("الإجراء:", ["---", "تحديث الحالة", "إرسال رسالة واتساب", "تصدير البيانات"])
            
            if st.button("تنفيذ الإجراء") and bulk_action != "---":
                st.success(f"تم تطبيق {bulk_action} على {len(selected_indices)} عميل")
        else:
            st.info("لا توجد عملاء محتملين لعرضها")
            
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {e}")

def get_quick_stats():
    try:
        user_id = st.session_state.user['username']
        
        # إجمالي العملاء
        total_result = supabase.table("leads").select("id", count="exact").eq("user_id", user_id).execute()
        total_leads = total_result.count or 0
        
        # العملاء الجدد (آخر 7 أيام)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        new_result = supabase.table("leads").select("id", count="exact").eq("user_id", user_id).gte("created_at", week_ago).execute()
        new_leads = new_result.count or 0
        
        # توزيع الجودة
        quality_result = supabase.table("leads").select("quality").eq("user_id", user_id).execute()
        quality_dist = {"ممتاز 🔥": 0, "جيد ⭐": 0, "رفض": 0}
        
        for lead in quality_result.data:
            quality = lead.get('quality')
            if quality in quality_dist:
                quality_dist[quality] += 1
        
        # معدل النجاح
        excellent_leads = quality_dist["ممتاز 🔥"]
        success_rate = round((excellent_leads / total_leads * 100), 1) if total_leads > 0 else 0
        
        return {
            'total_leads': total_leads,
            'new_leads': new_leads,
            'excellent_leads': excellent_leads,
            'success_rate': success_rate,
            'quality_distribution': quality_dist
        }
        
    except Exception as e:
        st.error(f"خطأ في جلب الإحصائيات: {e}")
        return {'total_leads': 0, 'new_leads': 0, 'excellent_leads': 0, 'success_rate': 0, 'quality_distribution': {}}

def create_quality_chart(quality_dist):
    labels = list(quality_dist.keys())
    values = list(quality_dist.values())
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.3,
        marker=dict(colors=colors)
    )])
    
    fig.update_layout(
        title="توزيع جودة العملاء",
        showlegend=True
    )
    
    return fig

def create_activity_chart():
    # بيانات نموذجية للنشاط
    days = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
    activity = [12, 19, 8, 15, 12, 18, 14]
    
    fig = go.Figure(data=[go.Bar(x=days, y=activity)])
    fig.update_layout(title="النشاط اليومي لإضافة العملاء")
    
    return fig

def user_management():
    if st.session_state.user['role'] != 'admin':
        st.warning("⛔ ليس لديك صلاحية للوصول إلى هذه الصفحة")
        return
    
    st.subheader("👥 إدارة المستخدمين")
    
    try:
        users_data = supabase.table("users").select("*").execute()
        
        if users_data.data:
            df = pd.DataFrame(users_data.data)
            st.dataframe(df[['username', 'role', 'is_active', 'created_at']], use_container_width=True)
            
            # إضافة مستخدم جديد
            with st.expander("إضافة مستخدم جديد"):
                with st.form("add_user_form"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        new_username = st.text_input("اسم المستخدم")
                    with col2:
                        new_password = st.text_input("كلمة المرور", type="password")
                    with col3:
                        new_role = st.selectbox("الدور", ["user", "manager", "admin"])
                    
                    if st.form_submit_button("إضافة مستخدم"):
                        if new_username and new_password:
                            st.success(f"تمت إضافة المستخدم {new_username}")
                        else:
                            st.error("يرجى إدخال جميع البيانات")
        else:
            st.info("لا توجد بيانات مستخدمين")
            
    except Exception as e:
        st.error(f"خطأ في تحميل بيانات المستخدمين: {e}")

def main():
    setup_page()
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        login_section()
        st.info("🔐 يرجى تسجيل الدخول من الشريط الجانبي")
        return
    
    # الشريط الجانبي
    st.sidebar.title(f"مرحباً {st.session_state.user['username']}")
    st.sidebar.write(f"الدور: {st.session_state.user['role']}")
    
    menu_options = ["اللوحة الرئيسية", "إدارة العملاء", "إدارة المستخدمين"]
    selected_menu = st.sidebar.selectbox("القائمة", menu_options)
    
    if selected_menu == "اللوحة الرئيسية":
        main_dashboard()
    elif selected_menu == "إدارة العملاء":
        leads_management()
    elif selected_menu == "إدارة المستخدمين":
        user_management()
    
    st.sidebar.markdown("---")
    if st.sidebar.button("تسجيل الخروج"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()
