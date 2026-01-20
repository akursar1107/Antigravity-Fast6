"""
Week Picks Tab - Display picks and results for selected week
"""

import streamlit as st
import pandas as pd
from utils import get_all_weeks, get_all_users, get_user_week_picks, get_result_for_pick


def show_week_picks_tab(season: int) -> None:
    """
    Display the week picks entry and management tab.
    
    Args:
        season: Current NFL season year
    
    Allows users to:
    - Select a week to view picks for
    - Add new picks for the selected week
    - View their existing picks
    - Delete incorrect or duplicate picks
    - See odds and calculated returns for each pick
    
    Picks are automatically validated against schedules to ensure
    games exist and teams are recognized.
    """
    st.header("📝 Weekly Picks & Results")
    
    # Get available weeks
    weeks = get_all_weeks(season)
    
    if not weeks:
        st.info("No weeks recorded yet.")
        return
    
    # Initialize session state for week selection if not exists
    if 'week_picks_selected_week_id' not in st.session_state:
        st.session_state.week_picks_selected_week_id = weeks[0]['id'] if weeks else None
    
    # Initialize session state for user filter if not exists
    if 'week_picks_selected_user_id' not in st.session_state:
        st.session_state.week_picks_selected_user_id = None
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Find index of currently selected week
        try:
            week_index = next(i for i, w in enumerate(weeks) if w['id'] == st.session_state.week_picks_selected_week_id)
        except (StopIteration, KeyError):
            week_index = 0
        
        selected_week_record = st.selectbox(
            "Select Week",
            options=weeks,
            format_func=lambda x: f"Week {x['week']}",
            index=week_index,
            key="public_week_select"
        )
        # Update session state
        st.session_state.week_picks_selected_week_id = selected_week_record['id']
    
    with col2:
        users = get_all_users()
        
        # Find index of currently selected user
        if st.session_state.week_picks_selected_user_id is None:
            user_index = 0
        else:
            try:
                user_index = next(i + 1 for i, u in enumerate(users) if u['id'] == st.session_state.week_picks_selected_user_id)
            except StopIteration:
                user_index = 0
        
        selected_user = st.selectbox(
            "Select Member (optional)",
            options=[None] + users,
            format_func=lambda x: "All Members" if x is None else x['name'],
            index=user_index,
            key="public_member_select"
        )
        # Update session state
        st.session_state.week_picks_selected_user_id = selected_user['id'] if selected_user else None
    
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
                        'Result': '✅ Correct' if result and result['is_correct'] == 1 else ('❌ Incorrect' if result and result['is_correct'] == 0 else '⏳ Pending'),
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
                                'Result': '✅' if result and result['is_correct'] == 1 else ('❌' if result and result['is_correct'] == 0 else '⏳'),
                                'Return': f"${result['actual_return']:.2f}" if result and result['actual_return'] is not None else "$0.00"
                            })
                        
                        picks_df = pd.DataFrame(picks_data)
                        st.dataframe(picks_df, width='stretch', hide_index=True)
            else:
                st.info(f"No picks recorded for Week {selected_week_record['week']}")
