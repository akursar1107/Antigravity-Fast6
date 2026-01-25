"""
User Stats Tab - Comprehensive performance breakdown per user.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services.performance_service import PickerPerformanceService
from utils import get_all_users


def show_user_stats_tab(season: int) -> None:
    """Display detailed user performance analytics."""
    
    st.header("👤 User Performance Statistics")
    
    # Get all users
    users = get_all_users()
    if not users:
        st.warning("⚠️ No users found.")
        return
    
    user_names = [u['name'] for u in users]
    user_map = {u['name']: u['id'] for u in users}
    
    # User selector
    selected_user_name = st.selectbox(
        "Select User",
        options=user_names,
        key="user_stats_select"
    )
    
    if not selected_user_name:
        st.info("Select a user to view detailed stats.")
        return
    
    selected_user_id = user_map[selected_user_name]
    
    st.markdown("---")
    
    # Initialize service
    service = PickerPerformanceService()
    
    try:
        # Get comprehensive summary
        summary = service.get_user_performance_summary(selected_user_id, season)
        
        if summary['total_picks'] == 0:
            st.info(f"No picks found for {selected_user_name} in {season}.")
            return
        
        # Top-level metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Picks", summary['total_picks'])
        
        with col2:
            st.metric("Win Rate", f"{summary['win_rate']:.1f}%")
        
        with col3:
            st.metric("Wins", summary['wins'])
        
        with col4:
            st.metric("Brier Score", f"{summary['brier_score']:.3f}")
        
        st.markdown("---")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Streaks", "ROI by Odds", "By Position", "By Game Type"])
        
        # ===== TAB 1: STREAKS =====
        with tab1:
            st.subheader("Streak Analysis")
            
            streaks = summary['streaks']
            col1, col2, col3 = st.columns(3)
            
            with col1:
                current = streaks.get('current_streak', 0)
                if current > 0:
                    st.metric("🔥 Current Win Streak", current)
                elif current < 0:
                    st.metric("❄️ Current Loss Streak", abs(current))
                else:
                    st.metric("Current Streak", "None")
            
            with col2:
                st.metric("🏆 Longest Win", streaks.get('longest_win_streak', 0))
            
            with col3:
                st.metric("😰 Longest Loss", streaks.get('longest_loss_streak', 0))
            
            st.markdown("---")
            
            is_hot = streaks.get('is_hot', False)
            if is_hot:
                st.success("🔥 **User is HOT!** 3+ wins in last 5 picks.")
            else:
                st.info("Temperature: Regular. Keep grinding.")
        
        # ===== TAB 2: ROI BY ODDS =====
        with tab2:
            st.subheader("Return on Investment by Odds Range")
            
            roi_df = summary['roi_summary']
            
            if roi_df is not None and not roi_df.empty:
                # Bar chart
                fig = px.bar(
                    roi_df,
                    x='odds_range',
                    y='roi_percent',
                    color='roi_percent',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    title="ROI by Odds Range",
                    labels={'odds_range': 'Odds Range', 'roi_percent': 'ROI (%)'},
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Table
                st.write("**Detailed Breakdown:**")
                st.dataframe(
                    roi_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'roi_percent': st.column_config.NumberColumn(format="%.2f %%")
                    }
                )
                
                # Interpretation
                st.write("**Interpretation:**")
                best_range = roi_df.loc[roi_df['roi_percent'].idxmax()]
                st.write(f"✅ Best ROI: **{best_range['odds_range']}** at {best_range['roi_percent']:.2f}%")
                worst_range = roi_df.loc[roi_df['roi_percent'].idxmin()]
                st.write(f"❌ Worst ROI: **{worst_range['odds_range']}** at {worst_range['roi_percent']:.2f}%")
            else:
                st.info("No ROI data available.")
        
        # ===== TAB 3: BY POSITION =====
        with tab3:
            st.subheader("Accuracy by Position")
            
            pos_df = summary['accuracy_by_position']
            
            if pos_df is not None and not pos_df.empty:
                # Bar chart
                fig = px.bar(
                    pos_df,
                    x='position',
                    y='accuracy',
                    color='accuracy',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    title="Pick Accuracy by Position",
                    labels={'position': 'Position', 'accuracy': 'Accuracy (%)'},
                )
                fig.update_layout(height=400, yaxis=dict(range=[0, 100]))
                st.plotly_chart(fig, use_container_width=True)
                
                # Table
                st.write("**Detailed Stats:**")
                st.dataframe(
                    pos_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Interpretation
                st.write("**Strengths & Weaknesses:**")
                strongest = pos_df.loc[pos_df['accuracy'].idxmax()]
                st.write(f"✅ Strongest: **{strongest['position']}** at {strongest['accuracy']:.1f}%")
                weakest = pos_df.loc[pos_df['accuracy'].idxmin()]
                st.write(f"⚠️ Needs Work: **{weakest['position']}** at {weakest['accuracy']:.1f}%")
            else:
                st.info("No position data available.")
        
        # ===== TAB 4: BY GAME TYPE =====
        with tab4:
            st.subheader("Accuracy by Game Type")
            
            game_df = summary['accuracy_by_game_type']
            
            if game_df is not None and not game_df.empty:
                # Bar chart
                fig = px.bar(
                    game_df,
                    x='game_type',
                    y='accuracy',
                    color='accuracy',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    title="Pick Accuracy by Game Type",
                    labels={'game_type': 'Game Type', 'accuracy': 'Accuracy (%)'},
                )
                fig.update_layout(height=400, yaxis=dict(range=[0, 100]))
                st.plotly_chart(fig, use_container_width=True)
                
                # Table
                st.write("**Detailed Stats:**")
                st.dataframe(
                    game_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No game type data available.")
    
    except Exception as e:
        st.error(f"Error loading user stats: {e}")
        import traceback
        st.write(traceback.format_exc())
    
    st.markdown("---")
    st.caption(f"Stats for {season} season.")
