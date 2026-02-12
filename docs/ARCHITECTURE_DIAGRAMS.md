# Fast6 Architecture: Data Flow & Schema

Diagrams use [Mermaid](https://mermaid.js.org/). Render in VS Code, GitHub, or any Mermaid-compatible viewer.

**→ [OPTIMIZATION_ROADMAP.md](./OPTIMIZATION_ROADMAP.md)** – Target architecture & optimization plan

---

## 1. Data Flow

```mermaid
flowchart TB
    subgraph External["External Sources"]
        nflread["nflreadpy API"]
    end

    subgraph Nflread["nflreadpy Functions"]
        load_sched["load_schedules()"]
        load_rosters["load_rosters()"]
        load_pbp["load_pbp()"]
    end

    subgraph Sync["Admin Sync (manual)"]
        game_sync["Sync Games"]
        roster_sync["Sync Rosters"]
        td_sync["Sync Touchdowns"]
    end

    subgraph DB["SQLite Database"]
        games["games"]
        rosters["rosters"]
        touchdowns["touchdowns"]
        users["users"]
        weeks["weeks"]
        picks["picks"]
        results["results"]
        player_stats["player_stats"]
        team_ratings["team_ratings"]
    end

    subgraph OTF["On-the-Fly (fallback)"]
        td_cache["TDLookupCache"]
    end

    subgraph Consumers["API / Frontend"]
        matchup["Matchup Page"]
        leaderboard["Leaderboard"]
        grading["Auto-Grade"]
        analytics["Analytics"]
    end

    nflread --> load_sched
    nflread --> load_rosters
    nflread --> load_pbp

    load_sched --> game_sync
    load_rosters --> roster_sync
    load_pbp --> td_sync
    game_sync --> games
    roster_sync --> rosters
    td_sync --> touchdowns

    touchdowns --> matchup
    touchdowns --> analytics
    td_cache --> grading

    games --> matchup
    games --> analytics
    picks --> matchup
    picks --> leaderboard
    picks --> grading
    results --> leaderboard
    results --> grading
    player_stats --> analytics
    team_ratings --> analytics
```

---

## 2. Data Flow (Simplified)

```mermaid
flowchart LR
    subgraph Sources["Sources"]
        S1["nflreadpy\nschedules"]
        S2["nflreadpy\nrosters"]
        S3["nflreadpy\nplay-by-play"]
    end

    subgraph Storage["Storage"]
        DB["SQLite DB"]
        CACHE["Memory Cache\n5 min TTL"]
    end

    subgraph Sinks["Consumers"]
        M["Matchup"]
        L["Leaderboard"]
        G["Grading"]
        A["Analytics"]
    end

    S1 -->|"sync_games"| DB
    S2 -->|"sync_rosters"| DB
    S3 -->|"sync_touchdowns"| DB
    S3 -->|"fallback"| CACHE
    CACHE --> G
    DB --> M
    DB --> L
    DB --> G
    DB --> A
```

---

## 3. Database Schema (ERD)

```mermaid
erDiagram
    users ||--o{ picks : "makes"
    weeks ||--o{ picks : "contains"
    picks ||--o| results : "graded"
    games ||--o{ picks : "game_id"
    picks }o--o| games : "game_id"

    users {
        int id PK
        string name
        string email
        int group_id
        bool is_admin
    }

    weeks {
        int id PK
        int season
        int week
        timestamp started_at
        timestamp ended_at
    }

    picks {
        int id PK
        int user_id FK
        int week_id FK
        string team
        string player_name
        float odds
        float theoretical_return
        string game_id
    }

    results {
        int id PK
        int pick_id FK "UNIQUE"
        string actual_scorer
        bool is_correct
        bool any_time_td
        float actual_return
    }

    games {
        string id PK
        int season
        int week
        date game_date
        string home_team
        string away_team
        int home_score
        int away_score
        string status
    }

    rosters {
        int id PK
        int season
        string player_name
        string team
        string position
    }

    player_stats {
        int id PK
        string player_name
        int season
        string team
        int first_td_count
        int any_time_td_count
    }

    team_ratings {
        int id PK
        string team
        int season
        int week
        float elo_rating
    }

    kickoff_decisions {
        int id PK
        string game_id
        string team
        string decision
    }

    market_odds {
        int id PK
        string source
        string game_id
        string player_name
        float implied_probability
    }

    touchdowns {
        int id PK
        string game_id
        string player_name
        string team
        bool is_first_td
        int play_id
        int season
    }

    games ||--o{ kickoff_decisions : "game_id"
    games ||--o{ touchdowns : "game_id"
```

---

## 4. Core Tables (Simplified)

```mermaid
flowchart TB
    subgraph Core["Core Domain"]
        U["users"]
        W["weeks"]
        P["picks"]
        R["results"]
    end

    subgraph NFL["NFL Data"]
        G["games"]
        ROS["rosters"]
    end

    subgraph Derived["Derived / Analytics"]
        PS["player_stats"]
        TR["team_ratings"]
    end

    U -->|user_id| P
    W -->|week_id| P
    P -->|game_id| G
    P -->|pick_id| R
    P -->|triggers| PS
    G -->|triggers| TR
```

---

## 5. Matchup Page Data Flow

```mermaid
sequenceDiagram
    participant F as Frontend
    participant API as API
    participant DB as Database
    participant NFL as nflreadpy

    F->>API: GET /matchup/{game_id}

    API->>DB: SELECT status FROM games
    API->>DB: SELECT picks + results (grouped by team)

    alt Has picks
        API->>API: Build teams from picks
    else No picks
        API->>DB: SELECT home_team, away_team FROM games
        API->>API: Build empty teams
    end

    alt Game status = final
        API->>NFL: load_pbp(season)
        API->>NFL: get_touchdowns(df)
        API->>API: Filter by game_id
        API->>API: Extract td_scorers
    end

    API->>F: { teams, status, td_scorers }
```

---

## 6. Grading Pipeline

```mermaid
flowchart LR
    subgraph Input["Input"]
        P["Ungraded picks"]
        NFL["nflreadpy PBP"]
    end

    subgraph Process["Process"]
        TD["get_touchdowns()"]
        FC["First TD per game"]
        AT["Any-time TD check"]
        NM["Name matching"]
    end

    subgraph Output["Output"]
        R["results table"]
    end

    NFL --> TD
    TD --> FC
    TD --> AT
    P --> FC
    P --> AT
    FC --> NM
    AT --> NM
    NM --> R
```

---

## Viewing These Diagrams

- **VS Code**: Install "Markdown Preview Mermaid Support" extension
- **GitHub**: Diagrams render automatically in `.md` files
- **Online**: [Mermaid Live Editor](https://mermaid.live/)
