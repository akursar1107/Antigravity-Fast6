"""
Public Dashboard - Read-only views for all users.
Displays first TD analysis, leaderboard, picks history, weekly schedule, and Phase 2 analytics.
Data sourced from NFL API and SQLite database.
"""

import streamlit as st
import pandas as pd
from utils.nfl_data import get_touchdowns, get_first_tds, load_rosters
from utils import init_db
from views.tabs import (
    show_first_td_tab,
    show_leaderboard_tab,
    show_all_touchdowns_tab,
    show_schedule_tab,
    show_analysis_tab,
    show_week_picks_tab
)
from views.tabs.player_trends import show_player_trends_tab
from views.tabs.team_trends import show_team_trends_tab
from views.tabs.user_stats import show_user_stats_tab
from views.tabs.performance_breakdown import show_performance_breakdown_tab



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

    # Load rosters once for tabs
    with st.spinner("Loading rosters..."):
        roster_df = load_rosters(season)

    # Dashboard view selector - responsive to all screen sizes
    view_options = [
        "🏆 Leaderboard",
        "📝 Week Picks",
        "📋 All Touchdowns", 
        "📅 Weekly Schedule", 
        "📊 Analysis",
        "🚀 First TD of Game",
        "📈 Player Trends",
        "🏈 Team Trends",
        "👤 User Stats",
        "📊 Performance Breakdown"
    ]
    
    selected_view = st.selectbox(
        "Select Dashboard View",
        options=view_options,
        index=0,
        key="dashboard_view_selector"
    )
    
    st.markdown("---")
    
    # Render selected view
    if selected_view == view_options[0]:
        show_leaderboard_tab()
    
    elif selected_view == view_options[1]:
        show_week_picks_tab(season)
    
    elif selected_view == view_options[2]:
        show_all_touchdowns_tab(all_tds)
    
    elif selected_view == view_options[3]:
        show_schedule_tab(schedule)
    
    elif selected_view == view_options[4]:
        show_analysis_tab(df, season)
    
    elif selected_view == view_options[5]:
        show_first_td_tab(first_tds)
    
    elif selected_view == view_options[6]:
        try:
            show_player_trends_tab(df, season, roster_df)
        except Exception as e:
            st.error(f"Error in Player Trends: {str(e)}")
            import traceback
            st.write(traceback.format_exc())
    
    elif selected_view == view_options[7]:
        try:
            show_team_trends_tab(first_tds, season)
        except Exception as e:
            st.error(f"Error in Team Trends: {str(e)}")
            import traceback
            st.write(traceback.format_exc())
    
    elif selected_view == view_options[8]:
        try:
            show_user_stats_tab(season)
        except Exception as e:
            st.error(f"Error in User Stats: {str(e)}")
            import traceback
            st.write(traceback.format_exc())
    
    elif selected_view == view_options[9]:
        try:
            show_performance_breakdown_tab(season)
        except Exception as e:
            st.error(f"Error in Performance Breakdown: {str(e)}")
            import traceback
            st.write(traceback.format_exc())
