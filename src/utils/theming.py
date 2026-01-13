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
    
    /* Main container and background */
    .main {{
        background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
        background-attachment: fixed;
    }}
    
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: rgba(255, 255, 255, 0.95);
        border-radius: {radius};
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }}
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {{
        font-family: '{font}';
        font-weight: 700;
        color: #1a202c;
        letter-spacing: -0.02em;
    }}
    
    h1 {{
        font-size: 3rem;
        background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1.5rem;
    }}
    
    p, div, span, label {{
        font-family: '{font}';
        color: #2d3748;
    }}
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #2d3748 0%, #1a202c 100%);
    }}
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {{
        color: #ffffff !important;
    }}
    
    [data-testid="stSidebar"] .stMarkdown {{
        color: #e2e8f0;
    }}
    
    /* Metric cards */
    [data-testid="stMetric"] {{
        background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
        padding: 1.5rem;
        border-radius: {radius};
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        border: none;
    }}
    
    [data-testid="stMetric"] label {{
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 600;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: #ffffff !important;
        font-size: 2.5rem;
        font-weight: 700;
        font-family: 'Roboto Mono', monospace;
    }}
    
    /* Tabs styling */
    .stTabs {{
        background: transparent;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: #f7fafc;
        padding: 8px;
        border-radius: 12px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 8px;
        color: #4a5568;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
        color: white !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }}
    
    /* Buttons */
    .stButton button {{
        background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-family: '{font}';
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
    }}
    
    .stButton button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }}
    
    /* DataFrames and Tables */
    [data-testid="stDataFrame"] {{
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }}
    
    .dataframe {{
        font-family: '{font}';
        border: none !important;
    }}
    
    .dataframe thead th {{
        background: linear-gradient(135deg, {primary} 0%, {secondary} 100%) !important;
        color: white !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        padding: 1rem !important;
        border: none !important;
    }}
    
    .dataframe tbody tr:nth-child(even) {{
        background-color: #f7fafc;
    }}
    
    .dataframe tbody tr:hover {{
        background-color: #edf2f7;
        transition: background-color 0.2s ease;
    }}
    
    .dataframe tbody td {{
        padding: 0.75rem 1rem;
        border: none !important;
        border-bottom: 1px solid #e2e8f0 !important;
    }}
    
    /* Input fields */
    .stTextInput input, .stNumberInput input, .stSelectbox select {{
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem;
        font-family: '{font}';
        transition: all 0.3s ease;
    }}
    
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {{
        border-color: {primary};
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        background: #f7fafc;
        border-radius: 10px;
        font-weight: 600;
        color: #2d3748;
        border: 1px solid #e2e8f0;
    }}
    
    .streamlit-expanderHeader:hover {{
        background: #edf2f7;
        border-color: #cbd5e0;
    }}
    
    /* Success/Error/Warning messages */
    .stSuccess {{
        background: linear-gradient(135deg, {success} 0%, {success} 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        border: none;
    }}
    
    .stError {{
        background: linear-gradient(135deg, {error} 0%, {error} 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        border: none;
    }}
    
    .stWarning {{
        background: linear-gradient(135deg, {warning} 0%, {warning} 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        border: none;
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
