/**
 * Tests for HTTP client configuration and error handling.
 *
 * @module lib/api/client.test
 */

import { http, HttpResponse } from "msw";
import { describe, it, expect, beforeEach } from "vitest";

import { server } from "@/test/mocks/server";

import { apiClient, ApiError, normalizeError, createApiClient } from "./client";

const API_BASE = "http://localhost:8000";

describe("apiClient", () => {
  describe("configuration", () => {
    it("uses the correct base URL", async () => {
      server.use(
        http.get(`${API_BASE}/api/v1/test`, () => {
          return HttpResponse.json({ success: true });
        }),
      );

      const response = await apiClient.get("api/v1/test").json();
      expect(response).toEqual({ success: true });
    });

    it("sends requests with JSON content type", async () => {
      let receivedContentType: string | null = null;

      server.use(
        http.post(`${API_BASE}/api/v1/test`, ({ request }) => {
          receivedContentType = request.headers.get("content-type");
          return HttpResponse.json({ received: true });
        }),
      );

      await apiClient.post("api/v1/test", { json: { data: "test" } }).json();
      expect(receivedContentType).toContain("application/json");
    });
  });

  describe("error handling", () => {
    it("throws on 4xx errors", async () => {
      server.use(
        http.get(`${API_BASE}/api/v1/not-found`, () => {
          return HttpResponse.json(
            { code: "NOT_FOUND", message: "Resource not found" },
            { status: 404 },
          );
        }),
      );

      await expect(apiClient.get("api/v1/not-found").json()).rejects.toThrow();
    });

    it("throws on 5xx errors", async () => {
      server.use(
        http.get(`${API_BASE}/api/v1/error`, () => {
          return HttpResponse.json(
            { code: "INTERNAL_ERROR", message: "Server error" },
            { status: 500 },
          );
        }),
      );

      await expect(apiClient.get("api/v1/error").json()).rejects.toThrow();
    });
  });
});

describe("createApiClient", () => {
  it("creates a new client with default options", () => {
    const client = createApiClient();
    expect(client).toBeDefined();
  });

  it("creates a client with custom timeout", async () => {
    const client = createApiClient({ timeout: 5000 });
    expect(client).toBeDefined();
  });
});

describe("ApiError", () => {
  describe("constructor", () => {
    it("creates error with all properties", () => {
      const error = new ApiError("Test error", 404, "NOT_FOUND", [], null);

      expect(error.message).toBe("Test error");
      expect(error.status).toBe(404);
      expect(error.code).toBe("NOT_FOUND");
      expect(error.details).toEqual([]);
      expect(error.rawResponse).toBeNull();
      expect(error.name).toBe("ApiError");
    });

    it("stores field validation errors", () => {
      const details = [
        { loc: ["body", "name"], msg: "required", type: "missing" },
      ];
      const error = new ApiError(
        "Validation failed",
        422,
        "VALIDATION",
        details,
        null,
      );

      expect(error.details).toEqual(details);
    });

    it("stores raw response for debugging", () => {
      const rawResponse = { error: "detailed info" };
      const error = new ApiError("Error", 500, "SERVER", [], rawResponse);

      expect(error.rawResponse).toEqual(rawResponse);
    });
  });

  describe("isClientError", () => {
    it("returns true for 4xx status codes", () => {
      expect(new ApiError("", 400, "", [], null).isClientError()).toBe(true);
      expect(new ApiError("", 404, "", [], null).isClientError()).toBe(true);
      expect(new ApiError("", 422, "", [], null).isClientError()).toBe(true);
      expect(new ApiError("", 499, "", [], null).isClientError()).toBe(true);
    });

    it("returns false for non-4xx status codes", () => {
      expect(new ApiError("", 200, "", [], null).isClientError()).toBe(false);
      expect(new ApiError("", 500, "", [], null).isClientError()).toBe(false);
      expect(new ApiError("", 0, "", [], null).isClientError()).toBe(false);
    });
  });

  describe("isServerError", () => {
    it("returns true for 5xx status codes", () => {
      expect(new ApiError("", 500, "", [], null).isServerError()).toBe(true);
      expect(new ApiError("", 502, "", [], null).isServerError()).toBe(true);
      expect(new ApiError("", 503, "", [], null).isServerError()).toBe(true);
      expect(new ApiError("", 599, "", [], null).isServerError()).toBe(true);
    });

    it("returns false for non-5xx status codes", () => {
      expect(new ApiError("", 200, "", [], null).isServerError()).toBe(false);
      expect(new ApiError("", 404, "", [], null).isServerError()).toBe(false);
      expect(new ApiError("", 0, "", [], null).isServerError()).toBe(false);
    });
  });

  describe("isNetworkError", () => {
    it("returns true for status 0", () => {
      expect(new ApiError("", 0, "", [], null).isNetworkError()).toBe(true);
    });

    it("returns false for non-zero status codes", () => {
      expect(new ApiError("", 200, "", [], null).isNetworkError()).toBe(false);
      expect(new ApiError("", 404, "", [], null).isNetworkError()).toBe(false);
      expect(new ApiError("", 500, "", [], null).isNetworkError()).toBe(false);
    });
  });
});

describe("normalizeError", () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  it("returns ApiError unchanged", async () => {
    const original = new ApiError("Test", 404, "NOT_FOUND", [], null);
    const normalized = await normalizeError(original);

    expect(normalized).toBe(original);
  });

  it("converts HTTPError to ApiError with parsed response", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/error`, () => {
        return HttpResponse.json(
          { code: "TEST_ERROR", message: "Test error message" },
          { status: 400 },
        );
      }),
    );

    try {
      await apiClient.get("api/v1/error").json();
    } catch (error) {
      const normalized = await normalizeError(error);

      expect(normalized).toBeInstanceOf(ApiError);
      expect(normalized.status).toBe(400);
      expect(normalized.code).toBe("TEST_ERROR");
      expect(normalized.message).toBe("Test error message");
    }
  });

  it("handles HTTPError with non-JSON response", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/text-error`, () => {
        return new HttpResponse("Not JSON", { status: 500 });
      }),
    );

    try {
      await apiClient.get("api/v1/text-error").json();
    } catch (error) {
      const normalized = await normalizeError(error);

      expect(normalized).toBeInstanceOf(ApiError);
      expect(normalized.status).toBe(500);
      expect(normalized.code).toBe("HTTP_500");
    }
  });

  it("converts generic Error to network ApiError", async () => {
    const error = new Error("Connection refused");
    const normalized = await normalizeError(error);

    expect(normalized).toBeInstanceOf(ApiError);
    expect(normalized.status).toBe(0);
    expect(normalized.code).toBe("NETWORK_ERROR");
    expect(normalized.message).toBe("Connection refused");
  });

  it("converts unknown errors to ApiError", async () => {
    const normalized = await normalizeError("string error");

    expect(normalized).toBeInstanceOf(ApiError);
    expect(normalized.status).toBe(0);
    expect(normalized.code).toBe("UNKNOWN_ERROR");
  });
});
