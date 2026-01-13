/**
 * HTTP client configuration for TechPulse API communication.
 *
 * @module lib/api/client
 */

import ky, { type KyInstance, type Options, HTTPError } from "ky";

/**
 * Standard error response structure from the FastAPI backend.
 */
export interface ApiErrorResponse {
  /** Machine-readable error code. */
  readonly code: string;
  /** Human-readable error message. */
  readonly message: string;
  /** Optional field-level validation errors. */
  readonly details?: ReadonlyArray<FieldValidationError>;
}

/**
 * Field-level validation error from Pydantic.
 */
export interface FieldValidationError {
  /** JSON path to the invalid field. */
  readonly loc: ReadonlyArray<string | number>;
  /** Validation error message. */
  readonly msg: string;
  /** Pydantic error type identifier. */
  readonly type: string;
}

/**
 * Normalized error thrown by the API client.
 *
 * Wraps both network errors and structured API error responses
 * into a consistent shape for error boundary handling.
 */
export class ApiError extends Error {
  /** HTTP status code (0 for network errors). */
  readonly status: number;
  /** Machine-readable error code from backend. */
  readonly code: string;
  /** Field-level validation errors if present. */
  readonly details: ReadonlyArray<FieldValidationError>;
  /** Original response body for debugging. */
  readonly rawResponse: unknown;

  /**
   * Create a normalized API error.
   *
   * @param message - Human-readable error message.
   * @param status - HTTP status code.
   * @param code - Machine-readable error code.
   * @param details - Field validation errors.
   * @param rawResponse - Original response for debugging.
   */
  constructor(
    message: string,
    status: number,
    code: string,
    details: ReadonlyArray<FieldValidationError> = [],
    rawResponse: unknown = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.rawResponse = rawResponse;
  }

  /**
   * Check if this error is a client error (4xx status).
   *
   * @returns True if status is 400-499.
   */
  isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }

  /**
   * Check if this error is a server error (5xx status).
   *
   * @returns True if status is 500-599.
   */
  isServerError(): boolean {
    return this.status >= 500 && this.status < 600;
  }

  /**
   * Check if this error is a network error (no response received).
   *
   * @returns True if status is 0.
   */
  isNetworkError(): boolean {
    return this.status === 0;
  }
}

/**
 * Type guard to check if a value is an ApiErrorResponse.
 *
 * @param value - Value to check.
 * @returns True if value matches ApiErrorResponse shape.
 */
function isApiErrorResponse(value: unknown): value is ApiErrorResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.code === "string" && typeof candidate.message === "string"
  );
}

/**
 * Parse an HTTPError into a normalized ApiError.
 *
 * Attempts to extract structured error information from the response body.
 * Falls back to generic error message if parsing fails.
 *
 * @param httpError - The HTTPError from ky.
 * @returns Normalized ApiError with extracted details.
 */
async function parseHttpError(httpError: HTTPError): Promise<ApiError> {
  const status = httpError.response.status;
  let rawResponse: unknown = null;
  let errorResponse: Partial<ApiErrorResponse> = {};

  try {
    rawResponse = await httpError.response.clone().json();
    if (isApiErrorResponse(rawResponse)) {
      errorResponse = rawResponse;
    }
  } catch {
    // Response body is not JSON or parsing failed
  }

  const message =
    errorResponse.message ?? httpError.message ?? `HTTP ${status} Error`;
  const code = errorResponse.code ?? `HTTP_${status}`;
  const details = errorResponse.details ?? [];

  return new ApiError(message, status, code, details, rawResponse);
}

/**
 * Convert any error into a normalized ApiError.
 *
 * @param error - Unknown error to normalize.
 * @returns Normalized ApiError.
 */
export async function normalizeError(error: unknown): Promise<ApiError> {
  if (error instanceof ApiError) {
    return error;
  }

  if (error instanceof HTTPError) {
    return parseHttpError(error);
  }

  if (error instanceof Error) {
    return new ApiError(error.message, 0, "NETWORK_ERROR", [], null);
  }

  return new ApiError(
    "An unknown error occurred",
    0,
    "UNKNOWN_ERROR",
    [],
    null,
  );
}

/**
 * Resolve the API base URL from environment.
 *
 * @returns The configured API URL or default localhost.
 */
function resolveApiBaseUrl(): string {
  const envApiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envApiUrl) {
    return envApiUrl;
  }
  // Default to localhost FastAPI server for development
  return "http://localhost:8000";
}

/**
 * Default configuration for the ky HTTP client.
 */
const DEFAULT_CLIENT_OPTIONS: Options = {
  prefixUrl: resolveApiBaseUrl(),
  timeout: 30_000,
  retry: {
    limit: 3,
    methods: ["get", "head", "options"],
    statusCodes: [408, 500, 502, 503, 504],
    backoffLimit: 3000,
  },
};

/**
 * Pre-configured ky instance for TechPulse API requests.
 *
 * Features:
 * - Base URL from NEXT_PUBLIC_API_URL environment variable
 * - 30 second request timeout
 * - Automatic retry for transient server errors (5xx)
 * - No retry for client errors (4xx)
 *
 * Use with `normalizeError` for consistent error handling:
 *
 * @example
 * ```typescript
 * import { apiClient, normalizeError } from '@/lib/api/client';
 *
 * try {
 *   const data = await apiClient.get('api/v1/technologies').json();
 * } catch (error) {
 *   const apiError = await normalizeError(error);
 *   console.error(apiError.code, apiError.message);
 * }
 * ```
 */
export const apiClient: KyInstance = ky.create(DEFAULT_CLIENT_OPTIONS);

/**
 * Create a new ky instance with custom options merged with defaults.
 *
 * Use this factory when you need request-specific configuration
 * while retaining the standard base URL and timeout settings.
 *
 * @param options - Custom ky options to merge with defaults.
 * @returns New ky instance with merged configuration.
 *
 * @example
 * ```typescript
 * const customClient = createApiClient({ timeout: 60_000 });
 * ```
 */
export function createApiClient(options: Options = {}): KyInstance {
  return ky.create({
    ...DEFAULT_CLIENT_OPTIONS,
    ...options,
  });
}
