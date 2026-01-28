"""
Defensive Matchup Analysis Tab

Displays defensive vulnerability analysis including:
- Worst/best defenses against TDs
- Position-specific matchups
- Red zone defense efficiency
- Defensive trends
- Matchup recommendations
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from services.analytics import (
    get_worst_defenses,
    get_best_defenses,
    get_position_matchups,
    get_red_zone_defense,
    get_defensive_trends,
    get_matchup_recommendations,
    get_defense_vs_position_matrix,
    analyze_defensive_performance
)
import config


def show_defense_matchups_tab(season: int):
    """Display defensive matchup analysis."""
    
    st.header("🛡️ Defensive Matchup Analysis")
    st.markdown("Identify defensive weaknesses and find favorable matchups for your picks")
    
    # Tab navigation
    tab1, tab2, tab3, tab4 = st.tabs([
        "📉 Worst Defenses",
        "🎯 Position Matchups",
        "🔴 Red Zone Defense",
        "💡 Recommendations"
    ])
    
    # Tab 1: Worst Defenses
    with tab1:
        st.subheader("Weakest Defenses - Most TDs Allowed")
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            limit = st.slider("Top N Defenses", min_value=5, max_value=20, value=10)
        
        worst_df = get_worst_defenses(season, limit=limit)
        
        if not worst_df.empty:
            # Bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=worst_df['team'],
                    y=worst_df['tds_per_game'],
                    marker_color='indianred',
                    text=worst_df['tds_per_game'].apply(lambda x: f"{x:.2f}"),
                    textposition='outside'
                )
            ])
            
            fig.update_layout(
                title="TDs Allowed Per Game",
                xaxis_title="Defense",
                yaxis_title="TDs Per Game",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table
            st.markdown("---")
            st.subheader("Detailed Stats")
            
            display_cols = ['rank', 'team', 'games_played', 'tds_allowed', 'tds_per_game', 'first_tds_allowed', 'first_td_rate']
            display_df = worst_df[display_cols].copy()
            display_df.columns = ['Rank', 'Team', 'Games', 'Total TDs', 'TDs/Game', 'First TDs', 'First TD Rate']
            
            # Format numbers
            display_df['TDs/Game'] = display_df['TDs/Game'].apply(lambda x: f"{x:.2f}")
            display_df['First TD Rate'] = display_df['First TD Rate'].apply(lambda x: f"{x:.2f}")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Insights
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                worst_team = worst_df.iloc[0]
                st.metric(
                    "Worst Defense",
                    worst_team['team'],
                    f"{worst_team['tds_per_game']:.2f} TDs/game"
                )
            
            with col2:
                avg_tds = worst_df['tds_per_game'].mean()
                st.metric("Average (Top 10)", f"{avg_tds:.2f} TDs/game")
            
            with col3:
                total_tds = worst_df['tds_allowed'].sum()
                st.metric("Total TDs Allowed", int(total_tds))
            
            # Best defenses for comparison
            st.markdown("---")
            st.subheader("Best Defenses (For Comparison)")
            
            best_df = get_best_defenses(season, limit=5)
            
            if not best_df.empty:
                display_best = best_df[['rank', 'team', 'tds_per_game', 'first_td_rate']].copy()
                display_best.columns = ['Rank', 'Team', 'TDs/Game', 'First TD Rate']
                display_best['TDs/Game'] = display_best['TDs/Game'].apply(lambda x: f"{x:.2f}")
                display_best['First TD Rate'] = display_best['First TD Rate'].apply(lambda x: f"{x:.2f}")
                
                st.dataframe(display_best, use_container_width=True, hide_index=True)
        else:
            st.info("No defensive data available for this season")
    
    # Tab 2: Position Matchups
    with tab2:
        st.subheader("Position-Specific Defensive Matchups")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            position = st.selectbox(
                "Select Position",
                options=['QB', 'RB', 'WR', 'TE'],
                index=2  # Default to WR
            )
        
        with col2:
            pos_matchups = get_position_matchups(season, position)
            
            if not pos_matchups.empty:
                # Bar chart
                fig = px.bar(
                    pos_matchups.head(15),
                    x='team',
                    y=f'{position}_tds_per_game',
                    title=f"Worst Defenses vs {position}",
                    labels={'team': 'Defense', f'{position}_tds_per_game': f'{position} TDs Per Game'},
                    color=f'{position}_tds_per_game',
                    color_continuous_scale='Reds',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                st.markdown("---")
                display_cols = ['team', 'games_played', f'{position}_tds_allowed', f'{position}_tds_per_game', 'unique_scorers']
                display_df = pos_matchups[display_cols].copy()
                display_df.columns = ['Team', 'Games', f'{position} TDs', 'TDs/Game', 'Unique Scorers']
                display_df['TDs/Game'] = display_df['TDs/Game'].apply(lambda x: f"{x:.2f}")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Position insights
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    worst_vs_pos = pos_matchups.iloc[0]
                    st.metric(
                        f"Worst vs {position}",
                        worst_vs_pos['team'],
                        f"{worst_vs_pos[f'{position}_tds_per_game']:.2f} TDs/game"
                    )
                
                with col2:
                    avg_allowed = pos_matchups[f'{position}_tds_per_game'].mean()
                    st.metric(f"League Avg vs {position}", f"{avg_allowed:.2f} TDs/game")
                
                with col3:
                    total_scorers = pos_matchups['unique_scorers'].sum()
                    st.metric(f"Unique {position} Scorers", int(total_scorers))
            else:
                st.info(f"No position data available for {position}")
        
        # Position matrix heatmap
        st.markdown("---")
        st.subheader("Defense vs Position Matrix")
        
        matrix_df = get_defense_vs_position_matrix(season)
        
        if not matrix_df.empty:
            fig = px.imshow(
                matrix_df,
                labels=dict(x="Position", y="Defense", color="TDs/Game"),
                x=matrix_df.columns,
                y=matrix_df.index,
                color_continuous_scale='Reds',
                aspect="auto",
                height=600
            )
            
            fig.update_layout(
                title="Defensive Vulnerability Heatmap (Higher = More TDs Allowed)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("💡 **Tip:** Darker red areas indicate weaker matchups. Target these defenses with the corresponding position.")
        else:
            st.info("Position matrix data not available")
    
    # Tab 3: Red Zone Defense
    with tab3:
        st.subheader("Red Zone Defensive Efficiency")
        
        rz_df = get_red_zone_defense(season)
        
        if not rz_df.empty:
            # Sort by TD rate
            rz_df = rz_df.sort_values('rz_td_rate', ascending=False)
            
            # Bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=rz_df.head(15)['team'],
                    y=rz_df.head(15)['rz_td_rate'],
                    marker_color='coral',
                    text=rz_df.head(15)['rz_td_rate'].apply(lambda x: f"{x:.1f}%"),
                    textposition='outside'
                )
            ])
            
            fig.update_layout(
                title="Red Zone TD Rate Allowed (Worst 15)",
                xaxis_title="Defense",
                yaxis_title="TD Rate (%)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table
            st.markdown("---")
            display_cols = ['team', 'games_played', 'rz_tds_allowed', 'rz_tds_per_game', 'rz_plays', 'rz_td_rate']
            display_df = rz_df[display_cols].copy()
            display_df.columns = ['Team', 'Games', 'RZ TDs', 'RZ TDs/Game', 'RZ Plays', 'TD Rate (%)']
            
            # Format numbers
            display_df['RZ TDs/Game'] = display_df['RZ TDs/Game'].apply(lambda x: f"{x:.2f}")
            display_df['TD Rate (%)'] = display_df['TD Rate (%)'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Red zone insights
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                worst_rz = rz_df.iloc[0]
                st.metric(
                    "Worst RZ Defense",
                    worst_rz['team'],
                    f"{worst_rz['rz_td_rate']:.1f}% TD rate"
                )
            
            with col2:
                avg_rz_rate = rz_df['rz_td_rate'].mean()
                st.metric("League Avg RZ TD Rate", f"{avg_rz_rate:.1f}%")
            
            with col3:
                best_rz = rz_df.iloc[-1]
                st.metric(
                    "Best RZ Defense",
                    best_rz['team'],
                    f"{best_rz['rz_td_rate']:.1f}% TD rate"
                )
        else:
            st.info("No red zone data available")
    
    # Tab 4: Recommendations
    with tab4:
        st.subheader("Matchup Recommendations")
        st.markdown("AI-powered recommendations based on defensive weaknesses")
        
        week = st.number_input(
            "Week",
            min_value=1,
            max_value=22,
            value=1,
            help="Week to get recommendations for"
        )
        
        recommendations = get_matchup_recommendations(season, week, limit=10)
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                trend_emoji = {
                    'DECLINING': '📉',
                    'IMPROVING': '📈',
                    'STABLE': '→'
                }.get(rec['trend'], '→')
                
                with st.expander(f"{i}. {rec['defense']} {trend_emoji}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total TDs Allowed", rec['tds_allowed'])
                    
                    with col2:
                        st.metric("TDs Per Game", f"{rec['tds_per_game']:.2f}")
                    
                    with col3:
                        st.metric("First TD Rate", f"{rec['first_td_rate']:.2f}")
                    
                    st.markdown(f"**Recommendation:** {rec['recommendation']}")
                    
                    # Get detailed trends
                    trend_data = get_defensive_trends(season, rec['defense'], weeks=5)
                    
                    if 'error' not in trend_data:
                        st.markdown(f"**Recent Form:** {trend_data['trend']} - {trend_data['recent_tds_allowed']} TDs in last {trend_data['weeks_analyzed']} weeks")
            
            # Summary insights
            st.markdown("---")
            st.markdown("### 📊 Key Insights")
            
            declining_count = sum(1 for r in recommendations if r['trend'] == 'DECLINING')
            avg_tds = sum(r['tds_per_game'] for r in recommendations) / len(recommendations)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**{declining_count} defenses** are trending worse (allowing more TDs recently)")
            
            with col2:
                st.info(f"**Average {avg_tds:.2f} TDs/game** allowed by these weak defenses")
        else:
            st.info("No recommendations available. Ensure defensive data has been analyzed.")
    
    # Footer with tips
    st.markdown("---")
    with st.expander("💡 How to Use Defensive Analysis"):
        st.markdown("""
        **Making Better Picks with Defensive Data:**
        
        1. **Target Weak Defenses**: Pick offensive players facing defenses in the "Worst Defenses" list
        2. **Position Matchups**: If picking a WR, check which defenses are worst against WRs specifically
        3. **Red Zone Weakness**: High red zone TD rates indicate defenses that struggle near the goal line
        4. **Trending Data**: Defenses trending worse (📉) are getting weaker - exploit them!
        5. **Matchup Matrix**: Use the heatmap to find the perfect position-defense mismatch
        
        **Strategy Tips:**
        - Combine defensive weakness with player form (hot players vs weak defenses = 🔥)
        - Consider game script - teams likely to score a lot create more TD opportunities
        - Red zone efficiency matters more for first TD picks
        - Don't ignore good offenses against average defenses
        
        **Example Pick Strategy:**
        1. Find worst defense vs WR (e.g., Team X allows 2.5 WR TDs/game)
        2. Check which team plays Team X this week
        3. Identify hot WR on that team (from Player Performance tab)
        4. Make your pick with confidence!
        """)
