"""
Leaderboard Tab - Display player standings and statistics.
"""

import streamlit as st
from database import get_leaderboard
from utils import format_odds, format_implied_probability


def show_leaderboard_tab() -> None:
    """
    Display the cumulative leaderboard tab.
    
    Shows all-time standings with simplified columns:
    - Rank: User position
    - Name: Player name
    - Points: Cumulative points (3 per First TD, 1 per Any Time TD)
    - Record: W-L format
    - ROI: Return on investment percentage
    
    Data is cached for 5 minutes to avoid repeated database queries.
    """
    st.header("🏆 Leaderboard")
    
    leaderboard = get_leaderboard()
    
    if leaderboard:
        # Show current leader prominently
        if len(leaderboard) > 0:
            leader = leaderboard[0]
            total_picks = leader.get('total_picks', 0) or 0
            wins = leader.get('wins', 0) or 0
            total_return = leader.get('total_return', 0) or 0
            roi = ((total_return - total_picks) / total_picks * 100) if total_picks > 0 else 0
            
            st.info(f"**Current Leader:** {leader['name']} — {leader.get('points', 0)} pts ({wins}-{total_picks - wins}) — ROI: {roi:+.1f}%")
        
        # Convert to simplified display format
        rows = []
        for entry in leaderboard:
            total_picks = entry.get('total_picks', 0) or 0
            wins = entry.get('wins', 0) or 0
            total_return = entry.get('total_return', 0) or 0
            
            # Calculate ROI
            roi = ((total_return - total_picks) / total_picks * 100) if total_picks > 0 else 0
            
            rows.append({
                'Rank': len(rows) + 1,
                'Name': entry['name'],
                'Points': entry.get('points', 0) or 0,
                'Record': f"{wins}-{total_picks - wins}",
                'ROI': f"{roi:+.1f}%"
            })

        import pandas as pd
        lb_df = pd.DataFrame(rows)
        
        st.dataframe(
            lb_df,
            width="stretch",
            hide_index=True,
            column_config={
                'Rank': st.column_config.NumberColumn(format="%d", width="small"),
                'Name': st.column_config.TextColumn(width="medium"),
                'Points': st.column_config.NumberColumn(format="%d", width="small"),
                'Record': st.column_config.TextColumn(width="small"),
                'ROI': st.column_config.TextColumn(width="small", help="Return on Investment (assuming $1 per pick)"),
            },
        )
        
        st.caption("**Points:** 3 for First TD, 1 for Any Time TD  •  **ROI:** Assumes $1 per pick at average odds")
    else:
        st.info("No leaderboard data available yet.")
