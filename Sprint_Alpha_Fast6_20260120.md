# Sprint Alpha - Fast6 Optimization & Architectural Improvements
**Project:** Fast6 - NFL First TD Prediction Tool  
**Sprint:** Alpha  
**Created:** January 20, 2026  
**Status:** Planning  

---

## Executive Summary

This sprint focuses on technical debt reduction, performance optimization, and architectural improvements identified during codebase analysis. The work is organized into 4 phases prioritized by impact and effort.

**Expected Outcomes:**
- 10-100x database query performance improvement
- Elimination of 927 lines of deprecated code
- Reduced memory footprint for grading operations
- Improved maintainability and code consistency
- Better error handling and user feedback

---

## 🚀 Phase 1: Critical Technical Debt (Priority: URGENT)
**Timeline:** 1-2 days  
**Effort:** Low  
**Impact:** High  

### Task 1.1: Remove Deprecated database.py
**Problem:** `src/database.py` (927 lines) duplicates all functionality already modularized in `utils/db_*.py` modules. This creates maintenance burden where bug fixes must be applied twice.

**Actions:**
- [ ] Audit all imports of `database.py` across codebase
- [ ] Update any remaining imports to use modular `utils/db_*.py` versions
- [ ] Delete `src/database.py`
- [ ] Verify all tests pass
- [ ] Update any documentation references

**Files Affected:**
- `src/database.py` (DELETE)
- Any files importing from database.py

**Risk:** Low (modular versions are already in use)

---

### Task 1.2: Add Database Indexes
**Problem:** Missing indexes on frequently queried columns causing slow leaderboard and pick lookup operations.

**Actions:**
- [ ] Create migration function in `db_connection.py`
- [ ] Add indexes:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_picks_week_id ON picks(week_id);
  CREATE INDEX IF NOT EXISTS idx_picks_user_id ON picks(user_id);
  CREATE INDEX IF NOT EXISTS idx_picks_game_id ON picks(game_id);
  CREATE INDEX IF NOT EXISTS idx_results_pick_id ON results(pick_id);
  CREATE INDEX IF NOT EXISTS idx_weeks_season_week ON weeks(season, week);
  ```
- [ ] Call index creation during app startup
- [ ] Test query performance improvements
- [ ] Document index strategy in CACHE_STRATEGY.md

**Files Affected:**
- `src/utils/db_connection.py` (add migration function)
- `src/app.py` (call migration on startup)

**Expected Impact:** 10-100x faster queries on leaderboard and picks

---

### Task 1.3: Implement Context Manager Pattern
**Problem:** 100+ instances of manual connection management with try-finally blocks. Risk of connection leaks and no transaction management.

**Actions:**
- [ ] Refactor all `db_users.py` functions to use `get_db_context()`
- [ ] Refactor all `db_picks.py` functions to use `get_db_context()`
- [ ] Refactor all `db_weeks.py` functions to use `get_db_context()`
- [ ] Refactor all `db_stats.py` functions to use `get_db_context()`
- [ ] Remove all manual `conn = get_db_connection()` / `conn.close()` patterns
- [ ] Test all database operations
- [ ] Verify proper error handling and rollback behavior

**Pattern Change:**
```python
# FROM:
def add_user(name: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT...")
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

# TO:
def add_user(name: str) -> int:
    with get_db_context() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT...")
        return cursor.lastrowid
```

**Files Affected:**
- `src/utils/db_users.py`
- `src/utils/db_picks.py`
- `src/utils/db_weeks.py`
- `src/utils/db_stats.py`
- Any other files with direct DB access

**Expected Impact:** 
- Cleaner code (200+ lines saved)
- Automatic transaction management
- Reduced risk of connection leaks

---

## 🔧 Phase 2: Performance Optimizations (Priority: HIGH)
**Timeline:** 2-3 days  
**Effort:** Medium  
**Impact:** High  

### Task 2.1: Optimize Grading Logic
**Problem:** `grading_logic.py` loads entire season play-by-play data into memory for every grading operation, even when grading a single pick.

**Current Inefficiency:**
```python
def auto_grade_season(season: int, week: Optional[int] = None):
    df = load_data(season)  # Loads ALL season PBP data (~500K rows)
    first_tds = get_first_tds(df)  # Processes entire dataset
    all_tds = get_touchdowns(df)
    # Then grades picks one by one
```

**Actions:**
- [ ] Create `TDLookupCache` class in `grading_logic.py`
- [ ] Pre-compute first TD lookup table by game_id
- [ ] Cache TD data per season with 1-hour TTL
- [ ] Modify `auto_grade_season()` to use cached lookups
- [ ] Add cache invalidation for when new PBP data arrives
- [ ] Test memory usage before/after
- [ ] Benchmark grading performance improvement

**Implementation:**
```python
@dataclass
class TDLookupCache:
    first_tds_by_game: Dict[str, pd.DataFrame]
    all_tds_by_game: Dict[str, pd.DataFrame]
    season: int
    cached_at: datetime

@st.cache_data(ttl=3600)
def get_td_lookups(season: int) -> TDLookupCache:
    # Build lookup tables once per hour
    pass
```

**Files Affected:**
- `src/utils/grading_logic.py`

**Expected Impact:** 
- 50-80% reduction in memory usage
- 5-10x faster grading operations
- Better scalability for multi-week grading

---

### Task 2.2: Fix Cache Inconsistency
**Problem:** Multiple cache TTLs without clear strategy. Leaderboard can show stale data for 5 minutes after grading. `clear_leaderboard_cache()` clears ALL Streamlit caches indiscriminately.

**Actions:**
- [ ] Audit all `@st.cache_data` decorators and document TTL rationale
- [ ] Implement selective cache clearing by function name
- [ ] Replace `st.cache_data.clear()` with targeted clearing
- [ ] Add cache strategy documentation to CACHE_STRATEGY.md
- [ ] Test cache invalidation after grading operations
- [ ] Consider adding manual "Refresh Data" buttons where appropriate

**Cache Strategy:**
```python
# NFL Data: 5 min (changes frequently during games)
@st.cache_data(ttl=300)

# Odds API: 1 hour (rate limit consideration)
@st.cache_data(ttl=3600)

# Leaderboard: No TTL (clear on write operations)
@st.cache_data
def get_leaderboard_data(...):
    pass

# Clear specific cache:
get_leaderboard_data.clear()  # Not st.cache_data.clear()
```

**Files Affected:**
- `src/utils/nfl_data.py`
- `src/utils/odds_api.py`
- `src/utils/db_stats.py`
- `src/utils/grading_logic.py`
- `CACHE_STRATEGY.md`

**Expected Impact:** Real-time data consistency after updates

---

### Task 2.3: Streamlit Session State Management
**Problem:** No use of `st.session_state` for UI state persistence. Every rerun reloads data from scratch unnecessarily.

**Actions:**
- [ ] Add session state for selected season/week in all tabs
- [ ] Cache filter selections (team, user, etc.)
- [ ] Persist form inputs across reruns
- [ ] Add session state initialization in `app.py`
- [ ] Test state persistence across tab navigation
- [ ] Document session state usage in code comments

**Implementation:**
```python
# In app.py or tab files
if 'selected_season' not in st.session_state:
    st.session_state.selected_season = config.CURRENT_SEASON

if 'selected_week' not in st.session_state:
    st.session_state.selected_week = config.CURRENT_WEEK
```

**Files Affected:**
- `src/app.py`
- `src/views/tabs/*.py`
- `src/views/admin/*.py`

**Expected Impact:** Improved UX, fewer unnecessary data reloads

---

## 🏗️ Phase 3: Architectural Improvements (Priority: MEDIUM)
**Timeline:** 3-4 days  
**Effort:** High  
**Impact:** Medium (Long-term maintainability)  

### Task 3.1: Implement Database Migrations System
**Problem:** Ad-hoc schema changes through `ensure_*_column()` functions are not versioned or tracked.

**Actions:**
- [ ] Create `migrations.py` module in `utils/`
- [ ] Add `schema_version` table to database
- [ ] Create migration registry with version tracking
- [ ] Convert existing migrations to versioned format:
  - v1: Initial schema
  - v2: Add game_id columns
  - v3: Add any_time_td columns
- [ ] Implement `run_migrations()` function
- [ ] Call migrations on app startup before any DB operations
- [ ] Document migration creation process

**Implementation:**
```python
# src/utils/migrations.py
MIGRATIONS = {
    1: initial_schema,
    2: add_game_id_columns,
    3: add_any_time_td_columns,
}

def get_current_version() -> int:
    # Query metadata table
    pass

def run_migrations():
    current = get_current_version()
    for version in sorted(MIGRATIONS.keys()):
        if version > current:
            MIGRATIONS[version]()
            update_version(version)
```

**Files Affected:**
- `src/utils/migrations.py` (NEW)
- `src/utils/db_connection.py` (remove ad-hoc migrations)
- `src/app.py` (call migrations)

**Expected Impact:** Safer schema evolution, rollback capability

---

### Task 3.2: Improve Error Handling & User Feedback
**Problem:** Most functions log errors but don't provide user-friendly messages. Users see generic errors or nothing at all.

**Actions:**
- [ ] Create custom exception types in `utils/exceptions.py`
- [ ] Add user-friendly error messages for common failures
- [ ] Implement try-except blocks at view layer
- [ ] Add Streamlit error/warning/success messages
- [ ] Add loading spinners for slow operations
- [ ] Log exceptions with full context for debugging
- [ ] Test error scenarios (DB locked, API timeout, invalid data)

**Implementation:**
```python
# src/utils/exceptions.py
class PickValidationError(Exception):
    """User-friendly error for invalid picks"""

class DataNotFoundError(Exception):
    """Expected data missing from NFL API"""

class GradingError(Exception):
    """Error during pick grading process"""

# In views:
try:
    result = grade_picks(season, week)
    st.success(f"Graded {result.count} picks successfully!")
except GradingError as e:
    st.error(f"Grading failed: {e}")
    logger.exception("Grading error details")
```

**Files Affected:**
- `src/utils/exceptions.py` (NEW)
- All view files in `src/views/admin/*.py`
- All tab files in `src/views/tabs/*.py`
- `src/utils/grading_logic.py`

**Expected Impact:** Better UX, easier debugging

---

### Task 3.3: Config Loading Optimization
**Problem:** Config loaded at module import time AND accessed throughout app. Scoring constants duplicated in `db_stats.py`.

**Actions:**
- [ ] Evaluate if config singleton pattern is needed
- [ ] Remove duplicate scoring constants in `db_stats.py`
- [ ] Access scoring values directly from `config` module
- [ ] Consider lazy loading for large config sections
- [ ] Document config access patterns in CONFIG_GUIDE.md
- [ ] Test config reloading (if needed for future features)

**Files Affected:**
- `src/config.py`
- `src/utils/db_stats.py`
- `CONFIG_GUIDE.md`

**Expected Impact:** Reduced code duplication, single source of truth

---

## 🎯 Phase 4: Advanced Enhancements (Priority: LOW)
**Timeline:** 4-5 days  
**Effort:** High  
**Impact:** Low (Future-proofing)  

### Task 4.1: Data Access Layer (DAL) Pattern
**Problem:** Database access scattered across multiple utility modules. No clear separation between data access and business logic.

**Actions:**
- [ ] Design repository interfaces for each entity
- [ ] Create `repositories/` directory
- [ ] Implement `UsersRepository`, `PicksRepository`, `WeeksRepository`, etc.
- [ ] Refactor existing utility functions to use repositories
- [ ] Add dependency injection for testability
- [ ] Update tests to use mock repositories
- [ ] Document repository pattern in PROJECT.md

**Implementation:**
```python
# src/repositories/picks_repository.py
class PicksRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
    
    def add_pick(self, user_id: int, week_id: int, ...) -> int:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO picks...")
        return cursor.lastrowid
    
    def get_ungraded_picks(self, season: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT...")
        return [dict(row) for row in cursor.fetchall()]
```

**Files Affected:**
- `src/repositories/*.py` (NEW)
- All view files (use repositories instead of direct DB utils)
- Test files

**Expected Impact:** 
- Better testability
- Clearer separation of concerns
- Easier to swap data stores in future

---

### Task 4.2: Separate Business Logic from Data Access
**Problem:** `grading_logic.py` mixes data loading, business logic, and database writes. Difficult to test and modify independently.

**Actions:**
- [ ] Create `services/` directory
- [ ] Implement `GradingService` class with pure business logic
- [ ] Implement `NFLDataService` for external API interactions
- [ ] Extract business rules from grading_logic.py
- [ ] Use repositories for data access in services
- [ ] Update admin grading page to use services
- [ ] Add unit tests for business logic

**Implementation:**
```python
# src/services/grading_service.py
class GradingService:
    def __init__(self, picks_repo: PicksRepository, 
                 nfl_data: NFLDataService):
        self.picks = picks_repo
        self.nfl_data = nfl_data
    
    def grade_pick(self, pick: Pick) -> GradeResult:
        # Pure business logic - no DB or API calls
        first_tds = self.nfl_data.get_first_tds(pick.game_id)
        is_correct = self.check_if_correct(pick, first_tds)
        return GradeResult(is_correct=is_correct, ...)
```

**Files Affected:**
- `src/services/*.py` (NEW)
- `src/utils/grading_logic.py` (refactor)
- `src/views/admin/grading.py` (use service)

**Expected Impact:** 
- Testable business logic
- Clearer code organization
- Easier to extend grading rules

---

### Task 4.3: Enhanced Type Safety
**Problem:** Partial type hints across codebase. Using dicts for complex objects makes IDE support limited.

**Actions:**
- [ ] Add type hints to all function signatures
- [ ] Create dataclass models for Pick, User, Week, Result entities
- [ ] Replace dict returns with typed objects
- [ ] Enable mypy in CI/CD (future)
- [ ] Document type conventions in PROJECT.md
- [ ] Use Pydantic for validation if needed

**Implementation:**
```python
# src/models/pick.py
@dataclass
class Pick:
    id: Optional[int]
    user_id: int
    week_id: int
    game_id: str
    player_name: str
    odds: Optional[float]
    theoretical_return: Optional[float]
    created_at: Optional[datetime]

@dataclass
class GradeResult:
    pick_id: int
    is_correct: bool
    any_time_td: bool
    actual_return: float
    points_earned: int
```

**Files Affected:**
- `src/models/*.py` (NEW)
- All modules (add type hints)

**Expected Impact:** 
- Better IDE autocomplete
- Catch errors at development time
- Self-documenting code

---

## 📊 Success Metrics

### Performance
- [ ] Database query time reduced by >10x (measure leaderboard load time)
- [ ] Grading operation memory usage reduced by >50%
- [ ] Grading time for full season reduced by >5x
- [ ] Page load times <2 seconds for all views

### Code Quality
- [ ] 927 lines of deprecated code removed
- [ ] 100+ manual connection management blocks replaced
- [ ] All database operations using context managers
- [ ] Zero connection leak issues

### Maintainability
- [ ] Database schema versioned and tracked
- [ ] Clear separation of concerns (data/business/presentation)
- [ ] Comprehensive error handling with user feedback
- [ ] Type hints on all public functions

---

## 🎯 Implementation Order

**Week 1 (Phase 1):**
- Day 1-2: Task 1.1 (Remove database.py) + Task 1.2 (Add indexes)
- Day 3-5: Task 1.3 (Context managers across all modules)

**Week 2 (Phase 2):**
- Day 1-2: Task 2.1 (Optimize grading logic)
- Day 3-4: Task 2.2 (Fix cache inconsistency)
- Day 5: Task 2.3 (Session state management)

**Week 3 (Phase 3):**
- Day 1-2: Task 3.1 (Migration system)
- Day 3-4: Task 3.2 (Error handling)
- Day 5: Task 3.3 (Config optimization)

**Week 4 (Phase 4 - Optional):**
- Day 1-2: Task 4.1 (DAL pattern)
- Day 3-4: Task 4.2 (Separate business logic)
- Day 5: Task 4.3 (Type safety)

---

## 🚨 Risks & Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation:** 
- Test after each task completion
- Keep git commits small and atomic
- Have rollback plan for each change

### Risk 2: Database Migration Failures
**Mitigation:**
- Backup database before migrations
- Test migrations on copy of production DB
- Keep old migration functions as fallback

### Risk 3: Performance Regressions
**Mitigation:**
- Benchmark before changes
- Profile after changes
- Keep monitoring in place

### Risk 4: Over-engineering
**Mitigation:**
- Phase 4 is optional - only do if needed
- Focus on Phase 1-2 for immediate value
- Re-evaluate priorities after Phase 2

---

## 📝 Notes

- **Phase 1 is CRITICAL** - High impact, low effort
- **Phase 2 provides tangible UX improvements** - Users will notice
- **Phase 3 is debt reduction** - Makes future work easier
- **Phase 4 is optional** - Only if scaling beyond friend group

**Current Status:** Fast6 is in excellent shape for Phase 3 completion. These optimizations will make it production-grade and prepare for Phase 4+ features.

---

## 🔗 Related Documents
- [PROJECT.md](PROJECT.md) - Overall project documentation
- [ROADMAP.md](ROADMAP.md) - Feature roadmap
- [REFACTORING.md](REFACTORING.md) - Phase 3 refactoring notes
- [CACHE_STRATEGY.md](CACHE_STRATEGY.md) - Caching strategy
- [CONFIG_GUIDE.md](CONFIG_GUIDE.md) - Configuration system
