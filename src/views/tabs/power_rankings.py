"""
Power Rankings Tab

Displays ELO-based team strength rankings including:
- Current power rankings
- Rating trends over time
- Offensive/defensive ratings
- Matchup predictions
- Strongest/weakest teams
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from services.elo_rating_service import (
    get_power_rankings,
    get_team_rating_history,
    get_matchup_prediction,
    get_strongest_weakest_teams,
    get_rating_trend_emoji,
    update_team_ratings,
    initialize_team_ratings
)
import config


def show_power_rankings_tab(season: int):
    """Display team power rankings and ELO ratings."""
    
    st.header("⚡ NFL Power Rankings")
    st.markdown("ELO-based team strength ratings and matchup predictions")
    
    # Get current week
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        week = st.number_input(
            "Select Week",
            min_value=1,
            max_value=22,
            value=1,
            help="Week to display rankings for"
        )
    
    with col2:
        if st.button("🔄 Update Ratings", help="Recalculate ELO ratings for this week"):
            with st.spinner(f"Updating ratings for Week {week}..."):
                if week == 1:
                    initialize_team_ratings(season, week)
                    st.success("✅ Initialized ratings for season")
                else:
                    result = update_team_ratings(season, week)
                    if result['errors'] == 0:
                        st.success(f"✅ Processed {result['games_processed']} games, updated {result['ratings_updated']} teams")
                    else:
                        st.error("Error updating ratings")
    
    # Tab navigation
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏆 Power Rankings",
        "📈 Rating Trends",
        "⚔️ Matchup Predictor",
        "📊 Team Comparison"
    ])
    
    # Tab 1: Power Rankings
    with tab1:
        st.subheader(f"Power Rankings - Week {week}")
        
        rankings_df = get_power_rankings(season, week)
        
        if not rankings_df.empty:
            # Add trend emoji
            rankings_df['Trend'] = rankings_df['rating_trend'].apply(get_rating_trend_emoji)
            
            # Prepare display columns
            display_cols = [
                'power_rank', 'Trend', 'team', 'elo_rating',
                'wins', 'losses', 'win_pct',
                'ppg', 'papg'
            ]
            display_df = rankings_df[display_cols].copy()
            display_df.columns = [
                'Rank', '📊', 'Team', 'ELO Rating',
                'W', 'L', 'Win %',
                'PPG', 'PAPG'
            ]
            
            # Format numbers
            display_df['ELO Rating'] = display_df['ELO Rating'].apply(lambda x: f"{x:.0f}")
            display_df['Win %'] = display_df['Win %'].apply(lambda x: f"{x:.1%}")
            display_df['PPG'] = display_df['PPG'].apply(lambda x: f"{x:.1f}")
            display_df['PAPG'] = display_df['PAPG'].apply(lambda x: f"{x:.1f}")
            
            # Color code by rank
            def highlight_rank(row):
                if row['Rank'] <= 5:
                    return ['background-color: #d4edda'] * len(row)
                elif row['Rank'] >= 28:
                    return ['background-color: #f8d7da'] * len(row)
                else:
                    return [''] * len(row)
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Top/Bottom teams
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 💪 Top 5 Teams")
                top_5 = rankings_df.head(5)
                for _, team in top_5.iterrows():
                    trend = get_rating_trend_emoji(team['rating_trend'])
                    st.markdown(
                        f"**{int(team['power_rank'])}. {team['team']}** {trend} - "
                        f"ELO: {team['elo_rating']:.0f} ({team['wins']}-{team['losses']})"
                    )
            
            with col2:
                st.markdown("#### 📉 Bottom 5 Teams")
                bottom_5 = rankings_df.tail(5)
                for _, team in bottom_5.iterrows():
                    trend = get_rating_trend_emoji(team['rating_trend'])
                    st.markdown(
                        f"**{int(team['power_rank'])}. {team['team']}** {trend} - "
                        f"ELO: {team['elo_rating']:.0f} ({team['wins']}-{team['losses']})"
                    )
            
            # Summary stats
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                highest_elo = rankings_df.iloc[0]
                st.metric("Highest ELO", f"{highest_elo['team']}", f"{highest_elo['elo_rating']:.0f}")
            
            with col2:
                lowest_elo = rankings_df.iloc[-1]
                st.metric("Lowest ELO", f"{lowest_elo['team']}", f"{lowest_elo['elo_rating']:.0f}")
            
            with col3:
                rising_teams = (rankings_df['rating_trend'] == 'RISING').sum()
                st.metric("Rising Teams", rising_teams)
            
            with col4:
                falling_teams = (rankings_df['rating_trend'] == 'FALLING').sum()
                st.metric("Falling Teams", falling_teams)
        else:
            st.info(f"No ratings available for Week {week}. Click 'Update Ratings' to calculate.")
    
    # Tab 2: Rating Trends
    with tab2:
        st.subheader("Team Rating Evolution")
        
        # Team selector
        teams = sorted(list(config.TEAM_MAP.keys()))
        selected_teams = st.multiselect(
            "Select Teams to Compare",
            options=teams,
            default=teams[:3] if len(teams) >= 3 else teams
        )
        
        if selected_teams:
            # Create line chart
            fig = go.Figure()
            
            for team in selected_teams:
                history_df = get_team_rating_history(team, season)
                
                if not history_df.empty:
                    fig.add_trace(go.Scatter(
                        x=history_df['week'],
                        y=history_df['elo_rating'],
                        mode='lines+markers',
                        name=team,
                        hovertemplate='<b>%{fullData.name}</b><br>' +
                                    'Week %{x}<br>' +
                                    'ELO: %{y:.0f}<br>' +
                                    '<extra></extra>'
                    ))
            
            fig.update_layout(
                title=f"ELO Rating Trends - {season} Season",
                xaxis_title="Week",
                yaxis_title="ELO Rating",
                hovermode='x unified',
                height=500,
                showlegend=True
            )
            
            fig.add_hline(y=1500, line_dash="dash", line_color="gray", opacity=0.5, annotation_text="League Average")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Team details
            st.markdown("---")
            st.subheader("Team Details")
            
            for team in selected_teams:
                history_df = get_team_rating_history(team, season)
                
                if not history_df.empty:
                    latest = history_df.iloc[-1]
                    first = history_df.iloc[0]
                    change = latest['elo_rating'] - first['elo_rating']
                    
                    with st.expander(f"📊 {config.TEAM_MAP.get(team, team)}"):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Current ELO", f"{latest['elo_rating']:.0f}")
                        
                        with col2:
                            st.metric("Season Change", f"{change:+.0f}")
                        
                        with col3:
                            st.metric("Record", f"{latest['wins']}-{latest['losses']}")
                        
                        with col4:
                            trend = get_rating_trend_emoji(latest['rating_trend'])
                            st.metric("Trend", trend)
        else:
            st.info("Select teams above to view rating trends")
    
    # Tab 3: Matchup Predictor
    with tab3:
        st.subheader("Matchup Prediction Tool")
        st.markdown("Predict game outcomes based on current ELO ratings")
        
        col1, col2 = st.columns(2)
        
        teams = sorted(list(config.TEAM_MAP.keys()))
        
        with col1:
            home_team = st.selectbox("Home Team", options=teams, key='home_team')
        
        with col2:
            away_team = st.selectbox("Away Team", options=teams, key='away_team')
        
        if home_team and away_team and home_team != away_team:
            prediction = get_matchup_prediction(home_team, away_team, season, week)
            
            if 'error' not in prediction:
                st.markdown("---")
                st.markdown("### 🎯 Matchup Prediction")
                
                # Win probability visualization
                col1, col2, col3 = st.columns([2, 1, 2])
                
                with col1:
                    st.markdown(f"**{config.TEAM_MAP.get(home_team, home_team)}** (Home)")
                    st.progress(prediction['home_win_prob'] / 100)
                    st.markdown(f"**Win Probability:** {prediction['home_win_prob']:.1f}%")
                    st.markdown(f"**ELO Rating:** {prediction['home_rating']:.0f}")
                
                with col2:
                    st.markdown("### VS")
                
                with col3:
                    st.markdown(f"**{config.TEAM_MAP.get(away_team, away_team)}** (Away)")
                    st.progress(prediction['away_win_prob'] / 100)
                    st.markdown(f"**Win Probability:** {prediction['away_win_prob']:.1f}%")
                    st.markdown(f"**ELO Rating:** {prediction['away_rating']:.0f}")
                
                # Prediction details
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    fav_team = config.TEAM_MAP.get(prediction['favorite'], prediction['favorite'])
                    st.metric("Favorite", fav_team)
                
                with col2:
                    spread = prediction['estimated_spread']
                    st.metric("Estimated Spread", f"{abs(spread):.1f}")
                
                with col3:
                    quality = prediction['matchup_quality']
                    if quality < 50:
                        quality_text = "Very Competitive"
                    elif quality < 100:
                        quality_text = "Competitive"
                    elif quality < 150:
                        quality_text = "Moderate Mismatch"
                    else:
                        quality_text = "Significant Mismatch"
                    st.metric("Matchup Quality", quality_text)
                
                # Interpretation
                st.info(
                    f"**Interpretation:** Based on ELO ratings, {fav_team} is favored by approximately "
                    f"{abs(spread):.1f} points. The matchup is considered {quality_text.lower()}."
                )
            else:
                st.warning(prediction['error'])
        elif home_team == away_team:
            st.warning("Please select different teams")
    
    # Tab 4: Team Comparison
    with tab4:
        st.subheader("Detailed Team Comparison")
        
        rankings_df = get_power_rankings(season, week)
        
        if not rankings_df.empty:
            # Team selector
            teams_to_compare = st.multiselect(
                "Select Teams to Compare (2-5 teams)",
                options=rankings_df['team'].tolist(),
                default=rankings_df['team'].head(3).tolist()
            )
            
            if len(teams_to_compare) >= 2:
                comp_df = rankings_df[rankings_df['team'].isin(teams_to_compare)].copy()
                
                # Radar chart for comparison
                categories = ['ELO Rating', 'Offensive Rating', 'Defensive Rating', 'Win %']
                
                fig = go.Figure()
                
                for _, team_data in comp_df.iterrows():
                    # Normalize values for radar chart
                    values = [
                        team_data['elo_rating'] / 2000 * 100,  # Normalize to 0-100
                        team_data['offensive_rating'] / 2000 * 100,
                        team_data['defensive_rating'] / 2000 * 100,
                        team_data['win_pct'] * 100
                    ]
                    
                    fig.add_trace(go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill='toself',
                        name=team_data['team']
                    ))
                
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=True,
                    title="Team Comparison Radar Chart",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Comparison table
                st.markdown("---")
                st.markdown("#### Detailed Stats")
                
                display_cols = [
                    'team', 'power_rank', 'elo_rating', 'offensive_rating', 'defensive_rating',
                    'wins', 'losses', 'win_pct', 'ppg', 'papg'
                ]
                display_df = comp_df[display_cols].copy()
                display_df.columns = [
                    'Team', 'Rank', 'ELO', 'Off Rating', 'Def Rating',
                    'W', 'L', 'Win %', 'PPG', 'PAPG'
                ]
                
                # Format numbers
                display_df['ELO'] = display_df['ELO'].apply(lambda x: f"{x:.0f}")
                display_df['Off Rating'] = display_df['Off Rating'].apply(lambda x: f"{x:.0f}")
                display_df['Def Rating'] = display_df['Def Rating'].apply(lambda x: f"{x:.0f}")
                display_df['Win %'] = display_df['Win %'].apply(lambda x: f"{x:.1%}")
                display_df['PPG'] = display_df['PPG'].apply(lambda x: f"{x:.1f}")
                display_df['PAPG'] = display_df['PAPG'].apply(lambda x: f"{x:.1f}")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("Select at least 2 teams to compare")
        else:
            st.info("No rankings data available")
    
    # Footer with ELO explanation
    st.markdown("---")
    with st.expander("ℹ️ Understanding ELO Ratings"):
        st.markdown("""
        **What is ELO?**
        
        ELO is a rating system that calculates the relative skill levels of teams. Originally developed for chess,
        it's widely used in sports analytics.
        
        **How it Works:**
        - Teams start at 1500 (league average)
        - Ratings increase with wins, decrease with losses
        - Beating a stronger team gives more points than beating a weaker team
        - Home teams get a 50-point advantage
        - Ratings regress toward the mean between seasons
        
        **Rating Ranges:**
        - **1700+**: Elite teams (Super Bowl contenders)
        - **1600-1700**: Strong playoff teams
        - **1500-1600**: Average to above-average teams
        - **1400-1500**: Below average teams
        - **<1400**: Struggling teams
        
        **Rating Trends:**
        - 📈 **RISING**: Rating increased by 10+ points from last week
        - 📉 **FALLING**: Rating decreased by 10+ points from last week
        - → **STABLE**: Rating changed by less than 10 points
        
        **Using ELO for Picks:**
        - Higher-rated teams are more likely to score first
        - Large rating gaps indicate mismatches
        - Consider matchup quality when assessing pick difficulty
        """)
