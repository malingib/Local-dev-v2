---
name: fix-performance
description: Identify and fix performance bottlenecks in React components. Generates staged visual approval for lazy loading, code splitting, and render optimization.
---

# Fix Performance

## What This Does
Targets performance issues in your frontend:
- **Render optimization**: Unnecessary re-renders, missing memoization, useCallback/useMemo
- **Code splitting**: Large component bundles, dynamic imports
- **Image optimization**: Missing lazy loading, unoptimized formats, oversized assets
- **Bundle analysis**: Large dependencies, dead code, duplicate packages

## Usage
Run this prompt when frontend feels slow or bundle size is large.

## Process

### 1. Profile Components
- Identifies components with >500ms render time
- Detects re-render cascades (parent → child chains)
- Analyzes dependency graph for code split opportunities

### 2. Propose Fixes (Staged Approval)
For each performance issue:
1. **Sketch**: Shows the optimization strategy
2. **Component Preview**: Tests fix in isolation
3. **Full Page Render**: Confirms no visual regressions
4. **Metrics**: Before/after (render time, bundle size, TTL)

### 3. Apply Approved Changes
Auto-applies:
- Dynamic imports: `const Component = lazy(() => import('./Component'))`
- Image lazy loading: `<img loading="lazy" />`
- Memoization: `React.memo()`, `useCallback()`, `useMemo()`
- Bundle analysis recommendations

Manual review required for:
- Refactoring component architecture
- Changing state management patterns

## Example Fixes
```typescript
// BEFORE: Renders on every parent update
const ActivityFeed = ({ sessions }) => {
  const sorted = sessions.sort(...);  // Re-computed every render
  return <div>{sorted.map(s => <Item key={s.id} session={s} />)}</div>;
};

// AFTER: Optimized
const ActivityFeed = React.memo(({ sessions }) => {
  const sorted = useMemo(() => sessions.sort(...), [sessions]);
  return <div>{sorted.map(s => <Item key={s.id} session={s} />)}</div>;
});
```

## Output Example
```
PERFORMANCE FIXES: 7 identified

✅ APPLIED AUTOMATICALLY (3)
  • FindingCard.tsx: Added React.memo() → -15% re-renders
  • SessionView.tsx: Lazy loaded chart component → -120KB bundle
  • ActivityFeed.tsx: Converted to lazy image loading → -3s TTL

⏳ AWAITING APPROVAL (4)
  1. Refactor store to use selectors (reduces re-renders)
  2. Split Dashboard into smaller chunks (code splitting)
  3. Replace recharts with lightweight alternative (bundle -50KB)
  4. Add service worker for offline caching

Estimated improvement:
  • Bundle size: 345KB → 280KB (-19%)
  • Initial load: 2.8s → 1.9s (-32%)
  • Re-renders: 890 → 120 per interaction (-87%)
```

## Next Steps
- View approved changes in `/src` — no CI step needed
- Run `npm run build` to verify bundle size improvement
- Use `/audit-frontend` to confirm no regressions
