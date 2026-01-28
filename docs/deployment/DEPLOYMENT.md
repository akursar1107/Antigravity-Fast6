# Deployment Guide: Fast6 NFL TD Tracker

Because this is a **Streamlit** app, the easiest way to share it with friends is using **Streamlit Community Cloud**. It's free, handles the hosting for you, and automatically updates when you push code to GitHub.

---

## Current Status

**Phase 1 Complete ✅ | Phase 2 In Progress 🚀**

The app is production-ready with:
- 6-tab admin interface (User Mgmt, Pick Input, Update Results, View Stats, Import CSV, Grade Picks)
- 6-tab public dashboard (Leaderboard, Weekly Picks, All TDs, Schedule, Analysis, First TD per Game)
- SQLite database with game_id tracking
- CSV import with Home/Visitor team matching
- Auto-grading using NFL PBP data

---

## Prerequisite: Install Git

Your system currently doesn't have `git` installed.
*   **Linux (Debian/Ubuntu)**: `sudo apt-get install git`
*   **Mac**: `brew install git`
*   **Windows**: Download from [git-scm.com](https://git-scm.com/downloads)

---

## Step 1: Push to GitHub

1.  **Create a new Repository** on [GitHub.com](https://github.com/new).
    *   Name it `fast6` or `nfl-td-tracker` (or similar).
    *   Make it **Public** (easiest) or **Private** (requires more setup).
    *   **Do NOT** initialize with README or .gitignore (we already have them).

2.  **Upload your Code**:
    Open your terminal in the project folder and run:
    ```bash
    git init
    git add .
    git commit -m "Phase 1 complete: Database, Admin, Dashboard, Grade Picks"
    git branch -M main
    git remote add origin https://github.com/YOUR_USERNAME/fast6.git
    git push -u origin main
    ```

---

## Step 2: Deploy to Streamlit Cloud

1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Click **"New app"**.
3.  Select your new GitHub repository (`fast6`).
4.  **Main file path**: `src/app.py`.
5.  Click **"Deploy!"**.

---

## Step 3: Configure Secrets (Crucial!)

Your app uses an API Key for odds. You must set this securely in the cloud.

1.  On your deployed app dashboard, go to **Settings** -> **Secrets**.
2.  Paste the contents of your secure configuration:
    ```toml
    odds_api_key = "11d265853d712ded110d5e0a5ff82c5b"
    ```
3.  `src/config.py` already uses `st.secrets` to load this value securely.

---

## Step 4: Database Considerations

**Important**: SQLite is file-based, so the database (`data/fast6.db`) is stored in the repo. When you deploy to Streamlit Cloud, the database file will be part of your deployment.

### Recommended Approach
- **Keep `fast6.db` in `.gitignore`** for local development
- **Upload clean database** with production data to GitHub before deployment
- **Backup database regularly** by downloading from deployed app or using git commits

### Future Migration
For production scale, consider migrating to PostgreSQL or another cloud database service.

---

## Step 5: Share with Friends

Once deployed, Streamlit Cloud provides a public URL like:
```
https://YOUR_USERNAME-fast6-srcapp-abc123.streamlit.app/
```

Share this URL with your friends. They can view the public dashboard without needing accounts or passwords.

---

## Updating the App

Whenever you push changes to GitHub, Streamlit Cloud auto-deploys:
```bash
git add .
git commit -m "Add point system feature"
git push
```

The app will automatically rebuild and redeploy.

---

## Troubleshooting

### Issue: "Module not found" errors
- Check `requirements.txt` includes all dependencies
- Verify correct package versions (e.g., `nflreadpy==0.1.5`)

### Issue: Database not persisting
- SQLite files are ephemeral on Streamlit Cloud
- Consider using Streamlit session state or external database for persistence

### Issue: API key not working
- Verify secrets are configured correctly in Settings -> Secrets
- Check `config.py` uses `st.secrets["odds_api_key"]`

### Issue: Slow load times
- Caching is enabled with 5-min TTL
- PBP data loads on demand, not at startup
- Consider adding progress bars for long operations

---

## Security Notes

- **API Keys**: Never commit API keys to GitHub; use Streamlit secrets
- **Database**: SQLite file in repo is visible to anyone with access
- **Admin Access**: Currently no authentication; consider adding light auth for production

---

## Next Steps

See [TODO.md](TODO.md) for upcoming features:
- Drop database and fresh import
- Point system for First TD and Anytime TD scorers
- Codebase refactoring

See [ROADMAP.md](ROADMAP.md) for long-term plans.
