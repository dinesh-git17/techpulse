/**
 * Query Key Factory for trends and technologies data.
 *
 * Implements the factory pattern for type-safe, refactor-friendly query keys.
 * All keys are readonly tuples to prevent accidental mutation.
 *
 * @module features/trends/keys
 * @see https://tanstack.com/query/latest/docs/framework/react/community/lukemorales-query-key-factory
 */

/**
 * Filter parameters for trends queries.
 *
 * Maps to the /api/v1/trends endpoint query parameters.
 */
export interface TrendFilters {
  /** Comma-separated technology keys (e.g., "python,react"). Required. */
  readonly techIds: string;
  /** Start date in ISO format (YYYY-MM-DD). Defaults to 12 months before end_date. */
  readonly startDate?: string;
  /** End date in ISO format (YYYY-MM-DD). Defaults to today. */
  readonly endDate?: string;
}

/**
 * Filter parameters for technologies queries.
 *
 * The /api/v1/technologies endpoint currently has no query parameters,
 * but this interface allows for future extension.
 */
export interface TechnologyFilters {
  /** Placeholder for future filtering capability. */
  readonly _placeholder?: never;
}

/**
 * Query key factory for trend-related queries.
 *
 * Provides hierarchical keys for granular cache invalidation:
 * - `trendKeys.all` - Invalidates all trend queries
 * - `trendKeys.lists()` - Invalidates all trend list queries
 * - `trendKeys.list(filters)` - Specific filtered list query
 * - `trendKeys.details()` - Invalidates all trend detail queries
 * - `trendKeys.detail(id)` - Specific trend detail query
 *
 * @example
 * ```typescript
 * // In a query hook
 * useQuery({
 *   queryKey: trendKeys.list({ period: '30d' }),
 *   queryFn: () => fetchTrends({ period: '30d' }),
 * });
 *
 * // Invalidate all trend lists
 * queryClient.invalidateQueries({ queryKey: trendKeys.lists() });
 * ```
 */
export const trendKeys = {
  /**
   * Root key for all trend queries.
   * Use for invalidating the entire trend cache.
   */
  all: ["trends"] as const,

  /**
   * Key prefix for all trend list queries.
   * Use for invalidating all filtered lists.
   */
  lists: () => [...trendKeys.all, "list"] as const,

  /**
   * Key for a specific filtered trend list query.
   *
   * @param filters - Optional filter parameters.
   * @returns Readonly query key tuple.
   */
  list: (filters?: TrendFilters) =>
    [...trendKeys.lists(), filters ?? {}] as const,

  /**
   * Key prefix for all trend detail queries.
   * Use for invalidating all detail views.
   */
  details: () => [...trendKeys.all, "detail"] as const,

  /**
   * Key for a specific trend detail query.
   *
   * @param id - Unique trend identifier.
   * @returns Readonly query key tuple.
   */
  detail: (id: string) => [...trendKeys.details(), id] as const,
} as const;

/**
 * Query key factory for technology-related queries.
 *
 * Provides hierarchical keys for granular cache invalidation:
 * - `technologyKeys.all` - Invalidates all technology queries
 * - `technologyKeys.lists()` - Invalidates all technology list queries
 * - `technologyKeys.list(filters)` - Specific filtered list query
 * - `technologyKeys.details()` - Invalidates all technology detail queries
 * - `technologyKeys.detail(id)` - Specific technology detail query
 *
 * @example
 * ```typescript
 * // In a query hook
 * useQuery({
 *   queryKey: technologyKeys.list({ category: 'frontend' }),
 *   queryFn: () => fetchTechnologies({ category: 'frontend' }),
 * });
 *
 * // Invalidate all technology data
 * queryClient.invalidateQueries({ queryKey: technologyKeys.all });
 * ```
 */
export const technologyKeys = {
  /**
   * Root key for all technology queries.
   * Use for invalidating the entire technology cache.
   */
  all: ["technologies"] as const,

  /**
   * Key prefix for all technology list queries.
   * Use for invalidating all filtered lists.
   */
  lists: () => [...technologyKeys.all, "list"] as const,

  /**
   * Key for a specific filtered technology list query.
   *
   * @param filters - Optional filter parameters.
   * @returns Readonly query key tuple.
   */
  list: (filters?: TechnologyFilters) =>
    [...technologyKeys.lists(), filters ?? {}] as const,

  /**
   * Key prefix for all technology detail queries.
   * Use for invalidating all detail views.
   */
  details: () => [...technologyKeys.all, "detail"] as const,

  /**
   * Key for a specific technology detail query.
   *
   * @param id - Unique technology identifier.
   * @returns Readonly query key tuple.
   */
  detail: (id: string) => [...technologyKeys.details(), id] as const,
} as const;

/**
 * Type helper to extract the return type of a query key factory function.
 *
 * @example
 * ```typescript
 * type TrendListKey = QueryKeyOf<typeof trendKeys.list>;
 * // Result: readonly ["trends", "list", TrendFilters | {}]
 * ```
 */
export type QueryKeyOf<T extends (...args: never[]) => readonly unknown[]> =
  ReturnType<T>;
