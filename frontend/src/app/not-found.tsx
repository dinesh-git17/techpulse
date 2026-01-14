/**
 * @fileoverview Application-level 404 page.
 *
 * Displayed when a user navigates to a route that does not exist.
 * Provides a clear path back to the main dashboard.
 */

import Link from "next/link";

/**
 * Not found component for the application.
 *
 * Renders when navigating to an unknown route (e.g., /dashboard/unknown).
 * Uses the root layout styles and provides navigation back to valid routes.
 */
export default function NotFound() {
  return (
    <div
      className="
        flex
        min-h-screen
        w-full
        items-center
        justify-center
        bg-[var(--bg-primary)]
        p-4
      "
    >
      <div
        className="
          flex
          max-w-md
          flex-col
          items-center
          gap-6
          rounded-lg
          border
          border-[var(--border-default)]
          bg-[var(--bg-secondary)]
          p-8
          text-center
        "
        role="alert"
      >
        <div
          className="
            flex
            h-16
            w-16
            items-center
            justify-center
            rounded-full
            bg-[var(--accent-warning)]/10
          "
        >
          <svg
            className="h-8 w-8 text-[var(--accent-warning)]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>

        <div className="space-y-2">
          <h1 className="text-xl font-semibold text-[var(--text-primary)]">
            Page not found
          </h1>
          <p className="text-sm text-[var(--text-secondary)]">
            The page you are looking for does not exist or has been moved.
          </p>
        </div>

        <Link
          href="/dashboard"
          className="
            rounded-md
            bg-[var(--accent-primary)]
            px-4
            py-2
            text-sm
            font-medium
            text-white
            transition-colors
            hover:bg-[var(--accent-primary)]/90
            focus:outline
            focus:outline-2
            focus:outline-offset-2
            focus:outline-[var(--accent-primary)]
          "
        >
          Go to Dashboard
        </Link>
      </div>
    </div>
  );
}
