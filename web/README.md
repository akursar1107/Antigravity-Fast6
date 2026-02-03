# Fast6 Web Frontend

Next.js frontend for the Fast6 NFL first touchdown scorer prediction app. Provides a modern, responsive interface for managing picks, viewing leaderboards, and analyzing performance across the league.

## Features

- **Leaderboard**: Real-time rankings of players and groups across seasons
- **Analytics**: Advanced performance tracking with ELO ratings and ROI analysis
- **Week Picks**: Submit and manage first touchdown scorer predictions
- **Matchup Analysis**: Defense/offense analysis and prediction market data
- **Player Stats**: Individual player performance history and trends
- **Admin Dashboard**: Manage users, grade picks, and configure settings

## Prerequisites

- **Node.js 18+** (check with `node --version`)
- **npm** or **yarn** package manager
- **Python backend running** (Fast6 API at `http://localhost:8000`)

## Installation

### 1. Clone or checkout the worktree
```bash
# If using git worktree
cd /var/home/akursar/Documents/Year\ of\ Vibe/1.\ Jan/Fast6/.worktrees/nextjs-frontend

# Or checkout the branch directly
git checkout nextjs-frontend
```

### 2. Navigate to web directory
```bash
cd web
```

### 3. Install dependencies
```bash
npm install
# or
yarn install
```

### 4. Setup environment variables
```bash
# Copy example to local config
cp .env.local.example .env.local

# Edit .env.local if needed (update API_BASE_URL if running on different host)
# Default: NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 5. Start development server
```bash
npm run dev
# or
yarn dev
```

Access the application at **http://localhost:3000**

## Development

### Available Scripts

```bash
# Start development server (with hot reload)
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run tests in watch mode
npm run test

# Run tests once (for CI/CD)
npx vitest run --watch=false

# Lint code
npm run lint

# Format code with Prettier
npm run format
```

## Running Tests

### Local development
```bash
npm run test
```
Runs Vitest in watch mode. Tests re-run on file changes.

### CI/CD pipelines
```bash
npx vitest run --watch=false
```
Runs tests once and exits.

## Troubleshooting

### Error: "API not responding"
- Ensure Python backend is running: `streamlit run Fast6/src/app.py`
- Check `NEXT_PUBLIC_API_BASE_URL` in `.env.local` matches backend host
- Verify backend is accessible: `curl http://localhost:8000/health` (if endpoint exists)

### Error: "Port 3000 already in use"
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or run on different port
PORT=3001 npm run dev
```

### Build fails with "Module not found"
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run build
```

### Environment variables not loading
- Ensure `.env.local` exists (not `.env.local.example`)
- Variables must start with `NEXT_PUBLIC_` to be exposed to browser
- Restart dev server after changing `.env.local`

## Project Structure

```
web/
├── src/
│   ├── app/               # Next.js App Router pages
│   ├── components/        # Reusable React components
│   ├── lib/              # Utility functions and helpers
│   ├── hooks/            # Custom React hooks
│   └── styles/           # Global styles and CSS modules
├── public/               # Static assets
├── tests/                # Test files (Vitest)
├── .env.local.example    # Environment variables template
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── next.config.js        # Next.js configuration
└── vitest.config.ts      # Vitest configuration
```

## Backend API Integration

The frontend communicates with the Fast6 backend API running on port 8000.

### Required Backend Endpoints
- `GET /api/leaderboard` - Fetch leaderboard data
- `GET /api/picks/:week` - Fetch picks for a week
- `POST /api/picks` - Submit new pick
- `GET /api/analytics/:user_id` - Fetch user analytics
- `GET /api/market-odds` - Fetch prediction market odds

Refer to [Fast6 Backend API Documentation](../docs/ARCHITECTURE.md) for complete endpoint specifications.

## Performance

- **Static Generation**: Pages are pre-rendered at build time where possible
- **Incremental Static Regeneration (ISR)**: Pages update without rebuilding entire app
- **Client Caching**: Browser caches stable data (leaderboard, historical stats)
- **API Caching**: Backend caches expensive computations (ELO ratings, analytics)

## Deployment

See [NEXTJS_DEPLOYMENT.md](../docs/plans/NEXTJS_DEPLOYMENT.md) for production deployment guide.

## Contributing

1. Create feature branch from `nextjs-frontend`
2. Make changes and test locally
3. Run `npm run build` to verify production build
4. Submit pull request with clear description

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [Fast6 Backend Documentation](../docs/README.md)
3. Open GitHub issue with reproduction steps
