# NFL Touchdown Tracker - Project Document

**Last Updated:** January 3, 2026

---

## 1. Project Overview

**NFL Touchdown Tracker** is a web-based prediction tool designed to replace manual spreadsheets for managing group NFL first-touchdown pick predictions among friends. The application provides a shared dashboard where one admin (you) manages all inputs and results, while friends view picks, leaderboards, and historical performance data.

### Target Users
- **Admin (You)**: Manages picks, updates game results, controls group settings
- **Friends**: View picks, track performance, compete on leaderboards

---

## 2. Vision & Goals

### Primary Vision
Create a **single pane of glass** for managing NFL first-touchdown predictions within a friend group, replacing spreadsheet-based tracking with a modern web application.

### Key Goals
1. **Simplify Pick Management** - One place to input weekly picks instead of scattered spreadsheets
2. **Shared Transparency** - Friends can see all picks and standings in real-time
3. **Performance Tracking** - Monitor ROI, win rates, and historical picks over time
4. **Scalable Foundation** - Build infrastructure for optional future features (user accounts, multi-group support)
5. **Stay on Streamlit** - Keep deployment simple and cost-effective

---

## 3. Current Architecture

### Technology Stack
- **Frontend/Framework**: Streamlit (Python web framework)
- **Data Source**: nflreadpy (NFL statistics library)
- **Data Processing**: pandas, numpy
- **Visualization**: Altair (via Streamlit)
- **Deployment**: Streamlit Community Cloud

### Current Features
- 📅 NFL game schedule browsing by season
- 📊 Player and team first-touchdown statistics
- 💰 Real-time betting odds integration
- 📈 Advanced player stats and historical data

### Project Structure
```
src/
├── app.py              # Main Streamlit application
├── config.py           # Configuration & constants
├── data_processor.py   # Data fetching & processing
└── __pycache__/

tests/
├── test_logic.py       # Unit tests
└── __pycache__/

docs/
├── README.md           # Quick start guide
├── ROADMAP.md          # Feature roadmap
├── DEPLOYMENT.md       # Deployment instructions
└── PROJECT.md          # This file

requirements.txt        # Python dependencies
TODO.md                 # Refactoring & task tracking
```

---

## 4. Development Roadmap

### Phase 1: Core Foundation (Current - Weeks 1-2)
**Goal**: Establish database and admin/dashboard infrastructure

#### 1.1 Database Integration
- Set up SQLite database with schema for users, weeks, picks, and results
- Implement CRUD operations for picks and results
- Enable persistent storage across sessions

#### 1.2 Admin Interface
- Create admin-only Streamlit page
- Forms to input weekly picks (player, team, odds)
- Results tracking interface
- Group member management

#### 1.3 Shared Dashboard
- Public-facing page showing current week's picks
- Leaderboard with win rates and ROI
- Historical pick tracking

### Phase 2: Enhanced Analytics (Weeks 3-4)
- ROI and profitability calculations
- Defensive matchup analysis
- +EV indicator comparisons
- Win rate trends

### Phase 3: User Experience (Future)
- Optional light user accounts (if friends request)
- Multi-group support
- Advanced filtering and search
- Mobile responsiveness improvements

---

## 5. Database Schema

### Design Principles
- Minimal but complete schema supporting core use cases
- No complex relationships; easy to query and understand
- SQLite for simplicity; easily migrated to PostgreSQL later

### Tables

#### `users`
Stores group member information.
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `weeks`
Organizes picks by NFL season and week.
```sql
CREATE TABLE weeks (
    week_id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    start_date DATE,
    end_date DATE,
    UNIQUE(season, week_number)
);
```

#### `picks`
Individual user predictions for each week.
```sql
CREATE TABLE picks (
    pick_id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    position TEXT,
    odds REAL,
    outcome TEXT,  -- 'pending', 'correct', 'incorrect'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (week_id) REFERENCES weeks(week_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

#### `results`
Game outcomes and ROI calculations.
```sql
CREATE TABLE results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pick_id INTEGER NOT NULL UNIQUE,
    game_date DATE,
    td_scorer_name TEXT,
    td_scorer_team TEXT,
    result TEXT,  -- 'correct', 'incorrect'
    theoretical_return REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pick_id) REFERENCES picks(pick_id)
);
```

---

## 6. Code Quality Standards

### Refactoring Priorities (See TODO.md)

**CRITICAL**
- [ ] Fix duplicate `get_team_abbr()` function

**HIGH**
- [ ] Extract `_classify_game_type()` helper
- [ ] Add consistent type hints
- [ ] Add TTL to Streamlit caches

**MEDIUM**
- [ ] Improve API error handling
- [ ] Move hardcoded configs
- [ ] Add input validation
- [ ] Fix test file duplicates

---

## 7. Deployment

### Local Development
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/app.py
```

### Cloud Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for Streamlit Cloud setup.

### Environment Variables
Required for production:
- `ODDS_API_KEY` - API key for betting odds data
- `NFL_API_KEY` (optional) - For future enhanced data sources

---

## 8. Testing Strategy

### Current Tests
- Basic unit tests in `tests/test_logic.py`
- Coverage for data processing functions

### Planned Tests (Phase 1+)
- Database CRUD operations
- Admin form validation
- Leaderboard calculations
- Results processing

### Running Tests
```bash
python -m pytest tests/
```

---

## 9. Contributing Guidelines

### Getting Started
1. Clone the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and test locally
4. Commit with clear messages
5. Push and create a pull request

### Code Standards
- Use type hints for all functions
- Follow PEP 8 style guide
- Add docstrings to functions
- Update tests when adding features
- Update ROADMAP.md and TODO.md as needed

---

## 10. Known Issues & Limitations

### Current Limitations
- **Session State**: Streamlit reruns entire script on interaction (acceptable for current scale)
- **Authentication**: No user login system yet
- **Real-time Updates**: Leaderboard not live-updating across users
- **Mobile UI**: Not optimized for mobile devices

### Workarounds
- Cache frequently-accessed data with TTL
- Admin manually refreshes to sync updates
- Use responsive Streamlit components for better mobile support

---

## 11. Future Enhancements (Beyond Phase 3)

- Docker containerization for consistent deployment
- PostgreSQL migration for production scale
- Automated data pipeline (GitHub Actions)
- Mobile app (React Native or Flutter)
- API layer for programmatic access
- Prediction analytics and ML-based suggestions

---

## 12. Support & Contact

For questions or issues:
- Check [README.md](README.md) for quick start
- Review [ROADMAP.md](ROADMAP.md) for planned features
- See [TODO.md](TODO.md) for current work items
- Open an issue on GitHub

---

## 13. License

MIT License - See repository for details.

---

## Appendix: Key Metrics & Success Criteria

### Phase 1 Success Criteria
- ✅ SQLite database initialized and operational
- ✅ Admin can input 5+ picks per week without errors
- ✅ Public dashboard displays picks and leaderboard correctly
- ✅ Results tracking calculates ROI accurately
- ✅ App deployed to Streamlit Cloud

### Performance Targets
- Page load time: < 2 seconds
- Admin form submission: < 1 second
- Database queries: < 500ms

### User Adoption Goals
- All friends can navigate dashboard intuitively
- Admin can manage picks in < 5 minutes per week
- Minimal bug reports in first month of use
