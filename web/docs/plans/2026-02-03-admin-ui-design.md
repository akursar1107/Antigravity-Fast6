# Admin UI parity plan (Next.js)

## Goal
Bring the Next.js frontend to parity with the Streamlit admin interface using existing FastAPI endpoints. Do not write directly to the database from the frontend.

## Scope
Admin tabs to implement:
- Dashboard
- Users
- Picks
- Results/Grading
- Settings/Tools (CSV import, roster sync, reset picks)

## Routing and auth
Create an /admin area with its own nav. All admin calls require an admin JWT. Use the server token helper for SSR and surface errors as a consistent banner. The admin username comes from NEXT_PUBLIC_TEST_USERNAME during development. For production, replace with real login flow.

## Data sources
Admin router:
- GET /api/admin/stats
- GET /api/admin/logs
- POST /api/admin/batch-grade
- POST /api/admin/csv-import
- POST /api/admin/sync-rosters
- POST /api/admin/user-reset

Admin-only routes in other routers:
- POST /api/users
- PATCH /api/users/{user_id}
- DELETE /api/users/{user_id}
- POST /api/weeks
- POST /api/results
- GET /api/results/ungraded/list

Admin-privileged access:
- GET /api/picks (all picks)
- DELETE /api/picks/{pick_id}
- GET /api/results?week_id=...

## UI behavior
Dashboard
- KPI grid: total users, total picks, graded, ungraded, grading percent.
- Activity summary card from /api/admin/logs.
- Quick links to Tools.

Users
- Table with name, email, admin flag.
- Actions: edit, toggle admin, delete.
- Confirm destructive actions and block deleting self.

Picks
- Filters for week and user.
- Table for user, team, player, odds, game.
- Delete pick action for admin.

Results/Grading
- Ungraded list by week.
- Inline grading inputs (correct, any-time, actual scorer).
- Batch submit via /api/admin/batch-grade.
- Read-only view of graded results.

Settings/Tools
- CSV import with file upload and optional week.
- Sync rosters by season.
- Reset user picks by user and optional week.

## Error handling
Show a single banner component for API errors. For destructive actions, show confirmation and clear success messaging. Keep all API errors surfaced to the admin.

## Testing
- Verify all admin pages load with a known admin user.
- Confirm each action hits the correct endpoint and updates UI state.
- Validate auth errors return "Admin access required" and display cleanly.

## Out of scope
- New backend endpoints
- Direct DB access from the frontend
- Public dashboard changes
