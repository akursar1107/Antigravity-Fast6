# Cache Strategy & Management

## Overview
Fast6 uses Streamlit's `@st.cache_data` decorator for caching expensive operations like NFL data loading and database queries. This document outlines the caching strategy, TTL rationale, and selective cache invalidation.

## Cache Categories

### 1. NFL Play-by-Play Data (TTL: 300s / 5 minutes)
**Files:** `src/utils/nfl_data.py`, `src/data_processor.py`

**Cached Functions:**
- `load_data(season)` - Loads ~500K rows of play-by-play data
- `get_game_schedule(df, season)` - Extracts game schedule from PBP data
- `get_touchdowns(df)` - Filters all TD plays from PBP data
- `get_first_tds(df)` - Identifies first TD scorer per game
- `load_rosters(season)` - Loads player roster data

**Rationale:** 
- NFL data changes frequently during active game days
- 5-minute TTL balances freshness with API call limits
- Data is immutable for completed games but updates for in-progress games

**Cache Key:** Function arguments (e.g., `season` parameter)

---

### 2. TD Lookup Cache (TTL: 3600s / 1 hour)
**File:** `src/utils/grading_logic.py`

**Cached Functions:**
- `get_td_lookup_cache(season)` - Pre-computed TD lookups indexed by game_id

**Rationale:**
- TD data is immutable once games complete
- 1-hour TTL allows live game updates while reducing memory usage
- Eliminates repeated processing of full season data
- Critical for grading performance (1.9s initial load, instantaneous lookups)

**Cache Key:** `season` parameter

---

### 3. Odds API Data (TTL: 3600s / 1 hour)
**Files:** `src/utils/odds_api.py`, `src/data_processor.py`

**Cached Functions:**
- `get_first_td_odds(api_key, week_start_date, week_end_date)` - Fetches odds from API

**Rationale:**
- API has rate limits (500 requests/month on free tier)
- Odds data doesn't change frequently (typically updates a few times per day)
- 1-hour TTL minimizes API calls while keeping odds reasonably fresh

**Cache Key:** Function arguments (api_key, date range)

---

### 4. Leaderboard & Stats (TTL: 300s / 5 minutes)
**File:** `src/utils/db_stats.py`

**Cached Functions:**
- `get_leaderboard(week_id)` - User standings with points and returns
- `get_user_stats(user_id, week_id)` - Individual user statistics
- `get_weekly_summary(week_id)` - Week summary stats

**Rationale:**
- Database queries are fast but still benefit from caching
- 5-minute TTL ensures reasonable freshness
- **Selective cache clearing** on data modifications ensures immediate updates

**Cache Key:** Function arguments (week_id, user_id)

**Manual Cache Clearing:**
```python
# Clear only leaderboard caches when results change
from utils.db_stats import clear_leaderboard_cache
clear_leaderboard_cache()
```

---

## Selective Cache Clearing Strategy

### ❌ OLD APPROACH (Inefficient)
```python
def add_result(...):
    # ... modify database ...
    st.cache_data.clear()  # Clears ALL caches, including NFL data!
```

**Problems:**
- Clears unrelated caches (NFL data, odds, etc.)
- Forces expensive data reloads
- Slow user experience

### ✅ NEW APPROACH (Targeted)
```python
def clear_leaderboard_cache():
    """Clear only leaderboard-related caches when results are updated."""
    get_leaderboard.clear()
    get_user_stats.clear()
    get_weekly_summary.clear()
```

**Benefits:**
- Only clears caches that depend on the modified data
- NFL data and odds caches remain intact
- Fast cache invalidation with minimal data reloading

---

## When Cache is Cleared

### ✅ Operations That Trigger Cache Clearing

#### 1. Adding/Updating Results (Grades)
- **Function**: `add_result()` in `src/utils/db_stats.py`
- **Trigger**: Grading picks (auto-grade or manual)
- **Clears**: Leaderboard caches only
- **Impact**: Points, wins, returns updated immediately

#### 2. Clearing Grading Results
- **Function**: `clear_grading_results()` in `src/utils/db_stats.py`
- **Trigger**: Admin override to re-grade picks
- **Clears**: Leaderboard caches only
- **Impact**: Results reset, ready for re-grading

#### 3. Importing CSV Picks
- **Function**: `import_picks_from_csv()` in `src/utils/csv_import_clean.py`
- **Trigger**: Admin imports new picks
- **Clears**: Leaderboard caches if picks_imported > 0
- **Impact**: New picks appear in stats

#### 4. Deleting Picks
- **Function**: `delete_pick()` in `src/utils/db_picks.py`
- **Trigger**: Admin removes invalid pick
- **Clears**: Leaderboard caches
- **Impact**: Pick removed from totals

#### 5. Deleting Users
- **Function**: `delete_user()` in `src/utils/db_users.py`
- **Trigger**: Admin removes user (cascades to picks/results)
- **Clears**: Leaderboard caches
- **Impact**: User removed from leaderboard

#### 6. Deduplicating Picks
- **Function**: `dedupe_all_picks()` in `src/utils/db_picks.py`
- **Trigger**: Admin maintenance operation
- **Clears**: Leaderboard caches if duplicates found
- **Impact**: Duplicate picks removed

---

## Cache Testing

### Manual Cache Verification
1. Navigate to leaderboard tab
2. Note current stats
3. Admin grading operation (results page)
4. Verify leaderboard updates within 5 seconds

### Debug Cache Behavior
```python
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Cache cleared: get_leaderboard, get_user_stats, get_weekly_summary")
```

---

## Cache Size & Memory

### Memory Usage Estimates
- **NFL PBP Data (season)**: ~50-80 MB per season in memory
- **TD Lookup Cache**: ~5-10 MB (organized by game_id)
- **Leaderboard Queries**: <1 MB (small result sets)
- **Odds API Data**: <1 MB (small JSON responses)

### Cache Storage
- Streamlit uses in-memory caching (no disk persistence)
- Cache cleared on app restart
- TTL automatically expires old entries

---

## Best Practices

### DO ✅
- Use `@st.cache_data(ttl=X)` for expensive operations
- Set appropriate TTL based on data mutability
- Clear specific caches when modifying related data
- Document cache rationale in comments

### DON'T ❌
- Don't use `st.cache_data.clear()` (clears everything)
- Don't cache mutable objects (use immutable types only)
- Don't set TTL=0 or very low values for expensive operations
- Don't cache database connections (use context managers)

---

## Implementation Details

### Decorator Pattern for Optional Caching
```python
def _cache_if_streamlit(func):
    """Apply caching only in Streamlit context."""
    if HAS_STREAMLIT:
        return st.cache_data(ttl=300)(func)
    return func

@_cache_if_streamlit
def get_leaderboard(week_id):
    # ... query database ...
```

**Benefits:**
- Works in Streamlit app (with caching)
- Works in scripts/tests (without caching)
- Graceful fallback

---

## Future Improvements

### Potential Enhancements
1. **Redis/External Cache**: For multi-process deployments
2. **Cache Warming**: Pre-load common queries on app startup
3. **Cache Metrics**: Track hit rates and performance
4. **Session State**: Complement caching with st.session_state for UI state

---

## References

- Streamlit Caching Docs: https://docs.streamlit.io/develop/concepts/architecture/caching
- Cache Decorator Reference: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data

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
