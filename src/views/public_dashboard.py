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
    
    # Key Metrics - Simplified and focused
    from database import get_leaderboard
    leaderboard = get_leaderboard()
    
    if leaderboard and len(leaderboard) > 0:
        leader = leaderboard[0]
        total_picks = leader.get('total_picks', 0) or 0
        wins = leader.get('wins', 0) or 0
        total_return = leader.get('total_return', 0) or 0
        roi = ((total_return - total_picks) / total_picks * 100) if total_picks > 0 else 0
        
        # Show current leader prominently
        st.success(f"**🏆 Current Leader:** {leader['name']} — {leader.get('points', 0)} points ({wins}-{total_picks - wins}) — ROI: {roi:+.1f}%")
    
    # Compact season stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Games", df['game_id'].nunique())
    with col2:
        all_tds = get_touchdowns(df)
        st.metric("Total TDs", len(all_tds))
    with col3:
        if leaderboard:
            st.metric("Players", len(leaderboard))
    with col4:
        if leaderboard:
            total_pool_picks = sum(entry.get('total_picks', 0) or 0 for entry in leaderboard)
            st.metric("Picks Made", total_pool_picks)

    st.markdown("---")

    # Load rosters once for tabs
    with st.spinner("Loading rosters..."):
        roster_df = load_rosters(season)

    # Initialize tab selection in session state
    if 'active_dashboard_tab' not in st.session_state:
        st.session_state.active_dashboard_tab = "🏆 Leaderboard"
    
    # Tab selection with session state persistence
    tab_options = [
        "🏆 Leaderboard",
        "📝 My Picks",
        "📅 Schedule",
        "📊 Analytics",
        "🧩 Team Stats"
    ]
    
    # Create columns for tab-like buttons
    cols = st.columns(len(tab_options))
    for idx, (col, tab_name) in enumerate(zip(cols, tab_options)):
        with col:
            # Style active tab differently
            if st.session_state.active_dashboard_tab == tab_name:
                if st.button(tab_name, key=f"tab_{idx}", use_container_width=True, type="primary"):
                    st.session_state.active_dashboard_tab = tab_name
                    st.rerun()
            else:
                if st.button(tab_name, key=f"tab_{idx}", use_container_width=True):
                    st.session_state.active_dashboard_tab = tab_name
                    st.rerun()
    
    st.markdown("---")
    
    # Render the active tab content
    if st.session_state.active_dashboard_tab == "🏆 Leaderboard":
        show_leaderboard_tab()
    
    elif st.session_state.active_dashboard_tab == "📝 My Picks":
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
    
    elif st.session_state.active_dashboard_tab == "📅 Schedule":
        show_schedule_tab(schedule)

    elif st.session_state.active_dashboard_tab == "📊 Analytics":
        # Initialize analytics sub-tab in session state
        if 'active_analytics_subtab' not in st.session_state:
            st.session_state.active_analytics_subtab = "Player Performance"
        
        # Sub-tab selector for analytics
        analytics_subtab = st.radio(
            "Analytics View",
            ["Player Performance", "ROI & Profitability", "Power Rankings", "Defense Matchups"],
            horizontal=True,
            key="analytics_subtab_selector",
            index=["Player Performance", "ROI & Profitability", "Power Rankings", "Defense Matchups"].index(st.session_state.active_analytics_subtab)
        )
        st.session_state.active_analytics_subtab = analytics_subtab
        
        st.markdown("---")
        
        if analytics_subtab == "Player Performance":
            show_player_performance_tab(season)
        elif analytics_subtab == "ROI & Profitability":
            show_roi_trends_tab(season)
        elif analytics_subtab == "Power Rankings":
            show_power_rankings_tab(season)
        else:  # Defense Matchups
            show_defense_matchups_tab(season)
    
    elif st.session_state.active_dashboard_tab == "🧩 Team Stats":
        try:
            show_team_analysis_tab(df, season)
        except Exception as e:
            st.error(f"Error in Team Analysis: {str(e)}")
            import traceback
            st.write(traceback.format_exc())


