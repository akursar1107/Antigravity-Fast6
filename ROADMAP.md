# NFL Touchdown Tracker - Future Roadmap

This document outlines potential next steps to elevate the NFL Touchdown Tracker from a personal prototype to a production-grade application.

## 1. Infrastructure & Backend (High Impact)
Currently, the app relies on in-memory data and `st.session_state`, which limits scalability and persistence.

*   **Database Integration (SQLite / PostgreSQL)**
    *   **Goal**: Persist user predictions and history across sessions.
    *   **Implementation**: Use `sqlite3` (local) or `PostgreSQL` (cloud) to store `UserPredictions`, `Games`, and `Odds` tables.
    *   **Feature Unlock**: "My History" tab to track ROI and profitability over the season.

*   **Containerization (Docker)**
    *   **Goal**: Ensure consistent environments across development and production.
    *   **Implementation**: Create a `Dockerfile` to package the app and dependencies.

*   **Automated Data Pipeline**
    *   **Goal**: Reduce load times and reliance on on-demand fetching.
    *   **Implementation**: GitHub Actions or Cron jobs to fetch `nflreadpy` data weekly/daily and save to stable storage (DB or S3).

## 2. Advanced Analysis Features ("The Edge")
Tools to help users identify betting value.

*   **Implied Probability vs. Actual Rate**
    *   **Goal**: Highlight +EV (Positive Expected Value) bets.
    *   **Implementation**: Compare a player's historical "First TD Rate" (e.g., 20%) against current Odds Implied Probability (e.g., +400 = 20%). Show a "Value" indicator when Actual > Implied.

*   **Defensive Matchup Analysis**
    *   **Goal**: Contextualize picks based on opponent weakness.
    *   **Implementation**: "Defense vs Position" stats (e.g., "The Bears allow the First TD to a RB 65% of the time").

## 3. User Experience & Gamification
*   **User Profiles (Lightweight vs Auth)**
    *   **Constraint**: Full authentication adds significant complexity (session management, security, cookies).
    *   **Alternative**: **Simple Name Selector**.
    *   **Implementation**: A dropdown config `["User A", "User B"]` in `config.py`. Users just pick their name at the start.
    *   **Benefit**: Zero friction, no passwords to manage, still enables history tracking and leaderboards (on the honor system).

*   **Leaderboard**
    *   **Goal**: Gamify the experience.
    *   **Implementation**: Track and rank users by correct picks or theoretical profit.

## 4. DevOps & Code Quality
*   **CI/CD Pipeline**
    *   **Goal**: Prevent bugs from reaching main branch.
    *   **Implementation**: Github Actions to run `tests/` on every push.
    *   **Actions**: Run `python -m unittest`, `black` (formatting), and `ruff` (linting).
