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
    st.caption("Group standings, total picks, first TD wins, and performance metrics. Points: 3 for First TD, 1 for Any Time TD.")
    
    leaderboard = get_leaderboard()
    
    if leaderboard:
        # Convert to display format and calculate ROI
        rows = []
        for entry in leaderboard:
            total_picks = entry.get('total_picks', 0) or 0
            wins = entry.get('wins', 0) or 0
            avg_odds = entry.get('avg_odds', 0) or 0
            total_return = entry.get('total_return', 0) or 0
            
            # Calculate metrics
            win_rate = (wins / total_picks * 100) if total_picks > 0 else 0
            roi = ((total_return - total_picks) / total_picks * 100) if total_picks > 0 else 0
            
            rows.append({
                'Rank': len(rows) + 1,
                'User': entry['name'],
                'Picks': total_picks,
                'First TD': wins,
                'Any Time TD': entry.get('any_time_td_wins', 0) or 0,
                'Points': entry.get('points', 0) or 0,
                'Win %': f"{win_rate:.1f}%",
                'ROI': f"{roi:+.1f}%",
                'Avg Odds': format_odds(avg_odds) if avg_odds else "N/A",
                'Implied %': format_implied_probability(avg_odds) if avg_odds else "N/A",
                'Raw ROI': roi # For podium sorting/display
            })
        
        # --- PODIUM SECTION ---
        if len(rows) >= 1:
            st.markdown("<br>", unsafe_allow_html=True)
            cols = st.columns([1, 1.2, 1])
            
            # Sort for podium (already sorted by points from DB, but let's be sure)
            podium_data = sorted(rows, key=lambda x: (int(x['Points']), float(x['Raw ROI'])), reverse=True)
            
            # Podium Styles
            st.markdown("""
                <style>
                .podium-card {
                    background: rgba(45, 55, 72, 0.4);
                    border-radius: 15px;
                    padding: 20px;
                    text-align: center;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
                    transition: transform 0.3s ease;
                }
                .podium-card:hover {
                    transform: translateY(-5px);
                    border-color: #228B22;
                }
                .rank-label {
                    font-size: 0.8rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    color: #A0AEC0;
                    margin-bottom: 5px;
                }
                .user-name {
                    font-size: 1.25rem;
                    font-weight: 700;
                    color: #F7FAFC;
                    margin-bottom: 10px;
                }
                .points-value {
                    font-size: 2rem;
                    font-weight: 800;
                    color: #228B22;
                    font-family: 'Roboto Mono', monospace;
                }
                .winner-accent {
                    color: #FFD700 !important;
                }
                .roi-badge {
                    display: inline-block;
                    padding: 2px 10px;
                    border-radius: 10px;
                    font-size: 0.85rem;
                    font-weight: 600;
                    margin-top: 8px;
                }
                .roi-positive { background: rgba(34, 139, 34, 0.2); color: #48bb78; border: 1px solid rgba(34, 139, 34, 0.3); }
                .roi-negative { background: rgba(229, 62, 62, 0.2); color: #fc8181; border: 1px solid rgba(229, 62, 62, 0.3); }
                </style>
            """, unsafe_allow_html=True)
            
            # 2nd Place
            with cols[0]:
                if len(podium_data) >= 2:
                    user = podium_data[1]
                    roi_class = "roi-positive" if float(user['Raw ROI']) >= 0 else "roi-negative"
                    st.markdown(f"""
                        <div class="podium-card" style="margin-top: 20px;">
                            <div class="rank-label">2nd Place</div>
                            <div class="user-name">{user['User']}</div>
                            <div class="points-value">{user['Points']}</div>
                            <div class="roi-badge {roi_class}">{user['ROI']} ROI</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            # 1st Place
            with cols[1]:
                user = podium_data[0]
                roi_class = "roi-positive" if float(user['Raw ROI']) >= 0 else "roi-negative"
                st.markdown(f"""
                    <div class="podium-card" style="border: 2px solid #228B22; background: rgba(45, 55, 72, 0.7); scale: 1.1;">
                        <div class="rank-label winner-accent">🏆 Winner</div>
                        <div class="user-name" style="font-size: 1.5rem;">{user['User']}</div>
                        <div class="points-value" style="font-size: 2.5rem; color: #FFD700;">{user['Points']}</div>
                        <div class="roi-badge {roi_class}">{user['ROI']} ROI</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # 3rd Place
            with cols[2]:
                if len(podium_data) >= 3:
                    user = podium_data[2]
                    roi_class = "roi-positive" if float(user['Raw ROI']) >= 0 else "roi-negative"
                    st.markdown(f"""
                        <div class="podium-card" style="margin-top: 40px;">
                            <div class="rank-label">3rd Place</div>
                            <div class="user-name">{user['User']}</div>
                            <div class="points-value">{user['Points']}</div>
                            <div class="roi-badge {roi_class}">{user['ROI']} ROI</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<br><br>", unsafe_allow_html=True)

        import pandas as pd
        lb_df = pd.DataFrame(rows).drop(columns=['Raw ROI'])
        
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
                'ROI': st.column_config.TextColumn(help="Return on Investment (assuming $1 per pick)"),
                'Avg Odds': st.column_config.TextColumn(),
                'Implied %': st.column_config.TextColumn(help="Break-even probability based on average odds"),
            },
        )
        
        # Add explanation
        st.caption("**Implied %** = break-even probability based on average odds. Win % > Implied % indicates profitable picking.")
    else:
        st.info("No leaderboard data available yet.")
