/**
 * Tests for the useSceneTimer hook.
 *
 * Validates elapsed time tracking, scene change resets,
 * pause/resume behavior, and animation frame management.
 *
 * @module hooks/useSceneTimer.test
 */

import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { useSceneTimer, type UseSceneTimerOptions } from "./useSceneTimer";

describe("useSceneTimer", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("initialization", () => {
    it("starts with elapsedTime of 0", () => {
      const { result } = renderHook(() =>
        useSceneTimer({
          sceneId: "scene-1",
          phase: "displaying",
          isPlaying: true,
        }),
      );

      expect(result.current.elapsedTime).toBe(0);
    });

    it("provides a reset function", () => {
      const { result } = renderHook(() =>
        useSceneTimer({
          sceneId: "scene-1",
          phase: "displaying",
          isPlaying: true,
        }),
      );

      expect(typeof result.current.reset).toBe("function");
    });
  });

  describe("time tracking", () => {
    it("increments elapsedTime when playing and displaying", async () => {
      const { result } = renderHook(() =>
        useSceneTimer({
          sceneId: "scene-1",
          phase: "displaying",
          isPlaying: true,
        }),
      );

      await act(async () => {
        vi.advanceTimersByTime(500);
      });

      expect(result.current.elapsedTime).toBeGreaterThan(0);
    });

    it("does not increment when not playing", async () => {
      const { result } = renderHook(() =>
        useSceneTimer({
          sceneId: "scene-1",
          phase: "displaying",
          isPlaying: false,
        }),
      );

      await act(async () => {
        vi.advanceTimersByTime(1000);
      });

      expect(result.current.elapsedTime).toBe(0);
    });

    it("does not increment during morphing phase", async () => {
      const { result } = renderHook(() =>
        useSceneTimer({
          sceneId: "scene-1",
          phase: "morphing",
          isPlaying: true,
        }),
      );

      await act(async () => {
        vi.advanceTimersByTime(1000);
      });

      expect(result.current.elapsedTime).toBe(0);
    });

    it("does not increment when sceneId is null", async () => {
      const { result } = renderHook(() =>
        useSceneTimer({
          sceneId: null,
          phase: "displaying",
          isPlaying: true,
        }),
      );

      await act(async () => {
        vi.advanceTimersByTime(1000);
      });

      expect(result.current.elapsedTime).toBe(0);
    });
  });

  describe("scene transitions", () => {
    it("resets elapsedTime when sceneId changes", async () => {
      const { result, rerender } = renderHook((props) => useSceneTimer(props), {
        initialProps: {
          sceneId: "scene-1",
          phase: "displaying" as const,
          isPlaying: true,
        },
      });

      await act(async () => {
        vi.advanceTimersByTime(500);
      });

      expect(result.current.elapsedTime).toBeGreaterThan(0);

      rerender({
        sceneId: "scene-2",
        phase: "displaying",
        isPlaying: true,
      });

      expect(result.current.elapsedTime).toBe(0);
    });

    it("resets elapsedTime when transitioning from morphing to displaying", async () => {
      const { result, rerender } = renderHook(
        (props: UseSceneTimerOptions) => useSceneTimer(props),
        {
          initialProps: {
            sceneId: "scene-1",
            phase: "displaying",
            isPlaying: true,
          } as UseSceneTimerOptions,
        },
      );

      await act(async () => {
        vi.advanceTimersByTime(500);
      });

      const elapsedBeforeMorph = result.current.elapsedTime;
      expect(elapsedBeforeMorph).toBeGreaterThan(0);

      rerender({
        sceneId: "scene-1",
        phase: "morphing",
        isPlaying: true,
      });

      rerender({
        sceneId: "scene-1",
        phase: "displaying",
        isPlaying: true,
      });

      expect(result.current.elapsedTime).toBe(0);
    });

    it("stops timer when entering morphing phase", async () => {
      const { result, rerender } = renderHook(
        (props: UseSceneTimerOptions) => useSceneTimer(props),
        {
          initialProps: {
            sceneId: "scene-1",
            phase: "displaying",
            isPlaying: true,
          } as UseSceneTimerOptions,
        },
      );

      await act(async () => {
        vi.advanceTimersByTime(500);
      });

      const elapsedBeforeMorph = result.current.elapsedTime;

      rerender({
        sceneId: "scene-1",
        phase: "morphing",
        isPlaying: true,
      });

      await act(async () => {
        vi.advanceTimersByTime(500);
      });

      expect(result.current.elapsedTime).toBe(elapsedBeforeMorph);
    });
  });

  describe("pause and resume", () => {
    it("pauses timer when isPlaying becomes false", async () => {
      const { result, rerender } = renderHook((props) => useSceneTimer(props), {
        initialProps: {
          sceneId: "scene-1",
          phase: "displaying" as const,
          isPlaying: true,
        },
      });

      await act(async () => {
        vi.advanceTimersByTime(500);
      });

      const elapsedAtPause = result.current.elapsedTime;

      rerender({
        sceneId: "scene-1",
        phase: "displaying",
        isPlaying: false,
      });

      await act(async () => {
        vi.advanceTimersByTime(1000);
      });

      expect(result.current.elapsedTime).toBe(elapsedAtPause);
    });

    it("resumes timer when isPlaying becomes true again", async () => {
      const { result, rerender } = renderHook((props) => useSceneTimer(props), {
        initialProps: {
          sceneId: "scene-1",
          phase: "displaying" as const,
          isPlaying: true,
        },
      });

      await act(async () => {
        vi.advanceTimersByTime(500);
      });

      const elapsedAtPause = result.current.elapsedTime;

      rerender({
        sceneId: "scene-1",
        phase: "displaying",
        isPlaying: false,
      });

      rerender({
        sceneId: "scene-1",
        phase: "displaying",
        isPlaying: true,
      });

      await act(async () => {
        vi.advanceTimersByTime(500);
      });

      expect(result.current.elapsedTime).toBeGreaterThan(elapsedAtPause);
    });
  });

  describe("reset function", () => {
    it("resets elapsedTime to 0", async () => {
      const { result } = renderHook(() =>
        useSceneTimer({
          sceneId: "scene-1",
          phase: "displaying",
          isPlaying: true,
        }),
      );

      await act(async () => {
        vi.advanceTimersByTime(500);
      });

      expect(result.current.elapsedTime).toBeGreaterThan(0);

      act(() => {
        result.current.reset();
      });

      expect(result.current.elapsedTime).toBe(0);
    });
  });

  describe("cleanup", () => {
    it("cancels animation frame on unmount", () => {
      const cancelSpy = vi.spyOn(window, "cancelAnimationFrame");

      const { unmount } = renderHook(() =>
        useSceneTimer({
          sceneId: "scene-1",
          phase: "displaying",
          isPlaying: true,
        }),
      );

      unmount();

      expect(cancelSpy).toHaveBeenCalled();
      cancelSpy.mockRestore();
    });

    it("does not throw when unmounting while paused", () => {
      const { unmount } = renderHook(() =>
        useSceneTimer({
          sceneId: "scene-1",
          phase: "displaying",
          isPlaying: false,
        }),
      );

      expect(() => unmount()).not.toThrow();
    });
  });

  describe("result stability", () => {
    it("reset function reference remains stable across renders", () => {
      const { result, rerender } = renderHook(() =>
        useSceneTimer({
          sceneId: "scene-1",
          phase: "displaying",
          isPlaying: true,
        }),
      );

      const firstReset = result.current.reset;

      rerender();

      expect(result.current.reset).toBe(firstReset);
    });
  });
});
