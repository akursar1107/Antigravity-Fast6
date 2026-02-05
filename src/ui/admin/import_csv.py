"""
Import CSV Tab - Upload and ingest picks from CSV files
"""

import streamlit as st
import tempfile
import os
from src.utils.csv_import import ingest_picks_from_csv
from views.admin.csv_import_clean import show_clean_csv_import
from src.utils.observability import log_event


def show_import_csv_tab(season: int) -> None:
    """
    Display CSV import tab for bulk pick uploads.
    
    Args:
        season: Current NFL season year
    
    Allows admins to:
    - Upload CSV files with pick data
    - Preview picks before import
    - Validate pick data (teams, players, weeks)
    - Handle duplicates and conflicts
    - Import picks in bulk to database
    
    CSV format expected:
    - user_name: User name (must exist in database)
    - week: Game week number
    - team: Team abbreviation
    - player_name: Player full name
    - odds: Optional point spread/odds
    - game_id: Optional unique game identifier
    """
    st.header("📥 Import Picks from CSV")
    
    # Choose import method
    import_method = st.radio(
        "Select Import Method",
        options=["🆕 Clean Import (Recommended)", "📦 Legacy Import"],
        index=0,
        help="Clean Import: Validates teams using rosters, prevents dirty data. Legacy Import: Direct import from old format."
    )
    
    if import_method == "🆕 Clean Import (Recommended)":
        show_clean_csv_import(season)
    else:
        show_legacy_import(season)


def show_legacy_import(season: int) -> None:
    """
    Legacy CSV import method (original implementation).
    Kept for backward compatibility with old CSV format.
    """
    st.markdown("Upload a CSV in the same format as 'First TD - 2025.csv'. Only regular-season weeks (1–18) are imported.")

    # Season selection for mapping
    sel_season = st.number_input("Season", value=season, min_value=2000, max_value=2100, step=1)
    uploaded = st.file_uploader("Upload CSV", type=["csv"], accept_multiple_files=False)
    run_import = st.button("Run Import", type="primary", disabled=(uploaded is None))

    if run_import and uploaded is not None:
        # Write to a temporary file path for ingestion
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(uploaded.getbuffer())
            tmp_path = tmp.name
        try:
            log_event("admin.csv_import.legacy.start", season=int(sel_season), filename=uploaded.name)
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
            log_event(
                "admin.csv_import.legacy.end",
                season=int(sel_season),
                picks_imported=summary.get('picks_imported', 0),
                results_imported=summary.get('results_imported', 0),
                picks_deleted=picks_deleted,
                results_deleted=results_deleted,
            )
            if st.button("Refresh Admin View", type="secondary"):
                st.rerun()
        except Exception as e:
            # Show both an error message and a toast for visibility
            st.error(f"Import failed: {e}")
            try:
                st.toast(f"Import failed: {e}")
            except Exception:
                pass
            log_event("admin.csv_import.legacy.error", season=int(sel_season), error=type(e).__name__)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
