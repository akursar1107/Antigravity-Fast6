"""
Team Trends Tab - First TD trends by team and position
"""

import streamlit as st
import pandas as pd


def show_team_trends_tab(first_tds_df: pd.DataFrame, season: int) -> None:
    """Display team-level first TD trends and position analysis."""
    
    st.header("🏈 Team & Position Trends")
    
    if first_tds_df is None or first_tds_df.empty:
        st.warning("⚠️ No first TD data available.")
        return
    
    # Create simple tabs
    tab1, tab2, tab3 = st.tabs(["Team Trends", "Position Analysis", "Weekly Breakdown"])
    
    with tab1:
        st.subheader("Team First TD Summary")
        if 'posteam' in first_tds_df.columns:
            team_counts = first_tds_df['posteam'].value_counts()
            st.bar_chart(team_counts)
            st.write(team_counts)
        else:
            st.info("Team data not available")
    
    with tab2:
        st.subheader("Position Analysis")
        if 'position' in first_tds_df.columns:
            pos_counts = first_tds_df['position'].value_counts()
            st.bar_chart(pos_counts)
            st.write(pos_counts)
        else:
            st.info("Position data not available")
    
    with tab3:
        st.subheader("Weekly Breakdown")
        if 'week' in first_tds_df.columns:
            week_counts = first_tds_df['week'].value_counts().sort_index()
            st.line_chart(week_counts)
            st.write(week_counts)
        else:
            st.info("Week data not available")
