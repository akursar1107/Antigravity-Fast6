"""
Admin Settings Tab - System configuration and dangerous operations
"""

import streamlit as st
import shutil
from pathlib import Path
from datetime import datetime
from src.database import get_db_connection


def show_settings_tab() -> None:
    """
    Display system settings and administrative operations.
    
    Provides:
    - Database backup and archive management
    - System configuration
    - Dangerous operations (in protected danger zone)
    """
    st.header("⚙️ System Settings")
    st.markdown("Manage system configuration and database operations.")
    
    # ========== DATABASE BACKUP ==========
    st.subheader("💾 Database Management")
    
    col_db1, col_db2 = st.columns(2)
    
    with col_db1:
        st.markdown("**Create Backup**")
        st.markdown("Archive the current database to preserve your data.")
        
        if st.button("📦 Create Backup Now", key="backup_db_btn", type="primary", use_container_width=True):
            try:
                # Database path
                db_path = Path(__file__).parent.parent.parent.parent / "data" / "fast6.db"
                archive_dir = Path(__file__).parent.parent.parent.parent / "archive"
                
                if not db_path.exists():
                    st.error("❌ Database file not found")
                else:
                    # Create archive directory if it doesn't exist
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Generate timestamped filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    archive_path = archive_dir / f"fast6_{timestamp}.db.bak"
                    
                    # Copy database to archive
                    shutil.copy2(db_path, archive_path)
                    
                    # Get file size for display
                    file_size = archive_path.stat().st_size / 1024  # KB
                    
                    st.success(f"✅ Database backed up successfully!")
                    st.info(f"📁 Saved to: `{archive_path.name}` ({file_size:.1f} KB)")
                    
            except Exception as e:
                st.error(f"❌ Failed to create backup: {str(e)}")
    
    with col_db2:
        st.markdown("**Recent Backups**")
        try:
            archive_dir = Path(__file__).parent.parent.parent.parent / "archive"
            if archive_dir.exists():
                backups = sorted(
                    [f for f in archive_dir.glob("fast6_*.db.bak")],
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
                
                if backups:
                    st.markdown(f"*{len(backups)} backup(s) found:*")
                    for backup in backups[:5]:  # Show last 5
                        size_kb = backup.stat().st_size / 1024
                        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
                        
                        col_b1, col_b2 = st.columns([3, 1])
                        with col_b1:
                            st.caption(f"📄 {backup.name}")
                            st.caption(f"   {mtime.strftime('%Y-%m-%d %H:%M')} ({size_kb:.1f} KB)")
                    
                    if len(backups) > 5:
                        st.caption(f"... and {len(backups) - 5} more")
                else:
                    st.info("No backups found yet.")
            else:
                st.info("Archive directory not found.")
        except Exception as e:
            st.warning(f"Could not read archives: {str(e)}")
    
    st.markdown("---")
    
    # ========== DATABASE INFO ==========
    st.subheader("📊 Database Information")
    
    try:
        db_path = Path(__file__).parent.parent.parent.parent / "data" / "fast6.db"
        
        if db_path.exists():
            db_size = db_path.stat().st_size / 1024  # KB
            db_modified = datetime.fromtimestamp(db_path.stat().st_mtime)
            
            col_info1, col_info2, col_info3 = st.columns(3)
            
            with col_info1:
                st.metric("Database Size", f"{db_size:.1f} KB")
            
            with col_info2:
                st.metric("Last Modified", db_modified.strftime('%m/%d %H:%M'))
            
            with col_info3:
                # Get row counts
                try:
                    with get_db_connection() as conn:
                        cursor = conn.execute("SELECT COUNT(*) FROM picks")
                        pick_count = cursor.fetchone()[0]
                    st.metric("Total Picks", f"{pick_count:,}")
                except Exception:
                    st.metric("Total Picks", "N/A")
        else:
            st.warning("Database file not found")
    
    except Exception as e:
        st.error(f"Could not read database info: {e}")
    
    st.markdown("---")
    
    # ========== SYSTEM CONFIGURATION ==========
    st.subheader("🔧 System Configuration")

    st.markdown("""
    **Current Configuration:**
    - Database: `data/fast6.db`
    - Archive Location: `archive/`
    - Backup Naming: `fast6_YYYYMMDD_HHMMSS.db.bak`

    *Note: Configuration is currently read from `config.py`. Future versions will support
    dynamic configuration management.*
    """)

    st.markdown("---")

    # ========== PREDICTION MARKET APIS ==========
    _show_prediction_market_settings()

    st.markdown("---")
    
    # ========== DANGER ZONE ==========
    st.subheader("🗑️ Danger Zone")
    st.error("⚠️ **WARNING:** Operations below are IRREVERSIBLE and can cause data loss!")
    
    with st.expander("⚠️ View Dangerous Operations", expanded=False):
        st.markdown("""
        ### Database Deletion
        
        **This will permanently delete the current user picks database file (`fast6.db`).**
        
        ⚠️ **Before proceeding:**
        1. Create a backup using the button above
        2. Verify the backup was successful
        3. Understand this cannot be undone
        """)
        
        # Multi-step confirmation
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            st.markdown("**Step 1:** Check if backup exists")
            
            archive_dir = Path(__file__).parent.parent.parent.parent / "archive"
            has_recent_backup = False
            
            if archive_dir.exists():
                backups = sorted(
                    [f for f in archive_dir.glob("fast6_*.db.bak")],
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
                if backups:
                    last_backup = datetime.fromtimestamp(backups[0].stat().st_mtime)
                    age_minutes = (datetime.now() - last_backup).total_seconds() / 60
                    
                    if age_minutes < 30:  # Recent backup within 30 minutes
                        has_recent_backup = True
                        st.success(f"✅ Recent backup found ({age_minutes:.0f} min ago)")
                    else:
                        st.warning(f"⚠️ Last backup is {age_minutes/60:.1f} hours old")
                else:
                    st.error("❌ No backups found")
            else:
                st.error("❌ Archive directory not found")
        
        with col_d2:
            st.markdown("**Step 2:** Type database name")
            delete_confirm = st.text_input(
                "Type **fast6.db** to confirm",
                key="delete_db_confirm",
                placeholder="fast6.db"
            )
        
        st.markdown("**Step 3:** Delete database")
        
        # Require backup AND correct text
        can_delete = has_recent_backup and delete_confirm.strip() == "fast6.db"
        
        delete_button_disabled = not can_delete
        
        if st.button(
            "🗑️ PERMANENTLY DELETE DATABASE",
            key="delete_db_btn",
            type="secondary",
            disabled=delete_button_disabled,
            use_container_width=True
        ):
            # Final confirmation
            if 'final_delete_confirm' not in st.session_state:
                st.session_state.final_delete_confirm = True
                st.warning("⚠️ Click DELETE button again to confirm")
                st.stop()
            
            # Actually delete
            try:
                db_path = Path(__file__).parent.parent.parent.parent / "data" / "fast6.db"
                if db_path.exists():
                    db_path.unlink()
                    st.success("✅ Database deleted. Restore from archive if needed.")
                    del st.session_state.final_delete_confirm
                    st.rerun()
                else:
                    st.info("Database file not found; nothing to delete.")
            except Exception as e:
                st.error(f"❌ Failed to delete database: {str(e)}")
        
        if delete_button_disabled:
            if not has_recent_backup:
                st.error("❌ Cannot delete: Create a backup first")
            if delete_confirm.strip() != "fast6.db":
                st.error("❌ Cannot delete: Type 'fast6.db' exactly")
    
    st.markdown("---")
    
    # ========== AUDIT LOG (Future) ==========
    st.subheader("📜 Activity Log")
    st.info("🚧 Activity logging coming in future update. This will show recent admin actions.")


def _show_prediction_market_settings():
    """Show prediction market API configuration and controls."""
    import config
    from services.market_data_service import MarketDataService, get_week_dates
    from src.utils.prediction_markets import test_connections, get_enabled_sources

    st.subheader("🎲 Prediction Market APIs")
    st.markdown("Configure and manage Polymarket and Kalshi integrations")

    # Status display
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Polymarket**")
        pm_status = "✅ Enabled" if config.POLYMARKET_ENABLED else "❌ Disabled"
        st.write(f"Status: {pm_status}")
        if config.POLYMARKET_ENABLED:
            st.write(f"Cache TTL: {config.POLYMARKET_CACHE_TTL}s")

    with col2:
        st.markdown("**Kalshi**")
        kalshi_status = "✅ Enabled" if config.KALSHI_ENABLED else "❌ Disabled"
        st.write(f"Status: {kalshi_status}")
        if config.KALSHI_ENABLED:
            has_key = "✅ Configured" if config.KALSHI_API_KEY else "⚠️ Not configured (using public API)"
            st.write(f"API Key: {has_key}")

    # Test connections
    st.markdown("---")
    st.markdown("**Connection Test**")

    if st.button("🔄 Test API Connections", key="test_pm_connections"):
        with st.spinner("Testing connections..."):
            results = test_connections()

            for source, success in results.items():
                if success:
                    st.success(f"✅ {source.title()}: Connected successfully")
                else:
                    st.error(f"❌ {source.title()}: Connection failed")

    # Manual data fetch
    st.markdown("---")
    st.markdown("**Manual Data Fetch**")
    st.markdown("Fetch current odds from prediction markets for a specific week")

    col_fetch1, col_fetch2 = st.columns(2)

    with col_fetch1:
        fetch_season = st.number_input(
            "Season",
            value=config.CURRENT_SEASON,
            min_value=2020,
            max_value=2030,
            key="pm_fetch_season"
        )

    with col_fetch2:
        fetch_week = st.number_input(
            "Week",
            value=1,
            min_value=1,
            max_value=22,
            key="pm_fetch_week"
        )

    if st.button("📥 Fetch Market Odds", type="primary", key="fetch_pm_odds"):
        enabled = get_enabled_sources()
        if not enabled:
            st.warning("No prediction market sources are enabled")
        else:
            with st.spinner(f"Fetching odds from {', '.join(enabled)}..."):
                try:
                    service = MarketDataService()
                    start_date, end_date = get_week_dates(fetch_season, fetch_week)

                    result = service.fetch_and_store_week_odds(
                        fetch_season, fetch_week, start_date, end_date
                    )

                    total = sum(result.values())
                    if total > 0:
                        st.success(f"✅ Fetched and stored {total} odds records!")
                        for source, count in result.items():
                            st.info(f"  • {source.title()}: {count} records")
                    else:
                        st.warning("No NFL first TD markets found for this week")

                except Exception as e:
                    st.error(f"❌ Error fetching odds: {str(e)}")

    # Link results
    st.markdown("---")
    st.markdown("**Link Results to Market Odds**")
    st.markdown("After games are complete, link market odds to actual first TD results")

    col_link1, col_link2 = st.columns(2)

    with col_link1:
        link_season = st.number_input(
            "Season",
            value=config.CURRENT_SEASON,
            min_value=2020,
            max_value=2030,
            key="pm_link_season"
        )

    with col_link2:
        link_week = st.number_input(
            "Week",
            value=1,
            min_value=1,
            max_value=22,
            key="pm_link_week"
        )

    if st.button("🔗 Link Results", key="link_pm_results"):
        with st.spinner("Linking results..."):
            try:
                service = MarketDataService()
                stats = service.link_week_results(link_season, link_week)

                st.success("✅ Results linked!")
                st.info(f"""
                **Linking Summary:**
                - Games processed: {stats.get('games_processed', 0)}
                - Odds linked: {stats.get('odds_linked', 0)}
                - Matches found: {stats.get('matches_found', 0)}
                - Favorites correct: {stats.get('favorites_correct', 0)}
                - Accuracy rate: {stats.get('accuracy_rate', 0)*100:.1f}%
                """)

            except Exception as e:
                st.error(f"❌ Error linking results: {str(e)}")
