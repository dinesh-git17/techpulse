/**
 * TanStack Query client configuration for TechPulse.
 *
 * Implements the Next.js App Router pattern for server/client QueryClient
 * management with request isolation on the server and singleton on the client.
 *
 * @module lib/api/query-client
 */

import { QueryClient, type QueryClientConfig } from "@tanstack/react-query";

/** Five minutes in milliseconds. */
const STALE_TIME_MS = 5 * 60 * 1000;

/** Ten minutes in milliseconds. */
const GC_TIME_MS = 10 * 60 * 1000;

/**
 * Check if an HTTP status code represents a client error (4xx).
 *
 * @param status - HTTP status code.
 * @returns True if status is 400-499.
 */
function isClientError(status: number): boolean {
  return status >= 400 && status < 500;
}

/**
 * Determine if a failed query should be retried.
 *
 * Implements retry logic:
 * - No retry for 4xx client errors (user/request issues)
 * - Up to 3 retries for 5xx server errors with exponential backoff
 * - Up to 3 retries for network errors
 *
 * @param failureCount - Number of times the query has failed.
 * @param error - The error that caused the failure.
 * @returns True if the query should be retried.
 */
function shouldRetryQuery(failureCount: number, error: unknown): boolean {
  const maxRetries = 3;

  if (failureCount >= maxRetries) {
    return false;
  }

  // Check for HTTP status in error
  if (
    error !== null &&
    typeof error === "object" &&
    "status" in error &&
    typeof error.status === "number"
  ) {
    // Never retry client errors (4xx)
    if (isClientError(error.status)) {
      return false;
    }
  }

  // Retry server errors (5xx) and network errors
  return true;
}

/**
 * Calculate retry delay with exponential backoff.
 *
 * Uses exponential backoff with jitter:
 * - Attempt 1: ~1000ms
 * - Attempt 2: ~2000ms
 * - Attempt 3: ~4000ms
 * Capped at 30 seconds maximum.
 *
 * @param attemptIndex - Zero-based retry attempt index.
 * @returns Delay in milliseconds before next retry.
 */
function calculateRetryDelay(attemptIndex: number): number {
  const baseDelay = 1000;
  const maxDelay = 30_000;
  const exponentialDelay = Math.min(baseDelay * 2 ** attemptIndex, maxDelay);
  // Add jitter (0-10% of delay) to prevent thundering herd
  const jitter = exponentialDelay * Math.random() * 0.1;
  return exponentialDelay + jitter;
}

/**
 * Default QueryClient configuration for TechPulse.
 *
 * Optimized for analytical dashboard data:
 * - Aggressive caching (5 min stale, 10 min gc)
 * - Smart retry logic (no retry for 4xx)
 * - Exponential backoff for transient failures
 */
const DEFAULT_QUERY_CLIENT_CONFIG: QueryClientConfig = {
  defaultOptions: {
    queries: {
      staleTime: STALE_TIME_MS,
      gcTime: GC_TIME_MS,
      retry: shouldRetryQuery,
      retryDelay: calculateRetryDelay,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
};

/**
 * Create a new QueryClient instance with TechPulse defaults.
 *
 * Use this factory to create QueryClient instances. On the server,
 * call this for each request to ensure isolation. On the client,
 * use the singleton pattern via `getQueryClient()`.
 *
 * @param config - Optional config overrides merged with defaults.
 * @returns Configured QueryClient instance.
 *
 * @example
 * ```typescript
 * // Server component prefetching
 * const queryClient = makeQueryClient();
 * await queryClient.prefetchQuery({ queryKey: ['trends'], queryFn: fetchTrends });
 * ```
 */
export function makeQueryClient(config?: QueryClientConfig): QueryClient {
  return new QueryClient({
    ...DEFAULT_QUERY_CLIENT_CONFIG,
    ...config,
    defaultOptions: {
      ...DEFAULT_QUERY_CLIENT_CONFIG.defaultOptions,
      ...config?.defaultOptions,
      queries: {
        ...DEFAULT_QUERY_CLIENT_CONFIG.defaultOptions?.queries,
        ...config?.defaultOptions?.queries,
      },
      mutations: {
        ...DEFAULT_QUERY_CLIENT_CONFIG.defaultOptions?.mutations,
        ...config?.defaultOptions?.mutations,
      },
    },
  });
}

/**
 * Browser-side QueryClient singleton.
 *
 * Lazily initialized on first access. Only exists in browser context.
 */
let browserQueryClient: QueryClient | undefined;

/**
 * Get or create the QueryClient instance.
 *
 * Implements the Next.js App Router pattern:
 * - Server: Always creates a new client (request isolation)
 * - Browser: Returns singleton (cache persistence across navigations)
 *
 * @returns QueryClient instance appropriate for the current environment.
 *
 * @example
 * ```typescript
 * // In a client component or provider
 * const queryClient = getQueryClient();
 * ```
 */
export function getQueryClient(): QueryClient {
  // Server: always create new client for request isolation
  if (typeof window === "undefined") {
    return makeQueryClient();
  }

  // Browser: use singleton for cache persistence
  if (!browserQueryClient) {
    browserQueryClient = makeQueryClient();
  }

  return browserQueryClient;
}
