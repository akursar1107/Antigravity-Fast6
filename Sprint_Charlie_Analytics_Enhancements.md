# Sprint Charlie – First TD Analytics Enhancements

**Project:** Fast6 – NFL First TD Prediction Tool  
**Sprint:** Charlie  
**Created:** [Insert Date]  
**Status:** Planning  
**Inspiration:** NFL Analytics Research

---

## Executive Summary

This sprint will introduce advanced analytics to improve first touchdown scorer predictions. The focus is on team and player tendencies, drive efficiency, and red zone performance, providing actionable insights for both admins and users.

**Expected Outcomes:**
- Deeper context for first TD picks
- New dashboard analytics tabs and visualizations
- Enhanced player and team stats for pick strategy

---

## 📊 Phase 1: Team & Drive Tendencies (Priority: HIGH)

**Timeline:** 2-3 days  
**Effort:** Medium  
**Impact:** High

### Task 1.1: Track Opening Kickoff Decisions
- [ ] Add data field for whether a team elects to receive or defer on opening kickoff
- [ ] Aggregate and display team tendencies (receive %, defer %, score on first drive %)
- [ ] Visualize in a new dashboard tab

### Task 1.2: Team First TD Record
- [ ] Calculate and display each team’s record for scoring the first TD (season and historical)
- [ ] Add sortable table to analytics dashboard

### Task 1.3: Scoring Splits
- [ ] Break down first TDs by type (passing, rushing, other)
- [ ] Show splits for in/out of red zone
- [ ] Add to team and player analytics views

---

## 📈 Phase 2: Drive Efficiency & Player Stats (Priority: HIGH)

**Timeline:** 3-4 days  
**Effort:** Medium  
**Impact:** High

### Task 2.1: First Drive Efficiency
- [ ] Calculate first drive scoring rates (offense and defense) for all teams
- [ ] Add stats for first 15 plays (scripted drives)
- [ ] Visualize with bar charts and leaderboards

### Task 2.2: Player First TD Leaders
- [ ] Aggregate first TDs by player per team and league-wide
- [ ] Add red zone targets/carries for top candidates
- [ ] Display in player analytics tab

### Task 2.3: First Drive Success Rates
- [ ] Calculate and display rushing/passing success rates on first drives (offense and defense)
- [ ] Add to team analytics and matchup previews

---

## 🛠️ Phase 3: Integration & Visualization (Priority: MEDIUM)

**Timeline:** 2 days  
**Effort:** Medium  
**Impact:** Medium

### Task 3.1: Data Integration
- [ ] Update data ingestion to support new fields (kickoff decision, drive stats, red zone stats)
- [ ] Ensure compatibility with existing grading and dashboard logic

### Task 3.2: UI/UX Enhancements
- [ ] Add new analytics tabs to dashboard
- [ ] Create visualizations (tables, bar charts, heatmaps) for all new metrics
- [ ] Write tooltips and documentation for new analytics

---

## 📋 Deliverables

- New/updated modules: `src/utils/analytics.py`, `src/views/tabs/analysis.py`, etc.
- Dashboard tabs: Team Tendencies, Player Stats, Drive Efficiency
- Documentation updates in `README.md` and analytics guide

---

## 🚦 Success Criteria

- All new analytics visible and interactive in the dashboard
- Data updates automatically with each new week/season
- Unit tests for new analytics functions
- User feedback collected for further improvements

---