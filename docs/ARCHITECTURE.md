## Clean Architecture Reference

### Overview

Fast6 has been restructured following **Clean Architecture** principles to improve maintainability, testability, and separation of concerns. The application is organized into distinct layers, each with clear responsibilities and minimal external dependencies.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  UI LAYER (Streamlit)                       │
│  - src/app.py (legacy entry point)                         │
│  - src/app_v2.py (new clean architecture entry point)      │
│  - src/ui/admin/*.py (admin views)                         │
│  - src/ui/public/*.py (public views)                       │
│  - src/ui/components/ (reusable UI components)             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│            API ORCHESTRATION LAYER                          │
│  - src/api/picks_api.py                                    │
│  - src/api/grading_api.py                                  │
│  - Coordinates core use cases with data repositories       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│          DATA PERSISTENCE LAYER (Repositories)              │
│  - src/data/repositories/base.py (CRUD mixin)             │
│  - src/data/repositories/picks_repository.py              │
│  - src/data/repositories/results_repository.py            │
│  - Implements abstract ports with SQLite                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│        BUSINESS LOGIC LAYER (Domain/Use Cases)              │
│  - src/core/picks/ (Pick entity, validation, use cases)   │
│  - src/core/grading/ (Grading logic, result tracking)     │
│  - Pure business logic, no external dependencies           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│     INFRASTRUCTURE LAYER (Shared Utilities)                 │
│  - src/lib/observability.py (logging, monitoring)         │
│  - src/lib/resilience.py (circuit breaker, retries)       │
│  - src/lib/caching.py (TTL config, invalidation)          │
│  - src/lib/error_handling.py (structured exceptions)      │
│  - src/lib/types.py (shared type definitions)             │
│  - src/lib/theming.py (UI theme generation)               │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

#### 1. Infrastructure Layer (`src/lib/`)
**Purpose**: Shared utilities that all layers can use without coupling

**Dependencies**: Python standard library + external packages (pydantic, streamlit optional)
**Exports**: Logging, caching, error handling, type definitions, UI utilities

**Modules**:
- `observability.py`: Log events, operation tracking, metrics
- `resilience.py`: Circuit breaker for API calls, request retries
- `caching.py`: Unified caching with TTL configuration, cache invalidation
- `error_handling.py`: Structured exceptions, error context, decorators
- `types.py`: Shared Pydantic models, enums
- `theming.py`: Dynamic theme CSS generation

**Key Principle**: **Config-optional** - Core modules can import without config.json

#### 2. Business Logic Layer (`src/core/`)
**Purpose**: Pure business logic independent of any framework or persistence mechanism

**Dependencies**: `src/lib` only (no Streamlit, no database)
**Exports**: Entities, validation, use case functions

**Structure per feature**:
```
src/core/picks/
├── entities.py       # Pydantic models: Pick, PickStatus, GameInfo
├── ports.py         # Abstract interfaces: PickRepository, GameRepository
├── use_cases.py     # Business functions: create_pick(), list_user_picks(), etc.
└── errors.py        # Domain-specific exceptions

src/core/grading/
├── entities.py      # Result, GradingResult
├── ports.py        # ResultRepository, PlayByPlayRepository
├── use_cases.py    # grade_pick(), grade_season()
└── errors.py       # GradingError, NameMatchError
```

**Key Principle**: **Dependency Injection** - Repositories passed as parameters, not imported

```python
# ✅ CORRECT - Core layer
def create_pick(
    user_id: int,
    week_id: int,
    game_id: str,
    team: str,
    player_name: str,
    odds: float,
    pick_repository: PickRepository,  # Injected, not imported
    game_repository: Optional[GameRepository] = None,
) -> Pick:
    # Pure business logic
    existing = pick_repository.get_user_picks(user_id, week_id)
    if any(p.game_id == game_id for p in existing):
        raise DuplicatePickError(...)
    # ...
```

#### 3. Data Persistence Layer (`src/data/`)
**Purpose**: Implement abstract repository interfaces for database access

**Dependencies**: `src/core` + `src/lib` + sqlite3
**Exports**: Repository implementations

**Modules**:
- `base.py`: BaseRepository mixin with common CRUD operations
- `picks_repository.py`: SQLitePickRepository implements PickRepository port
- `results_repository.py`: SQLiteResultRepository implements ResultRepository port
- `*_repository.py`: One file per entity/aggregate

**Key Principle**: **Repository Pattern** - Hide database details behind abstract interfaces

```python
# Core defines what it needs
class PickRepository(ABC):
    def get_user_picks(self, user_id: int, week_id: int) -> list[Pick]: ...

# Data implements how to get it
class SQLitePickRepository(BaseRepository, PickRepository):
    def get_user_picks(self, user_id: int, week_id: int) -> list[Pick]:
        # SQLite-specific implementation
        rows = self._query("SELECT * FROM picks WHERE ...")
        return [Pick(**row) for row in rows]
```

#### 4. API Orchestration Layer (`src/api/`)
**Purpose**: Coordinate core use cases with data repositories, provide clean API for UI

**Dependencies**: `src/core` + `src/data` + `src/lib`
**Exports**: API functions that accept user input and return results

**Modules**:
- `picks_api.py`: `api_create_pick()`, `api_list_user_picks()`, etc.
- `grading_api.py`: `api_grade_season()`, `api_grade_pick()`, etc.

**Key Principle**: **Dependency Management** - Handles instantiation of repositories

```python
# API layer coordinates core + data
def api_create_pick(
    user_id: int,
    week_id: int,
    game_id: str,
    team: str,
    player_name: str,
    odds: float,
) -> dict:
    # Instantiate repositories
    pick_repo = SQLitePickRepository(get_db_connection())
    game_repo = SQLiteGameRepository(get_db_connection())
    
    # Call core use case with injected dependencies
    pick = create_pick(
        user_id, week_id, game_id, team, player_name, odds,
        pick_repository=pick_repo,
        game_repository=game_repo,
    )
    
    # Return serialized result to UI
    return pick.dict()
```

#### 5. UI Presentation Layer (`src/ui/`)
**Purpose**: Streamlit interface, user interaction, display logic

**Dependencies**: `src/api` + `src/lib` + streamlit
**Exports**: Streamlit pages and components

**Structure**:
```
src/ui/
├── app.py                    # Main entry point router
├── app_v2.py               # New architecture entry point (alternative)
├── components/             # Reusable Streamlit components
│   ├── __init__.py
│   ├── forms.py           # Input forms (pick, result, etc.)
│   ├── tables.py          # Data tables, leaderboards
│   └── charts.py          # Plots and visualizations
├── admin/                  # Admin dashboard views
│   ├── __init__.py
│   ├── dashboard.py       # Overview, quick stats
│   ├── picks.py          # Manage picks
│   ├── results.py        # Record results
│   ├── grading.py        # Auto-grade picks
│   ├── settings.py       # App configuration
│   ├── exports.py        # Export data
│   ├── users.py          # User management
│   └── shared.py         # Shared admin utilities
└── public/                 # Public dashboard views
    ├── __init__.py
    ├── leaderboard.py     # League standings
    ├── week_picks.py      # View picks for week
    ├── player_performance.py # Player stats
    ├── roi_trends.py      # ROI tracking
    ├── power_rankings.py   # Team rankings
    ├── market_comparison.py # Compare odds
    ├── defense_matchups.py  # Defensive analysis
    ├── team_analysis.py    # Team insights
    └── schedule.py        # Game schedule
```

**Key Principle**: **Thin UI Layer** - Most logic in core/api, UI only handles display

```python
# ✅ CORRECT - UI layer is thin
def show_create_pick_form():
    with st.form("create_pick"):
        user_id = st.selectbox("User", get_users())
        week_id = st.selectbox("Week", get_weeks())
        # ... other form inputs
        
        if st.form_submit_button("Create Pick"):
            # Call API layer (which manages core + data)
            result = api_create_pick(
                user_id=user_id,
                week_id=week_id,
                # ... other args
            )
            
            # Simple display logic
            if result.get("success"):
                st.success("Pick created!")
            else:
                st.error(result.get("error"))
```

### Dependency Direction

```
UI imports API ✓
UI imports lib ✓
API imports core ✓
API imports data ✓
API imports lib ✓
Data imports core ✓
Data imports lib ✓
Core imports lib ✓

UI imports core ✗ (goes through API)
UI imports database/views ✗ (use API layer)
Core imports Streamlit ✗ (config-optional only)
Core imports database ✗ (uses dependency injection)
```

### Isolation & Testing Benefits

#### Core Layer Tests
```python
# Core is independently testable with mocked repositories
def test_create_pick():
    # Mock repository
    mock_repo = MockPickRepository()
    
    # Call core use case directly, no Streamlit/database needed
    pick = create_pick(
        user_id=1,
        week_id=1,
        game_id="game1",
        team="KC",
        player_name="Mahomes",
        odds=250,
        pick_repository=mock_repo,
    )
    
    assert pick.player_name == "Mahomes"
    assert mock_repo.save_called
```

#### API Layer Tests
```python
# API layer tests with real repository (SQLite in-memory)
def test_api_create_pick():
    # Real SQLite, real use case
    result = api_create_pick(
        user_id=1,
        week_id=1,
        game_id="game1",
        team="KC",
        player_name="Mahomes",
        odds=250,
    )
    
    assert result["success"]
    assert result["pick_id"]
```

#### UI Layer Tests
```python
# UI layer tests with mocked API layer
def test_create_pick_form():
    with patch("ui.admin.api_create_pick") as mock_api:
        mock_api.return_value = {"success": True, "pick_id": 1}
        
        # Simulate user interaction
        st.button("Create Pick")  # Would call api_create_pick
        
        assert mock_api.called
```

### Migration Path: Old → New

**Current State** (Phases 1-9):
- Legacy app.py still works (uses old database/ and utils/)
- New clean architecture in place (lib/, core/, data/, api/, ui/)
- Both can coexist during transition

**Phase 10-11 Plan**:
1. View files copied to src/ui/ but still use old imports
2. Gradually update view imports to use API layer
3. One view/module at a time to minimize risk
4. Archive old src/views/, src/database/, src/utils/ once all migrated
5. Switch primary entry point from app.py → app_v2.py

**Benefits of Parallel Run**:
- ✅ Can test new architecture without breaking existing functionality
- ✅ Gradual migration reduces risk
- ✅ Easy rollback if issues found
- ✅ Can deploy new features using new architecture while old views still work

### Configuration Access

**Infrastructure layer** (src/lib/) made config-optional:

```python
# Old way (breaks at import time if config missing)
from src import config
TTL = config.ODDS_API_CACHE_TTL  # NameError if config not loaded

# New way (config is optional)
class CacheTTL:
    ODDS_API = 3600  # Default
    
    @classmethod
    def load_from_config(cls):
        # Optional: Override defaults from config if available
        try:
            from src import config
            if hasattr(config, 'ODDS_API_CACHE_TTL'):
                cls.ODDS_API = config.ODDS_API_CACHE_TTL
        except ImportError:
            pass  # Config not available, use defaults
```

Application startup calls `CacheTTL.load_from_config()` to override defaults if config exists.

### Key Files Reference

**Entry Points**:
- `src/app.py` - Legacy Streamlit app (still works)
- `src/app_v2.py` - New clean architecture entry point

**Run Command**:
```bash
# Legacy app (old code path)
streamlit run Fast6/src/app.py

# New architecture (new code path)
streamlit run Fast6/src/app_v2.py
```

**Configuration**:
- `src/config.json` - Centralized settings (teams, scoring, API keys)
- `src/config.py` - Python wrapper for config.json access

**Key Modules**:
- Import all from one place: `from src.lib import *`
- Use core use cases directly: `from src.core.picks.use_cases import create_pick`
- Call API layer from UI: `from src.api.picks_api import api_create_pick`

### Summary

| Aspect | Benefit |
|--------|---------|
| **Separation of Concerns** | Each layer has single responsibility, easier to understand |
| **Testability** | Core logic testable without Streamlit/database, no mocks needed |
| **Reusability** | Core logic can be used by API, CLI, mobile backend, etc. |
| **Maintainability** | Clear dependency flow, no circular dependencies |
| **Deployment Flexibility** | Can deploy core logic to serverless, cache separately, etc. |
| **Scaling** | Core layer has no I/O, can optimize independently |
| **Team Collaboration** | Different teams can work on different layers simultaneously |

---

**Architecture Version**: v2.0.0  
**Implementation Date**: February 2025  
**Status**: Stable with ongoing view migration (Phase 10+)
