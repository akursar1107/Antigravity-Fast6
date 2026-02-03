# Next.js Frontend Deployment Guide

Production deployment guide for the Fast6 Next.js frontend.

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

## Docker Deployment

### Build Docker Image

```dockerfile
# Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY next.config.js ./

EXPOSE 3000
ENV NODE_ENV=production

CMD ["npm", "start"]
```

### Run Docker Container

```bash
# Build image
docker build -t fast6-web:latest .

# Run container
docker run -d \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_BASE_URL=https://api.fast6.app \
  -e NEXT_PUBLIC_CURRENT_SEASON=2025 \
  --name fast6-web \
  fast6-web:latest

# View logs
docker logs -f fast6-web

# Stop container
docker stop fast6-web
docker rm fast6-web
```

## Railway Deployment

### Prerequisites
- GitHub repository with Next.js code
- Railway account (railway.app)
- Backend API already deployed

### Option 1: GitHub Integration (Recommended)

1. Push code to GitHub:
```bash
git push origin nextjs-frontend
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
   - Railway auto-deploys on push to main branch
   - Or manually trigger from Railway dashboard

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
