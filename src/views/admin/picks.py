"""
Admin Picks Tab - Input and manage user picks for the week.
"""

import streamlit as st
import pandas as pd
from utils.nfl_data import load_rosters
from utils import (
    add_week, get_week_by_season_week, get_all_users, get_user_week_picks,
    add_pick
)


def show_picks_tab(season: int, schedule: pd.DataFrame) -> None:
    """Display the picks input interface."""
    st.header("📝 Input Weekly Picks")
    
    users = get_all_users()
    if not users:
        st.warning("⚠️ No members added yet. Go to User Management tab first.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_user = st.selectbox(
            "Select Member",
            options=users,
            format_func=lambda x: x['name'],
            key="pick_user_select"
        )
    
    with col2:
        st.write(f"**Season:** {season}")
    
    with col3:
        available_weeks = sorted(schedule['week'].unique()) if not schedule.empty else []
        selected_week = st.selectbox(
            "Select Week",
            options=available_weeks,
            format_func=lambda x: f"Week {x}",
            key="pick_week_select"
        )
    
    # Get or create week in database
    week_id = None
    if selected_week:
        week_record = get_week_by_season_week(season, selected_week)
        if not week_record:
            week_id = add_week(season, selected_week)
        else:
            week_id = week_record['id']
    
    # Get games for this week
    games_for_week = schedule[schedule['week'] == selected_week] if selected_week else pd.DataFrame()
    
    if games_for_week.empty:
        st.warning(f"No games found for Week {selected_week}")
        return
    
    # Load rosters
    with st.spinner("Loading rosters..."):
        roster_df = load_rosters(season)
    
    if roster_df.empty:
        st.error("Could not load rosters.")
        return
    
    roster_df['display_name'] = roster_df['full_name'] + " (" + roster_df['position'] + ")"
    
    # Get existing picks for this user/week
    existing_picks = get_user_week_picks(selected_user['id'], week_id) if week_id else []
    existing_picks_dict = {p['team']: p for p in existing_picks}
    
    st.subheader(f"Picks for {selected_user['name']} - Week {selected_week}")
    
    picks_to_add = []
    
    # Iterate through games
    for _, game in games_for_week.iterrows():
        home_team = game['home_team']
        away_team = game['away_team']
        
        with st.expander(f"{away_team} @ {home_team}", expanded=False):
            col_team, col_player = st.columns(2)
            
            # Get team-specific players
            off_positions = ['QB', 'RB', 'WR', 'TE', 'FB']
            team_players = roster_df[
                (roster_df['team'].isin([home_team, away_team])) & 
                (roster_df['position'].isin(off_positions))
            ].sort_values('full_name')
            
            options = ["-- Select Player --"] + team_players['display_name'].tolist()
            
            with col_team:
                st.write(f"**{away_team} @ {home_team}**")
            
            with col_player:
                selected_player = st.selectbox(
                    "First TD Scorer",
                    options=options,
                    key=f"pick_{home_team}_{away_team}",
                    index=0
                )
            
            if selected_player != "-- Select Player --":
                # Extract clean name (remove position)
                clean_name = selected_player.split(" (")[0]
                picks_to_add.append({
                    'game_key': f"{away_team}_{home_team}",
                    'team': away_team,
                    'player_name': clean_name,
                    'game': f"{away_team} @ {home_team}"
                })
    
    # Save picks button
    if picks_to_add:
        if st.button("💾 Save All Picks", key="save_picks_btn"):
            for pick in picks_to_add:
                try:
                    pick_id = add_pick(
                        user_id=selected_user['id'],
                        week_id=week_id,
                        team=pick['team'],
                        player_name=pick['player_name']
                    )
                    st.success(f"✅ Saved: {pick['player_name']} - {pick['game']}")
                except Exception as e:
                    st.error(f"❌ Error saving {pick['player_name']}: {str(e)}")
            st.rerun()
