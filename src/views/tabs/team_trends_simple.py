"""
Team Trends Tab - Simple placeholder version
"""

import streamlit as st
import pandas as pd


def show_team_trends_tab(first_tds_df: pd.DataFrame, season: int) -> None:
    """Display team-level first TD trends."""
    
    st.header("🏈 Team & Position Trends")
    st.info("📊 Team trends analysis - Coming soon with full data integration")
    
    if first_tds_df is None or first_tds_df.empty:
        st.warning("No first TD data available.")
        return
    
    st.write(f"Data shape: {first_tds_df.shape}")
    st.write(f"Available columns: {list(first_tds_df.columns)[:5]}...")
