import streamlit as st
import pandas as pd
from data_processor import (
    load_data, get_touchdowns, get_first_tds, get_game_schedule, 
    load_rosters, get_first_td_odds, get_team_full_name,
    get_team_first_td_counts, get_player_first_td_counts, get_position_first_td_counts,
    names_match
)
import config

st.set_page_config(
    page_title="NFL TD Tracker",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished look
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main-header {
        font-family: 'Inter', sans-serif;
        color: #1f1f1f;
        font-weight: 700;
    }
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box_shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Configuration")
    season = st.selectbox(
        "Select Season",
        options=config.SEASONS,
        index=0  # Defaults to 2024 (first item)
    )
    
    # Game Type Filter
    game_type_filter = st.radio(
        "Game Type",
        options=["All", "Main Slate", "Standalone"],
        index=0,
        help="Main Slate: Sunday games < 8PM EST. Standalone: All others."
    )

    st.markdown("---")
    st.markdown("""
    **About**
    This app uses `nflreadpy` to analyze NFL play-by-play data and identify touchdown scorers.
    """)

# Main Content
st.title(f"🏈 NFL Touchdown Tracker - {season}")

# Load Data
with st.spinner(f"Loading data for {season}..."):
    df = load_data(season)

if df.empty:
    st.warning("No data found for this season or an error occurred.")
else:
    # Filter by Game Type
    if game_type_filter == "Main Slate":
        df = df[df['game_type'] == "Main Slate"]
    elif game_type_filter == "Standalone":
        df = df[df['game_type'] == "Standalone"]
        
    # Process Data
    all_tds = get_touchdowns(df)
    first_tds = get_first_tds(df)

    # Key Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Games", df['game_id'].nunique())
    with col2:
        st.metric("Total Touchdowns", len(all_tds))
    with col3:
        # Most common first TD scorer
        if not first_tds.empty:
            top_scorer = first_tds['td_player_name'].mode()
            if not top_scorer.empty:
                st.metric("Top First TD Scorer", top_scorer[0])

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚀 First TD of the Game", "📋 All Touchdowns", "📅 Weekly Schedule", "🔮 Prediction", "📊 Analysis"])

    with tab1:
        st.header("First Touchdowns per Game")
        st.markdown("This list shows the first touchdown scored in every game of the season.")
        
        if not first_tds.empty:
            # Display columns cleanup
            display_cols = [
                'week', 'away_team', 'home_team', 'td_player_name', 'posteam', 'qtr', 'desc'
            ]
            # Ensure columns exist before filtering
            valid_cols = [c for c in display_cols if c in first_tds.columns]
            
            # Sort by week
            first_tds_display = first_tds.sort_values(by=['week', 'game_id'])
            
            st.dataframe(
                first_tds_display[valid_cols],
                width="stretch",
                column_config={
                    "week": st.column_config.NumberColumn("Week", format="%d"),
                    "away_team": "Away",
                    "home_team": "Home",
                    "td_player_name": "Player",
                    "posteam": "Scoring Team",
                    "qtr": "Quarter",
                    "desc": "Play Description"
                },
                hide_index=True
            )
        else:
            st.info("No First TDs found.")

    with tab2:
        st.header("All Touchdown Scored")
        
        if not all_tds.empty:
            # Filters
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                selected_team = st.multiselect("Filter by Scoring Team", options=sorted(all_tds['posteam'].dropna().unique()))
            with col_f2:
                selected_week = st.multiselect("Filter by Week", options=sorted(all_tds['week'].dropna().unique()))
            
            filtered_tds = all_tds
            if selected_team:
                filtered_tds = filtered_tds[filtered_tds['posteam'].isin(selected_team)]
            if selected_week:
                filtered_tds = filtered_tds[filtered_tds['week'].isin(selected_week)]
                
            display_cols_all = [
                'week', 'posteam', 'defteam', 'td_player_name', 'play_type', 'qtr', 'time', 'desc'
            ]
            valid_cols_all = [c for c in display_cols_all if c in filtered_tds.columns]

            st.dataframe(
                filtered_tds[valid_cols_all],
                width="stretch",
                hide_index=True
            )
        else:
            st.info("No touchdowns found.")
            
    with tab3:
        st.header("Weekly Schedule & Results")
        
        schedule = get_game_schedule(df, season)
        if not schedule.empty:
            # Week Selector
            available_weeks = sorted(schedule['week'].unique())
            
            # Default to latest week if available
            default_ix = len(available_weeks) - 1 if available_weeks else 0
            
            selected_schedule_week = st.selectbox(
                "Select Week", 
                options=available_weeks, 
                index=default_ix,
                format_func=lambda x: f"Week {x}"
            )
            
            # Filter
            week_schedule = schedule[schedule['week'] == selected_schedule_week]
            
            if not week_schedule.empty:
                st.dataframe(
                    week_schedule,
                    width="stretch",
                    column_config={
                        "game_date": "Date",
                        "start_time": "Time",
                        "home_team": "Home",
                        "away_team": "Away",
                        "home_score": st.column_config.NumberColumn("Home Score", format="%d"),
                        "away_score": st.column_config.NumberColumn("Away Score", format="%d"),
                        "game_type": "Type"
                    },
                    hide_index=True
                )
            else:
                st.info(f"No games found for Week {selected_schedule_week}.")
        else:
            st.info("No schedule data available.")

    with tab4:
        st.header("🔮 First TD Scorer Predictor")
        st.markdown("Pick who you think will score the first touchdown in each game!")

        # Initialize session state for predictions if not exists
        if 'predictions' not in st.session_state:
            st.session_state['predictions'] = {}

        if schedule.empty:
             st.warning("No schedule data available to make predictions.")
        else:
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
            else:
                # Filter 'Active' players mostly? Or just all? 'ACT' is usual status but maybe 'RES' etc.
                # Let's take all for now to be safe, maybe filter by team later
                roster_df['display_name'] = roster_df['full_name'] + " (" + roster_df['position'] + ")"

                # Odds Logic
                # API Key from config
                api_key = config.ODDS_API_KEY
                
                # Check bounds for the week to fetch odds efficiently
                # games_for_week['game_date'] format is YYYY-MM-DD
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
                    # The odds_data key is (home_team, away_team) from API
                    # We try to match with team names or alias matching if needed
                    # Simple try first:
                    this_game_odds = odds_data.get((home_team, away_team))
                    if not this_game_odds:
                        # Try reverse? Unlikely but possible
                        this_game_odds = odds_data.get((away_team, home_team), {})

                    # Container
                    with st.expander(f"{away_team} @ {home_team}", expanded=True):
                        col_p1, col_p2 = st.columns([2, 1])
                        
                        # Filter Roster: OFFENSE ONLY + D/ST synthetic option
                        # Keep: QB, RB, WR, TE, FB
                        off_positions = ['QB', 'RB', 'WR', 'TE', 'FB']
                        
                        team_players = roster_df[
                            (roster_df['team'].isin([home_team, away_team])) & 
                            (roster_df['position'].isin(off_positions))
                        ].sort_values('full_name')
                        
                        # Build options list with odds if available
                        base_options = team_players['display_name'].tolist()
                        
                        # Add D/ST options for both teams
                        dst_options = []
                        for tm in [away_team, home_team]:
                             dst_options.append(f"{tm} D/ST")
                             
                        # Combine base options with D/ST (sorted appropriately? or just append D/ST at end?)
                        # Let's put D/ST at the end of the list usually
                        # But we are sorting by odds below, so it will float up if favored.
                        
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
                            # Odds API Key usually: "TeamName Defense"
                            # Need to map Abbr -> Full Name
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
                            final_options += base_options + sorted(dst_options)
                        # Current selection from session state is 'Clean Name (POS)'
                        current_selection_clean = st.session_state['predictions'].get(game_id, "None")
                        
                        # Find index of current selection in the potentially odd-ified list
                        # We match by checking if the option starts with the clean selection
                        sel_index = 0
                        if current_selection_clean != "None":
                            for i, opt in enumerate(final_options):
                                # Check if opt is exactly the clean selection OR "Clean selection [...]"
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
                            # Strip odds part if present: "Name (POS) [+100]" -> "Name (POS)"
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
                                    # Use clean value from state directly or strip from selected_option
                                    # safely getting from state is better
                                    curr_val = st.session_state['predictions'].get(game_id, "None")
                                    # Extract name from prediction "Name (POS)"
                                    pred_name = curr_val.split(" (")[0] if curr_val != "None" else "None"
                                    
                                    
                                    if names_match(pred_name, actual_scorer):
                                        st.success(f"CORRECT! {actual_scorer} scored first.")
                                        st.balloons()
                                    else:
                                        st.error(f"Incorrect. {actual_scorer} scored first.")
                                        
                            # Show verify status if game is over/has scorer
                            if actual_scorer != 'None':
                                st.caption(f"Actual: {actual_scorer}")

    # --- TAB 5: ANALYSIS ---
    with tab5:
        st.header("First Touchdown Analysis")
        
        # Use df which is already filtered by main filters (Main Slate / Standalone)
        # filtered_df was a typo/misassumption
        analyzed_df = df
        
        if analyzed_df.empty:
            st.info("No data available for analysis.")
        else:
            col_a1, col_a2 = st.columns(2)
            
            with col_a1:
                st.subheader("Team Rankings")
                # Calculate first TDs for current view (analyzed_df) once
                # But our optimization was to pass pre-calculated first_tds.
                # get_team_first_td_counts now expects a DataFrame of First TDs, NOT raw PBP.
                # So we must calculate first_tds from analyzed_df here.
                analyzed_first_tds = get_first_tds(analyzed_df)
                
                team_stats = get_team_first_td_counts(analyzed_first_tds)
                if not team_stats.empty:
                    # Sort desc
                    team_stats = team_stats.sort_values('First TDs', ascending=False)
                    st.dataframe(
                        team_stats, 
                        column_config={
                            "Team": st.column_config.TextColumn("Team"),
                            "First TDs": st.column_config.ProgressColumn("First TDs", format="%d", min_value=0, max_value=int(team_stats['First TDs'].max()))
                        },
                        hide_index=True,
                        width="stretch"

                    )
                else:
                    st.caption("No data.")

            with col_a2:
                st.subheader("Player Leaderboard")
                # Reuse analyzed_first_tds
                player_stats = get_player_first_td_counts(analyzed_first_tds)
                if not player_stats.empty:
                    # Top 20
                    player_stats = player_stats.sort_values('First TDs', ascending=False)
                    top_players = player_stats.head(20)
                    st.bar_chart(top_players.set_index('Player'))
                else:
                    st.caption("No data.")
            
            st.divider()
            
            st.subheader("First TDs by Position")
            with st.spinner("Analyzing positions..."):
                roster_for_stats = load_rosters(season)
                # content
                pos_stats = get_position_first_td_counts(analyzed_first_tds, roster_for_stats)
                
            if not pos_stats.empty:
                pos_stats = pos_stats.sort_values('First TDs', ascending=False)
                st.bar_chart(pos_stats.set_index('Position'))
            else:
                st.caption("No position data available (could not link IDs).")

