# Phase 11: Deploy & Verify

**Current Status:** v2.0.0 Clean Architecture Complete  
**Last Updated:** February 3, 2026

## Phase 11 Task Checklist

### Pre-Deployment Verification
- [ ] Set up pytest environment
  - `pip install pytest pytest-cov`
- [ ] Run full test suite
  - `python -m pytest tests/ -v --cov=src`
- [ ] Verify no regressions

### App Verification
- [ ] Test legacy app (app.py)
  - `streamlit run src/app.py`
  - Verify login, admin ops, leaderboard
- [ ] Test new architecture (app_v2.py)
  - `streamlit run src/app_v2.py`
  - Verify entry point works

### Database Verification
- [ ] Verify database works (data/fast6.db)
- [ ] Test pick creation, grading, results
- [ ] Verify no data corruption

### Gradual View Migration
- [ ] Update view imports (one at a time)
  - Change `from database import` → `from src.api import`
  - Change `from utils import` → `from src.lib import`
  - Test each view thoroughly before next

### Production Deployment
- [ ] Deploy to production
- [ ] Monitor logs for errors
- [ ] Get team sign-off

### Post-Deployment
- [ ] Archive old code (src/views/, src/database/, src/utils/)
- [ ] Tag as v2.1.0 when fully migrated
- [ ] Update documentation

## Estimated Timeline
- Setup & Testing: 1 hour
- App Verification: 1 hour
- View Migration: 2-3 hours (gradual)
- Production Deploy: 1 hour
- **Total: 5-6 hours**

## Documentation References
- [Architecture Reference](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/deployment/DEPLOYMENT.md)
- [Completed Phases](archive/completed-phases/)

## Previous Phases
See [archive/completed-phases/](archive/completed-phases/) for historical phase documentation:
- PHASE9_TESTING_SUMMARY.md
- PHASE10_CLEANUP_MERGE.md
- CLEAN_ARCHITECTURE_STATUS.md
