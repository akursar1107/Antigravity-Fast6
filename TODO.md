# TODO - January 6, 2026

## 🎯 CURRENT SPRINT

### Phase 2 Continued: Database Reset & Point System
### Code Refactoring (Completed)
- [x] **Fixed duplicate `get_team_abbr()` function** - Removed untyped version
- [x] **Extracted `_classify_game_type()` helper** - Eliminated duplication
- [x] **Added consistent type hints** - All data_processor functions typed
- [x] **Added TTL to caches** - `load_data()` refresh: 5 minutes
- [x] **Improved API error handling** - Specific exceptions + logging
- [x] **Moved API config to config.py** - ODDS_API_* constants
- [x] **Added input validation** - Column checks with graceful returns
- [x] **Fixed test file** - Removed duplicate assertions
- [x] **Refactored app.py into modular pages** - 459 lines → 90 line router

---

## 📋 NEXT PHASE: Database Reset & Features

### High Priority
1. **Drop database and fresh import**
   - Delete fast6.db
   - Recreate schema with game_id support
   - Reimport "First TD - Sheet5 (1).csv" with Home/Visitor columns
   - Verify all picks have valid game_ids
   - Test Grade Picks with clean data

2. **Add point system for TD scorers**
   - Design schema for pick_type (first_td, anytime_td)
   - Define scoring system (points per correct/incorrect)
   - Update admin to support both pick types
   - Display points on leaderboard and stats
   - Update Grade Picks for both types

3. **Refactor codebase**
   - Create `src/utils/admin_utils.py` - Backfill, dedupe, maintenance functions
   - Create `src/utils/grading_logic.py` - Grade operations, name matching
   - Create `src/utils/team_resolution.py` - Team matching, game_id lookup
   - Consolidate helper functions
   - Remove duplicate code

### Medium Priority
- [ ] ROI & Profitability trends
- [ ] Defensive matchup analysis
- [ ] User self-management (light auth)
- [ ] Multi-group support

---

## 📊 Code Statistics
- **1,800+ lines** new/updated code
- **95+ functions** across modules
- **5 database tables** with foreign keys
- **12 UI tabs** (6 admin + 6 public)
- **3 caching strategies** with 5-min TTL
- **100% test pass rate**

---

## 📝 Notes
- Phase 1 complete and deployed
- Phase 2a (Auto-grading) complete; starting Phase 2b
- Ready for database reset and fresh import
- Codebase ready for modularization

See [ROADMAP.md](ROADMAP.md) for detailed feature roadmap.unctions typed
- [x] **Added TTL to caches** - `load_data()` refresh: 5 minutes
- [x] **Improved API error handling** - Specific exceptions + logging
- [x] **Moved API config to config.py** - ODDS_API_* constants
- [x] **Added input validation** - Column checks with graceful returns
- [x] **Fixed test file** - Removed duplicate assertions
- [x] **Refactored app.py into modular pages** - 459 lines → 90 line router

### Phase 1: Database Integration (All Complete)
- [x] **SQLite schema setup** - 4 tables, foreign keys, cascading deletes
- [x] **Database module creation** - 550 lines, 50+ functions
- [x] **Admin interface page** - 4 tabs for user/pick/result management
- [x] **Public dashboard expansion** - 6 tabs including leaderboard
- [x] **Comprehensive testing** - 8 integration test suites (all passing)

---

## 🚀 Phase 2: Enhanced Analytics (Future)

### Optional Features
- [ ] **ROI & Profitability Tracking**: Advanced analytics and trends
- [ ] **Defensive Matchup Analysis**: Context-aware pick suggestions
- [ ] **User Self-Management**: Light auth if friends want to submit picks
- [ ] **Multi-Group Support**: Separate leaderboards for multiple groups

---

## 📝 Notes
- Phase 1 is production-ready and deployed
- All features tested and validated
- Database persists all picks and results
- Ready for Streamlit Community Cloud deployment
- See PHASE1_COMPLETE.md for detailed implementation summary
