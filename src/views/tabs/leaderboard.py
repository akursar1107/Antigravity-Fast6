"""
Leaderboard Tab - Display player standings and statistics.
"""

import streamlit as st
from utils import get_leaderboard


def show_leaderboard_tab() -> None:
    """Display leaderboard and standings."""
    st.header("🏆 Leaderboard & Standings")
    st.markdown("Cumulative standings throughout the season. Points: 3 for First TD, 1 for Any Time TD.")
    
    leaderboard = get_leaderboard()
    
    if leaderboard:
        # Convert to display format
        rows = []
        for entry in leaderboard:
            rows.append({
                'Rank': len(rows) + 1,
                'User': entry['name'],
                'Picks': entry.get('total_picks', 0) or 0,
                'Wins': entry.get('wins', 0) or 0,
                'Losses': entry.get('losses', 0) or 0,
                'Any Time TD': entry.get('any_time_td_wins', 0) or 0,
                'Points': entry.get('points', 0) or 0,
                'Total Return': f"${entry.get('total_return', 0) or 0:.2f}",
                'Avg Return': f"${entry.get('avg_return', 0) or 0:.2f}",
                'Avg Odds': f"{entry.get('avg_odds', 0) or 0:.0f}"
            })
        
        import pandas as pd
        lb_df = pd.DataFrame(rows)
        
        st.dataframe(
            lb_df,
            width="stretch",
            hide_index=True,
            column_config={
                'Rank': st.column_config.NumberColumn(format="%d"),
                'User': st.column_config.TextColumn(),
                'Picks': st.column_config.NumberColumn(format="%d"),
                'Wins': st.column_config.NumberColumn(format="%d"),
                'Losses': st.column_config.NumberColumn(format="%d"),
                'Any Time TD': st.column_config.NumberColumn(format="%d"),
                'Points': st.column_config.NumberColumn(format="%d"),
            }
        )
    else:
        st.info("No leaderboard data available yet.")
