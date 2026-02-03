"""Fast6 v2 - New Clean Architecture Entry Point

This is the new application using the clean architecture patterns:
- Core business logic independent of Streamlit/DB
- API layer for orchestration
- Data layer with repository pattern
- Thin Streamlit UI layer

To run this version instead of the legacy app:
  streamlit run src/app_v2.py
"""

import streamlit as st
from src.lib.theming import apply_global_theme
import config


def initialize_session():
    """Initialize Streamlit session state"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'role' not in st.session_state:
        st.session_state.role = "user"


def show_login():
    """Login page"""
    st.title("⏈ Fast6 - First TD Scorer Predictions")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("### Welcome")
        st.write("Sign in to your account to manage your picks and view the leaderboard.")
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Sign In", use_container_width=True):
            if username and password:
                # TODO: Integrate with auth system
                # For now, simple auth for testing
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_id = 1  # Placeholder
                st.session_state.role = "admin" if username == "admin" else "user"
                st.rerun()
            else:
                st.error("Please enter username and password")


def show_public_dashboard():
    """Public dashboard with leaderboard and picks"""
    st.header("📊 Public Dashboard")
    
    tab1, tab2, tab3 = st.tabs(["Leaderboard", "My Picks", "Analytics"])
    
    with tab1:
        st.info("Leaderboard view coming soon - will display top performers")
    
    with tab2:
        st.info("My Picks view coming soon - show user's current and past picks")
    
    with tab3:
        st.info("Analytics view coming soon - ROI, stats, trends")


def show_admin_dashboard():
    """Admin dashboard for managing system"""
    st.header("⚙️ Admin Dashboard")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Manage Picks", "Grading", "Users"])
    
    with tab1:
        st.info("Admin overview coming soon")
    
    with tab2:
        st.info("Pick management UI coming soon")
    
    with tab3:
        st.info("Grading interface coming soon")
    
    with tab4:
        st.info("User management coming soon")


def main():
    """Main application entry point"""
    
    # Initialize session state
    initialize_session()
    
    # Configure page
    st.set_page_config(
        page_title="Fast6 - NFL TD Tracker",
        page_icon="🏈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply theme
    apply_global_theme(config.THEME)
    
    # Sidebar
    with st.sidebar:
        st.title("⏈ Fast6")
        st.write("---")
        
        if st.session_state.logged_in:
            st.write(f"**User:** {st.session_state.username}")
            st.write(f"**Role:** {st.session_state.role}")
            
            if st.button("Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.role = "user"
                st.rerun()
    
    # Main content
    if not st.session_state.logged_in:
        show_login()
    else:
        if st.session_state.role == "admin":
            show_admin_dashboard()
        else:
            show_public_dashboard()
        
        # Footer
        st.write("---")
        st.write("✅ Running on Clean Architecture v2 | Database: SQLite")


if __name__ == "__main__":
    main()
