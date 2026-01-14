/**
 * @fileoverview Skeleton loading state for the dashboard layout.
 *
 * Renders a placeholder UI that exactly mirrors the DashboardShell grid
 * structure to prevent layout shift when the actual content loads.
 * Uses pulse animation and ARIA attributes for accessibility.
 */
import type { ReactNode } from "react";

/** Aspect ratio matching TrendChart (16:9). */
const CHART_ASPECT_RATIO = 16 / 9;

/**
 * Renders a single skeleton placeholder element with pulse animation.
 *
 * @param props.className - Additional Tailwind classes for sizing.
 */
function SkeletonBlock({
  className = "",
}: {
  readonly className?: string;
}): ReactNode {
  return (
    <div
      className={`animate-skeleton-pulse rounded bg-[var(--bg-tertiary)] ${className}`}
      aria-hidden="true"
    />
  );
}

/**
 * Skeleton for the sidebar region matching DashboardContainer sidebar content.
 *
 * Structure mirrors:
 * - Title block (h1 + p with gap)
 * - TechnologySelector input (min-h-[44px])
 * - DateRangePicker button (min-h-[44px])
 */
function SidebarSkeleton(): ReactNode {
  return (
    <div className="flex flex-col gap-6">
      {/* Title block */}
      <div>
        <SkeletonBlock className="mb-2 h-7 w-48" />
        <SkeletonBlock className="h-5 w-64" />
      </div>

      {/* TechnologySelector placeholder */}
      <div className="flex flex-col gap-2">
        <SkeletonBlock className="h-4 w-24" />
        <SkeletonBlock className="min-h-[44px] w-full rounded-md" />
      </div>

      {/* DateRangePicker placeholder */}
      <div className="flex flex-col gap-2">
        <SkeletonBlock className="h-4 w-20" />
        <SkeletonBlock className="min-h-[44px] w-full rounded-md" />
      </div>
    </div>
  );
}

/**
 * Skeleton for the main content region matching DashboardContainer main content.
 *
 * Structure mirrors:
 * - Header row (h2 + count text)
 * - TrendChart with 16:9 aspect ratio container
 */
function MainContentSkeleton(): ReactNode {
  return (
    <div className="flex flex-col gap-4">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <SkeletonBlock className="h-7 w-36" />
        <SkeletonBlock className="h-5 w-32" />
      </div>

      {/* Chart placeholder with fixed aspect ratio */}
      <div className="w-full">
        <div
          className="relative w-full"
          style={{ paddingBottom: `${(1 / CHART_ASPECT_RATIO) * 100}%` }}
        >
          <div className="absolute inset-0">
            <SkeletonBlock className="h-full w-full rounded-md" />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Full dashboard skeleton matching DashboardShell grid layout.
 *
 * Renders immediately during route navigation to provide instant visual
 * feedback. Uses the same CSS Grid structure as DashboardShell to ensure
 * zero cumulative layout shift (CLS) when content loads.
 *
 * Accessibility:
 * - Container has aria-busy="true" to indicate loading state
 * - aria-live="polite" on main region announces content changes
 *
 * @example
 * ```tsx
 * // In loading.tsx
 * export default function Loading() {
 *   return <DashboardSkeleton />;
 * }
 * ```
 */
export function DashboardSkeleton(): ReactNode {
  return (
    <div
      className="
        grid
        min-h-screen
        w-full
        grid-cols-1
        md:grid-cols-[280px_1fr]
      "
      aria-busy="true"
      aria-label="Loading dashboard"
    >
      <aside
        className="
          border-b
          border-[var(--border-muted)]
          bg-[var(--bg-secondary)]
          p-4
          md:border-b-0
          md:border-r
          md:p-6
        "
        aria-label="Loading filters"
      >
        <SidebarSkeleton />
      </aside>

      <main
        className="
          min-w-0
          bg-[var(--bg-primary)]
          p-4
          md:p-6
        "
        aria-live="polite"
      >
        <MainContentSkeleton />
      </main>
    </div>
  );
}
