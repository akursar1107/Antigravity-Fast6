# Data Ingestion & Schema Improvement - Complete Package

## 📚 Documentation Index

This package contains a complete overhaul plan for Fast6's data infrastructure. Start here and work through in order.

---

## 1️⃣ START HERE: Executive Summary
**File**: [DATA_SCHEMA_IMPROVEMENT_SUMMARY.md](DATA_SCHEMA_IMPROVEMENT_SUMMARY.md)  
**Read time**: 5 minutes  
**What you'll learn**:
- The 6 critical problems with current system
- High-level solution (6 SQL migrations)
- Expected outcomes (5x faster queries, zero duplicates)
- Implementation roadmap

**Key questions answered**:
- Why do we need to change anything?
- What's the payoff?
- How long will it take?

---

## 2️⃣ DESIGN DEEP DIVE: Schema & Ingestion Plan
**File**: [SCHEMA_AND_INGESTION_PLAN.md](SCHEMA_AND_INGESTION_PLAN.md)  
**Read time**: 15 minutes  
**What you'll learn**:
- Current schema issues (missing PK/FK, no indexes, denormalized)
- Proposed schema changes (games table, rosters table, constraints)
- Normalization analysis (1NF → 3NF)
- 4-phase implementation strategy

**Key questions answered**:
- What tables should we add?
- What constraints should we add?
- How do we normalize the data?
- What's the implementation order?

---

## 3️⃣ FLOWS & TRIGGERS: Data Pipeline
**File**: [DATA_INGESTION_FLOWS.md](DATA_INGESTION_FLOWS.md)  
**Read time**: 20 minutes  
**What you'll learn**:
- Current state (manual, error-prone)
- Proposed state (automated, event-driven)
- Data quality pipeline with validation layers
- Service responsibilities
- Database triggers reference
- Migration execution plan with rollback

**Key questions answered**:
- How does data flow through the system?
- How do triggers update leaderboards?
- What services are needed?
- How do we execute migrations safely?

---

## 4️⃣ SQL CODE: Complete Migrations
**File**: [SQL_MIGRATIONS_V9_V14.md](SQL_MIGRATIONS_V9_V14.md)  
**Read time**: 30 minutes (reference material)  
**What you'll learn**:
- Complete Python code for all 6 migrations
- Create games table (v9)
- Create rosters table (v10)
- Add unique constraint to picks (v11)
- Add game foreign key to picks (v12)
- Add performance indexes (v13)
- Add automation triggers (v14)
- Testing strategy and rollback procedure

**Key questions answered**:
- What's the exact SQL to run?
- How do I test migrations?
- What if something breaks?
- How do I verify it worked?

---

## 5️⃣ IMPLEMENTATION GUIDE: Step-by-Step
**File**: [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)  
**Read time**: 20 minutes  
**What you'll learn**:
- Quick start (3 commands to get running)
- Step-by-step implementation (5 steps)
- How to create ingestion services
- How to update app.py
- How to test setup
- Troubleshooting guide
- Performance verification

**Key questions answered**:
- How do I actually implement this?
- What code do I need to write?
- How do I set up the ingestion services?
- How do I know if it's working?

---

## 📊 Reading Paths by Role

### For Product Managers / Stakeholders
Read these to understand impact and timeline:
1. [DATA_SCHEMA_IMPROVEMENT_SUMMARY.md](DATA_SCHEMA_IMPROVEMENT_SUMMARY.md) (5 min)
2. Expected Outcomes section in Summary (2 min)
3. Success Criteria (1 min)

**Total**: ~8 minutes

### For Backend Engineers (Implementation)
Read these for detailed implementation:
1. [DATA_SCHEMA_IMPROVEMENT_SUMMARY.md](DATA_SCHEMA_IMPROVEMENT_SUMMARY.md) (5 min)
2. [SCHEMA_AND_INGESTION_PLAN.md](SCHEMA_AND_INGESTION_PLAN.md) (15 min)
3. [SQL_MIGRATIONS_V9_V14.md](SQL_MIGRATIONS_V9_V14.md) (30 min - code reference)
4. [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) (20 min - step-by-step)

**Total**: ~70 minutes

### For Database Administrators
Read these for migration strategy and monitoring:
1. [DATA_INGESTION_FLOWS.md](DATA_INGESTION_FLOWS.md) (20 min)
2. [SQL_MIGRATIONS_V9_V14.md](SQL_MIGRATIONS_V9_V14.md) (30 min)
3. Migration Execution Checklist + Rollback Procedure

**Total**: ~50 minutes

### For QA / Testing Engineers
Read these for testing strategy:
1. [DATA_SCHEMA_IMPROVEMENT_SUMMARY.md](DATA_SCHEMA_IMPROVEMENT_SUMMARY.md) - Success Criteria (5 min)
2. [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) - Testing section (10 min)
3. [SQL_MIGRATIONS_V9_V14.md](SQL_MIGRATIONS_V9_V14.md) - Testing Strategy (10 min)

**Total**: ~25 minutes

---

## 🎯 Key Concepts Explained

### Unique Constraint
**Problem**: User can pick same player twice in same week (already happened)  
**Solution**: `ALTER TABLE picks ADD UNIQUE(user_id, week_id, player_name)`  
**Benefit**: Prevents duplicates at database level  
**Performance**: Negligible impact

### Foreign Key Constraint
**Problem**: Picks not linked to games; can delete games without knowing which picks affected  
**Solution**: `ALTER TABLE picks ADD FOREIGN KEY(game_id) REFERENCES games(id)`  
**Benefit**: Referential integrity, enables joins  
**Performance**: Negligible impact with indexes

### Database Trigger
**Problem**: First TD counts don't update when results graded; manual recalculation needed  
**Solution**: `CREATE TRIGGER update_player_stats_on_result_insert AFTER INSERT ON results`  
**Benefit**: Automatic, real-time leaderboard updates  
**Performance**: Slight overhead on grading (~10ms), but eliminates manual scripts

### Index
**Problem**: Leaderboard queries full-scan 485 rows; takes 500ms  
**Solution**: `CREATE INDEX idx_player_stats_position_season ON player_stats(position, season)`  
**Benefit**: Indexed lookup instead of full scan; 5x faster  
**Performance**: Small write overhead, but huge read improvement

---

## 🚀 Quick Start Commands

```bash
# Clone the Fast6 repo
cd Fast6

# Activate virtual environment
source .venv/bin/activate

# Backup database
cp data/fast6.db data/fast6.db.backup-$(date +%Y%m%d)

# Copy migration code into src/database/migrations.py
# (See SQL_MIGRATIONS_V9_V14.md)

# Run app (migrations auto-apply)
streamlit run src/app.py

# Verify migrations applied
sqlite3 data/fast6.db
# > SELECT version FROM schema_version ORDER BY version DESC LIMIT 1;
# > .schema games
```

---

## 📈 Timeline

| Phase | Duration | What | Who |
|-------|----------|------|-----|
| Phase 1: Review | 1 day | Read docs, ask questions | Product + Engineering |
| Phase 2: Prep | 1 day | Backup DB, prepare code | Engineering |
| Phase 3: Test | 1 day | Run migrations on backup, verify | QA + Engineering |
| Phase 4: Deploy | ½ day | Apply migrations to prod | DevOps + Engineering |
| Phase 5: Ingestion | ½ day | Sync rosters, games, market data | DevOps + Engineering |
| Phase 6: Monitor | Ongoing | Daily data quality checks | DevOps |

**Total**: 4 days (includes buffer for testing)

---

## ✅ Success Criteria

After implementation:
- [ ] Zero duplicate picks possible (unique constraint)
- [ ] All picks have valid game_id (FK constraint)
- [ ] All players have position (rosters normalized)
- [ ] Leaderboard queries < 100ms (indexes)
- [ ] First TD updates real-time (triggers)
- [ ] All 78 tests pass (regression testing)
- [ ] Nightly data quality checks active (monitoring)
- [ ] Can rollback in < 5 minutes (rollback plan)

---

## 🤔 FAQ

### Q: Can I implement this incrementally?
**A**: Yes, but follow the order: v9 (games) → v10 (rosters) → v11 (unique) → v12 (FK) → v13 (indexes) → v14 (triggers)

### Q: What if I mess up?
**A**: You have a backup (Step 1) and a rollback procedure. Worst case: restore backup and start over. Estimated recovery time: 5 minutes.

### Q: Will this break existing code?
**A**: No, migrations are backward compatible. Existing queries still work; new features just become available.

### Q: How much will this slow down the app?
**A**: Slightly faster! Query performance improves 5-20x. Write performance unchanged (triggers add ~10ms per grading).

### Q: Can I skip some migrations?
**A**: Not recommended. Each one solves a specific problem:
- v9: Enables game linking (required for scheduling features)
- v10: Enables position normalization (required for position filter)
- v11: Prevents data corruption (critical)
- v12: Enables referential integrity (critical)
- v13: Improves performance (highly recommended)
- v14: Enables automation (highly recommended)

Skip v13-v14 if urgent, but implement them ASAP.

### Q: Who should review this?
**A**: Product (impact), Backend Engineers (implementation), DBAs (migration strategy), QA (testing).

---

## 📞 Questions or Issues?

If you need clarification on any concept:
1. Check the FAQ above
2. Re-read the relevant section in the document
3. Search for the keyword in all docs (e.g., "foreign key")
4. Ask in code review

---

## 🎓 Learning Resources

### Concepts Used
- **Normalization**: [SCHEMA_AND_INGESTION_PLAN.md](SCHEMA_AND_INGESTION_PLAN.md#normalization-analysis)
- **Foreign Keys**: [SQL_MIGRATIONS_V9_V14.md](SQL_MIGRATIONS_V9_V14.md#migration-v12-add-game-foreign-key-to-picks)
- **Triggers**: [DATA_INGESTION_FLOWS.md](DATA_INGESTION_FLOWS.md#database-triggers-reference)
- **Indexes**: [SQL_MIGRATIONS_V9_V14.md](SQL_MIGRATIONS_V9_V14.md#migration-v13-add-performance-indexes)

### External References
- SQLite documentation: https://www.sqlite.org/lang_createtable.html
- Database normalization: https://en.wikipedia.org/wiki/Database_normalization
- Trigger examples: https://www.sqlite.org/lang_createtrigger.html

---

## 📋 Implementation Checklist

Use this when you're ready to implement:

### Pre-Implementation
- [ ] Read [DATA_SCHEMA_IMPROVEMENT_SUMMARY.md](DATA_SCHEMA_IMPROVEMENT_SUMMARY.md)
- [ ] Read [SCHEMA_AND_INGESTION_PLAN.md](SCHEMA_AND_INGESTION_PLAN.md)
- [ ] Read [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
- [ ] Backup database: `cp data/fast6.db data/fast6.db.backup-20260203`
- [ ] Create feature branch: `git checkout -b feature/schema-improvements`

### Implementation
- [ ] Copy migrations v9-v14 into `src/database/migrations.py`
- [ ] Update MIGRATIONS dict
- [ ] Create `src/services/data_sync/` directory
- [ ] Create `roster_ingestion.py`
- [ ] Create `game_sync.py`
- [ ] Update `src/app.py` to call sync on startup
- [ ] Update pick creation in `src/database/picks.py`

### Testing
- [ ] Run migrations on backup database
- [ ] Verify all tables created
- [ ] Test pick creation (auto-position)
- [ ] Test result grading (auto-update)
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Manual testing in Streamlit app

### Deployment
- [ ] Create pull request with migrations
- [ ] Code review (1-2 reviewers)
- [ ] Merge to main
- [ ] Deploy to staging
- [ ] Test in staging (24 hours)
- [ ] Deploy to production
- [ ] Monitor data quality (24 hours)

---

## 🎉 Completion

When all steps are done:
- Commit changes with message: "feat: implement data schema improvements (v9-v14)"
- Create milestone "Schema v2" as complete
- Update backlog: Mark related issues closed
- Celebrate! You've eliminated manual data scripts and prevented future bugs

