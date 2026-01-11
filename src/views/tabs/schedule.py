"""
Schedule Tab - Display weekly schedule and results
"""

import streamlit as st
import pandas as pd


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
