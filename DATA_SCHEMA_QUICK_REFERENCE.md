# Quick Reference Card - Data Improvements

**Print this out or bookmark it**

---

## The 6 Critical Issues

| Issue | Problem | Solution | Benefit |
|-------|---------|----------|---------|
| 🔴 Manual population | Player stats need script | Migrations v9-v10 | Automated on startup |
| 🔴 No automation | First TD counts stale | Trigger (v14) | Real-time updates |
| 🔴 No constraints | Duplicate picks possible | v11: UNIQUE constraint | Data integrity |
| 🔴 Missing tables | Games/rosters not linked | v9-v10: Add tables | Enable advanced queries |
| 🔴 Poor performance | Leaderboard query 500ms | v13: Indexes | <100ms queries |
| 🔴 No monitoring | Data corruption silent | Nightly QA service | Catch issues early |

---

## 6 SQL Migrations (In Order)

```
v9:  CREATE TABLE games (NFL schedule reference)
v10: CREATE TABLE rosters (Player positions)
v11: ALTER TABLE picks ADD UNIQUE(user_id, week_id, player_name)
v12: ALTER TABLE picks ADD FOREIGN KEY(game_id) REFERENCES games(id)
v13: CREATE INDEX on player_stats, results, team_ratings
v14: CREATE TRIGGER for auto-update on result insert/delete
```

---

## Expected Results

| Metric | Before | After |
|--------|--------|-------|
| Duplicate picks allowed | ✅ Yes | ❌ Impossible |
| Unknown positions | 118/485 (24%) | ~10/485 (2%) |
| First TD updates | ❌ Manual | ✅ Automatic |
| Leaderboard query | 500ms | <100ms |
| Position filter query | 450ms | 20ms |
| Manual scripts needed | ✅ Yes | ❌ No |

---

## Implementation Steps

```bash
1. Backup: cp data/fast6.db data/fast6.db.backup-20260203
2. Copy migrations into src/database/migrations.py
3. Update MIGRATIONS dict to include v9-v14
4. Create src/services/data_sync/ with ingestion services
5. Update src/app.py to call sync on startup
6. Update src/database/picks.py for auto-position
7. Test on backup first
8. Deploy to production
9. Monitor data quality nightly
```

---

## File Sizes & Read Time

| Document | Size | Time | Best For |
|----------|------|------|----------|
| [DATA_INGESTION_INDEX.md](DATA_INGESTION_INDEX.md) | 11K | 5 min | Navigation |
| [DATA_SCHEMA_IMPROVEMENT_SUMMARY.md](DATA_SCHEMA_IMPROVEMENT_SUMMARY.md) | 8.1K | 5 min | Overview |
| [SCHEMA_AND_INGESTION_PLAN.md](SCHEMA_AND_INGESTION_PLAN.md) | 20K | 15 min | Design |
| [DATA_INGESTION_FLOWS.md](DATA_INGESTION_FLOWS.md) | 16K | 20 min | Architecture |
| [SQL_MIGRATIONS_V9_V14.md](SQL_MIGRATIONS_V9_V14.md) | 32K | 30 min | Code reference |
| [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) | 18K | 20 min | Step-by-step |

---

## Key Queries to Know

### Check schema version
```sql
SELECT MAX(version) FROM schema_version;
```

### Verify tables exist
```sql
.schema games
.schema rosters
SELECT COUNT(*) FROM games;      -- Should have 256+ games
SELECT COUNT(*) FROM rosters;    -- Should have 1000+ players
```

### Test trigger
```sql
INSERT INTO results (pick_id, is_correct) VALUES (1, 1);
SELECT first_td_count FROM player_stats WHERE player_name = 'Patrick Mahomes';
-- Count should have incremented
```

### Check position distribution
```sql
SELECT position, COUNT(*) FROM player_stats WHERE season = 2025 GROUP BY position;
-- Should show QB, RB, WR, TE with counts
```

### Leaderboard query (should be <100ms)
```sql
SELECT p.player_name, p.first_td_count FROM player_stats p
WHERE p.position = 'WR' AND p.season = 2025
ORDER BY p.first_td_count DESC LIMIT 10;
```

---

## Rollback in 30 Seconds

```bash
# 1. Stop app
# 2. Restore backup
cp data/fast6.db.backup-20260203 data/fast6.db

# 3. Verify
sqlite3 data/fast6.db "SELECT MAX(version) FROM schema_version;"
# Should show 8 (pre-migration state)

# 4. Restart app
streamlit run src/app.py
```

---

## Success Checkpoints

✅ **Checkpoint 1**: Migrations Applied
- `SELECT MAX(version) FROM schema_version;` returns 14
- `SELECT name FROM sqlite_master WHERE type='table';` shows games, rosters

✅ **Checkpoint 2**: Data Loaded
- `SELECT COUNT(*) FROM games WHERE season = 2025;` ≥ 256
- `SELECT COUNT(*) FROM rosters WHERE season = 2025;` ≥ 1000

✅ **Checkpoint 3**: Automation Working
- Create a pick → check player_stats has position (not "Unknown")
- Grade a pick as correct → check first_td_count incremented

✅ **Checkpoint 4**: Performance Improved
- Leaderboard query: <100ms
- Position filter query: <50ms
- All 78 tests pass: `pytest tests/ -v`

✅ **Checkpoint 5**: Ready for Production
- Database backed up
- Monitoring active
- Rollback plan tested
- Team briefed

---

## Decision Points

| Decision | Options | Recommendation |
|----------|---------|-----------------|
| When to deploy? | ASAP / After v12 approval / After Phase 11 | ASAP (Phase 11) |
| Polymarket integration? | Nightly / On-demand / Disabled | Nightly (later) |
| Data retention? | Keep all / Archive old seasons | Keep all (for now) |
| Monitoring alert level? | Strict / Lenient / Custom | Custom (see docs) |

---

## Contact & Questions

- **Schema questions**: See SCHEMA_AND_INGESTION_PLAN.md
- **Implementation questions**: See IMPLEMENTATION_GUIDE.md
- **Architecture questions**: See DATA_INGESTION_FLOWS.md
- **SQL code questions**: See SQL_MIGRATIONS_V9_V14.md
- **All of the above**: See DATA_INGESTION_INDEX.md

---

## Timeline at a Glance

```
Monday:    Review docs (4 hours)
Tuesday:   Implement code (6 hours)
Wednesday: Test on backup (4 hours)
Thursday:  Deploy to prod (2 hours)
Friday:    Monitor & verify (ongoing)
```

**Total**: 4 days (with 1 day buffer)

---

## Remember

✅ **Do**:
- Back up database first
- Test on backup before production
- Apply migrations in order (v9→v10→...→v14)
- Monitor first 24 hours after deployment
- Keep rollback plan handy

❌ **Don't**:
- Skip migrations
- Apply out of order
- Skip testing
- Skip backup
- Deploy late Friday

---

## Files Included

```
Fast6/
├── DATA_INGESTION_INDEX.md           ← Start here (navigation)
├── DATA_SCHEMA_IMPROVEMENT_SUMMARY.md ← Executive summary
├── SCHEMA_AND_INGESTION_PLAN.md      ← Detailed design
├── DATA_INGESTION_FLOWS.md           ← Architecture & flows
├── SQL_MIGRATIONS_V9_V14.md          ← Complete SQL code
├── IMPLEMENTATION_GUIDE.md           ← Step-by-step instructions
└── DATA_SCHEMA_QUICK_REFERENCE.md    ← This file
```

---

## One-Paragraph Summary

Fast6 has a data infrastructure problem: player stats and positions are populated manually, first TD counts don't update automatically, duplicate picks are possible, and leaderboard queries are slow. Solution: 6 SQL migrations that add games/rosters tables, enforce unique/foreign key constraints, add indexes, and enable automation triggers. Result: Real-time analytics, zero duplicates, 5x faster queries, and no more manual scripts.

---

**Last Updated**: Feb 3, 2026  
**Version**: 1.0  
**Status**: Ready for Implementation
