"""Admin Router - Batch Operations and Configuration"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query
from typing import List, Dict, Any
import logging
import sqlite3
import csv
import io
from datetime import datetime

from backend.api.fastapi_dependencies import get_current_admin_user, get_db_async
from backend.api.fastapi_models import AdminPickCreate, PickResponse
from backend.api.fastapi_config import settings
from backend.config import config
from backend.services.data_sync import sync_games_for_season, sync_rosters, sync_touchdowns_for_season
from backend.grading.grading_logic import auto_grade_season
from backend.database.stats import clear_leaderboard_cache
from backend.database import add_pick, get_pick, get_user_week_picks
from backend.database.weeks import get_week, get_week_by_season_week, add_week

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/sync-games")
async def admin_sync_games(
    season: int = Query(None, description="Season year (default: current)"),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """Sync games from nflreadpy into the games table."""
    year = season or settings.current_season
    stats = sync_games_for_season(year)
    logger.info(f"Admin {current_user['name']} synced games for {year}: {stats}")
    return {
        "success": stats["errors"] == 0,
        "season": year,
        "inserted": stats["inserted"],
        "errors": stats["errors"],
    }


@router.post("/sync-rosters")
async def admin_sync_rosters(
    season: int = Query(None, description="Season year (default: current)"),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """Sync rosters from nflreadpy into the rosters table."""
    year = season or settings.current_season
    stats = sync_rosters(year)
    logger.info(f"Admin {current_user['name']} synced rosters for {year}: {stats}")
    return {
        "success": stats["errors"] == 0,
        "season": year,
        "inserted": stats["inserted"],
        "errors": stats["errors"],
    }


@router.post("/sync-touchdowns")
async def admin_sync_touchdowns(
    season: int = Query(None, description="Season year (default: current)"),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """Sync touchdown scorers for final games into touchdowns table."""
    year = season or settings.current_season
    stats = sync_touchdowns_for_season(year)
    logger.info(f"Admin {current_user['name']} synced touchdowns for {year}: {stats}")
    return {
        "success": stats.get("errors", 0) == 0,
        "season": year,
        "games_synced": stats.get("games_synced", 0),
        "inserted": stats.get("inserted", 0),
        "errors": stats.get("errors", 0),
    }


@router.post("/clear-games-and-touchdowns")
async def admin_clear_games_and_touchdowns(
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Clear all rows from games and touchdowns tables. Picks are NOT affected."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM touchdowns")
    tds_deleted = cursor.rowcount
    cursor.execute("DELETE FROM games")
    games_deleted = cursor.rowcount
    conn.commit()
    logger.info(f"Admin {current_user['name']} cleared {games_deleted} games and {tds_deleted} touchdowns")
    return {"success": True, "games_deleted": games_deleted, "touchdowns_deleted": tds_deleted}


@router.post("/picks", response_model=PickResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_pick(
    pick: AdminPickCreate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
) -> PickResponse:
    """Create a pick for a user (admin only)."""
    week = get_week(pick.week_id)
    if not week:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Week not found")

    existing = get_user_week_picks(pick.user_id, pick.week_id)
    if any(
        p.get("player_name", "").lower() == pick.player_name.lower()
        for p in existing
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a pick for this player in this week",
        )

    try:
        pick_id = add_pick(
            user_id=pick.user_id,
            week_id=pick.week_id,
            team=pick.team,
            player_name=pick.player_name,
            odds=pick.odds,
            game_id=pick.game_id,
        )
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has a pick for this player in this week",
            )
        raise

    created = get_pick(pick_id)
    logger.info(f"Admin {current_user['name']} created pick for user {pick.user_id}: {pick.player_name} (ID: {pick_id})")
    return PickResponse(
        id=created["id"],
        user_id=created["user_id"],
        week_id=created["week_id"],
        team=created["team"],
        player_name=created["player_name"],
        odds=created.get("odds"),
        game_id=created.get("game_id"),
        created_at=created.get("created_at") or datetime.utcnow(),
    )


@router.get("/users/{user_id}/picks-with-results")
async def admin_get_user_picks_with_results(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> List[Dict[str, Any]]:
    """Get list of picks for a user with grading info (result_id, is_correct, any_time_td)."""
    cursor = conn.cursor()
    cursor.execute(
        """SELECT p.id, p.user_id, p.week_id, p.team, p.player_name, p.odds, p.game_id,
                  r.id as result_id, r.is_correct, r.any_time_td
           FROM picks p
           LEFT JOIN results r ON p.id = r.pick_id
           WHERE p.user_id = ?
           ORDER BY p.week_id, p.id""",
        (user_id,)
    )
    rows = cursor.fetchall()
    return [
        {
            "id": r[0],
            "user_id": r[1],
            "week_id": r[2],
            "team": r[3],
            "player_name": r[4],
            "odds": r[5],
            "game_id": r[6],
            "result_id": r[7],
            "is_correct": bool(r[8]) if r[8] is not None else None,
            "any_time_td": bool(r[9]) if r[9] is not None else None,
        }
        for r in rows
    ]


@router.post("/recalculate-stats")
async def admin_recalculate_stats(
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Recalculate actual_return for all graded picks from odds, then clear leaderboard cache.
    Use when PTS/ROI/REC appear incorrect after edits or manual grading."""
    cursor = conn.cursor()
    from backend.config import config
    default_stake = config.ROI_STAKE
    cursor.execute(
        """SELECT r.id, r.pick_id, r.is_correct, p.odds, COALESCE(u.base_bet, ?) as stake
           FROM results r
           JOIN picks p ON p.id = r.pick_id
           JOIN users u ON p.user_id = u.id
        """,
        (default_stake,)
    )
    rows = cursor.fetchall()
    updated = 0
    for row in rows:
        result_id, pick_id, is_correct, odds, stake = row
        if is_correct and odds is not None and odds != 0:
            actual_return = stake * (odds / 100.0)  # profit = stake * odds/100
        else:
            actual_return = -stake if not is_correct else 0.0  # loss = -stake
        cursor.execute(
            "UPDATE results SET actual_return = ? WHERE id = ?",
            (actual_return, result_id)
        )
        if cursor.rowcount:
            updated += 1
    conn.commit()
    clear_leaderboard_cache()
    logger.info(f"Admin {current_user['name']} recalculated stats: {updated} results updated")
    return {
        "success": True,
        "results_updated": updated,
        "message": f"Recalculated actual_return for {updated} graded picks. Leaderboard cache cleared.",
    }


@router.post("/cleanup-non-final-games")
async def admin_cleanup_non_final_games(
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Soft-delete games that are scheduled or in progress. Keeps only final games visible."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE games SET deleted_at = CURRENT_TIMESTAMP WHERE status IN ('scheduled', 'in_progress') AND (deleted_at IS NULL OR deleted_at = '')"
        )
    except sqlite3.OperationalError:
        cursor.execute(
            "DELETE FROM games WHERE status IN ('scheduled', 'in_progress')"
        )
    deleted = cursor.rowcount
    conn.commit()
    logger.info(f"Admin {current_user['name']} removed {deleted} non-final games")
    return {"success": True, "deleted": deleted}


@router.post("/grade-pending")
async def admin_grade_pending(
    season: int = Query(None, description="Season year (default: current)"),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """Grade only ungraded (pending) picks for the season. Does not clear existing results."""
    year = season or settings.current_season
    stats = auto_grade_season(year)
    if "error" in stats:
        return {"success": False, "season": year, "error": stats["error"], "graded_picks": 0}
    graded = stats.get("graded_picks", 0)
    logger.info(f"Admin {current_user['name']} graded {graded} pending picks for season {year}")
    return {
        "success": True,
        "season": year,
        "graded_picks": graded,
        "correct_first_td": stats.get("correct_first_td", 0),
        "any_time_td": stats.get("any_time_td", 0),
        "failed_to_match": stats.get("failed_to_match", 0),
    }


@router.post("/regrade-season")
async def admin_regrade_season(
    season: int = Query(None, description="Season year (default: current)"),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Delete all results for the season and re-run auto-grading. Use when TD data or logic has changed."""
    year = season or settings.current_season
    cursor = conn.cursor()
    cursor.execute(
        """DELETE FROM results WHERE pick_id IN (
            SELECT p.id FROM picks p
            JOIN weeks w ON p.week_id = w.id
            WHERE w.season = ?
        )""",
        (year,),
    )
    deleted = cursor.rowcount
    conn.commit()
    logger.info(f"Admin {current_user['name']} cleared {deleted} results for season {year}, re-grading...")
    stats = auto_grade_season(year)
    if "error" in stats:
        return {"success": False, "season": year, "error": stats["error"], "graded_picks": 0}
    return {
        "success": True,
        "season": year,
        "results_cleared": deleted,
        "graded_picks": stats.get("graded_picks", 0),
        "correct_first_td": stats.get("correct_first_td", 0),
        "any_time_td": stats.get("any_time_td", 0),
        "failed_to_match": stats.get("failed_to_match", 0),
    }


@router.post("/batch-grade")
async def batch_grade_picks(
    grades: List[Dict[str, Any]],
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Batch grade multiple picks. Each grade dict: {pick_id, is_correct, any_time_td, actual_scorer}"""
    cursor = conn.cursor()
    graded_count = 0
    errors = []
    
    for grade in grades:
        try:
            pick_id = grade.get("pick_id")
            is_correct = grade.get("is_correct", False)
            any_time_td = grade.get("any_time_td", False)
            actual_scorer = grade.get("actual_scorer")
            
            # Verify pick exists and get odds, user's base_bet for actual_return
            cursor.execute(
                """SELECT p.id, p.odds, COALESCE(u.base_bet, ?) FROM picks p
                   JOIN users u ON p.user_id = u.id WHERE p.id = ?""",
                (config.ROI_STAKE, pick_id)
            )
            pick_row = cursor.fetchone()
            if not pick_row:
                errors.append(f"Pick {pick_id} not found")
                continue
            
            odds, stake = pick_row[1], pick_row[2]
            if is_correct and odds is not None and odds != 0:
                actual_return = stake * (odds / 100.0)  # profit = stake * odds/100
            else:
                actual_return = -stake if not is_correct else 0.0  # loss = -stake
            
            # Check if already graded
            cursor.execute("SELECT id FROM results WHERE pick_id = ?", (pick_id,))
            if cursor.fetchone():
                errors.append(f"Pick {pick_id} already graded")
                continue
            
            # Insert result
            cursor.execute(
                """INSERT INTO results (pick_id, is_correct, any_time_td, actual_scorer, actual_return)
                   VALUES (?, ?, ?, ?, ?)""",
                (pick_id, int(is_correct), int(any_time_td), actual_scorer, actual_return)
            )
            graded_count += 1
            
        except Exception as e:
            errors.append(f"Error grading pick {pick_id}: {str(e)}")
    
    conn.commit()
    logger.info(f"Admin {current_user['name']} batch graded {graded_count} picks")
    
    return {
        "success": True,
        "graded_count": graded_count,
        "error_count": len(errors),
        "errors": errors if errors else None
    }


@router.post("/csv-import")
async def import_picks_csv(
    file: UploadFile = File(...),
    week_id: int = None,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Import picks from CSV file. Columns: User,Player,Team,Odds (Team optional)"""
    cursor = conn.cursor()
    imported_count = 0
    errors = []
    
    try:
        contents = await file.read()
        text_stream = io.StringIO(contents.decode("utf-8"))
        reader = csv.DictReader(text_stream)
        
        # If week_id not provided, use current week
        if not week_id:
            cursor.execute("SELECT id FROM weeks WHERE started_at <= datetime('now') AND ended_at > datetime('now') LIMIT 1")
            row = cursor.fetchone()
            if not row:
                raise ValueError("No active week found and week_id not provided")
            week_id = row[0]
        
        for row_idx, row in enumerate(reader, start=2):  # Start at 2 (after header)
            try:
                user_name = row.get("User", "").strip()
                player_name = row.get("Player", "").strip()
                team = row.get("Team", "").strip()
                odds = float(row.get("Odds", 0))
                
                if not all([user_name, player_name]):
                    errors.append(f"Row {row_idx}: Missing User or Player")
                    continue
                
                # Find user
                cursor.execute("SELECT id FROM users WHERE name = ?", (user_name,))
                user_row = cursor.fetchone()
                if not user_row:
                    errors.append(f"Row {row_idx}: User '{user_name}' not found")
                    continue
                
                user_id = user_row[0]
                
                # Check for duplicate
                cursor.execute(
                    "SELECT id FROM picks WHERE user_id = ? AND week_id = ? AND player_name = ?",
                    (user_id, week_id, player_name)
                )
                if cursor.fetchone():
                    errors.append(f"Row {row_idx}: Duplicate pick for {user_name}/{player_name}")
                    continue
                
                # Insert pick
                cursor.execute(
                    """INSERT INTO picks (user_id, week_id, team, player_name, odds)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, week_id, team or "Unknown", player_name, odds or None)
                )
                imported_count += 1
                
            except ValueError as e:
                errors.append(f"Row {row_idx}: Invalid odds value - {str(e)}")
            except Exception as e:
                errors.append(f"Row {row_idx}: {str(e)}")
        
        conn.commit()
        logger.info(f"Admin {current_user['name']} imported {imported_count} picks from CSV")
        
        return {
            "success": True,
            "imported_count": imported_count,
            "error_count": len(errors),
            "errors": errors if errors else None
        }
        
    except Exception as e:
        logger.error(f"CSV import error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"CSV import failed: {str(e)}")


@router.get("/logs")
async def get_admin_logs(
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """Get admin activity and error logs (stub - no admin_logs table)"""
    return {
        "status": "operational",
        "activity_summary": {
            "total_grades": 0,
            "total_imports": 0,
            "users_created": 0,
            "users_deleted": 0
        },
        "logs": [],
        "message": "Admin logs not yet implemented"
    }


@router.post("/user-reset")
async def reset_user_picks(
    user_id: int,
    week_id: int = None,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Reset (delete) all picks for a user in a week or season"""
    cursor = conn.cursor()
    
    try:
        # Verify user exists
        cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        if week_id:
            # Delete results first (foreign key on picks), then picks
            cursor.execute(
                "DELETE FROM results WHERE pick_id IN (SELECT id FROM picks WHERE user_id = ? AND week_id = ?)",
                (user_id, week_id)
            )
            cursor.execute("DELETE FROM picks WHERE user_id = ? AND week_id = ?", (user_id, week_id))
        else:
            # Delete results first, then all picks for user
            cursor.execute(
                "DELETE FROM results WHERE pick_id IN (SELECT id FROM picks WHERE user_id = ?)",
                (user_id,)
            )
            cursor.execute("DELETE FROM picks WHERE user_id = ?", (user_id,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        logger.warning(f"Admin {current_user['name']} reset {deleted_count} picks for user {user[0]}")
        
        return {
            "success": True,
            "user_id": user_id,
            "user_name": user[0],
            "deleted_count": deleted_count,
            "week_id": week_id
        }
        
    except Exception as e:
        logger.error(f"User reset error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/stats")
async def get_admin_stats(
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Get system-wide statistics for admin dashboard"""
    cursor = conn.cursor()
    
    # Get various counts
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM picks")
    pick_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM results")
    result_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM weeks")
    week_count = cursor.fetchone()[0]
    
    ungraded = pick_count - result_count
    
    return {
        "system_stats": {
            "total_users": user_count,
            "total_picks": pick_count,
            "graded_picks": result_count,
            "ungraded_picks": ungraded,
            "grading_progress": round(100.0 * result_count / max(pick_count, 1), 1),
            "total_seasons": week_count
        }
    }
