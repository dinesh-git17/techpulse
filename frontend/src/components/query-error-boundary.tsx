"use client";

/**
 * Query-specific Error Boundary for TechPulse.
 *
 * Catches and displays errors from TanStack Query hooks with
 * contextual messages based on error type (schema validation,
 * network, HTTP errors).
 *
 * @module components/query-error-boundary
 */

import { Component, type ReactNode } from "react";

import { QueryErrorResetBoundary } from "@tanstack/react-query";

import { ApiError } from "@/lib/api/client";
import { isSchemaValidationError } from "@/lib/api/fetcher";

/**
 * Props for the QueryErrorBoundary component.
 */
export interface QueryErrorBoundaryProps {
  /** Child components to render within the boundary. */
  readonly children: ReactNode;
  /** Optional custom fallback render function. */
  readonly fallback?: (props: ErrorFallbackProps) => ReactNode;
}

/**
 * Props passed to the error fallback component.
 */
export interface ErrorFallbackProps {
  /** The caught error. */
  readonly error: Error;
  /** Function to reset the error boundary and retry queries. */
  readonly resetErrorBoundary: () => void;
}

/**
 * Internal state for the error boundary.
 */
interface QueryErrorBoundaryState {
  /** Whether an error has been caught. */
  readonly hasError: boolean;
  /** The caught error, if any. */
  readonly error: Error | null;
}

/**
 * Categorized error information for display.
 */
interface ErrorInfo {
  /** User-friendly error title. */
  readonly title: string;
  /** User-friendly error description. */
  readonly description: string;
  /** Technical details for debugging. */
  readonly technicalDetails: string;
  /** Whether the error is likely recoverable via retry. */
  readonly canRetry: boolean;
}

/**
 * Extract display information from an error based on its type.
 *
 * @param error - The error to analyze.
 * @returns Categorized error information.
 */
function getErrorInfo(error: Error): ErrorInfo {
  if (isSchemaValidationError(error)) {
    const fieldPaths = error.fieldErrors
      .map((fieldError) => fieldError.path.join(".") || "root")
      .join(", ");

    return {
      title: "Data Format Error",
      description:
        "The server returned data in an unexpected format. This may indicate an API version mismatch.",
      technicalDetails: `Schema validation failed for fields: ${fieldPaths}\n\nDetails:\n${JSON.stringify(error.fieldErrors, null, 2)}\n\nRaw response:\n${JSON.stringify(error.rawResponse, null, 2)}`,
      canRetry: false,
    };
  }

  if (error instanceof ApiError) {
    if (error.isNetworkError()) {
      return {
        title: "Connection Error",
        description:
          "Unable to connect to the server. Please check your internet connection and try again.",
        technicalDetails: `Network error: ${error.message}\nCode: ${error.code}`,
        canRetry: true,
      };
    }

    if (error.isClientError()) {
      return {
        title: "Request Error",
        description: error.message || "The request could not be processed.",
        technicalDetails: `HTTP ${error.status}: ${error.message}\nCode: ${error.code}\n\nDetails:\n${JSON.stringify(error.details, null, 2)}`,
        canRetry: false,
      };
    }

    if (error.isServerError()) {
      return {
        title: "Server Error",
        description:
          "The server encountered an error. Please try again in a moment.",
        technicalDetails: `HTTP ${error.status}: ${error.message}\nCode: ${error.code}`,
        canRetry: true,
      };
    }

    return {
      title: "Request Failed",
      description: error.message || "An error occurred while fetching data.",
      technicalDetails: `HTTP ${error.status}: ${error.message}\nCode: ${error.code}`,
      canRetry: true,
    };
  }

  return {
    title: "Unexpected Error",
    description: "An unexpected error occurred. Please try again.",
    technicalDetails: `${error.name}: ${error.message}\n\nStack:\n${error.stack ?? "No stack trace available"}`,
    canRetry: true,
  };
}

/**
 * Log error details to console in development mode.
 *
 * @param error - The error to log.
 * @param errorInfo - React error info with component stack.
 */
/* eslint-disable no-console */
function logErrorInDevelopment(
  error: Error,
  errorInfo: { componentStack?: string | null },
): void {
  if (process.env.NODE_ENV !== "development") {
    return;
  }

  console.group("QueryErrorBoundary caught an error");
  console.error("Error:", error);

  if (isSchemaValidationError(error)) {
    console.error("Field errors:", error.fieldErrors);
    console.error("Raw response:", error.rawResponse);
  } else if (error instanceof ApiError) {
    console.error("Status:", error.status);
    console.error("Code:", error.code);
    console.error("Details:", error.details);
    console.error("Raw response:", error.rawResponse);
  }

  if (errorInfo.componentStack) {
    console.error("Component stack:", errorInfo.componentStack);
  }

  console.groupEnd();
}
/* eslint-enable no-console */

/**
 * Default error fallback UI component.
 *
 * Displays error information with collapsible technical details
 * and a retry button for recoverable errors.
 *
 * @param props - Fallback component props.
 * @returns Error UI elements.
 */
function DefaultErrorFallback({
  error,
  resetErrorBoundary,
}: ErrorFallbackProps): ReactNode {
  const errorInfo = getErrorInfo(error);

  return (
    <div
      role="alert"
      className="mx-auto max-w-lg rounded-lg border border-red-200 bg-red-50 p-6"
    >
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-red-800">
          {errorInfo.title}
        </h2>
        <p className="mt-1 text-sm text-red-700">{errorInfo.description}</p>
      </div>

      {errorInfo.canRetry && (
        <button
          type="button"
          onClick={resetErrorBoundary}
          className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:outline-none"
        >
          Try Again
        </button>
      )}

      {process.env.NODE_ENV === "development" && (
        <details className="mt-4">
          <summary className="cursor-pointer text-sm font-medium text-red-600 hover:text-red-800">
            Technical Details
          </summary>
          <pre className="mt-2 max-h-64 overflow-auto rounded bg-red-100 p-3 text-xs text-red-900">
            {errorInfo.technicalDetails}
          </pre>
        </details>
      )}
    </div>
  );
}

/**
 * Inner error boundary class component.
 *
 * Handles the actual error catching and state management.
 */
class ErrorBoundaryInner extends Component<
  QueryErrorBoundaryProps & { onReset: () => void },
  QueryErrorBoundaryState
> {
  constructor(props: QueryErrorBoundaryProps & { onReset: () => void }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): QueryErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(
    error: Error,
    errorInfo: { componentStack?: string | null },
  ): void {
    logErrorInDevelopment(error, errorInfo);
  }

  resetErrorBoundary = (): void => {
    this.props.onReset();
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    const { hasError, error } = this.state;
    const { children, fallback } = this.props;

    if (hasError && error) {
      const FallbackComponent = fallback ?? DefaultErrorFallback;
      return (
        <FallbackComponent
          error={error}
          resetErrorBoundary={this.resetErrorBoundary}
        />
      );
    }

    return children;
  }
}

/**
 * Query-aware Error Boundary for TanStack Query.
 *
 * Wraps children in an error boundary that:
 * - Catches errors from query hooks (including Suspense queries)
 * - Differentiates between schema validation, network, and HTTP errors
 * - Displays contextual error messages with collapsible technical details
 * - Integrates with TanStack Query's reset mechanism for retry functionality
 *
 * @param props - Component props.
 * @param props.children - Child components to protect.
 * @param props.fallback - Optional custom fallback render function.
 *
 * @example
 * ```tsx
 * <QueryErrorBoundary>
 *   <Suspense fallback={<Loading />}>
 *     <TrendsDisplay />
 *   </Suspense>
 * </QueryErrorBoundary>
 * ```
 *
 * @example
 * ```tsx
 * // With custom fallback
 * <QueryErrorBoundary
 *   fallback={({ error, resetErrorBoundary }) => (
 *     <CustomErrorUI error={error} onRetry={resetErrorBoundary} />
 *   )}
 * >
 *   {children}
 * </QueryErrorBoundary>
 * ```
 */
export function QueryErrorBoundary({
  children,
  fallback,
}: QueryErrorBoundaryProps): ReactNode {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundaryInner onReset={reset} fallback={fallback}>
          {children}
        </ErrorBoundaryInner>
      )}
    </QueryErrorResetBoundary>
  );
}
