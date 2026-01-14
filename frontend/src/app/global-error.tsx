"use client";

/**
 * @fileoverview Root-level error boundary.
 *
 * Catches catastrophic errors that occur in the root layout or its children.
 * This component must include its own <html> and <body> tags since it
 * completely replaces the root layout when triggered.
 */

import { useEffect } from "react";

/**
 * Props for the GlobalError component provided by Next.js App Router.
 */
interface GlobalErrorProps {
  /** The error that was thrown. */
  error: Error & { digest?: string };
  /** Function to reset the error boundary and re-render. */
  reset: () => void;
}

/**
 * Global error boundary for the application.
 *
 * Renders when a catastrophic error occurs that cannot be handled by
 * route-level error boundaries (e.g., root layout crash). Provides
 * options to retry or perform a hard page reload.
 *
 * @param props.error - The caught error object.
 * @param props.reset - Callback to attempt recovery.
 */
export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    // Log error for debugging (production would send to error tracking)
    console.error("Global error:", error);
  }, [error]);

  const handleReload = () => {
    window.location.reload();
  };

  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          fontFamily:
            'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          backgroundColor: "#ffffff",
          color: "#0f172a",
        }}
      >
        <div
          style={{
            display: "flex",
            minHeight: "100vh",
            width: "100%",
            alignItems: "center",
            justifyContent: "center",
            padding: "1rem",
          }}
        >
          <div
            style={{
              display: "flex",
              maxWidth: "28rem",
              flexDirection: "column",
              alignItems: "center",
              gap: "1.5rem",
              borderRadius: "0.5rem",
              border: "1px solid #e2e8f0",
              backgroundColor: "#f8f9fa",
              padding: "2rem",
              textAlign: "center",
            }}
            role="alert"
          >
            <div
              style={{
                display: "flex",
                height: "4rem",
                width: "4rem",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "9999px",
                backgroundColor: "rgba(220, 38, 38, 0.1)",
              }}
            >
              <svg
                style={{ height: "2rem", width: "2rem", color: "#dc2626" }}
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

            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "0.5rem",
              }}
            >
              <h1
                style={{
                  margin: 0,
                  fontSize: "1.25rem",
                  fontWeight: 600,
                  color: "#0f172a",
                }}
              >
                Application Error
              </h1>
              <p
                style={{
                  margin: 0,
                  fontSize: "0.875rem",
                  color: "#475569",
                }}
              >
                A critical error occurred. Please reload the page to continue.
              </p>
            </div>

            <div style={{ display: "flex", gap: "0.75rem" }}>
              <button
                type="button"
                onClick={reset}
                style={{
                  borderRadius: "0.375rem",
                  backgroundColor: "#2563eb",
                  padding: "0.5rem 1rem",
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  color: "white",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                Try Again
              </button>
              <button
                type="button"
                onClick={handleReload}
                style={{
                  borderRadius: "0.375rem",
                  border: "1px solid #e2e8f0",
                  backgroundColor: "#ffffff",
                  padding: "0.5rem 1rem",
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  color: "#0f172a",
                  cursor: "pointer",
                }}
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
