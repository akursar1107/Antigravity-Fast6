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
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: #0F1419 !important;
    }}
    
    .main {{
        background: transparent !important;
    }}
    
    .block-container {{
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }}
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {{
        font-family: '{font}';
        font-weight: 700;
        color: #F7FAFC;
        letter-spacing: -0.01em;
    }}
    
    h1 {{
        font-size: 2.5rem;
        color: #F7FAFC;
        margin-bottom: 1rem;
    }}
    
    h2 {{
        font-size: 1.75rem;
        color: #F7FAFC;
        margin-bottom: 0.75rem;
    }}
    
    p, div, span, label {{
        font-family: '{font}';
        color: #F7FAFC;
    }}
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background: {secondary};
        border-right: 1px solid #2D3748;
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
    
    /* Metric Cards */
    [data-testid="stMetric"] {{
        background: {secondary};
        padding: 1.5rem;
        border-radius: {radius};
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        border: 1px solid #2D3748;
        border-left: 4px solid {primary};
    }}
    
    [data-testid="stMetric"] [data-testid="stMetricLabel"] {{
        color: #A0AEC0 !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.75rem !important;
    }}
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {primary} !important;
        font-weight: 700 !important;
        font-family: 'Roboto Mono', monospace;
    }}
    
    /* Tabs styling */
    .stTabs {{
        background: transparent;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: {secondary};
        padding: 8px;
        border-radius: {radius};
        border: 1px solid #2D3748;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: {radius};
        color: #A0AEC0;
        font-weight: 600;
        padding: 10px 20px;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {primary};
        color: #ffffff;
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
    
    /* Buttons */
    .stButton button {{
        background: {primary};
        color: #ffffff !important;
        border: none;
        border-radius: {radius};
        padding: 0.6rem 1.75rem;
        font-weight: 600;
        font-family: '{font}';
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }}
    
    .stButton button:hover {{
        background: {accent};
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }}
    
    /* DataFrames and Tables */
    [data-testid="stDataFrame"], [data-testid="stTable"] {{
        background-color: transparent !important;
        border-radius: {radius};
        border: 1px solid #2D3748 !important;
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
        color: {primary} !important;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        padding: 0.875rem !important;
        border: none !important;
        border-bottom: 2px solid {primary} !important;
    }}
    
    .dataframe tbody tr {{
        background-color: transparent !important;
        color: #F7FAFC !important;
    }}
    
    .dataframe tbody tr:nth-child(even) {{
        background-color: rgba(26, 35, 50, 0.5) !important;
    }}
    
    .dataframe tbody td {{
        color: #F7FAFC !important;
        border-bottom: 1px solid #2D3748 !important;
    }}
    
    /* Input fields */
    div[data-baseweb="select"] {{
        background-color: {secondary} !important;
        border-radius: {radius} !important;
        border: 1px solid #2D3748 !important;
    }}
    
    div[data-baseweb="select"] * {{
        color: #F7FAFC !important;
    }}
    
    .stTextInput input, .stNumberInput input {{
        background-color: {secondary} !important;
        border: 1px solid #2D3748 !important;
        color: #F7FAFC !important;
        border-radius: {radius};
        padding: 0.75rem;
        font-family: '{font}';
    }}
    
    .stTextInput input:focus, .stNumberInput input:focus {{
        border-color: {primary} !important;
        box-shadow: 0 0 0 2px rgba(91, 143, 249, 0.2) !important;
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        background: {secondary} !important;
        border-radius: {radius} !important;
        font-weight: 600;
        color: #F7FAFC !important;
        border: 1px solid #2D3748 !important;
    }}
    
    .streamlit-expanderContent {{
        background: #0F1419 !important;
        border-radius: 0 0 {radius} {radius} !important;
        border: 1px solid #2D3748 !important;
        border-top: none !important;
    }}
    
    .streamlit-expanderHeader:hover {{
        background: #2D3748 !important;
        border-color: {primary} !important;
    }}
    
    /* Success/Error/Warning messages */
    .stSuccess {{
        background: rgba(81, 207, 102, 0.15) !important;
        color: {success} !important;
        border: 1px solid {success} !important;
        border-radius: {radius};
    }}
    
    .stError {{
        background: rgba(255, 107, 107, 0.15) !important;
        color: {error} !important;
        border: 1px solid {error} !important;
        border-radius: {radius};
    }}
    
    .stWarning {{
        background: rgba(255, 169, 77, 0.15) !important;
        color: {warning} !important;
        border: 1px solid {warning} !important;
        border-radius: {radius};
    }}
    
    .stInfo {{
        background: rgba(116, 143, 252, 0.15) !important;
        color: {info} !important;
        border: 1px solid {info} !important;
        border-radius: {radius};
        padding: 1rem;
    }}
    
    /* Progress bars */
    .stProgress > div > div {{
        background: {primary};
        border-radius: {radius};
    }}
    
    /* Dividers */
    hr {{
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: #2D3748;
    }}
    
    /* Column config for better spacing */
    [data-testid="column"] {{
        padding: 0 0.5rem;
    }}
    
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {{
        h1 {{
            font-size: 1.75rem;
        }}
        
        h2 {{
            font-size: 1.25rem;
        }}
        
        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 1.5rem;
        }}
        
        [data-testid="stMetric"] {{
            padding: 1rem;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            padding: 8px 12px;
            font-size: 0.85rem;
        }}
        
        .stButton button {{
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
        }}
        
        [data-testid="column"] {{
            padding: 0 0.25rem;
        }}
    }}
    
    /* Improve touch targets for mobile */
    @media (max-width: 768px) {{
        .stButton button {{
            min-height: 44px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            min-height: 44px;
        }}
    }}
    
    /* Radio buttons */
    .stRadio > label {{
        font-weight: 600;
        color: #F7FAFC;
    }}
    
    /* Checkbox */
    .stCheckbox > label {{
        font-weight: 500;
        color: #F7FAFC;
    }}
    
    /* File uploader */
    [data-testid="stFileUploader"] {{
        border: 2px dashed #2D3748;
        border-radius: {radius};
        padding: 2rem;
        background: {secondary};
    }}
    
    [data-testid="stFileUploader"]:hover {{
        border-color: {primary};
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
        border-radius: {radius};
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    .badge-success {{
        background: {success};
        color: white;
    }}
    
    .badge-error {{
        background: {error};
        color: white;
    }}
    
    .badge-pending {{
        background: {warning};
        color: white;
    }}
</style>
"""
    return css
