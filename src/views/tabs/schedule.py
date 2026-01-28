"""
Schedule Tab - Display weekly schedule and results
"""

import streamlit as st
import pandas as pd


def get_logo_url(team_abbr: str) -> str:
    """Get ESPN logo URL for a team abbreviation."""
    # Handle common abbreviation differences if any
    # ESPN uses 'WSH' for Washington, 'LV' for Raiders, etc.
    logo_map = {
        'WAS': 'WSH',
        # Add others if needed
    }
    abbr = logo_map.get(team_abbr, team_abbr)
    return f"https://a.espncdn.com/i/teamlogos/nfl/500/{abbr.lower()}.png"

def show_schedule_tab(schedule: pd.DataFrame) -> None:
    """
    Display the NFL schedule tab with a visual card-style layout.
    """
    st.header("🏈 NFL Schedule & Results")
    
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
        st.session_state.schedule_selected_week = selected_schedule_week
        
        week_schedule = schedule[schedule['week'] == selected_schedule_week]
        
        if not week_schedule.empty:
            # Custom CSS for schedule cards
            st.markdown("""
                <style>
                .schedule-card {
                    background: rgba(45, 55, 72, 0.4);
                    border-radius: 12px;
                    padding: 15px;
                    margin-bottom: 15px;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
                    backdrop-filter: blur(8px);
                }
                .team-row {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin: 5px 0;
                }
                .team-info {
                    display: flex;
                    align-items: center;
                }
                .team-logo {
                    width: 30px;
                    height: 30px;
                    margin-right: 12px;
                    object-fit: contain;
                }
                .team-name {
                    font-weight: 600;
                    font-size: 1.1rem;
                    color: #F7FAFC;
                }
                .score {
                    font-weight: 800;
                    font-size: 1.25rem;
                    color: #F7FAFC;
                    font-family: 'Roboto Mono', monospace;
                }
                .game-meta {
                    font-size: 0.8rem;
                    color: #A0AEC0;
                    border-top: 1px solid rgba(255, 255, 255, 0.05);
                    margin-top: 10px;
                    padding-top: 8px;
                    display: flex;
                    justify-content: space-between;
                }
                .win-inc { color: #228B22; font-weight: 700; text-shadow: 0 0 10px rgba(34, 139, 34, 0.3); }
                </style>
            """, unsafe_allow_html=True)

            # Display games in a grid (2 per row on desktop)
            game_cols = st.columns(2)
            
            for i, (_, row) in enumerate(week_schedule.iterrows()):
                col_idx = i % 2
                with game_cols[col_idx]:
                    home_abbr = row.get('home_team', 'N/A')
                    away_abbr = row.get('away_team', 'N/A')
                    home_score = row.get('home_score', 0)
                    away_score = row.get('away_score', 0)
                    
                    # Highlight winner if game is done
                    home_win_class = "win-inc" if home_score > away_score else ""
                    away_win_class = "win-inc" if away_score > home_score else ""
                    
                    st.markdown(f"""
                        <div class="schedule-card">
                            <div class="team-row">
                                <div class="team-info">
                                    <img src="{get_logo_url(away_abbr)}" class="team-logo">
                                    <span class="team-name {away_win_class}">{away_abbr}</span>
                                </div>
                                <div class="score">{int(away_score) if not pd.isna(away_score) else 0}</div>
                            </div>
                            <div class="team-row">
                                <div class="team-info">
                                    <img src="{get_logo_url(home_abbr)}" class="team-logo">
                                    <span class="team-name {home_win_class}">{home_abbr}</span>
                                </div>
                                <div class="score">{int(home_score) if not pd.isna(home_score) else 0}</div>
                            </div>
                            <div class="game-meta">
                                <span>{row.get('game_date', '')}</span>
                                <span>{row.get('game_type', 'Regular')}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info(f"No games found for Week {selected_schedule_week}.")
    else:
        st.info("No schedule data available.")
