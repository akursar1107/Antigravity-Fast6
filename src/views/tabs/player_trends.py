"""
Player Trends Tab - Rolling first TD rates and player performance.
"""

import streamlit as st
import pandas as pd
from utils.nfl_data import load_rosters


def show_player_trends_tab(pbp_df: pd.DataFrame, season: int, roster_df: pd.DataFrame = None) -> None:
    """Display player rolling stats, trends, and performance analysis."""
    
    st.header("📈 Player Trends & Performance")
    
    try:
        # Load rosters if not provided
        if roster_df is None:
            with st.spinner("Loading rosters..."):
                roster_df = load_rosters(season)
        
        if pbp_df.empty:
            st.warning("⚠️ No play-by-play data available for this season.")
            return
        
        # Player selector
        available_players = sorted(pbp_df['td_player_name'].dropna().unique().tolist())
        if not available_players:
            st.warning("⚠️ No touchdown scorers found in data.")
            return
        
        col1, col2 = st.columns(2)
        with col1:
            selected_player = st.selectbox(
                "Select Player",
                options=available_players,
                key="player_trends_select"
            )
        
        with col2:
            window_size = st.radio(
                "Rolling Window",
                options=[4, 8, 12],
                index=1,
                horizontal=True,
                help="Games to average over"
            )
        
        if not selected_player:
            st.info("Select a player to view trends.")
            return
        
        st.markdown("---")
        
        # Player summary
        player_games = pbp_df[pbp_df['td_player_name'] == selected_player]
        if not player_games.empty:
            first_td_count = len(player_games)
            st.metric(f"{selected_player} - Total First TDs", first_td_count)
        
        st.success(f"✅ Data loaded for {selected_player}")
    
    except Exception as e:
        st.error(f"Error loading player trends: {str(e)}")
        import traceback
        st.write(traceback.format_exc())
