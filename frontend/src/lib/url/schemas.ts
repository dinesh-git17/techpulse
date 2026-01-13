/**
 * Zod schemas for dashboard URL search parameters.
 *
 * Defines the contract for URL state management, including validation,
 * constraints, and default values. Used by both server and client contexts.
 *
 * @module lib/url/schemas
 */

import { z } from "zod";

/**
 * Maximum number of technologies allowed in a single URL selection.
 * Prevents excessively long URLs and limits API query complexity.
 */
export const MAX_TECH_IDS = 10;

/**
 * Number of months to look back for the default date range.
 */
export const DEFAULT_LOOKBACK_MONTHS = 12;

/**
 * ISO 8601 date format pattern (YYYY-MM-DD).
 */
const ISO_DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

/**
 * Validate that a string is a valid ISO 8601 date (YYYY-MM-DD) and represents
 * an actual calendar date.
 *
 * @param value - The string to validate.
 * @returns True if valid ISO date, false otherwise.
 */
function isValidIsoDate(value: string): boolean {
  if (!ISO_DATE_PATTERN.test(value)) {
    return false;
  }
  const date = new Date(value + "T00:00:00Z");
  if (Number.isNaN(date.getTime())) {
    return false;
  }
  const [year, month, day] = value.split("-").map(Number);
  return (
    date.getUTCFullYear() === year &&
    date.getUTCMonth() + 1 === month &&
    date.getUTCDate() === day
  );
}

/**
 * Calculate the default start date (12 months before today in UTC).
 *
 * @returns ISO 8601 date string (YYYY-MM-DD).
 */
export function getDefaultStartDate(): string {
  const now = new Date();
  const utcDate = new Date(
    Date.UTC(
      now.getUTCFullYear(),
      now.getUTCMonth() - DEFAULT_LOOKBACK_MONTHS,
      now.getUTCDate(),
    ),
  );
  return utcDate.toISOString().slice(0, 10);
}

/**
 * Calculate the default end date (today in UTC).
 *
 * @returns ISO 8601 date string (YYYY-MM-DD).
 */
export function getDefaultEndDate(): string {
  const now = new Date();
  const utcDate = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()),
  );
  return utcDate.toISOString().slice(0, 10);
}

/**
 * Schema for ISO 8601 date string validation.
 *
 * Validates format (YYYY-MM-DD) and ensures the date is a real calendar date.
 */
export const IsoDateSchema = z.string().refine(isValidIsoDate, {
  message: "Invalid date format. Expected YYYY-MM-DD.",
});

/**
 * Schema for technology ID array derived from comma-separated URL string.
 *
 * Constraints:
 * - Maximum 10 items
 * - Alphabetically sorted for cache consistency
 * - Empty strings filtered out
 */
export const TechIdsSchema = z
  .array(z.string().min(1))
  .max(MAX_TECH_IDS)
  .transform((ids) => [...ids].sort());

/**
 * Raw URL search parameters as received from the browser or server.
 *
 * All values are optional strings matching URL query parameter format.
 */
export interface RawDashboardParams {
  /** Comma-separated technology keys. */
  readonly tech_ids?: string;
  /** Start date in YYYY-MM-DD format. */
  readonly start?: string;
  /** End date in YYYY-MM-DD format. */
  readonly end?: string;
}

/**
 * Parsed and validated dashboard parameters with typed values.
 *
 * Guaranteed to have valid values after parsing, with defaults applied.
 */
export interface ParsedDashboardParams {
  /** Array of selected technology keys, alphabetically sorted. */
  readonly techIds: readonly string[];
  /** Start date in YYYY-MM-DD format. */
  readonly startDate: string;
  /** End date in YYYY-MM-DD format. */
  readonly endDate: string;
}

/**
 * Validation result containing parsed params and any corrections made.
 */
export interface ParseResult {
  /** Validated and normalized parameters. */
  readonly params: ParsedDashboardParams;
  /** List of corrections applied during parsing. */
  readonly corrections: readonly ParamCorrection[];
}

/**
 * Describes a correction made during parameter parsing.
 */
export interface ParamCorrection {
  /** Type of correction applied. */
  readonly type:
    | "invalid_date_format"
    | "impossible_date_range"
    | "excess_tech_ids"
    | "unknown_tech_ids";
  /** User-friendly message describing the correction. */
  readonly message: string;
}

/**
 * Parse a comma-separated string into an array of technology IDs.
 *
 * @param value - Comma-separated string or undefined.
 * @returns Array of non-empty technology IDs.
 */
export function parseTechIdsString(value: string | undefined): string[] {
  if (!value || value.trim() === "") {
    return [];
  }
  return value
    .split(",")
    .map((id) => id.trim())
    .filter((id) => id.length > 0);
}

/**
 * Serialize an array of technology IDs to a comma-separated string.
 *
 * @param ids - Array of technology IDs.
 * @returns Alphabetically sorted, comma-separated string. Empty string if no IDs.
 */
export function serializeTechIds(ids: readonly string[]): string {
  if (ids.length === 0) {
    return "";
  }
  return [...ids].sort().join(",");
}

/**
 * Parse raw URL parameters into validated, typed dashboard parameters.
 *
 * Applies the following transformations:
 * - Invalid dates fall back to defaults (T-12M for start, today for end)
 * - Date ranges where start >= end are corrected
 * - Excess tech_ids (>10) are truncated
 * - Tech_ids are alphabetically sorted
 *
 * @param raw - Raw URL search parameters.
 * @param knownTechIds - Optional set of valid technology IDs for filtering.
 * @returns Parsed parameters with list of any corrections applied.
 */
export function parseDashboardParams(
  raw: RawDashboardParams,
  knownTechIds?: ReadonlySet<string>,
): ParseResult {
  const corrections: ParamCorrection[] = [];

  const rawTechIds = parseTechIdsString(raw.tech_ids);
  let techIds = rawTechIds;

  if (knownTechIds && knownTechIds.size > 0) {
    const filtered = techIds.filter((id) => knownTechIds.has(id));
    if (filtered.length < techIds.length) {
      corrections.push({
        type: "unknown_tech_ids",
        message: "Some technologies were not recognized.",
      });
      techIds = filtered;
    }
  }

  if (techIds.length > MAX_TECH_IDS) {
    corrections.push({
      type: "excess_tech_ids",
      message: `Selection limited to ${MAX_TECH_IDS} technologies.`,
    });
    techIds = techIds.slice(0, MAX_TECH_IDS);
  }

  const sortedTechIds = [...techIds].sort();

  const defaultStart = getDefaultStartDate();
  const defaultEnd = getDefaultEndDate();

  let startDate = defaultStart;
  let endDate = defaultEnd;

  if (raw.start) {
    if (isValidIsoDate(raw.start)) {
      startDate = raw.start;
    } else {
      corrections.push({
        type: "invalid_date_format",
        message: "Invalid date format. Showing last 12 months.",
      });
    }
  }

  if (raw.end) {
    if (isValidIsoDate(raw.end)) {
      endDate = raw.end;
    } else {
      corrections.push({
        type: "invalid_date_format",
        message: "Invalid date format. Showing last 12 months.",
      });
    }
  }

  if (startDate >= endDate) {
    corrections.push({
      type: "impossible_date_range",
      message: "End date adjusted to be after start date.",
    });
    const startDateObj = new Date(startDate + "T00:00:00Z");
    startDateObj.setUTCMonth(startDateObj.getUTCMonth() + 1);
    endDate = startDateObj.toISOString().slice(0, 10);
  }

  return {
    params: {
      techIds: sortedTechIds,
      startDate,
      endDate,
    },
    corrections,
  };
}

/**
 * Convert parsed dashboard parameters back to raw URL format.
 *
 * @param params - Parsed dashboard parameters.
 * @returns Raw parameters suitable for URL serialization.
 */
export function toRawParams(params: ParsedDashboardParams): RawDashboardParams {
  return {
    tech_ids: serializeTechIds(params.techIds),
    start: params.startDate,
    end: params.endDate,
  };
}
