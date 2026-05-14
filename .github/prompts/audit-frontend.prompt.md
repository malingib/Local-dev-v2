---
name: audit-frontend
description: Run a complete audit of frontend React components using CodeAudit agents (accessibility, performance, responsive design, console errors). Generates findings report without modifications.
---

# Audit Frontend

## What This Does
Analyzes your React frontend (`app/src/`) for:
- **UI Issues**: Accessibility (WCAG), design quality, responsive breakpoints
- **Performance**: Component re-renders, large bundles, missing lazy loading, slow image assets
- **Mobile**: Touch targets, fixed widths, viewport configuration
- **Runtime Errors**: Console warnings, React warnings, unhandled promises

## Usage
Run this prompt when you want a comprehensive audit of frontend code **without applying changes**.

## Process

### 1. Gather Frontend Code
Scans `app/src/components/`, `app/src/pages/`, identifies:
- React component patterns
- Component dependency graph
- CSS/Tailwind usage
- TypeScript type coverage

### 2. Run Parallel Audits
Five specialist agents analyze independently:
- **UI Agent**: Accessibility (ARIA, semantic HTML), design patterns, WCAG compliance
- **Performance Agent**: Bundle size, re-render frequency, code splitting opportunities
- **Mobile Agent**: Responsive breakpoints, touch target sizes, viewport configuration
- **Auditor**: Anti-patterns, dead code, logic errors, naming conventions
- **Meta Agent**: Cross-agent analysis, prioritization

### 3. Generate Findings Report
Output: Prioritized findings with:
- Type (accessibility, performance, mobile, bug)
- Severity (critical, high, medium, low)
- Affected component + line number
- Hypothesis + confidence score
- Suggested fix (UI-only; requires approval)

## Output Example
```
AUDIT COMPLETE: 23 findings

🔴 CRITICAL (4)
  • ActivityFeed.tsx: Missing alt text on 12 images (accessibility)
    Confidence: 98% | Auto-fixable
  
  • SessionView.tsx: Re-renders 890 times per interaction (performance)
    Confidence: 76% | Requires review

🟠 HIGH (8)
  • FindingCard.tsx: Touch target < 44px on close button (mobile)
    Confidence: 94% | Auto-fixable

... (medium and low findings) ...
```

## Next Steps
- Review findings in CodeAudit UI (http://localhost:8000)
- Use `/fix-performance` or `/improve-accessibility` for targeted fixes
- Export findings to JSON for team review
