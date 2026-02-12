# Fast6 Deployment Guide

Production deployment for the Fast6 platform: **FastAPI backend** + **Next.js frontend**.

---

## Backend (FastAPI)

The project `Dockerfile` and `railway.json` deploy the **backend only**. The Next.js app is built during the Docker image build but not served by the container.

### Docker

```bash
docker build -t fast6 .
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data fast6
```

- Mount a volume at `/app/data` for persistent SQLite
- Set `DATABASE_PATH`, `SECRET_KEY`, `CORS_ORIGINS` via `-e` if needed

### Railway

1. Connect repo at [railway.app](https://railway.app)
2. Railway uses `railway.json` and the Dockerfile
3. **Required env vars:**
   - `DATABASE_PATH` — `/app/data/fast6.db` (or path to mounted volume)
   - `SECRET_KEY` — secure random string
   - `CORS_ORIGINS` — comma-separated frontend URLs (e.g. `https://your-app.vercel.app`)
4. Add a **volume** at `/app/data` for persistent storage

---

## Frontend (Next.js)

Deploy the frontend separately (Vercel, Railway, etc.) and set `NEXT_PUBLIC_API_BASE_URL` to your backend URL.

## Building for Production

### Local Build
```bash
cd web

# Install dependencies
npm ci  # Use ci instead of install for reproducible builds

# Build for production
npm run build

# Start production server locally
npm run start
```

The build output is in `.next/` directory.

### Build Verification
```bash
# Check build completed successfully
ls -la .next/

# Start and test production server
npm run start
# Access at http://localhost:3000
```

## Environment Variables

### Required for Production

```env
# API Configuration - MUST match backend URL
NEXT_PUBLIC_API_BASE_URL=https://api.fast6.app

# Application Settings
NEXT_PUBLIC_CURRENT_SEASON=2025

# Optional: Monitoring/Analytics
NEXT_PUBLIC_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

**Note**: All variables must start with `NEXT_PUBLIC_` to be accessible in browser.

### Setup Production Environment

1. Create `.env.production.local` (gitignored):
```bash
cp .env.local.example .env.production.local
```

2. Update values for production:
```env
NEXT_PUBLIC_API_BASE_URL=https://api.fast6.app
NEXT_PUBLIC_CURRENT_SEASON=2025
```

## Frontend Docker (Optional)

To run the Next.js app in its own container:

```dockerfile
# Dockerfile.web (example - create in web/ or use root with -f)
FROM node:20-slim AS builder
WORKDIR /app
COPY web/package*.json ./
RUN npm ci
COPY web/ .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
ENV NODE_ENV=production
EXPOSE 3000
CMD ["node", "server.js"]
```

Requires `output: "standalone"` in `next.config.ts` (already set).

## Railway Deployment

### Prerequisites
- GitHub repository with Next.js code
- Railway account (railway.app)
- Backend API already deployed

### Option 1: GitHub Integration (Recommended)

1. Push code to GitHub:
```bash
git push origin main
```

2. In Railway dashboard:
   - Click "New Project" → "Deploy from GitHub repo"
   - Select Fast6 repository
   - Select `web` as root directory
   - Configure environment variables

3. Environment Variables in Railway:
   ```
   NODE_ENV = production
   NEXT_PUBLIC_API_BASE_URL = https://fast6-api.up.railway.app
   NEXT_PUBLIC_CURRENT_SEASON = 2025
   ```

4. Deploy:
   - Railway auto-deploys on push to connected branch
   - Or manually trigger from Railway dashboard

**Note:** The backend uses the root `Dockerfile` (FastAPI). For frontend-only, set root directory to `web` and use Nixpacks or a separate Dockerfile.

### Option 2: Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
cd web
railway init

# Set environment variables
railway variables set NEXT_PUBLIC_API_BASE_URL=https://fast6-api.up.railway.app
railway variables set NEXT_PUBLIC_CURRENT_SEASON=2025

# Deploy
railway up
```

## Vercel Deployment

### Option 1: GitHub Integration

1. Connect GitHub repo to Vercel at vercel.com
2. Import project:
   - Framework: Next.js
   - Root directory: `web`
3. Environment variables:
   ```
   NEXT_PUBLIC_API_BASE_URL = https://fast6-api.production.com
   NEXT_PUBLIC_CURRENT_SEASON = 2025
   ```
4. Deploy

### Option 2: CLI

```bash
npm install -g vercel

# Deploy
vercel

# Set environment for production
vercel env add NEXT_PUBLIC_API_BASE_URL
vercel env add NEXT_PUBLIC_CURRENT_SEASON
```

## Production Checklist

- [ ] Build completes without errors: `npm run build`
- [ ] Environment variables configured for production API
- [ ] Backend API accessible from production frontend
- [ ] CORS enabled on backend (if frontend on different domain)
- [ ] SSL/TLS certificate configured
- [ ] Monitoring/logging setup (Sentry, etc.)
- [ ] Performance baseline established (Lighthouse)
- [ ] Database backups tested
- [ ] Error handling working (404, 500 pages)
- [ ] Analytics/tracking configured if needed

## Monitoring Production

### Health Checks

```bash
# Check frontend is responding
curl https://fast6-frontend.app/

# Check API connectivity
curl https://fast6-api.app/health
```

### Performance Monitoring

- Use Vercel/Railway built-in analytics
- Enable Sentry for error tracking
- Monitor API response times from backend logs

### Common Issues

| Issue | Solution |
|-------|----------|
| 504 Gateway Timeout | Backend API not responding; check API deployment |
| CORS errors | Enable CORS on backend for frontend domain |
| Variables undefined | Ensure `NEXT_PUBLIC_` prefix; restart deployment |
| Build fails | Check Node.js version matches (18+); clear cache |
| Port conflicts | Use different port or kill existing process |

## Scaling

### For High Traffic

1. **CDN**: Use Vercel/Railway CDN for static assets
2. **Caching**: Increase ISR revalidation times
3. **Database**: Implement read replicas on backend
4. **Load Balancing**: Both services support auto-scaling

### Database Connection Pooling

Backend should implement connection pooling for SQLite/PostgreSQL to handle concurrent frontend requests.

## Security

- [ ] Never commit `.env.local` or `.env.production.local`
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS only in production
- [ ] Set secure cookie flags
- [ ] Implement rate limiting on backend API
- [ ] Validate all user input on backend
- [ ] Keep dependencies updated: `npm audit fix`

## Rollback

```bash
# Vercel: Automatic with GitHub integration
# Simply push previous commit to main

# Railway/Docker: Tag images with version
docker tag fast6-web:latest fast6-web:v1.0.0
docker push fast6-web:v1.0.0

# Revert to previous version in deployment
```

## References

- [Next.js Production Checklist](https://nextjs.org/docs/going-to-production)
- [Deployment Documentation](https://nextjs.org/docs/deployment)
- [Vercel Deployment](https://vercel.com/docs/frameworks/nextjs)
- [Railway Documentation](https://docs.railway.app/)
