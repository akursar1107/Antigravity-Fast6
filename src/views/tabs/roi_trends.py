"""
ROI & Profitability Trends Tab

Displays financial performance analytics including:
- Cumulative ROI trends over time
- Weekly profit/loss breakdowns
- Best/worst pick analysis
- ROI by position and odds range
- Pick difficulty analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from services.analytics import (
    get_user_roi_trend,
    get_weekly_roi_all_users,
    get_best_worst_picks,
    get_roi_by_position,
    get_roi_by_odds_range,
    get_pick_difficulty_analysis,
    get_profitability_summary,
    get_user_rank_by_roi
)
from src.database import get_all_users


def show_roi_trends_tab(season: int):
    """Display ROI and profitability trends analytics."""
    
    st.header("💰 ROI & Profitability Tracker")
    st.markdown("Track financial performance, identify winning strategies, and optimize your picks")
    
    # Get users list
    users = get_all_users()
    
    if not users:
        st.warning("No users found. Add users in the Admin Interface.")
        return
    
    # Tab navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 ROI Trends",
        "💵 Weekly Performance",
        "🎯 Best/Worst Picks",
        "📊 Strategy Analysis",
        "🏆 Leaderboard"
    ])
    
    # Tab 1: ROI Trends
    with tab1:
        st.subheader("Cumulative ROI Over Time")
        
        st.info("📊 **Note:** Charts only show weeks where users have graded picks. If a line starts late or has gaps, that user didn't make picks in those weeks.")
        
        # User selector
        user_names = [u['name'] for u in users]
        selected_users = st.multiselect(
            "Select Users to Compare",
            options=user_names,
            default=user_names[:3] if len(user_names) >= 3 else user_names
        )
        
        if selected_users:
            # Create line chart
            fig = go.Figure()
            
            for user_name in selected_users:
                user_data = next((u for u in users if u['name'] == user_name), None)
                if user_data:
                    trend_df = get_user_roi_trend(user_data['id'], season)
                    
                    if not trend_df.empty:
                        # Important: Don't connect to origin if user didn't start in week 1
                        # This prevents the flat line artifact
                        fig.add_trace(go.Scatter(
                            x=trend_df['week'],
                            y=trend_df['cumulative_roi'],
                            mode='lines+markers',
                            name=user_name,
                            connectgaps=False,  # Don't connect across missing data
                            hovertemplate='<b>%{fullData.name}</b><br>' +
                                        'Week %{x}<br>' +
                                        'ROI: %{y:.1f}%<br>' +
                                        '<extra></extra>'
                        ))
            
            fig.update_layout(
                title=f"Cumulative ROI Trend - {season} Season",
                xaxis_title="Week",
                yaxis_title="Cumulative ROI (%)",
                hovermode='x unified',
                height=500,
                showlegend=True
            )
            
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Profitability summary for each user
            st.markdown("---")
            st.subheader("Season Summary")
            
            for user_name in selected_users:
                user_data = next((u for u in users if u['name'] == user_name), None)
                if user_data:
                    summary = get_profitability_summary(user_data['id'], season)
                    
                    with st.expander(f"📊 {user_name}'s Performance"):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Total Profit/Loss", f"${summary['total_profit']:.2f}")
                            st.metric("Total Picks", summary['total_picks'])
                        
                        with col2:
                            st.metric("ROI", f"{summary['roi']:.1f}%")
                            st.metric("Win Rate", f"{summary['win_rate']:.1f}%")
                        
                        with col3:
                            st.metric("Best Return", f"${summary['best_return']:.2f}")
                            st.metric("Worst Return", f"${summary['worst_return']:.2f}")
                        
                        with col4:
                            st.metric("Avg Return", f"${summary['avg_return']:.2f}")
                            st.metric("Avg Odds", f"+{abs(summary['avg_odds']):.0f}")
        else:
            st.info("Select users above to view ROI trends")
    
    # Tab 2: Weekly Performance
    with tab2:
        st.subheader("Weekly Profit/Loss Breakdown")
        
        weekly_df = get_weekly_roi_all_users(season)
        
        if not weekly_df.empty:
            # Create bar chart for weekly performance
            fig = px.bar(
                weekly_df,
                x='week',
                y='week_profit',
                color='user_name',
                title=f"Weekly Profit/Loss by User - {season} Season",
                labels={'week': 'Week', 'week_profit': 'Profit/Loss ($)', 'user_name': 'User'},
                barmode='group',
                height=500
            )
            
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table
            st.markdown("---")
            st.subheader("Detailed Weekly Performance")
            
            # Pivot table for better readability
            pivot_df = weekly_df.pivot(
                index='week',
                columns='user_name',
                values='week_profit'
            ).fillna(0)
            
            # Format as currency
            styled_df = pivot_df.style.format("${:.2f}").background_gradient(
                cmap='RdYlGn', axis=None, vmin=-5, vmax=5
            )
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Weekly stats
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                best_week = weekly_df.loc[weekly_df['week_profit'].idxmax()]
                st.markdown(f"**Best Week:** {best_week['user_name']} (Week {best_week['week']}) - ${best_week['week_profit']:.2f}")
            
            with col2:
                worst_week = weekly_df.loc[weekly_df['week_profit'].idxmin()]
                st.markdown(f"**Worst Week:** {worst_week['user_name']} (Week {worst_week['week']}) - ${worst_week['week_profit']:.2f}")
            
            with col3:
                avg_profit = weekly_df['week_profit'].mean()
                st.markdown(f"**Avg Weekly Profit:** ${avg_profit:.2f}")
        else:
            st.info("No weekly data available yet")
    
    # Tab 3: Best/Worst Picks
    with tab3:
        st.subheader("Pick Analysis - Wins and Losses")
        
        # User selector
        user_name = st.selectbox(
            "Select User",
            options=[u['name'] for u in users]
        )
        
        if user_name:
            user_data = next((u for u in users if u['name'] == user_name), None)
            if user_data:
                picks = get_best_worst_picks(user_data['id'], season, limit=10)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🎉 Best Picks")
                    best_df = picks['best']
                    
                    if not best_df.empty:
                        display_best = best_df[['week', 'player_name', 'team', 'odds', 'actual_return']].copy()
                        display_best.columns = ['Week', 'Player', 'Team', 'Odds', 'Return']
                        display_best['Return'] = display_best['Return'].apply(lambda x: f"${x:.2f}")
                        
                        st.dataframe(display_best, use_container_width=True, hide_index=True)
                        
                        total_best = best_df['actual_return'].sum()
                        st.success(f"Total from best picks: ${total_best:.2f}")
                    else:
                        st.info("No data available")
                
                with col2:
                    st.markdown("#### 😞 Worst Picks")
                    worst_df = picks['worst']
                    
                    if not worst_df.empty:
                        display_worst = worst_df[['week', 'player_name', 'team', 'odds', 'actual_return']].copy()
                        display_worst.columns = ['Week', 'Player', 'Team', 'Odds', 'Return']
                        display_worst['Return'] = display_worst['Return'].apply(lambda x: f"${x:.2f}")
                        
                        st.dataframe(display_worst, use_container_width=True, hide_index=True)
                        
                        total_worst = worst_df['actual_return'].sum()
                        st.error(f"Total from worst picks: ${total_worst:.2f}")
                    else:
                        st.info("No data available")
    
    # Tab 4: Strategy Analysis
    with tab4:
        st.subheader("Strategic Performance Insights")
        
        # User selector
        user_name = st.selectbox(
            "Select User for Analysis",
            options=[u['name'] for u in users],
            key='strategy_user'
        )
        
        if user_name:
            user_data = next((u for u in users if u['name'] == user_name), None)
            if user_data:
                # ROI by Odds Range
                st.markdown("#### ROI by Odds Range")
                odds_df = get_roi_by_odds_range(user_data['id'], season)
                
                if not odds_df.empty:
                    fig = go.Figure(data=[
                        go.Bar(
                            x=odds_df['odds_category'],
                            y=odds_df['roi'],
                            marker_color=odds_df['roi'].apply(
                                lambda x: 'green' if x > 0 else 'red'
                            ),
                            text=odds_df['roi'].apply(lambda x: f"{x:.1f}%"),
                            textposition='outside'
                        )
                    ])
                    
                    fig.update_layout(
                        title="ROI by Odds Category",
                        xaxis_title="Odds Range",
                        yaxis_title="ROI (%)",
                        height=400
                    )
                    
                    fig.add_hline(y=0, line_dash="dash", line_color="gray")
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Data table
                    display_odds = odds_df[['odds_category', 'picks_count', 'wins', 'win_rate', 'roi']].copy()
                    display_odds.columns = ['Odds Range', 'Picks', 'Wins', 'Win Rate (%)', 'ROI (%)']
                    st.dataframe(display_odds, use_container_width=True, hide_index=True)
                else:
                    st.info("No odds data available")
                
                # Pick Difficulty Analysis
                st.markdown("---")
                st.markdown("#### Pick Difficulty Assessment")
                
                difficulty = get_pick_difficulty_analysis(user_data['id'], season)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Favorites ROI", f"{difficulty['favorite_roi']:.1f}%")
                    st.metric("Favorites Count", difficulty['favorite_count'])
                
                with col2:
                    st.metric("Longshots ROI", f"{difficulty['longshot_roi']:.1f}%")
                    st.metric("Longshots Count", difficulty['longshot_count'])
                
                # Strategy recommendation
                st.info(f"**Strategy Assessment:** {difficulty['strategy_assessment']}")
                
                # ROI by Position
                st.markdown("---")
                st.markdown("#### ROI by Position")
                
                pos_df = get_roi_by_position(user_data['id'], season)
                
                if not pos_df.empty and 'position' in pos_df.columns:
                    # Filter out None positions
                    pos_df = pos_df[pos_df['position'].notna()]
                    
                    if not pos_df.empty:
                        fig = px.bar(
                            pos_df,
                            x='position',
                            y='roi',
                            title="ROI by Player Position",
                            labels={'position': 'Position', 'roi': 'ROI (%)'},
                            color='roi',
                            color_continuous_scale='RdYlGn',
                            height=400
                        )
                        
                        fig.add_hline(y=0, line_dash="dash", line_color="gray")
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Position data table
                        display_pos = pos_df[['position', 'picks_count', 'wins', 'win_rate', 'roi']].copy()
                        display_pos.columns = ['Position', 'Picks', 'Wins', 'Win Rate (%)', 'ROI (%)']
                        st.dataframe(display_pos, use_container_width=True, hide_index=True)
                    else:
                        st.info("No position data available (positions may not be tracked for all players)")
                else:
                    st.info("No position data available")
    
    # Tab 5: Leaderboard
    with tab5:
        st.subheader("Profitability Rankings")
        
        rankings_df = get_user_rank_by_roi(season)
        
        if not rankings_df.empty:
            # Add rank emoji
            def get_rank_emoji(rank):
                if rank == 1:
                    return "🥇"
                elif rank == 2:
                    return "🥈"
                elif rank == 3:
                    return "🥉"
                else:
                    return f"{rank}."
            
            rankings_df['Rank'] = rankings_df['rank'].apply(get_rank_emoji)
            
            # Reorder columns for display
            display_cols = ['Rank', 'user_name', 'total_profit', 'total_picks', 'wins', 'win_rate', 'roi']
            display_df = rankings_df[display_cols].copy()
            display_df.columns = ['Rank', 'User', 'Total Profit', 'Picks', 'Wins', 'Win Rate (%)', 'ROI (%)']
            
            # Format numbers
            display_df['Total Profit'] = display_df['Total Profit'].apply(lambda x: f"${x:.2f}")
            display_df['Win Rate (%)'] = display_df['Win Rate (%)'].apply(lambda x: f"{x:.1f}%")
            display_df['ROI (%)'] = display_df['ROI (%)'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Leaderboard stats
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                top_profit = rankings_df.iloc[0]
                st.markdown(f"**Most Profitable:** {top_profit['user_name']}")
                st.markdown(f"${top_profit['total_profit']:.2f}")
            
            with col2:
                best_roi = rankings_df.loc[rankings_df['roi'].idxmax()]
                st.markdown(f"**Best ROI:** {best_roi['user_name']}")
                st.markdown(f"{best_roi['roi']:.1f}%")
            
            with col3:
                best_wr = rankings_df.loc[rankings_df['win_rate'].idxmax()]
                st.markdown(f"**Best Win Rate:** {best_wr['user_name']}")
                st.markdown(f"{best_wr['win_rate']:.1f}%")
            
            with col4:
                total_picks = rankings_df['total_picks'].sum()
                total_profit = rankings_df['total_profit'].sum()
                st.markdown(f"**Group Total:**")
                st.markdown(f"${total_profit:.2f} ({total_picks} picks)")
        else:
            st.info("No ranking data available yet")
    
    # Footer with tips
    st.markdown("---")
    with st.expander("💡 How to Use This Data"):
        st.markdown("""
        **Understanding Your Performance:**
        
        1. **ROI Trends**: Watch your cumulative ROI over time. A rising line means profitable picks!
        2. **Weekly Performance**: Identify which weeks were best/worst and learn from them.
        3. **Best/Worst Picks**: Review your wins and losses to refine your strategy.
        4. **Strategy Analysis**: Discover which odds ranges and positions work best for you.
        5. **Leaderboard**: Compare your profitability against the group.
        
        **Tips for Improvement:**
        - If longshots aren't paying off, consider more conservative picks
        - Track which positions give you the best ROI
        - Avoid chasing losses with increasingly risky picks
        - Consistency often beats occasional big wins
        """)
