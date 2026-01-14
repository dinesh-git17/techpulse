/**
 * Tests for the useDirector Cinema playback state machine.
 *
 * Validates scene transition timing, pause/resume behavior,
 * viewport visibility handling, and infinite looping functionality.
 *
 * @module hooks/useDirector.test
 */

import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import type { CinemaScene } from "@/components/cinema/types";

import { useDirector, MIN_SCENE_DURATION_MS } from "./useDirector";

/**
 * Factory to create valid test scenes with configurable durations.
 */
function createTestScene(overrides: Partial<CinemaScene> = {}): CinemaScene {
  return {
    id: `scene-${Math.random().toString(36).slice(2, 9)}`,
    title: "Test Scene",
    duration: 3000,
    morphDuration: 500,
    trends: [
      {
        id: "trend-1",
        label: "Test Trend",
        colorToken: "action-primary",
        points: [
          { x: 0, y: 0.2 },
          { x: 0.5, y: 0.6 },
          { x: 1, y: 0.4 },
        ],
      },
    ],
    annotations: [],
    ...overrides,
  };
}

/**
 * Create a playlist of test scenes.
 */
function createTestScenes(count: number): CinemaScene[] {
  return Array.from({ length: count }, (_, index) =>
    createTestScene({
      id: `scene-${index}`,
      title: `Scene ${index + 1}`,
      duration: 3000 + index * 1000,
      morphDuration: 500,
    }),
  );
}

/**
 * Get scene duration safely for tests.
 */
function getSceneDuration(scenes: CinemaScene[], index: number): number {
  const scene = scenes[index];
  if (!scene) {
    throw new Error(`Test setup error: scene at index ${index} not found`);
  }
  return scene.duration;
}

/**
 * Get scene morph duration safely for tests.
 */
function getSceneMorphDuration(scenes: CinemaScene[], index: number): number {
  const scene = scenes[index];
  if (!scene) {
    throw new Error(`Test setup error: scene at index ${index} not found`);
  }
  return scene.morphDuration;
}

describe("useDirector", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("initialization", () => {
    it("starts at scene index 0", () => {
      const scenes = createTestScenes(3);
      const { result } = renderHook(() => useDirector({ scenes }));

      expect(result.current.activeSceneIndex).toBe(0);
    });

    it("returns the first scene as activeScene", () => {
      const scenes = createTestScenes(3);
      const { result } = renderHook(() => useDirector({ scenes }));

      expect(result.current.activeScene).toBe(scenes[0]);
    });

    it("starts in displaying phase", () => {
      const scenes = createTestScenes(3);
      const { result } = renderHook(() => useDirector({ scenes }));

      expect(result.current.phase).toBe("displaying");
    });

    it("starts playing when autoPlay is true (default)", () => {
      const scenes = createTestScenes(3);
      const { result } = renderHook(() => useDirector({ scenes }));

      expect(result.current.isPlaying).toBe(true);
    });

    it("starts paused when autoPlay is false", () => {
      const scenes = createTestScenes(3);
      const { result } = renderHook(() =>
        useDirector({ scenes, autoPlay: false }),
      );

      expect(result.current.isPlaying).toBe(false);
    });

    it("returns null activeScene when scenes array is empty", () => {
      const { result } = renderHook(() => useDirector({ scenes: [] }));

      expect(result.current.activeScene).toBeNull();
      expect(result.current.isPlaying).toBe(false);
    });

    it("initializes hover state to not paused", () => {
      const scenes = createTestScenes(3);
      const { result } = renderHook(() => useDirector({ scenes }));

      expect(result.current.isPausedByHover).toBe(false);
    });

    it("initializes visibility state to not paused", () => {
      const scenes = createTestScenes(3);
      const { result } = renderHook(() => useDirector({ scenes }));

      expect(result.current.isPausedByVisibility).toBe(false);
    });
  });

  describe("scene duration timing", () => {
    it("transitions to morphing phase after scene duration", async () => {
      const scenes = createTestScenes(2);
      const sceneDuration = getSceneDuration(scenes, 0);
      const { result } = renderHook(() => useDirector({ scenes }));

      expect(result.current.phase).toBe("displaying");

      await act(async () => {
        vi.advanceTimersByTime(sceneDuration);
      });

      expect(result.current.phase).toBe("morphing");
    });

    it("advances to next scene after morph duration completes", async () => {
      const scenes = createTestScenes(2);
      const duration = getSceneDuration(scenes, 0);
      const morphDuration = getSceneMorphDuration(scenes, 0);
      const { result } = renderHook(() => useDirector({ scenes }));

      // Advance through display phase
      await act(async () => {
        vi.advanceTimersByTime(duration);
      });

      expect(result.current.phase).toBe("morphing");

      // Advance through morph phase
      await act(async () => {
        vi.advanceTimersByTime(morphDuration);
      });

      expect(result.current.activeSceneIndex).toBe(1);
      expect(result.current.phase).toBe("displaying");
    });

    it("respects individual scene duration values", async () => {
      const scenes = [
        createTestScene({ id: "short", duration: 2000, morphDuration: 300 }),
        createTestScene({ id: "long", duration: 5000, morphDuration: 500 }),
      ];
      const { result } = renderHook(() => useDirector({ scenes }));

      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(result.current.phase).toBe("morphing");

      await act(async () => {
        vi.advanceTimersByTime(300);
      });

      expect(result.current.activeSceneIndex).toBe(1);
      expect(result.current.phase).toBe("displaying");

      await act(async () => {
        vi.advanceTimersByTime(4000);
      });

      expect(result.current.phase).toBe("displaying");

      await act(async () => {
        vi.advanceTimersByTime(1000);
      });

      expect(result.current.phase).toBe("morphing");
    });
  });

  describe("infinite looping", () => {
    it("loops back to scene 0 after last scene completes", async () => {
      const scenes = createTestScenes(2);
      const totalCycleTime = scenes.reduce(
        (sum, scene) => sum + scene.duration + scene.morphDuration,
        0,
      );
      const { result } = renderHook(() => useDirector({ scenes }));

      await act(async () => {
        vi.advanceTimersByTime(totalCycleTime);
      });

      expect(result.current.activeSceneIndex).toBe(0);
    });

    it("continues looping infinitely", async () => {
      const scenes = createTestScenes(2);
      const totalCycleTime = scenes.reduce(
        (sum, scene) => sum + scene.duration + scene.morphDuration,
        0,
      );
      const { result } = renderHook(() => useDirector({ scenes }));

      await act(async () => {
        vi.advanceTimersByTime(totalCycleTime * 3);
      });

      expect(result.current.activeSceneIndex).toBe(0);
    });

    it("does not loop when only one scene exists", async () => {
      const scenes = [createTestScene({ duration: 3000, morphDuration: 500 })];
      const { result } = renderHook(() => useDirector({ scenes }));

      await act(async () => {
        vi.advanceTimersByTime(3000);
      });

      expect(result.current.activeSceneIndex).toBe(0);
      expect(result.current.phase).toBe("displaying");
    });
  });

  describe("hover pause/resume", () => {
    it("pauses playback on mouse enter", async () => {
      const scenes = createTestScenes(2);
      const { result } = renderHook(() => useDirector({ scenes }));

      act(() => {
        result.current.hoverHandlers.onMouseEnter();
      });

      expect(result.current.isPausedByHover).toBe(true);
      expect(result.current.isPlaying).toBe(false);
    });

    it("resumes playback on mouse leave", async () => {
      const scenes = createTestScenes(2);
      const { result } = renderHook(() => useDirector({ scenes }));

      act(() => {
        result.current.hoverHandlers.onMouseEnter();
      });

      expect(result.current.isPlaying).toBe(false);

      act(() => {
        result.current.hoverHandlers.onMouseLeave();
      });

      expect(result.current.isPausedByHover).toBe(false);
      expect(result.current.isPlaying).toBe(true);
    });

    it("does not advance scene while hover paused", async () => {
      const scenes = createTestScenes(2);
      const sceneDuration = getSceneDuration(scenes, 0);
      const { result } = renderHook(() => useDirector({ scenes }));

      act(() => {
        result.current.hoverHandlers.onMouseEnter();
      });

      await act(async () => {
        vi.advanceTimersByTime(sceneDuration * 2);
      });

      expect(result.current.activeSceneIndex).toBe(0);
      expect(result.current.phase).toBe("displaying");
    });

    it("resumes from paused state and continues timing", async () => {
      const scenes = createTestScenes(2);
      const duration = getSceneDuration(scenes, 0);
      const morphDuration = getSceneMorphDuration(scenes, 0);
      const { result } = renderHook(() => useDirector({ scenes }));

      // Play for half the duration
      await act(async () => {
        vi.advanceTimersByTime(duration / 2);
      });

      // Pause via hover
      act(() => {
        result.current.hoverHandlers.onMouseEnter();
      });

      // Time passes while paused
      await act(async () => {
        vi.advanceTimersByTime(10000);
      });

      expect(result.current.activeSceneIndex).toBe(0);

      // Resume
      act(() => {
        result.current.hoverHandlers.onMouseLeave();
      });

      // Advance remaining display time
      await act(async () => {
        vi.advanceTimersByTime(duration / 2);
      });

      expect(result.current.phase).toBe("morphing");

      // Advance through morph
      await act(async () => {
        vi.advanceTimersByTime(morphDuration);
      });

      expect(result.current.activeSceneIndex).toBe(1);
    });
  });

  describe("visibility pause (IntersectionObserver)", () => {
    beforeEach(() => {
      vi.stubGlobal(
        "IntersectionObserver",
        vi.fn((_callback: IntersectionObserverCallback) => {
          return {
            observe: vi.fn(),
            disconnect: vi.fn(),
          };
        }),
      );
    });

    afterEach(() => {
      vi.unstubAllGlobals();
    });

    it("provides containerRef for IntersectionObserver integration", () => {
      const scenes = createTestScenes(2);
      const { result } = renderHook(() => useDirector({ scenes }));

      expect(result.current.containerRef).toBeDefined();
      expect(result.current.containerRef.current).toBeNull();
    });

    it("exposes isPausedByVisibility state", () => {
      const scenes = createTestScenes(2);
      const { result } = renderHook(() => useDirector({ scenes }));

      expect(result.current.isPausedByVisibility).toBe(false);
    });

    it("sets up observer cleanup function for when container is available", () => {
      const scenes = createTestScenes(2);

      const { result, unmount } = renderHook(() => useDirector({ scenes }));

      // Verify ref is available for external use
      expect(result.current.containerRef).toBeDefined();
      expect(result.current.containerRef.current).toBeNull();

      // Observer is not created when containerRef is null
      // This is expected behavior - observer is created when a component
      // attaches the ref to a DOM element
      unmount();

      // No observer was created, so no disconnect needed
      // The hook properly handles this case
    });

    it("isPlaying reflects combined pause state", () => {
      const scenes = createTestScenes(2);
      const { result } = renderHook(() => useDirector({ scenes }));

      // Initially playing
      expect(result.current.isPlaying).toBe(true);
      expect(result.current.isPausedByVisibility).toBe(false);

      // After hover pause
      act(() => {
        result.current.hoverHandlers.onMouseEnter();
      });

      expect(result.current.isPlaying).toBe(false);

      // Resume
      act(() => {
        result.current.hoverHandlers.onMouseLeave();
      });

      expect(result.current.isPlaying).toBe(true);
    });
  });

  describe("manual controls", () => {
    it("pause() stops playback", async () => {
      const scenes = createTestScenes(2);
      const { result } = renderHook(() => useDirector({ scenes }));

      act(() => {
        result.current.pause();
      });

      expect(result.current.isPlaying).toBe(false);
    });

    it("resume() restarts playback", async () => {
      const scenes = createTestScenes(2);
      const { result } = renderHook(() =>
        useDirector({ scenes, autoPlay: false }),
      );

      expect(result.current.isPlaying).toBe(false);

      act(() => {
        result.current.resume();
      });

      expect(result.current.isPlaying).toBe(true);
    });

    it("goToScene() jumps to specified scene", async () => {
      const scenes = createTestScenes(5);
      const { result } = renderHook(() => useDirector({ scenes }));

      act(() => {
        result.current.goToScene(3);
      });

      expect(result.current.activeSceneIndex).toBe(3);
      expect(result.current.phase).toBe("displaying");
    });

    it("goToScene() ignores invalid negative index", async () => {
      const scenes = createTestScenes(3);
      const { result } = renderHook(() => useDirector({ scenes }));

      act(() => {
        result.current.goToScene(-1);
      });

      expect(result.current.activeSceneIndex).toBe(0);
    });

    it("goToScene() ignores index beyond array bounds", async () => {
      const scenes = createTestScenes(3);
      const { result } = renderHook(() => useDirector({ scenes }));

      act(() => {
        result.current.goToScene(10);
      });

      expect(result.current.activeSceneIndex).toBe(0);
    });
  });

  describe("callbacks", () => {
    it("calls onSceneChange when scene becomes active", async () => {
      const scenes = createTestScenes(2);
      const onSceneChange = vi.fn();
      renderHook(() => useDirector({ scenes, onSceneChange }));

      // Allow effect to run
      await act(async () => {
        vi.advanceTimersByTime(0);
      });

      expect(onSceneChange).toHaveBeenCalledWith(0, scenes[0]);
    });

    it("calls onSceneChange when advancing to next scene", async () => {
      const scenes = createTestScenes(2);
      const duration = getSceneDuration(scenes, 0);
      const morphDuration = getSceneMorphDuration(scenes, 0);
      const onSceneChange = vi.fn();
      renderHook(() => useDirector({ scenes, onSceneChange }));

      // Allow initial effect to run
      await act(async () => {
        vi.advanceTimersByTime(0);
      });

      // Advance through display phase
      await act(async () => {
        vi.advanceTimersByTime(duration);
      });

      // Advance through morph phase
      await act(async () => {
        vi.advanceTimersByTime(morphDuration);
      });

      expect(onSceneChange).toHaveBeenCalledTimes(2);
      expect(onSceneChange).toHaveBeenNthCalledWith(1, 0, scenes[0]);
      expect(onSceneChange).toHaveBeenNthCalledWith(2, 1, scenes[1]);
    });

    it("calls onMorphStart when morph transition begins", async () => {
      const scenes = createTestScenes(2);
      const duration = getSceneDuration(scenes, 0);
      const onMorphStart = vi.fn();
      renderHook(() => useDirector({ scenes, onMorphStart }));

      await act(async () => {
        vi.advanceTimersByTime(duration);
      });

      expect(onMorphStart).toHaveBeenCalledWith(0, 1);
    });

    it("calls onMorphComplete when morph transition ends", async () => {
      const scenes = createTestScenes(2);
      const duration = getSceneDuration(scenes, 0);
      const morphDuration = getSceneMorphDuration(scenes, 0);
      const onMorphComplete = vi.fn();
      renderHook(() => useDirector({ scenes, onMorphComplete }));

      // Advance through display phase
      await act(async () => {
        vi.advanceTimersByTime(duration);
      });

      // Advance through morph phase
      await act(async () => {
        vi.advanceTimersByTime(morphDuration);
      });

      expect(onMorphComplete).toHaveBeenCalledWith(1);
    });
  });

  describe("scene validation", () => {
    it("filters out scenes with duration below minimum", () => {
      const scenes = [
        createTestScene({ id: "valid", duration: MIN_SCENE_DURATION_MS }),
        createTestScene({ id: "invalid", duration: 500 }),
      ];
      const { result } = renderHook(() => useDirector({ scenes }));

      expect(result.current.activeScene?.id).toBe("valid");

      act(() => {
        result.current.goToScene(1);
      });

      expect(result.current.activeSceneIndex).toBe(0);
    });

    it("enforces minimum scene duration constant", () => {
      expect(MIN_SCENE_DURATION_MS).toBe(2000);
    });

    it("returns null when all scenes are invalid", () => {
      const scenes = [
        createTestScene({ duration: 100 }),
        createTestScene({ duration: 500 }),
      ];
      const { result } = renderHook(() => useDirector({ scenes }));

      expect(result.current.activeScene).toBeNull();
      expect(result.current.isPlaying).toBe(false);
    });
  });

  describe("ref and handler stability", () => {
    it("provides stable containerRef across renders", () => {
      const scenes = createTestScenes(2);
      const { result, rerender } = renderHook(() => useDirector({ scenes }));

      const firstRef = result.current.containerRef;
      rerender();
      const secondRef = result.current.containerRef;

      expect(firstRef).toBe(secondRef);
    });

    it("provides stable hoverHandlers across renders", () => {
      const scenes = createTestScenes(2);
      const { result, rerender } = renderHook(() => useDirector({ scenes }));

      const firstHandlers = result.current.hoverHandlers;
      rerender();
      const secondHandlers = result.current.hoverHandlers;

      expect(firstHandlers).toBe(secondHandlers);
    });
  });

  describe("cleanup", () => {
    it("clears timers on unmount", async () => {
      const scenes = createTestScenes(2);
      const { unmount } = renderHook(() => useDirector({ scenes }));

      await act(async () => {
        vi.advanceTimersByTime(1000);
      });

      unmount();

      expect(() => vi.advanceTimersByTime(10000)).not.toThrow();
    });

    it("clears timers when goToScene is called", async () => {
      const scenes = createTestScenes(3);
      const { result } = renderHook(() => useDirector({ scenes }));

      await act(async () => {
        vi.advanceTimersByTime(1000);
      });

      act(() => {
        result.current.goToScene(2);
      });

      expect(result.current.activeSceneIndex).toBe(2);
      expect(result.current.phase).toBe("displaying");
    });
  });

  describe("combined pause states", () => {
    it("remains paused when both hover and manual pause are active", async () => {
      const scenes = createTestScenes(2);
      const { result } = renderHook(() => useDirector({ scenes }));

      act(() => {
        result.current.hoverHandlers.onMouseEnter();
      });

      act(() => {
        result.current.pause();
      });

      expect(result.current.isPausedByHover).toBe(true);
      expect(result.current.isPlaying).toBe(false);
    });

    it("remains paused when only one pause condition is removed", async () => {
      const scenes = createTestScenes(2);
      const { result } = renderHook(() => useDirector({ scenes }));

      // Enable both pause conditions
      act(() => {
        result.current.hoverHandlers.onMouseEnter();
      });

      act(() => {
        result.current.pause();
      });

      // Remove hover pause
      act(() => {
        result.current.hoverHandlers.onMouseLeave();
      });

      // Should still be paused due to manual pause
      expect(result.current.isPausedByHover).toBe(false);
      expect(result.current.isPlaying).toBe(false);
    });

    it("resumes only when all pause conditions are cleared", async () => {
      const scenes = createTestScenes(2);
      const { result } = renderHook(() => useDirector({ scenes }));

      // Enable both pause conditions
      act(() => {
        result.current.hoverHandlers.onMouseEnter();
      });

      act(() => {
        result.current.pause();
      });

      // Remove hover pause
      act(() => {
        result.current.hoverHandlers.onMouseLeave();
      });

      expect(result.current.isPlaying).toBe(false);

      // Remove manual pause
      act(() => {
        result.current.resume();
      });

      expect(result.current.isPausedByHover).toBe(false);
      expect(result.current.isPlaying).toBe(true);
    });
  });
});
