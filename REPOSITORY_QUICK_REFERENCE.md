# Fast6 Database Layer Quick Reference Card

## Import Repositories
```python
from database import (
    user_repo, week_repo, pick_repo, result_repo,
    kickoff_repo, market_odds_repo
)
```

## Common Operations Cheat Sheet

### CREATE
```python
user_id = user_repo.create("John Doe", "john@example.com")
week_id = week_repo.create(2025, 1)
pick_id = pick_repo.create(user_id, week_id, "KC", "Mahomes", 250)
result_id = result_repo.create(pick_id, True, "Mahomes", True, 250)
```

### READ by ID
```python
user = user_repo.find_by_id(123)
pick = pick_repo.find_by_id(456)
result = result_repo.find_by_pick(456)
```

### READ with Filters
```python
# User-specific
admins = user_repo.find_all_admins()
user = user_repo.find_by_name("John")
user = user_repo.find_by_email("john@example.com")

# Week-specific
weeks = week_repo.find_by_season(2025)
current = week_repo.find_current_week(2025)

# Pick-specific
picks = pick_repo.find_by_user_and_week(123, 1)
ungraded = pick_repo.find_ungraded(2025, week=1)

# Result-specific
correct = result_repo.find_correct_picks(123, 1)
any_tds = result_repo.find_any_time_tds(123, 1)
```

### UPDATE
```python
user_repo.update(123, {'email': 'newemail@example.com'})
kickoff_repo.update_result("game_id", "KC", "won_game")
```

### DELETE (Auto-invalidates cache)
```python
pick_repo.delete_by_id(123)  # Invalidates pick cache
```

### COUNT
```python
count = pick_repo.count_for_user_week(123, 1)
correct_count = result_repo.count_correct_for_user_week(123, 1)
any_td_count = result_repo.count_any_time_tds_for_user_week(123, 1)
```

## Type Hints
```python
from typing import List, Optional
from utils.types import User, Pick, Result

user: Optional[User] = user_repo.find_by_id(123)
picks: List[Pick] = pick_repo.find_by_user_and_week(123, 1)
```

## Error Handling
```python
from utils.error_handling import DatabaseError

try:
    pick_id = pick_repo.create(...)
except DatabaseError as e:
    print(f"Error: {e.context}")  # Has context info
```

## Batch Operations
```python
users_data = [
    {'name': 'Alice', 'email': 'alice@example.com', 'is_admin': False},
    {'name': 'Bob', 'email': 'bob@example.com', 'is_admin': False},
]
inserted = user_repo.insert_many(users_data)
```

## Generic Methods (All Repositories)
```python
user_repo.find_all(limit=50, offset=0)
user_repo.find_where({'is_admin': 1}, order_by='name', limit=10)
user_repo.exists({'name': 'John'})
user_repo.count({'is_admin': 1})
```

## Full Documentation
- **Quick Guide**: `docs/guides/REPOSITORY_PATTERN_GUIDE.md`
- **Step 5 Details**: `STEP5_BASEREPOSITORY_COMPLETE.md`
- **Error Handling**: `STEP1_EXCEPTION_HANDLING_COMPLETE.md`
- **Caching**: `STEP2_UNIFIED_CACHING_COMPLETE.md`
- **Types**: `STEP4_TYPE_SAFETY_COMPLETE.md`
