/**
 * @fileoverview High-fidelity skeleton for the TrendChart component.
 *
 * Renders a placeholder that mimics the visual structure of the actual chart
 * including Y-axis area, horizontal grid lines, and X-axis labels. Uses the
 * same 16:9 aspect ratio container to prevent layout shift.
 */
import type { ReactNode } from "react";

/** Aspect ratio matching TrendChart (16:9). */
const CHART_ASPECT_RATIO = 16 / 9;

/** Number of horizontal grid lines to display. */
const GRID_LINE_COUNT = 5;

/** Number of X-axis tick placeholders. */
const X_AXIS_TICK_COUNT = 6;

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
 * Renders a horizontal grid line skeleton.
 */
function GridLine(): ReactNode {
  return (
    <div
      className="h-px w-full animate-skeleton-pulse bg-[var(--border-muted)]"
      aria-hidden="true"
    />
  );
}

/**
 * High-fidelity skeleton for the TrendChart component.
 *
 * Mimics the visual structure of the actual Recharts line chart:
 * - Y-axis area on the left (60px width)
 * - Horizontal grid lines across the chart area
 * - X-axis tick labels along the bottom
 *
 * Uses the same 16:9 aspect ratio container as TrendChart to ensure
 * zero cumulative layout shift (CLS) when the real chart loads.
 *
 * @example
 * ```tsx
 * <Suspense fallback={<ChartSkeleton />}>
 *   <TrendChart {...props} />
 * </Suspense>
 * ```
 */
export function ChartSkeleton(): ReactNode {
  return (
    <div className="w-full" aria-busy="true" aria-label="Loading chart">
      {/* Fixed aspect ratio container matching TrendChart */}
      <div
        className="relative w-full"
        style={{ paddingBottom: `${(1 / CHART_ASPECT_RATIO) * 100}%` }}
      >
        <div className="absolute inset-0 flex flex-col">
          {/* Chart area with Y-axis and grid */}
          <div className="flex flex-1">
            {/* Y-axis area */}
            <div className="flex w-[60px] flex-col items-end justify-between py-2 pr-2">
              {Array.from({ length: GRID_LINE_COUNT }).map((_, index) => (
                <SkeletonBlock key={`y-tick-${index}`} className="h-3 w-8" />
              ))}
            </div>

            {/* Chart plot area with grid lines */}
            <div className="relative flex-1 border-b border-l border-[var(--border-default)]">
              {/* Horizontal grid lines */}
              <div className="absolute inset-0 flex flex-col justify-between py-2">
                {Array.from({ length: GRID_LINE_COUNT }).map((_, index) => (
                  <GridLine key={`grid-${index}`} />
                ))}
              </div>

              {/* Placeholder chart line area */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="h-1/2 w-3/4 animate-skeleton-pulse rounded-lg bg-[var(--bg-tertiary)] opacity-30" />
              </div>
            </div>
          </div>

          {/* X-axis area */}
          <div className="flex">
            {/* Spacer for Y-axis width */}
            <div className="w-[60px]" />

            {/* X-axis tick labels */}
            <div className="flex flex-1 justify-between px-2 pt-2">
              {Array.from({ length: X_AXIS_TICK_COUNT }).map((_, index) => (
                <SkeletonBlock key={`x-tick-${index}`} className="h-3 w-10" />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Screen reader text */}
      <span className="sr-only">Loading chart data...</span>
    </div>
  );
}
