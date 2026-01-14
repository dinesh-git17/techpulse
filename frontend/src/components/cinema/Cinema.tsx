"use client";

/**
 * @fileoverview Cinema visualization orchestrator component.
 *
 * Main entry point for the cinematic trend visualization engine.
 * Handles SSR hydration, reduced motion preferences, data loading
 * failures, and orchestrates the full animated experience.
 */

import { type ReactNode, useMemo, useSyncExternalStore } from "react";

import { useDirector, usePrefersReducedMotion } from "@/hooks";

import { AnnotationLayer } from "./AnnotationLayer";
import { CinemaStage } from "./CinemaStage";
import { StaticFallback } from "./StaticFallback";
import { StaticSceneRenderer } from "./StaticSceneRenderer";
import { TrendLine } from "./TrendLine";
import type { CinemaScene } from "./types";

/**
 * Props for the Cinema component.
 */
export interface CinemaProps {
  /** Array of scenes to cycle through. Empty array triggers fallback. */
  scenes: CinemaScene[];
  /** Start playback automatically on mount (default: true) */
  autoPlay?: boolean;
  /** Additional CSS classes for the container wrapper */
  className?: string;
  /** Accessible label describing the visualization content */
  "aria-label"?: string;
  /** Callback when scene transition begins */
  onSceneChange?: (sceneIndex: number, scene: CinemaScene) => void;
  /** Callback when morph transition begins */
  onMorphStart?: (fromIndex: number, toIndex: number) => void;
  /** Callback when morph transition completes */
  onMorphComplete?: (sceneIndex: number) => void;
}

/**
 * Hook to detect client-side hydration without triggering cascading renders.
 *
 * @returns True on client after hydration, false during SSR.
 */
function useIsHydrated(): boolean {
  const subscribe = (): (() => void) => {
    return () => {};
  };

  const getSnapshot = (): boolean => {
    return true;
  };

  const getServerSnapshot = (): boolean => {
    return false;
  };

  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

/**
 * Cinematic visualization orchestrator for the landing page Hero section.
 *
 * Renders an animated trend visualization that auto-plays through a
 * sequence of data stories. Handles multiple rendering modes:
 *
 * 1. **SSR Mode:** Server renders Scene 1 as static SVG for LCP optimization
 * 2. **Reduced Motion:** Shows static Scene 1 without animation (WCAG 2.3.3)
 * 3. **Animated Mode:** Full Director-controlled playback with morphing
 * 4. **Fallback Mode:** Branded placeholder when no scenes provided
 *
 * Implements hover-to-pause (WCAG 2.2.2) and viewport visibility optimization.
 *
 * @param props - Component configuration including scenes and callbacks.
 * @returns Cinema visualization container with appropriate rendering mode.
 *
 * @example
 * ```tsx
 * <Cinema
 *   scenes={trendScenes}
 *   autoPlay={true}
 *   aria-label="Technology trend comparison"
 *   onSceneChange={(idx, scene) => console.log(`Now playing: ${scene.title}`)}
 * />
 * ```
 */
export function Cinema({
  scenes,
  autoPlay = true,
  className,
  "aria-label": ariaLabel = "Technology trend visualization",
  onSceneChange,
  onMorphStart,
  onMorphComplete,
}: CinemaProps): ReactNode {
  const prefersReducedMotion = usePrefersReducedMotion();
  const isHydrated = useIsHydrated();

  const firstScene = scenes[0] ?? null;

  const { activeScene, phase, isPlaying, containerRef, hoverHandlers } =
    useDirector({
      scenes,
      autoPlay: autoPlay && !prefersReducedMotion,
      onSceneChange,
      onMorphStart,
      onMorphComplete,
    });

  const shouldShowStatic = useMemo(() => {
    if (scenes.length === 0) {
      return false;
    }

    if (prefersReducedMotion) {
      return true;
    }

    if (!isHydrated) {
      return true;
    }

    return false;
  }, [scenes.length, prefersReducedMotion, isHydrated]);

  if (scenes.length === 0 || firstScene === null) {
    return (
      <StaticFallback
        className={className}
        aria-label="Trend visualization temporarily unavailable"
      />
    );
  }

  if (shouldShowStatic) {
    return (
      <div
        className={className}
        aria-label={ariaLabel}
        data-testid="cinema-static"
      >
        <CinemaStage aria-label={ariaLabel}>
          <StaticSceneRenderer scene={firstScene} />
        </CinemaStage>
      </div>
    );
  }

  return (
    <div
      ref={containerRef as React.RefObject<HTMLDivElement>}
      className={className}
      data-testid="cinema-animated"
      {...hoverHandlers}
    >
      <CinemaStage aria-label={ariaLabel}>
        {activeScene?.trends.map((trend) => (
          <TrendLine key={trend.id} trend={trend} />
        ))}

        <AnnotationLayer
          scene={activeScene}
          phase={phase}
          isPlaying={isPlaying}
        />
      </CinemaStage>
    </div>
  );
}
