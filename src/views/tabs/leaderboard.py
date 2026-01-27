"""
Leaderboard Tab - Display player standings and statistics.
"""

import streamlit as st
from utils import get_leaderboard, format_odds, format_implied_probability


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
    - Win %: Win rate (First TD wins / total picks)
    - Avg Odds: Average odds of picks
    - Implied %: Average implied probability from odds
    
    Data is cached for 5 minutes to avoid repeated database queries.
    """
    st.header("🏆 Leaderboard & Standings")
    st.markdown("Cumulative standings throughout the season. Points: 3 for First TD, 1 for Any Time TD.")
    
    leaderboard = get_leaderboard()
    
    if leaderboard:
        # Convert to display format
        rows = []
        for entry in leaderboard:
            total_picks = entry.get('total_picks', 0) or 0
            wins = entry.get('wins', 0) or 0
            avg_odds = entry.get('avg_odds', 0) or 0
            
            # Calculate win rate
            win_rate = (wins / total_picks * 100) if total_picks > 0 else 0
            
            rows.append({
                'Rank': len(rows) + 1,
                'User': entry['name'],
                'Picks': total_picks,
                'First TD': wins,
                'Any Time TD': entry.get('any_time_td_wins', 0) or 0,
                'Points': entry.get('points', 0) or 0,
                'Win %': f"{win_rate:.1f}%",
                'Avg Odds': format_odds(avg_odds) if avg_odds else "N/A",
                'Implied %': format_implied_probability(avg_odds) if avg_odds else "N/A",
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
                'Win %': st.column_config.TextColumn(),
                'Avg Odds': st.column_config.TextColumn(),
                'Implied %': st.column_config.TextColumn(help="Break-even probability based on average odds"),
            },
            use_container_width=True,
        )
        
        # Add explanation
        st.caption("**Implied %** = break-even probability based on average odds. Win % > Implied % indicates profitable picking.")
        
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
