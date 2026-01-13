/**
 * Tests for QueryClient factory configuration.
 *
 * @module lib/api/query-client.test
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";

import { makeQueryClient, getQueryClient } from "./query-client";

describe("makeQueryClient", () => {
  describe("default configuration", () => {
    it("creates a QueryClient instance", () => {
      const client = makeQueryClient();
      expect(client).toBeDefined();
      expect(client.getDefaultOptions()).toBeDefined();
    });

    it("sets staleTime to 5 minutes", () => {
      const client = makeQueryClient();
      const options = client.getDefaultOptions();

      expect(options.queries?.staleTime).toBe(5 * 60 * 1000);
    });

    it("sets gcTime to 10 minutes", () => {
      const client = makeQueryClient();
      const options = client.getDefaultOptions();

      expect(options.queries?.gcTime).toBe(10 * 60 * 1000);
    });

    it("disables refetchOnWindowFocus", () => {
      const client = makeQueryClient();
      const options = client.getDefaultOptions();

      expect(options.queries?.refetchOnWindowFocus).toBe(false);
    });

    it("disables retry for mutations", () => {
      const client = makeQueryClient();
      const options = client.getDefaultOptions();

      expect(options.mutations?.retry).toBe(false);
    });
  });

  describe("retry configuration", () => {
    it("configures retry as a function for queries", () => {
      const client = makeQueryClient();
      const options = client.getDefaultOptions();

      expect(typeof options.queries?.retry).toBe("function");
    });

    it("retry function returns false after 3 failures", () => {
      const client = makeQueryClient();
      const retry = client.getDefaultOptions().queries?.retry;

      if (typeof retry === "function") {
        expect(retry(3, new Error("test"))).toBe(false);
        expect(retry(4, new Error("test"))).toBe(false);
      }
    });

    it("retry function returns false for 4xx errors", () => {
      const client = makeQueryClient();
      const retry = client.getDefaultOptions().queries?.retry;

      if (typeof retry === "function") {
        // Create error-like objects with status property
        const error400 = Object.assign(new Error("Bad Request"), {
          status: 400,
        });
        const error404 = Object.assign(new Error("Not Found"), { status: 404 });
        const error422 = Object.assign(new Error("Unprocessable"), {
          status: 422,
        });

        expect(retry(0, error400)).toBe(false);
        expect(retry(0, error404)).toBe(false);
        expect(retry(0, error422)).toBe(false);
      }
    });

    it("retry function returns true for 5xx errors within limit", () => {
      const client = makeQueryClient();
      const retry = client.getDefaultOptions().queries?.retry;

      if (typeof retry === "function") {
        // Create error-like objects with status property
        const error500 = Object.assign(new Error("Server Error"), {
          status: 500,
        });
        const error502 = Object.assign(new Error("Bad Gateway"), {
          status: 502,
        });

        expect(retry(0, error500)).toBe(true);
        expect(retry(1, error502)).toBe(true);
        expect(retry(2, error500)).toBe(true);
      }
    });

    it("retry function returns true for network errors within limit", () => {
      const client = makeQueryClient();
      const retry = client.getDefaultOptions().queries?.retry;

      if (typeof retry === "function") {
        const networkError = new Error("Network error");

        expect(retry(0, networkError)).toBe(true);
        expect(retry(1, networkError)).toBe(true);
        expect(retry(2, networkError)).toBe(true);
      }
    });
  });

  describe("retryDelay configuration", () => {
    it("configures retryDelay as a function", () => {
      const client = makeQueryClient();
      const options = client.getDefaultOptions();

      expect(typeof options.queries?.retryDelay).toBe("function");
    });

    it("increases delay exponentially", () => {
      const client = makeQueryClient();
      const retryDelay = client.getDefaultOptions().queries?.retryDelay;

      if (typeof retryDelay === "function") {
        const delay0 = retryDelay(0, new Error());
        const delay1 = retryDelay(1, new Error());
        const delay2 = retryDelay(2, new Error());

        // Base delay is 1000ms, so delays should increase exponentially
        // With jitter, we check approximate ranges
        expect(delay0).toBeGreaterThanOrEqual(1000);
        expect(delay0).toBeLessThanOrEqual(1100); // 1000 + 10% jitter

        expect(delay1).toBeGreaterThanOrEqual(2000);
        expect(delay1).toBeLessThanOrEqual(2200);

        expect(delay2).toBeGreaterThanOrEqual(4000);
        expect(delay2).toBeLessThanOrEqual(4400);
      }
    });

    it("caps delay at 30 seconds", () => {
      const client = makeQueryClient();
      const retryDelay = client.getDefaultOptions().queries?.retryDelay;

      if (typeof retryDelay === "function") {
        // At attempt 10, exponential would be 2^10 * 1000 = 1,024,000ms
        // But it should be capped at 30,000ms
        const delay = retryDelay(10, new Error());
        expect(delay).toBeLessThanOrEqual(33000); // 30000 + 10% jitter
      }
    });
  });

  describe("custom configuration", () => {
    it("allows overriding staleTime", () => {
      const client = makeQueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000,
          },
        },
      });
      const options = client.getDefaultOptions();

      expect(options.queries?.staleTime).toBe(1000);
    });

    it("preserves other defaults when overriding", () => {
      const client = makeQueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000,
          },
        },
      });
      const options = client.getDefaultOptions();

      // gcTime should still be default
      expect(options.queries?.gcTime).toBe(10 * 60 * 1000);
    });
  });
});

describe("getQueryClient", () => {
  const originalWindow = global.window;

  afterEach(() => {
    // Restore window
    global.window = originalWindow;
  });

  describe("server environment", () => {
    beforeEach(() => {
      // Simulate server environment
      // @ts-expect-error - intentionally setting window to undefined for test
      global.window = undefined;
    });

    it("creates new client on each call", () => {
      const client1 = getQueryClient();
      const client2 = getQueryClient();

      expect(client1).not.toBe(client2);
    });
  });

  describe("browser environment", () => {
    beforeEach(() => {
      // Simulate browser environment
      global.window = {} as Window & typeof globalThis;
    });

    it("returns the same client on multiple calls", () => {
      // Need to reset module state for this test
      // Since we can't easily reset the module, we verify the singleton pattern
      const client1 = getQueryClient();
      const client2 = getQueryClient();

      expect(client1).toBe(client2);
    });
  });
});
