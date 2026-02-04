"""
Player Performance Analytics Tab

Displays player statistics including:
- Hot/cold player indicators
- TD scoring rates and trends
- Position-based leaderboards
- Player comparison tools
"""

import streamlit as st
import pandas as pd
from services.analytics import (
    get_hot_players,
    get_position_leaders,
    get_team_top_scorers,
    get_player_comparison,
    get_form_badge_emoji,
    get_player_summary_text,
    update_player_stats
)
from src import config


def show_player_performance_tab(season: int):
    """Display player performance analytics."""
    
    st.header("🌟 Player Performance Tracker")
    
    # Refresh data button
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("Track player form, TD rates, and identify hot streaks")
    
    with col3:
        if st.button("🔄 Refresh Stats", help="Update player statistics from latest data"):
            with st.spinner("Updating player stats..."):
                result = update_player_stats(season)
                if result['errors'] == 0:
                    st.success(f"✅ Updated {result['players_updated']} players, added {result['new_players']} new")
                else:
                    st.error("Error updating player stats")
    
    # Tab navigation
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔥 Hot Players",
        "📊 Position Leaders",
        "🏈 Team Analysis",
        "⚖️ Player Comparison"
    ])
    
    # Tab 1: Hot Players
    with tab1:
        st.subheader("Hot Players - Strong Recent Performance")
        st.markdown("Players with 3+ TD-scoring weeks in their last 5 games")
        
        min_tds = st.slider("Minimum TDs", min_value=1, max_value=10, value=2)
        
        hot_df = get_hot_players(season, min_tds=min_tds)
        
        if not hot_df.empty:
            # Add form badge column
            hot_df['Form'] = hot_df['recent_form'].apply(get_form_badge_emoji)
            
            # Reorder columns for display
            display_cols = [
                'Form', 'player_name', 'team', 'position',
                'first_td_count', 'any_time_td_count', 
                'games_played', 'first_td_rate', 'any_td_rate'
            ]
            display_df = hot_df[display_cols].copy()
            display_df.columns = [
                '🔥', 'Player', 'Team', 'Pos',
                'First TDs', 'Any TDs',
                'Games', 'First TD Rate', 'Any TD Rate'
            ]
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Hot Players", len(hot_df))
            with col2:
                avg_rate = hot_df['first_td_rate'].mean()
                st.metric("Avg First TD Rate", f"{avg_rate:.3f}")
            with col3:
                total_tds = hot_df['any_time_td_count'].sum()
                st.metric("Total TDs", int(total_tds))
        else:
            st.info("No hot players found with current filters. Try lowering the minimum TDs.")
    
    # Tab 2: Position Leaders
    with tab2:
        st.subheader("Position-Based TD Leaders")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            position = st.selectbox(
                "Select Position",
                options=['QB', 'RB', 'WR', 'TE', 'FB'],
                index=2  # Default to WR
            )
            
            limit = st.number_input(
                "Top N Players",
                min_value=5,
                max_value=50,
                value=10
            )
        
        with col2:
            pos_df = get_position_leaders(season, position, limit=int(limit))
            
            if not pos_df.empty:
                # Add form badges
                pos_df['Form'] = pos_df['recent_form'].apply(get_form_badge_emoji)
                
                # Prepare display
                display_cols = [
                    'Form', 'player_name', 'team',
                    'first_td_count', 'any_time_td_count',
                    'games_played', 'first_td_rate'
                ]
                display_df = pos_df[display_cols].copy()
                display_df.columns = [
                    '🔥', 'Player', 'Team',
                    'First TDs', 'Any TDs',
                    'Games', 'First TD Rate'
                ]
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Position insights
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(f"{position}s Tracked", len(pos_df))
                with col2:
                    avg_first_td = pos_df['first_td_count'].mean()
                    st.metric("Avg First TDs", f"{avg_first_td:.1f}")
                with col3:
                    hot_count = (pos_df['recent_form'] == 'HOT').sum()
                    st.metric("Hot Players", hot_count)
                with col4:
                    top_rate = pos_df['first_td_rate'].max()
                    st.metric("Best Rate", f"{top_rate:.3f}")
            else:
                st.info(f"No data available for {position} position")
    
    # Tab 3: Team Analysis
    with tab3:
        st.subheader("Team Top Scorers")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Get list of teams from config
            teams = sorted(list(config.TEAM_MAP.keys()))
            team = st.selectbox("Select Team", options=teams)
            
            top_n = st.number_input(
                "Top N Players",
                min_value=3,
                max_value=15,
                value=5
            )
        
        with col2:
            team_df = get_team_top_scorers(season, team, limit=int(top_n))
            
            if not team_df.empty:
                # Add form badges
                team_df['Form'] = team_df['recent_form'].apply(get_form_badge_emoji)
                
                # Prepare display
                display_cols = [
                    'Form', 'player_name', 'position',
                    'first_td_count', 'any_time_td_count',
                    'games_played', 'last_td_week'
                ]
                display_df = team_df[display_cols].copy()
                display_df.columns = [
                    '🔥', 'Player', 'Pos',
                    'First TDs', 'Any TDs',
                    'Games', 'Last TD Week'
                ]
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Team summary
                st.markdown("---")
                st.markdown(f"**{config.TEAM_MAP.get(team, team)} TD Leaders**")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_first = team_df['first_td_count'].sum()
                    st.metric("Total First TDs", int(total_first))
                with col2:
                    total_any = team_df['any_time_td_count'].sum()
                    st.metric("Total TDs", int(total_any))
                with col3:
                    hot_players = (team_df['recent_form'] == 'HOT').sum()
                    st.metric("Hot Players", hot_players)
            else:
                st.info(f"No data available for {team}")
    
    # Tab 4: Player Comparison
    with tab4:
        st.subheader("Compare Multiple Players")
        
        st.markdown("Enter player names to compare their TD statistics side-by-side")
        
        # Multi-select for player names
        player_input = st.text_area(
            "Enter player names (one per line)",
            height=100,
            placeholder="Patrick Mahomes\nChristian McCaffrey\nCeeDee Lamb"
        )
        
        if player_input:
            player_names = [name.strip() for name in player_input.split('\n') if name.strip()]
            
            if player_names:
                comp_df = get_player_comparison(player_names, season)
                
                if not comp_df.empty:
                    # Add form badges
                    comp_df['Form'] = comp_df['recent_form'].apply(get_form_badge_emoji)
                    
                    # Prepare display
                    display_cols = [
                        'Form', 'player_name', 'team', 'position',
                        'first_td_count', 'any_time_td_count',
                        'games_played', 'first_td_rate', 'any_td_rate'
                    ]
                    display_df = comp_df[display_cols].copy()
                    display_df.columns = [
                        '🔥', 'Player', 'Team', 'Pos',
                        'First TDs', 'Any TDs',
                        'Games', 'First TD Rate', 'Any TD Rate'
                    ]
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Comparison insights
                    st.markdown("---")
                    st.markdown("**Comparison Insights**")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        best_first_td = comp_df.loc[comp_df['first_td_count'].idxmax()]
                        st.markdown(f"**Most First TDs:** {best_first_td['player_name']} ({int(best_first_td['first_td_count'])})")
                    
                    with col2:
                        best_rate = comp_df.loc[comp_df['first_td_rate'].idxmax()]
                        st.markdown(f"**Best First TD Rate:** {best_rate['player_name']} ({best_rate['first_td_rate']:.3f})")
                    
                    with col3:
                        hot_in_comp = (comp_df['recent_form'] == 'HOT').sum()
                        st.markdown(f"**Hot Players:** {hot_in_comp} of {len(comp_df)}")
                else:
                    st.warning("No data found for the entered players. Check spelling and try again.")
        else:
            st.info("👆 Enter player names above to compare their statistics")
    
    # Footer with legend
    st.markdown("---")
    with st.expander("ℹ️ Understanding Player Form"):
        st.markdown("""
        **Player Form Indicators:**
        - 🔥 **HOT**: Scored TD in 3+ of last 5 weeks - Strong recent performance
        - ✓ **AVERAGE**: Scored TD in 1-2 of last 5 weeks - Moderate activity
        - ❄️ **COLD**: No TDs in last 5 weeks - Consider alternatives
        
        **Metrics Explained:**
        - **First TDs**: Number of times player scored the first TD in a game
        - **Any TDs**: Total touchdowns scored (all types)
        - **First TD Rate**: First TDs per game played (higher is better)
        - **Games**: Games where player scored at least one TD
        
        **Tips for Picks:**
        - Target 🔥 hot players for safer picks
        - High First TD Rate indicates consistent early scoring
        - Consider team offensive strength and matchup
        """)
