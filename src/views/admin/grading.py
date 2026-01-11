"""
Grading Tab - Auto-grade picks against play-by-play data
"""

import streamlit as st
import pandas as pd
import config
from utils import get_all_weeks, get_ungraded_picks, add_result
from utils.nfl_data import load_rosters
from utils.csv_import import get_first_td_map
from utils.name_matching import names_match


def show_grading_tab(season: int, schedule: pd.DataFrame) -> None:
    """Display the grading interface for ungraded picks."""
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
    ungraded = _get_filtered_ungraded_picks(
        grade_season, grade_week, selected_game, selected_date, selected_player,
        grade_schedule, preview_ungraded
    )
    
    if not ungraded:
        st.info("No ungraded picks found for the selected filters.")
        return
    
    st.write(f"**{len(ungraded)} ungraded pick(s) found**")
    
    # Auto-Grade Button
    _show_auto_grade_button(ungraded, grade_season, grade_week)
    
    # Check for Unknown teams
    _show_unknown_teams_fix(ungraded, grade_season)
    
    # Load first TD data and show preview table
    first_td_map = _load_first_td_map(grade_season, grade_week)
    preview_data = _build_preview_data(ungraded, grade_schedule, first_td_map)
    
    # Display and handle editable table
    _show_editable_preview_table(preview_data, grade_schedule, grade_season, first_td_map, ungraded)
    
    # Grading actions
    _show_grading_actions(preview_data)


def _get_filtered_ungraded_picks(grade_season, grade_week, selected_game, selected_date, 
                                  selected_player, grade_schedule, preview_ungraded):
    """Apply all filters to ungraded picks."""
    if grade_week:
        game_id_filter = None
        if selected_game != "All Games":
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
        ungraded = get_ungraded_picks(grade_season, None, None)
    
    # Apply player filter
    if selected_player != "All Players":
        ungraded = [p for p in ungraded if p['player_name'] == selected_player]
    
    # Apply date filter
    if selected_date != "All Dates" and selected_game == "All Games" and grade_week and not grade_schedule.empty:
        date_games = grade_schedule[(grade_schedule['week'] == grade_week) & (grade_schedule['game_date'] == selected_date)]
        date_game_ids = date_games['game_id'].tolist()
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
    
    return ungraded


def _show_auto_grade_button(ungraded, grade_season, grade_week):
    """Show auto-grade button and handle grading."""
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


def _show_unknown_teams_fix(ungraded, grade_season):
    """Show warning and fix button for Unknown teams."""
    unknown_teams = [p for p in ungraded if p.get('team') == 'Unknown']
    if unknown_teams:
        st.warning(f"⚠️ {len(unknown_teams)} pick(s) have team='Unknown' and cannot be graded.")
        # TODO: Implement backfill_team_for_picks function to fix Unknown teams
        # if st.button("🔧 Auto-Fix Unknown Teams", type="secondary"):
        #     with st.spinner("Looking up player teams from roster..."):
        #         from utils.team_utils import backfill_team_for_picks
        #         result = backfill_team_for_picks(grade_season)
        #         if 'error' in result:
        #             st.error(result['error'])
        #         else:
        #             msg = f"Updated {result['updated']} pick(s)"
        #             if result['duplicates'] > 0:
        #                 msg += f", removed {result['duplicates']} duplicate(s)"
        #             if result['failed'] > 0:
        #                 msg += f", {result['failed']} failed to resolve"
        #             st.success(msg)
        #             st.rerun()


def _load_first_td_map(grade_season, grade_week):
    """Load first TD mapping data."""
    with st.spinner("Loading first TD data..."):
        try:
            first_td_map = get_first_td_map(grade_season, grade_week)
        except Exception as e:
            st.error(f"Failed to load first TD data: {e}")
            first_td_map = {}
    return first_td_map


def _build_preview_data(ungraded, grade_schedule, first_td_map):
    """Build preview data for the table."""
    preview_data = []
    for pick in ungraded:
        game_id = None
        game_date = 'N/A'
        game_matchup = 'N/A'
        
        if not grade_schedule.empty:
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
    
    return preview_data


def _show_editable_preview_table(preview_data, grade_schedule, grade_season, first_td_map, ungraded):
    """Show and handle editable preview table."""
    preview_df = pd.DataFrame(preview_data)
    display_cols = ['User', 'Week', 'Game Date', 'Game', 'Player Pick', 'Odds', 'Detected First TD', 'Match', 'Proposed Result']
    
    # Prepare dropdown options
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
    
    # Add existing player picks to dropdown
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
            'Game Date': st.column_config.SelectboxColumn(options=available_dates),
            'Game': st.column_config.SelectboxColumn(options=available_games),
            'Player Pick': st.column_config.SelectboxColumn(options=available_players),
            'Odds': st.column_config.Column(disabled=True),
            'Detected First TD': st.column_config.Column(disabled=True),
            'Match': st.column_config.Column(disabled=True),
            'Proposed Result': st.column_config.Column(disabled=True),
            'Pick ID': st.column_config.Column(disabled=True),
            'Team': st.column_config.Column(disabled=True)
        },
        column_order=['User', 'Week', 'Game Date', 'Game', 'Player Pick', 'Odds', 'Detected First TD', 'Match', 'Proposed Result'],
        key="grade_picks_editor"
    )
    
    # Handle edits
    if not edited_df.equals(preview_df[display_cols + ['Pick ID', 'Team']]):
        st.info("⚠️ You have unsaved changes in the table above.")
        if st.button("💾 Save & Recalculate Matches", type="primary"):
            _save_edits_and_recalculate(edited_df, preview_df, preview_data, grade_schedule, first_td_map)


def _save_edits_and_recalculate(edited_df, preview_df, preview_data, grade_schedule, first_td_map):
    """Save edits and recalculate matches."""
    from utils import get_db_connection
    
    changes_saved = 0
    for idx, row in edited_df.iterrows():
        pick_id = row['Pick ID']
        orig_row = preview_df.iloc[idx]
        
        if (row['Player Pick'] != orig_row['Player Pick'] or 
            row['Game Date'] != orig_row['Game Date'] or 
            row['Game'] != orig_row['Game']):
            
            if row['Player Pick'] != orig_row['Player Pick']:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE picks SET player_name = ? WHERE id = ?", 
                                 (row['Player Pick'], pick_id))
                    conn.commit()
                    conn.close()
                    changes_saved += 1
                except Exception as e:
                    st.error(f"Failed to update pick {pick_id}: {e}")
            
            # Recalculate match
            game_id = None
            if row['Game'] != 'N/A' and not grade_schedule.empty:
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
            
            # Update preview_data
            for pd_row in preview_data:
                if pd_row['Pick ID'] == pick_id:
                    pd_row['Player Pick'] = row['Player Pick']
                    pd_row['Game Date'] = row['Game Date']
                    pd_row['Game'] = row['Game']
                    
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


def _show_grading_actions(preview_data):
    """Show grading action buttons."""
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Grade All Matches", type="primary", use_container_width=True):
            graded_correct = 0
            for row in preview_data:
                if row['Match'] == '✅':
                    theo_return = row['Theo Return']
                    actual_return = float(theo_return.replace('$', '')) if theo_return != 'N/A' else 0.0
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
            for row in preview_data:
                theo_return_str = row['Theo Return']
                actual_return = float(theo_return_str.replace('$', '')) if theo_return_str != 'N/A' else 0.0
                
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
