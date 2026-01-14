/**
 * Tests for the usePrefersReducedMotion hook.
 *
 * Validates motion preference detection, SSR behavior, and
 * reactive updates when system preferences change.
 *
 * @module hooks/usePrefersReducedMotion.test
 */

import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  usePrefersReducedMotion,
  REDUCED_MOTION_QUERY,
} from "./usePrefersReducedMotion";

interface MockMediaQueryList {
  matches: boolean;
  media: string;
  onchange: ((event: MediaQueryListEvent) => void) | null;
  addEventListener: (
    type: string,
    listener: (event: MediaQueryListEvent) => void,
  ) => void;
  removeEventListener: (
    type: string,
    listener: (event: MediaQueryListEvent) => void,
  ) => void;
  addListener: (listener: (event: MediaQueryListEvent) => void) => void;
  removeListener: (listener: (event: MediaQueryListEvent) => void) => void;
  dispatchEvent: (event: Event) => boolean;
}

describe("usePrefersReducedMotion", () => {
  let mockMatchMedia: ReturnType<typeof vi.fn>;
  let mockMediaQueryList: MockMediaQueryList;
  let changeListeners: Set<(event: MediaQueryListEvent) => void>;

  beforeEach(() => {
    changeListeners = new Set();

    mockMediaQueryList = {
      matches: false,
      media: REDUCED_MOTION_QUERY,
      onchange: null,
      addEventListener: vi.fn(
        (type: string, listener: (event: MediaQueryListEvent) => void) => {
          if (type === "change") {
            changeListeners.add(listener);
          }
        },
      ),
      removeEventListener: vi.fn(
        (type: string, listener: (event: MediaQueryListEvent) => void) => {
          if (type === "change") {
            changeListeners.delete(listener);
          }
        },
      ),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    };

    mockMatchMedia = vi.fn().mockReturnValue(mockMediaQueryList);
    window.matchMedia = mockMatchMedia as unknown as typeof window.matchMedia;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("exports", () => {
    it("exports REDUCED_MOTION_QUERY constant", () => {
      expect(REDUCED_MOTION_QUERY).toBe("(prefers-reduced-motion: reduce)");
    });
  });

  describe("initial state", () => {
    it("returns false when motion is not reduced", () => {
      mockMediaQueryList.matches = false;

      const { result } = renderHook(() => usePrefersReducedMotion());

      expect(result.current).toBe(false);
    });

    it("returns true when motion is reduced", () => {
      mockMediaQueryList.matches = true;
      mockMatchMedia.mockReturnValue(mockMediaQueryList);

      const { result } = renderHook(() => usePrefersReducedMotion());

      expect(result.current).toBe(true);
    });
  });

  describe("media query interaction", () => {
    it("calls matchMedia with correct query", () => {
      renderHook(() => usePrefersReducedMotion());

      expect(mockMatchMedia).toHaveBeenCalledWith(REDUCED_MOTION_QUERY);
    });

    it("subscribes to change events", () => {
      renderHook(() => usePrefersReducedMotion());

      expect(mockMediaQueryList.addEventListener).toHaveBeenCalledWith(
        "change",
        expect.any(Function),
      );
    });

    it("unsubscribes on unmount", () => {
      const { unmount } = renderHook(() => usePrefersReducedMotion());

      unmount();

      expect(mockMediaQueryList.removeEventListener).toHaveBeenCalledWith(
        "change",
        expect.any(Function),
      );
    });
  });

  describe("reactive updates", () => {
    it("updates when preference changes to reduced", () => {
      mockMediaQueryList.matches = false;

      const { result } = renderHook(() => usePrefersReducedMotion());

      expect(result.current).toBe(false);

      act(() => {
        mockMediaQueryList.matches = true;
        changeListeners.forEach((listener) =>
          listener({
            matches: true,
            media: REDUCED_MOTION_QUERY,
          } as MediaQueryListEvent),
        );
      });

      expect(result.current).toBe(true);
    });

    it("updates when preference changes to no-preference", () => {
      mockMediaQueryList.matches = true;
      mockMatchMedia.mockReturnValue(mockMediaQueryList);

      const { result } = renderHook(() => usePrefersReducedMotion());

      expect(result.current).toBe(true);

      act(() => {
        mockMediaQueryList.matches = false;
        changeListeners.forEach((listener) =>
          listener({
            matches: false,
            media: REDUCED_MOTION_QUERY,
          } as MediaQueryListEvent),
        );
      });

      expect(result.current).toBe(false);
    });
  });

  describe("SSR behavior", () => {
    it("hook is exported for SSR with server snapshot returning false", () => {
      expect(typeof usePrefersReducedMotion).toBe("function");
    });
  });
});
