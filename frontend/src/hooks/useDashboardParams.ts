/**
 * Hook for managing dashboard URL search parameters.
 *
 * Provides a type-safe interface for reading and updating URL state,
 * with automatic array canonicalization and replaceState navigation.
 *
 * @module hooks/useDashboardParams
 */

"use client";

import { useCallback, useMemo } from "react";

import { useQueryStates } from "nuqs";

import {
  dashboardSearchParams,
  defaultParserOptions,
  searchParamKeys,
} from "@/lib/url";

/**
 * Date range representation for dashboard filters.
 */
export interface DateRange {
  /** Start date in ISO 8601 format (YYYY-MM-DD). */
  readonly startDate: string;
  /** End date in ISO 8601 format (YYYY-MM-DD). */
  readonly endDate: string;
}

/**
 * Return type for the useDashboardParams hook.
 */
export interface UseDashboardParamsReturn {
  /** Currently selected technology IDs, alphabetically sorted. */
  readonly selectedTechs: readonly string[];
  /** Update selected technologies. Array will be sorted automatically. */
  readonly setTechs: (techs: string[]) => void;
  /** Current date range for trend data. */
  readonly dateRange: DateRange;
  /** Update date range. */
  readonly setDateRange: (range: Partial<DateRange>) => void;
  /** Whether the URL state is being initialized (first render). */
  readonly isReady: boolean;
}

/**
 * Options for configuring the dashboard params hook.
 */
export interface UseDashboardParamsOptions {
  /**
   * Enable throttling of URL updates to reduce browser history spam.
   * Defaults to 50ms.
   */
  readonly throttleMs?: number;
}

/**
 * Manages dashboard filter state via URL search parameters.
 *
 * Provides a clean abstraction over URL manipulation with:
 * - Automatic array canonicalization (alphabetical sorting)
 * - Replace-only navigation (no history pollution)
 * - Type-safe getters and setters
 * - SSR-safe hydration handling
 *
 * @param options - Configuration options for the hook.
 * @returns Dashboard parameter state and update functions.
 *
 * @example
 * ```tsx
 * function DashboardFilters() {
 *   const { selectedTechs, setTechs, dateRange, setDateRange } = useDashboardParams();
 *
 *   return (
 *     <>
 *       <TechnologySelector
 *         selected={selectedTechs}
 *         onChange={setTechs}
 *       />
 *       <DateRangePicker
 *         startDate={dateRange.startDate}
 *         endDate={dateRange.endDate}
 *         onChange={setDateRange}
 *       />
 *     </>
 *   );
 * }
 * ```
 */
export function useDashboardParams(
  options: UseDashboardParamsOptions = {},
): UseDashboardParamsReturn {
  const { throttleMs = 50 } = options;

  const queryOptions = useMemo(
    () => ({
      history: defaultParserOptions.history,
      shallow: defaultParserOptions.shallow,
      throttleMs,
    }),
    [throttleMs],
  );

  const [params, setParams] = useQueryStates(
    dashboardSearchParams,
    queryOptions,
  );

  const selectedTechs = useMemo(() => {
    const techs = params[searchParamKeys.techIds];
    return [...techs].sort();
  }, [params]);

  const dateRange: DateRange = useMemo(
    () => ({
      startDate: params[searchParamKeys.start],
      endDate: params[searchParamKeys.end],
    }),
    [params],
  );

  const setTechs = useCallback(
    (techs: string[]) => {
      const sorted = [...techs].sort();
      void setParams({ [searchParamKeys.techIds]: sorted });
    },
    [setParams],
  );

  const setDateRange = useCallback(
    (range: Partial<DateRange>) => {
      const updates: Record<string, string> = {};
      if (range.startDate !== undefined) {
        updates[searchParamKeys.start] = range.startDate;
      }
      if (range.endDate !== undefined) {
        updates[searchParamKeys.end] = range.endDate;
      }
      void setParams(updates);
    },
    [setParams],
  );

  const isReady = params !== null;

  return {
    selectedTechs,
    setTechs,
    dateRange,
    setDateRange,
    isReady,
  };
}
