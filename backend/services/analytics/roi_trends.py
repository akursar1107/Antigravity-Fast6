"""
ROI and Profitability Trends Service

Tracks financial performance metrics including:
- Cumulative ROI over time
- Weekly profit/loss breakdowns
- Best/worst pick analysis
- ROI efficiency trends
- Profitability by position, team, odds range

Usage:
    from backend.services.roi_trends_service import get_user_roi_trend, get_weekly_roi
    
    # Get user's ROI over time
    trend = get_user_roi_trend(user_id=1, season=2025)
    
    # Get weekly performance breakdown
    weekly = get_weekly_roi(user_id=1, season=2025)
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from backend.database import get_db_context
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def get_user_roi_trend(user_id: int, season: int) -> pd.DataFrame:
    """
    Calculate cumulative ROI trend for a user over the season.
    
    Args:
        user_id: User ID
        season: NFL season
    
    Returns:
        DataFrame with columns: week, cumulative_roi, cumulative_profit, week_profit
    """
    with get_db_context() as conn:
        query = """
            SELECT 
                w.week,
                SUM(COALESCE(r.actual_return, 0)) as week_profit,
                COUNT(p.id) as picks_count,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN r.is_correct = 0 THEN 1 ELSE 0 END) as losses
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            LEFT JOIN results r ON r.pick_id = p.id
            WHERE p.user_id = ?
                AND w.season = ?
                AND r.actual_return IS NOT NULL
            GROUP BY w.week
            ORDER BY w.week
        """
        
        df = pd.read_sql_query(query, conn, params=(user_id, season))
        
        if df.empty:
            return df
        
        # Convert bytes to proper types if needed (SQLite sometimes returns bytes)
        for col in df.columns:
            if df[col].dtype == object:
                # Try to convert bytes to proper types
                df[col] = df[col].apply(lambda x: int.from_bytes(x, byteorder='little') if isinstance(x, bytes) else x)
        
        # Ensure all numeric columns are proper types
        df['week'] = pd.to_numeric(df['week'], errors='coerce').fillna(0).astype(int)
        df['week_profit'] = pd.to_numeric(df['week_profit'], errors='coerce').fillna(0.0).astype(float)
        df['picks_count'] = pd.to_numeric(df['picks_count'], errors='coerce').fillna(0).astype(int)
        df['wins'] = pd.to_numeric(df['wins'], errors='coerce').fillna(0).astype(int)
        df['losses'] = pd.to_numeric(df['losses'], errors='coerce').fillna(0).astype(int)
        
        # Calculate cumulative ROI
        df['cumulative_profit'] = df['week_profit'].cumsum()
        df['cumulative_picks'] = df['picks_count'].cumsum()
        
        # ROI calculation: (profit / investment) * 100
        # Assuming $1 per pick, investment = number of picks
        df['cumulative_roi'] = (df['cumulative_profit'] / df['cumulative_picks']) * 100
        df['week_roi'] = (df['week_profit'] / df['picks_count']) * 100
        
        # Handle edge case: if cumulative_picks is 0, set ROI to 0
        df['cumulative_roi'] = df['cumulative_roi'].fillna(0)
        df['week_roi'] = df['week_roi'].fillna(0)
        
        return df


def get_weekly_roi_all_users(season: int) -> pd.DataFrame:
    """
    Get weekly ROI for all users for comparison.
    
    Args:
        season: NFL season
    
    Returns:
        DataFrame with columns: week, user_name, week_profit, week_roi, cumulative_roi
    """
    with get_db_context() as conn:
        query = """
            SELECT 
                u.name as user_name,
                w.week,
                SUM(COALESCE(r.actual_return, 0)) as week_profit,
                COUNT(p.id) as picks_count,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as wins
            FROM picks p
            JOIN users u ON p.user_id = u.id
            JOIN weeks w ON p.week_id = w.id
            LEFT JOIN results r ON r.pick_id = p.id
            WHERE w.season = ?
                AND r.actual_return IS NOT NULL
            GROUP BY u.id, u.name, w.week
            ORDER BY u.name, w.week
        """
        
        df = pd.read_sql_query(query, conn, params=(season,))
        
        if df.empty:
            return df
        
        # Convert bytes to proper types if needed (SQLite sometimes returns bytes)
        for col in df.columns:
            if col != 'user_name' and df[col].dtype == object:
                df[col] = df[col].apply(lambda x: int.from_bytes(x, byteorder='little') if isinstance(x, bytes) else x)
        
        # Ensure all columns are proper types
        df['user_name'] = df['user_name'].astype(str)
        df['week'] = pd.to_numeric(df['week'], errors='coerce').fillna(0).astype(int)
        df['week_profit'] = pd.to_numeric(df['week_profit'], errors='coerce').fillna(0.0).astype(float)
        df['picks_count'] = pd.to_numeric(df['picks_count'], errors='coerce').fillna(0).astype(int)
        df['wins'] = pd.to_numeric(df['wins'], errors='coerce').fillna(0).astype(int)
        
        # Calculate ROI per week
        df['week_roi'] = (df['week_profit'] / df['picks_count']) * 100
        
        # Calculate cumulative by user
        df['cumulative_profit'] = df.groupby('user_name')['week_profit'].cumsum()
        df['cumulative_picks'] = df.groupby('user_name')['picks_count'].cumsum()
        df['cumulative_roi'] = (df['cumulative_profit'] / df['cumulative_picks']) * 100
        
        return df


def get_best_worst_picks(user_id: int, season: int, limit: int = 5) -> Dict[str, pd.DataFrame]:
    """
    Get user's best and worst picks by return.
    
    Args:
        user_id: User ID
        season: NFL season
        limit: Number of picks to return for each category
    
    Returns:
        Dict with 'best' and 'worst' DataFrames
    """
    with get_db_context() as conn:
        query = """
            SELECT 
                w.week,
                p.player_name,
                p.team,
                p.odds,
                r.is_correct,
                r.actual_return,
                r.actual_scorer,
                p.theoretical_return
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            LEFT JOIN results r ON r.pick_id = p.id
            WHERE p.user_id = ?
                AND w.season = ?
                AND r.actual_return IS NOT NULL
            ORDER BY r.actual_return DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(user_id, season))
        
        if df.empty:
            return {'best': pd.DataFrame(), 'worst': pd.DataFrame()}
        
        # Get best and worst
        best_picks = df.head(limit)
        worst_picks = df.tail(limit)
        
        return {
            'best': best_picks,
            'worst': worst_picks
        }


def get_roi_by_position(user_id: Optional[int], season: int) -> pd.DataFrame:
    """
    Calculate ROI breakdown by player position.
    
    Args:
        user_id: User ID (None for all users)
        season: NFL season
    
    Returns:
        DataFrame with position-based ROI metrics
    """
    with get_db_context() as conn:
        # Load player positions from player_stats or NFL data
        query = """
            SELECT 
                ps.position,
                COUNT(p.id) as picks_count,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as wins,
                SUM(COALESCE(r.actual_return, 0)) as total_return,
                AVG(p.odds) as avg_odds,
                AVG(COALESCE(r.actual_return, 0)) as avg_return
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            LEFT JOIN results r ON r.pick_id = p.id
            LEFT JOIN player_stats ps ON ps.player_name = p.player_name 
                AND ps.season = w.season
                AND ps.team = p.team
            WHERE w.season = ?
                AND r.actual_return IS NOT NULL
        """
        
        params = [season]
        
        if user_id is not None:
            query += " AND p.user_id = ?"
            params.append(user_id)
        
        query += " GROUP BY ps.position ORDER BY wins DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        
        if not df.empty:
            df['win_rate'] = (df['wins'] / df['picks_count']) * 100
            df['roi'] = (df['total_return'] / df['picks_count']) * 100
        
        return df


def get_roi_by_odds_range(user_id: Optional[int], season: int) -> pd.DataFrame:
    """
    Calculate ROI breakdown by odds ranges.
    
    Args:
        user_id: User ID (None for all users)
        season: NFL season
    
    Returns:
        DataFrame with odds-based ROI metrics
    """
    with get_db_context() as conn:
        query = """
            SELECT 
                p.odds,
                COUNT(p.id) as picks_count,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as wins,
                SUM(COALESCE(r.actual_return, 0)) as total_return,
                AVG(COALESCE(r.actual_return, 0)) as avg_return
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            LEFT JOIN results r ON r.pick_id = p.id
            WHERE w.season = ?
                AND r.actual_return IS NOT NULL
                AND p.odds IS NOT NULL
        """
        
        params = [season]
        
        if user_id is not None:
            query += " AND p.user_id = ?"
            params.append(user_id)
        
        query += " GROUP BY p.odds ORDER BY p.odds"
        
        df = pd.read_sql_query(query, conn, params=params)
        
        if df.empty:
            return df
        
        # Categorize odds into buckets
        def categorize_odds(odds):
            if pd.isna(odds):
                return 'Unknown'
            odds_val = abs(odds)
            if odds_val <= 200:
                return 'Heavy Favorites (<= +200)'
            elif odds_val <= 400:
                return 'Favorites (+200 to +400)'
            elif odds_val <= 600:
                return 'Moderate (+400 to +600)'
            elif odds_val <= 1000:
                return 'Longshots (+600 to +1000)'
            else:
                return 'Heavy Longshots (> +1000)'
        
        df['odds_category'] = df['odds'].apply(categorize_odds)
        
        # Group by category
        result = df.groupby('odds_category').agg({
            'picks_count': 'sum',
            'wins': 'sum',
            'total_return': 'sum',
            'avg_return': 'mean'
        }).reset_index()
        
        result['win_rate'] = (result['wins'] / result['picks_count']) * 100
        result['roi'] = (result['total_return'] / result['picks_count']) * 100
        
        # Sort by odds value
        category_order = [
            'Heavy Favorites (<= +200)',
            'Favorites (+200 to +400)',
            'Moderate (+400 to +600)',
            'Longshots (+600 to +1000)',
            'Heavy Longshots (> +1000)',
            'Unknown'
        ]
        result['sort_order'] = result['odds_category'].map({cat: i for i, cat in enumerate(category_order)})
        result = result.sort_values('sort_order').drop('sort_order', axis=1)
        
        return result


def get_pick_difficulty_analysis(user_id: int, season: int) -> Dict[str, any]:
    """
    Analyze if user's harder picks (longer odds) are paying off.
    
    Args:
        user_id: User ID
        season: NFL season
    
    Returns:
        Dict with difficulty analysis metrics
    """
    with get_db_context() as conn:
        query = """
            SELECT 
                p.odds,
                r.is_correct,
                r.actual_return
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            LEFT JOIN results r ON r.pick_id = p.id
            WHERE p.user_id = ?
                AND w.season = ?
                AND r.actual_return IS NOT NULL
                AND p.odds IS NOT NULL
        """
        
        df = pd.read_sql_query(query, conn, params=(user_id, season))
        
        if df.empty:
            return {
                'correlation': 0,
                'longshot_roi': 0,
                'favorite_roi': 0,
                'strategy_assessment': 'Insufficient data'
            }
        
        # Calculate correlation between odds and success
        correlation = df['odds'].corr(df['is_correct'].astype(float))
        
        # Split into favorites vs longshots
        median_odds = df['odds'].median()
        favorites = df[df['odds'] <= median_odds]
        longshots = df[df['odds'] > median_odds]
        
        fav_roi = (favorites['actual_return'].sum() / len(favorites)) * 100 if len(favorites) > 0 else 0
        long_roi = (longshots['actual_return'].sum() / len(longshots)) * 100 if len(longshots) > 0 else 0
        
        # Assess strategy
        if long_roi > fav_roi and long_roi > 0:
            strategy = 'Strong longshot strategy - higher odds paying off'
        elif fav_roi > long_roi and fav_roi > 0:
            strategy = 'Conservative strategy - favorites performing well'
        elif fav_roi < 0 and long_roi < 0:
            strategy = 'Consider strategy adjustment - both ranges negative'
        else:
            strategy = 'Mixed results - continue current approach'
        
        return {
            'correlation': correlation,
            'longshot_roi': long_roi,
            'favorite_roi': fav_roi,
            'longshot_count': len(longshots),
            'favorite_count': len(favorites),
            'median_odds': median_odds,
            'strategy_assessment': strategy
        }


def get_profitability_summary(user_id: int, season: int) -> Dict[str, any]:
    """
    Get comprehensive profitability summary for a user.
    
    Args:
        user_id: User ID
        season: NFL season
    
    Returns:
        Dict with summary metrics
    """
    with get_db_context() as conn:
        query = """
            SELECT 
                COUNT(p.id) as total_picks,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN r.is_correct = 0 THEN 1 ELSE 0 END) as losses,
                SUM(COALESCE(r.actual_return, 0)) as total_profit,
                AVG(COALESCE(r.actual_return, 0)) as avg_return,
                MAX(COALESCE(r.actual_return, 0)) as best_return,
                MIN(COALESCE(r.actual_return, 0)) as worst_return,
                AVG(p.odds) as avg_odds,
                SUM(p.theoretical_return) as total_theo_return
            FROM picks p
            JOIN weeks w ON p.week_id = w.id
            LEFT JOIN results r ON r.pick_id = p.id
            WHERE p.user_id = ?
                AND w.season = ?
                AND r.actual_return IS NOT NULL
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (user_id, season))
        result = cursor.fetchone()
        
        if not result or result['total_picks'] == 0:
            return {
                'total_picks': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'total_profit': 0,
                'avg_return': 0,
                'roi': 0,
                'best_return': 0,
                'worst_return': 0,
                'avg_odds': 0,
                'roi_efficiency': 0
            }
        
        win_rate = (result['wins'] / result['total_picks']) * 100
        roi = (result['total_profit'] / result['total_picks']) * 100
        
        # ROI Efficiency = Actual ROI / Theoretical ROI
        roi_efficiency = 0
        if result['total_theo_return'] and result['total_theo_return'] != 0:
            theo_roi = (result['total_theo_return'] / result['total_picks']) * 100
            roi_efficiency = (roi / theo_roi) * 100 if theo_roi != 0 else 0
        
        return {
            'total_picks': result['total_picks'],
            'wins': result['wins'],
            'losses': result['losses'],
            'win_rate': win_rate,
            'total_profit': result['total_profit'],
            'avg_return': result['avg_return'],
            'roi': roi,
            'best_return': result['best_return'],
            'worst_return': result['worst_return'],
            'avg_odds': result['avg_odds'],
            'roi_efficiency': roi_efficiency
        }


def get_user_rank_by_roi(season: int) -> pd.DataFrame:
    """
    Get user rankings by ROI for the season.
    
    Args:
        season: NFL season
    
    Returns:
        DataFrame with user rankings
    """
    with get_db_context() as conn:
        query = """
            SELECT 
                u.name as user_name,
                COUNT(p.id) as total_picks,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as wins,
                SUM(COALESCE(r.actual_return, 0)) as total_profit,
                AVG(COALESCE(r.actual_return, 0)) as avg_return
            FROM picks p
            JOIN users u ON p.user_id = u.id
            JOIN weeks w ON p.week_id = w.id
            LEFT JOIN results r ON r.pick_id = p.id
            WHERE w.season = ?
                AND r.actual_return IS NOT NULL
            GROUP BY u.id, u.name
            ORDER BY total_profit DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(season,))
        
        if not df.empty:
            df['win_rate'] = (df['wins'] / df['total_picks']) * 100
            df['roi'] = (df['total_profit'] / df['total_picks']) * 100
            df['rank'] = df['total_profit'].rank(ascending=False, method='dense').astype(int)
        
        return df
