"""
Admin Exports Tab - Generate and download data snapshots for external analysis.
"""

import streamlit as st
import pandas as pd
from src.utils.exports import (
    export_weekly_picks_snapshot,
    export_leaderboard_history,
    export_player_stats,
    export_user_performance,
    export_season_snapshot,
    list_exported_files,
    DEFAULT_EXPORT_DIR
)
from src.database import get_all_users
from services.performance_service import PickerPerformanceService
import os


def show_exports_tab(season: int, df: pd.DataFrame = None) -> None:
    """Display data export interface."""
    
    st.header("📥 Data Exports")
    
    st.write("""
    Export data for external analysis in Excel, Tableau, or Python notebooks.
    All exports are saved to `data/exports/` and include timestamped filenames.
    """)
    
    st.markdown("---")
    
    # Tab for different export types
    tab1, tab2, tab3 = st.tabs(["Quick Exports", "Bulk Export", "Manage Files"])
    
    # ===== TAB 1: QUICK EXPORTS =====
    with tab1:
        st.subheader("Quick Export Options")
        
        col1, col2 = st.columns(2)
        
        # Export user performance
        with col1:
            st.write("**📊 User Performance Summary**")
            st.write("Export all users' performance metrics (wins, ROI, Brier score, etc)")
            
            if st.button("Export User Performance", key="export_perf"):
                try:
                    users = get_all_users()
                    if users:
                        service = PickerPerformanceService()
                        summaries = []
                        
                        for user in users:
                            summary = service.get_user_performance_summary(user['id'], season)
                            if summary['total_picks'] > 0:
                                summaries.append({
                                    'user_name': user['name'],
                                    'total_picks': summary['total_picks'],
                                    'wins': summary['wins'],
                                    'losses': summary['losses'],
                                    'win_rate': summary['win_rate'],
                                    'brier_score': summary['brier_score'],
                                    'current_streak': summary['streaks'].get('current_streak', 0),
                                    'is_hot': summary['streaks'].get('is_hot', False),
                                })
                        
                        if summaries:
                            perf_df = pd.DataFrame(summaries)
                            export_user_performance(season, summaries)
                            st.success(f"✅ Exported {len(summaries)} users")
                            st.dataframe(perf_df, width="stretch", hide_index=True)
                        else:
                            st.info("No performance data to export.")
                    else:
                        st.warning("No users found.")
                
                except Exception as e:
                    st.error(f"Error exporting user performance: {e}")
        
        # Export player stats
        with col2:
            st.write("**🏈 Player First TD Statistics**")
            st.write("Export first TD rates and stats for all players")
            
            if st.button("Export Player Stats", key="export_players"):
                try:
                    if df is not None and not df.empty:
                        from src.utils.nfl_data import get_first_tds, load_rosters
                        from src.utils.analytics import get_player_first_td_counts, get_position_first_td_counts
                        
                        first_tds = get_first_tds(df)
                        roster_df = load_rosters(season)
                        
                        # Build player stats
                        player_counts = get_player_first_td_counts(first_tds)
                        
                        if not player_counts.empty:
                            export_player_stats(season, player_counts)
                            st.success(f"✅ Exported {len(player_counts)} players")
                            st.dataframe(player_counts.head(20), width="stretch", hide_index=True)
                        else:
                            st.info("No player data to export.")
                    else:
                        st.warning("No game data available.")
                
                except Exception as e:
                    st.error(f"Error exporting player stats: {e}")
    
    # ===== TAB 2: BULK EXPORT =====
    with tab2:
        st.subheader("Bulk Season Export")
        
        st.write("Export all data for the season as multiple files.")
        
        if st.button("📦 Export Complete Season", type="primary"):
            try:
                if df is not None and not df.empty:
                    from src.utils.nfl_data import get_first_tds
                    
                    first_tds = get_first_tds(df)
                    
                    # Get all picks and leaderboard
                    from utils import get_all_picks, get_leaderboard
                    
                    all_picks = get_all_picks(season)
                    leaderboard = get_leaderboard()
                    
                    # Convert to DataFrames if needed
                    picks_df = pd.DataFrame(all_picks) if all_picks else None
                    lb_df = pd.DataFrame(leaderboard) if leaderboard else None
                    
                    result = export_season_snapshot(season, df, picks_df, lb_df)
                    
                    if result['success']:
                        st.success(f"✅ Exported {len(result['files'])} files:")
                        for f in result['files']:
                            st.write(f"  - {os.path.basename(f)}")
                    else:
                        st.error(f"Export failed: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("No data available for export.")
            
            except Exception as e:
                st.error(f"Error during bulk export: {e}")
    
    # ===== TAB 3: MANAGE FILES =====
    with tab3:
        st.subheader("Exported Files")
        
        files = list_exported_files()
        
        if files:
            st.write(f"**Total files:** {len(files)}")
            
            for filename in files[:20]:  # Show last 20
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    file_path = os.path.join(DEFAULT_EXPORT_DIR, filename)
                    try:
                        file_size = os.path.getsize(file_path) / 1024  # KB
                        st.write(f"📄 {filename} ({file_size:.1f} KB)")
                    except:
                        st.write(f"📄 {filename}")
                
                with col2:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            st.download_button(
                                label="⬇️",
                                data=f.read(),
                                file_name=filename,
                                key=f"download_{filename}"
                            )
            
            if len(files) > 20:
                st.info(f"Showing first 20 of {len(files)} files. Older files available in {DEFAULT_EXPORT_DIR}/")
        else:
            st.info(f"No exported files yet. Export data from the tabs above.")
            st.write(f"Files will be saved to: `{DEFAULT_EXPORT_DIR}/`")
    
    st.markdown("---")
    st.caption("Exports are timestamped and non-destructive. Previous exports are preserved in data/exports/")
