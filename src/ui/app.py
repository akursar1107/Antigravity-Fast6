"""Main Streamlit application - entry point"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Fast6"))

from src.lib.theming import apply_global_theme
from src import config


def main():
    """Main Streamlit app"""
    
    # Apply global theme
    apply_global_theme(config.THEME)
    
    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    # Sidebar logout button
    with st.sidebar:
        st.title("Fast6")
        if st.session_state.logged_in and st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
    
    # Route to appropriate view
    if not st.session_state.logged_in:
        show_login()
    else:
        st.info("Dashboard loading... [Full UI coming next]")


def show_login():
    """Login page"""
    st.title("Fast6 - First TD Scorer Predictions")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("### Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Sign In"):
            if username and password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Please enter username and password")


if __name__ == "__main__":
    main()
