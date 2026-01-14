/**
 * @fileoverview Dashboard route loading state.
 *
 * Next.js App Router automatically renders this component during route
 * navigation while the page content is being loaded. Uses DashboardSkeleton
 * to provide instant visual feedback matching the final layout structure.
 */

import { DashboardSkeleton } from "@/components/skeletons/DashboardSkeleton";

/**
 * Loading component for the dashboard route.
 *
 * Rendered automatically by Next.js during:
 * - Initial navigation to /dashboard
 * - Client-side navigation to /dashboard from other routes
 *
 * The skeleton exactly mirrors DashboardShell dimensions to prevent
 * cumulative layout shift (CLS) when actual content loads.
 */
export default function Loading() {
  return <DashboardSkeleton />;
}
