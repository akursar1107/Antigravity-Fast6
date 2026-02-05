"""
Week Picks Tab - Display picks and results for selected week
"""

import streamlit as st
import pandas as pd
from src.database import get_all_weeks, get_all_users, get_user_week_picks, get_result_for_pick
from src.utils.common import ensure_session_state, format_pick_for_display, format_pick_for_display_compact, decode_bytes_to_int


def show_week_picks_tab(season: int, week: int = None) -> None:
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
    st.header("📝 User Weekly Picks & Results")
    

    # Get available weeks and sort numerically
    weeks = get_all_weeks(season)
    for w in weeks:
        w['week'] = decode_bytes_to_int(w['week'])
    weeks = sorted(weeks, key=lambda x: int(x['week']))

    if not weeks:
        st.info("No weeks recorded yet.")
        return

    # Initialize session state using helper
    # If week argument is provided, use it to set default week
    if week is not None:
        # Find the week record with the matching week number
        week_record = next((w for w in weeks if w['week'] == week), None)
        default_week_id = week_record['id'] if week_record else weeks[0]['id']
    else:
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
        week_display = decode_bytes_to_int(selected_week_record['week'])

        if selected_user:
            # Show picks for specific user
            picks = get_user_week_picks(selected_user['id'], week_id)

            if picks:
                st.subheader(f"{selected_user['name']}'s Picks - Week {week_display}")

                picks_data = []
                for pick in picks:
                    result = get_result_for_pick(pick['id'])
                    picks_data.append(format_pick_for_display(pick, result))

                picks_df = pd.DataFrame(picks_data)
                st.dataframe(picks_df, width='stretch', hide_index=True)
            else:
                st.info(f"No picks for {selected_user['name']} in Week {week_display}")
        else:
            # Show all picks for the week in a unified table
            st.subheader(f"All Members' Picks - Week {week_display}")

            all_users = get_all_users()
            all_picks_data = []

            for user in all_users:
                picks = get_user_week_picks(user['id'], week_id)
                for pick in picks:
                    result = get_result_for_pick(pick['id'])
                    pick_display = format_pick_for_display(pick, result)
                    pick_display['Member'] = user['name']  # Add member name
                    all_picks_data.append(pick_display)

            if all_picks_data:
                # Create unified dataframe
                all_picks_df = pd.DataFrame(all_picks_data)
                
                # Reorder columns to put Member first
                cols = ['Member'] + [col for col in all_picks_df.columns if col != 'Member']
                all_picks_df = all_picks_df[cols]
                
                # Quick stats at top
                total_picks = len(all_picks_df)
                wins = all_picks_df['Result'].str.contains('✅', na=False).sum()
                losses = all_picks_df['Result'].str.contains('❌', na=False).sum()
                pending = total_picks - wins - losses
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Picks", total_picks)
                with col2:
                    st.metric("Wins", f"{wins} ✅")
                with col3:
                    st.metric("Losses", f"{losses} ❌")
                with col4:
                    st.metric("Pending", f"{pending} ⏳")
                
                st.markdown("---")
                
                # Display table
                st.dataframe(all_picks_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"No picks recorded for Week {week_display}")
