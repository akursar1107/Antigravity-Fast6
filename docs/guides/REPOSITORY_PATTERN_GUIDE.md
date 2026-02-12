# Repository Pattern Quick Reference Guide

## Overview

The Fast6 database layer supports a **repository pattern** for cleaner, more maintainable database access. Repositories provide:

**Note:** When importing from the backend package, use `from backend.database import ...` (e.g. in API routers, scripts, tests).

- ✅ Standardized CRUD operations
- ✅ Type-safe queries with TypedDict returns
- ✅ Automatic cache invalidation
- ✅ Consistent error handling
- ✅ Reduced code duplication

## Importing Repositories

### Option 1: Import Singletons (Recommended)
```python
from database import user_repo, pick_repo, result_repo, week_repo

# Use immediately
user = user_repo.find_by_id(123)
picks = pick_repo.find_by_user_and_week(user_id=123, week_id=1)
```

### Option 2: Import Classes
```python
from database import UserRepository, PickRepository

repo = UserRepository()
user = repo.find_by_id(123)
```

### Option 3: Import from repositories module directly
```python
from database.repositories import user_repo, pick_repo

user = user_repo.find_by_name("John Doe")
```

## Common Operations

### Creating Records

```python
from database import user_repo, week_repo, pick_repo, result_repo
from datetime import datetime

# Create a user
user_id = user_repo.create(
    name="John Doe",
    email="john@example.com",
    is_admin=False
)

# Create a season/week
week_id = week_repo.create(
    season=2025,
    week=1,
    started_at=datetime(2025, 9, 4)
)

# Create a pick
pick_id = pick_repo.create(
    user_id=user_id,
    week_id=week_id,
    team="KC",
    player_name="Patrick Mahomes",
    odds=250,
    game_id="2025_09_04_KC_JAX"
)

# Create a result (with automatic cache invalidation)
result_id = result_repo.create(
    pick_id=pick_id,
    is_correct=True,
    actual_scorer="Patrick Mahomes",
    any_time_td=True,
    actual_return=250
)
```

### Reading Records

```python
from database import user_repo, pick_repo, result_repo, week_repo

# Get by ID (works on all repositories)
user = user_repo.find_by_id(123)
pick = pick_repo.find_by_id(456)
week = week_repo.find_by_id(1)

# Get all records with pagination
users = user_repo.find_all(limit=50, offset=0)

# Find by name/email (user-specific)
user = user_repo.find_by_name("John Doe")
user = user_repo.find_by_email("john@example.com")

# Get admin users
admins = user_repo.find_all_admins()

# Get user's picks for a week
picks = pick_repo.find_by_user_and_week(user_id=123, week_id=1)

# Get all picks in a week
week_picks = pick_repo.find_by_week(week_id=1)

# Get ungraded picks
ungraded = pick_repo.find_ungraded(season=2025, week=1)

# Get results for a week
results = result_repo.find_by_week(week_id=1)

# Get correct picks for user in week
correct = result_repo.find_correct_picks(user_id=123, week_id=1)

# Count operations
pick_count = pick_repo.count_for_user_week(user_id=123, week_id=1)
correct_count = result_repo.count_correct_for_user_week(user_id=123, week_id=1)
```

### Querying with Conditions (Generic Methods)

```python
from database import user_repo

# Find records matching conditions
conditions = {'is_admin': 1, 'group_id': 5}
admins = user_repo.find_where(conditions)

# Check if record exists
exists = user_repo.exists({'name': 'John Doe'})

# Count with conditions
count = user_repo.count({'is_admin': 1})
```

### Updating Records

```python
from database import user_repo, kickoff_repo

# Update by ID
success = user_repo.update(
    id_value=123,
    data={'email': 'newemail@example.com', 'is_admin': True}
)

# Update where conditions match
updated_count = user_repo.update_where(
    conditions={'group_id': 5},
    data={'is_admin': 0}
)

# Entity-specific update
kickoff_repo.update_result(
    game_id="2025_09_04_KC_JAX",
    team="KC",
    result="won_game"
)
```

### Deleting Records

```python
from database import user_repo, pick_repo

# Delete by ID (with automatic cache invalidation for picks)
success = pick_repo.delete_by_id(123)

# Delete with conditions
deleted_count = user_repo.delete_where({'is_admin': 0})
```

### Batch Operations

```python
from database import user_repo, pick_repo

# Insert multiple records
users_data = [
    {'name': 'Alice', 'email': 'alice@example.com', 'is_admin': False},
    {'name': 'Bob', 'email': 'bob@example.com', 'is_admin': True},
]
inserted = user_repo.insert_many(users_data)
print(f"Inserted {inserted} users")
```

## Available Repositories

### UserRepository
```python
user_repo.find_by_name(name)
user_repo.find_by_email(email)
user_repo.find_all_admins()
user_repo.find_all_by_group(group_id)
user_repo.create(name, email, is_admin, group_id)
user_repo.delete_by_id(user_id)  # Invalidates caches
```

### WeekRepository
```python
week_repo.find_by_season_and_week(season, week)
week_repo.find_by_season(season)
week_repo.find_current_week(season)
week_repo.create(season, week, started_at, ended_at)
```

### PickRepository
```python
pick_repo.find_by_user_and_week(user_id, week_id)
pick_repo.find_by_week(week_id)
pick_repo.find_by_user(user_id)
pick_repo.find_ungraded(season, week)
pick_repo.create(user_id, week_id, team, player_name, odds, theoretical_return, game_id)
pick_repo.delete_by_id(pick_id)  # Invalidates caches
pick_repo.count_for_user_week(user_id, week_id)
```

### ResultRepository
```python
result_repo.find_by_pick(pick_id)
result_repo.find_by_week(week_id)
result_repo.find_by_user_week(user_id, week_id)
result_repo.find_correct_picks(user_id, week_id)
result_repo.find_any_time_tds(user_id, week_id)
result_repo.create(pick_id, is_correct, actual_scorer, any_time_td, actual_return)
result_repo.count_correct_for_user_week(user_id, week_id)
result_repo.count_any_time_tds_for_user_week(user_id, week_id)
```

### KickoffRepository
```python
kickoff_repo.find_by_game(game_id)
kickoff_repo.find_by_team(team)
kickoff_repo.find_by_game_and_team(game_id, team)
kickoff_repo.create(game_id, team, decision, result)
kickoff_repo.update_result(game_id, team, result)
```

### MarketOddsRepository
```python
market_odds_repo.find_for_game(game_id, source)
market_odds_repo.find_for_player(player_name, season, week)
market_odds_repo.find_for_week(season, week, source)
market_odds_repo.find_latest_for_player_game(game_id, player_name, source)
market_odds_repo.create(game_id, player_name, source, odds, season, week, timestamp)
```

## All Inherited Methods (From BaseRepository)

Every repository inherits these methods:

```python
# Read
repo.find_by_id(id_value)
repo.find_all(limit, offset)
repo.find_where(conditions, order_by, limit)
repo.count(conditions)
repo.exists(conditions)

# Write
repo.insert(data)
repo.insert_many(records)
repo.update(id_value, data)
repo.update_where(conditions, data)
repo.delete(id_value)
repo.delete_where(conditions)

# Query
repo.execute_query(query, params)  # Custom SELECT
repo.execute_update(query, params)  # Custom UPDATE/DELETE

# Transaction
with repo.transaction() as conn:
    conn.execute(...)
    conn.execute(...)
```

## Type Hints

All repositories return TypedDict types for full IDE support:

```python
from typing import List, Optional
from utils.types import User, Pick, Result

# IDE knows the exact fields
user: Optional[User] = user_repo.find_by_id(123)
picks: List[Pick] = pick_repo.find_by_user_and_week(123, 1)

# Autocomplete works for field names
if user:
    print(user['name'])  # IDE suggests 'name' field
```

## Automatic Cache Invalidation

Some operations automatically invalidate related caches:

```python
from database import pick_repo, result_repo

# Automatically calls invalidate_on_pick_change()
pick_repo.delete_by_id(123)

# Automatically calls invalidate_on_result_change() and invalidate_on_grading_complete()
result_repo.create(pick_id=123, is_correct=True, actual_scorer="John")
```

## Migration from Old Code

### Before
```python
from database.picks import get_user_week_picks
from database.users import add_user
from database.results import add_result

picks = get_user_week_picks(123, 1)
user_id = add_user("John Doe", "john@example.com")
result_id = add_result(pick_id=456, is_correct=True, actual_scorer="John")
```

### After
```python
from database import pick_repo, user_repo, result_repo

picks = pick_repo.find_by_user_and_week(123, 1)
user_id = user_repo.create("John Doe", "john@example.com")
result_id = result_repo.create(pick_id=456, is_correct=True, actual_scorer="John")
```

## Best Practices

1. **Use type hints** — Add return types for better IDE support
   ```python
   from typing import List
   from utils.types import Pick
   
   def get_week_picks(week_id: int) -> List[Pick]:
       return pick_repo.find_by_week(week_id)
   ```

2. **Leverage entity-specific methods** — They're more efficient than generic find_where()
   ```python
   # ✅ Good — entity-specific method
   picks = pick_repo.find_ungraded(season=2025, week=1)
   
   # ❌ Less efficient — generic method (no optimization)
   all_picks = pick_repo.find_all()
   ungraded = [p for p in all_picks if not p['result']]
   ```

3. **Use find_where for complex queries** when entity-specific methods don't exist
   ```python
   # Generic find_where (with AND logic)
   results = user_repo.find_where(
       {'is_admin': 1, 'group_id': 5},
       order_by='name',
       limit=10
   )
   ```

4. **Use transactions for multi-step operations**
   ```python
   from database import pick_repo, result_repo
   
   with pick_repo.transaction() as conn:
       conn.execute("DELETE FROM picks WHERE week_id = ?", (1,))
       conn.execute("DELETE FROM results WHERE pick_id IN (SELECT id FROM picks WHERE week_id = ?)", (1,))
   ```

## Error Handling

All repository methods use the unified error handling system:

```python
from database import pick_repo
from utils.error_handling import DatabaseError

try:
    pick_id = pick_repo.create(
        user_id=999,  # Invalid user
        week_id=1,
        team="KC",
        player_name="Mahomes"
    )
except DatabaseError as e:
    print(f"Database error: {e.context}")
    # Error is logged automatically with context
```

## More Information

- [STEP5_BASEREPOSITORY_COMPLETE.md](STEP5_BASEREPOSITORY_COMPLETE.md) — Detailed implementation notes
- [src/database/repositories.py](src/database/repositories.py) — Repository source code
- [src/database/base_repository.py](src/database/base_repository.py) — BaseRepository implementation
- [src/utils/types.py](src/utils/types.py) — Type definitions
