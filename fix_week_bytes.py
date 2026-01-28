"""
Fix bytes-stored week numbers in the database
"""

import sqlite3
import sys
sys.path.insert(0, 'src')

from database import get_db_context

def fix_week_bytes():
    """Convert byte-stored week numbers to proper integers and merge duplicates"""
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Get all weeks
        cursor.execute("SELECT id, week, season FROM weeks")
        weeks = cursor.fetchall()
        
        print(f"Found {len(weeks)} week records")
        
        # Find byte-stored weeks
        byte_weeks = []
        for week_id, week_val, season in weeks:
            if isinstance(week_val, bytes):
                week_int = int.from_bytes(week_val, 'little')
                byte_weeks.append((week_id, week_val, week_int, season))
                print(f"  Found byte week: ID={week_id}, Season={season}, Week={week_val} → {week_int}")
        
        if not byte_weeks:
            print("No byte-stored weeks found!")
            return
        
        # For each byte week, check if an integer version exists
        merged_count = 0
        deleted_count = 0
        
        for byte_week_id, byte_val, week_int, season in byte_weeks:
            # Find the integer version
            cursor.execute(
                "SELECT id FROM weeks WHERE season = ? AND week = ? AND typeof(week) = 'integer'",
                (season, week_int)
            )
            int_week = cursor.fetchone()
            
            if int_week:
                int_week_id = int_week[0]
                print(f"\n  Merging: Byte week ID={byte_week_id} → Integer week ID={int_week_id} (Season {season}, Week {week_int})")
                
                # Update all picks pointing to byte week to point to integer week
                cursor.execute(
                    "UPDATE picks SET week_id = ? WHERE week_id = ?",
                    (int_week_id, byte_week_id)
                )
                affected = cursor.rowcount
                print(f"    Moved {affected} picks")
                
                # Delete the byte week record
                cursor.execute("DELETE FROM weeks WHERE id = ?", (byte_week_id,))
                deleted_count += 1
                merged_count += 1
            else:
                # No integer version exists, just update this one
                print(f"\n  Converting: ID={byte_week_id}, Season={season}, Week {byte_val} → {week_int}")
                cursor.execute(
                    "UPDATE weeks SET week = ? WHERE id = ?",
                    (week_int, byte_week_id)
                )
        
        conn.commit()
        
        print(f"\n✅ Merged and deleted {merged_count} duplicate week records")
        
        # Verify
        cursor.execute("SELECT id, week, season, typeof(week) FROM weeks ORDER BY season, week")
        all_weeks = cursor.fetchall()
        print(f"\n✅ Final week count: {len(all_weeks)}")
        print("\nSample:")
        for week_id, week_val, season, week_type in all_weeks[:10]:
            print(f"  ID={week_id}, Season={season}, Week={week_val}, Type={week_type}")

if __name__ == "__main__":
    print("=== Fixing byte-stored week numbers ===\n")
    fix_week_bytes()
    print("\n=== Complete! ===")
