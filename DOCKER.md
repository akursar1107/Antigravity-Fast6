# 🐳 Running Fast6 with Docker

This guide explains how to run the Fast6 NFL First TD Tracker using Docker.

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system
- (Optional) [Docker Compose](https://docs.docker.com/compose/install/) for easier management

---

## Quick Start

### 1. Build the Docker Image

```bash
cd Fast6
docker build -t fast6 .
```

### 2. Run the Container

```bash
docker run -d -p 8501:8501 --name fast6-app fast6
```

### 3. Access the App

Open your browser and go to: **http://localhost:8501**

---

## Running with Persistent Data

By default, the SQLite database is stored inside the container and will be lost when the container is removed. To persist your data:

### Option A: Volume Mount (Recommended)

```bash
# Create a directory for data
mkdir -p ./docker-data

# Run with volume mount
docker run -d \
  -p 8501:8501 \
  -v $(pwd)/docker-data:/app/data \
  --name fast6-app \
  fast6
```

### Option B: Named Volume

```bash
# Create a named volume
docker volume create fast6-data

# Run with named volume
docker run -d \
  -p 8501:8501 \
  -v fast6-data:/app/data \
  --name fast6-app \
  fast6
```

---

## Environment Variables

You can pass environment variables to configure the app:

| Variable | Description | Default |
|----------|-------------|---------|
| `ODDS_API_KEY` | API key for The Odds API | (empty) |

### Example with Environment Variables

```bash
docker run -d \
  -p 8501:8501 \
  -v $(pwd)/docker-data:/app/data \
  -e ODDS_API_KEY=your_api_key_here \
  --name fast6-app \
  fast6
```

---

## Docker Compose (Recommended)

Create a `docker-compose.yml` file for easier management:

```yaml
version: '3.8'

services:
  fast6:
    build: .
    container_name: fast6-app
    ports:
      - "8501:8501"
    volumes:
      - ./docker-data:/app/data
    environment:
      - ODDS_API_KEY=${ODDS_API_KEY:-}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Using Docker Compose

```bash
# Start the app
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the app
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

---

## Common Commands

### View Logs

```bash
docker logs -f fast6-app
```

### Stop the Container

```bash
docker stop fast6-app
```

### Remove the Container

```bash
docker rm fast6-app
```

### Rebuild After Code Changes

```bash
docker build -t fast6 . --no-cache
docker stop fast6-app
docker rm fast6-app
docker run -d -p 8501:8501 -v $(pwd)/docker-data:/app/data --name fast6-app fast6
```

### Access Container Shell (Debugging)

```bash
docker exec -it fast6-app /bin/bash
```

---

## Troubleshooting

### Port Already in Use

If port 8501 is in use, change the host port:

```bash
docker run -d -p 8080:8501 --name fast6-app fast6
# Access at http://localhost:8080
```

### Container Keeps Restarting

Check the logs for errors:

```bash
docker logs fast6-app
```

### Database Issues

If you're having database issues, you can reset the database:

```bash
# Stop container
docker stop fast6-app

# Remove the database file
rm -rf ./docker-data/fast6.db

# Start container (will recreate database)
docker start fast6-app
```

### Memory Issues

If the container runs out of memory, increase the limit:

```bash
docker run -d \
  -p 8501:8501 \
  --memory=2g \
  --name fast6-app \
  fast6
```

---

## Production Deployment

For production deployments, consider:

1. **Use HTTPS** - Put a reverse proxy (nginx, Traefik) in front
2. **Set resource limits** - `--memory` and `--cpus` flags
3. **Use secrets** - Docker secrets or external secret management
4. **Enable logging** - Configure log drivers for monitoring
5. **Regular backups** - Backup the data volume regularly

### Example Production Command

```bash
docker run -d \
  -p 8501:8501 \
  -v fast6-data:/app/data \
  -e ODDS_API_KEY=$ODDS_API_KEY \
  --memory=1g \
  --cpus=1 \
  --restart=unless-stopped \
  --name fast6-app \
  fast6
```

---

## Free Hosting Options

### Streamlit Community Cloud (Easiest)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Select `src/app.py` as the main file
5. Add secrets in the dashboard settings

⚠️ **Note**: SQLite data is NOT persistent on Streamlit Cloud.

### Fly.io (~$2/month with persistent data)

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Launch app
fly launch

# Create volume for data persistence
fly volumes create fast6_data --size 1

# Deploy
fly deploy
```

### Railway.app (Free tier available)

1. Connect GitHub repo at [railway.app](https://railway.app)
2. Railway auto-detects the Dockerfile
3. Set environment variables in dashboard
4. Deploy automatically on git push

---

## Need Help?

- Check the main [README.md](README.md) for app documentation
- Review [config.json.example](config.json.example) for configuration options
- Open an issue on GitHub for bugs or feature requests
