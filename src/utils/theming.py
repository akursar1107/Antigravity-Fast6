"""
Theme generation utility for dynamic Streamlit UI styling.
Generates CSS from configuration values for consistent theming.
"""

from typing import Dict


def generate_theme_css(theme: Dict[str, str]) -> str:
    """
    Generate comprehensive Streamlit CSS from theme configuration.
    
    Args:
        theme: Dictionary with theme colors and settings:
            - primary_color: Main brand color (e.g., #667eea)
            - secondary_color: Secondary/accent color (e.g., #764ba2)
            - accent_color: Tertiary accent (e.g., #f093fb)
            - success_color: Success state color (e.g., #48bb78)
            - error_color: Error state color (e.g., #f56565)
            - warning_color: Warning state color (e.g., #ed8936)
            - info_color: Info state color (e.g., #4299e1)
            - font_family: Font family for text (e.g., Inter, sans-serif)
            - border_radius: Border radius for components (e.g., 20px)
    
    Returns:
        CSS string ready to use with st.markdown(..., unsafe_allow_html=True)
    """
    primary = theme.get("primary_color", "#667eea")
    secondary = theme.get("secondary_color", "#764ba2")
    accent = theme.get("accent_color", "#f093fb")
    success = theme.get("success_color", "#48bb78")
    error = theme.get("error_color", "#f56565")
    warning = theme.get("warning_color", "#ed8936")
    info = theme.get("info_color", "#4299e1")
    font = theme.get("font_family", "Inter, sans-serif")
    radius = theme.get("border_radius", "20px")
    
    css = f"""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap');
    
    /* Main container and background - Midnight Navy */
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: {secondary} !important;
        background-image: radial-gradient(circle at 50% 0%, #102a43 0%, {secondary} 100%);
        background-attachment: fixed;
    }}
    
    .main {{
        background: transparent !important;
    }}
    
    .block-container {{
        padding-top: 3rem;
        padding-bottom: 3rem;
        background: rgba(45, 55, 72, 0.4); /* Charcoal Gray glass */
        border-radius: {radius};
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    
    /* Typography - Soft White */
    h1, h2, h3, h4, h5, h6 {{
        font-family: '{font}';
        font-weight: 700;
        color: #F7FAFC; /* Soft White */
        letter-spacing: -0.02em;
    }}
    
    h1 {{
        font-size: 2.75rem;
        background: linear-gradient(135deg, #F7FAFC 0%, #FFD700 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1.5rem;
    }}
    
    p, div, span, label {{
        font-family: '{font}';
        color: #F7FAFC; /* Soft White */
    }}
    
    /* Sidebar styling - Midnight Navy Glassmorphism */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #102a43 0%, #0A1A2F 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }}
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {{
        color: #f7fafc !important;
    }}
    
    [data-testid="stSidebar"] .stMarkdown {{
        color: #e2e8f0;
    }}
    
    /* Metric Cards - Modern Dark Glass */
    [data-testid="stMetric"] {{
        background: rgba(45, 55, 72, 0.6);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-left: 6px solid {accent};
        transition: all 0.3s ease;
    }}
    
    [data-testid="stMetric"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        border-color: rgba(255, 255, 255, 0.1);
    }}
    
    [data-testid="stMetric"] [data-testid="stMetricLabel"] {{
        color: #cbd5e0 !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.75rem !important;
    }}
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: #FFD700 !important;
        font-weight: 700 !important;
        font-family: 'Roboto Mono', monospace;
    }}
    
    /* Tabs styling */
    .stTabs {{
        background: transparent;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: rgba(15, 23, 42, 0.8);
        padding: 8px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 8px;
        color: #cbd5e0;
        font-weight: 600;
        padding: 10px 20px;
        transition: all 0.25s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {accent} 0%, #2f855a 100%);
        box-shadow: 0 4px 15px rgba(56, 161, 105, 0.3);
    }}
    
    /* Hide the default Streamlit tab highlight line */
    [data-baseweb="tab-highlight"] {{
        background-color: transparent !important;
    }}
    
    /* Target ALL possible inner text elements in active tab */
    .stTabs [aria-selected="true"] p,
    .stTabs [aria-selected="true"] span,
    .stTabs [aria-selected="true"] div,
    .stTabs [aria-selected="true"] label {{
        color: #ffffff !important;
    }}
    
    /* Buttons - Forest Green accent */
    .stButton button {{
        background: linear-gradient(135deg, {accent} 0%, #1a6d1a 100%);
        color: #ffffff !important;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.75rem;
        font-weight: 600;
        font-family: '{font}';
        box-shadow: 0 4px 12px rgba(34, 139, 34, 0.2);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .stButton button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(34, 139, 34, 0.3);
        background: linear-gradient(135deg, #2ea44f 0%, {accent} 100%);
    }}
    
    /* DataFrames and Tables - Advanced Dark Theme Refined */
    [data-testid="stDataFrame"], [data-testid="stTable"] {{
        background-color: transparent !important;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }}
    
    /* Target cells in st.dataframe (Glide Data Grid) */
    [data-testid="stDataFrame"] div[data-testid="stTable"] td {{
        background-color: transparent !important;
        color: #F7FAFC !important;
    }}
    
    .dataframe {{
        font-family: '{font}';
        border: none !important;
        background-color: transparent !important;
    }}
    
    .dataframe thead th {{
        background: {secondary} !important;
        color: #FFD700 !important; /* Victory Gold headers */
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        padding: 0.875rem !important;
        border: none !important;
        border-bottom: 2px solid {accent} !important;
    }}
    
    .dataframe tbody tr {{
        background-color: transparent !important;
        color: #F7FAFC !important;
    }}
    
    .dataframe tbody tr:nth-child(even) {{
        background-color: rgba(255, 255, 255, 0.03) !important;
    }}
    
    .dataframe tbody td {{
        color: #F7FAFC !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    }}
    
    /* Input fields - Dark Theme Refined */
    div[data-baseweb="select"] {{
        background-color: rgba(15, 23, 42, 0.8) !important;
        border-radius: 8px !important;
    }}
    
    div[data-baseweb="select"] * {{
        color: #F7FAFC !important;
    }}
    
    .stTextInput input, .stNumberInput input {{
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #F7FAFC !important;
        border-radius: 8px;
        padding: 0.75rem;
        font-family: '{font}';
        transition: all 0.3s ease;
    }}
    
    .stTextInput input:focus, .stNumberInput input:focus {{
        border-color: #FFD700 !important;
        box-shadow: 0 0 0 2px rgba(255, 215, 0, 0.2) !important;
    }}
    
    /* Expanders - Professional dark style */
    .streamlit-expanderHeader {{
        background: rgba(45, 55, 72, 0.4) !important;
        border-radius: 10px !important;
        font-weight: 600;
        color: #F7FAFC !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }}
    
    .streamlit-expanderContent {{
        background: rgba(45, 55, 72, 0.2) !important;
        border-radius: 0 0 10px 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-top: none !important;
    }}
    
    .streamlit-expanderHeader:hover {{
        background: rgba(45, 55, 72, 0.7) !important;
        border-color: {accent} !important;
    }}
    
    /* Success/Error/Warning messages */
    .stSuccess {{
        background: rgba(34, 139, 34, 0.2) !important;
        color: #48bb78 !important;
        border: 1px solid rgba(34, 139, 34, 0.3) !important;
        border-radius: 12px;
    }}
    
    .stError {{
        background: rgba(229, 62, 62, 0.1) !important;
        color: #fc8181 !important;
        border: 1px solid rgba(229, 62, 62, 0.2) !important;
        border-radius: 12px;
    }}
    
    .stWarning {{
        background: rgba(255, 215, 0, 0.1) !important;
        color: #FFD700 !important;
        border: 1px solid rgba(255, 215, 0, 0.2) !important;
        border-radius: 12px;
    }}
    
    .stInfo {{
        background: linear-gradient(135deg, {info} 0%, {info} 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        border: none;
    }}
    
    /* Progress bars */
    .stProgress > div > div {{
        background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
        border-radius: 10px;
    }}
    
    /* Dividers */
    hr {{
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
    }}
    
    /* Column config for better spacing */
    [data-testid="column"] {{
        padding: 0 1rem;
    }}
    
    /* Radio buttons */
    .stRadio > label {{
        font-weight: 600;
        color: #2d3748;
    }}
    
    /* Checkbox */
    .stCheckbox > label {{
        font-weight: 500;
        color: #2d3748;
    }}
    
    /* File uploader */
    [data-testid="stFileUploader"] {{
        border: 2px dashed #cbd5e0;
        border-radius: 12px;
        padding: 2rem;
        background: #f7fafc;
        transition: all 0.3s ease;
    }}
    
    [data-testid="stFileUploader"]:hover {{
        border-color: {primary};
        background: #edf2f7;
    }}
    
    /* Spinner */
    .stSpinner > div {{
        border-top-color: {primary} !important;
    }}
    
    /* Footer */
    footer {{
        visibility: hidden;
    }}
    
    /* Custom badge styles */
    .badge {{
        display: inline-block;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    .badge-success {{
        background: linear-gradient(135deg, {success} 0%, {success} 100%);
        color: white;
    }}
    
    .badge-error {{
        background: linear-gradient(135deg, {error} 0%, {error} 100%);
        color: white;
    }}
    
    .badge-pending {{
        background: linear-gradient(135deg, {warning} 0%, {warning} 100%);
        color: white;
    }}
</style>
"""
    return css
