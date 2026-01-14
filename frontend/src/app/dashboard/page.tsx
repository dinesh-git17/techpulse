/**
 * @fileoverview Dashboard page with URL-driven state.
 *
 * Entry point for the technology trends dashboard. All filter state
 * is managed via URL search parameters, enabling deep linking and
 * shareable dashboard configurations.
 *
 * URL Parameters:
 * - tech_ids: Comma-separated technology keys (e.g., "python,react")
 * - start: Start date in YYYY-MM-DD format
 * - end: End date in YYYY-MM-DD format
 */

import { Suspense } from "react";

import { DashboardContainer } from "@/components/containers";
import { DashboardSkeleton } from "@/components/skeletons/DashboardSkeleton";

/**
 * Dashboard page component.
 *
 * Renders the DashboardContainer which handles URL state and data fetching.
 * URL parameters are parsed client-side via nuqs hooks.
 *
 * Wrapped in Suspense to handle the async nature of useSearchParams in
 * Next.js App Router.
 *
 * @example
 * ```
 * // Navigate to dashboard with filters
 * /dashboard?tech_ids=python,react&start=2024-01-01&end=2024-12-31
 * ```
 */
export default function DashboardPage() {
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <DashboardContainer />
    </Suspense>
  );
}
