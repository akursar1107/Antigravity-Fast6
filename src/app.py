import streamlit as st
import pandas as pd
from utils.nfl_data import load_data, get_game_schedule
from utils import init_db, ensure_game_id_column, ensure_any_time_td_column
from views.public_dashboard import show_public_dashboard
from views.admin_page import show_admin_interface
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

# Custom CSS - Modern NFL Theme inspired by nfelo
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap');
    
    /* Main container and background */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #1a202c;
        letter-spacing: -0.02em;
    }
    
    h1 {
        font-size: 3rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1.5rem;
    }
    
    p, div, span, label {
        font-family: 'Inter', sans-serif;
        color: #2d3748;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d3748 0%, #1a202c 100%);
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    
    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        border: none;
    }
    
    [data-testid="stMetric"] label {
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 600;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2.5rem;
        font-weight: 700;
        font-family: 'Roboto Mono', monospace;
    }
    
    /* Tabs styling */
    .stTabs {
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f7fafc;
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #4a5568;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* DataFrames and Tables */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    .dataframe {
        font-family: 'Inter', sans-serif;
        border: none !important;
    }
    
    .dataframe thead th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        padding: 1rem !important;
        border: none !important;
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: #f7fafc;
    }
    
    .dataframe tbody tr:hover {
        background-color: #edf2f7;
        transition: background-color 0.2s ease;
    }
    
    .dataframe tbody td {
        padding: 0.75rem 1rem;
        border: none !important;
        border-bottom: 1px solid #e2e8f0 !important;
    }
    
    /* Input fields */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: #f7fafc;
        border-radius: 10px;
        font-weight: 600;
        color: #2d3748;
        border: 1px solid #e2e8f0;
    }
    
    .streamlit-expanderHeader:hover {
        background: #edf2f7;
        border-color: #cbd5e0;
    }
    
    /* Success/Error/Warning messages */
    .stSuccess {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        border: none;
    }
    
    .stError {
        background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        border: none;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        border: none;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        border: none;
    }
    
    /* Progress bars */
    .stProgress > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* Dividers */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
    }
    
    /* Column config for better spacing */
    [data-testid="column"] {
        padding: 0 1rem;
    }
    
    /* Radio buttons */
    .stRadio > label {
        font-weight: 600;
        color: #2d3748;
    }
    
    /* Checkbox */
    .stCheckbox > label {
        font-weight: 500;
        color: #2d3748;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #cbd5e0;
        border-radius: 12px;
        padding: 2rem;
        background: #f7fafc;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #667eea;
        background: #edf2f7;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Footer */
    footer {
        visibility: hidden;
    }
    
    /* Custom badge styles */
    .badge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .badge-success {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
    }
    
    .badge-error {
        background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
        color: white;
    }
    
    .badge-pending {
        background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

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
