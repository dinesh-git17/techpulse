/**
 * Skeleton loading components for data fetching states.
 *
 * Provides visual placeholders that match expected content dimensions
 * to prevent layout shift during loading.
 *
 * @module components/skeletons/data-skeleton
 */

import { type ReactNode } from "react";

/**
 * Available skeleton display variants.
 */
export type SkeletonVariant = "list" | "card" | "detail";

/**
 * Props for the DataSkeleton component.
 */
export interface DataSkeletonProps {
  /**
   * Visual variant determining the skeleton layout.
   * - `list`: Horizontal rows suitable for table/list data
   * - `card`: Rectangular card with title and content areas
   * - `detail`: Full detail view with header, metadata, and content
   * @default "list"
   */
  readonly variant?: SkeletonVariant;

  /**
   * Number of skeleton rows to display (list variant only).
   * @default 3
   */
  readonly rows?: number;

  /**
   * Additional CSS classes to apply to the container.
   */
  readonly className?: string;
}

/**
 * Base skeleton element with pulse animation.
 *
 * Respects `prefers-reduced-motion` by disabling animation
 * for users who prefer reduced motion.
 *
 * @param props - Component props.
 * @param props.className - CSS classes for sizing and styling.
 * @returns Animated skeleton element.
 */
function SkeletonElement({
  className = "",
}: {
  readonly className?: string;
}): ReactNode {
  return (
    <div
      className={`motion-safe:animate-pulse rounded bg-gray-200 ${className}`}
      aria-hidden="true"
    />
  );
}

/**
 * Single row skeleton for list items.
 *
 * @returns Row skeleton with icon, title, and value placeholders.
 */
function ListRowSkeleton(): ReactNode {
  return (
    <div className="flex items-center gap-4 py-3">
      <SkeletonElement className="h-8 w-8 shrink-0 rounded-full" />
      <div className="min-w-0 flex-1">
        <SkeletonElement className="mb-2 h-4 w-3/4" />
        <SkeletonElement className="h-3 w-1/2" />
      </div>
      <SkeletonElement className="h-6 w-16 shrink-0" />
    </div>
  );
}

/**
 * List variant skeleton with multiple rows.
 *
 * @param props - Component props.
 * @param props.rows - Number of rows to display.
 * @returns List skeleton with specified number of rows.
 */
function ListSkeleton({ rows }: { readonly rows: number }): ReactNode {
  return (
    <div className="divide-y divide-gray-100">
      {Array.from({ length: rows }, (_, index) => (
        <ListRowSkeleton key={index} />
      ))}
    </div>
  );
}

/**
 * Card variant skeleton for card-based layouts.
 *
 * @returns Card skeleton with header, content, and footer areas.
 */
function CardSkeleton(): ReactNode {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <div className="mb-4 flex items-center justify-between">
        <SkeletonElement className="h-5 w-32" />
        <SkeletonElement className="h-6 w-16 rounded-full" />
      </div>
      <SkeletonElement className="mb-3 h-8 w-24" />
      <SkeletonElement className="mb-4 h-4 w-full" />
      <SkeletonElement className="h-4 w-2/3" />
      <div className="mt-6 flex gap-2">
        <SkeletonElement className="h-8 w-20 rounded-md" />
        <SkeletonElement className="h-8 w-20 rounded-md" />
      </div>
    </div>
  );
}

/**
 * Detail variant skeleton for full detail views.
 *
 * @returns Detail skeleton with header, metadata, and content sections.
 */
function DetailSkeleton(): ReactNode {
  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="border-b border-gray-200 pb-6">
        <SkeletonElement className="mb-2 h-8 w-64" />
        <SkeletonElement className="h-4 w-96" />
      </div>

      {/* Metadata grid */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }, (_, index) => (
          <div key={index}>
            <SkeletonElement className="mb-2 h-3 w-16" />
            <SkeletonElement className="h-6 w-24" />
          </div>
        ))}
      </div>

      {/* Content section */}
      <div className="space-y-3">
        <SkeletonElement className="h-4 w-full" />
        <SkeletonElement className="h-4 w-full" />
        <SkeletonElement className="h-4 w-3/4" />
      </div>

      {/* Chart placeholder */}
      <SkeletonElement className="h-64 w-full rounded-lg" />
    </div>
  );
}

/**
 * Skeleton loading placeholder for data fetching states.
 *
 * Renders animated placeholder content that matches the expected
 * layout dimensions, preventing layout shift when data loads.
 * Animation respects `prefers-reduced-motion` accessibility setting.
 *
 * Can be used as:
 * - Suspense fallback for async components
 * - Conditional render during loading states
 * - Placeholder while data is being fetched
 *
 * @param props - Component props.
 * @param props.variant - Layout variant: "list", "card", or "detail".
 * @param props.rows - Number of rows for list variant (default: 3).
 * @param props.className - Additional CSS classes for the container.
 *
 * @example
 * ```tsx
 * // As Suspense fallback
 * <Suspense fallback={<DataSkeleton variant="list" rows={5} />}>
 *   <TrendsList />
 * </Suspense>
 * ```
 *
 * @example
 * ```tsx
 * // Conditional render
 * {isLoading ? (
 *   <DataSkeleton variant="card" />
 * ) : (
 *   <TrendCard data={data} />
 * )}
 * ```
 *
 * @example
 * ```tsx
 * // Detail view loading
 * <DataSkeleton variant="detail" />
 * ```
 */
export function DataSkeleton({
  variant = "list",
  rows = 3,
  className = "",
}: DataSkeletonProps): ReactNode {
  return (
    <div
      className={className}
      role="status"
      aria-label="Loading content"
      aria-busy="true"
    >
      {variant === "list" && <ListSkeleton rows={rows} />}
      {variant === "card" && <CardSkeleton />}
      {variant === "detail" && <DetailSkeleton />}
      <span className="sr-only">Loading...</span>
    </div>
  );
}
