# Data Pipeline & Schema Review

*Assessment prompted by TD scorer accuracy issues (K. Boutte bug) and data consistency concerns.*

**→ [ARCHITECTURE_DIAGRAMS.md](./ARCHITECTURE_DIAGRAMS.md)** – Visual data flow & schema  
**→ [OPTIMIZATION_ROADMAP.md](./OPTIMIZATION_ROADMAP.md)** – Best practices & implementation plan

---

## Current Architecture

### Data Sources

| Source | What | Where Used |
|--------|------|------------|
| **nflreadpy** | Play-by-play (PBP), schedules, rosters | Via `load_data()`, `load_schedules()`, `load_rosters()` |
| **Games table** | id, season, week, teams, scores, status | Matchup status, schedule, game lookup |
| **Picks table** | user_id, week_id, team, player_name, odds, game_id | Core user predictions |
| **Results table** | pick_id, actual_scorer, is_correct, any_time_td | Grading output |

### Data Flow

```
nflreadpy (external)          DB (SQLite)
────────────────────         ────────────
load_schedules() ──sync──►   games
load_rosters()   ──sync──►   rosters

load_pbp()       ──never stored──►  TD scorers (computed on-the-fly)
                              Grading (via TDLookupCache)
                              ELO, player_stats, defense_analysis
```

---

## Issues Identified

### 1. **Split Sources of Truth**

- **TD scorers** (matchup page): computed from `load_pbp()` every request (cached 5 min)
- **Game status**: from `games` table (synced from schedules)
- **Grading**: uses same `get_touchdowns()` logic but via separate cache

If nflreadpy PBP and schedules disagree (e.g. game_id format, timing), we get inconsistent views.

### 2. **No Materialized TD Data**

Every matchup view for a final game triggers:
1. `load_data(season)` – full season PBP (~hundreds of MB)
2. `get_touchdowns(df)` – filter all TDs
3. Filter by game_id

This is expensive and repeated. TD data is derived but never stored.

### 3. **Game ID Format Assumptions**

- We parse `game_id` as `"2025_01_AWAY_HOME"` (season_week_away_home)
- nflreadpy `game_id` format may differ across seasons or play types
- No validation or normalization layer

### 4. **`posteam` on Return TDs**

For INT/fumble return TDs, `posteam` = team with possession at snap (the offense that threw/fumbled). The scorer is on the defense. We use `posteam` for team in the matchup display – defensive TDs could show the wrong team.

### 5. **Game Sync Status**

- Only `scheduled` vs `final` (no `in_progress`)
- Games with partial scores might be mid-game
- `in_progress` rarely used even if schema allows it

### 6. **Orphaned Picks**

After "Remove non-final games", `games` rows are deleted. Picks still reference those `game_id`s. Matchup page 404s when game isn’t in `games` and no picks exist; with picks we can show matchup but no status/TD scorers.

### 7. **Any-Time-TD Team Filter**

Grading filters `td_row['posteam'] == team_abbr`. On return TDs, `posteam` is the offense. Defensive scorers might not match team filter correctly – edge case for any-time-TD grading.

---

## Recommendations

### Short-term (Low Effort)

1. **Add `touchdowns` table** – Materialize TD scorers when games become final:
   - `(game_id, player_name, team, is_first_td, play_id)`
   - Populate during game sync or a post-sync job for final games
   - Matchup page reads from DB instead of recomputing

2. **Fix `posteam` for return TDs** – Use `defteam` or a conditional: if `return_touchdown == 1`, the scorer’s team is the one that scored (opposite of `posteam` on INT/fumble returns).

3. **Validate game_id format** – Normalize or reject early if format doesn’t match expected pattern.

### Medium-term (Schema + Pipeline)

4. **Single sync pipeline** – One job that:
   - Syncs games (schedules)
   - Syncs rosters
   - For final games: derives TDs from PBP and writes to `touchdowns`
   - Ensures games, TDs, and grading all use same PBP snapshot

5. **Soft-delete games** – Mark games as `deleted` instead of removing them, so picks stay valid and we can still show historical matchups.

6. **`in_progress` support** – When syncing, set `in_progress` when scores exist but game isn’t final.

### Long-term (Architecture)

7. **Data contract layer** – Validate nflreadpy output (columns, types, game_id format) before use.

8. **Event sourcing for grading** – Store “TD occurred” events with sources; re-grade by replaying events.

---

## Schema Additions (Proposed)

### `touchdowns` table (optional migration)

```sql
CREATE TABLE touchdowns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    player_name TEXT NOT NULL,
    team TEXT NOT NULL,
    is_first_td BOOLEAN DEFAULT 0,
    play_id INTEGER,
    season INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id),
    UNIQUE(game_id, play_id)
);
CREATE INDEX idx_touchdowns_game ON touchdowns(game_id);
CREATE INDEX idx_touchdowns_season ON touchdowns(season);
```

Populate when game sync marks a game as final; backfill from PBP for existing final games.

---

## Next Steps

1. Decide whether to add `touchdowns` table now or keep on-the-fly computation.
2. Fix `posteam` for return TDs in display and grading.
3. Schedule a sync job (cron/admin) that keeps games, rosters, and TDs in sync.
4. Add integration tests that load real nflreadpy data and assert TD scorer correctness for known games.
