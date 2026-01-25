"""
Performance Breakdown Tab - Simple user comparison view.
"""

import streamlit as st
import pandas as pd
from services.performance_service import PickerPerformanceService
from utils import get_all_users


def show_performance_breakdown_tab(season: int) -> None:
    """Display multi-dimensional performance comparison across all users."""
    
    st.header("📊 Performance Breakdown & Comparison")
    
    # Get all users
    users = get_all_users()
    if not users:
        st.warning("⚠️ No users found.")
        return
    
    st.markdown("---")
    
    service = PickerPerformanceService()
    
    # Collect metrics for all users
    user_summaries = []
    for user in users:
        try:
            summary = service.get_user_performance_summary(user['id'], season)
            if summary['total_picks'] > 0:
                user_summaries.append({
                    'name': user['name'],
                    'total_picks': summary['total_picks'],
                    'wins': summary['wins'],
                    'win_rate': summary['win_rate'],
                    'brier_score': summary['brier_score'],
                })
        except Exception as e:
            st.warning(f"⚠️ Error loading {user['name']}: {str(e)}")
    
    if not user_summaries:
        st.info("No performance data available for any users yet.")
        return
    
    user_df = pd.DataFrame(user_summaries)
    
    st.write("### User Performance Summary")
    st.dataframe(user_df.sort_values('win_rate', ascending=False), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.success("✅ All user data loaded successfully!")
