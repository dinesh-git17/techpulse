"use client";

/**
 * @fileoverview Dashboard route error boundary.
 *
 * Catches runtime errors within the dashboard segment and displays
 * a recoverable error state. Users can retry without a full page reload
 * using the reset function provided by Next.js.
 */

import { useEffect } from "react";

/**
 * Props for the Error component provided by Next.js App Router.
 */
interface ErrorProps {
  /** The error that was thrown. */
  error: Error & { digest?: string };
  /** Function to reset the error boundary and re-render the segment. */
  reset: () => void;
}

/**
 * Error boundary component for the dashboard route.
 *
 * Renders when a runtime error occurs within the dashboard page or its
 * children. Provides a "Try Again" button that triggers the reset function
 * to re-render the route segment without a full navigation.
 *
 * @param props.error - The caught error object.
 * @param props.reset - Callback to reset the error boundary.
 */
export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log error for debugging (production would send to error tracking)
    console.error("Dashboard error:", error);
  }, [error]);

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
            bg-[var(--accent-danger)]/10
          "
        >
          <svg
            className="h-8 w-8 text-[var(--accent-danger)]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>

        <div className="space-y-2">
          <h1 className="text-xl font-semibold text-[var(--text-primary)]">
            Something went wrong
          </h1>
          <p className="text-sm text-[var(--text-secondary)]">
            We encountered an issue loading this page. Try again or return to
            the dashboard.
          </p>
        </div>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={reset}
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
            Try Again
          </button>
          <a
            href="/dashboard"
            className="
              rounded-md
              border
              border-[var(--border-default)]
              bg-[var(--bg-primary)]
              px-4
              py-2
              text-sm
              font-medium
              text-[var(--text-primary)]
              transition-colors
              hover:bg-[var(--bg-tertiary)]
              focus:outline
              focus:outline-2
              focus:outline-offset-2
              focus:outline-[var(--accent-primary)]
            "
          >
            Go to Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
