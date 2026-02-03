import streamlit as st
import pandas as pd
from utils.nfl_data import load_data, get_game_schedule
from database import run_migrations
from views.public_dashboard import show_public_dashboard
from views.admin_page import show_admin_interface
from utils.theming import apply_global_theme
import config

# Run database migrations (replaces old init_db + ensure_* functions)
run_migrations()

# Initialize session state for persistent UI selections
if 'selected_season' not in st.session_state:
    st.session_state.selected_season = config.CURRENT_SEASON

if 'selected_week' not in st.session_state:
    st.session_state.selected_week = config.CURRENT_WEEK

if 'game_type_filter' not in st.session_state:
    st.session_state.game_type_filter = "All"

if 'selected_page' not in st.session_state:
    st.session_state.selected_page = "📊 Public Dashboard"

# Page Configuration
st.set_page_config(
    page_title="NFL TD Tracker",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply theme from configuration
apply_global_theme(config.THEME)

# Sidebar Configuration
with st.sidebar:
    st.header("Configuration")
    
    season = st.selectbox(
        "Select Season",
        options=config.SEASONS,
        index=config.SEASONS.index(st.session_state.selected_season) if st.session_state.selected_season in config.SEASONS else 0,
        key='season_selector'
    )
    # Update session state when selection changes
    st.session_state.selected_season = season
    
    # Game Type Filter
    game_type_filter = st.radio(
        "Game Type",
        options=["All", "Main Slate", "Standalone"],
        index=["All", "Main Slate", "Standalone"].index(st.session_state.game_type_filter),
        key='game_type_selector',
        help="Main Slate: Sunday games < 8PM EST. Standalone: All others."
    )
    # Update session state when selection changes
    st.session_state.game_type_filter = game_type_filter
    
    # Page Selection
    st.markdown("---")
    page = st.radio(
        "Select View",
        options=["📊 Public Dashboard", "🔐 Admin Interface"],
        index=["📊 Public Dashboard", "🔐 Admin Interface"].index(st.session_state.selected_page),
        key='page_selector',
        help="Public Dashboard: Data views for all users. Admin Interface: Pick management."
    )
    # Update session state when selection changes
    st.session_state.selected_page = page

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
