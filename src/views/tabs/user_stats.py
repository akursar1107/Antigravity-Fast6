"""
User Stats Tab - Simple performance breakdown per user.
"""

import streamlit as st
import pandas as pd
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
        st.success("✅ Performance data loaded successfully!")
        
    except Exception as e:
        st.error(f"Error loading user stats: {str(e)}")
