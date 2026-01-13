"""
Clean CSV Import Admin Interface
"""

import streamlit as st
from utils.csv_import_clean import import_picks_from_csv, ImportResult
import tempfile
import os


def show_clean_csv_import(season: int):
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
