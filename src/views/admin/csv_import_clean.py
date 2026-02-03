"""
Clean CSV Import Admin Interface
"""

import streamlit as st
import pandas as pd
from utils.csv_import_clean import (
    import_picks_from_csv, 
    validate_week, 
    validate_team, 
    find_player_team,
    find_game_id
)
from utils.nfl_data import load_rosters, get_game_schedule, load_data
from utils.exceptions import ImportError, NFLDataError, ValidationError
import tempfile
import os
import logging
from utils.observability import log_event

logger = logging.getLogger(__name__)


def get_game_players(season: int, game_id: str, rosters_df: pd.DataFrame) -> list:
    """
    Get all players from a specific game from rosters.
    """
    try:
        nfl_data = load_data(season)
        schedule = get_game_schedule(nfl_data, season)
        
        game = schedule[schedule['game_id'] == game_id]
        if game.empty:
            return []
        
        visitor = game.iloc[0]['away_team']
        home = game.iloc[0]['home_team']
        
        players = []
        for team in [visitor, home]:
            team_players = rosters_df[rosters_df['team'] == team]
            for _, player in team_players.iterrows():
                player_name = player.get('full_name', '')
                if player_name:
                    players.append((player_name, team))
        
        players.sort(key=lambda x: x[0])
        return players
    except Exception as e:
        st.error(f"Error loading game players: {e}")
        return []


def validate_csv_data(df: pd.DataFrame, season: int):
    """
    Validate CSV data and return validation results with game/roster info.
    """
    required_cols = ["Week", "Visitor", "Home", "Player", "Picker"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    nfl_data = load_data(season)
    schedule = get_game_schedule(nfl_data, season)
    rosters = load_rosters(season)
    
    # Add validation columns
    df['game_found'] = False
    df['game_id'] = None
    df['player_team'] = None
    df['team_in_game'] = True
    df['has_error'] = False
    df['error_message'] = ""
    
    for idx, row in df.iterrows():
        week = validate_week(row['Week'])
        visitor = validate_team(row['Visitor'])
        home = validate_team(row['Home'])
        
        # Check for empty player name
        player_name = str(row.get('Player', '')).strip() if pd.notna(row.get('Player')) else ''
        if not player_name:
            df.at[idx, 'has_error'] = True
            df.at[idx, 'error_message'] = "Player name is empty"
            continue
        
        if not (week and visitor and home):
            df.at[idx, 'has_error'] = True
            if not week:
                df.at[idx, 'error_message'] = f"Invalid week: {row['Week']}"
            elif not visitor:
                df.at[idx, 'error_message'] = f"Invalid visitor: {row['Visitor']}"
            else:
                df.at[idx, 'error_message'] = f"Invalid home: {row['Home']}"
            continue
        
        # Find game
        game_id = find_game_id(season, week, visitor, home, schedule)
        if game_id:
            df.at[idx, 'game_found'] = True
            df.at[idx, 'game_id'] = game_id
        else:
            df.at[idx, 'has_error'] = True
            df.at[idx, 'error_message'] = f"Game not found: Week {week}, {visitor} @ {home}"
            continue
        
        # Find player team
        player_team = find_player_team(row['Player'], season, rosters)
        if not player_team:
            player_team = 'Unknown'
        
        df.at[idx, 'player_team'] = player_team
        
        # Check if team is in game
        if player_team != 'Unknown' and player_team not in [visitor, home]:
            df.at[idx, 'team_in_game'] = False
            df.at[idx, 'has_error'] = True
            df.at[idx, 'error_message'] = f"{row['Player']} ({player_team}) not in game {visitor} @ {home}"
    
    return {
        'df': df,
        'rosters': rosters,
        'schedule': schedule
    }


def show_clean_csv_import(season: int):
    """
    Display clean CSV import interface with preview and corrections.
    
    Multi-step workflow:
    1. Upload CSV
    2. Preview data with validation
    3. Fix any issues using dropdowns
    4. Confirm and import
    """
    st.subheader("🔄 Import Picks from CSV")
    
    st.markdown("""
    ### Required CSV Format
    
    | Week | Gameday | Picker | Visitor | Home | Player | Position | 1st TD Odds |
    |------|---------|--------|---------|------|--------|----------|-------------|
    | 1 | 2024-09-08 | John | KC | BAL | Patrick Mahomes | QB | +650 |
    
    **Required Columns:** Week, Picker, Visitor, Home, Player  
    **Optional Columns:** Gameday, Position, 1st TD Odds (→ -110)
    """)
    
    # Step 1: Upload file
    uploaded_file = st.file_uploader(
        "Upload CSV File",
        type=['csv'],
        help="CSV file with required columns: Week, Picker, Visitor, Home, Player"
    )
    
    if not uploaded_file:
        return
    
    # Read CSV
    try:
        df = pd.read_csv(uploaded_file)
    except pd.errors.EmptyDataError:
        st.error("❌ CSV file is empty. Please upload a file with data.")
        return
    except pd.errors.ParserError as e:
        st.error(f"❌ CSV Parse Error: {e}")
        st.info("💡 **Tip:** Ensure your CSV is properly formatted with commas separating values.")
        return
    except Exception as e:
        st.error(f"❌ Failed to read CSV: {e}")
        logger.exception("CSV read error")
        return
    
    st.info(f"📋 Loaded {len(df)} rows from CSV")
    
    # Step 2: Validate data
    try:
        with st.spinner("Validating data against NFL schedules and rosters..."):
            validation = validate_csv_data(df, season)
    except NFLDataError as e:
        st.error(f"❌ {e}")
        st.info("💡 **Tip:** NFL data may not be available yet. Check back later or verify the season.")
        return
    except ValueError as e:
        st.error(f"❌ CSV validation failed: {e}")
        st.info("💡 **Tip:** Check that all required columns are present: Week, Picker, Visitor, Home, Player")
        return
    except Exception as e:
        st.error(f"❌ Validation error: {e}")
        logger.exception("CSV validation error")
        return
    
    df = validation['df']
    rosters = validation['rosters']
    schedule = validation['schedule']
    
    error_rows = df[df['has_error']]
    
    st.markdown("---")
    
    # Step 3: Show preview with corrections
    if len(error_rows) > 0:
        st.warning(f"⚠️ Found {len(error_rows)} row(s) with issues that need fixing:")
        
        # Create corrections dict in session state
        if 'import_corrections' not in st.session_state:
            st.session_state['import_corrections'] = {}
        
        # Show each error with correction dropdown
        for idx, (row_idx, row) in enumerate(error_rows.iterrows()):
            row_num = row_idx + 2  # +2 for header and 0-indexing
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.error(f"**Row {row_num}** - {row['error_message']}")
            
            # Show correction options if it's a team validation error
            if row['game_found'] and not row['team_in_game']:
                game_id = row['game_id']
                game = schedule[schedule['game_id'] == game_id]
                if not game.empty:
                    visitor = game.iloc[0]['away_team']
                    home = game.iloc[0]['home_team']
                    game_str = f"{visitor} @ {home}"
                    
                    st.caption(f"Game: {game_str} | Player: {row['Player']}")
                    
                    # Get available players
                    available_players = get_game_players(season, game_id, rosters)
                    
                    if available_players:
                        player_options = [f"{name} ({team})" for name, team in available_players]
                        
                        selected_idx = st.selectbox(
                            f"Select correct player for Row {row_num}",
                            options=range(len(player_options)),
                            format_func=lambda i: player_options[i],
                            key=f"player_select_{row_num}",
                        )
                        
                        selected_player, selected_team = available_players[selected_idx]
                        st.session_state['import_corrections'][row_num] = {
                            'player': selected_player,
                            'team': selected_team
                        }
                        st.success(f"✓ Will use: {selected_player} ({selected_team})")
                    else:
                        st.warning("Could not load available players")
            
            st.divider()
    
    # Step 4: Show preview table
    st.subheader("📊 Data Preview")
    
    # Display columns
    display_df = df[['Week', 'Picker', 'Visitor', 'Home', 'Player', 'player_team']].copy()
    display_df.columns = ['Week', 'Picker', 'Visitor', 'Home', 'Player', 'Player Team']
    display_df.insert(0, 'Row', range(2, len(df) + 2))  # Add row numbers
    
    # Highlight error rows
    def highlight_errors(row):
        if row['Row'] - 2 in df.index and df.loc[row['Row'] - 2, 'has_error']:
            return ['background-color: #ffe6e6'] * len(row)
        return [''] * len(row)
    
    st.dataframe(
        display_df.style.apply(highlight_errors, axis=1),
        width="stretch"
    )
    
    st.markdown("---")
    
    # Step 5: Confirm and import
    col1, col2 = st.columns(2)
    
    with col1:
        auto_create_users = st.checkbox(
            "Auto-Create Users",
            value=True,
            help="Automatically create user accounts for pickers that don't exist"
        )
    
    with col2:
        if st.button("✅ Confirm & Import", type="primary"):
            # Get corrections
            corrections = st.session_state.get('import_corrections', {})
            
            # Save CSV to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
                df.to_csv(tmp, index=False)
                tmp_path = tmp.name
            
            try:
                log_event(
                    "admin.csv_import.clean.start",
                    season=season,
                    corrections=len(corrections),
                    auto_create_users=auto_create_users,
                )
                with st.spinner("Importing picks..."):
                    result = import_picks_from_csv(
                        csv_path=tmp_path,
                        season=season,
                        dry_run=False,
                        auto_create_users=auto_create_users,
                        corrections=corrections
                    )
                
                # Clear session state
                if 'import_corrections' in st.session_state:
                    del st.session_state['import_corrections']
                
                st.success("✅ **Import Complete!**")
                
                # Show results
                col1, col2, col3 = st.columns(3)
                col1.metric("✓ Successful", result.success_count)
                col2.metric("✗ Errors", result.error_count)
                col3.metric("⚠ Warnings", result.warning_count)
                
                if result.success_count > 0:
                    with st.expander("✅ Imported Picks"):
                        success_df = pd.DataFrame(result.success_picks)
                        st.dataframe(success_df, width="stretch")
                
                if result.errors:
                    with st.expander("❌ Errors"):
                        for err in result.errors:
                            st.error(f"Row {err['row']}: {err['message']}")
                
                if result.warnings:
                    with st.expander("⚠️ Warnings"):
                        for warn in result.warnings:
                            st.warning(f"Row {warn['row']}: {warn['message']}")
                log_event(
                    "admin.csv_import.clean.end",
                    season=season,
                    success_count=result.success_count,
                    error_count=result.error_count,
                    warning_count=result.warning_count,
                )
                
            except Exception as e:
                st.error(f"Import failed: {e}")
                logger.error(f"Import error: {e}", exc_info=True)
                log_event("admin.csv_import.clean.error", season=season, error=type(e).__name__)
            finally:
                try:
                    os.unlink(tmp_path)
                except:
                    pass
