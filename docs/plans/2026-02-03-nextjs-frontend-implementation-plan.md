# Next.js Frontend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a public, dark-mode Next.js dashboard that reads Fast6 data from FastAPI.

**Architecture:** A Next.js App Router app under `web/` with client-side data fetching via a typed API wrapper and shared UI components. No auth or server-side rendering in v1.

**Tech Stack:** Next.js (App Router, TypeScript), Tailwind CSS, Recharts, Vitest + React Testing Library.

---

### Task 1: Scaffold the Next.js app

**Files:**
- Create: `web/` (Next.js app)

**Step 1: Create the app**

Run:
```
cd /var/home/akursar/Documents/Year of Vibe/1. Jan/Fast6/.worktrees/nextjs-frontend
npx create-next-app@latest web --ts --app --src-dir --eslint --tailwind
```
Expected: `web/` created with `app/`, `src/`, `tailwind.config.*`, and `package.json`.

**Step 2: Run dev server once**

Run:
```
cd web
npm run dev
```
Expected: App boots with default page.

**Step 3: Commit**

```
git add web
git commit -m "feat(web): scaffold Next.js app"
```

---

### Task 2: Base layout + theme shell

**Files:**
- Modify: `web/src/app/layout.tsx`
- Modify: `web/src/app/page.tsx`
- Create: `web/src/components/layout/DashboardLayout.tsx`
- Create: `web/src/components/ui/*` (card, badge, skeleton, error banner)

**Step 1: Write failing test**

Create `web/src/components/layout/__tests__/DashboardLayout.test.tsx`:
```tsx
import { render, screen } from "@testing-library/react";
import DashboardLayout from "../DashboardLayout";

test("renders nav and content area", () => {
  render(
    <DashboardLayout>
      <div>Content</div>
    </DashboardLayout>
  );
  expect(screen.getByText(/Fast6/i)).toBeInTheDocument();
  expect(screen.getByText("Content")).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run:
```
cd web
npm run test
```
Expected: FAIL (test runner not set up or component missing).

**Step 3: Implement layout + UI components**

- Add a dark theme layout (sidebar + main content).
- Add `StatCard`, `ChartCard`, `Badge`, `Skeleton`, `ErrorBanner`.

**Step 4: Run tests**

Run:
```
cd web
npm run test
```
Expected: PASS for layout test.

**Step 5: Commit**

```
git add web/src/app/layout.tsx web/src/app/page.tsx web/src/components
git commit -m "feat(web): add dashboard layout and UI components"
```

---

### Task 3: API wrapper + caching

**Files:**
- Create: `web/src/lib/api.ts`
- Create: `web/src/lib/cache.ts`

**Step 1: Write failing tests**

Create `web/src/lib/__tests__/api.test.ts`:
```ts
import { request } from "../api";

test("request returns ok false on 500", async () => {
  global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}) }) as any;
  const res = await request("/api/leaderboard/season/2025");
  expect(res.ok).toBe(false);
});
```

**Step 2: Run test to verify it fails**

Run:
```
cd web
npm run test
```
Expected: FAIL (module missing).

**Step 3: Implement API wrapper**

- `request()` with base URL, timeout, retry on 5xx.
- Typed helpers for leaderboard and analytics endpoints.
- In-memory cache with 60s TTL.

**Step 4: Run tests**

Run:
```
cd web
npm run test
```
Expected: PASS.

**Step 5: Commit**

```
git add web/src/lib
git commit -m "feat(web): add API wrapper and cache"
```

---

### Task 4: Leaderboard page

**Files:**
- Create: `web/src/app/leaderboard/page.tsx`
- Create: `web/src/components/leaderboard/LeaderboardTable.tsx`

**Step 1: Write failing test**

Create `web/src/components/leaderboard/__tests__/LeaderboardTable.test.tsx`.

**Step 2: Implement table**

- Render rank, user, points, ROI, win%.
- Handle empty state.

**Step 3: Run tests**

`npm run test`

**Step 4: Commit**

```
git add web/src/app/leaderboard web/src/components/leaderboard
git commit -m "feat(web): add leaderboard page"
```

---

### Task 5: Analytics page

**Files:**
- Create: `web/src/app/analytics/page.tsx`
- Create: `web/src/components/analytics/*` (ROI chart, odds chart, player stats)

**Step 1: Write failing tests**

Add one test per chart component.

**Step 2: Implement charts**

- Use Recharts line + bar charts.
- Show loading and error states.

**Step 3: Run tests**

`npm run test`

**Step 4: Commit**

```
git add web/src/app/analytics web/src/components/analytics
git commit -m "feat(web): add analytics dashboard"
```

---

### Task 6: Week + Matchup pages

**Files:**
- Create: `web/src/app/weeks/[weekId]/page.tsx`
- Create: `web/src/app/matchups/[gameId]/page.tsx`
- Create: `web/src/components/weeks/*`

**Step 1: Write failing tests**

Add minimal tests for page rendering and empty states.

**Step 2: Implement pages**

- Week picks table + weekly leaderboard snapshot.
- Matchup cards from `/api/analytics/matchup/{game_id}`.

**Step 3: Run tests**

`npm run test`

**Step 4: Commit**

```
git add web/src/app/weeks web/src/app/matchups web/src/components/weeks
git commit -m "feat(web): add week and matchup pages"
```

---

### Task 7: Docs + environment setup

**Files:**
- Modify: `README.md`
- Create: `web/.env.local.example`

**Step 1: Document usage**

- Add Next.js dev instructions.
- Document `NEXT_PUBLIC_API_BASE_URL`.

**Step 2: Commit**

```
git add README.md web/.env.local.example
git commit -m "docs(web): add Next.js setup instructions"
```

---

## Verification

Run:
```
cd web
npm run lint
npm run test
```
Expected: all tests pass, lint clean.

## Notes
- If tests are heavy, reduce to API wrapper + one page test in v1.
- Keep pages client-rendered to avoid auth complexity.
