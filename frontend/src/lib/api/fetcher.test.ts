/**
 * Tests for Zod-validated fetcher utilities.
 *
 * @module lib/api/fetcher.test
 */

import { http, HttpResponse } from "msw";
import { describe, it, expect } from "vitest";
import { z } from "zod";

import { server } from "@/test/mocks/server";

import {
  SchemaValidationError,
  isSchemaValidationError,
  fetchWithSchema,
  createTypedFetcher,
} from "./fetcher";

const API_BASE = "http://localhost:8000";

describe("SchemaValidationError", () => {
  describe("constructor", () => {
    it("creates error with all properties", () => {
      const fieldErrors = [
        { path: ["data", "name"], message: "Required", code: "invalid_type" },
      ];
      const rawResponse = { data: { name: null } };

      const error = new SchemaValidationError(
        "Validation failed",
        fieldErrors,
        rawResponse,
      );

      expect(error.message).toBe("Validation failed");
      expect(error.name).toBe("SchemaValidationError");
      expect(error.code).toBe("SCHEMA_VALIDATION_ERROR");
      expect(error.status).toBe(0);
      expect(error.fieldErrors).toEqual(fieldErrors);
      expect(error.rawResponse).toEqual(rawResponse);
    });
  });

  describe("fromZodError", () => {
    it("creates error from ZodError with single field", () => {
      const schema = z.object({ name: z.string() });
      const result = schema.safeParse({ name: 123 });

      if (!result.success) {
        const error = SchemaValidationError.fromZodError(result.error, {
          name: 123,
        });

        expect(error.fieldErrors).toHaveLength(1);
        const firstError = error.fieldErrors[0];
        expect(firstError).toBeDefined();
        expect(firstError?.path).toEqual(["name"]);
        expect(error.message).toContain("Schema validation failed");
      }
    });

    it("creates error from ZodError with multiple fields", () => {
      const schema = z.object({
        name: z.string(),
        age: z.number(),
      });
      const result = schema.safeParse({ name: 123, age: "invalid" });

      if (!result.success) {
        const error = SchemaValidationError.fromZodError(result.error, {
          name: 123,
          age: "invalid",
        });

        expect(error.fieldErrors.length).toBeGreaterThan(1);
        expect(error.message).toContain("errors");
      }
    });

    it("preserves original response for debugging", () => {
      const schema = z.object({ id: z.number() });
      const rawResponse = { id: "not-a-number" };
      const result = schema.safeParse(rawResponse);

      if (!result.success) {
        const error = SchemaValidationError.fromZodError(
          result.error,
          rawResponse,
        );

        expect(error.rawResponse).toEqual(rawResponse);
      }
    });
  });
});

describe("isSchemaValidationError", () => {
  it("returns true for SchemaValidationError", () => {
    const error = new SchemaValidationError("Test", [], null);
    expect(isSchemaValidationError(error)).toBe(true);
  });

  it("returns false for regular Error", () => {
    const error = new Error("Test");
    expect(isSchemaValidationError(error)).toBe(false);
  });

  it("returns false for non-error objects", () => {
    expect(isSchemaValidationError({ message: "Test" })).toBe(false);
    expect(isSchemaValidationError(null)).toBe(false);
    expect(isSchemaValidationError(undefined)).toBe(false);
  });
});

describe("fetchWithSchema", () => {
  const TestSchema = z.object({
    id: z.number(),
    name: z.string(),
  });

  it("returns validated data for valid response", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/test-valid`, () => {
        return HttpResponse.json({ id: 1, name: "Test" });
      }),
    );

    const data = await fetchWithSchema("api/v1/test-valid", TestSchema);

    expect(data).toEqual({ id: 1, name: "Test" });
  });

  it("throws SchemaValidationError for invalid response", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/test-invalid`, () => {
        return HttpResponse.json({ id: "not-a-number", name: "Test" });
      }),
    );

    await expect(
      fetchWithSchema("api/v1/test-invalid", TestSchema),
    ).rejects.toThrow(SchemaValidationError);
  });

  it("includes field errors in SchemaValidationError", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/test-invalid-fields`, () => {
        return HttpResponse.json({ id: "invalid", name: 123 });
      }),
    );

    try {
      await fetchWithSchema("api/v1/test-invalid-fields", TestSchema);
    } catch (error) {
      expect(isSchemaValidationError(error)).toBe(true);
      if (isSchemaValidationError(error)) {
        expect(error.fieldErrors.length).toBeGreaterThan(0);
      }
    }
  });

  it("throws ApiError for network/HTTP errors", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/test-http-error`, () => {
        return HttpResponse.json(
          { code: "ERROR", message: "Server error" },
          { status: 500 },
        );
      }),
    );

    await expect(
      fetchWithSchema("api/v1/test-http-error", TestSchema),
    ).rejects.toThrow();
  });
});

describe("createTypedFetcher", () => {
  const TestSchema = z.object({
    items: z.array(z.string()),
  });

  it("creates a function that fetches and validates", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/items`, () => {
        return HttpResponse.json({ items: ["a", "b", "c"] });
      }),
    );

    const fetcher = createTypedFetcher("api/v1/items", TestSchema);
    const data = await fetcher();

    expect(data).toEqual({ items: ["a", "b", "c"] });
  });

  it("created function throws on invalid data", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/invalid-items`, () => {
        return HttpResponse.json({ items: [1, 2, 3] }); // numbers instead of strings
      }),
    );

    const fetcher = createTypedFetcher("api/v1/invalid-items", TestSchema);

    await expect(fetcher()).rejects.toThrow(SchemaValidationError);
  });
});
