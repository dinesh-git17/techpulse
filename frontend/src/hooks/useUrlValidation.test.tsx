/**
 * Tests for the useUrlValidation hook.
 *
 * Covers all guardrail scenarios defined in the URL State & Deep Linking epic:
 * - Invalid date formats
 * - Impossible date ranges
 * - Excess tech_ids
 * - Unknown tech_ids
 *
 * @module hooks/useUrlValidation.test
 */

import { type ReactNode } from "react";

import { renderHook, act } from "@testing-library/react";
import { toast } from "sonner";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { MAX_TECH_IDS, type RawDashboardParams } from "@/lib/url";

import { useUrlValidation } from "./useUrlValidation";

vi.mock("sonner", () => ({
  toast: {
    warning: vi.fn(),
  },
}));

const mockToastWarning = vi.mocked(toast.warning);

/**
 * Simple wrapper for hook testing.
 */
function Wrapper({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

/**
 * Extract first call argument from mock with type safety.
 */
function getFirstCallArg(
  mockFn: ReturnType<typeof vi.fn>,
): RawDashboardParams | undefined {
  const calls = mockFn.mock.calls;
  if (calls.length === 0) {
    return undefined;
  }
  const firstCall = calls[0];
  if (!firstCall || firstCall.length === 0) {
    return undefined;
  }
  return firstCall[0] as RawDashboardParams;
}

describe("useUrlValidation", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2025-06-15T12:00:00Z"));
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  /**
   * Helper to flush pending effects with fake timers.
   */
  async function flushEffects(): Promise<void> {
    await act(async () => {
      vi.runAllTimers();
    });
  }

  describe("when disabled", () => {
    it("does not run validation", () => {
      const onCorrect = vi.fn();
      const knownTechIds = new Set(["python", "react"]);

      renderHook(
        () =>
          useUrlValidation({
            rawParams: {
              tech_ids: "invalid_tech",
              start: "2024-01-01",
              end: "2024-12-31",
            },
            knownTechIds,
            onCorrect,
            enabled: false,
          }),
        { wrapper: Wrapper },
      );

      expect(onCorrect).not.toHaveBeenCalled();
      expect(mockToastWarning).not.toHaveBeenCalled();
    });
  });

  describe("when params are valid", () => {
    it("does not call onCorrect", () => {
      const onCorrect = vi.fn();
      const knownTechIds = new Set(["python", "react"]);

      renderHook(
        () =>
          useUrlValidation({
            rawParams: {
              tech_ids: "python,react",
              start: "2024-01-01",
              end: "2024-12-31",
            },
            knownTechIds,
            onCorrect,
            enabled: true,
          }),
        { wrapper: Wrapper },
      );

      expect(onCorrect).not.toHaveBeenCalled();
      expect(mockToastWarning).not.toHaveBeenCalled();
    });
  });

  describe("invalid date format guardrail", () => {
    it("corrects invalid start date and shows toast", async () => {
      const onCorrect = vi.fn();
      const knownTechIds = new Set(["python"]);

      renderHook(
        () =>
          useUrlValidation({
            rawParams: {
              tech_ids: "python",
              start: "invalid",
              end: "2024-12-31",
            },
            knownTechIds,
            onCorrect,
            enabled: true,
          }),
        { wrapper: Wrapper },
      );

      await flushEffects();

      expect(onCorrect).toHaveBeenCalledTimes(1);
      const correctedParams = getFirstCallArg(onCorrect);
      expect(correctedParams?.start).toBe("2024-06-15");

      expect(mockToastWarning).toHaveBeenCalledWith(
        "Invalid date format",
        expect.objectContaining({
          description: "Invalid date format. Showing last 12 months.",
        }),
      );
    });

    it("corrects invalid end date and shows toast", async () => {
      const onCorrect = vi.fn();
      const knownTechIds = new Set(["python"]);

      renderHook(
        () =>
          useUrlValidation({
            rawParams: {
              tech_ids: "python",
              start: "2024-01-01",
              end: "hello",
            },
            knownTechIds,
            onCorrect,
            enabled: true,
          }),
        { wrapper: Wrapper },
      );

      await flushEffects();

      expect(onCorrect).toHaveBeenCalledTimes(1);
      const correctedParams = getFirstCallArg(onCorrect);
      expect(correctedParams?.end).toBe("2025-06-15");

      expect(mockToastWarning).toHaveBeenCalledWith(
        "Invalid date format",
        expect.objectContaining({
          description: "Invalid date format. Showing last 12 months.",
        }),
      );
    });

    it("corrects garbage date values", async () => {
      const onCorrect = vi.fn();
      const knownTechIds = new Set(["python"]);

      renderHook(
        () =>
          useUrlValidation({
            rawParams: {
              tech_ids: "python",
              start: "2024-13-45",
              end: "2024-12-31",
            },
            knownTechIds,
            onCorrect,
            enabled: true,
          }),
        { wrapper: Wrapper },
      );

      await flushEffects();

      expect(onCorrect).toHaveBeenCalled();
      expect(mockToastWarning).toHaveBeenCalled();
    });
  });

  describe("impossible date range guardrail", () => {
    it("corrects when start >= end and shows toast", async () => {
      const onCorrect = vi.fn();
      const knownTechIds = new Set(["python"]);

      renderHook(
        () =>
          useUrlValidation({
            rawParams: {
              tech_ids: "python",
              start: "2025-06-01",
              end: "2025-05-01",
            },
            knownTechIds,
            onCorrect,
            enabled: true,
          }),
        { wrapper: Wrapper },
      );

      await flushEffects();

      expect(onCorrect).toHaveBeenCalledTimes(1);
      const correctedParams = getFirstCallArg(onCorrect);
      expect(correctedParams?.start).toBe("2025-06-01");
      expect(correctedParams?.end).toBe("2025-07-01");

      expect(mockToastWarning).toHaveBeenCalledWith(
        "Date range adjusted",
        expect.objectContaining({
          description: "End date adjusted to be after start date.",
        }),
      );
    });

    it("corrects when start equals end", async () => {
      const onCorrect = vi.fn();
      const knownTechIds = new Set(["python"]);

      renderHook(
        () =>
          useUrlValidation({
            rawParams: {
              tech_ids: "python",
              start: "2025-06-01",
              end: "2025-06-01",
            },
            knownTechIds,
            onCorrect,
            enabled: true,
          }),
        { wrapper: Wrapper },
      );

      await flushEffects();

      expect(onCorrect).toHaveBeenCalled();
      const correctedParams = getFirstCallArg(onCorrect);
      expect(correctedParams?.end).toBe("2025-07-01");

      expect(mockToastWarning).toHaveBeenCalledWith(
        "Date range adjusted",
        expect.objectContaining({
          description: "End date adjusted to be after start date.",
        }),
      );
    });
  });

  describe("excess tech_ids guardrail", () => {
    it("truncates to MAX_TECH_IDS and shows toast", async () => {
      const onCorrect = vi.fn();
      const manyTechIds = Array.from({ length: 15 }, (_, i) => `tech${i}`);
      const knownTechIds = new Set(manyTechIds);

      renderHook(
        () =>
          useUrlValidation({
            rawParams: {
              tech_ids: manyTechIds.join(","),
              start: "2024-01-01",
              end: "2024-12-31",
            },
            knownTechIds,
            onCorrect,
            enabled: true,
          }),
        { wrapper: Wrapper },
      );

      await flushEffects();

      expect(onCorrect).toHaveBeenCalledTimes(1);
      const correctedParams = getFirstCallArg(onCorrect);
      const correctedTechIds = correctedParams?.tech_ids?.split(",") ?? [];
      expect(correctedTechIds.length).toBe(MAX_TECH_IDS);

      expect(mockToastWarning).toHaveBeenCalledWith(
        "Selection trimmed",
        expect.objectContaining({
          description: `Selection limited to ${MAX_TECH_IDS} technologies.`,
        }),
      );
    });

    it("does not truncate at exactly MAX_TECH_IDS", async () => {
      const onCorrect = vi.fn();
      const exactTechIds = Array.from(
        { length: MAX_TECH_IDS },
        (_, i) => `tech${i}`,
      );
      const knownTechIds = new Set(exactTechIds);

      renderHook(
        () =>
          useUrlValidation({
            rawParams: {
              tech_ids: exactTechIds.join(","),
              start: "2024-01-01",
              end: "2024-12-31",
            },
            knownTechIds,
            onCorrect,
            enabled: true,
          }),
        { wrapper: Wrapper },
      );

      await flushEffects();

      expect(onCorrect).not.toHaveBeenCalled();
    });
  });

  describe("unknown tech_ids guardrail", () => {
    it("filters unknown IDs and shows toast", async () => {
      const onCorrect = vi.fn();
      const knownTechIds = new Set(["python", "react"]);

      renderHook(
        () =>
          useUrlValidation({
            rawParams: {
              tech_ids: "python,unknown_tech,react,invalid_id",
              start: "2024-01-01",
              end: "2024-12-31",
            },
            knownTechIds,
            onCorrect,
            enabled: true,
          }),
        { wrapper: Wrapper },
      );

      await flushEffects();

      expect(onCorrect).toHaveBeenCalledTimes(1);
      const correctedParams = getFirstCallArg(onCorrect);
      expect(correctedParams?.tech_ids).toBe("python,react");

      expect(mockToastWarning).toHaveBeenCalledWith(
        "Unknown technologies removed",
        expect.objectContaining({
          description: "Some technologies were not recognized.",
        }),
      );
    });

    it("removes all tech_ids when none are known", async () => {
      const onCorrect = vi.fn();
      const knownTechIds = new Set(["python", "react"]);

      renderHook(
        () =>
          useUrlValidation({
            rawParams: {
              tech_ids: "unknown1,unknown2",
              start: "2024-01-01",
              end: "2024-12-31",
            },
            knownTechIds,
            onCorrect,
            enabled: true,
          }),
        { wrapper: Wrapper },
      );

      await flushEffects();

      expect(onCorrect).toHaveBeenCalled();
      const correctedParams = getFirstCallArg(onCorrect);
      expect(correctedParams?.tech_ids).toBe("");
    });
  });

  describe("multiple corrections", () => {
    it("shows toast for each correction type", async () => {
      const onCorrect = vi.fn();
      const manyTechIds = Array.from({ length: 15 }, (_, i) => `tech${i}`);
      const knownTechIds = new Set(manyTechIds.slice(0, 5));

      renderHook(
        () =>
          useUrlValidation({
            rawParams: {
              tech_ids: manyTechIds.join(","),
              start: "invalid",
              end: "2024-12-31",
            },
            knownTechIds,
            onCorrect,
            enabled: true,
          }),
        { wrapper: Wrapper },
      );

      await flushEffects();

      expect(onCorrect).toHaveBeenCalled();
      expect(mockToastWarning.mock.calls.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe("re-validation behavior", () => {
    it("does not re-validate when params unchanged", async () => {
      const onCorrect = vi.fn();
      const knownTechIds = new Set(["python"]);

      const { rerender } = renderHook(
        () =>
          useUrlValidation({
            rawParams: {
              tech_ids: "python",
              start: "2024-01-01",
              end: "2024-12-31",
            },
            knownTechIds,
            onCorrect,
            enabled: true,
          }),
        { wrapper: Wrapper },
      );

      await flushEffects();
      rerender();
      await flushEffects();
      rerender();
      await flushEffects();

      expect(onCorrect).not.toHaveBeenCalled();
    });

    it("re-validates when params change", async () => {
      const onCorrect = vi.fn();
      const knownTechIds = new Set(["python", "react"]);

      const { rerender } = renderHook(
        ({ rawParams }) =>
          useUrlValidation({
            rawParams,
            knownTechIds,
            onCorrect,
            enabled: true,
          }),
        {
          wrapper: Wrapper,
          initialProps: {
            rawParams: {
              tech_ids: "python",
              start: "2024-01-01",
              end: "2024-12-31",
            },
          },
        },
      );

      await flushEffects();
      expect(onCorrect).not.toHaveBeenCalled();

      await act(async () => {
        rerender({
          rawParams: {
            tech_ids: "unknown_tech",
            start: "2024-01-01",
            end: "2024-12-31",
          },
        });
      });

      await flushEffects();

      expect(onCorrect).toHaveBeenCalled();
    });
  });

  describe("toast configuration", () => {
    it("uses warning toast type with 5 second duration", async () => {
      const onCorrect = vi.fn();
      const knownTechIds = new Set(["python"]);

      renderHook(
        () =>
          useUrlValidation({
            rawParams: {
              tech_ids: "python",
              start: "invalid",
              end: "2024-12-31",
            },
            knownTechIds,
            onCorrect,
            enabled: true,
          }),
        { wrapper: Wrapper },
      );

      await flushEffects();

      expect(mockToastWarning).toHaveBeenCalled();
      expect(mockToastWarning).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          duration: 5000,
        }),
      );
    });
  });
});
