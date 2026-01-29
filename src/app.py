import streamlit as st
import pandas as pd
from utils.nfl_data import load_data, get_game_schedule
from database import run_migrations
from views.public_dashboard import show_public_dashboard
from views.admin_page import show_admin_interface
from utils.theming import generate_theme_css
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
theme_css = generate_theme_css(config.THEME)
st.markdown(theme_css, unsafe_allow_html=True)

# Additional CSS fix for dropdown menus (Streamlit renders these outside main container)
# This includes Chromium/Edge specific fixes
dropdown_fix_css = """
<style>
/* Fix for Streamlit selectbox dropdown - targets the portal element */
div[data-baseweb="popover"] {
    background-color: #1A2332 !important;
}
div[data-baseweb="popover"] ul {
    background-color: #1A2332 !important;
}
div[data-baseweb="popover"] li {
    background-color: #1A2332 !important;
    color: #F7FAFC !important;
}
div[data-baseweb="popover"] li:hover {
    background-color: #2D3748 !important;
}
div[data-baseweb="popover"] li[aria-selected="true"] {
    background-color: #5B8FF9 !important;
}
/* Target the specific Streamlit virtual dropdown */
[data-testid="stSelectboxVirtualDropdown"] {
    background-color: #1A2332 !important;
}
[data-testid="stSelectboxVirtualDropdown"] * {
    color: #F7FAFC !important;
}

/* ========================================
   CHROMIUM/EDGE SPECIFIC FIXES
   ======================================== */

/* Chromium renders BaseWeb menus differently */
div[data-baseweb="menu"] {
    background-color: #1A2332 !important;
    background: #1A2332 !important;
}

div[data-baseweb="menu"] ul {
    background-color: #1A2332 !important;
    background: #1A2332 !important;
}

div[data-baseweb="menu"] li {
    background-color: #1A2332 !important;
    background: #1A2332 !important;
    color: #F7FAFC !important;
}

div[data-baseweb="menu"] li:hover {
    background-color: #2D3748 !important;
    background: #2D3748 !important;
}

/* Target the inner content of list items */
div[data-baseweb="menu"] li > div {
    background-color: transparent !important;
    color: #F7FAFC !important;
}

div[data-baseweb="menu"] li span {
    color: #F7FAFC !important;
}

/* BaseWeb block-level overrides for Chromium */
[data-baseweb="block"] {
    background-color: #1A2332 !important;
}

/* Force color on any child elements */
div[data-baseweb="popover"] div,
div[data-baseweb="popover"] span,
div[data-baseweb="menu"] div,
div[data-baseweb="menu"] span {
    color: #F7FAFC !important;
}

/* Target styled-components classes that Chromium uses */
[class*="StyledList"] {
    background-color: #1A2332 !important;
}

[class*="StyledListItem"] {
    background-color: #1A2332 !important;
    color: #F7FAFC !important;
}

[class*="StyledListItem"]:hover {
    background-color: #2D3748 !important;
}

/* Layer/overlay targeting for Edge */
div[data-layer] ul,
div[data-layer] li {
    background-color: #1A2332 !important;
    color: #F7FAFC !important;
}
</style>
"""
st.markdown(dropdown_fix_css, unsafe_allow_html=True)

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
