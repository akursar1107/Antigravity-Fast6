# Deployment Guide: NFL TD Tracker

Because this is a **Streamlit** app, the easiest way to share it with friends is using **Streamlit Community Cloud**. It's free, handles the hosting for you, and automatically updates when you push code to GitHub.

## Prerequisite: Install Git
Your system currently doesn't have `git` installed.
*   **Linux (Debian/Ubuntu)**: `sudo apt-get install git`
*   **Mac**: `brew install git`
*   **Windows**: Download from [git-scm.com](https://git-scm.com/downloads)

## Step 1: Push to GitHub
1.  **Create a new Repository** on [GitHub.com](https://github.com/new).
    *   Name it `nfl-td-tracker` (or similar).
    *   Make it **Public** (easiest) or **Private** (requires more setup).
    *   **Do NOT** initialize with README or .gitignore (we already have them).

2.  **Upload your Code**:
    Open your terminal in the project folder and run:
    ```bash
    git init
    git add .
    git commit -m "Initial commit: NFL TD Tracker App"
    git branch -M main
    git remote add origin https://github.com/YOUR_USERNAME/nfl-td-tracker.git
    git push -u origin main
    ```

## Step 2: Deploy to Streamlit Cloud
1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Click **"New app"**.
3.  Select your new GitHub repository (`nfl-td-tracker`).
4.  **Main file path**: `src/app.py`.
5.  Click **"Deploy!"**.

## Step 3: Configure Secrets (Crucial!)
Your app uses an API Key for odds. You must set this securely in the cloud.
1.  On your deployed app dashboard, go to **Settings** -> **Secrets**.
2.  Paste the contents of your secure configuration:
    ```toml
    [secrets]
    odds_api_key = "11d265853d712ded110d5e0a5ff82c5b"
    ```
3.  Update your `src/config.py` to use `st.secrets` if you haven't yet, or just hardcode it for now (less secure but works for private dashboards).
