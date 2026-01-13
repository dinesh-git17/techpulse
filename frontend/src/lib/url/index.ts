/**
 * URL state management utilities for the dashboard.
 *
 * Provides type-safe URL parameter parsing, validation, and serialization
 * for deep linking and shareable dashboard states.
 *
 * @module lib/url
 */

export {
  DEFAULT_LOOKBACK_MONTHS,
  getDefaultEndDate,
  getDefaultStartDate,
  IsoDateSchema,
  MAX_TECH_IDS,
  parseDashboardParams,
  parseTechIdsString,
  serializeTechIds,
  TechIdsSchema,
  toRawParams,
} from "./schemas";

export type {
  ParamCorrection,
  ParsedDashboardParams,
  ParseResult,
  RawDashboardParams,
} from "./schemas";

export {
  dashboardSearchParams,
  defaultParserOptions,
  parseAsIsoDate,
  parseAsTechIds,
  searchParamKeys,
} from "./parsers";

export type { DashboardSearchParams } from "./parsers";
