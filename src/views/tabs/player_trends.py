"""
Player Trends Tab - Rolling first TD rates, recent performance, and home/away splits.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.analytics import (
    get_player_rolling_first_td_rate,
    get_player_recent_games,
    get_player_home_away_splits,
)
from utils.nfl_data import load_rosters


def show_player_trends_tab(pbp_df: pd.DataFrame, season: int, roster_df: pd.DataFrame = None) -> None:
    """Display player rolling stats, trends, and performance analysis."""
    
    st.header("📈 Player Trends & Performance")
    
    # Load rosters if not provided
    if roster_df is None:
        with st.spinner("Loading rosters..."):
            roster_df = load_rosters(season)
    
    if pbp_df.empty:
        st.warning("⚠️ No play-by-play data available for this season.")
        return
    
    # Player selector
    available_players = sorted(pbp_df['td_player_name'].dropna().unique().tolist())
    if not available_players:
        st.warning("⚠️ No touchdown scorers found in data.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        selected_player = st.selectbox(
            "Select Player",
            options=available_players,
            key="player_trends_select"
        )
    
    with col2:
        window_size = st.radio(
            "Rolling Window",
            options=[4, 8, 12],
            value=8,
            horizontal=True,
            help="Games to average over"
        )
    
    if not selected_player:
        st.info("Select a player to view trends.")
        return
    
    st.markdown("---")
    
    # Tab 1: Rolling Stats Chart
    with st.expander("📊 Rolling First TD Rate", expanded=True):
        try:
            rolling_df = get_player_rolling_first_td_rate(pbp_df, selected_player, roster_df, window=window_size)
            
            if rolling_df.empty:
                st.warning(f"No data found for {selected_player}.")
            else:
                # Chart
                fig = px.line(
                    rolling_df,
                    x='game_date',
                    y='rolling_first_td_rate',
                    markers=True,
                    title=f"{selected_player} - L{window_size} First TD Rate",
                    labels={'rolling_first_td_rate': 'First TD Rate', 'game_date': 'Date'},
                )
                fig.update_layout(
                    hovermode='x unified',
                    height=400,
                    yaxis=dict(tickformat='.0%'),
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Stats summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    current_rate = rolling_df['rolling_first_td_rate'].iloc[-1] if len(rolling_df) > 0 else 0
                    st.metric("Current L4 Rate", f"{current_rate:.1%}")
                
                with col2:
                    avg_rate = rolling_df['rolling_first_td_rate'].mean()
                    st.metric("Season Avg", f"{avg_rate:.1%}")
                
                with col3:
                    total_tds = rolling_df['scored_first_td'].sum()
                    st.metric("First TDs", int(total_tds))
        
        except Exception as e:
            st.error(f"Error loading rolling stats: {e}")
    
    # Tab 2: Recent Games
    with st.expander("📋 Recent Games (Last 10)", expanded=False):
        try:
            recent_df = get_player_recent_games(pbp_df, selected_player, last_n_games=10)
            
            if recent_df.empty:
                st.info(f"No recent game data for {selected_player}.")
            else:
                display_cols = ['game_date', 'week', 'opponent', 'scored_first_td']
                display_cols = [c for c in display_cols if c in recent_df.columns]
                
                st.dataframe(
                    recent_df[display_cols],
                    use_container_width=True,
                    hide_index=True
                )
        
        except Exception as e:
            st.error(f"Error loading recent games: {e}")
    
    # Tab 3: Home/Away Splits
    with st.expander("🏠 Home vs Away Performance", expanded=False):
        try:
            splits = get_player_home_away_splits(pbp_df, selected_player)
            
            if splits:
                col1, col2 = st.columns(2)
                
                with col1:
                    home = splits.get('home', {})
                    st.subheader("🏠 Home")
                    if home:
                        st.write(f"**Games:** {home.get('games', 0)}")
                        st.write(f"**First TDs:** {home.get('first_tds', 0)}")
                        st.write(f"**Rate:** {home.get('rate', 0):.1%}")
                    else:
                        st.write("No home game data.")
                
                with col2:
                    away = splits.get('away', {})
                    st.subheader("✈️ Away")
                    if away:
                        st.write(f"**Games:** {away.get('games', 0)}")
                        st.write(f"**First TDs:** {away.get('first_tds', 0)}")
                        st.write(f"**Rate:** {away.get('rate', 0):.1%}")
                    else:
                        st.write("No away game data.")
            else:
                st.info("Home/away data not available.")
        
        except Exception as e:
            st.error(f"Error loading home/away splits: {e}")
    
    st.markdown("---")
    st.caption(f"Data as of {season} season. Rolling stats require sufficient game sample.")
