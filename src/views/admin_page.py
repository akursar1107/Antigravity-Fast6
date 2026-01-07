"""
Admin Interface - For managing predictions and results.
Handles prediction input, user management, pick input, and result tracking.
All data persisted to SQLite database.
"""

import streamlit as st
import pandas as pd
import time
from utils.nfl_data import (
    load_rosters, get_game_schedule
)
from utils.name_matching import names_match
from data_processor import (
    get_first_td_odds, get_team_full_name
)
from utils.csv_import import ingest_picks_from_csv, get_first_td_map
import config
from database import (
    init_db, add_user, get_all_users, delete_user, get_user_by_name,
    add_week, get_week_by_season_week, get_all_weeks,
    add_pick, get_user_week_picks, get_user_all_picks, delete_pick,
    add_result, get_result_for_pick, get_user_stats,
    dedupe_picks_for_user_week, create_unique_picks_index, dedupe_all_picks,
    get_ungraded_picks, clear_grading_results
)


def show_prediction_tab(schedule: pd.DataFrame, season: int) -> None:
    """Prediction interface for first TD picks."""
    st.header("🔮 First TD Scorer Predictor")
    st.markdown("Pick who you think will score the first touchdown in each game!")

    # Initialize session state for predictions if not exists
    if 'predictions' not in st.session_state:
        st.session_state['predictions'] = {}

    if schedule.empty:
        st.warning("No schedule data available to make predictions.")
        return
    
    # Week Selection for Prediction
    pred_weeks = sorted(schedule['week'].unique())
    default_pred_ix = len(pred_weeks) - 1 if pred_weeks else 0
    selected_pred_week = st.selectbox(
        "Select Prediction Week", 
        options=pred_weeks, 
        index=default_pred_ix,
        format_func=lambda x: f"Week {x}",
        key="pred_week_selector"
    )

    # Get games for this week
    games_for_week = schedule[schedule['week'] == selected_pred_week]
    
    # Load Rosters for dropdowns
    with st.spinner("Loading rosters..."):
        roster_df = load_rosters(season)
    
    if roster_df.empty:
        st.error("Could not load rosters. Player selection unavailable.")
        return
    
    # Prepare roster display
    roster_df['display_name'] = roster_df['full_name'] + " (" + roster_df['position'] + ")"

    # Odds Logic
    api_key = config.ODDS_API_KEY
    
    # Check bounds for the week
    if not games_for_week.empty:
        min_date = games_for_week['game_date'].min()
        max_date = games_for_week['game_date'].max()
    else:
        min_date, max_date = None, None
    
    odds_data = {}
    if st.button("Load First TD Odds (Costs API Quota)", help="Fetch odds from The Odds API"):
        if min_date and max_date:
            with st.spinner("Fetching odds..."):
                odds_data = get_first_td_odds(api_key, min_date, max_date)
                if not odds_data:
                    st.warning("No odds found or API error. (Check if market is available)")
                else:
                    st.success("Odds loaded!")
        else:
            st.error("No valid dates for this week.")
    
    # Iterate through games
    for _, game in games_for_week.iterrows():
        game_id = game['game_id']
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Try to get odds for this game
        this_game_odds = odds_data.get((home_team, away_team))
        if not this_game_odds:
            this_game_odds = odds_data.get((away_team, home_team), {})

        # Container
        with st.expander(f"{away_team} @ {home_team}", expanded=True):
            col_p1, col_p2 = st.columns([2, 1])
            
            # Filter Roster: OFFENSE ONLY + D/ST synthetic option
            off_positions = ['QB', 'RB', 'WR', 'TE', 'FB']
            
            team_players = roster_df[
                (roster_df['team'].isin([home_team, away_team])) & 
                (roster_df['position'].isin(off_positions))
            ].sort_values('full_name')
            
            # Build options list with odds if available
            base_options = team_players['display_name'].tolist()
            final_options = ["None"]
            
            if this_game_odds:
                formatted_odds = []
                formatted_no_odds = []
                
                # Process Players
                for p_name, display_str in zip(team_players['full_name'], team_players['display_name']):
                    price = this_game_odds.get(p_name)
                    if price:
                        price_str = f"+{price}" if price > 0 else str(price)
                        formatted_odds.append((price, f"{display_str} [{price_str}]"))
                    else:
                        formatted_no_odds.append(display_str)
                
                # Process D/ST
                for tm_abbr in [away_team, home_team]:
                    tm_full = get_team_full_name(tm_abbr)
                    dst_key = f"{tm_full} Defense"
                    price = this_game_odds.get(dst_key)
                    
                    display_str = f"{tm_abbr} D/ST"
                    if price:
                        price_str = f"+{price}" if price > 0 else str(price)
                        formatted_odds.append((price, f"{display_str} [{price_str}]"))
                    else:
                        formatted_no_odds.append(display_str)

                # Sort odds: lowest price (highest probability) first
                formatted_odds.sort(key=lambda x: x[0])
                
                # Combine
                final_options += [x[1] for x in formatted_odds] + sorted(formatted_no_odds)
            else:
                # No odds loaded, just roster + D/ST
                dst_options = [f"{tm} D/ST" for tm in [away_team, home_team]]
                final_options += base_options + sorted(dst_options)
            
            # Current selection from session state
            current_selection_clean = st.session_state['predictions'].get(game_id, "None")
            
            # Find index of current selection
            sel_index = 0
            if current_selection_clean != "None":
                for i, opt in enumerate(final_options):
                    if opt == current_selection_clean or opt.startswith(current_selection_clean + " ["):
                        sel_index = i
                        break
                
            with col_p1:
                selected_option = st.selectbox(
                    "Pick First TD Scorer",
                    options=final_options,
                    index=sel_index,
                    key=f"pred_{game_id}"
                )
                
                # Save CLEAN version to session state
                if selected_option != "None":
                    clean_val = selected_option.split(" [")[0]
                    st.session_state['predictions'][game_id] = clean_val
                else:
                    if game_id in st.session_state['predictions']:
                        del st.session_state['predictions'][game_id]

            with col_p2:
                # Verify Result
                actual_scorer = game.get('First TD Scorer', 'None')
                
                if st.button("Check Result", key=f"btn_{game_id}"):
                    if actual_scorer == 'None':
                        st.info("No First TD recorded yet.")
                    else:
                        curr_val = st.session_state['predictions'].get(game_id, "None")
                        pred_name = curr_val.split(" (")[0] if curr_val != "None" else "None"
                        
                        if names_match(pred_name, actual_scorer):
                            st.success(f"CORRECT! {actual_scorer} scored first.")
                            st.balloons()
                        else:
                            st.error(f"Incorrect. {actual_scorer} scored first.")
                            
                # Show verify status if game is over/has scorer
                if actual_scorer != 'None':
                    st.caption(f"Actual: {actual_scorer}")


def show_admin_interface(df: pd.DataFrame, season: int, schedule: pd.DataFrame) -> None:
    """Admin interface with multiple tabs for database management."""
    # Initialize database if not already done
    init_db()
    
    # Create tabs for different admin functions
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "👥 User Management",
        "📝 Input Picks",
        "✅ Update Results",
        "📊 View Stats",
        "📥 Import CSV",
        "🎯 Grade Picks"
    ])
    
    # ============= TAB 1: USER MANAGEMENT =============
    with tab1:
        st.header("👥 Group Member Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Add New Member")
            new_name = st.text_input("Member Name", placeholder="e.g., John")
            new_email = st.text_input("Email (optional)", placeholder="e.g., john@example.com")
            
            if st.button("Add Member", key="add_user_btn"):
                if new_name.strip():
                    try:
                        user_id = add_user(new_name.strip(), new_email if new_email else None)
                        st.success(f"✅ Added {new_name} (ID: {user_id})")
                        st.rerun()
                    except ValueError as e:
                        st.error(f"❌ {str(e)}")
                else:
                    st.warning("Please enter a name")
        
        with col2:
            st.subheader("Current Members")
            users = get_all_users()
            
            if users:
                users_df = pd.DataFrame(users)
                st.dataframe(
                    users_df[['id', 'name', 'email', 'created_at']],
                    width='stretch',
                    hide_index=True
                )
                
                st.markdown("---")
                st.subheader("Remove Member")
                user_to_remove = st.selectbox(
                    "Select member to remove",
                    options=users,
                    format_func=lambda x: x['name'],
                    key="remove_user_select"
                )
                
                if st.button("Delete Member", key="delete_user_btn", type="secondary"):
                    if delete_user(user_to_remove['id']):
                        st.success(f"✅ Removed {user_to_remove['name']}")
                        st.rerun()
            else:
                st.info("No members yet. Add one to get started!")
    
    # ============= TAB 2: INPUT PICKS =============
    with tab2:
        st.header("📝 Input Weekly Picks")
        
        users = get_all_users()
        if not users:
            st.warning("⚠️ No members added yet. Go to User Management tab first.")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_user = st.selectbox(
                "Select Member",
                options=users,
                format_func=lambda x: x['name'],
                key="pick_user_select"
            )
        
        with col2:
            st.write(f"**Season:** {season}")
        
        with col3:
            available_weeks = sorted(schedule['week'].unique()) if not schedule.empty else []
            selected_week = st.selectbox(
                "Select Week",
                options=available_weeks,
                format_func=lambda x: f"Week {x}",
                key="pick_week_select"
            )
        
        # Get or create week in database
        week_id = None
        if selected_week:
            week_record = get_week_by_season_week(season, selected_week)
            if not week_record:
                week_id = add_week(season, selected_week)
            else:
                week_id = week_record['id']
        
        # Get games for this week
        games_for_week = schedule[schedule['week'] == selected_week] if selected_week else pd.DataFrame()
        
        if games_for_week.empty:
            st.warning(f"No games found for Week {selected_week}")
            return
        
        # Load rosters
        with st.spinner("Loading rosters..."):
            roster_df = load_rosters(season)
        
        if roster_df.empty:
            st.error("Could not load rosters.")
            return
        
        roster_df['display_name'] = roster_df['full_name'] + " (" + roster_df['position'] + ")"
        
        # Get existing picks for this user/week
        existing_picks = get_user_week_picks(selected_user['id'], week_id) if week_id else []
        existing_picks_dict = {p['team']: p for p in existing_picks}
        
        st.subheader(f"Picks for {selected_user['name']} - Week {selected_week}")
        
        picks_to_add = []
        
        # Iterate through games
        for _, game in games_for_week.iterrows():
            home_team = game['home_team']
            away_team = game['away_team']
            
            with st.expander(f"{away_team} @ {home_team}", expanded=False):
                col_team, col_player = st.columns(2)
                
                # Get team-specific players
                off_positions = ['QB', 'RB', 'WR', 'TE', 'FB']
                team_players = roster_df[
                    (roster_df['team'].isin([home_team, away_team])) & 
                    (roster_df['position'].isin(off_positions))
                ].sort_values('full_name')
                
                options = ["-- Select Player --"] + team_players['display_name'].tolist()
                
                with col_team:
                    st.write(f"**{away_team} @ {home_team}**")
                
                with col_player:
                    selected_player = st.selectbox(
                        "First TD Scorer",
                        options=options,
                        key=f"pick_{home_team}_{away_team}",
                        index=0
                    )
                
                if selected_player != "-- Select Player --":
                    # Extract clean name (remove position)
                    clean_name = selected_player.split(" (")[0]
                    picks_to_add.append({
                        'game_key': f"{away_team}_{home_team}",
                        'team': away_team,
                        'player_name': clean_name,
                        'game': f"{away_team} @ {home_team}"
                    })
        
        # Save picks button
        if picks_to_add:
            if st.button("💾 Save All Picks", key="save_picks_btn"):
                for pick in picks_to_add:
                    try:
                        pick_id = add_pick(
                            user_id=selected_user['id'],
                            week_id=week_id,
                            team=pick['team'],
                            player_name=pick['player_name']
                        )
                        st.success(f"✅ Saved: {pick['player_name']} - {pick['game']}")
                    except Exception as e:
                        st.error(f"❌ Error saving {pick['player_name']}: {str(e)}")
                st.rerun()
    
    # ============= TAB 3: UPDATE RESULTS =============
    with tab3:
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
    
    # ============= TAB 4: VIEW STATS =============
    with tab4:
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

    # ============= TAB 5: IMPORT CSV =============
    with tab5:
        st.header("📥 Import Picks from CSV")
        st.markdown("Upload a CSV in the same format as 'First TD - 2025.csv'. Only regular-season weeks (1–18) are imported.")

        # Season selection for mapping
        sel_season = st.number_input("Season", value=season, min_value=2000, max_value=2100, step=1)
        uploaded = st.file_uploader("Upload CSV", type=["csv"], accept_multiple_files=False)
        run_import = st.button("Run Import", type="primary", disabled=(uploaded is None))

        if run_import and uploaded is not None:
            import tempfile, os
            # Write to a temporary file path for ingestion
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded.getbuffer())
                tmp_path = tmp.name
            try:
                with st.spinner("Importing picks..."):
                    summary = ingest_picks_from_csv(tmp_path, int(sel_season))
                # Confirmation toast; no auto-rerun to avoid duplicate imports
                picks_deleted = summary.get('picks_deleted', 0)
                results_deleted = summary.get('results_deleted', 0)
                
                if picks_deleted > 0 or results_deleted > 0:
                    msg = (
                        f"Wiped {picks_deleted} existing picks, {results_deleted} results. "
                        f"Imported {summary.get('picks_imported', 0)} picks, "
                        f"{summary.get('results_imported', 0)} results."
                    )
                else:
                    msg = (
                        f"Imported {summary.get('picks_imported', 0)} picks, "
                        f"{summary.get('results_imported', 0)} results."
                    )
                st.toast(msg)
                st.write(summary)
                if st.button("Refresh Admin View", type="secondary"):
                    st.rerun()
            except Exception as e:
                # Show both an error message and a toast for visibility
                st.error(f"Import failed: {e}")
                try:
                    st.toast(f"Import failed: {e}")
                except Exception:
                    pass
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    # ============= TAB 6: GRADE PICKS =============
    with tab6:
        st.header("🎯 Grade Ungraded Picks")
        st.markdown("Automatically grade picks based on actual first TD scorers from play-by-play data.")
        
        # Season and Week filters
        col1, col2, col3 = st.columns(3)
        with col1:
            grade_season = st.number_input("Season", value=season, min_value=2000, max_value=2100, step=1, key="grade_season")
        
        # Load schedule for the grade season if different from current season
        if grade_season != season:
            with st.spinner(f"Loading schedule for {grade_season}..."):
                try:
                    import nflreadpy as nfl
                    grade_schedule_df = nfl.load_schedules(seasons=[int(grade_season)]).to_pandas()
                    grade_schedule = grade_schedule_df[['game_id', 'week', 'gameday', 'home_team', 'away_team']].copy()
                    grade_schedule.rename(columns={'gameday': 'game_date'}, inplace=True)
                except Exception as e:
                    st.error(f"Failed to load schedule for {grade_season}: {e}")
                    grade_schedule = pd.DataFrame()
        else:
            # Use the existing schedule DataFrame
            grade_schedule = schedule[['game_id', 'week', 'game_date', 'home_team', 'away_team']].copy() if not schedule.empty else pd.DataFrame()
        
        with col2:
            # Get all weeks for this season
            all_weeks = get_all_weeks()
            season_weeks = [w for w in all_weeks if w['season'] == grade_season]
            week_options = ["All"] + [f"Week {w['week']}" for w in season_weeks]
            selected_week_str = st.selectbox("Week", options=week_options, key="grade_week")
            if selected_week_str == "All":
                grade_week = None
            else:
                grade_week = int(selected_week_str.split()[1])
        with col3:
            # Show total ungraded count for context
            if grade_week:
                preview_ungraded = get_ungraded_picks(grade_season, grade_week, None)
            else:
                preview_ungraded = get_ungraded_picks(grade_season, None, None)
            st.metric("Ungraded Picks", len(preview_ungraded))
        
        # Additional filters row
        if grade_week and not grade_schedule.empty:
            st.markdown("---")
            st.subheader("Filter by Game or Player")
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                # Game date filter
                week_schedule = grade_schedule[grade_schedule['week'] == grade_week]
                if not week_schedule.empty:
                    date_options = ["All Dates"] + sorted(week_schedule['game_date'].unique().tolist())
                    selected_date = st.selectbox("Game Date", options=date_options, key="grade_date")
                else:
                    selected_date = "All Dates"
            
            with filter_col2:
                # Game matchup filter
                if selected_date != "All Dates" and not week_schedule.empty:
                    date_schedule = week_schedule[week_schedule['game_date'] == selected_date]
                else:
                    date_schedule = week_schedule
                
                if not date_schedule.empty:
                    game_options = ["All Games"] + [
                        f"{row['away_team']} @ {row['home_team']}" 
                        for _, row in date_schedule.iterrows()
                    ]
                    selected_game = st.selectbox("Game", options=game_options, key="grade_game")
                else:
                    selected_game = "All Games"
            
            with filter_col3:
                # Player filter
                if preview_ungraded:
                    player_options = ["All Players"] + sorted(list(set([p['player_name'] for p in preview_ungraded])))
                    selected_player = st.selectbox("Player Pick", options=player_options, key="grade_player")
                else:
                    selected_player = "All Players"
        else:
            selected_game = "All Games"
            selected_date = "All Dates"
            selected_player = "All Players"
        
        # Fetch ungraded picks with filters
        if grade_week:
            game_id_filter = None
            if selected_game != "All Games":
                # Find game_id from schedule
                game_parts = selected_game.split(" @ ")
                if len(game_parts) == 2:
                    away, home = game_parts
                    week_schedule = grade_schedule[grade_schedule['week'] == grade_week]
                    matching = week_schedule[
                        (week_schedule['away_team'] == away) & 
                        (week_schedule['home_team'] == home)
                    ]
                    if not matching.empty:
                        game_id_filter = matching.iloc[0]['game_id']
            
            ungraded = get_ungraded_picks(grade_season, grade_week, game_id_filter)
        else:
            # Get all ungraded for the season
            ungraded = get_ungraded_picks(grade_season, None, None)
        
        # Apply player filter
        if selected_player != "All Players":
            ungraded = [p for p in ungraded if p['player_name'] == selected_player]
        
        # Apply date filter (if no specific game selected but date is selected)
        if selected_date != "All Dates" and selected_game == "All Games" and grade_week and not grade_schedule.empty:
            # Get game_ids for this date
            date_games = grade_schedule[(grade_schedule['week'] == grade_week) & (grade_schedule['game_date'] == selected_date)]
            date_game_ids = date_games['game_id'].tolist()
            # Filter picks by matching their team to games on this date
            filtered_ungraded = []
            for pick in ungraded:
                if not grade_schedule.empty:
                    pick_games = grade_schedule[
                        (grade_schedule['week'] == pick['week']) &
                        ((grade_schedule['home_team'] == pick['team']) | (grade_schedule['away_team'] == pick['team']))
                    ]
                    if not pick_games.empty and pick_games.iloc[0]['game_id'] in date_game_ids:
                        filtered_ungraded.append(pick)
            ungraded = filtered_ungraded
        
        if not ungraded:
            st.info("No ungraded picks found for the selected filters.")
        else:
            st.write(f"**{len(ungraded)} ungraded pick(s) found**")
            
            # Auto-Grade Button - Grade all ungraded picks against database
            col_auto_grade = st.columns(3)
            with col_auto_grade[0]:
                if st.button("⚡ Auto-Grade All Against Database", type="primary", key="auto_grade_btn"):
                    with st.spinner(f"Auto-grading {len(ungraded)} pick(s)..."):
                        try:
                            from utils.grading_logic import auto_grade_season
                            result = auto_grade_season(grade_season, grade_week)
                            
                            if 'error' in result:
                                st.error(f"❌ {result['error']}")
                            else:
                                st.success(
                                    f"✅ Auto-graded {result['graded_picks']} picks\n\n"
                                    f"📊 **Results:**\n"
                                    f"• First TD Wins: {result['correct_first_td']}\n"
                                    f"• Any Time TD: {result['any_time_td']}\n"
                                    f"• Failed to Match: {result['failed_to_match']}\n"
                                    f"• Total Return: ${result['total_return']:.2f}"
                                )
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Auto-grade failed: {str(e)}")
            
            # Check if any picks have Unknown team and offer to fix
            unknown_teams = [p for p in ungraded if p.get('team') == 'Unknown']
            if unknown_teams:
                st.warning(f"⚠️ {len(unknown_teams)} pick(s) have team='Unknown' and cannot be graded.")
                if st.button("🔧 Auto-Fix Unknown Teams", type="secondary"):
                    with st.spinner("Looking up player teams from roster..."):
                        from data_processor import backfill_team_for_picks
                        result = backfill_team_for_picks(grade_season)
                        if 'error' in result:
                            st.error(result['error'])
                        else:
                            msg = f"Updated {result['updated']} pick(s)"
                            if result['duplicates'] > 0:
                                msg += f", removed {result['duplicates']} duplicate(s)"
                            if result['failed'] > 0:
                                msg += f", {result['failed']} failed to resolve"
                            st.success(msg)
                            st.rerun()
            
            # Load first TD data for matching
            with st.spinner("Loading first TD data..."):
                try:
                    first_td_map = get_first_td_map(grade_season, grade_week)
                except Exception as e:
                    st.error(f"Failed to load first TD data: {e}")
                    first_td_map = {}
            
            # Build preview table
            preview_data = []
            for pick in ungraded:
                # Find matching first TD
                game_id = None
                game_date = 'N/A'
                game_matchup = 'N/A'
                # Get game_id from schedule matching team and week
                if not grade_schedule.empty:
                    # Normalize team name to abbreviation for matching
                    team_abbr = config.TEAM_ABBR_MAP.get(pick['team'], pick['team'])
                    
                    matching_games = grade_schedule[
                        (grade_schedule['week'] == pick['week']) &
                        ((grade_schedule['home_team'] == team_abbr) | (grade_schedule['away_team'] == team_abbr))
                    ]
                    if not matching_games.empty:
                        game_row = matching_games.iloc[0]
                        game_id = game_row['game_id']
                        game_date = game_row['game_date']
                        game_matchup = f"{game_row['away_team']} @ {game_row['home_team']}"
                
                first_td_info = first_td_map.get(game_id, {})
                detected_player = first_td_info.get('player', 'N/A')
                detected_team = first_td_info.get('team', 'N/A')
                
                # Name matching
                is_match = False
                if detected_player != 'N/A':
                    is_match = names_match(pick['player_name'], detected_player)
                
                preview_data.append({
                    'Pick ID': pick['id'],
                    'User': pick['user_name'],
                    'Week': pick['week'],
                    'Game Date': game_date,
                    'Game': game_matchup,
                    'Team': pick['team'],
                    'Player Pick': pick['player_name'],
                    'Odds': f"+{pick['odds']}" if pick['odds'] and pick['odds'] > 0 else str(pick['odds']) if pick['odds'] else 'N/A',
                    'Theo Return': f"${pick['theoretical_return']:.2f}" if pick['theoretical_return'] else 'N/A',
                    'Detected First TD': detected_player,
                    'TD Team': detected_team,
                    'Match': '✅' if is_match else '❌',
                    'Proposed Result': 'Correct' if is_match else 'Incorrect',
                    'Game ID': game_id
                })
            
            # Display preview table with editing capability
            preview_df = pd.DataFrame(preview_data)
            display_cols = ['User', 'Week', 'Game Date', 'Game', 'Player Pick', 'Odds', 'Detected First TD', 'Match', 'Proposed Result']
            
            # Prepare dropdown options
            # Game dates from schedule
            if not grade_schedule.empty:
                available_dates = ['N/A'] + sorted(grade_schedule['game_date'].unique().tolist())
                available_games = ['N/A'] + sorted([
                    f"{row['away_team']} @ {row['home_team']}" 
                    for _, row in grade_schedule.iterrows()
                ])
            else:
                available_dates = ['N/A']
                available_games = ['N/A']
            
            # Player names from roster
            roster_df = load_rosters(grade_season)
            if not roster_df.empty and 'full_name' in roster_df.columns:
                available_players = ['N/A'] + sorted(roster_df['full_name'].unique().tolist())
            else:
                available_players = ['N/A']
            
            # Add existing player picks to the dropdown options to ensure they display
            for pick in ungraded:
                if pick['player_name'] and pick['player_name'] not in available_players:
                    available_players.append(pick['player_name'])
            available_players = sorted(available_players)
            
            # Configure editable columns
            edited_df = st.data_editor(
                preview_df[display_cols + ['Pick ID', 'Team']],
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                column_config={
                    'User': st.column_config.Column(disabled=True),
                    'Week': st.column_config.Column(disabled=True),
                    'Game Date': st.column_config.SelectboxColumn(
                        options=available_dates,
                        help="Select game date from dropdown"
                    ),
                    'Game': st.column_config.SelectboxColumn(
                        options=available_games,
                        help="Select game matchup from dropdown"
                    ),
                    'Player Pick': st.column_config.SelectboxColumn(
                        options=available_players,
                        help="Select player name from dropdown"
                    ),
                    'Odds': st.column_config.Column(disabled=True),
                    'Detected First TD': st.column_config.Column(
                        disabled=True,
                        help="Auto-detected from play-by-play data"
                    ),
                    'Match': st.column_config.Column(
                        disabled=True,
                        help="Auto-calculated based on name matching"
                    ),
                    'Proposed Result': st.column_config.Column(
                        disabled=True,
                        help="Auto-calculated: Correct if Match=✅, Incorrect if Match=❌"
                    ),
                    'Pick ID': st.column_config.Column(disabled=True),
                    'Team': st.column_config.Column(disabled=True)
                },
                column_order=['User', 'Week', 'Game Date', 'Game', 'Player Pick', 'Odds', 'Detected First TD', 'Match', 'Proposed Result'],
                key="grade_picks_editor"
            )
            
            # Show save button if data changed
            if not edited_df.equals(preview_df[display_cols + ['Pick ID', 'Team']]):
                st.info("⚠️ You have unsaved changes in the table above.")
                if st.button("💾 Save & Recalculate Matches", type="primary"):
                    changes_saved = 0
                    # Update picks in database and recalculate matches
                    for idx, row in edited_df.iterrows():
                        pick_id = row['Pick ID']
                        orig_row = preview_df.iloc[idx]
                        
                        # Check if any editable fields changed
                        if (row['Player Pick'] != orig_row['Player Pick'] or 
                            row['Game Date'] != orig_row['Game Date'] or 
                            row['Game'] != orig_row['Game']):
                            
                            # Update player name in database if changed
                            if row['Player Pick'] != orig_row['Player Pick']:
                                try:
                                    import database
                                    conn = database.get_db_connection()
                                    cursor = conn.cursor()
                                    cursor.execute("UPDATE picks SET player_name = ? WHERE id = ?", 
                                                 (row['Player Pick'], pick_id))
                                    conn.commit()
                                    conn.close()
                                    changes_saved += 1
                                except Exception as e:
                                    st.error(f"Failed to update pick {pick_id}: {e}")
                            
                            # Recalculate match for this pick
                            game_id = None
                            if row['Game'] != 'N/A' and not grade_schedule.empty:
                                # Parse game matchup
                                game_parts = row['Game'].split(" @ ")
                                if len(game_parts) == 2:
                                    away, home = game_parts
                                    week = row['Week']
                                    matching = grade_schedule[
                                        (grade_schedule['week'] == week) &
                                        (grade_schedule['away_team'] == away) &
                                        (grade_schedule['home_team'] == home)
                                    ]
                                    if not matching.empty:
                                        game_id = matching.iloc[0]['game_id']
                            
                            # Update preview_data with recalculated values
                            for pd_row in preview_data:
                                if pd_row['Pick ID'] == pick_id:
                                    pd_row['Player Pick'] = row['Player Pick']
                                    pd_row['Game Date'] = row['Game Date']
                                    pd_row['Game'] = row['Game']
                                    
                                    # Recalculate match
                                    first_td_info = first_td_map.get(game_id, {})
                                    detected_player = first_td_info.get('player', 'N/A')
                                    is_match = False
                                    if detected_player != 'N/A':
                                        is_match = names_match(row['Player Pick'], detected_player)
                                    
                                    pd_row['Detected First TD'] = detected_player
                                    pd_row['Match'] = '✅' if is_match else '❌'
                                    pd_row['Proposed Result'] = 'Correct' if is_match else 'Incorrect'
                                    break
                    
                    st.success(f"✅ Saved {changes_saved} change(s) and recalculated matches.")
                    st.rerun()
            
            # Grading actions
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Grade All Matches", type="primary", use_container_width=True):
                    graded_correct = 0
                    graded_incorrect = 0
                    for row in preview_data:
                        if row['Match'] == '✅':
                            # Grade as correct
                            theo_return = preview_df[preview_df['Pick ID'] == row['Pick ID']].iloc[0]['Theo Return']
                            if theo_return != 'N/A':
                                actual_return = float(theo_return.replace('$', ''))
                            else:
                                actual_return = 0.0
                            try:
                                add_result(row['Pick ID'], is_correct=True, actual_return=actual_return)
                                graded_correct += 1
                            except Exception as e:
                                st.warning(f"Failed to grade pick {row['Pick ID']}: {e}")
                    st.success(f"Graded {graded_correct} pick(s) as correct.")
                    st.rerun()
            
            with col2:
                if st.button("❌ Grade All as Incorrect", type="secondary", use_container_width=True):
                    graded = 0
                    for row in preview_data:
                        try:
                            add_result(row['Pick ID'], is_correct=False, actual_return=-1.0)
                            graded += 1
                        except Exception as e:
                            st.warning(f"Failed to grade pick {row['Pick ID']}: {e}")
                    st.success(f"Graded {graded} pick(s) as incorrect.")
                    st.rerun()
            
            with col3:
                if st.button("🔄 Grade All (Auto)", type="primary", use_container_width=True):
                    graded_correct = 0
                    graded_incorrect = 0
                    for idx, row in enumerate(preview_data):
                        theo_return_str = preview_df.iloc[idx]['Theo Return']
                        if theo_return_str != 'N/A':
                            actual_return = float(theo_return_str.replace('$', ''))
                        else:
                            actual_return = 0.0
                        
                        if row['Match'] == '✅':
                            try:
                                add_result(row['Pick ID'], is_correct=True, actual_return=actual_return)
                                graded_correct += 1
                            except Exception as e:
                                st.warning(f"Failed to grade pick {row['Pick ID']}: {e}")
                        else:
                            try:
                                add_result(row['Pick ID'], is_correct=False, actual_return=-1.0)
                                graded_incorrect += 1
                            except Exception as e:
                                st.warning(f"Failed to grade pick {row['Pick ID']}: {e}")
                    
                    st.success(f"Auto-graded {graded_correct} correct, {graded_incorrect} incorrect.")
                    st.rerun()
