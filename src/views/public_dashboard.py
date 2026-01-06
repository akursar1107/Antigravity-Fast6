"""
Public Dashboard - Read-only views for all users.
Displays first TD analysis, leaderboard, picks history, and weekly schedule.
Data sourced from NFL API and SQLite database.
"""

import streamlit as st
import pandas as pd
from data_processor import (
    load_data, get_touchdowns, get_first_tds, get_game_schedule,
    get_team_first_td_counts, get_player_first_td_counts, get_position_first_td_counts,
    load_rosters
)
from database import (
    init_db, get_leaderboard, get_user_stats, get_all_users, get_all_weeks,
    get_user_week_picks, get_result_for_pick, get_weekly_summary
)


def show_first_td_tab(first_tds: pd.DataFrame) -> None:
    """Display first touchdowns for each game."""
    st.header("First Touchdowns per Game")
    st.markdown("This list shows the first touchdown scored in every game of the season.")
    
    if not first_tds.empty:
        display_cols = [
            'week', 'away_team', 'home_team', 'td_player_name', 'posteam', 'qtr', 'desc'
        ]
        valid_cols = [c for c in display_cols if c in first_tds.columns]
        
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


def show_all_touchdowns_tab(all_tds: pd.DataFrame) -> None:
    """Display all touchdowns with filtering options."""
    st.header("All Touchdowns Scored")
    
    if not all_tds.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            selected_team = st.multiselect(
                "Filter by Scoring Team", 
                options=sorted(all_tds['posteam'].dropna().unique())
            )
        with col_f2:
            selected_week = st.multiselect(
                "Filter by Week", 
                options=sorted(all_tds['week'].dropna().unique())
            )
        
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


def show_schedule_tab(schedule: pd.DataFrame) -> None:
    """Display weekly schedule and results."""
    st.header("Weekly Schedule & Results")
    
    if not schedule.empty:
        available_weeks = sorted(schedule['week'].unique())
        default_ix = len(available_weeks) - 1 if available_weeks else 0
        
        selected_schedule_week = st.selectbox(
            "Select Week", 
            options=available_weeks, 
            index=default_ix,
            format_func=lambda x: f"Week {x}"
        )
        
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


def show_analysis_tab(df: pd.DataFrame, season: int) -> None:
    """Display analysis: team rankings, player leaderboard, position stats."""
    st.header("First Touchdown Analysis")
    
    if df.empty:
        st.info("No data available for analysis.")
        return
    
    # Calculate first TDs for current filtered data
    analyzed_first_tds = get_first_tds(df)
    
    col_a1, col_a2 = st.columns(2)
    
    with col_a1:
        st.subheader("Team Rankings")
        team_stats = get_team_first_td_counts(analyzed_first_tds)
        if not team_stats.empty:
            team_stats = team_stats.sort_values('First TDs', ascending=False)
            st.dataframe(
                team_stats, 
                column_config={
                    "Team": st.column_config.TextColumn("Team"),
                    "First TDs": st.column_config.ProgressColumn(
                        "First TDs", 
                        format="%d", 
                        min_value=0, 
                        max_value=int(team_stats['First TDs'].max())
                    )
                },
                hide_index=True,
                width="stretch"
            )
        else:
            st.caption("No data.")

    with col_a2:
        st.subheader("Player Leaderboard")
        player_stats = get_player_first_td_counts(analyzed_first_tds)
        if not player_stats.empty:
            player_stats = player_stats.sort_values('First TDs', ascending=False)
            top_players = player_stats.head(20)
            st.bar_chart(top_players.set_index('Player'))
        else:
            st.caption("No data.")
    
    st.divider()
    
    st.subheader("First TDs by Position")
    with st.spinner("Analyzing positions..."):
        roster_for_stats = load_rosters(season)
        pos_stats = get_position_first_td_counts(analyzed_first_tds, roster_for_stats)
        
    if not pos_stats.empty:
        pos_stats = pos_stats.sort_values('First TDs', ascending=False)
        st.bar_chart(pos_stats.set_index('Position'))
    else:
        st.caption("No position data available (could not link IDs).")


def show_public_dashboard(df: pd.DataFrame, season: int, schedule: pd.DataFrame) -> None:
    """Main dashboard view with tabs for different data views."""
    # Initialize database
    init_db()
    
    if df.empty:
        st.warning("No data found for this season or an error occurred.")
        return
    
    # Key Metrics
    all_tds = get_touchdowns(df)
    first_tds = get_first_tds(df)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Games", df['game_id'].nunique())
    with col2:
        st.metric("Total Touchdowns", len(all_tds))
    with col3:
        if not first_tds.empty:
            top_scorer = first_tds['td_player_name'].mode()
            if not top_scorer.empty:
                st.metric("Top First TD Scorer", top_scorer[0])

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏆 Leaderboard",
        "📝 Week Picks",
        "📋 All Touchdowns", 
        "📅 Weekly Schedule", 
        "📊 Analysis",
        "🚀 First TD of Game"
    ])

    with tab1:
        show_leaderboard_tab()

    with tab2:
        show_week_picks_tab(season)

    with tab3:
        show_all_touchdowns_tab(all_tds)
            
    with tab4:
        show_schedule_tab(schedule)

    with tab5:
        show_analysis_tab(df, season)

    with tab6:
        show_first_td_tab(first_tds)


def show_leaderboard_tab() -> None:
    """Display group leaderboard with cumulative stats."""
    st.header("🏆 Group Leaderboard")
    st.markdown("Member statistics and rankings across all weeks.")
    
    # Get cumulative leaderboard
    leaderboard = get_leaderboard()
    
    if leaderboard:
        leaderboard_df = pd.DataFrame(leaderboard)
        
        # Display with formatting
        st.dataframe(
            leaderboard_df[[
                'name', 'total_picks', 'wins', 'losses', 'total_return', 'avg_return'
            ]].rename(columns={
                'name': 'Member',
                'total_picks': 'Picks',
                'wins': 'Wins',
                'losses': 'Losses',
                'total_return': 'Total ROI',
                'avg_return': 'Avg Return'
            }),
            width='stretch',
            hide_index=True,
            column_config={
                "Picks": st.column_config.NumberColumn(format="%d"),
                "Wins": st.column_config.NumberColumn(format="%d"),
                "Losses": st.column_config.NumberColumn(format="%d"),
                "Total ROI": st.column_config.NumberColumn(format="$%.2f"),
                "Avg Return": st.column_config.NumberColumn(format="$%.2f")
            }
        )
        
        # Show individual member stats in expandable sections
        st.markdown("---")
        st.subheader("📊 Member Details")
        
        users = get_all_users()
        for user in users:
            with st.expander(f"{user['name']}"):
                stats = get_user_stats(user['id'])
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Picks", stats['total_picks'] or 0)
                with col2:
                    st.metric("Wins", stats['wins'] or 0)
                with col3:
                    st.metric("Losses", stats['losses'] or 0)
                with col4:
                    st.metric("ROI", f"${stats['total_return'] or 0:.2f}")
                
                # Win percentage
                total = (stats['wins'] or 0) + (stats['losses'] or 0)
                if total > 0:
                    win_pct = (stats['wins'] / total) * 100
                    st.metric("Win %", f"{win_pct:.1f}%")
    else:
        st.info("No picks yet. Start in the Admin Interface!")


def show_week_picks_tab(season: int) -> None:
    """Display picks for a selected week."""
    st.header("📝 Weekly Picks & Results")
    
    # Get available weeks
    weeks = get_all_weeks(season)
    
    if not weeks:
        st.info("No weeks recorded yet.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_week_record = st.selectbox(
            "Select Week",
            options=weeks,
            format_func=lambda x: f"Week {x['week']}",
            key="public_week_select"
        )
    
    with col2:
        users = get_all_users()
        selected_user = st.selectbox(
            "Select Member (optional)",
            options=[None] + users,
            format_func=lambda x: "All Members" if x is None else x['name'],
            key="public_member_select"
        )
    
    if selected_week_record:
        week_id = selected_week_record['id']
        
        if selected_user:
            # Show picks for specific user
            picks = get_user_week_picks(selected_user['id'], week_id)
            
            if picks:
                st.subheader(f"{selected_user['name']}'s Picks - Week {selected_week_record['week']}")
                
                picks_data = []
                for pick in picks:
                    result = get_result_for_pick(pick['id'])
                    picks_data.append({
                        'Team': pick['team'],
                        'Player': pick['player_name'],
                        'Result': '✅ Correct' if result and result['is_correct'] else ('❌ Incorrect' if result and result['is_correct'] is False else '⏳ Pending'),
                        'Return': f"${result['actual_return']:.2f}" if result else "-"
                    })
                
                picks_df = pd.DataFrame(picks_data)
                st.dataframe(picks_df, width='stretch', hide_index=True)
            else:
                st.info(f"No picks for {selected_user['name']} in Week {selected_week_record['week']}")
        else:
            # Show all picks for the week
            st.subheader(f"All Members' Picks - Week {selected_week_record['week']}")
            
            all_users = get_all_users()
            picks_by_user = {}
            
            for user in all_users:
                picks = get_user_week_picks(user['id'], week_id)
                if picks:
                    picks_by_user[user['name']] = picks
            
            if picks_by_user:
                for member_name in sorted(picks_by_user.keys()):
                    with st.expander(f"👤 {member_name}", expanded=True):
                        picks = picks_by_user[member_name]
                        picks_data = []
                        
                        for pick in picks:
                            result = get_result_for_pick(pick['id'])
                            picks_data.append({
                                'Team': pick['team'],
                                'Player': pick['player_name'],
                                'Result': '✅' if result and result['is_correct'] else ('❌' if result and result['is_correct'] is False else '⏳'),
                                'Return': f"${result['actual_return']:.2f}" if result and result['actual_return'] is not None else "-"
                            })
                        
                        picks_df = pd.DataFrame(picks_data)
                        st.dataframe(picks_df, width='stretch', hide_index=True)
            else:
                st.info(f"No picks recorded for Week {selected_week_record['week']}")

