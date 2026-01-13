/**
 * TanStack Query hooks for trends and technologies data.
 *
 * Provides type-safe data fetching with Zod validation, leveraging
 * the infrastructure from the API integration layer.
 *
 * @module features/trends/queries
 */

import {
  useQuery,
  useSuspenseQuery,
  type UseQueryResult,
  type UseSuspenseQueryResult,
  type QueryClient,
} from "@tanstack/react-query";

import { apiClient, normalizeError } from "@/lib/api/client";
import {
  SchemaValidationError,
  type SchemaFieldError,
} from "@/lib/api/fetcher";

import { trendKeys, technologyKeys, type TrendFilters } from "./keys";
import {
  TechnologiesResponseSchema,
  TrendsResponseSchema,
  type TechnologiesResponse,
  type TrendsResponse,
} from "./schemas";

/**
 * Build URL search params from trend filters.
 *
 * @param filters - Trend filter parameters.
 * @returns URL query string (without leading ?).
 */
function buildTrendQueryParams(filters: TrendFilters): string {
  const params = new URLSearchParams();

  params.set("tech_ids", filters.techIds);

  if (filters.startDate) {
    params.set("start_date", filters.startDate);
  }

  if (filters.endDate) {
    params.set("end_date", filters.endDate);
  }

  return params.toString();
}

/**
 * Fetch technologies from the API with schema validation.
 *
 * @returns Validated technologies response.
 * @throws {SchemaValidationError} If response fails validation.
 * @throws {ApiError} If the request fails.
 */
async function fetchTechnologies(): Promise<TechnologiesResponse> {
  let rawResponse: unknown;

  try {
    rawResponse = await apiClient.get("api/v1/technologies").json();
  } catch (error) {
    throw await normalizeError(error);
  }

  const parseResult = TechnologiesResponseSchema.safeParse(rawResponse);

  if (!parseResult.success) {
    const fieldErrors: SchemaFieldError[] = parseResult.error.errors.map(
      (issue) => ({
        path: issue.path,
        message: issue.message,
        code: issue.code,
      }),
    );
    throw new SchemaValidationError(
      `Technologies response validation failed with ${fieldErrors.length} errors`,
      fieldErrors,
      rawResponse,
    );
  }

  return parseResult.data;
}

/**
 * Fetch trends from the API with schema validation.
 *
 * @param filters - Required filter parameters including tech_ids.
 * @returns Validated trends response.
 * @throws {SchemaValidationError} If response fails validation.
 * @throws {ApiError} If the request fails.
 */
async function fetchTrends(filters: TrendFilters): Promise<TrendsResponse> {
  const queryString = buildTrendQueryParams(filters);
  let rawResponse: unknown;

  try {
    rawResponse = await apiClient.get(`api/v1/trends?${queryString}`).json();
  } catch (error) {
    throw await normalizeError(error);
  }

  const parseResult = TrendsResponseSchema.safeParse(rawResponse);

  if (!parseResult.success) {
    const fieldErrors: SchemaFieldError[] = parseResult.error.errors.map(
      (issue) => ({
        path: issue.path,
        message: issue.message,
        code: issue.code,
      }),
    );
    throw new SchemaValidationError(
      `Trends response validation failed with ${fieldErrors.length} errors`,
      fieldErrors,
      rawResponse,
    );
  }

  return parseResult.data;
}

/**
 * Hook options for useTechnologies.
 */
export interface UseTechnologiesOptions {
  /** Whether the query is enabled. Defaults to true. */
  readonly enabled?: boolean;
}

/**
 * Fetch the technology catalog.
 *
 * Returns all available technologies that can be used for trend queries.
 * Data is cached according to QueryClient defaults (5 min stale time).
 *
 * @param options - Optional query configuration.
 * @returns Query result with technologies data.
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useTechnologies();
 *
 * if (isLoading) return <DataSkeleton variant="list" />;
 * if (error) return <ErrorDisplay error={error} />;
 *
 * return (
 *   <ul>
 *     {data.data.map((tech) => (
 *       <li key={tech.key}>{tech.name}</li>
 *     ))}
 *   </ul>
 * );
 * ```
 */
export function useTechnologies(
  options: UseTechnologiesOptions = {},
): UseQueryResult<TechnologiesResponse, Error> {
  const { enabled = true } = options;

  return useQuery({
    queryKey: technologyKeys.list(),
    queryFn: fetchTechnologies,
    enabled,
  });
}

/**
 * Suspense-enabled hook to fetch the technology catalog.
 *
 * Suspends during loading and throws on error. Use with Suspense
 * and QueryErrorBoundary.
 *
 * @returns Query result with technologies data (never undefined).
 *
 * @example
 * ```tsx
 * // Wrap with Suspense and QueryErrorBoundary
 * function TechnologiesList() {
 *   const { data } = useTechnologiesSuspense();
 *   return <ul>{data.data.map(tech => <li key={tech.key}>{tech.name}</li>)}</ul>;
 * }
 * ```
 */
export function useTechnologiesSuspense(): UseSuspenseQueryResult<
  TechnologiesResponse,
  Error
> {
  return useSuspenseQuery({
    queryKey: technologyKeys.list(),
    queryFn: fetchTechnologies,
  });
}

/**
 * Hook options for useTrends.
 */
export interface UseTrendsOptions {
  /** Filter parameters. Required: techIds. */
  readonly filters: TrendFilters;
  /** Whether the query is enabled. Defaults to true. */
  readonly enabled?: boolean;
}

/**
 * Fetch trend data for specified technologies.
 *
 * Returns time series data showing job posting mentions over time.
 * Requires at least one technology ID in the filters.
 *
 * @param options - Query options including required filters.
 * @returns Query result with trends data.
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useTrends({
 *   filters: { techIds: 'python,react' },
 * });
 *
 * if (isLoading) return <DataSkeleton variant="detail" />;
 * if (error) return <ErrorDisplay error={error} />;
 *
 * return <TrendChart trends={data.data} />;
 * ```
 */
export function useTrends(
  options: UseTrendsOptions,
): UseQueryResult<TrendsResponse, Error> {
  const { filters, enabled = true } = options;

  return useQuery({
    queryKey: trendKeys.list(filters),
    queryFn: () => fetchTrends(filters),
    enabled,
  });
}

/**
 * Suspense-enabled hook to fetch trend data.
 *
 * Suspends during loading and throws on error. Use with Suspense
 * and QueryErrorBoundary.
 *
 * @param filters - Required filter parameters including techIds.
 * @returns Query result with trends data (never undefined).
 *
 * @example
 * ```tsx
 * function TrendChart({ techIds }: { techIds: string }) {
 *   const { data } = useTrendsSuspense({ techIds });
 *   return <Chart data={data.data} />;
 * }
 * ```
 */
export function useTrendsSuspense(
  filters: TrendFilters,
): UseSuspenseQueryResult<TrendsResponse, Error> {
  return useSuspenseQuery({
    queryKey: trendKeys.list(filters),
    queryFn: () => fetchTrends(filters),
  });
}

/**
 * Prefetch technologies data on the server.
 *
 * Call in Server Components to prefetch data before rendering.
 * The prefetched data is included in the dehydrated state for
 * hydration on the client.
 *
 * @param queryClient - QueryClient instance from the server.
 *
 * @example
 * ```tsx
 * // In a Server Component
 * export default async function TechnologiesPage() {
 *   const queryClient = makeQueryClient();
 *   await prefetchTechnologies(queryClient);
 *
 *   return (
 *     <HydrationBoundary state={dehydrate(queryClient)}>
 *       <TechnologiesList />
 *     </HydrationBoundary>
 *   );
 * }
 * ```
 */
export async function prefetchTechnologies(
  queryClient: QueryClient,
): Promise<void> {
  await queryClient.prefetchQuery({
    queryKey: technologyKeys.list(),
    queryFn: fetchTechnologies,
  });
}

/**
 * Prefetch trends data on the server.
 *
 * Call in Server Components to prefetch trend data before rendering.
 * The prefetched data is included in the dehydrated state for
 * hydration on the client.
 *
 * @param queryClient - QueryClient instance from the server.
 * @param filters - Required filter parameters including techIds.
 *
 * @example
 * ```tsx
 * // In a Server Component
 * export default async function TrendsPage() {
 *   const queryClient = makeQueryClient();
 *   await prefetchTrends(queryClient, { techIds: 'python,react' });
 *
 *   return (
 *     <HydrationBoundary state={dehydrate(queryClient)}>
 *       <TrendChart techIds="python,react" />
 *     </HydrationBoundary>
 *   );
 * }
 * ```
 */
export async function prefetchTrends(
  queryClient: QueryClient,
  filters: TrendFilters,
): Promise<void> {
  await queryClient.prefetchQuery({
    queryKey: trendKeys.list(filters),
    queryFn: () => fetchTrends(filters),
  });
}
