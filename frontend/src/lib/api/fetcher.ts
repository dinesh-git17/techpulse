/**
 * Type-safe data fetching utilities with Zod schema validation.
 *
 * Implements the "Trust, but Verify" principle: all API responses are
 * validated at runtime against Zod schemas before being returned to components.
 *
 * @module lib/api/fetcher
 */

import {
  useQuery,
  useSuspenseQuery,
  type UseQueryOptions,
  type UseSuspenseQueryOptions,
  type UseQueryResult,
  type UseSuspenseQueryResult,
  type QueryKey,
} from "@tanstack/react-query";
import { type ZodType, ZodError } from "zod";

import { apiClient, normalizeError } from "./client";

/**
 * Individual field error from Zod validation.
 */
export interface SchemaFieldError {
  /** JSON path to the invalid field (e.g., ["data", "items", 0, "name"]). */
  readonly path: ReadonlyArray<string | number>;
  /** Human-readable error message. */
  readonly message: string;
  /** Zod error code (e.g., "invalid_type", "too_small"). */
  readonly code: string;
}

/**
 * Error thrown when API response fails Zod schema validation.
 *
 * Contains detailed information about which fields failed validation,
 * enabling precise error messages in the UI and debugging.
 */
export class SchemaValidationError extends Error {
  /** Machine-readable error code for error boundary handling. */
  readonly code = "SCHEMA_VALIDATION_ERROR" as const;
  /** HTTP status code (always 0 for validation errors). */
  readonly status = 0 as const;
  /** Detailed field-level validation errors. */
  readonly fieldErrors: ReadonlyArray<SchemaFieldError>;
  /** Original response that failed validation. */
  readonly rawResponse: unknown;

  /**
   * Create a schema validation error.
   *
   * @param message - Summary error message.
   * @param fieldErrors - Field-level validation errors.
   * @param rawResponse - Original API response for debugging.
   */
  constructor(
    message: string,
    fieldErrors: ReadonlyArray<SchemaFieldError>,
    rawResponse: unknown,
  ) {
    super(message);
    this.name = "SchemaValidationError";
    this.fieldErrors = fieldErrors;
    this.rawResponse = rawResponse;
  }

  /**
   * Create SchemaValidationError from a ZodError.
   *
   * @param zodError - The Zod validation error.
   * @param rawResponse - Original response that failed validation.
   * @returns SchemaValidationError with extracted field details.
   */
  static fromZodError(
    zodError: ZodError,
    rawResponse: unknown,
  ): SchemaValidationError {
    const fieldErrors: SchemaFieldError[] = zodError.errors.map((issue) => ({
      path: issue.path,
      message: issue.message,
      code: issue.code,
    }));

    const fieldCount = fieldErrors.length;
    const firstError = fieldErrors[0];
    const message =
      fieldCount === 1 && firstError
        ? `Schema validation failed: ${firstError.message}`
        : `Schema validation failed with ${fieldCount} errors`;

    return new SchemaValidationError(message, fieldErrors, rawResponse);
  }
}

/**
 * Type guard to check if an error is a SchemaValidationError.
 *
 * @param error - Error to check.
 * @returns True if error is a SchemaValidationError.
 */
export function isSchemaValidationError(
  error: unknown,
): error is SchemaValidationError {
  return error instanceof SchemaValidationError;
}

/**
 * Fetch JSON data from an API endpoint and validate against a Zod schema.
 *
 * @typeParam TOutput - The validated output type from the schema.
 * @param endpoint - API endpoint path (relative to base URL).
 * @param schema - Zod schema for response validation.
 * @returns Validated and typed response data.
 * @throws {SchemaValidationError} If response fails schema validation.
 * @throws {ApiError} If the HTTP request fails.
 *
 * @example
 * ```typescript
 * const TechnologySchema = z.object({
 *   id: z.string(),
 *   name: z.string(),
 * });
 *
 * const data = await fetchWithSchema('api/v1/technologies', TechnologySchema);
 * // data is typed as { id: string; name: string }
 * ```
 */
export async function fetchWithSchema<TOutput>(
  endpoint: string,
  schema: ZodType<TOutput>,
): Promise<TOutput> {
  let rawResponse: unknown;

  try {
    rawResponse = await apiClient.get(endpoint).json();
  } catch (error) {
    throw await normalizeError(error);
  }

  const parseResult = schema.safeParse(rawResponse);

  if (!parseResult.success) {
    throw SchemaValidationError.fromZodError(parseResult.error, rawResponse);
  }

  return parseResult.data;
}

/**
 * Create a typed fetcher function for use with TanStack Query.
 *
 * Returns a queryFn that fetches from the endpoint and validates
 * the response against the provided Zod schema.
 *
 * @typeParam TOutput - The validated output type from the schema.
 * @param endpoint - API endpoint path (relative to base URL).
 * @param schema - Zod schema for response validation.
 * @returns A queryFn suitable for useQuery/useSuspenseQuery.
 *
 * @example
 * ```typescript
 * const queryFn = createTypedFetcher('api/v1/trends', TrendsResponseSchema);
 *
 * useQuery({
 *   queryKey: trendKeys.list(),
 *   queryFn,
 * });
 * ```
 */
export function createTypedFetcher<TOutput>(
  endpoint: string,
  schema: ZodType<TOutput>,
): () => Promise<TOutput> {
  return () => fetchWithSchema(endpoint, schema);
}

/**
 * Options for useTypedQuery, extending standard UseQueryOptions.
 *
 * @typeParam TOutput - The validated output type from the schema.
 * @typeParam TError - Error type (defaults to Error).
 * @typeParam TQueryKey - Query key type.
 */
export interface UseTypedQueryOptions<
  TOutput,
  TError = Error,
  TQueryKey extends QueryKey = QueryKey,
> extends Omit<
  UseQueryOptions<TOutput, TError, TOutput, TQueryKey>,
  "queryFn"
> {
  /** API endpoint path (relative to base URL). */
  endpoint: string;
  /** Zod schema for response validation. */
  schema: ZodType<TOutput>;
}

/**
 * Query hook with built-in Zod schema validation.
 *
 * Wraps useQuery to automatically validate API responses against
 * a Zod schema, throwing SchemaValidationError on validation failure.
 *
 * @typeParam TOutput - The validated output type from the schema.
 * @typeParam TError - Error type (defaults to Error).
 * @typeParam TQueryKey - Query key type.
 * @param options - Query options including endpoint and schema.
 * @returns Standard UseQueryResult with validated data.
 *
 * @example
 * ```typescript
 * const { data, isLoading, error } = useTypedQuery({
 *   queryKey: trendKeys.list({ period: '30d' }),
 *   endpoint: 'api/v1/trends?period=30d',
 *   schema: TrendsResponseSchema,
 * });
 *
 * if (isSchemaValidationError(error)) {
 *   console.error('Schema mismatch:', error.fieldErrors);
 * }
 * ```
 */
export function useTypedQuery<
  TOutput,
  TError = Error,
  TQueryKey extends QueryKey = QueryKey,
>(
  options: UseTypedQueryOptions<TOutput, TError, TQueryKey>,
): UseQueryResult<TOutput, TError> {
  const { endpoint, schema, ...queryOptions } = options;

  return useQuery({
    ...queryOptions,
    queryFn: createTypedFetcher(endpoint, schema),
  });
}

/**
 * Options for useSuspenseTypedQuery, extending standard UseSuspenseQueryOptions.
 *
 * @typeParam TOutput - The validated output type from the schema.
 * @typeParam TError - Error type (defaults to Error).
 * @typeParam TQueryKey - Query key type.
 */
export interface UseSuspenseTypedQueryOptions<
  TOutput,
  TError = Error,
  TQueryKey extends QueryKey = QueryKey,
> extends Omit<
  UseSuspenseQueryOptions<TOutput, TError, TOutput, TQueryKey>,
  "queryFn"
> {
  /** API endpoint path (relative to base URL). */
  endpoint: string;
  /** Zod schema for response validation. */
  schema: ZodType<TOutput>;
}

/**
 * Suspense-enabled query hook with built-in Zod schema validation.
 *
 * Wraps useSuspenseQuery to automatically validate API responses against
 * a Zod schema. Suspends during loading and throws on error (for Error Boundary).
 *
 * @typeParam TOutput - The validated output type from the schema.
 * @typeParam TError - Error type (defaults to Error).
 * @typeParam TQueryKey - Query key type.
 * @param options - Query options including endpoint and schema.
 * @returns UseSuspenseQueryResult with validated data (never undefined).
 *
 * @example
 * ```typescript
 * // In a component wrapped with Suspense and ErrorBoundary
 * const { data } = useSuspenseTypedQuery({
 *   queryKey: trendKeys.list(),
 *   endpoint: 'api/v1/trends',
 *   schema: TrendsResponseSchema,
 * });
 *
 * // data is always defined (no loading state to handle)
 * return <TrendsList trends={data.items} />;
 * ```
 */
export function useSuspenseTypedQuery<
  TOutput,
  TError = Error,
  TQueryKey extends QueryKey = QueryKey,
>(
  options: UseSuspenseTypedQueryOptions<TOutput, TError, TQueryKey>,
): UseSuspenseQueryResult<TOutput, TError> {
  const { endpoint, schema, ...queryOptions } = options;

  return useSuspenseQuery({
    ...queryOptions,
    queryFn: createTypedFetcher(endpoint, schema),
  });
}
