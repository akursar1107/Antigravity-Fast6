# TODO - January 6, 2026

## ✅ COMPLETED WORK

### Code Refactoring (All Complete)
- [x] **Fixed duplicate `get_team_abbr()` function** - Removed untyped version
- [x] **Extracted `_classify_game_type()` helper** - Eliminated duplication
- [x] **Added consistent type hints** - All data_processor functions typed
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
