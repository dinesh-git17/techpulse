/**
 * nuqs parsers for dashboard URL search parameters.
 *
 * Provides type-safe serialization and deserialization of URL parameters
 * for use with nuqs hooks. All parsers use replaceState by default to
 * avoid polluting browser history.
 *
 * @module lib/url/parsers
 */

import { createParser, parseAsString } from "nuqs";

import {
  getDefaultEndDate,
  getDefaultStartDate,
  MAX_TECH_IDS,
  parseTechIdsString,
  serializeTechIds,
} from "./schemas";

/**
 * Parser for technology IDs stored as comma-separated string in URL.
 *
 * Handles:
 * - Parsing: comma-separated string → sorted string array
 * - Serializing: string array → sorted comma-separated string
 * - Empty values return empty array (not null)
 *
 * Arrays are automatically sorted alphabetically to ensure consistent
 * cache keys regardless of selection order.
 */
export const parseAsTechIds = createParser({
  parse: (value: string): string[] => {
    const ids = parseTechIdsString(value);
    return [...ids].sort().slice(0, MAX_TECH_IDS);
  },
  serialize: (value: string[]): string => {
    return serializeTechIds(value);
  },
  eq: (a: string[], b: string[]): boolean => {
    if (a.length !== b.length) return false;
    const sortedA = [...a].sort();
    const sortedB = [...b].sort();
    return sortedA.every((val, idx) => val === sortedB[idx]);
  },
});

/**
 * Parser for ISO 8601 date strings (YYYY-MM-DD).
 *
 * Uses string representation directly as URL parameters are already strings.
 * Validation is handled separately in the schema layer.
 */
export const parseAsIsoDate = parseAsString;

/**
 * Search parameter key definitions for the dashboard.
 *
 * Maps semantic names to URL parameter keys matching backend API conventions.
 */
export const searchParamKeys = {
  /** Technology selection parameter key. */
  techIds: "tech_ids",
  /** Start date parameter key. */
  start: "start",
  /** End date parameter key. */
  end: "end",
} as const;

/**
 * Default parser options for dashboard parameters.
 *
 * Uses replaceState to prevent history pollution when filters change.
 */
export const defaultParserOptions = {
  history: "replace",
  shallow: true,
} as const;

/**
 * Dashboard search parameter configuration for nuqs.
 *
 * Provides parser definitions with defaults for all dashboard URL parameters.
 * Use with `useQueryStates` for coordinated multi-parameter updates.
 */
export const dashboardSearchParams = {
  [searchParamKeys.techIds]: parseAsTechIds.withDefault([]),
  [searchParamKeys.start]: parseAsIsoDate.withDefault(getDefaultStartDate()),
  [searchParamKeys.end]: parseAsIsoDate.withDefault(getDefaultEndDate()),
} as const;

/**
 * Type representing the parsed dashboard search parameters from nuqs.
 */
export type DashboardSearchParams = {
  [searchParamKeys.techIds]: string[];
  [searchParamKeys.start]: string;
  [searchParamKeys.end]: string;
};
