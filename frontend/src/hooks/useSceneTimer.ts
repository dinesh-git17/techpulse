"use client";

/**
 * @fileoverview Scene timer hook for annotation synchronization.
 *
 * Tracks elapsed time since the current scene started displaying,
 * enabling precise timing of annotation enter/exit animations
 * relative to the Director's scene transitions.
 */

import { useState, useEffect, useRef, useCallback } from "react";

import type { DirectorPhase } from "./useDirector";

/**
 * Target frame rate for timer updates (60fps).
 */
const FRAME_INTERVAL_MS = 1000 / 60;

/**
 * Configuration options for the useSceneTimer hook.
 */
export interface UseSceneTimerOptions {
  /** Current scene identifier (resets timer on change) */
  sceneId: string | null;
  /** Current Director playback phase */
  phase: DirectorPhase;
  /** Whether playback is currently active */
  isPlaying: boolean;
}

/**
 * Return value from the useSceneTimer hook.
 */
export interface UseSceneTimerResult {
  /** Milliseconds elapsed since current scene started */
  elapsedTime: number;
  /** Reset timer to zero */
  reset: () => void;
}

/**
 * Track elapsed time since scene started displaying.
 *
 * Uses requestAnimationFrame for smooth 60fps updates while respecting
 * pause states and scene transitions. Timer resets when scene changes
 * or enters displaying phase from morphing.
 *
 * @param options - Timer configuration including scene and playback state.
 * @returns Elapsed time in milliseconds and reset function.
 *
 * @example
 * ```tsx
 * const { activeScene, phase, isPlaying } = useDirector({ scenes });
 *
 * const { elapsedTime } = useSceneTimer({
 *   sceneId: activeScene?.id ?? null,
 *   phase,
 *   isPlaying,
 * });
 *
 * // Use elapsedTime to sync annotation timing
 * <Annotation sceneElapsedTime={elapsedTime} ... />
 * ```
 */
export function useSceneTimer(
  options: UseSceneTimerOptions,
): UseSceneTimerResult {
  const { sceneId, phase, isPlaying } = options;

  const [elapsedTime, setElapsedTime] = useState(0);

  const frameRef = useRef<number | null>(null);
  const lastTickRef = useRef<number>(0);
  const accumulatedTimeRef = useRef(0);
  const previousSceneIdRef = useRef<string | null>(sceneId);
  const previousPhaseRef = useRef<DirectorPhase>(phase);

  const reset = useCallback(() => {
    accumulatedTimeRef.current = 0;
    lastTickRef.current = 0;
    setElapsedTime(0);
  }, []);

  useEffect(() => {
    const sceneChanged = sceneId !== previousSceneIdRef.current;
    const enteredDisplaying =
      phase === "displaying" && previousPhaseRef.current === "morphing";

    previousSceneIdRef.current = sceneId;
    previousPhaseRef.current = phase;

    if (sceneChanged || enteredDisplaying) {
      accumulatedTimeRef.current = 0;
      lastTickRef.current = 0;
      // Required: Reset state on scene/phase transitions (React docs: adjusting state when props change)
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setElapsedTime(0);
    }
  }, [sceneId, phase]);

  useEffect(() => {
    if (phase === "morphing") {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
        frameRef.current = null;
      }
      return;
    }

    const shouldTick = isPlaying && phase === "displaying" && sceneId !== null;

    if (!shouldTick) {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
        frameRef.current = null;
      }
      return;
    }

    if (lastTickRef.current === 0) {
      lastTickRef.current = performance.now();
    }

    const tick = (timestamp: number) => {
      const delta = timestamp - lastTickRef.current;

      if (delta >= FRAME_INTERVAL_MS) {
        accumulatedTimeRef.current += delta;
        const newElapsed = Math.floor(accumulatedTimeRef.current);
        setElapsedTime(newElapsed);
        lastTickRef.current = timestamp;
      }

      frameRef.current = requestAnimationFrame(tick);
    };

    frameRef.current = requestAnimationFrame(tick);

    return () => {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
        frameRef.current = null;
      }
    };
  }, [sceneId, phase, isPlaying]);

  useEffect(() => {
    return () => {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
      }
    };
  }, []);

  return {
    elapsedTime,
    reset,
  };
}
