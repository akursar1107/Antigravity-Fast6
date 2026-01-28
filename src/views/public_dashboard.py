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
    show_leaderboard_tab,
    show_schedule_tab,
    show_week_picks_tab,
    show_team_analysis_tab,
    show_player_performance_tab,
    show_roi_trends_tab,
    show_power_rankings_tab,
    show_defense_matchups_tab
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

    # Load rosters once for tabs
    with st.spinner("Loading rosters..."):
        roster_df = load_rosters(season)

    # Dashboard view selector - responsive to all screen sizes
    view_options = [
        "🏆 Leaderboard",
        "📝 User Weekly Picks",
        "🌟 Player Performance",
        "💰 ROI & Profitability",
        "⚡ Power Rankings",
        "🛡️ Defense Matchups",
        "📅 NFL Schedule",
        "🧩 Team Analysis"
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
        # Default to current week if possible
        import datetime
        current_week = None
        if 'week' in df.columns:
            try:
                # Try to get the latest week with data for the current season
                current_week = int(df[df['season'] == season]['week'].max())
            except Exception:
                current_week = None
        show_week_picks_tab(season, week=current_week) if current_week else show_week_picks_tab(season)
    
    elif selected_view == view_options[2]:
        show_player_performance_tab(season)
    
    elif selected_view == view_options[3]:
        show_roi_trends_tab(season)
    
    elif selected_view == view_options[4]:
        show_power_rankings_tab(season)
    
    elif selected_view == view_options[5]:
        show_defense_matchups_tab(season)
    
    elif selected_view == view_options[6]:
        show_schedule_tab(schedule)

    elif selected_view == view_options[7]:
        try:
            show_team_analysis_tab(df, season)
        except Exception as e:
            st.error(f"Error in Team Analysis: {str(e)}")
            import traceback
            st.write(traceback.format_exc())


