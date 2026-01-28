# 🏗️ Architecture & Refactoring Improvement Plan
*Analysis Date: January 27, 2026*

## 📊 Current State Analysis

### Codebase Statistics:
- **Total Python files:** 53 files
- **Utils folder:** 24 files (5,282 lines) ⚠️ **TOO BIG**
- **Services folder:** 6 files (2,297 lines) ✅ Good
- **Views folder:** 21 files ✅ Organized
- **Database files:** 6 files (1,246 lines) ⚠️ Fragmented

---

## 🎯 Identified Issues & Opportunities

### 🔴 CRITICAL: Utils Folder is Bloated (24 files!)

**Problem:** The `src/utils/` folder has become a dumping ground for miscellaneous code.

**Current Structure:**
```
src/utils/
├── analytics.py
├── common.py
├── csv_import_clean.py
├── csv_import.py
├── db_connection.py      ← Database layer (1,246 lines across 6 files)
├── db_kickoff.py
├── db_picks.py           ← 394 lines
├── db_stats.py           ← 472 lines
├── db_users.py
├── db_weeks.py
├── exceptions.py
├── exports.py
├── first_drive_success.py
├── grading_logic.py
├── migrations.py
├── name_matching.py
├── nfl_data.py
├── odds_api.py
├── odds_utils.py
├── opening_drive_analytics.py
├── team_utils.py
├── theming.py
└── type_utils.py
```

**Issues:**
1. **Database layer fragmented** - 6 separate db_*.py files
2. **Unclear organization** - Mix of database, analytics, utilities, APIs
3. **Large files** - db_stats.py (472 lines), db_picks.py (394 lines)
4. **No clear ownership** - Everything is "utils"

---

### 🟡 MODERATE: Database Layer Needs Consolidation

**Current Pattern:**
- 6 separate files: `db_connection.py`, `db_picks.py`, `db_stats.py`, `db_users.py`, `db_weeks.py`, `db_kickoff.py`
- Each file creates its own connection
- No clear repository pattern
- 1,246 lines of database code scattered

**Issues:**
```python
# Every db_*.py file does this:
from utils.db_connection import get_db_connection

def add_user(...):
    conn = get_db_connection()  # New connection
    cursor = conn.cursor()
    # ... operations ...
    conn.close()
    
def get_user(...):
    conn = get_db_connection()  # Another new connection
    cursor = conn.cursor()
    # ... operations ...
    conn.close()
```

**Problem:** No connection pooling, repetitive code, hard to maintain.

---

### 🟡 MODERATE: Analytics Code Split Between Utils & Services

**Current State:**
- `src/utils/analytics.py` - Basic analytics functions
- `src/utils/opening_drive_analytics.py` - Opening drive specific
- `src/utils/first_drive_success.py` - First drive specific
- `src/services/` - Phase 5 analytics (Player, ROI, ELO, Defense)

**Issue:** No clear separation - some analytics in utils, some in services.

---

### 🟢 MINOR: Import Inconsistencies

**Current:**
```python
# In some files:
from utils.db_connection import get_db_connection

# In others:
from utils import get_db_connection

# In __init__.py:
try:
    from utils.nfl_data import load_data
except ImportError:
    pass  # Why are we catching ImportError?
```

**Issue:** Mixed import styles, unnecessary try/except blocks.

---

### 🟢 MINOR: No Data Models / DTOs

**Current:**
```python
# Everywhere uses dicts and tuples
def add_pick(user_id: int, week_id: int, team: str, player_name: str, ...):
    return pick_id  # Returns int

def get_pick(pick_id: int) -> Optional[Dict]:
    return row_dict  # Returns dict
    
# No type safety, no validation
```

**Issue:** No structured data models, hard to track what fields exist.

---

## 🏗️ Recommended Architecture

### Option A: Full Restructure (Recommended)

```
src/
├── models/                     ← NEW: Data models
│   ├── __init__.py
│   ├── user.py                (User, UserStats)
│   ├── pick.py                (Pick, PickResult)
│   ├── week.py                (Week, Season)
│   └── analytics.py           (PlayerStats, TeamRating, etc.)
│
├── repositories/               ← NEW: Database access layer
│   ├── __init__.py
│   ├── base.py                (BaseRepository with connection pooling)
│   ├── user_repository.py
│   ├── pick_repository.py
│   ├── stats_repository.py
│   └── week_repository.py
│
├── services/                   ← EXISTING: Business logic
│   ├── __init__.py
│   ├── analytics/             ← NEW: Group analytics services
│   │   ├── player_stats_service.py
│   │   ├── roi_trends_service.py
│   │   ├── elo_rating_service.py
│   │   └── defense_analysis_service.py
│   ├── grading_service.py     ← MOVE from utils
│   ├── import_service.py      ← MOVE from utils
│   └── performance_service.py
│
├── integrations/               ← NEW: External APIs
│   ├── __init__.py
│   ├── nfl_data.py            ← MOVE from utils
│   └── odds_api.py            ← MOVE from utils
│
├── utils/                      ← REFACTORED: Only utilities
│   ├── __init__.py
│   ├── name_matching.py       (Keep - pure utility)
│   ├── type_utils.py          (Keep - pure utility)
│   ├── odds_utils.py          (Keep - calculations)
│   ├── common.py              (Keep - formatters)
│   ├── exceptions.py          (Keep - custom exceptions)
│   └── theming.py             (Keep - UI utilities)
│
├── database/                   ← NEW: Database management
│   ├── __init__.py
│   ├── connection.py          ← MOVE from utils
│   ├── migrations.py          ← MOVE from utils
│   └── schema.sql             ← NEW: SQL schema definition
│
├── views/                      ← EXISTING: UI components
│   ├── tabs/                  (Already clean!)
│   ├── admin/
│   ├── admin_page.py
│   └── public_dashboard.py
│
├── config.py
└── app.py
```

---

### Option B: Minimal Refactor (Faster)

Just consolidate the most problematic areas:

```
src/
├── database/                   ← NEW: Consolidate all db_* files
│   ├── __init__.py
│   ├── connection.py
│   ├── migrations.py
│   ├── users.py
│   ├── picks.py
│   ├── stats.py
│   └── weeks.py
│
├── services/
│   ├── analytics/             ← NEW: Group analytics
│   │   ├── player_stats_service.py
│   │   ├── roi_trends_service.py
│   │   ├── elo_rating_service.py
│   │   └── defense_analysis_service.py
│   ├── grading_service.py     ← MOVE grading_logic.py here
│   └── nfl_service.py         ← MOVE nfl_data.py here
│
├── utils/                      ← SLIM DOWN (10 files instead of 24)
│   [Keep only pure utilities]
│
└── [rest stays same]
```

---

## 📋 Detailed Refactoring Plan

### Phase 1: Database Layer Consolidation (HIGH PRIORITY)

**Goal:** Move all `db_*.py` files to a proper `database/` folder with repository pattern.

**Steps:**

#### 1.1 Create Database Package
```bash
mkdir src/database
```

#### 1.2 Move and Rename Files
```bash
mv src/utils/db_connection.py src/database/connection.py
mv src/utils/migrations.py src/database/migrations.py
mv src/utils/db_users.py src/database/user_repository.py
mv src/utils/db_picks.py src/database/pick_repository.py
mv src/utils/db_stats.py src/database/stats_repository.py
mv src/utils/db_weeks.py src/database/week_repository.py
mv src/utils/db_kickoff.py src/database/kickoff_repository.py
```

#### 1.3 Create Base Repository (NEW FILE)

**`src/database/base_repository.py`:**
```python
"""Base repository with shared database operations."""
from contextlib import contextmanager
from typing import Generator
import sqlite3

class BaseRepository:
    """Base class for all repositories."""
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get database connection with auto-commit/rollback."""
        from .connection import get_db_connection
        
        conn = get_db_connection()
        try:
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> list:
        """Execute SELECT query and return results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_write(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid or cursor.rowcount
```

**Benefits:**
- ✅ Centralized connection management
- ✅ Consistent error handling
- ✅ Easier to add connection pooling later
- ✅ DRY - no repeated connection code

---

### Phase 2: Create Data Models (MEDIUM PRIORITY)

**Goal:** Add type safety with dataclasses.

**`src/models/pick.py`:**
```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Pick:
    """Represents a user's touchdown prediction."""
    id: Optional[int] = None
    user_id: int = 0
    week_id: int = 0
    team: str = ""
    player_name: str = ""
    odds: Optional[float] = None
    theoretical_return: Optional[float] = None
    game_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database operations."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'week_id': self.week_id,
            'team': self.team,
            'player_name': self.player_name,
            'odds': self.odds,
            'theoretical_return': self.theoretical_return,
            'game_id': self.game_id
        }
    
    @classmethod
    def from_row(cls, row: dict) -> 'Pick':
        """Create Pick from database row."""
        return cls(
            id=row.get('id'),
            user_id=row.get('user_id'),
            week_id=row.get('week_id'),
            team=row.get('team'),
            player_name=row.get('player_name'),
            odds=row.get('odds'),
            theoretical_return=row.get('theoretical_return'),
            game_id=row.get('game_id'),
            created_at=row.get('created_at')
        )

@dataclass
class PickResult:
    """Represents the result of a pick."""
    id: Optional[int] = None
    pick_id: int = 0
    actual_scorer: Optional[str] = None
    is_correct: Optional[bool] = None
    actual_return: Optional[float] = None
    any_time_td: Optional[bool] = None
    created_at: Optional[datetime] = None
```

**Benefits:**
- ✅ Type safety (IDE autocomplete)
- ✅ Validation at object creation
- ✅ Clear structure (no more wondering what fields exist)
- ✅ Easier testing

---

### Phase 3: Reorganize Services (MEDIUM PRIORITY)

**Goal:** Group related services, move logic from utils.

**Current:**
```
src/services/
├── defense_analysis_service.py
├── elo_rating_service.py
├── performance_service.py
├── player_stats_service.py
└── roi_trends_service.py
```

**Proposed:**
```
src/services/
├── analytics/                  ← GROUP Phase 5 analytics
│   ├── __init__.py
│   ├── player_stats.py
│   ├── roi_trends.py
│   ├── elo_ratings.py
│   └── defense_analysis.py
├── grading.py                  ← MOVE from utils/grading_logic.py
├── import_export.py            ← MOVE from utils/csv_import*.py & exports.py
├── nfl_data.py                 ← MOVE from utils/nfl_data.py
└── performance.py              ← EXISTING
```

---

### Phase 4: Slim Down Utils (HIGH PRIORITY)

**Goal:** Only keep pure utility functions in utils.

**Files to KEEP in utils/ (10 files):**
- ✅ `common.py` - Formatters, session state
- ✅ `type_utils.py` - Safe type conversions
- ✅ `odds_utils.py` - Odds calculations
- ✅ `name_matching.py` - Player name matching
- ✅ `team_utils.py` - Team abbreviation mapping
- ✅ `theming.py` - UI theming
- ✅ `exceptions.py` - Custom exceptions
- ✅ `__init__.py` - Package exports

**Files to MOVE OUT (14 files):**
- ❌ All `db_*.py` files → `src/database/`
- ❌ `migrations.py` → `src/database/`
- ❌ `grading_logic.py` → `src/services/grading.py`
- ❌ `analytics.py` → `src/services/analytics/`
- ❌ `opening_drive_analytics.py` → `src/services/analytics/`
- ❌ `first_drive_success.py` → `src/services/analytics/`
- ❌ `nfl_data.py` → `src/integrations/nfl_data.py`
- ❌ `odds_api.py` → `src/integrations/odds_api.py`
- ❌ `csv_import*.py` → `src/services/import_export.py`
- ❌ `exports.py` → `src/services/import_export.py`

**Result:** Utils goes from 24 files → 8-10 files

---

### Phase 5: Add Integration Layer (LOW PRIORITY)

**Goal:** Separate external API calls from business logic.

**`src/integrations/`:**
```
integrations/
├── __init__.py
├── nfl_data.py        (nflreadpy wrapper)
└── odds_api.py        (odds API wrapper)
```

**Benefits:**
- ✅ Clear boundary for external dependencies
- ✅ Easier to mock for testing
- ✅ Can add rate limiting, caching, retry logic
- ✅ Swap implementations without changing business logic

---

## 📊 Impact Analysis

### Current Structure Issues:

| Issue | Severity | Impact | Files Affected |
|-------|----------|--------|----------------|
| **Utils folder bloat** | 🔴 High | Hard to find code | 24 files |
| **Fragmented database layer** | 🔴 High | Repetitive code | 6 files |
| **No data models** | 🟡 Medium | Type safety | All files |
| **Analytics split** | 🟡 Medium | Unclear organization | 8 files |
| **Import inconsistencies** | 🟢 Low | Minor confusion | Many files |

---

### Proposed Structure Benefits:

#### Developer Experience:
- ✅ **Clear organization** - Know where code belongs
- ✅ **Faster navigation** - Logical folder structure
- ✅ **Easier onboarding** - Self-documenting architecture
- ✅ **Less cognitive load** - Similar files grouped together

#### Code Quality:
- ✅ **DRY** - Eliminate repeated database connection code
- ✅ **Type safety** - Data models with validation
- ✅ **Testability** - Easier to mock repositories
- ✅ **Maintainability** - Changes isolated to specific modules

#### Performance:
- ✅ **Connection pooling** - Can add to BaseRepository
- ✅ **Caching** - Centralized in repositories
- ✅ **Query optimization** - All SQL in one place

---

## 🎯 Recommended Implementation Order

### Option A: Full Refactor (2-3 days)
**Best for long-term project health.**

1. **Day 1 Morning:** Create new folders, move database layer
2. **Day 1 Afternoon:** Create data models (Pick, User, Week)
3. **Day 2 Morning:** Reorganize services, move analytics
4. **Day 2 Afternoon:** Slim down utils, create integrations folder
5. **Day 3:** Update all imports, test everything, fix issues

**Effort:** 16-20 hours  
**Benefit:** Major architecture improvement  
**Risk:** Medium (many import changes)

---

### Option B: Incremental Refactor (3-5 days, safer)
**Best for minimizing risk.**

**Week 1: Database Layer**
- Create `src/database/` folder
- Move all `db_*.py` files
- Create BaseRepository
- Update imports
- Test

**Week 2: Services**
- Create `src/services/analytics/` subfolder
- Move analytics from utils
- Move grading logic
- Update imports
- Test

**Week 3: Clean Up**
- Slim down utils
- Create integrations folder
- Add data models (optional)
- Final cleanup

**Effort:** 20-30 hours total  
**Benefit:** Same as Option A  
**Risk:** LOW (incremental, can roll back each step)

---

### Option C: Minimal Refactor (1 day)
**Just fix the biggest pain points.**

**Priority 1: Database consolidation**
- Move `db_*.py` to `src/database/`
- Update imports
- Done!

**Priority 2: Utils cleanup**
- Move 5-6 biggest files out of utils
- Leave the rest for later

**Effort:** 4-6 hours  
**Benefit:** Addresses 70% of issues  
**Risk:** VERY LOW

---

## 🚀 Quick Wins (Do These Now)

### 1. Create Database Package (30 minutes)
```bash
mkdir src/database
mv src/utils/db_*.py src/database/
mv src/utils/migrations.py src/database/
```

### 2. Group Analytics Services (15 minutes)
```bash
mkdir src/services/analytics
mv src/services/*_service.py src/services/analytics/
# (Keep performance_service.py in services/)
```

### 3. Update Imports (20 minutes)
Use find/replace:
- `from utils.db_` → `from database.`
- `from services.player_stats_service` → `from services.analytics.player_stats`

**Total Time:** 1 hour  
**Impact:** Much cleaner structure immediately!

---

## 📝 Additional Improvements

### 1. Add Connection Pooling
**File:** `src/database/connection.py`

```python
from sqlite3 import Connection
from queue import Queue
from contextlib import contextmanager

class ConnectionPool:
    def __init__(self, max_connections: int = 5):
        self.pool = Queue(maxsize=max_connections)
        for _ in range(max_connections):
            self.pool.put(self._create_connection())
    
    def _create_connection(self) -> Connection:
        # ... create connection ...
        
    @contextmanager
    def get_connection(self):
        conn = self.pool.get()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.put(conn)

# Global pool instance
_pool = None

def get_pooled_connection():
    global _pool
    if _pool is None:
        _pool = ConnectionPool()
    return _pool.get_connection()
```

---

### 2. Add Environment-Based Configuration
**File:** `src/config.py`

```python
import os
from pathlib import Path

class Config:
    # Environment
    ENV = os.getenv('ENV', 'development')
    DEBUG = ENV == 'development'
    
    # Database
    DB_PATH = Path(os.getenv('DB_PATH', 'data/fast6.db'))
    
    # Caching
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))  # 5 minutes
    
    # NFL Data
    NFL_DATA_CACHE_DAYS = int(os.getenv('NFL_DATA_CACHE_DAYS', '1'))
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables."""
        return cls()

config = Config()
```

---

### 3. Add Proper Logging
**File:** `src/utils/logging.py` (NEW)

```python
import logging
import sys
from pathlib import Path

def setup_logging(level: str = 'INFO'):
    """Configure application logging."""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_dir / 'fast6.log')
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger
```

---

### 4. Add Integration Tests
**File:** `tests/integration/test_database_layer.py` (NEW)

```python
import pytest
from database.user_repository import UserRepository
from database.pick_repository import PickRepository
from models.user import User
from models.pick import Pick

class TestDatabaseIntegration:
    
    @pytest.fixture
    def user_repo(self):
        return UserRepository()
    
    @pytest.fixture
    def pick_repo(self):
        return PickRepository()
    
    def test_create_user_and_pick(self, user_repo, pick_repo):
        """Test creating a user and their pick."""
        # Create user
        user = User(name="Test User", email="test@test.com")
        user_id = user_repo.create(user)
        assert user_id > 0
        
        # Create pick
        pick = Pick(
            user_id=user_id,
            week_id=1,
            team="KC",
            player_name="Patrick Mahomes"
        )
        pick_id = pick_repo.create(pick)
        assert pick_id > 0
        
        # Verify
        saved_pick = pick_repo.get_by_id(pick_id)
        assert saved_pick.user_id == user_id
```

---

## 🎯 Final Recommendation

**I recommend Option B: Incremental Refactor**

**Why:**
1. **Low risk** - Make changes gradually
2. **Testable** - Verify each step works
3. **Reversible** - Can roll back if issues
4. **Complete** - Addresses all major issues
5. **Sustainable** - Sets up for future growth

**Start with these 3 quick wins (1 hour):**
1. Move `db_*.py` to `src/database/`
2. Create `src/services/analytics/` subfolder
3. Update imports

**Then continue incrementally over the next few weeks.**

---

## 📊 Success Metrics

### After Refactoring:

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| **Utils files** | 24 | 8-10 | ✅ 60% reduction |
| **Database files location** | Scattered in utils | Organized in database/ | ✅ Centralized |
| **Import clarity** | Mixed patterns | Consistent | ✅ Clear |
| **Type safety** | None (dicts) | Data models | ✅ Improved |
| **Code duplication** | High (connection code) | Low (BaseRepository) | ✅ DRY |
| **Developer onboarding time** | 2-3 days | 1 day | ✅ Faster |

---

**Status:** Ready for implementation  
**Estimated Effort:** 1 hour (quick wins) to 20 hours (full refactor)  
**Risk Level:** LOW (incremental approach)  
**ROI:** HIGH (better maintainability, scalability, developer experience)

---

*Architecture analysis completed on January 27, 2026*
