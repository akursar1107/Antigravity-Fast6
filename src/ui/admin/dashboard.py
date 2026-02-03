"""
Admin Dashboard - System overview and quick actions
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from database import (
    get_all_users, get_all_weeks, get_week_all_picks,
    get_ungraded_picks, get_leaderboard
)
import config


def show_dashboard_tab(season: int, schedule: pd.DataFrame) -> None:
    """
    Display admin dashboard with system overview and quick actions.
    
    Provides:
    - Key metrics and system status
    - Alerts for pending actions
    - Quick action buttons
    - Recent activity summary
    """
    st.header("🏠 Admin Dashboard")
    st.markdown("Welcome to the Fast6 Admin Center. Here's your system overview.")
    
    # Get current data
    users = get_all_users()
    weeks = get_all_weeks()
    current_week = config.CURRENT_WEEK
    
    # Filter weeks for current season
    season_weeks = [w for w in weeks if w.get('season') == season]
    
    # Get current week data
    current_week_record = next(
        (w for w in season_weeks if w.get('week_number') == current_week),
        None
    )
    
    # Calculate metrics
    total_users = len(users)
    total_picks_this_week = 0
    ungraded_picks = []
    
    if current_week_record:
        week_picks = get_week_all_picks(current_week_record['id'])
        total_picks_this_week = len(week_picks)
        ungraded_picks = [p for p in week_picks if p.get('is_correct') is None]
    
    # Get games for current week
    games_this_week = schedule[schedule['week'] == current_week] if not schedule.empty else pd.DataFrame()
    expected_picks = total_users * len(games_this_week) if not games_this_week.empty else 0
    pick_completion = (total_picks_this_week / expected_picks * 100) if expected_picks > 0 else 0
    
    # Database backup check
    archive_dir = Path(__file__).parent.parent.parent.parent / "archive"
    last_backup = None
    backup_age_days = None
    
    if archive_dir.exists():
        backups = sorted(
            [f for f in archive_dir.glob("fast6_*.db.bak")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        if backups:
            last_backup = datetime.fromtimestamp(backups[0].stat().st_mtime)
            backup_age_days = (datetime.now() - last_backup).days
    
    # ========== KEY METRICS ==========
    st.subheader("📊 System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Users",
            value=total_users,
            delta=None
        )
    
    with col2:
        st.metric(
            label="Current Week",
            value=f"Week {current_week}",
            delta=None
        )
    
    with col3:
        st.metric(
            label="Picks This Week",
            value=f"{total_picks_this_week}/{expected_picks}",
            delta=f"{pick_completion:.0f}%" if expected_picks > 0 else "N/A"
        )
    
    with col4:
        st.metric(
            label="Pending Grading",
            value=len(ungraded_picks),
            delta="Needs attention" if len(ungraded_picks) > 5 else None,
            delta_color="inverse"
        )
    
    # Progress bar for pick completion
    if expected_picks > 0:
        st.progress(pick_completion / 100, text=f"Pick Completion: {pick_completion:.1f}%")
    
    st.markdown("---")
    
    # ========== ALERTS ==========
    st.subheader("⚠️ Alerts & Notifications")
    
    alerts = []
    
    # Check for users who haven't submitted picks
    if current_week_record and expected_picks > 0:
        user_pick_counts = {}
        for pick in get_week_all_picks(current_week_record['id']):
            user_id = pick.get('user_id')
            user_pick_counts[user_id] = user_pick_counts.get(user_id, 0) + 1
        
        expected_per_user = len(games_this_week)
        missing_picks_users = []
        
        for user in users:
            user_picks = user_pick_counts.get(user['id'], 0)
            if user_picks < expected_per_user:
                missing_picks_users.append(f"{user['name']} ({user_picks}/{expected_per_user})")
        
        if missing_picks_users:
            alerts.append({
                'type': 'warning',
                'icon': '👤',
                'message': f"{len(missing_picks_users)} user(s) with incomplete picks: {', '.join(missing_picks_users[:3])}"
            })
    
    # Check for pending grading
    if len(ungraded_picks) > 0:
        alerts.append({
            'type': 'info',
            'icon': '🎯',
            'message': f"{len(ungraded_picks)} pick(s) waiting to be graded"
        })
    
    # Check backup age
    if backup_age_days is not None:
        if backup_age_days > 7:
            alerts.append({
                'type': 'error',
                'icon': '💾',
                'message': f"Database backup is {backup_age_days} days old - consider archiving"
            })
        elif backup_age_days > 3:
            alerts.append({
                'type': 'warning',
                'icon': '💾',
                'message': f"Database last backed up {backup_age_days} days ago"
            })
    else:
        alerts.append({
            'type': 'warning',
            'icon': '💾',
            'message': "No database backups found"
        })
    
    # Check for games starting soon
    if not games_this_week.empty:
        try:
            games_this_week = games_this_week.copy()
            games_this_week['game_datetime'] = pd.to_datetime(games_this_week['game_date'])
            now = datetime.now()
            upcoming_games = games_this_week[games_this_week['game_datetime'] > now]
            
            if not upcoming_games.empty:
                next_game = upcoming_games.iloc[0]
                time_until = next_game['game_datetime'] - now
                hours_until = time_until.total_seconds() / 3600
                
                if hours_until < 24:
                    alerts.append({
                        'type': 'info',
                        'icon': '🏈',
                        'message': f"Next game in {hours_until:.1f} hours: {next_game['away_team']} @ {next_game['home_team']}"
                    })
        except Exception:
            pass  # Skip if date parsing fails
    
    # Display alerts
    if alerts:
        for alert in alerts:
            if alert['type'] == 'error':
                st.error(f"{alert['icon']} {alert['message']}")
            elif alert['type'] == 'warning':
                st.warning(f"{alert['icon']} {alert['message']}")
            else:
                st.info(f"{alert['icon']} {alert['message']}")
    else:
        st.success("✅ All systems nominal - no alerts")
    
    st.markdown("---")
    
    # ========== QUICK ACTIONS ==========
    st.subheader("🔥 Quick Actions")
    
    col_a1, col_a2, col_a3 = st.columns(3)
    
    with col_a1:
        if st.button("🎯 Grade All Pending", key="qa_grade", use_container_width=True, type="primary"):
            st.info("Navigate to 'Grade Picks' tab to grade pending picks")
    
    with col_a2:
        if st.button("📥 Import CSV", key="qa_import", use_container_width=True):
            st.info("Navigate to 'Tools' tab for CSV import")
    
    with col_a3:
        if st.button("💾 Backup Database", key="qa_backup", use_container_width=True):
            st.info("Navigate to 'Settings' tab to create backup")
    
    st.markdown("---")
    
    # ========== LEADERBOARD PREVIEW ==========
    st.subheader("🏆 Current Standings (Top 5)")
    
    try:
        leaderboard = get_leaderboard()  # Get all, then limit
        if leaderboard:
            leaderboard = leaderboard[:5]  # Top 5 only
            leaderboard_df = pd.DataFrame(leaderboard)
            
            # Add rank if not present
            if 'rank' not in leaderboard_df.columns:
                leaderboard_df['rank'] = range(1, len(leaderboard_df) + 1)
            
            # Select available columns
            display_columns = []
            column_mapping = {}
            
            if 'rank' in leaderboard_df.columns:
                display_columns.append('rank')
                column_mapping['rank'] = 'Rank'
            if 'name' in leaderboard_df.columns:
                display_columns.append('name')
                column_mapping['name'] = 'Player'
            if 'correct' in leaderboard_df.columns:
                display_columns.append('correct')
                column_mapping['correct'] = 'Wins'
            if 'total' in leaderboard_df.columns:
                display_columns.append('total')
                column_mapping['total'] = 'Picks'
            if 'accuracy' in leaderboard_df.columns:
                display_columns.append('accuracy')
                column_mapping['accuracy'] = 'Accuracy'
            if 'roi' in leaderboard_df.columns:
                display_columns.append('roi')
                column_mapping['roi'] = 'ROI'
            
            if not display_columns:
                st.info("Leaderboard data structure is empty")
            else:
                display_df = leaderboard_df[display_columns].copy()
                
                # Format accuracy and ROI if present
                if 'accuracy' in display_df.columns:
                    display_df['accuracy'] = display_df['accuracy'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
                if 'roi' in display_df.columns:
                    display_df['roi'] = display_df['roi'].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/A")
                
                # Create column config
                col_config = {}
                if 'rank' in display_df.columns:
                    col_config['rank'] = st.column_config.NumberColumn('Rank', format='#%d')
                if 'name' in display_df.columns:
                    col_config['name'] = 'Player'
                if 'correct' in display_df.columns:
                    col_config['correct'] = st.column_config.NumberColumn('Wins')
                if 'total' in display_df.columns:
                    col_config['total'] = st.column_config.NumberColumn('Picks')
                if 'accuracy' in display_df.columns:
                    col_config['accuracy'] = 'Accuracy'
                if 'roi' in display_df.columns:
                    col_config['roi'] = 'ROI'
                
                st.dataframe(
                    display_df,
                    hide_index=True,
                    use_container_width=True,
                    column_config=col_config
                )
        else:
            st.info("No graded picks yet this season")
    except Exception as e:
        st.warning(f"Could not load leaderboard: {e}")
    
    st.markdown("---")
    
    # ========== SYSTEM INFO ==========
    st.subheader("ℹ️ System Information")
    
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        st.markdown("**Configuration:**")
        st.text(f"Season: {config.CURRENT_SEASON}")
        st.text(f"Week: {config.CURRENT_WEEK}")
        st.text(f"Database: fast6.db")
        if last_backup:
            st.text(f"Last Backup: {last_backup.strftime('%Y-%m-%d %H:%M')}")
    
    with col_s2:
        st.markdown("**Database Stats:**")
        st.text(f"Users: {total_users}")
        st.text(f"Weeks Tracked: {len(season_weeks)}")
        st.text(f"Total Picks (This Week): {total_picks_this_week}")
        st.text(f"Games This Week: {len(games_this_week)}")
