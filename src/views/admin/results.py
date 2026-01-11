"""
Results Tab - Manually update game results and manage picks
"""

import streamlit as st
import config
from utils import (
    get_all_weeks, get_all_users, get_user_week_picks, 
    get_result_for_pick, add_result, delete_pick,
    dedupe_picks_for_user_week, create_unique_picks_index,
    dedupe_all_picks, clear_grading_results
)


def show_results_tab(season: int) -> None:
    """Display the results update interface."""
    st.header("✅ Update Game Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        available_weeks = get_all_weeks(season)
        selected_week_record = st.selectbox(
            "Select Week",
            options=available_weeks,
            format_func=lambda x: f"Season {x['season']}, Week {x['week']}",
            key="result_week_select"
        )
    
    with col2:
        available_users = get_all_users()
        selected_result_user = st.selectbox(
            "Select Member",
            options=available_users,
            format_func=lambda x: x['name'],
            key="result_user_select"
        )
    
    if selected_week_record and selected_result_user:
        # Get picks for this user/week
        picks = get_user_week_picks(selected_result_user['id'], selected_week_record['id'])
        
        if picks:
            st.subheader(f"{selected_result_user['name']}'s Picks - Week {selected_week_record['week']}")
            
            for pick in picks:
                with st.expander(f"{pick['team']} - {pick['player_name']}", expanded=False):
                    col_result, col_return = st.columns(2)
                    # Show odds and theoretical return summary
                    odds_val = pick.get('odds')
                    theo_ret = pick.get('theoretical_return')
                    odds_str = (
                        f"+{int(odds_val)}" if isinstance(odds_val, (int, float)) and odds_val >= 0 else
                        (str(int(odds_val)) if isinstance(odds_val, (int, float)) else "-")
                    )
                    st.caption(f"Odds: {odds_str} • Potential Return: ${theo_ret:.2f}" if isinstance(theo_ret, (int, float)) else f"Odds: {odds_str}")
                    
                    # Get existing result
                    existing_result = get_result_for_pick(pick['id'])
                    current_correct = existing_result['is_correct'] if existing_result else None
                    current_any_time_td = existing_result.get('any_time_td') if existing_result else None
                    current_return = existing_result['actual_return'] if existing_result else None
                    
                    with col_result:
                        is_correct = st.selectbox(
                            "First TD (Win/Loss)",
                            options=[None, True, False],
                            format_func=lambda x: "Pending" if x is None else ("✅ Correct" if x else "❌ Incorrect"),
                            index=0 if current_correct is None else (1 if current_correct else 2),
                            key=f"result_{pick['id']}"
                        )
                    
                    # Add Any Time TD toggle
                    any_time_td = st.checkbox(
                        "Any Time TD?",
                        value=current_any_time_td or False,
                        key=f"any_time_td_{pick['id']}"
                    )
                    
                    with col_return:
                        actual_return = st.number_input(
                            "Return ($)",
                            value=float(current_return) if current_return else 0.0,
                            key=f"return_{pick['id']}"
                        )
                    
                    if st.button("Save Result", key=f"save_result_{pick['id']}", type="secondary"):
                        try:
                            add_result(
                                pick_id=pick['id'],
                                actual_scorer=pick['player_name'],
                                is_correct=is_correct,
                                actual_return=actual_return if is_correct else 0.0,
                                any_time_td=any_time_td
                            )
                            st.success(f"✅ Result saved for {pick['player_name']}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

                    # Delete pick action
                    if st.button("🗑️ Delete Pick", key=f"delete_pick_{pick['id']}"):
                        try:
                            if delete_pick(pick['id']):
                                st.success("Pick deleted.")
                                st.rerun()
                            else:
                                st.warning("Pick not found or already deleted.")
                        except Exception as e:
                            st.error(f"❌ Error deleting pick: {e}")
        else:
            st.info(f"No picks found for {selected_result_user['name']} in Week {selected_week_record['week']}")

    # Maintenance tools for duplicates and uniqueness
    st.markdown("---")
    st.subheader("Maintenance")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🧹 Remove Duplicate Picks for Selected User/Week"):
            try:
                summary = dedupe_picks_for_user_week(selected_result_user['id'], selected_week_record['id'])
                st.success(f"Removed {summary['duplicates_removed']} duplicates. Kept {summary['unique_kept']} unique picks.")
                st.rerun()
            except Exception as e:
                st.error(f"Dedupe failed: {e}")
    with col_b:
        if st.button("🔒 Enforce Unique Picks Constraint"):
            ok = create_unique_picks_index()
            if ok:
                st.success("Unique index created or already exists.")
            else:
                st.warning("Could not create unique index. Remove duplicates first.")

    if st.button("🧹 Full Database Dedupe"):
        try:
            summary = dedupe_all_picks()
            st.success(f"Removed {summary['duplicates_removed']} duplicates globally. Kept {summary['unique_kept']} unique picks.")
            st.rerun()
        except Exception as e:
            st.error(f"Full dedupe failed: {e}")

    # Override Grading Tools - Use Sparingly
    st.markdown("---")
    st.subheader("⚠️ Override Grading (Use Sparingly)")
    st.markdown("Clear grading results to re-grade picks. Useful when updating to new metrics or fixing scoring errors.")
    
    override_col1, override_col2 = st.columns(2)
    with override_col1:
        override_season = st.selectbox(
            "Season to Override",
            options=config.SEASONS,
            index=0,
            key="override_season"
        )
    
    with override_col2:
        all_weeks_list = get_all_weeks(override_season)
        week_options = ["All Weeks"] + [f"Week {w['week']}" for w in all_weeks_list]
        selected_override_scope = st.selectbox(
            "Scope",
            options=week_options,
            index=0,
            key="override_scope"
        )
    
    if st.button("🔄 Clear Grading Results", type="secondary", key="override_button"):
        with st.expander("⚠️ CONFIRM OVERRIDE - This action will clear grading results", expanded=True):
            st.warning(
                f"This will delete all grading results for **{override_season}** {selected_override_scope.lower()}. "
                "Picks will remain and can be re-graded. This action cannot be undone."
            )
            
            confirm_col1, confirm_col2 = st.columns(2)
            with confirm_col1:
                if st.button("✅ Confirm Override", type="primary", key="confirm_override"):
                    try:
                        if selected_override_scope == "All Weeks":
                            result = clear_grading_results(override_season)
                            st.success(
                                f"✅ Cleared {result['results_cleared']} grading results for Season {override_season}. "
                                f"{result['picks_remaining']} picks remain for re-grading."
                            )
                        else:
                            week_num = int(selected_override_scope.split()[1])
                            result = clear_grading_results(override_season, week_num)
                            st.success(
                                f"✅ Cleared {result['results_cleared']} grading results for Season {override_season} Week {week_num}. "
                                f"{result['picks_remaining']} picks remain for re-grading."
                            )
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Override failed: {str(e)}")
            
            with confirm_col2:
                if st.button("❌ Cancel", key="cancel_override"):
                    st.info("Override cancelled.")
