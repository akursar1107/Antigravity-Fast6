"""
All Touchdowns Tab - Display all touchdowns with filtering
"""

import streamlit as st
import pandas as pd


def show_all_touchdowns_tab(all_tds: pd.DataFrame) -> None:
    """Display all touchdowns with filtering options."""
    st.header("All Touchdowns Scored")
    
    if not all_tds.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            selected_team = st.multiselect(
                "Filter by Scoring Team", 
                options=sorted(all_tds['posteam'].dropna().unique())
            )
        with col_f2:
            selected_week = st.multiselect(
                "Filter by Week", 
                options=sorted(all_tds['week'].dropna().unique())
            )
        
        filtered_tds = all_tds
        if selected_team:
            filtered_tds = filtered_tds[filtered_tds['posteam'].isin(selected_team)]
        if selected_week:
            filtered_tds = filtered_tds[filtered_tds['week'].isin(selected_week)]
            
        display_cols_all = [
            'week', 'posteam', 'defteam', 'td_player_name', 'play_type', 'qtr', 'time', 'desc'
        ]
        valid_cols_all = [c for c in display_cols_all if c in filtered_tds.columns]

        st.dataframe(
            filtered_tds[valid_cols_all],
            width="stretch",
            hide_index=True
        )
    else:
        st.info("No touchdowns found.")
