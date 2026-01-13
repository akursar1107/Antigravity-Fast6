"""
First TD Tab - Display first touchdowns per game.
"""

import streamlit as st
import pandas as pd


def show_first_td_tab(first_tds: pd.DataFrame) -> None:
    """
    Display the First Touchdown leaders tab.
    
    Args:
        first_tds: DataFrame with First TD data containing:
            - Player: Player name
            - Team: Player team
            - Count: Number of games where player scored first TD
            - Games: List of game dates when player scored first TD
    
    Shows players ranked by frequency of scoring the first TD of games,
    providing valuable insights for First TD picking strategy.
    """
    st.header("First Touchdowns per Game")
    st.markdown("This list shows the first touchdown scored in every game of the season.")
    
    if not first_tds.empty:
        display_cols = [
            'week', 'away_team', 'home_team', 'td_player_name', 'posteam', 'qtr', 'desc'
        ]
        valid_cols = [c for c in display_cols if c in first_tds.columns]
        
        first_tds_display = first_tds.sort_values(by=['week', 'game_id'])
        
        st.dataframe(
            first_tds_display[valid_cols],
            width="stretch",
            column_config={
                "week": st.column_config.NumberColumn("Week", format="%d"),
                "away_team": "Away",
                "home_team": "Home",
                "td_player_name": "Player",
                "posteam": "Scoring Team",
                "qtr": "Quarter",
                "desc": "Play Description"
            },
            hide_index=True
        )
    else:
        st.info("No First TDs found.")
