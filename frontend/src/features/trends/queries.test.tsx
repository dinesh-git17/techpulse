/**
 * Tests for trends and technologies query hooks.
 *
 * @module features/trends/queries.test
 */

import { type ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, it, expect, beforeEach } from "vitest";

import { mockTechnologies, mockTrends } from "@/test/mocks/handlers";
import { server } from "@/test/mocks/server";

import { technologyKeys, trendKeys } from "./keys";
import {
  useTechnologies,
  useTrends,
  prefetchTechnologies,
  prefetchTrends,
} from "./queries";

const API_BASE = "http://localhost:8000";

/**
 * Create a wrapper with a fresh QueryClient for each test.
 */
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe("useTechnologies", () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  it("fetches technologies successfully", async () => {
    const { result } = renderHook(() => useTechnologies(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockTechnologies);
    expect(result.current.data?.data).toHaveLength(3);
  });

  it("handles loading state", () => {
    const { result } = renderHook(() => useTechnologies(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);
  });

  it("handles error state", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/technologies`, () => {
        // Use 400 error to avoid ky's default retry for 5xx
        return HttpResponse.json(
          { code: "BAD_REQUEST", message: "Bad request" },
          { status: 400 },
        );
      }),
    );

    const { result } = renderHook(() => useTechnologies(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });

  it("respects enabled option", () => {
    const { result } = renderHook(() => useTechnologies({ enabled: false }), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(result.current.data).toBeUndefined();
  });

  it("validates response against schema", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/technologies`, () => {
        return HttpResponse.json({
          data: [{ key: "test" }], // Missing required fields
          meta: {
            request_id: "test",
            timestamp: "2024-01-01T00:00:00Z",
            total_count: 1,
            page: null,
            page_size: null,
            has_more: null,
          },
        });
      }),
    );

    const { result } = renderHook(() => useTechnologies(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe("useTrends", () => {
  const defaultFilters = { techIds: "python,react" };

  beforeEach(() => {
    server.resetHandlers();
  });

  it("fetches trends successfully", async () => {
    const { result } = renderHook(
      () => useTrends({ filters: defaultFilters }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockTrends);
    expect(result.current.data?.data).toHaveLength(2);
  });

  it("includes tech_ids in request", async () => {
    let requestedUrl: string | null = null;

    server.use(
      http.get(`${API_BASE}/api/v1/trends`, ({ request }) => {
        requestedUrl = request.url;
        return HttpResponse.json(mockTrends);
      }),
    );

    const { result } = renderHook(
      () => useTrends({ filters: { techIds: "python" } }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(requestedUrl).toContain("tech_ids=python");
  });

  it("includes optional date filters", async () => {
    let requestedUrl: string | null = null;

    server.use(
      http.get(`${API_BASE}/api/v1/trends`, ({ request }) => {
        requestedUrl = request.url;
        return HttpResponse.json(mockTrends);
      }),
    );

    const { result } = renderHook(
      () =>
        useTrends({
          filters: {
            techIds: "python",
            startDate: "2024-01-01",
            endDate: "2024-12-31",
          },
        }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(requestedUrl).toContain("start_date=2024-01-01");
    expect(requestedUrl).toContain("end_date=2024-12-31");
  });

  it("respects enabled option", () => {
    const { result } = renderHook(
      () => useTrends({ filters: defaultFilters, enabled: false }),
      { wrapper: createWrapper() },
    );

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
  });

  it("handles error response", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/trends`, () => {
        return HttpResponse.json(
          { code: "VALIDATION_ERROR", message: "Invalid tech_ids" },
          { status: 400 },
        );
      }),
    );

    const { result } = renderHook(
      () => useTrends({ filters: defaultFilters }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe("prefetchTechnologies", () => {
  it("prefetches technologies into QueryClient cache", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    await prefetchTechnologies(queryClient);

    const cachedData = queryClient.getQueryData(technologyKeys.list());
    expect(cachedData).toEqual(mockTechnologies);
  });

  it("handles prefetch errors gracefully", async () => {
    server.use(
      http.get(`${API_BASE}/api/v1/technologies`, () => {
        return HttpResponse.json(
          { code: "ERROR", message: "Server error" },
          { status: 500 },
        );
      }),
    );

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    // prefetchQuery doesn't throw, it stores the error in the cache
    await prefetchTechnologies(queryClient);

    const cachedData = queryClient.getQueryData(technologyKeys.list());
    expect(cachedData).toBeUndefined();
  });
});

describe("prefetchTrends", () => {
  const filters = { techIds: "python,react" };

  it("prefetches trends into QueryClient cache", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    await prefetchTrends(queryClient, filters);

    const cachedData = queryClient.getQueryData(trendKeys.list(filters));
    expect(cachedData).toEqual(mockTrends);
  });

  it("uses correct query key for filters", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    const specificFilters = {
      techIds: "typescript",
      startDate: "2024-01-01",
    };

    await prefetchTrends(queryClient, specificFilters);

    // Data should be cached under the specific filter key
    const cachedData = queryClient.getQueryData(
      trendKeys.list(specificFilters),
    );
    expect(cachedData).toBeDefined();

    // Different filters should not have cached data
    const differentFilters = { techIds: "different" };
    const notCached = queryClient.getQueryData(
      trendKeys.list(differentFilters),
    );
    expect(notCached).toBeUndefined();
  });
});
