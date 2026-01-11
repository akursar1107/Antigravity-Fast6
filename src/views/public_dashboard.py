"""
Public Dashboard - Read-only views for all users.
Displays first TD analysis, leaderboard, picks history, and weekly schedule.
Data sourced from NFL API and SQLite database.
"""

import streamlit as st
import pandas as pd
from utils.nfl_data import get_touchdowns, get_first_tds
from utils import init_db
from views.tabs import (
    show_first_td_tab,
    show_leaderboard_tab,
    show_all_touchdowns_tab,
    show_schedule_tab,
    show_analysis_tab,
    show_week_picks_tab
)



def show_public_dashboard(df: pd.DataFrame, season: int, schedule: pd.DataFrame) -> None:
    """Main dashboard view with tabs for different data views."""
    # Initialize database
    init_db()
    
    if df.empty:
        st.warning("No data found for this season or an error occurred.")
        return
    
    # Key Metrics
    all_tds = get_touchdowns(df)
    first_tds = get_first_tds(df)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Games", df['game_id'].nunique())
    with col2:
        st.metric("Total Touchdowns", len(all_tds))
    with col3:
        if not first_tds.empty:
            top_scorer = first_tds['td_player_name'].mode()
            if not top_scorer.empty:
                st.metric("Top First TD Scorer", top_scorer[0])

    st.markdown("---")

    # Tabs - use modular components
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏆 Leaderboard",
        "📝 Week Picks",
        "📋 All Touchdowns", 
        "📅 Weekly Schedule", 
        "📊 Analysis",
        "🚀 First TD of Game"
    ])

    with tab1:
        show_leaderboard_tab()

    with tab2:
        show_week_picks_tab(season)

    with tab3:
        show_all_touchdowns_tab(all_tds)
            
    with tab4:
        show_schedule_tab(schedule)

    with tab5:
        show_analysis_tab(df, season)

    with tab6:
        show_first_td_tab(first_tds)
