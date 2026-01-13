"""
Leaderboard Tab - Display player standings and statistics.
"""

import streamlit as st
from utils import get_leaderboard


def show_leaderboard_tab() -> None:
    """
    Display the cumulative leaderboard tab.
    
    Shows all-time standings with columns:
    - Rank: User position
    - User: Player name
    - Picks: Total picks made
    - First TD: First TD correct predictions
    - Any Time TD: Correct Any Time TD picks
    - Points: Cumulative points (3 per First TD, 1 per Any Time TD)
    
    Data is cached for 5 minutes to avoid repeated database queries.
    """
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
                'First TD': entry.get('wins', 0) or 0,
                'Any Time TD': entry.get('any_time_td_wins', 0) or 0,
                'Points': entry.get('points', 0) or 0,
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
                'First TD': st.column_config.NumberColumn(format="%d"),
                'Any Time TD': st.column_config.NumberColumn(format="%d"),
                'Points': st.column_config.NumberColumn(format="%d"),
            },
            use_container_width=True,
        )
        
        # Center the dataframe content using CSS
        st.markdown("""
        <style>
        [data-testid="dataframe"] {
            margin: 0 auto;
        }
        [data-testid="dataframe"] td, [data-testid="dataframe"] th {
            text-align: center !important;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.info("No leaderboard data available yet.")
