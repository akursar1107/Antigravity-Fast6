"""
Clean CSV Import Admin Interface
"""

import streamlit as st
import pandas as pd
from utils.csv_import_clean import import_picks_from_csv, ImportResult
from utils.nfl_data import load_rosters, get_game_schedule, load_data
import tempfile
import os


def get_game_players(season: int, game_id: str, rosters_df: pd.DataFrame) -> list:
    """
    Get all players from a specific game from rosters.
    
    Args:
        season: NFL season
        game_id: Game ID
        rosters_df: Rosters DataFrame
        
    Returns:
        List of (player_name, team) tuples for players in the game
    """
    try:
        nfl_data = load_data(season)
        schedule = get_game_schedule(nfl_data, season)
        
        # Find game details
        game = schedule[schedule['game_id'] == game_id]
        if game.empty:
            return []
        
        visitor = game.iloc[0]['away_team']
        home = game.iloc[0]['home_team']
        
        # Get players from both teams
        players = []
        for team in [visitor, home]:
            team_players = rosters_df[rosters_df['team'] == team]
            for _, player in team_players.iterrows():
                player_name = player.get('full_name', '')
                if player_name:
                    players.append((player_name, team))
        
        # Sort by player name
        players.sort(key=lambda x: x[0])
        return players
    except Exception as e:
        st.error(f"Error loading game players: {e}")
        return []


def show_clean_csv_import(season: int):
    """
    Display clean CSV import interface with validation and error correction.
    
    Args:
        season: Current season year
    """
    st.subheader("🔄 Import Picks from CSV")
    
    st.markdown("""
    ### Required CSV Format
    
    | Week | Gameday | Picker | Visitor | Home | Player | Position | 1st TD Odds |
    |------|---------|--------|---------|------|--------|----------|-------------|
    | 1 | 2024-09-08 | John | KC | BAL | Patrick Mahomes | QB | +650 |
    | 1 | 2024-09-08 | Jane | KC | BAL | Travis Kelce | TE | +900 |
    
    **Required Columns:**
    - Week, Picker, Visitor, Home, Player
    
    **Optional Columns:**
    - Gameday (for reference)
    - Position (informational)
    - 1st TD Odds (defaults to -110 if empty)
    
    **What This Does:**
    1. ✓ Validates week, teams, and finds the game_id
    2. ✓ Looks up player's actual team from NFL rosters
    3. ✓ Validates player's team is in the game (prevents dirty data!)
    4. ✓ Handles odds parsing (empty → -110)
    5. ✓ Creates users that don't exist
    6. ✓ Detects and skips duplicate picks
    """)
    
    # Upload file
    uploaded_file = st.file_uploader(
        "Upload CSV File",
        type=['csv'],
        help="CSV file with required columns: Week, Picker, Visitor, Home, Player"
    )
    
    if not uploaded_file:
        return
    
    # Options
    col1, col2 = st.columns(2)
    
    with col1:
        dry_run = st.checkbox(
            "Dry Run (Validate Only)",
            value=True,
            help="Check this to validate without importing. Uncheck to actually import data."
        )
    
    with col2:
        auto_create_users = st.checkbox(
            "Auto-Create Users",
            value=True,
            help="Automatically create user accounts for pickers that don't exist"
        )
    
    # Import button
    if st.button("🚀 Import Picks", type="primary", disabled=not uploaded_file):
        # Check if we have corrections to apply
        corrections = st.session_state.get('csv_corrections', {})
        
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            with st.spinner("Processing CSV..."):
                result = import_picks_from_csv(
                    csv_path=tmp_path,
                    season=season,
                    dry_run=dry_run,
                    auto_create_users=auto_create_users,
                    corrections=corrections
                )
            
            # Clear corrections after use
            if 'csv_corrections' in st.session_state:
                del st.session_state['csv_corrections']
            
            # Store result in session state for error correction
            st.session_state['last_import_result'] = result
            st.session_state['last_csv_path'] = tmp_path
            st.session_state['last_season'] = season
            
            # Display summary
            if dry_run:
                st.info("**DRY RUN COMPLETE** - No data was imported")
            else:
                st.success("**IMPORT COMPLETE**")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("✓ Successful", result.success_count)
            col2.metric("✗ Errors", result.error_count)
            col3.metric("⚠ Warnings", result.warning_count)
            
            # Show detailed results in expanders
            if result.errors:
                with st.expander(f"❌ Errors ({len(result.errors)})", expanded=True):
                    # Check if we have team validation errors
                    team_errors = [e for e in result.errors if e['field'] == 'Team Validation']
                    
                    if team_errors and dry_run:
                        st.info("💡 **You can fix these by selecting the correct player from the game:**")
                        
                        # Load rosters for corrections
                        rosters = load_rosters(season)
                        corrections = {}
                        
                        for err in team_errors:
                            row_num = err['row']
                            data = err.get('data', {})
                            game = data.get('game', 'Unknown')
                            player_name = data.get('player', 'Unknown')
                            picked_team = data.get('team', 'Unknown')
                            game_id = data.get('game_id')
                            
                            st.error(f"**Row {row_num}** - {player_name} ({picked_team}) not in game {game}")
                            
                            # Load available players in this game
                            if game_id:
                                available_players = get_game_players(season, game_id, rosters)
                                
                                if available_players:
                                    # Create display names with team
                                    player_options = [f"{name} ({team})" for name, team in available_players]
                                    
                                    selected_idx = st.selectbox(
                                        f"Select correct player for Row {row_num}",
                                        options=range(len(player_options)),
                                        format_func=lambda i: player_options[i],
                                        key=f"correct_player_{row_num}",
                                        help=f"Players available in {game}"
                                    )
                                    
                                    selected_player, selected_team = available_players[selected_idx]
                                    corrections[row_num] = {
                                        'player': selected_player,
                                        'team': selected_team
                                    }
                                    st.caption(f"✓ Will use: {selected_player} ({selected_team})")
                                else:
                                    st.warning(f"Could not load available players for {game}")
                            else:
                                st.warning("Could not determine game ID")
                            
                            st.divider()
                        
                        # Show retry button if corrections were made
                        if corrections:
                            st.session_state['csv_corrections'] = corrections
                            if st.button("🔄 Re-import with Corrections", type="primary"):
                                st.success(f"Applying {len(corrections)} correction(s)...")
                                st.rerun()
                    else:
                        # Show other errors normally
                        for err in result.errors:
                            st.error(f"**Row {err['row']}** - {err['field']}: {err['message']}")
                            if err.get('data') and err['field'] != 'Team Validation':
                                st.json(err['data'])
            
            if result.warnings:
                with st.expander(f"⚠️ Warnings ({len(result.warnings)})"):
                    for warn in result.warnings:
                        st.warning(f"**Row {warn['row']}** - {warn['field']}: {warn['message']}")
            
            if result.success_picks:
                with st.expander(f"✅ Successful Imports ({len(result.success_picks)})"):
                    success_df = pd.DataFrame(result.success_picks)
                    st.dataframe(success_df, use_container_width=True)
            
            # Show raw summary
            with st.expander("📋 Detailed Log"):
                st.text(result.get_summary())
            
            # Prompt for actual import if dry run
            if dry_run and result.error_count == 0 and result.success_count > 0:
                st.info("✅ Validation passed! Uncheck 'Dry Run' above and click Import to insert data.")
        
        except Exception as e:
            st.error(f"Import failed: {e}")
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass


def show_error_correction_ui(season: int, result: ImportResult):
    """
    Show UI for correcting validation errors by selecting correct players.
    
    Args:
        season: NFL season
        result: ImportResult object with errors
    """
    st.subheader("🔧 Fix Validation Errors")
    
    # Load rosters once
    rosters = load_rosters(season)
    
    team_errors = [e for e in result.errors if e['field'] == 'Team Validation']
    
    if not team_errors:
        st.info("No team validation errors to fix")
        return
    
    st.write(f"Found {len(team_errors)} team validation error(s). Select the correct player from the game:")
    
    corrections = {}
    
    for err in team_errors:
        row_num = err['row']
        data = err.get('data', {})
        game = data.get('game', 'Unknown')
        player_name = data.get('player', 'Unknown')
        
        st.markdown(f"### Row {row_num}: {player_name}")
        st.caption(f"Game: {game} | Error: {err['message']}")
        
        # Get available players in this game
        game_id = data.get('game_id')
        if game_id:
            available_players = get_game_players(season, game_id, rosters)
            
            if available_players:
                player_options = [f"{name} ({team})" for name, team in available_players]
                selected = st.selectbox(
                    f"Select correct player for Row {row_num}",
                    options=player_options,
                    key=f"correct_player_{row_num}"
                )
                
                if selected:
                    # Extract selected player name and team
                    selected_player, selected_team = available_players[player_options.index(selected)]
                    corrections[row_num] = {
                        'player': selected_player,
                        'team': selected_team
                    }
            else:
                st.warning(f"Could not load available players for {game}")
        else:
            st.warning("Could not determine game ID for this error")
    
    if corrections:
        st.success(f"Marked {len(corrections)} correction(s)")
        return corrections
    
    return {}
    """
    Display clean CSV import interface with validation.
    
    Args:
        season: Current season year
    """
    st.subheader("🔄 Import Picks from CSV")
    
    st.markdown("""
    ### Required CSV Format
    
    | Week | Gameday | Picker | Visitor | Home | Player | Position | 1st TD Odds |
    |------|---------|--------|---------|------|--------|----------|-------------|
    | 1 | 2024-09-08 | John | KC | BAL | Patrick Mahomes | QB | +650 |
    | 1 | 2024-09-08 | Jane | KC | BAL | Travis Kelce | TE | +900 |
    
    **Required Columns:**
    - Week, Picker, Visitor, Home, Player
    
    **Optional Columns:**
    - Gameday (for reference)
    - Position (informational)
    - 1st TD Odds (defaults to -110 if empty)
    
    **What This Does:**
    1. ✓ Validates week, teams, and finds the game_id
    2. ✓ Looks up player's actual team from NFL rosters
    3. ✓ Validates player's team is in the game (prevents dirty data!)
    4. ✓ Handles odds parsing (empty → -110)
    5. ✓ Creates users that don't exist
    6. ✓ Detects and skips duplicate picks
    """)
    
    # Upload file
    uploaded_file = st.file_uploader(
        "Upload CSV File",
        type=['csv'],
        help="CSV file with required columns: Week, Picker, Visitor, Home, Player"
    )
    
    if not uploaded_file:
        return
    
    # Options
    col1, col2 = st.columns(2)
    
    with col1:
        dry_run = st.checkbox(
            "Dry Run (Validate Only)",
            value=True,
            help="Check this to validate without importing. Uncheck to actually import data."
        )
    
    with col2:
        auto_create_users = st.checkbox(
            "Auto-Create Users",
            value=True,
            help="Automatically create user accounts for pickers that don't exist"
        )
    
    # Import button
    if st.button("🚀 Import Picks", type="primary", disabled=not uploaded_file):
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            with st.spinner("Processing CSV..."):
                result = import_picks_from_csv(
                    csv_path=tmp_path,
                    season=season,
                    dry_run=dry_run,
                    auto_create_users=auto_create_users
                )
            
            # Display summary
            if dry_run:
                st.info("**DRY RUN COMPLETE** - No data was imported")
            else:
                st.success("**IMPORT COMPLETE**")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("✓ Successful", result.success_count)
            col2.metric("✗ Errors", result.error_count)
            col3.metric("⚠ Warnings", result.warning_count)
            
            # Show detailed results in expanders
            if result.errors:
                with st.expander(f"❌ Errors ({len(result.errors)})", expanded=True):
                    for err in result.errors:
                        st.error(f"**Row {err['row']}** - {err['field']}: {err['message']}")
                        if err.get('data'):
                            st.json(err['data'])
            
            if result.warnings:
                with st.expander(f"⚠️ Warnings ({len(result.warnings)})"):
                    for warn in result.warnings:
                        st.warning(f"**Row {warn['row']}** - {warn['field']}: {warn['message']}")
            
            if result.success_picks:
                with st.expander(f"✅ Successful Imports ({len(result.success_picks)})"):
                    import pandas as pd
                    success_df = pd.DataFrame(result.success_picks)
                    st.dataframe(success_df, use_container_width=True)
            
            # Show raw summary
            with st.expander("📋 Detailed Log"):
                st.text(result.get_summary())
            
            # Prompt for actual import if dry run
            if dry_run and result.error_count == 0 and result.success_count > 0:
                st.info("✅ Validation passed! Uncheck 'Dry Run' above and click Import to insert data.")
            
        except Exception as e:
            st.error(f"Import failed: {e}")
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
