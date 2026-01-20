"""
Schedule Tab - Display weekly schedule and results
"""

import streamlit as st
import pandas as pd


def show_schedule_tab(schedule: pd.DataFrame) -> None:
    """
    Display the NFL schedule tab.
    
    Args:
        schedule: DataFrame with NFL schedule containing:
            - Week: Game week number
            - Date: Game date/time
            - Home: Home team name
            - Away: Away team name
            - Spread: Vegas spread (Home team perspective)
            - OU: Over/Under total points
    
    Shows upcoming games, historical games, and quick score updates.
    Uses Streamlit data editor for interactive schedule viewing.
    """
    st.header("Weekly Schedule & Results")
    
    if not schedule.empty:
        available_weeks = sorted(schedule['week'].unique())
        default_ix = len(available_weeks) - 1 if available_weeks else 0
        
        # Initialize session state for schedule week selection
        if 'schedule_selected_week' not in st.session_state:
            st.session_state.schedule_selected_week = available_weeks[default_ix] if available_weeks else None
        
        # Find index of currently selected week
        try:
            week_index = available_weeks.index(st.session_state.schedule_selected_week)
        except (ValueError, KeyError):
            week_index = default_ix
        
        selected_schedule_week = st.selectbox(
            "Select Week", 
            options=available_weeks, 
            index=week_index,
            format_func=lambda x: f"Week {x}",
            key="schedule_week_selector"
        )
        # Update session state
        st.session_state.schedule_selected_week = selected_schedule_week
        
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
