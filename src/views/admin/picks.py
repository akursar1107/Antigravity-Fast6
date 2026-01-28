"""
Admin Picks Tab - Input and manage user picks for the week.
"""

import streamlit as st
import pandas as pd
from utils.nfl_data import load_rosters
from utils.odds_utils import (
    american_to_probability,
    calculate_expected_value,
    is_positive_ev,
    kelly_criterion,
)
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
        home_abbr = game['home_team']
        away_abbr = game['away_team']
        
        with st.expander(f"🏈 {away_abbr} @ {home_abbr}", expanded=False):
            col_team, col_player, col_odds = st.columns([1, 1.5, 1])
            
            with col_team:
                pick_team = st.radio(
                    "Team", 
                    options=[away_abbr, home_abbr], 
                    key=f"team_{away_abbr}_{home_abbr}",
                    horizontal=True
                )
            
            # Get team-specific players
            off_positions = ['QB', 'RB', 'WR', 'TE', 'FB', 'K', 'D/ST']
            team_players = roster_df[
                (roster_df['team'] == pick_team) & 
                (roster_df['position'].isin(off_positions))
            ].sort_values('full_name')
            
            player_options = ["-- Select Player --"] + team_players['display_name'].tolist()
            
            with col_player:
                selected_player = st.selectbox(
                    "First TD Scorer",
                    options=player_options,
                    key=f"player_{away_abbr}_{home_abbr}",
                    help=f"Select first TD scorer for {pick_team}"
                )
            
            with col_odds:
                odds = st.number_input(
                    "Odds",
                    value=250,
                    step=25,
                    key=f"odds_{away_abbr}_{home_abbr}"
                )
            
            if selected_player != "-- Select Player --":
                # Extract clean name (remove position)
                clean_name = selected_player.split(" (")[0]
                picks_to_add.append({
                    'team': pick_team,
                    'player_name': clean_name,
                    'odds': float(odds),
                    'game': f"{away_abbr} @ {home_abbr}"
                })
    
    # Save picks button
    if picks_to_add:
        st.markdown("---")
        if st.button("💾 Save All Picks", key="save_picks_btn", type="primary"):
            success_count = 0
            for pick in picks_to_add:
                try:
                    # Calculate theoretical return if needed
                    theo_return = (pick['odds'] / 100.0) if pick['odds'] > 0 else (100.0 / abs(pick['odds']))
                    
                    add_pick(
                        user_id=selected_user['id'],
                        week_id=week_id,
                        team=pick['team'],
                        player_name=pick['player_name'],
                        odds=pick['odds'],
                        theoretical_return=theo_return
                    )
                    success_count += 1
                except Exception as e:
                    st.error(f"❌ Error saving {pick['player_name']}: {str(e)}")
            
            if success_count > 0:
                st.toast(f"✅ Successfully saved {success_count} picks for {selected_user['name']}!", icon="🏈")
                st.rerun()
