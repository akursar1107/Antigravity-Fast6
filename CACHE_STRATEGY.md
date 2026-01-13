# Cache Invalidation Strategy

## Overview
When admin users modify data (create, update, delete), the public dashboard must immediately reflect these changes. This document outlines the cache invalidation strategy.

## Cached Data
- **Leaderboard Data**: Cached for 5 minutes via `@_cache_if_streamlit` decorator on `get_leaderboard()`
- **NFL Play-by-Play Data**: Cached for 5 minutes via `load_data()` function
- **Roster Data**: Cached for 5 minutes via `load_rosters()` function

## Cache Clearing Function
Located in `src/utils/db_stats.py`:
```python
def clear_leaderboard_cache():
    """Clear the leaderboard cache in Streamlit."""
    st.cache_data.clear()
```

## When Cache is Cleared

### ✅ Data Modification Operations with Cache Clearing

#### 1. Adding Results (Grades)
- **Function**: `add_result()` in [src/utils/db_stats.py](src/utils/db_stats.py#L52)
- **Trigger**: Whenever a pick is graded with a result (first TD, any-time TD, actual return)
- **Cache Clear**: YES - Called at start of function

#### 2. Clearing Grading Results (Override)
- **Function**: `clear_grading_results()` in [src/utils/db_stats.py](src/utils/db_stats.py#L173)
- **Trigger**: When admin uses "Override Grading (Use Sparingly)" button
- **Cache Clear**: YES - Called at start of function

#### 3. Deleting Picks
- **Function**: `delete_pick()` in [src/utils/db_picks.py](src/utils/db_picks.py#L46)
- **Trigger**: When admin deletes a pick from results tab
- **Cache Clear**: YES - Called after successful deletion
- **Impact**: Pick removed from leaderboard totals

#### 4. Importing CSV Picks
- **Function**: `import_picks_from_csv()` in [src/utils/csv_import_clean.py](src/utils/csv_import_clean.py#L477)
- **Trigger**: When admin imports picks from CSV file
- **Cache Clear**: YES - Called before returning results if picks_imported > 0
- **Impact**: New picks added to leaderboard

#### 5. Deduplicating Picks
- **Function**: `dedupe_all_picks()` in [src/utils/db_picks.py](src/utils/db_picks.py#L265)
- **Trigger**: When admin runs "Deduplicate All Picks" from maintenance tools
- **Cache Clear**: YES - Called after deletion if duplicates found
- **Impact**: Duplicate picks removed, leaderboard totals updated

#### 6. Deleting Users
- **Function**: `delete_user()` in [src/utils/db_users.py](src/utils/db_users.py#L78)
- **Trigger**: When admin deletes a user (cascades to picks and results)
- **Cache Clear**: YES - Called after successful deletion
- **Impact**: User removed from leaderboard

#### 7. Auto-Grading Season
- **Function**: `auto_grade_season()` in [src/utils/grading_logic.py](src/utils/grading_logic.py#L1)
- **Trigger**: When admin uses "Auto-Grade All Picks" button
- **Cache Clear**: YES - Indirectly via `add_result()` calls for each graded pick
- **Impact**: Leaderboard updated with first TD and any-time TD grades

#### 8. Grading Any-Time TD Only
- **Function**: `grade_any_time_td_only()` in [src/utils/grading_logic.py](src/utils/grading_logic.py#L211)
- **Trigger**: When admin uses "Grade Any Time TD Only" button
- **Cache Clear**: YES - Called after grading completes if graded_picks > 0
- **Impact**: Any-time TD stats updated on leaderboard

## Implementation Details

### Pattern: Post-Operation Cache Clearing
```python
def operation_that_modifies_data():
    # ... perform modification ...
    
    if operation_successful:
        from .db_stats import clear_leaderboard_cache
        clear_leaderboard_cache()
```

### Pattern: Conditional Cache Clearing
Some operations clear cache only if data was actually modified:
```python
# Only clear if imports were successful
if result.picks_imported > 0:
    from .db_stats import clear_leaderboard_cache
    clear_leaderboard_cache()
```

## Flow: Admin Update → Public Dashboard Refresh

1. Admin performs operation (e.g., grades picks)
2. Data is modified in SQLite database
3. Cache is cleared via `clear_leaderboard_cache()`
4. Streamlit re-runs the app (via `st.rerun()` button callback)
5. Public dashboard queries fresh leaderboard data
6. User sees updated stats immediately

## Testing Cache Invalidation

When testing admin operations:
1. Note the leaderboard values before admin action
2. Perform admin action (import, grade, delete)
3. Switch to public dashboard
4. Verify leaderboard has updated values
5. No need to wait 5 minutes for cache expiration

## Future Enhancements

- Add optional parameter to cache functions to control clearing behavior
- Implement transaction logging to audit cache clears
- Add cache statistics to admin dashboard (hits/misses)
- Consider Redis for distributed cache in multi-instance deployments
