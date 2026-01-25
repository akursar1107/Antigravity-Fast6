"""
Team Trends Tab - First TD trends by team, position heatmaps, and hot positions.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.analytics import (
    get_team_first_td_trends,
    get_position_trending,
)
import config


def show_team_trends_tab(first_tds_df: pd.DataFrame, season: int) -> None:
    """Display team-level first TD trends and position analysis."""
    
    st.header("🏈 Team & Position Trends")
    
    if first_tds_df is None or first_tds_df.empty:
        st.warning("⚠️ No first TD data available.")
        return
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Team Trends", "Position Trending", "Weekly Breakdown"])
    
    # ===== TAB 1: TEAM TRENDS =====
    with tab1:
        st.subheader("Team First TD Scorers (Last 4 Weeks)")
        
        # Team selector
        teams = sorted(first_tds_df['posteam'].dropna().unique().tolist())
        if not teams:
            st.warning("No team data available.")
        else:
            selected_team = st.selectbox(
                "Select Team",
                options=teams,
                key="team_trends_select"
            )
            
            try:
                trends = get_team_first_td_trends(first_tds_df, selected_team, last_n_weeks=4)
                
                if trends:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("First TDs (L4W)", trends.get('total_first_tds', 0))
                    
                    with col2:
                        by_player = trends.get('by_player', {})
                        top_player = max(by_player, key=by_player.get) if by_player else 'N/A'
                        st.metric("Leading Scorer", top_player)
                    
                    with col3:
                        by_pos = trends.get('by_position', {})
                        top_pos = max(by_pos, key=by_pos.get) if by_pos else 'N/A'
                        st.metric("Hot Position", top_pos)
                    
                    st.markdown("---")
                    
                    # By Player Breakdown
                    if trends.get('by_player'):
                        st.write("**First TD Scorers (Last 4 Weeks):**")
                        player_data = pd.DataFrame(
                            list(trends['by_player'].items()),
                            columns=['Player', 'First TDs']
                        ).sort_values('First TDs', ascending=False)
                        
                        fig = px.bar(player_data, x='Player', y='First TDs', title=f"{selected_team} - First TD Scorers")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # By Position Breakdown
                    if trends.get('by_position'):
                        st.write("**By Position:**")
                        pos_data = pd.DataFrame(
                            list(trends['by_position'].items()),
                            columns=['Position', 'Count']
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            fig = px.pie(pos_data, names='Position', values='Count', title="Position Distribution")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            st.dataframe(pos_data.sort_values('Count', ascending=False), use_container_width=True, hide_index=True)
                else:
                    st.info(f"No first TD data for {selected_team} in the last 4 weeks.")
            
            except Exception as e:
                st.error(f"Error loading team trends: {e}")
    
    # ===== TAB 2: POSITION TRENDING =====
    with tab2:
        st.subheader("Position Analysis (Last 4 Weeks)")
        
        try:
            pos_df = get_position_trending(first_tds_df, last_n_weeks=4)
            
            if pos_df.empty:
                st.info("No position data available.")
            else:
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    top_pos = pos_df.iloc[0] if len(pos_df) > 0 else None
                    if top_pos is not None:
                        st.metric("Hottest Position", top_pos['position'], f"{top_pos['pct_of_total']:.1f}%")
                
                with col2:
                    total_tds = pos_df['first_tds_count'].sum()
                    st.metric("Total First TDs", int(total_tds))
                
                with col3:
                    st.metric("Positions Active", len(pos_df))
                
                st.markdown("---")
                
                # Visualization
                fig = px.bar(
                    pos_df,
                    x='position',
                    y='first_tds_count',
                    title="First TDs by Position (Last 4 Weeks)",
                    labels={'position': 'Position', 'first_tds_count': 'First TDs'},
                    text='pct_of_total',
                )
                fig.update_traces(texttemplate='%{text:.1f}%', textposition='auto')
                st.plotly_chart(fig, use_container_width=True)
                
                # Detailed table
                st.write("**Detailed Breakdown:**")
                st.dataframe(pos_df, use_container_width=True, hide_index=True)
        
        except Exception as e:
            st.error(f"Error loading position trends: {e}")
    
    # ===== TAB 3: WEEKLY BREAKDOWN =====
    with tab3:
        st.subheader("Weekly First TD Count")
        
        try:
            if 'week' in first_tds_df.columns:
                weekly_df = first_tds_df['week'].value_counts().sort_index().reset_index()
                weekly_df.columns = ['Week', 'First TDs']
                
                fig = px.line(
                    weekly_df,
                    x='Week',
                    y='First TDs',
                    markers=True,
                    title="First TDs per Week",
                    labels={'Week': 'Week', 'First TDs': 'Count'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(weekly_df, use_container_width=True, hide_index=True)
            else:
                st.info("Week data not available.")
        
        except Exception as e:
            st.error(f"Error loading weekly breakdown: {e}")
    
    st.markdown("---")
    st.caption(f"Data as of {season} season.")
