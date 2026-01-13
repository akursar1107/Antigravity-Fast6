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
    """
    Display results review and management tab.
    
    Args:
        season: Current NFL season year
    
    Allows admins to:
    - View all graded and ungraded picks for the season
    - See actual scores and results
    - Manually override automated grading if needed
    - Audit the grading process
    - Export results for record-keeping
    
    Results show:
    - Which picks were correct (First TD or Any Time)
    - Actual scoring players
    - Point returns for each pick
    - User-by-user performance summary
    """
    st.header("✅ Update Game Results")
    
    # Select user and view all their season picks
    available_users = get_all_users()
    selected_result_user = st.selectbox(
        "Select Member",
        options=available_users,
        format_func=lambda x: x['name'],
        key="result_user_select"
    )
    
    if selected_result_user:
        # Get all picks for this user across entire season
        from utils import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, w.week, w.season, r.is_correct, r.any_time_td, r.actual_return
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            LEFT JOIN results r ON p.id = r.pick_id
            WHERE p.user_id = ? AND w.season = ?
            ORDER BY w.week, p.created_at
        """, (selected_result_user['id'], season))
        
        picks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if picks:
            st.subheader(f"{selected_result_user['name']}'s Picks - Season {season}")
            st.info(f"Showing {len(picks)} pick(s) for the entire season")
            
            for pick in picks:
                with st.expander(f"Week {pick['week']}: {pick['team']} - {pick['player_name']}", expanded=False):
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
                    current_correct = pick.get('is_correct')
                    current_any_time_td = pick.get('any_time_td')
                    current_return = pick.get('actual_return')
                    
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
            st.info(f"No picks found for {selected_result_user['name']} in season {season}")

    # Maintenance tools for duplicates and uniqueness
    st.markdown("---")
    st.subheader("Maintenance Tools")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔒 Enforce Unique Picks Constraint"):
            ok = create_unique_picks_index()
            if ok:
                st.success("Unique index created or already exists.")
            else:
                st.warning("Could not create unique index. Remove duplicates first.")
    with col_b:
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
