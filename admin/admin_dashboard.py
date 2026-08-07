import streamlit as st
from admin import analytics, user_manager, course_manager, quiz_manager, notification_manager
from database import db_session, User, Assessment

def show_dashboard(ai_engine=None):
    # Sidebar User Profile & Logout
    with st.sidebar:
        st.title("TalentSphere Elevate")
        st.markdown("---")
        st.write(f"👤 **{st.session_state.get('username', 'Admin')}**")
        st.write("*Administrator*")
        st.divider()
        if st.button("🚪 Logout", key="admin_sidebar_logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # Top Header with Title and Logout button
    head_col1, head_col2 = st.columns([6, 1])
    with head_col1:
        st.title("Admin Management System")
        st.caption("Welcome to the TalentSphere Elevate Admin control panel.")
    with head_col2:
        st.write("")  # Spacing
        if st.button("🚪 Logout", key="admin_header_logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Verify Admin Role
    if st.session_state.get("user_type") != "Admin":
        st.error("Unauthorized access. Admin privileges required.")
        return
        
    with db_session() as session:
        total_users = session.query(User).count()
        total_assessments = session.query(Assessment).count()
        
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", total_users)
    with col2:
        st.metric("Total Assessments", total_assessments)
    with col3:
        st.metric("System Health", "99.9%")
    with col4:
        st.metric("Active Sessions", 1)
        
    tabs = st.tabs([
        "Analytics", 
        "User Management", 
        "Course & Career Paths", 
        "Quiz Management", 
        "Notification Center"
    ])
    
    with tabs[0]:
        with st.container(border=True):
            analytics.render_analytics(ai_engine)
        
    with tabs[1]:
        with st.container(border=True):
            user_manager.render_user_manager(ai_engine)
        
    with tabs[2]:
        with st.container(border=True):
            course_manager.render_course_manager()
        
    with tabs[3]:
        with st.container(border=True):
            quiz_manager.render_quiz_manager()
        
    with tabs[4]:
        with st.container(border=True):
            notification_manager.render_notification_manager()
