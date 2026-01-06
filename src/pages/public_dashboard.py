"""
Public Dashboard - Read-only views for all users.
Displays first TD analysis, all touchdowns, and weekly schedule.
"""

import streamlit as st
import pandas as pd
from data_processor import (
    load_data, get_touchdowns, get_first_tds, get_game_schedule,
    get_team_first_td_counts, get_player_first_td_counts, get_position_first_td_counts,
    load_rosters
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
    tab1, tab2, tab3, tab5 = st.tabs([
        "🚀 First TD of the Game", 
        "📋 All Touchdowns", 
        "📅 Weekly Schedule", 
        "📊 Analysis"
    ])

    with tab1:
        show_first_td_tab(first_tds)

    with tab2:
        show_all_touchdowns_tab(all_tds)
            
    with tab3:
        show_schedule_tab(schedule)

    with tab5:
        show_analysis_tab(df, season)
