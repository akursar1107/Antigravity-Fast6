"""
Import CSV Tab - Upload and ingest picks from CSV files
"""

import streamlit as st
import tempfile
import os
from utils.csv_import import ingest_picks_from_csv


def show_import_csv_tab(season: int) -> None:
    """Display the CSV import interface."""
    st.header("📥 Import Picks from CSV")
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
