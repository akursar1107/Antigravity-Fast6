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
from utils.odds_api import get_first_td_odds
from utils.team_utils import get_team_full_name
import config
from utils import init_db
from views.admin import (
    show_users_tab,
    show_picks_tab,
    show_results_tab,
    show_import_csv_tab,
    show_grading_tab
)
from views.admin.shared import show_stats_tab


def show_prediction_tab(schedule: pd.DataFrame, season: int) -> None:
    """
    Display admin predictions and model output tab.
    
    Args:
        schedule: NFL schedule DataFrame
        season: Current NFL season year
    
    Displays:
    - Nfelo model predictions for First TD
    - Expected value calculations
    - Confidence scores
    - Historical accuracy metrics
    
    Used by admins to review algorithmic predictions and validate
    model performance before distributing to users.
    """
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
    """
    Display main admin interface with tabs for administrative tasks.
    
    Args:
        df: Play-by-play data DataFrame
        season: Current NFL season year
        schedule: NFL schedule DataFrame
    
    Provides tabs for:
    - Grading picks against actual results
    - Importing picks from CSV
    - Viewing and managing results
    - Model predictions and validation
    
    Only accessible to admin users. Handles all backend data management
    and integrity checking.
    """
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
    
    # Use modular tab components
    with tab1:
        show_users_tab()
    
    with tab2:
        show_picks_tab(season, schedule)
    
    with tab3:
        show_results_tab(season)
    
    with tab4:
        show_stats_tab()
    
    with tab5:
        show_import_csv_tab(season)
    
    with tab6:
        show_grading_tab(season, schedule)
