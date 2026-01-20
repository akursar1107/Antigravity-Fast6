"""
Shared admin utilities and helpers.
Common functions used across admin tabs.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
from utils import get_all_weeks, get_all_users, get_user_stats, get_user_all_picks, get_result_for_pick, add_result


def get_season_and_week_selectors(season: int, seasons_list: List[int], key_prefix: str = "") -> tuple:
    """
    Create standardized season and week selectors for admin interface.
    
    Args:
        season: Default/current season to display
        seasons_list: List of available seasons to select from
        key_prefix: Prefix for Streamlit widget keys (prevents collisions)
    
    Returns:
        tuple: (selected_season: int, selected_week: Optional[int])
            - selected_season: Selected NFL season year
            - selected_week: Selected week number or None if "All Weeks" selected
    
    Creates two columns with:
    - Season input: Number input for year selection (2000-2100)
    - Week selector: Dropdown for week selection with "All Weeks" option
    
    Used consistently across admin tabs for unified filtering.
    """
    col1, col2 = st.columns(2)
    
    with col1:
        selected_season = st.number_input(
            "Season",
            value=season,
            min_value=2000,
            max_value=2100,
            step=1,
            key=f"season_{key_prefix}"
        )
    
    with col2:
        # Get all weeks for this season
        all_weeks = get_all_weeks()
        season_weeks = [w for w in all_weeks if w['season'] == selected_season]
        week_options = ["All Weeks"] + [f"Week {w['week']}" for w in season_weeks]
        
        selected_week_str = st.selectbox(
            "Week",
            options=week_options,
            key=f"week_{key_prefix}",
            index=0
        )
        
        selected_week = None if selected_week_str == "All Weeks" else int(selected_week_str.split()[1])
    
    return selected_season, selected_week


def format_odds(odds: Optional[float]) -> str:
    """
    Format American odds for display.
    
    Args:
        odds: American odds as float/int or None
    
    Returns:
        str: Formatted odds string (e.g., "-110", "+150", "N/A")
    
    Handles None values by returning "N/A".
    Converts float odds to integer representation.
    """
    if odds is None:
        return "N/A"
    if odds > 0:
        return f"+{int(odds)}"
    return str(int(odds))


def format_currency(value: Optional[float]) -> str:
    """Format value as currency."""
    if value is None or (isinstance(value, float) and value == 0.0):
        return "N/A"
    return f"${float(value):.2f}"


def show_pick_with_result_editor(pick: Dict, existing_result: Optional[Dict] = None) -> Dict:
    """
    Display a pick with editable result fields.
    Returns dict with 'is_correct', 'any_time_td', 'actual_return' keys.
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        is_correct = st.selectbox(
            "First TD (Win/Loss)",
            options=[None, True, False],
            format_func=lambda x: "Pending" if x is None else ("✅ Correct" if x else "❌ Incorrect"),
            index=0 if (existing_result is None or existing_result.get('is_correct') is None) 
                  else (1 if existing_result['is_correct'] else 2),
            key=f"result_{pick['id']}"
        )
    
    with col2:
        any_time_td = st.checkbox(
            "Any Time TD?",
            value=(existing_result.get('any_time_td') if existing_result else False),
            key=f"any_time_td_{pick['id']}"
        )
    
    with col3:
        theo_ret = pick.get('theoretical_return', 0)
        actual_return = st.number_input(
            "Return ($)",
            value=float(existing_result['actual_return']) if (existing_result and existing_result.get('actual_return')) else 0.0,
            key=f"return_{pick['id']}"
        )
    
    return {
        'is_correct': is_correct,
        'any_time_td': any_time_td,
        'actual_return': actual_return
    }


def show_maintenance_section() -> None:
    """Display maintenance tools for pick deduplication."""
    st.markdown("---")
    st.subheader("Maintenance")
    
    from utils import dedupe_picks_for_user_week, create_unique_picks_index, dedupe_all_picks, get_all_users
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Initialize session state for maintenance user selection
        if 'maintenance_selected_user_id' not in st.session_state:
            all_users_list = get_all_users()
            st.session_state.maintenance_selected_user_id = all_users_list[0]['id'] if all_users_list else None
        
        users_list = get_all_users()
        # Find index of currently selected user
        try:
            user_index = next(i for i, u in enumerate(users_list) if u['id'] == st.session_state.maintenance_selected_user_id)
        except StopIteration:
            user_index = 0
        
        selected_user = st.selectbox("Select User", users_list, format_func=lambda x: x['name'], index=user_index, key="maintenance_user")
        # Update session state
        st.session_state.maintenance_selected_user_id = selected_user['id']
        
        # Initialize session state for maintenance week selection
        if 'maintenance_selected_week_id' not in st.session_state:
            all_weeks_list = get_all_weeks()
            st.session_state.maintenance_selected_week_id = all_weeks_list[0]['id'] if all_weeks_list else None
        
        weeks_list = get_all_weeks()
        # Find index of currently selected week
        try:
            week_index = next(i for i, w in enumerate(weeks_list) if w['id'] == st.session_state.maintenance_selected_week_id)
        except StopIteration:
            week_index = 0
        
        selected_week = st.selectbox("Select Week", weeks_list, 
                                     format_func=lambda x: f"S{x['season']}W{x['week']}", index=week_index, key="maintenance_week")
        # Update session state
        st.session_state.maintenance_selected_week_id = selected_week['id']
        
        if st.button("🧹 Remove Duplicates for User/Week"):
            try:
                summary = dedupe_picks_for_user_week(selected_user['id'], selected_week['id'])
                st.success(f"Removed {summary['duplicates_removed']} duplicates. Kept {summary['unique_kept']} unique.")
            except Exception as e:
                st.error(f"Failed: {e}")
    
    with col2:
        st.write("**Global Maintenance**")
        
        if st.button("🔒 Create Unique Index"):
            ok = create_unique_picks_index()
            if ok:
                st.success("Unique index created or already exists.")
            else:
                st.warning("Could not create index. Remove duplicates first.")
        
        if st.button("🧹 Full Database Dedupe"):
            try:
                summary = dedupe_all_picks()
                st.success(f"Removed {summary['duplicates_removed']} duplicates globally.")
            except Exception as e:
                st.error(f"Failed: {e}")


def show_stats_tab() -> None:
    """Display member statistics and quick edit interface."""
    st.header("📊 Member Statistics")
    
    users = get_all_users()
    if not users:
        st.warning("No members yet.")
        return
    
    selected_stat_user = st.selectbox(
        "Select Member",
        options=users,
        format_func=lambda x: x['name'],
        key="stat_user_select"
    )
    
    stats = get_user_stats(selected_stat_user['id'])
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Picks", stats['total_picks'] or 0)
        
        with col2:
            st.metric("Wins", stats['wins'] or 0)
        
        with col3:
            st.metric("Losses", stats['losses'] or 0)
        
        with col4:
            st.metric("ROI", f"${stats['total_return'] or 0:.2f}")
        
        # Win percentage
        total = (stats['wins'] or 0) + (stats['losses'] or 0)
        if total > 0:
            win_pct = (stats['wins'] / total) * 100
            st.metric("Win %", f"{win_pct:.1f}%")

    # Quick edit table for all picks of selected user
    st.markdown("---")
    st.subheader("Quick Edit: All Picks for Member")
    all_picks = get_user_all_picks(selected_stat_user['id'])
    if all_picks:
        rows = []
        for p in all_picks:
            res = get_result_for_pick(p['id'])
            status = (
                "Pending" if not res or res['is_correct'] is None else
                ("Correct" if res['is_correct'] else "Incorrect")
            )
            rtn = float(res['actual_return']) if res and res['actual_return'] is not None else 0.0
            odds_val = p.get('odds')
            odds_str = (
                f"+{int(odds_val)}" if isinstance(odds_val, (int, float)) and odds_val >= 0 else
                (str(int(odds_val)) if isinstance(odds_val, (int, float)) else "-")
            )
            theo_ret = p.get('theoretical_return')
            rows.append({
                'Pick ID': p['id'],
                'Season': p['season'],
                'Week': p['week'],
                'Team': p['team'],
                'Player': p['player_name'],
                'Odds': odds_str,
                'Theo Return ($)': float(theo_ret) if isinstance(theo_ret, (int, float)) else 0.0,
                'Result': status,
                'Return ($)': rtn
            })

        edit_df = pd.DataFrame(rows)
        edited = st.data_editor(
            edit_df,
            hide_index=True,
            num_rows="fixed",
            disabled=False,
            column_config={
                'Pick ID': st.column_config.Column(disabled=True),
                'Season': st.column_config.Column(disabled=True),
                'Week': st.column_config.Column(disabled=True),
                'Team': st.column_config.Column(disabled=True),
                'Player': st.column_config.Column(disabled=True),
                'Odds': st.column_config.Column(disabled=True),
                'Theo Return ($)': st.column_config.NumberColumn(format='$%.2f', min_value=0.0, step=0.1, disabled=True),
                'Result': st.column_config.SelectboxColumn(options=["Pending", "Correct", "Incorrect"]),
                'Return ($)': st.column_config.NumberColumn(format='$%.2f', min_value=0.0, step=0.1)
            },
            key="user_picks_editor"
        )

        if st.button("💾 Save All Changes", key="save_all_changes_btn"):
            try:
                for _, r in edited.iterrows():
                    res_val = r['Result']
                    is_correct = None if res_val == 'Pending' else (res_val == 'Correct')
                    actual_ret = float(r['Return ($)']) if is_correct else 0.0
                    add_result(
                        pick_id=int(r['Pick ID']),
                        actual_scorer=str(r['Player']),
                        is_correct=is_correct,
                        actual_return=actual_ret
                    )
                st.success("All changes saved.")
                st.rerun()
            except Exception as e:
                st.error(f"Save failed: {e}")
    else:
        st.info("No picks found for this member.")
