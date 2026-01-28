"""
Team Analysis Tab
Displays team-specific touchdown analysis with logo, total touchdowns, and position distribution.
"""
import streamlit as st
import pandas as pd
from utils.nfl_data import get_touchdowns, load_rosters


def get_team_logo_url(team_abbr: str) -> str:
    """
    Get ESPN logo URL for a team abbreviation.
    Reuses the same logic as the Schedule tab.
    """
    # Handle common abbreviation differences
    logo_map = {
        'WAS': 'WSH',
        'LAR': 'LA',  # Rams
        'LAC': 'LAC',  # Chargers
    }
    abbr = logo_map.get(team_abbr, team_abbr)
    return f"https://a.espncdn.com/i/teamlogos/nfl/500/{abbr.lower()}.png"

def show_team_analysis_tab(df: pd.DataFrame, season: int) -> None:
    # Header and team selector side by side
    header_col, select_col = st.columns([2, 3])
    with header_col:
        st.header("🧩 Team Analysis")
        st.caption("Select a team to view touchdown stats and position breakdown.")
    with select_col:
        st.markdown("")  # Spacer for alignment
        teams = sorted(df['posteam'].dropna().unique())
        team = st.selectbox("Select Team", options=teams, key="team_analysis_select", index=0 if teams else None)

    if not team:
        st.info("Please select a team.")
        return

    # Show team logo and basic info
    col_logo, col_info = st.columns([1, 4])
    with col_logo:
        logo_url = get_team_logo_url(team)
        st.image(logo_url, width=120)
    
    with col_info:
        st.markdown(f"## {team}")
        # Try to get ELO rating if available
        try:
            from services.elo_rating_service import get_current_ratings
            from config import CURRENT_SEASON
            ratings = get_current_ratings(season)
            if not ratings.empty and team in ratings['team'].values:
                team_rating = ratings[ratings['team'] == team].iloc[0]
                elo = team_rating['current_rating']
                st.metric("ELO Rating", f"{elo:.0f}")
        except Exception:
            pass  # ELO not available, skip it

    # Touchdown type selector
    td_type = st.radio(
        "Touchdown Type",
        options=["All Touchdowns", "First TD of Game"],
        horizontal=True,
        key="team_analysis_td_type"
    )

    if td_type == "All Touchdowns":
        tds = get_touchdowns(df)
        team_tds = tds[tds['posteam'] == team]
        st.metric("Total Touchdowns", len(team_tds))
    else:
        from utils.nfl_data import get_first_tds
        tds = get_first_tds(df)
        team_tds = tds[tds['posteam'] == team]
        st.metric("First TDs of Game", len(team_tds))

    # Use the same roster-based position join logic as League Analysis
    from utils.analytics import get_position_first_td_counts
    roster = load_rosters(season)
    pos_counts_df = None
    if not roster.empty and not team_tds.empty:
        # Use the same function as league analysis, but for all TDs not just first TDs
        # We can reuse the function by passing team_tds and roster
        pos_counts_df = get_position_first_td_counts(team_tds, roster)
    # Show Position, Player, and Type tables side by side
    cols = st.columns(3)
    # Touchdowns by Position
    with cols[0]:
        if pos_counts_df is not None and not pos_counts_df.empty:
            st.markdown("**Touchdowns by Position**")
            st.dataframe(pos_counts_df, use_container_width=True, hide_index=True)
        else:
            st.info("Position data not available.")
    # Touchdowns by Player
    with cols[1]:
        if not team_tds.empty and 'td_player_name' in team_tds.columns:
            player_counts = team_tds['td_player_name'].fillna('Unknown').value_counts().reset_index()
            player_counts.columns = ['Player', 'Touchdowns']
            st.markdown("**Touchdowns by Player**")
            st.dataframe(player_counts, use_container_width=True, hide_index=True)
        else:
            st.info("Player touchdown data not available.")
    # Touchdowns by Type
    with cols[2]:
        if not team_tds.empty:
            def td_type_func(row):
                desc = str(row.get('desc', '')).lower()
                # Defensive TDs: interception, fumble return, pick-six, fumble recovery, etc.
                if any(x in desc for x in ['interception return', 'fumble return', 'pick six', 'pick-six', 'fumble recovery', 'defensive touchdown', 'interception touchdown', 'defense touchdown', 'def td']):
                    return 'Defensive'
                # Special Teams TDs: punt return, kick return, blocked punt, blocked fg, missed fg return, etc.
                if any(x in desc for x in ['punt return', 'kick return', 'kickoff return', 'blocked punt', 'blocked field goal', 'missed field goal return', 'special teams touchdown', 'special teams td', 'kickoff td', 'punt td', 'kickoff recovered', 'onside kick return']):
                    return 'Special Teams'
                # Passing TD
                if pd.notna(row.get('receiver_player_name')) and str(row.get('receiver_player_name')).strip() != '':
                    return 'Passing'
                # Rushing TD
                if pd.notna(row.get('rusher_player_name')) and str(row.get('rusher_player_name')).strip() != '':
                    return 'Rushing'
                return 'Other'
            td_types = team_tds.apply(td_type_func, axis=1).value_counts().reset_index()
            td_types.columns = ['Type', 'Touchdowns']
            st.markdown("**Touchdowns by Type**")
            st.dataframe(td_types, use_container_width=True, hide_index=True)
        else:
            st.info("Touchdown type data not available.")

    # Red Zone Efficiency (move below the tables)
    def is_red_zone(row):
        if 'yardline_100' in row and not pd.isna(row['yardline_100']):
            return row['yardline_100'] <= 20
        return False
    if 'yardline_100' in team_tds.columns:
        rz = team_tds.apply(is_red_zone, axis=1)
        rz_counts = rz.value_counts().rename({True: 'Red Zone', False: 'Outside Red Zone'})
        st.markdown("**Red Zone Efficiency**")
        st.bar_chart(rz_counts)
