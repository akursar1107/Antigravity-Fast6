"""
Week Picks Tab - Display picks and results for selected week
"""

import streamlit as st
import pandas as pd
from utils import get_all_weeks, get_all_users, get_user_week_picks, get_result_for_pick


def show_week_picks_tab(season: int) -> None:
    """Display picks for a selected week."""
    st.header("📝 Weekly Picks & Results")
    
    # Get available weeks
    weeks = get_all_weeks(season)
    
    if not weeks:
        st.info("No weeks recorded yet.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_week_record = st.selectbox(
            "Select Week",
            options=weeks,
            format_func=lambda x: f"Week {x['week']}",
            key="public_week_select"
        )
    
    with col2:
        users = get_all_users()
        selected_user = st.selectbox(
            "Select Member (optional)",
            options=[None] + users,
            format_func=lambda x: "All Members" if x is None else x['name'],
            key="public_member_select"
        )
    
    if selected_week_record:
        week_id = selected_week_record['id']
        
        if selected_user:
            # Show picks for specific user
            picks = get_user_week_picks(selected_user['id'], week_id)
            
            if picks:
                st.subheader(f"{selected_user['name']}'s Picks - Week {selected_week_record['week']}")
                
                picks_data = []
                for pick in picks:
                    result = get_result_for_pick(pick['id'])
                    # Format odds as string (e.g., +1500) if available
                    odds_val = pick.get('odds')
                    odds_str = (
                        f"+{int(odds_val)}" if isinstance(odds_val, (int, float)) and odds_val >= 0 else
                        (str(int(odds_val)) if isinstance(odds_val, (int, float)) else "-")
                    )
                    theo_ret = pick.get('theoretical_return')
                    picks_data.append({
                        'Team': pick['team'],
                        'Player': pick['player_name'],
                        'Odds': odds_str,
                        'Theo Return': f"${theo_ret:.2f}" if isinstance(theo_ret, (int, float)) else "$0.00",
                        'Result': '✅ Correct' if result and result['is_correct'] else ('❌ Incorrect' if result and result['is_correct'] is False else '⏳ Pending'),
                        'Return': f"${result['actual_return']:.2f}" if result and result['actual_return'] is not None else "$0.00"
                    })
                
                picks_df = pd.DataFrame(picks_data)
                st.dataframe(picks_df, width='stretch', hide_index=True)
            else:
                st.info(f"No picks for {selected_user['name']} in Week {selected_week_record['week']}")
        else:
            # Show all picks for the week
            st.subheader(f"All Members' Picks - Week {selected_week_record['week']}")
            
            all_users = get_all_users()
            picks_by_user = {}
            
            for user in all_users:
                picks = get_user_week_picks(user['id'], week_id)
                if picks:
                    picks_by_user[user['name']] = picks
            
            if picks_by_user:
                for member_name in sorted(picks_by_user.keys()):
                    with st.expander(f"👤 {member_name}", expanded=True):
                        picks = picks_by_user[member_name]
                        picks_data = []
                        
                        for pick in picks:
                            result = get_result_for_pick(pick['id'])
                            odds_val = pick.get('odds')
                            odds_str = (
                                f"+{int(odds_val)}" if isinstance(odds_val, (int, float)) and odds_val >= 0 else
                                (str(int(odds_val)) if isinstance(odds_val, (int, float)) else "-")
                            )
                            theo_ret = pick.get('theoretical_return')
                            picks_data.append({
                                'Team': pick['team'],
                                'Player': pick['player_name'],
                                'Odds': odds_str,
                                'Theo Return': f"${theo_ret:.2f}" if isinstance(theo_ret, (int, float)) else "$0.00",
                                'Result': '✅' if result and result['is_correct'] else ('❌' if result and result['is_correct'] is False else '⏳'),
                                'Return': f"${result['actual_return']:.2f}" if result and result['actual_return'] is not None else "$0.00"
                            })
                        
                        picks_df = pd.DataFrame(picks_data)
                        st.dataframe(picks_df, width='stretch', hide_index=True)
            else:
                st.info(f"No picks recorded for Week {selected_week_record['week']}")
