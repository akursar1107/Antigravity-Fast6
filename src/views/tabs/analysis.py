"""
Analysis Tab - Display first touchdown analysis and statistics
"""

import streamlit as st
import pandas as pd
from utils.nfl_data import get_first_tds, load_rosters
from utils.analytics import (
    get_team_first_td_counts, 
    get_player_first_td_counts, 
    get_position_first_td_counts
)


def show_analysis_tab(df: pd.DataFrame, season: int) -> None:
    """Display analysis: team rankings, player leaderboard, position stats."""
    st.header("First Touchdown Analysis")
    
    if df.empty:
        st.info("No data available for analysis.")
        return
    
    # Calculate first TDs for current filtered data
    analyzed_first_tds = get_first_tds(df)
    
    col_a1, col_a2 = st.columns(2)
    
    with col_a1:
        st.subheader("Team Rankings")
        team_stats = get_team_first_td_counts(analyzed_first_tds)
        if not team_stats.empty:
            team_stats = team_stats.sort_values('First TDs', ascending=False)
            st.dataframe(
                team_stats, 
                column_config={
                    "Team": st.column_config.TextColumn("Team"),
                    "First TDs": st.column_config.ProgressColumn(
                        "First TDs", 
                        format="%d", 
                        min_value=0, 
                        max_value=int(team_stats['First TDs'].max())
                    )
                },
                hide_index=True,
                width="stretch"
            )
        else:
            st.caption("No data.")

    with col_a2:
        st.subheader("Player Leaderboard")
        player_stats = get_player_first_td_counts(analyzed_first_tds)
        if not player_stats.empty:
            player_stats = player_stats.sort_values('First TDs', ascending=False)
            top_players = player_stats.head(20)
            st.bar_chart(top_players.set_index('Player'))
        else:
            st.caption("No data.")
    
    st.divider()
    
    st.subheader("First TDs by Position")
    with st.spinner("Analyzing positions..."):
        roster_for_stats = load_rosters(season)
        pos_stats = get_position_first_td_counts(analyzed_first_tds, roster_for_stats)
        
    if not pos_stats.empty:
        pos_stats = pos_stats.sort_values('First TDs', ascending=False)
        st.bar_chart(pos_stats.set_index('Position'))
    else:
        st.caption("No position data available (could not link IDs).")
