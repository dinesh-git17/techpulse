# Frontend Contributing Guidelines

This document outlines the standards and conventions for contributing to the TechPulse frontend.

## Folder Structure

```
src/
├── app/           # Next.js App Router (pages, layouts, routing)
├── features/      # Domain-specific feature modules
├── components/    # Shared UI components (atoms, molecules)
├── lib/           # Utilities, helpers, constants
└── types/         # Shared TypeScript type definitions
```

### When to Use Each Directory

| Directory     | Purpose                                                                       | Examples                                                    |
| ------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `features/`   | Domain-specific modules that encapsulate related components, hooks, and logic | `features/auth/`, `features/dashboard/`, `features/trends/` |
| `components/` | Reusable UI primitives shared across multiple features                        | `Button`, `Card`, `Modal`, `Input`                          |
| `lib/`        | Pure utilities with no React dependencies                                     | `formatDate()`, `cn()`, API clients, constants              |
| `types/`      | Shared TypeScript interfaces and type definitions                             | `ApiResponse`, `User`, `TrendData`                          |

### Feature Module Structure

Each feature directory should be self-contained:

```
features/
└── dashboard/
    ├── components/     # Feature-specific components
    ├── hooks/          # Feature-specific hooks
    ├── api/            # Feature-specific API calls
    ├── types.ts        # Feature-specific types
    └── index.ts        # Public exports
```

## Import Ordering

Imports must follow this order, enforced by ESLint:

1. **React/Next.js** — `react`, `next`, `next/*`
2. **External packages** — Third-party node_modules
3. **Internal aliases** — `@/features/*`, `@/components/*`, `@/lib/*`, `@/types/*`
4. **Relative imports** — `./`, `../`

Each group must be separated by a blank line. Imports within groups are alphabetized.

```typescript
import type { Metadata } from "next";

import { Geist } from "next/font/google";
import { useState } from "react";

import { Button } from "@/components/Button";
import { useAuth } from "@/features/auth";
import { formatDate } from "@/lib/formatDate";

import { LocalComponent } from "./LocalComponent";
```

## TypeScript Strictness

The project enforces maximum TypeScript strictness:

| Setting                    | Value  | Effect                                             |
| -------------------------- | ------ | -------------------------------------------------- |
| `strict`                   | `true` | Enables all strict type checking options           |
| `noUncheckedIndexedAccess` | `true` | Array/object index access returns `T \| undefined` |
| `noImplicitAny`            | `true` | Errors on implicit `any` types                     |
| `strictNullChecks`         | `true` | `null` and `undefined` are distinct types          |

### Handling Index Access

With `noUncheckedIndexedAccess`, you must handle potential `undefined`:

```typescript
const items = ["a", "b", "c"];

// Error: Object is possibly 'undefined'
const first = items[0].toUpperCase();

// Correct: Check for undefined
const first = items[0];
if (first !== undefined) {
  console.log(first.toUpperCase());
}

// Or use optional chaining
const first = items[0]?.toUpperCase();
```

### Forbidden Patterns

- `any` type — Use `unknown` with type narrowing instead
- Implicit `any` — Always provide explicit types
- Non-null assertions (`!`) — Avoid unless absolutely necessary

## Pre-Commit Hooks

The following hooks run automatically on every commit:

| Hook       | Action            | Scope              |
| ---------- | ----------------- | ------------------ |
| `prettier` | Format code       | `frontend/`        |
| `eslint`   | Lint and auto-fix | `frontend/`        |
| `tsc`      | Type check        | `frontend/*.ts(x)` |

### Hook Behavior

1. **Format** — Prettier formats all staged files
2. **Lint** — ESLint checks and auto-fixes issues
3. **Type Check** — TypeScript compiler verifies types

If any hook fails, the commit is rejected. Fix the issues and retry.

### Bypassing Hooks (Emergency Only)

```bash
git commit --no-verify -m "fix: emergency hotfix"
```

CI will still enforce all checks on push.

## Commands Reference

### Development

| Command      | Description              |
| ------------ | ------------------------ |
| `pnpm dev`   | Start development server |
| `pnpm build` | Create production build  |
| `pnpm start` | Start production server  |

### Code Quality

| Command                  | Description               |
| ------------------------ | ------------------------- |
| `pnpm lint`              | Run ESLint                |
| `pnpm format:check`      | Check Prettier formatting |
| `pnpm exec tsc --noEmit` | Run TypeScript type check |

### Combined Validation

Run all checks before pushing:

```bash
pnpm format:check && pnpm lint && pnpm exec tsc --noEmit && pnpm build
```

## Path Aliases

The `@/*` alias maps to `./src/*`:

| Alias            | Resolves To          |
| ---------------- | -------------------- |
| `@/features/*`   | `./src/features/*`   |
| `@/components/*` | `./src/components/*` |
| `@/lib/*`        | `./src/lib/*`        |
| `@/types/*`      | `./src/types/*`      |
| `@/app/*`        | `./src/app/*`        |
