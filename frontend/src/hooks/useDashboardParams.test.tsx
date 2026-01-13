/**
 * Tests for the useDashboardParams hook.
 *
 * @module hooks/useDashboardParams.test
 */

import { type ReactNode } from "react";

import { renderHook, act } from "@testing-library/react";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { describe, it, expect } from "vitest";

import { getDefaultEndDate, getDefaultStartDate } from "@/lib/url";

import { useDashboardParams } from "./useDashboardParams";

/**
 * Create a wrapper with NuqsTestingAdapter for hook testing.
 *
 * @param initialParams - Initial URL search parameters.
 */
function createWrapper(initialParams?: Record<string, string>) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <NuqsTestingAdapter searchParams={initialParams}>
        {children}
      </NuqsTestingAdapter>
    );
  };
}

describe("useDashboardParams", () => {
  describe("initial state", () => {
    it("returns empty selectedTechs by default", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper(),
      });

      expect(result.current.selectedTechs).toEqual([]);
    });

    it("returns default date range when no params provided", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper(),
      });

      expect(result.current.dateRange.startDate).toBe(getDefaultStartDate());
      expect(result.current.dateRange.endDate).toBe(getDefaultEndDate());
    });

    it("parses tech_ids from URL", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper({ tech_ids: "python,react,vue" }),
      });

      expect(result.current.selectedTechs).toEqual(["python", "react", "vue"]);
    });

    it("parses date range from URL", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper({
          start: "2024-01-01",
          end: "2024-12-31",
        }),
      });

      expect(result.current.dateRange.startDate).toBe("2024-01-01");
      expect(result.current.dateRange.endDate).toBe("2024-12-31");
    });

    it("indicates ready state", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isReady).toBe(true);
    });
  });

  describe("setTechs", () => {
    it("provides a setter function", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper(),
      });

      expect(typeof result.current.setTechs).toBe("function");
    });

    it("setter can be called with array", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper(),
      });

      expect(() => {
        act(() => {
          result.current.setTechs(["python", "react"]);
        });
      }).not.toThrow();
    });

    it("setter does not mutate input array", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper(),
      });

      const input = ["vue", "react", "python"];
      const originalInput = [...input];

      act(() => {
        result.current.setTechs(input);
      });

      expect(input).toEqual(originalInput);
    });
  });

  describe("setDateRange", () => {
    it("provides a setter function", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper(),
      });

      expect(typeof result.current.setDateRange).toBe("function");
    });

    it("setter can be called with partial range", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper(),
      });

      expect(() => {
        act(() => {
          result.current.setDateRange({ startDate: "2024-01-01" });
        });
      }).not.toThrow();

      expect(() => {
        act(() => {
          result.current.setDateRange({ endDate: "2024-12-31" });
        });
      }).not.toThrow();
    });

    it("setter can be called with full range", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper(),
      });

      expect(() => {
        act(() => {
          result.current.setDateRange({
            startDate: "2024-01-01",
            endDate: "2024-12-31",
          });
        });
      }).not.toThrow();
    });
  });

  describe("array canonicalization", () => {
    it("returns sorted array from unsorted URL params", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper({ tech_ids: "vue,react,python" }),
      });

      expect(result.current.selectedTechs).toEqual(["python", "react", "vue"]);
    });

    it("returns sorted array from already sorted URL params", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper({ tech_ids: "alpha,beta,gamma" }),
      });

      expect(result.current.selectedTechs).toEqual(["alpha", "beta", "gamma"]);
    });

    it("handles single tech id", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper({ tech_ids: "python" }),
      });

      expect(result.current.selectedTechs).toEqual(["python"]);
    });
  });

  describe("type safety", () => {
    it("returns readonly array for selectedTechs", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper({ tech_ids: "python,react" }),
      });

      const techs: readonly string[] = result.current.selectedTechs;
      expect(techs).toBeDefined();
    });

    it("returns readonly DateRange object", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper(),
      });

      const range: {
        readonly startDate: string;
        readonly endDate: string;
      } = result.current.dateRange;
      expect(range).toBeDefined();
    });
  });

  describe("options", () => {
    it("accepts custom throttle value", () => {
      const { result } = renderHook(
        () => useDashboardParams({ throttleMs: 100 }),
        { wrapper: createWrapper() },
      );

      expect(result.current.isReady).toBe(true);
    });

    it("uses default throttle when not specified", () => {
      const { result } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isReady).toBe(true);
    });
  });

  describe("hook stability", () => {
    it("setTechs function is stable across renders", () => {
      const { result, rerender } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper(),
      });

      const firstSetTechs = result.current.setTechs;
      rerender();
      const secondSetTechs = result.current.setTechs;

      expect(firstSetTechs).toBe(secondSetTechs);
    });

    it("setDateRange function is stable across renders", () => {
      const { result, rerender } = renderHook(() => useDashboardParams(), {
        wrapper: createWrapper(),
      });

      const firstSetDateRange = result.current.setDateRange;
      rerender();
      const secondSetDateRange = result.current.setDateRange;

      expect(firstSetDateRange).toBe(secondSetDateRange);
    });
  });
});
