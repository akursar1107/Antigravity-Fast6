# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),

## [Unreleased]

### Added
- CI/CD workflow (GitHub Actions) for backend and frontend tests
- Rate limiting on login endpoint (5 requests/minute)
- CHANGELOG.md and LICENSE

### Changed
- Pinned backend dependencies in requirements.txt for reproducible builds
- Improved production error handling (no exception details in response when debug=false)
- Config validation at startup (database path consistency)
- **Documentation**: Updated README, docs, web/README, data/README, and deployment guide for Next.js + FastAPI; Docker/Railway env vars and volume instructions
- **Dockerfile**: Health check uses `${PORT}` for Railway; `DATABASE_PATH` default; build/run notes
- **railway.json**: Formatted for readability

### Security
- Documented auth posture: username-only auth intended for private friend groups only

### Fixed
- README paths corrected for project root (project root vs Fast6 subfolder)

## [1.0.0] - 2025

- Initial release: Next.js dashboard, FastAPI backend, SQLite, NFL data integration, auto-grading, analytics
