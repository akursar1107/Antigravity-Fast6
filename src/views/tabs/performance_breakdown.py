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
    
    # ===== TAB 1: WIN RATE LEADERBOARD =====
    with tab1:
        st.subheader("Win Rate Leaderboard")
        
        sorted_by_wr = user_df.sort_values('win_rate', ascending=False)
        
        # Ranking visualization
        fig = px.bar(
            sorted_by_wr,
            x='name',
            y='win_rate',
            color='win_rate',
            color_continuous_scale=['red', 'yellow', 'green'],
            title="Win Rate by User",
            labels={'name': 'User', 'win_rate': 'Win Rate (%)'},
        )
        fig.update_layout(height=400, yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed rankings
        st.write("**Rankings:**")
        ranking_df = sorted_by_wr[['name', 'wins', 'losses', 'total_picks', 'win_rate']].reset_index(drop=True)
        ranking_df.index = ranking_df.index + 1
        ranking_df.index.name = 'Rank'
        
        st.dataframe(ranking_df, use_container_width=True)
    
    # ===== TAB 2: BRIER SCORE RANKINGS =====
    with tab2:
        st.subheader("Calibration Rankings (Brier Score)")
        
        st.info("🎯 **Lower Brier Score = Better Calibration.** Measures how well confidence matches actual results.")
        
        sorted_by_bs = user_df.sort_values('brier_score', ascending=True)
        
        # Lower is better, so reverse color scale
        fig = px.bar(
            sorted_by_bs,
            x='name',
            y='brier_score',
            color='brier_score',
            color_continuous_scale=['green', 'yellow', 'red'],  # Reversed
            title="Brier Score by User (Lower = Better)",
            labels={'name': 'User', 'brier_score': 'Brier Score'},
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed rankings
        st.write("**Rankings:**")
        ranking_df = sorted_by_bs[['name', 'brier_score', 'total_picks', 'win_rate']].reset_index(drop=True)
        ranking_df.index = ranking_df.index + 1
        ranking_df.index.name = 'Rank'
        
        st.dataframe(ranking_df, use_container_width=True)
    
    # ===== TAB 3: PICK VOLUME =====
    with tab3:
        st.subheader("Pick Volume & Experience")
        
        sorted_by_pv = user_df.sort_values('total_picks', ascending=False)
        
        fig = px.scatter(
            sorted_by_pv,
            x='total_picks',
            y='win_rate',
            size='total_picks',
            hover_name='name',
            color='win_rate',
            color_continuous_scale=['red', 'yellow', 'green'],
            title="Pick Volume vs Win Rate",
            labels={'total_picks': 'Total Picks', 'win_rate': 'Win Rate (%)'},
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.write("**Volume Leaders:**")
        vol_df = sorted_by_pv[['name', 'total_picks', 'wins', 'win_rate']].head(10)
        st.dataframe(vol_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Overall comparison table
    st.subheader("Overall Performance Summary")
    
    summary_table = user_df.sort_values('win_rate', ascending=False)[
        ['name', 'total_picks', 'wins', 'losses', 'win_rate', 'brier_score']
    ]
    
    st.dataframe(
        summary_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            'win_rate': st.column_config.NumberColumn(format="%.2f %%"),
            'brier_score': st.column_config.NumberColumn(format="%.3f")
        }
    )
    
    st.markdown("---")
    st.caption(f"Data from {season} season.")
