"""
Week Picks Tab - Display picks and results for selected week
"""

import streamlit as st
import pandas as pd
from utils import get_all_weeks, get_all_users, get_user_week_picks, get_result_for_pick
from utils.common import ensure_session_state, format_pick_for_display, format_pick_for_display_compact


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
    
    # Initialize session state using helper
    default_week_id = weeks[0]['id'] if weeks else None
    ensure_session_state('week_picks_selected_week_id', default_week_id)
    ensure_session_state('week_picks_selected_user_id', None)
    
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
                    picks_data.append(format_pick_for_display(pick, result))
                
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
                            # Use compact format for space efficiency in expanders
                            picks_data.append(format_pick_for_display_compact(pick, result))
                        
                        picks_df = pd.DataFrame(picks_data)
                        st.dataframe(picks_df, width='stretch', hide_index=True)
            else:
                st.info(f"No picks recorded for Week {selected_week_record['week']}")
