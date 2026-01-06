"""
Admin Interface - For managing predictions and results.
Handles prediction input, user management, pick input, and result tracking.
All data persisted to SQLite database.
"""

import streamlit as st
import pandas as pd
from data_processor import (
    load_rosters, get_first_td_odds, get_team_full_name, get_game_schedule,
    names_match
)
import config
from database import (
    init_db, add_user, get_all_users, delete_user, get_user_by_name,
    add_week, get_week_by_season_week, get_all_weeks,
    add_pick, get_user_week_picks, delete_pick,
    add_result, get_result_for_pick, get_user_stats
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
    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 User Management",
        "📝 Input Picks",
        "✅ Update Results",
        "📊 View Stats"
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
                        
                        # Get existing result
                        existing_result = get_result_for_pick(pick['id'])
                        current_correct = existing_result['is_correct'] if existing_result else None
                        current_return = existing_result['actual_return'] if existing_result else None
                        
                        with col_result:
                            is_correct = st.selectbox(
                                "Result",
                                options=[None, True, False],
                                format_func=lambda x: "Pending" if x is None else ("✅ Correct" if x else "❌ Incorrect"),
                                index=0 if current_correct is None else (1 if current_correct else 2),
                                key=f"result_{pick['id']}"
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
                                    actual_return=actual_return if is_correct else 0.0
                                )
                                st.success(f"✅ Result saved for {pick['player_name']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
            else:
                st.info(f"No picks found for {selected_result_user['name']} in Week {selected_week_record['week']}")
    
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

