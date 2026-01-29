"""
Market Comparison Tab
Compare prediction market odds from Polymarket and Kalshi with actual results.

Features:
- Side-by-side odds comparison across sources
- Historical odds movement charts
- Calibration analysis (how accurate are market probabilities?)
- Value opportunities identification
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, Dict, List

import config
from database.market_odds import (
    get_market_odds_for_week,
    get_market_odds_for_player,
    get_latest_odds_snapshot,
    get_market_accuracy_stats,
    get_odds_comparison
)
from database import get_all_weeks
from services.market_data_service import MarketDataService, get_week_dates
from utils.prediction_markets import get_enabled_sources, test_connections


def show_market_comparison_tab(season: int, schedule: Optional[pd.DataFrame] = None):
    """Display prediction market comparison analytics."""

    st.header("📊 Prediction Market Analysis")
    st.markdown("Compare first TD odds from Polymarket, Kalshi, and traditional sportsbooks")

    # Check if any sources are enabled
    enabled = get_enabled_sources()
    if not enabled:
        st.warning(
            "No prediction market sources are enabled. "
            "Enable Polymarket and/or Kalshi in the configuration."
        )
        return

    st.info(f"**Enabled sources:** {', '.join(s.title() for s in enabled)}")

    # Sub-tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Game Odds",
        "📈 Price History",
        "🎲 Market Accuracy",
        "💡 Value Finder"
    ])

    with tab1:
        _show_game_odds_comparison(season, schedule)

    with tab2:
        _show_price_history(season)

    with tab3:
        _show_accuracy_analysis(season)

    with tab4:
        _show_value_finder(season)


def _show_game_odds_comparison(season: int, schedule: Optional[pd.DataFrame]):
    """Compare odds across sources for a specific game."""
    st.subheader("Compare Odds by Game")

    # Week selector
    weeks = get_all_weeks(season)
    if not weeks:
        st.warning("No data available for this season")
        return

    week_options = [w['week'] for w in weeks]
    selected_week = st.selectbox(
        "Select Week",
        options=week_options,
        index=len(week_options) - 1 if week_options else 0,
        key="market_week"
    )

    # Get odds for the week
    week_odds = get_market_odds_for_week(season, selected_week)

    if not week_odds:
        st.info(f"No market odds data available for Week {selected_week}")

        # Offer to fetch
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Fetch Odds", type="primary"):
                with st.spinner("Fetching from prediction markets..."):
                    service = MarketDataService()
                    start_date, end_date = get_week_dates(season, selected_week)
                    result = service.fetch_and_store_week_odds(
                        season, selected_week, start_date, end_date
                    )
                    total = sum(result.values())
                    if total > 0:
                        st.success(f"Fetched {total} odds records!")
                        st.rerun()
                    else:
                        st.warning("No NFL first TD markets found for this week")
        return

    # Get unique games
    games = list(set(o['game_id'] for o in week_odds))
    selected_game = st.selectbox(
        "Select Game",
        options=games,
        key="market_game"
    )

    if selected_game:
        # Get odds comparison for this game
        game_odds = get_odds_comparison(selected_game)

        if not game_odds:
            st.info("No odds data for this game")
            return

        # Build comparison dataframe
        rows = []
        for player, sources in game_odds.items():
            row = {'Player': player}
            for source_data in sources:
                source = source_data['source']
                prob = source_data.get('implied_probability', 0)
                odds = source_data.get('american_odds', 0)
                row[f'{source.title()} Prob'] = f"{prob*100:.1f}%"
                row[f'{source.title()} Odds'] = f"+{odds}" if odds > 0 else str(odds)
            rows.append(row)

        df = pd.DataFrame(rows)

        # Display table
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Visualization
        _plot_odds_comparison(game_odds, selected_game)


def _plot_odds_comparison(game_odds: Dict, game_id: str):
    """Create bar chart comparing odds across sources."""
    # Prepare data for plotting
    plot_data = []
    for player, sources in game_odds.items():
        for source_data in sources:
            plot_data.append({
                'Player': player[:20],  # Truncate long names
                'Source': source_data['source'].title(),
                'Probability': source_data.get('implied_probability', 0) * 100
            })

    if not plot_data:
        return

    df = pd.DataFrame(plot_data)

    fig = px.bar(
        df,
        x='Player',
        y='Probability',
        color='Source',
        barmode='group',
        title=f"First TD Odds Comparison - {game_id}",
        labels={'Probability': 'Implied Probability (%)'}
    )

    fig.update_layout(
        xaxis_tickangle=-45,
        height=400,
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)


def _show_price_history(season: int):
    """Show historical price movement for a player."""
    st.subheader("Historical Price Movement")

    # Player search
    player_search = st.text_input(
        "Search Player Name",
        placeholder="e.g., Patrick Mahomes",
        key="market_player_search"
    )

    if not player_search:
        st.info("Enter a player name to see their historical odds")
        return

    odds_data = get_market_odds_for_player(player_search, season)

    if not odds_data:
        st.warning(f"No odds history found for '{player_search}'")
        return

    df = pd.DataFrame(odds_data)

    # Summary stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", len(df))
    with col2:
        avg_prob = df['implied_probability'].mean() * 100
        st.metric("Avg Probability", f"{avg_prob:.1f}%")
    with col3:
        sources = df['source'].nunique()
        st.metric("Sources", sources)

    # Time series chart
    if 'snapshot_time' in df.columns:
        fig = go.Figure()

        for source in df['source'].unique():
            source_df = df[df['source'] == source].sort_values('snapshot_time')
            fig.add_trace(go.Scatter(
                x=source_df['snapshot_time'],
                y=source_df['implied_probability'] * 100,
                mode='lines+markers',
                name=source.title(),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                              'Time: %{x}<br>' +
                              'Probability: %{y:.1f}%<br>' +
                              '<extra></extra>'
            ))

        fig.update_layout(
            title=f"Historical Odds - {player_search}",
            xaxis_title="Time",
            yaxis_title="Implied Probability (%)",
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

    # Data table
    with st.expander("View Raw Data"):
        display_df = df[['source', 'game_id', 'week', 'implied_probability', 'american_odds', 'volume', 'snapshot_time']]
        st.dataframe(display_df, use_container_width=True, hide_index=True)


def _show_accuracy_analysis(season: int):
    """Analyze how well calibrated market probabilities are."""
    st.subheader("Market Accuracy Analysis")

    st.markdown("""
    **How accurate are prediction market odds?**

    This analysis compares market favorites (highest probability players)
    against actual first TD scorers to measure prediction accuracy.
    """)

    # Get stats for each source
    sources = get_enabled_sources()

    if not sources:
        st.info("No sources enabled")
        return

    col1, col2 = st.columns(2)

    for i, source in enumerate(sources):
        stats = get_market_accuracy_stats(season, source)

        with col1 if i % 2 == 0 else col2:
            st.markdown(f"### {source.title()}")

            if stats and stats.get('total_games', 0) > 0:
                m1, m2 = st.columns(2)
                with m1:
                    st.metric(
                        "Games Analyzed",
                        stats.get('total_games', 0)
                    )
                with m2:
                    accuracy = stats.get('accuracy_rate', 0) * 100
                    st.metric(
                        "Favorite Win Rate",
                        f"{accuracy:.1f}%"
                    )

                avg_prob = stats.get('avg_winner_probability', 0) * 100
                st.metric(
                    "Avg Winner Probability",
                    f"{avg_prob:.1f}%"
                )
            else:
                st.info("Not enough data for analysis")

    # Overall stats
    st.markdown("---")
    st.markdown("### Combined Analysis")

    overall_stats = get_market_accuracy_stats(season)
    if overall_stats and overall_stats.get('total_games', 0) > 0:
        cols = st.columns(4)
        with cols[0]:
            st.metric("Total Games", overall_stats.get('total_games', 0))
        with cols[1]:
            st.metric("Favorites Won", overall_stats.get('favorites_correct', 0))
        with cols[2]:
            accuracy = overall_stats.get('accuracy_rate', 0) * 100
            st.metric("Accuracy Rate", f"{accuracy:.1f}%")
        with cols[3]:
            avg_prob = overall_stats.get('avg_winner_probability', 0) * 100
            st.metric("Avg Winner Prob", f"{avg_prob:.1f}%")
    else:
        st.info(
            "Link market odds to actual results using the Admin interface "
            "to see accuracy statistics."
        )


def _show_value_finder(season: int):
    """Identify potential value picks based on market discrepancies."""
    st.subheader("Value Opportunity Finder")

    st.markdown("""
    **Find players where prediction market odds differ significantly**

    Large differences between sources may indicate value opportunities
    or market inefficiencies.
    """)

    # Week selector
    weeks = get_all_weeks(season)
    if not weeks:
        st.warning("No data available")
        return

    week_options = [w['week'] for w in weeks]
    selected_week = st.selectbox(
        "Select Week",
        options=week_options,
        index=len(week_options) - 1 if week_options else 0,
        key="value_week"
    )

    # Threshold slider
    threshold = st.slider(
        "Minimum Probability Difference",
        min_value=1,
        max_value=20,
        value=5,
        format="%d%%",
        key="value_threshold"
    ) / 100

    # Find opportunities
    service = MarketDataService()
    opportunities = service.get_value_opportunities(
        season, selected_week, threshold
    )

    if not opportunities:
        st.info(
            f"No significant odds differences (>{threshold*100:.0f}%) found for Week {selected_week}. "
            "Try fetching odds from multiple sources first."
        )
        return

    # Display opportunities
    st.success(f"Found {len(opportunities)} potential value opportunities")

    # Build dataframe
    rows = []
    for opp in opportunities:
        rows.append({
            'Player': opp['player'],
            'Game': opp['game_id'],
            f"{opp['source1'].title()} Prob": f"{opp['prob1']*100:.1f}%",
            f"{opp['source2'].title()} Prob": f"{opp['prob2']*100:.1f}%",
            'Difference': f"{opp['prob_diff']*100:.1f}%"
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Visualization
    if len(opportunities) > 0:
        fig = px.bar(
            pd.DataFrame(opportunities),
            x='player',
            y='prob_diff',
            color='source1',
            title="Probability Differences by Player",
            labels={'prob_diff': 'Probability Difference', 'player': 'Player'}
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            yaxis_tickformat='.1%',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
