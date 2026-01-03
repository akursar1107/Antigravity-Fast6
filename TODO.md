# TODO - January 3, 2026

## Code Refactoring & Optimization

### Priority: CRITICAL
- [ ] **Fix duplicate `get_team_abbr()` function** in src/data_processor.py (lines 161-165)
  - Two definitions exist; remove the first untyped version
  - Keep the type-hinted version (line 164)

### Priority: HIGH
- [ ] **Extract `_classify_game_type()` helper function**
  - Remove duplication between `process_game_type()` and `get_game_schedule()`
  - Create single reusable function for game classification logic
  
- [ ] **Add consistent type hints**
  - Review all functions in `data_processor.py`
  - Add missing type hints for parameters and return values
  - Improves maintainability before database integration

- [ ] **Add TTL to Streamlit caches**
  - `@st.cache_data(ttl=300)` for `load_data()` 
  - `@st.cache_data(ttl=300)` for `load_rosters()`
  - Needed for database sync in Phase 1

### Priority: MEDIUM
- [ ] **Improve API error handling** in `get_first_td_odds()`
  - Replace silent `except: continue` with logging
  - Add debug output for failed API calls
  - Consider retry logic

- [ ] **Move hardcoded API config** to `config.py`
  - Extract `ODDS_API_MARKET = "player_anytime_td"` 
  - Replace hardcoded strings in functions

- [ ] **Add input validation** to data processor functions
  - Validate required columns exist before accessing
  - Handle edge cases gracefully

- [ ] **Fix test file** in tests/test_logic.py
  - Remove duplicate assertion on line 34-35
  - Add test for `get_first_td_odds()`
  - Add tests for new database functions (post-Phase 1)

### Priority: LOW (Post-Database)
- [ ] **Refactor `app.py`** into modular pages
  - Split into `admin_page.py` for admin interface
  - Create `public_dashboard.py` for shared view
  - Keep `app.py` as router/orchestrator
  - Current file is 459 lines (too large)

---

## Phase 1: Database Integration (Next Steps)

- [ ] Set up SQLite schema (see ROADMAP.md)
- [ ] Create database initialization module
- [ ] Build admin interface page
- [ ] Build public dashboard page

---

## Notes
- Current app is fully functional on Streamlit + nflreadpy
- Refactoring should be completed before Phase 1 database work
- Estimated time: 2-3 hours for all HIGH priority items
