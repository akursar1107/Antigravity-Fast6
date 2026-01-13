import streamlit as st
import pandas as pd
from utils.nfl_data import load_data, get_game_schedule
from utils import init_db, ensure_game_id_column, ensure_any_time_td_column
from views.public_dashboard import show_public_dashboard
from views.admin_page import show_admin_interface
from utils.theming import generate_theme_css
import config

# Initialize database and run migrations
init_db()
ensure_game_id_column()
ensure_any_time_td_column()

# Page Configuration
st.set_page_config(
    page_title="NFL TD Tracker",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply theme from configuration
theme_css = generate_theme_css(config.THEME)
st.markdown(theme_css, unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.header("Configuration")
    
    season = st.selectbox(
        "Select Season",
        options=config.SEASONS,
        index=0
    )
    
    # Game Type Filter
    game_type_filter = st.radio(
        "Game Type",
        options=["All", "Main Slate", "Standalone"],
        index=0,
        help="Main Slate: Sunday games < 8PM EST. Standalone: All others."
    )
    
    # Page Selection
    st.markdown("---")
    page = st.radio(
        "Select View",
        options=["📊 Public Dashboard", "🔐 Admin Interface"],
        index=0,
        help="Public Dashboard: Data views for all users. Admin Interface: Pick management."
    )

    st.markdown("---")
    st.markdown("""
    **About**
    This app uses `nflreadpy` to analyze NFL play-by-play data and identify touchdown scorers.
    """)

# Main Content
st.title(f"🏈 NFL Touchdown Tracker - {season}")

# Load Data
with st.spinner(f"Loading data for {season}..."):
    df = load_data(season)

# Apply game type filter (only if available)
if not df.empty and 'game_type' in df.columns:
    if game_type_filter == "Main Slate":
        df = df[df['game_type'] == "Main Slate"]
    elif game_type_filter == "Standalone":
        df = df[df['game_type'] == "Standalone"]

# Load Schedule
with st.spinner("Loading schedule..."):
    schedule = get_game_schedule(df, season)

# Route to appropriate page
if page == "📊 Public Dashboard":
    show_public_dashboard(df, season, schedule)
elif page == "🔐 Admin Interface":
    show_admin_interface(df, season, schedule)
