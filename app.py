"""
Main Application Entry Point for TalentSphere Elevate.

This Streamlit application serves as the frontend for the Career Development Platform.
It handles user registration, authentication, and routing to specific modules based on user type.
"""

import streamlit as st
import bcrypt
from database import init_db, db_session, User
import modules.high_school as high_school
import modules.college as college
import modules.working_professional as working_professional
import modules.wp_models as wp_models
from ai import AIEngine

# Ensure the database tables are created on startup
init_db()

# Migration: Clean up orphaned ResumeData for High School Students
from database import db_session, User, ResumeData, engine
def run_migrations():
    try:
        with db_session() as session:
            hs_users = session.query(User).filter_by(user_type="High School").all()
            hs_user_ids = [u.id for u in hs_users]
            if hs_user_ids:
                session.query(ResumeData).filter(ResumeData.user_id.in_(hs_user_ids)).delete(synchronize_session=False)
    except Exception:
        pass

def run_column_migrations():
    """
    Safely adds new nullable columns to existing tables.
    Uses ALTER TABLE so existing data is never lost.
    """
    from sqlalchemy import text
    new_columns = [
        ("users", "full_name", "VARCHAR(100)"),
        ("users", "dob", "VARCHAR(10)"),
    ]
    with engine.connect() as conn:
        for table, column, col_type in new_columns:
            try:
                conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
                ))
                conn.commit()
            except Exception:
                # Column already exists — safe to ignore
                pass

run_migrations()
run_column_migrations()

# Page Configuration
st.set_page_config(
    page_title="TalentSphere Elevate",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide the Deploy button only
st.markdown(
    """
    <style>
    [data-testid="stAppDeployButton"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Authentication Utilities
def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    """Verifies a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def login_user(username: str, password: str) -> bool:
    """Authenticates the user and sets the session state."""
    with db_session() as session:
        user = session.query(User).filter(User.username == username).first()
        
        if user and check_password(password, user.password_hash):
            if hasattr(user, 'is_active') and getattr(user, 'is_active') == 0:
                return False # Account deactivated
            st.session_state['logged_in'] = True
            st.session_state['username'] = user.username
            st.session_state['user_type'] = user.user_type
            st.session_state['user_id'] = user.id
            return True
        return False

def register_user(
    username: str,
    password: str,
    user_type: str,
    full_name: str = None,
    dob: str = None
) -> tuple[bool, str]:
    """Registers a new user into the database."""
    with db_session() as session:
        # Check if user already exists
        if session.query(User).filter(User.username == username).first():
            return False, "Username already exists."
            
        try:
            hashed_pw = hash_password(password)
            new_user = User(
                username=username,
                password_hash=hashed_pw,
                user_type=user_type,
                full_name=full_name,
                dob=dob
            )
            session.add(new_user)
            # The context manager handles the commit automatically upon successful exit
            return True, "Registration successful. Please log in."
        except Exception:
            # The context manager handles rollback
            return False, "An error occurred during registration."

# UI Components
def show_login_page() -> None:
    """Displays the login and registration UI."""
    st.title("Welcome to TalentSphere Elevate 🚀")
    st.subheader("Your AI-Powered Career Development Platform")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.write("### Login to your account")
        with st.form("login_form"):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Username")
            with col2:
                password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login to account")
            
            if submit_button:
                if login_user(username, password):
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    
    with tab2:
        st.write("### Create a new account")
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Choose a Username")
                new_password = st.text_input("Choose a Password", type="password")
                user_type = st.selectbox(
                    "Select your profile type", 
                    ["High School Student", "College Student", "Working Professional", "Admin"]
                )
            with col2:
                full_name = st.text_input("Full Name (optional)")
                confirm_password = st.text_input("Confirm Password", type="password")
                dob = st.text_input("Date of Birth (DD/MM/YYYY, optional)")
            register_button = st.form_submit_button("Register account")
            
            if register_button:
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    success, message = register_user(
                        new_username, new_password, user_type,
                        full_name=full_name.strip() if full_name.strip() else None,
                        dob=dob.strip() if dob.strip() else None
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

def show_dashboard() -> None:
    """Displays the main dashboard based on user type."""
    user_type = st.session_state.get('user_type')
    
    # Initialize the AI Engine
    ai_engine = AIEngine()
    
    # Route to the appropriate module based on user profile type
    if user_type == "Admin":
        import admin.admin_dashboard as admin_dashboard
        admin_dashboard.show_dashboard(ai_engine)
    elif user_type == "High School Student":
        if hasattr(high_school, 'show_dashboard'):
            high_school.show_dashboard(ai_engine)
        else:
            st.info("High School module is currently under development.")
    elif user_type == "College Student":
        if hasattr(college, 'show_dashboard'):
            college.show_dashboard(ai_engine)
        else:
            st.info("College module is currently under development.")
    elif user_type == "Working Professional":
        if hasattr(working_professional, 'show_dashboard'):
            working_professional.show_dashboard(ai_engine)
        else:
            st.info("Professional module is currently under development.")
    else:
        st.error("Unknown user profile type.")

def main() -> None:
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        show_login_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
