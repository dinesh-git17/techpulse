/**
 * Zod schemas for trends and technologies API responses.
 *
 * These schemas validate API responses at runtime, ensuring the frontend
 * receives data matching the expected contract from the FastAPI backend.
 *
 * @module features/trends/schemas
 */

import { z } from "zod";

/**
 * Schema for API response metadata.
 *
 * Present in all API responses, contains request tracking and pagination info.
 */
export const MetaSchema = z.object({
  /** UUID identifying the request for correlation. */
  request_id: z.string(),
  /** ISO 8601 UTC timestamp of the response. */
  timestamp: z.string(),
  /** Total number of items available (optional for non-paginated responses). */
  total_count: z.number().int().nonnegative().nullable(),
  /** Current page number, 1-indexed (optional). */
  page: z.number().int().positive().nullable(),
  /** Number of items per page (optional). */
  page_size: z.number().int().positive().nullable(),
  /** Whether more pages exist (optional). */
  has_more: z.boolean().nullable(),
});

/**
 * Inferred TypeScript type for API metadata.
 */
export type Meta = z.infer<typeof MetaSchema>;

/**
 * Schema for a technology entity.
 *
 * Represents a single technology in the catalog.
 */
export const TechnologySchema = z.object({
  /** Unique identifier (e.g., "python", "react"). */
  key: z.string().min(1),
  /** Human-readable display name (e.g., "Python", "React"). */
  name: z.string().min(1),
  /** Technology classification (e.g., "Language", "Framework"). */
  category: z.string().min(1),
});

/**
 * Inferred TypeScript type for a technology.
 */
export type Technology = z.infer<typeof TechnologySchema>;

/**
 * Schema for a single trend data point.
 *
 * Represents job mention count for a specific month.
 */
export const TrendDataPointSchema = z.object({
  /** Month in YYYY-MM format. */
  month: z.string().regex(/^\d{4}-\d{2}$/, "Month must be in YYYY-MM format"),
  /** Number of job postings mentioning this technology. */
  count: z.number().int().nonnegative(),
});

/**
 * Inferred TypeScript type for a trend data point.
 */
export type TrendDataPoint = z.infer<typeof TrendDataPointSchema>;

/**
 * Schema for technology trend data.
 *
 * Contains the time series data for a single technology.
 */
export const TechnologyTrendSchema = z.object({
  /** Unique technology identifier. */
  tech_key: z.string().min(1),
  /** Human-readable display name. */
  name: z.string().min(1),
  /** Monthly data points in chronological order. */
  data: z.array(TrendDataPointSchema),
});

/**
 * Inferred TypeScript type for technology trend data.
 */
export type TechnologyTrend = z.infer<typeof TechnologyTrendSchema>;

/**
 * Create a response envelope schema for a given data type.
 *
 * @typeParam T - Zod schema type for the data payload.
 * @param dataSchema - Zod schema for the data field.
 * @returns Response envelope schema wrapping the data type.
 */
function createResponseEnvelopeSchema<T extends z.ZodTypeAny>(dataSchema: T) {
  return z.object({
    /** Response payload. */
    data: dataSchema,
    /** Response metadata. */
    meta: MetaSchema,
  });
}

/**
 * Schema for the /api/v1/technologies endpoint response.
 *
 * Returns a list of all available technologies.
 */
export const TechnologiesResponseSchema = createResponseEnvelopeSchema(
  z.array(TechnologySchema),
);

/**
 * Inferred TypeScript type for technologies response.
 */
export type TechnologiesResponse = z.infer<typeof TechnologiesResponseSchema>;

/**
 * Schema for the /api/v1/trends endpoint response.
 *
 * Returns trend data for requested technologies.
 */
export const TrendsResponseSchema = createResponseEnvelopeSchema(
  z.array(TechnologyTrendSchema),
);

/**
 * Inferred TypeScript type for trends response.
 */
export type TrendsResponse = z.infer<typeof TrendsResponseSchema>;
