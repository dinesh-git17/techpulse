"use client";

/**
 * @fileoverview Director state machine for Cinema visualization playback.
 *
 * Orchestrates the playlist of CinemaScene objects, managing automatic
 * scene transitions, pause/resume behavior, and viewport visibility.
 * The Director is the "conductor" that drives the narrative animation.
 */

import { useState, useEffect, useRef, useCallback, useMemo } from "react";

import type { CinemaScene } from "@/components/cinema/types";

/**
 * Minimum allowed scene duration in milliseconds.
 * Enforced to prevent seizure-inducing rapid transitions.
 */
export const MIN_SCENE_DURATION_MS = 2000;

/**
 * Playback phase within the Director lifecycle.
 */
export type DirectorPhase = "displaying" | "morphing";

/**
 * Configuration options for the useDirector hook.
 */
export interface UseDirectorOptions {
  /** Array of scenes to cycle through. Must contain at least one scene. */
  scenes: CinemaScene[];
  /** Start playback automatically on mount (default: true) */
  autoPlay?: boolean;
  /** Callback when scene transition begins */
  onSceneChange?: (sceneIndex: number, scene: CinemaScene) => void;
  /** Callback when morph transition begins */
  onMorphStart?: (fromIndex: number, toIndex: number) => void;
  /** Callback when morph transition completes */
  onMorphComplete?: (sceneIndex: number) => void;
}

/**
 * Return value from the useDirector hook.
 */
export interface UseDirectorResult {
  /** Index of the currently active scene */
  activeSceneIndex: number;
  /** The currently active scene object, or null if no scenes provided */
  activeScene: CinemaScene | null;
  /** Current playback phase: displaying content or morphing to next scene */
  phase: DirectorPhase;
  /** Whether animation is currently playing (not paused) */
  isPlaying: boolean;
  /** Whether playback is paused due to hover */
  isPausedByHover: boolean;
  /** Whether playback is paused due to viewport visibility */
  isPausedByVisibility: boolean;
  /** Ref to attach to the container element for IntersectionObserver */
  containerRef: React.RefObject<HTMLElement | null>;
  /** Event handlers to attach for hover pause/resume */
  hoverHandlers: {
    onMouseEnter: () => void;
    onMouseLeave: () => void;
  };
  /** Manually pause playback */
  pause: () => void;
  /** Manually resume playback */
  resume: () => void;
  /** Jump to a specific scene index */
  goToScene: (index: number) => void;
}

/**
 * Validate scene duration meets minimum requirements.
 *
 * @param scene - Scene to validate.
 * @returns True if scene duration is valid.
 */
function isValidSceneDuration(scene: CinemaScene): boolean {
  return scene.duration >= MIN_SCENE_DURATION_MS;
}

/**
 * Director state machine for Cinema visualization playback.
 *
 * Manages automatic scene transitions through a playlist of CinemaScene
 * objects, respecting per-scene timing configuration. Implements pause
 * behavior for hover (WCAG 2.2.2) and viewport visibility optimization.
 *
 * @param options - Director configuration including scenes and callbacks.
 * @returns State, refs, and handlers for controlling playback.
 *
 * @example
 * ```tsx
 * const {
 *   activeScene,
 *   phase,
 *   isPlaying,
 *   containerRef,
 *   hoverHandlers,
 * } = useDirector({
 *   scenes: cinemaScenes,
 *   onSceneChange: (index, scene) => console.log(`Now playing: ${scene.title}`),
 * });
 *
 * return (
 *   <div ref={containerRef} {...hoverHandlers}>
 *     {activeScene && <TrendLine trend={activeScene.trends[0]} />}
 *   </div>
 * );
 * ```
 */
export function useDirector(options: UseDirectorOptions): UseDirectorResult {
  const {
    scenes,
    autoPlay = true,
    onSceneChange,
    onMorphStart,
    onMorphComplete,
  } = options;

  const [activeSceneIndex, setActiveSceneIndex] = useState(0);
  const [phase, setPhase] = useState<DirectorPhase>("displaying");
  const [isPausedByHover, setIsPausedByHover] = useState(false);
  const [isPausedByVisibility, setIsPausedByVisibility] = useState(false);
  const [isManuallyPaused, setIsManuallyPaused] = useState(!autoPlay);

  const containerRef = useRef<HTMLElement | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const phaseStartTimeRef = useRef<number>(0);
  const remainingTimeRef = useRef<number>(0);
  const callbacksRef = useRef({ onSceneChange, onMorphStart, onMorphComplete });

  // Keep callbacks ref up to date
  useEffect(() => {
    callbacksRef.current = { onSceneChange, onMorphStart, onMorphComplete };
  }, [onSceneChange, onMorphStart, onMorphComplete]);

  const validScenes = useMemo(
    () => scenes.filter(isValidSceneDuration),
    [scenes],
  );

  const activeScene = useMemo(() => {
    if (validScenes.length === 0) {
      return null;
    }
    return validScenes[activeSceneIndex] ?? null;
  }, [validScenes, activeSceneIndex]);

  const isPlaying = useMemo(() => {
    return (
      !isPausedByHover &&
      !isPausedByVisibility &&
      !isManuallyPaused &&
      validScenes.length > 0
    );
  }, [
    isPausedByHover,
    isPausedByVisibility,
    isManuallyPaused,
    validScenes.length,
  ]);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const getNextSceneIndex = useCallback(
    (currentIndex: number): number => {
      if (validScenes.length === 0) {
        return 0;
      }
      return (currentIndex + 1) % validScenes.length;
    },
    [validScenes.length],
  );

  const handleMouseEnter = useCallback(() => {
    setIsPausedByHover(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    setIsPausedByHover(false);
  }, []);

  const pause = useCallback(() => {
    setIsManuallyPaused(true);
  }, []);

  const resume = useCallback(() => {
    setIsManuallyPaused(false);
  }, []);

  const goToScene = useCallback(
    (index: number) => {
      if (index < 0 || index >= validScenes.length) {
        return;
      }
      clearTimer();
      setActiveSceneIndex(index);
      setPhase("displaying");
      remainingTimeRef.current = 0;
    },
    [validScenes.length, clearTimer],
  );

  // Main playback effect - manages timer lifecycle
  useEffect(() => {
    // Not playing - don't schedule anything
    if (!activeScene || !isPlaying || validScenes.length === 0) {
      return;
    }

    // Skip looping for single scene
    if (validScenes.length === 1) {
      if (
        phase === "displaying" &&
        timerRef.current === null &&
        remainingTimeRef.current === 0
      ) {
        callbacksRef.current.onSceneChange?.(activeSceneIndex, activeScene);
      }
      return;
    }

    const scheduleNextTransition = () => {
      if (phase === "displaying") {
        const duration =
          remainingTimeRef.current > 0
            ? remainingTimeRef.current
            : activeScene.duration;

        if (remainingTimeRef.current === 0) {
          callbacksRef.current.onSceneChange?.(activeSceneIndex, activeScene);
        }

        phaseStartTimeRef.current = Date.now();
        remainingTimeRef.current = duration;

        timerRef.current = setTimeout(() => {
          remainingTimeRef.current = 0;
          const nextIndex = getNextSceneIndex(activeSceneIndex);
          callbacksRef.current.onMorphStart?.(activeSceneIndex, nextIndex);
          setPhase("morphing");
        }, duration);
      } else {
        const duration =
          remainingTimeRef.current > 0
            ? remainingTimeRef.current
            : activeScene.morphDuration;

        phaseStartTimeRef.current = Date.now();
        remainingTimeRef.current = duration;

        timerRef.current = setTimeout(() => {
          remainingTimeRef.current = 0;
          const nextIndex = getNextSceneIndex(activeSceneIndex);
          callbacksRef.current.onMorphComplete?.(nextIndex);
          setActiveSceneIndex(nextIndex);
          setPhase("displaying");
        }, duration);
      }
    };

    if (timerRef.current === null) {
      scheduleNextTransition();
    }

    return () => {
      // Capture remaining time when pausing (cleanup runs before next effect)
      if (timerRef.current !== null) {
        const elapsed = Date.now() - phaseStartTimeRef.current;
        remainingTimeRef.current = Math.max(
          0,
          remainingTimeRef.current - elapsed,
        );
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [
    activeScene,
    activeSceneIndex,
    phase,
    isPlaying,
    validScenes.length,
    getNextSceneIndex,
  ]);

  // IntersectionObserver for viewport visibility
  useEffect(() => {
    const element = containerRef.current;
    if (!element) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry) {
          setIsPausedByVisibility(!entry.isIntersecting);
        }
      },
      {
        threshold: 0.1,
      },
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimer();
    };
  }, [clearTimer]);

  const hoverHandlers = useMemo(
    () => ({
      onMouseEnter: handleMouseEnter,
      onMouseLeave: handleMouseLeave,
    }),
    [handleMouseEnter, handleMouseLeave],
  );

  return {
    activeSceneIndex,
    activeScene,
    phase,
    isPlaying,
    isPausedByHover,
    isPausedByVisibility,
    containerRef,
    hoverHandlers,
    pause,
    resume,
    goToScene,
  };
}
