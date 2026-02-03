"""Admin Router - Batch Operations and Configuration"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import List, Dict, Any
import logging
import sqlite3
import csv
import io
from datetime import datetime

from src.api.fastapi_dependencies import get_current_admin_user, get_db_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


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
            
            # Verify pick exists
            cursor.execute("SELECT id FROM picks WHERE id = ?", (pick_id,))
            if not cursor.fetchone():
                errors.append(f"Pick {pick_id} not found")
                continue
            
            # Check if already graded
            cursor.execute("SELECT id FROM results WHERE pick_id = ?", (pick_id,))
            if cursor.fetchone():
                errors.append(f"Pick {pick_id} already graded")
                continue
            
            # Insert result
            cursor.execute(
                """INSERT INTO results (pick_id, is_correct, any_time_td, actual_scorer, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (pick_id, int(is_correct), int(any_time_td), actual_scorer, datetime.now().isoformat())
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
                
                # Look up position from rosters
                position = None
                if team:
                    cursor.execute(
                        "SELECT position FROM rosters WHERE player_name = ? AND team = ?",
                        (player_name, team)
                    )
                    pos_row = cursor.fetchone()
                    if pos_row:
                        position = pos_row[0]
                
                # Insert pick
                cursor.execute(
                    """INSERT INTO picks (user_id, week_id, team, player_name, odds, position, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, week_id, team or "Unknown", player_name, odds or None, position, datetime.now().isoformat())
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


@router.post("/sync-rosters")
async def manual_sync_rosters(
    season: int,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Manually trigger roster sync from NFL data"""
    try:
        from src.utils.nfl_data import sync_rosters
        
        cursor = conn.cursor()
        sync_rosters(conn, season)
        
        cursor.execute("SELECT COUNT(*) FROM rosters WHERE season = ?", (season,))
        roster_count = cursor.fetchone()[0]
        
        logger.info(f"Admin {current_user['name']} synced rosters for season {season}")
        
        return {
            "success": True,
            "season": season,
            "roster_count": roster_count,
            "message": f"Synced {roster_count} roster entries"
        }
        
    except Exception as e:
        logger.error(f"Roster sync error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Roster sync failed: {str(e)}")


@router.get("/logs")
async def get_admin_logs(
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
    conn: sqlite3.Connection = Depends(get_db_async)
) -> Dict[str, Any]:
    """Get admin activity and error logs"""
    cursor = conn.cursor()
    
    # Activity summary
    cursor.execute(
        """SELECT 
                COALESCE(SUM(CASE WHEN action = 'grade' THEN 1 ELSE 0 END), 0) as grades,
                COALESCE(SUM(CASE WHEN action = 'import' THEN 1 ELSE 0 END), 0) as imports,
                COALESCE(SUM(CASE WHEN action = 'user_create' THEN 1 ELSE 0 END), 0) as users_created,
                COALESCE(SUM(CASE WHEN action = 'user_delete' THEN 1 ELSE 0 END), 0) as users_deleted
           FROM admin_logs LIMIT 1"""
    )
    
    summary = cursor.fetchone() or (0, 0, 0, 0)
    
    return {
        "status": "operational",
        "activity_summary": {
            "total_grades": summary[0],
            "total_imports": summary[1],
            "users_created": summary[2],
            "users_deleted": summary[3]
        },
        "message": "Admin logs retrieved successfully"
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
            # Reset single week
            cursor.execute("DELETE FROM picks WHERE user_id = ? AND week_id = ?", (user_id, week_id))
        else:
            # Reset all picks for user
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
