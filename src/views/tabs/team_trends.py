"""
Team Trends Tab - First TD trends by team and position analysis.
"""

import streamlit as st
import pandas as pd


def show_team_trends_tab(first_tds_df: pd.DataFrame, season: int) -> None:
    """Display team-level first TD trends and position analysis."""
    
    st.header("🏈 Team & Position Trends")
    
    # Defensive check
    if first_tds_df is None:
        st.warning("⚠️ No data provided.")
        return
    
    if isinstance(first_tds_df, pd.Series):
        st.warning("⚠️ Data format issue - received Series instead of DataFrame.")
        return
    
    if not isinstance(first_tds_df, pd.DataFrame):
        st.warning(f"⚠️ Unexpected data type: {type(first_tds_df)}")
        return
    
    if first_tds_df.empty:
        st.warning("⚠️ No first TD data available.")
        return
    
    try:
        # Create simple tabs
        tab1, tab2, tab3 = st.tabs(["Team Trends", "Position Analysis", "Weekly Breakdown"])
        
        with tab1:
            st.subheader("Team First TD Summary")
            if 'posteam' in first_tds_df.columns:
                team_counts = first_tds_df['posteam'].value_counts()
                st.bar_chart(team_counts)
            else:
                st.info("Team data not available in dataset")
        
        with tab2:
            st.subheader("Position Analysis")
            if 'position' in first_tds_df.columns:
                pos_counts = first_tds_df['position'].value_counts()
                st.bar_chart(pos_counts)
            else:
                st.info("Position data not available in dataset")
        
        with tab3:
            st.subheader("Weekly Breakdown")
            if 'week' in first_tds_df.columns:
                week_counts = first_tds_df['week'].value_counts().sort_index()
                st.line_chart(week_counts)
            else:
                st.info("Week data not available in dataset")
    
    except Exception as e:
        st.error(f"Error rendering team trends: {str(e)}")
        st.write(f"Debug - Data shape: {first_tds_df.shape}, Type: {type(first_tds_df)}")
        st.write(f"Debug - Columns: {list(first_tds_df.columns) if hasattr(first_tds_df, 'columns') else 'N/A'}")
