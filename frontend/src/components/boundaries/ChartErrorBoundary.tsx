"use client";

/**
 * @fileoverview Error boundary for isolating chart component failures.
 *
 * Wraps the TrendChart to catch runtime errors without affecting the
 * rest of the dashboard (sidebar, filters). Uses class component pattern
 * as required by React error boundaries.
 */

import { Component, type ReactNode } from "react";

/** Aspect ratio matching TrendChart (16:9). */
const CHART_ASPECT_RATIO = 16 / 9;

/**
 * Props for the ChartErrorBoundary component.
 */
interface ChartErrorBoundaryProps {
  /** Child components to render (typically TrendChart). */
  children: ReactNode;
  /** Optional callback when an error is caught. */
  onError?: (error: Error) => void;
}

/**
 * State for the ChartErrorBoundary component.
 */
interface ChartErrorBoundaryState {
  /** Whether an error has been caught. */
  hasError: boolean;
  /** The caught error, if any. */
  error: Error | null;
}

/**
 * Error boundary that isolates chart failures from the rest of the UI.
 *
 * When the TrendChart throws an error, this boundary catches it and
 * displays an error state with a retry button. The sidebar and other
 * dashboard components remain functional.
 *
 * @example
 * ```tsx
 * <ChartErrorBoundary>
 *   <TrendChart {...props} />
 * </ChartErrorBoundary>
 * ```
 */
export class ChartErrorBoundary extends Component<
  ChartErrorBoundaryProps,
  ChartErrorBoundaryState
> {
  constructor(props: ChartErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ChartErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error): void {
    // Log error for debugging (production would send to error tracking)
    console.error("Chart error:", error);
    this.props.onError?.(error);
  }

  handleRetry = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="w-full">
          {/* Fixed aspect ratio container matching TrendChart */}
          <div
            className="relative w-full"
            style={{ paddingBottom: `${(1 / CHART_ASPECT_RATIO) * 100}%` }}
          >
            <div className="absolute inset-0">
              <div
                className="
                  flex
                  h-full
                  w-full
                  flex-col
                  items-center
                  justify-center
                  gap-4
                  rounded-md
                  border
                  border-[var(--accent-danger)]/30
                  bg-[var(--accent-danger)]/5
                  p-6
                "
                role="alert"
              >
                <svg
                  className="h-10 w-10 text-[var(--accent-danger)]"
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
                <p className="text-center text-sm text-[var(--text-primary)]">
                  Failed to render chart. Try again or adjust your filters.
                </p>
                <button
                  type="button"
                  onClick={this.handleRetry}
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
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
