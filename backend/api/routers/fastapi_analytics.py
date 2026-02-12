"""Analytics Router - Player and Team Analytics"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Dict, Any
import logging
import sqlite3

from backend.api.fastapi_dependencies import get_current_user, get_db_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/player-stats")
async def get_player_stats(
    season: int = Query(..., description="NFL season"),
    limit: int = Query(50, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get top performing players for the season"""
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT 
                p.player_name,
                p.team,
                COUNT(DISTINCT ps.player_name) as first_td_count,
                ROUND(SUM(CASE WHEN r.any_time_td = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT p.id), 0) * 100, 1) as any_time_td_rate,
                ROUND(100.0 * COUNT(CASE WHEN r.is_correct = 1 THEN 1 END) / NULLIF(COUNT(DISTINCT p.id), 0), 1) as accuracy
           FROM picks p
           LEFT JOIN weeks w ON p.week_id = w.id
           LEFT JOIN results r ON p.id = r.pick_id
           LEFT JOIN player_stats ps ON p.player_name = ps.player_name AND ps.season = w.season
           WHERE w.season = ?
           GROUP BY p.player_name, p.team
           ORDER BY first_td_count DESC, accuracy DESC
           LIMIT ?""",
        (season, limit)
    )
    
    results = cursor.fetchall()
    return [
        {
            "player_name": r[0],
            "team": r[1],
            "first_td_count": r[2] or 0,
            "any_time_td_rate": r[3] or 0,
            "accuracy": r[4] or 0
        }
        for r in results
    ]


@router.get("/team-defense")
async def get_team_defense_stats(
    season: int = Query(..., description="NFL season"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get defensive matchup statistics - which teams allow most TDs"""
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT 
                p.team as team_picked,
                COUNT(p.id) as total_picks,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as correct_picks,
                ROUND(100.0 * SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(p.id), 0), 1) as accuracy
           FROM picks p
           LEFT JOIN weeks w ON p.week_id = w.id
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE w.season = ?
           GROUP BY p.team
           ORDER BY accuracy DESC""",
        (season,)
    )
    
    results = cursor.fetchall()
    return [
        {
            "team": r[0],
            "total_picks": r[1] or 0,
            "correct_picks": r[2] or 0,
            "accuracy": r[3] or 0
        }
        for r in results
    ]


@router.get("/roi-trends")
async def get_roi_trends(
    season: int = Query(..., description="NFL season"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get ROI trends by week. ROI: loss = -stake, win = stake * (odds/100) profit."""
    from backend.config import config
    roi_fb = f"""CASE WHEN p.odds IS NOT NULL AND r.is_correct IS NOT NULL THEN
        CASE WHEN r.is_correct = 1 THEN COALESCE(u.base_bet, {config.ROI_STAKE}) * (p.odds/100.0) ELSE -COALESCE(u.base_bet, {config.ROI_STAKE}) END ELSE 0 END"""
    cursor = conn.cursor()
    cursor.execute(
        f"""SELECT 
                w.week,
                COUNT(p.id) as picks_count,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                ROUND(100.0 * SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(p.id), 0), 1) as accuracy,
                SUM(COALESCE(r.actual_return, {roi_fb})) as roi_dollars
           FROM weeks w
           LEFT JOIN picks p ON w.id = p.week_id
           LEFT JOIN users u ON p.user_id = u.id
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE w.season = ?
           GROUP BY w.week
           ORDER BY w.week""",
        (season,)
    )
    
    results = cursor.fetchall()
    return [
        {
            "week": r[0],
            "picks_count": r[1] or 0,
            "correct_count": r[2] or 0,
            "accuracy": r[3] or 0,
            "roi_dollars": round(r[4] or 0, 2)
        }
        for r in results
    ]


@router.get("/roi-trends-by-user")
async def get_roi_trends_by_user(
    season: int = Query(..., description="NFL season"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get per-user ROI by week for multi-user comparison chart"""
    cursor = conn.cursor()
    from backend.config import config
    roi_fb = f"""CASE WHEN p.odds IS NOT NULL AND r.is_correct IS NOT NULL THEN
        CASE WHEN r.is_correct = 1 THEN COALESCE(u.base_bet, {config.ROI_STAKE}) * (p.odds/100.0) ELSE -COALESCE(u.base_bet, {config.ROI_STAKE}) END ELSE 0 END"""
    cursor.execute(
        f"""SELECT 
                w.week,
                u.name as user_name,
                SUM(COALESCE(r.actual_return, {roi_fb})) as roi_dollars
           FROM weeks w
           JOIN picks p ON w.id = p.week_id
           JOIN users u ON p.user_id = u.id
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE w.season = ?
           GROUP BY w.week, u.id, u.name
           ORDER BY w.week, u.name""",
        (season,)
    )
    results = cursor.fetchall()
    return [
        {
            "week": r[0],
            "user_name": r[1],
            "roi_dollars": round(r[2] or 0, 2)
        }
        for r in results
    ]


@router.get("/odds-accuracy")
async def get_odds_accuracy(
    season: int = Query(..., description="NFL season"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get accuracy grouped by odds ranges"""
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT 
                CASE
                    WHEN p.odds < 100 THEN '<100'
                    WHEN p.odds < 200 THEN '100-200'
                    WHEN p.odds < 500 THEN '200-500'
                    WHEN p.odds < 1000 THEN '500-1000'
                    ELSE '1000+'
                END as odds_range,
                COUNT(p.id) as picks_count,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                ROUND(100.0 * SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(p.id), 0), 1) as accuracy,
                ROUND(AVG(p.odds), 0) as avg_odds
           FROM picks p
           LEFT JOIN weeks w ON p.week_id = w.id
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE w.season = ? AND p.odds IS NOT NULL
           GROUP BY odds_range
           ORDER BY avg_odds""",
        (season,)
    )
    
    results = cursor.fetchall()
    return [
        {
            "odds_range": r[0],
            "picks_count": r[1] or 0,
            "correct_count": r[2] or 0,
            "accuracy": r[3] or 0,
            "avg_odds": int(r[4] or 0)
        }
        for r in results
    ]


@router.get("/grading-status")
async def get_grading_status(
    season: int = Query(..., description="NFL season"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Get grading progress for season"""
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT 
                COUNT(DISTINCT p.id) as total_picks,
                SUM(CASE WHEN r.id IS NOT NULL THEN 1 ELSE 0 END) as graded_picks,
                SUM(CASE WHEN r.id IS NULL THEN 1 ELSE 0 END) as ungraded_picks
           FROM picks p
           LEFT JOIN weeks w ON p.week_id = w.id
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE w.season = ?""",
        (season,)
    )
    
    stats = cursor.fetchone()
    total = stats[0] or 0
    graded = stats[1] or 0
    ungraded = stats[2] or 0
    
    return {
        "season": season,
        "total_picks": total,
        "graded_picks": graded,
        "ungraded_picks": ungraded,
        "grading_progress": round(100.0 * graded / max(total, 1), 1)
    }


@router.get("/user-stats")
async def get_user_stats(
    season: int = Query(..., description="NFL season"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get current user's performance stats: win rate, Brier score, etc."""
    from backend.services.performance_service import PickerPerformanceService
    service = PickerPerformanceService()
    summary = service.get_user_performance_summary(current_user["id"], season)
    return {
        "user_id": current_user["id"],
        "user_name": current_user["name"],
        "season": season,
        "total_picks": summary["total_picks"],
        "wins": summary["wins"],
        "losses": summary["losses"],
        "win_rate": summary["win_rate"],
        "brier_score": summary["brier_score"],
        "current_streak": summary["streaks"]["current_streak"],
        "longest_win_streak": summary["streaks"]["longest_win_streak"],
        "is_hot": summary["streaks"]["is_hot"],
    }


@router.get("/performance-breakdown")
async def get_performance_breakdown(
    season: int = Query(..., description="NFL season"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get per-user performance stats (win rate, Brier score) for multi-user comparison."""
    from backend.database import get_all_users
    from backend.services.performance_service import PickerPerformanceService

    service = PickerPerformanceService()
    users = get_all_users()
    results = []

    for u in users:
        summary = service.get_user_performance_summary(u["id"], season)
        results.append({
            "user_id": u["id"],
            "user_name": u["name"],
            "total_picks": summary["total_picks"],
            "wins": summary["wins"],
            "losses": summary["losses"],
            "win_rate": summary["win_rate"],
            "brier_score": summary["brier_score"],
            "current_streak": summary["streaks"]["current_streak"],
            "is_hot": summary["streaks"]["is_hot"],
        })

    return sorted(results, key=lambda r: (-r["total_picks"], r["user_name"]))


@router.get("/all-touchdowns")
async def get_all_touchdowns(
    season: int = Query(..., description="NFL season"),
    week: int = Query(None, description="Filter by week (optional)"),
    team: str = Query(None, description="Filter by team abbreviation (optional)"),
    first_td_only: bool = Query(False, description="Only first TD of each game"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get all touchdowns for the season, optionally filtered by week/team. Data from touchdowns table; sync via Admin first."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='touchdowns'")
    if not cursor.fetchone():
        return []

    query = "SELECT t.game_id, t.player_name, t.team, t.is_first_td, t.play_id, t.season FROM touchdowns t WHERE t.season = ?"
    params: List[Any] = [season]

    if week is not None:
        query += " AND t.game_id LIKE ?"
        params.append(f"{season}_{week:02d}_%")

    if team:
        query += " AND t.team = ?"
        params.append(team.upper())

    if first_td_only:
        query += " AND t.is_first_td = 1"

    query += " ORDER BY t.game_id, t.play_id"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    return [
        {
            "game_id": str(r[0] or ""),
            "player_name": str(r[1] or "").strip(),
            "team": str(r[2] or "").strip(),
            "is_first_td": bool(r[3]),
            "play_id": r[4],
            "season": r[5],
        }
        for r in rows
    ]


def _get_td_scorers_from_db(conn: sqlite3.Connection, game_id: str) -> List[Dict[str, Any]]:
    """Get touchdown scorers from touchdowns table. Returns [] if empty."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT player_name, team, COALESCE(is_first_td, 0) FROM touchdowns WHERE game_id = ? ORDER BY play_id",
        (game_id,),
    )
    rows = cursor.fetchall()
    return [
        {"player_name": str(r[0] or "").strip(), "team": str(r[1] or "").strip(), "is_first_td": bool(r[2])}
        for r in rows
    ]


def _get_td_scorers_from_pbp(game_id: str) -> List[Dict[str, Any]]:
    """Fallback: get TD scorers from nflreadpy play-by-play. Returns [] if unavailable."""
    try:
        from backend.services.data_sync import validate_game_id
        if not validate_game_id(game_id):
            return []
        parts = game_id.split("_")
        season = int(parts[0])
        from backend.analytics.nfl_data import load_data, get_touchdowns

        df = load_data(season)
        if df.empty:
            return []
        tds = get_touchdowns(df)
        if tds.empty or "game_id" not in tds.columns:
            return []
        game_tds = tds[tds["game_id"] == game_id]
        if game_tds.empty:
            return []
        if "play_id" in game_tds.columns:
            game_tds = game_tds.sort_values("play_id")
        team_col = "td_scorer_team" if "td_scorer_team" in tds.columns else "posteam"
        result = []
        first_play_id = game_tds.iloc[0].get("play_id") if "play_id" in game_tds.columns else None
        for idx, (_, row) in enumerate(game_tds.iterrows()):
            name = row.get("td_player_name") or "Unknown"
            team = row.get(team_col) or ""
            play_id = row.get("play_id")
            is_first = bool(play_id is not None and play_id == first_play_id) if first_play_id is not None else (idx == 0)
            result.append({
                "player_name": str(name).strip(),
                "team": str(team) if team else "",
                "is_first_td": is_first,
            })
        return result
    except Exception as e:
        logger.warning(f"Could not load TD scorers from PBP for {game_id}: {e}")
        return []


def _parse_game_id_fallback(game_id: str) -> tuple[str, str] | None:
    """Parse game_id format season_week_away_home (e.g. 2025_01_DAL_PHI) -> (home_team, away_team)."""
    parts = game_id.split("_")
    if len(parts) >= 4:
        try:
            away, home = parts[2], parts[3]
            if len(away) in (2, 3) and len(home) in (2, 3):
                return (home, away)
        except (ValueError, IndexError):
            pass
    return None


@router.get("/matchup/{game_id}")
async def get_game_matchup_data(
    game_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Get analytics for specific game matchup"""
    cursor = conn.cursor()

    cursor.execute(
        "SELECT home_team, away_team, status FROM games WHERE id = ?",
        (game_id,)
    )
    game = cursor.fetchone()

    if game:
        home_team, away_team, game_status = game[0], game[1], game[2]
    else:
        parsed = _parse_game_id_fallback(game_id)
        if not parsed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
        home_team, away_team = parsed
        game_status = "scheduled"

    cursor.execute(
        """SELECT 
                p.team,
                COUNT(p.id) as picks_count,
                SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                ROUND(100.0 * SUM(CASE WHEN r.is_correct = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(p.id), 0), 1) as accuracy
           FROM picks p
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE p.game_id = ?
           GROUP BY p.team""",
        (game_id,)
    )
    pick_stats = {r[0]: {"picks_count": r[1] or 0, "correct_count": r[2] or 0, "accuracy": r[3] or 0} for r in cursor.fetchall()}

    def team_stats(team: str) -> Dict[str, Any]:
        s = pick_stats.get(team, {"picks_count": 0, "correct_count": 0, "accuracy": 0})
        return {"team": team, "picks_count": s["picks_count"], "correct_count": s["correct_count"], "accuracy": s["accuracy"]}

    resp = {
        "game_id": game_id,
        "status": game_status,
        "teams": [
            team_stats(home_team),
            team_stats(away_team),
        ],
    }

    if game_status == "final":
        td_scorers = _get_td_scorers_from_db(conn, game_id)
        if not td_scorers:
            td_scorers = _get_td_scorers_from_pbp(game_id)
        resp["td_scorers"] = td_scorers
    else:
        resp["td_scorers"] = []

    # Include picks for this game
    cursor.execute(
        """SELECT p.id, u.name, p.team, p.player_name, p.odds, r.is_correct, r.actual_scorer, r.any_time_td
           FROM picks p
           JOIN users u ON p.user_id = u.id
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE p.game_id = ?
           ORDER BY p.created_at""",
        (game_id,),
    )
    picks_rows = cursor.fetchall()
    resp["picks"] = [
        {
            "id": r[0],
            "user_name": str(r[1] or ""),
            "team": str(r[2] or ""),
            "player_name": str(r[3] or ""),
            "odds": r[4] or 0,
            "is_correct": bool(r[5]) if r[5] is not None else None,
            "actual_scorer": str(r[6]).strip() if r[6] else None,
            "any_time_td": bool(r[7]) if r[7] is not None else None,
        }
        for r in picks_rows
    ]

    return resp
