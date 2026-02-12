# Fast6 Design System

Design tokens and UX guidelines for the Fast6 Ticket Office theme.

---

## UX principles

### Optimization opportunities

| Area | Current | Target |
|------|---------|--------|
| **Scan-ability** | Card headings, tables | Clear hierarchy; bold primary metrics |
| **Feedback** | Loading text, error banners | Loading states; consider toasts for success |
| **Accessibility** | Contrast, focus rings | WCAG AA; visible focus on all interactive |
| **Consistency** | Spacing p-4/p-6, card borders | Unified spacing scale; consistent buttons |
| **Friction** | Multiple taps for filters | Fewer taps; sensible defaults |

### User-focused improvements

- **Faster decisions** — Surface key numbers (win rate, ROI) first; hide detail until needed
- **Clearer context** — Tooltips on metrics (e.g. Brier score); aria-labels on controls
- **Easier navigation** — Tabs reduce scrolling; bottom nav on mobile
- **Error recovery** — Error banners with retry; empty states with next steps
- **Delight** — Streak indicators, subtle animations; maintain professional tone

---

## Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--background` | #F1EEE6 | Page background (cream) |
| `--foreground` | #234058 | Primary text, sidebar (salty-dog) |
| `--salty-dog-dark` | #1a3348 | Sidebar active state |
| `--tanager` | #8C302C | Accent, buttons, highlights |
| `--bronze` | #A2877D | Secondary accent |
| `--muted-blue` | #8faec7 | Sidebar inactive nav |
| `--border-gray` | #d1d5db | Card borders |
| `--text-muted` | #5c5a57 | Secondary text (WCAG AA) |
| `--success-green` | #15803d | Success states, correct picks |

## Typography

- **Body:** Geist Sans
- **Headings / data:** Geist Mono
- **Labels:** Uppercase, tracking, font-mono

## Analytics Layout

- Tabbed interface: Overview | Performance | Touchdowns
- Within each tab: vertical stack of cards; consistent padding (p-6)
- Section: heading + description + content
- Touchdowns: single table with view toggle (All touchdowns | First TD only) and week/team filters
- Empty state: clear message + action hint (e.g. "Sync touchdowns first")

## Tabs (WAI-ARIA)

- `role="tablist"`, `role="tab"`, `role="tabpanel"`
- `aria-selected`, `aria-controls`, `aria-labelledby`
- Keyboard: Arrow keys (Left/Right) to move between tabs; Home/End for first/last
- Tab: moves focus out of tablist; Tab index -1 for inactive tabs
- Active tab: focus ring (tanager accent)

## Mobile

- **Bottom nav** (md and below): Fixed bar with Board, Schedule, Rankings, Fast6, Analysis, About; safe-area-inset-bottom for notched devices
- **Touch targets**: min 44×44px for nav links, selects, tab buttons (WCAG 2.5.5)
- **Content padding**: pb-28 on main content so it isn’t hidden behind fixed bottom nav
- **Tables**: overflow-x-auto for horizontal scroll on narrow screens
- **Forms**: Full-width selects on mobile (w-full sm:w-auto)
- **Viewport**: No overflow; body uses overflow-x-hidden where needed

## Accessibility

- Muted text meets WCAG AA contrast on cream
- Success feedback uses green, not red
- Focus indicators on interactive elements
- Tab buttons: min 44px touch target (WCAG 2.5.5)
