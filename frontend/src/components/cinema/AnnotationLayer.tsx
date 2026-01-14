"use client";

/**
 * @fileoverview Annotation layer for Cinema visualization scenes.
 *
 * Manages rendering of all annotations for the active scene, handling
 * timing synchronization with Director state and coordinating entry/exit
 * animations across multiple text labels.
 */

import { useSceneTimer, type DirectorPhase } from "@/hooks";

import { Annotation } from "./Annotation";
import type { CinemaScene } from "./types";

/**
 * Props for the AnnotationLayer component.
 */
export interface AnnotationLayerProps {
  /** Currently active scene containing annotations to render */
  scene: CinemaScene | null;
  /** Current Director playback phase */
  phase: DirectorPhase;
  /** Whether playback is currently active */
  isPlaying: boolean;
  /** Semantic color token for annotation text (default: "text-primary") */
  colorToken?: string;
}

/**
 * Coordinated annotation layer for Cinema scene playback.
 *
 * Renders all annotations defined in the active scene with synchronized
 * timing relative to scene start. Manages the scene timer internally
 * and passes elapsed time to individual Annotation components.
 *
 * @param props - Component configuration including scene and playback state.
 * @returns SVG group containing all animated annotation elements.
 *
 * @example
 * ```tsx
 * const { activeScene, phase, isPlaying, containerRef, hoverHandlers } =
 *   useDirector({ scenes });
 *
 * <div ref={containerRef} {...hoverHandlers}>
 *   <CinemaStage>
 *     {activeScene?.trends.map((trend) => (
 *       <TrendLine key={trend.id} trend={trend} />
 *     ))}
 *     <AnnotationLayer
 *       scene={activeScene}
 *       phase={phase}
 *       isPlaying={isPlaying}
 *     />
 *   </CinemaStage>
 * </div>
 * ```
 */
export function AnnotationLayer({
  scene,
  phase,
  isPlaying,
  colorToken = "text-primary",
}: AnnotationLayerProps) {
  const { elapsedTime } = useSceneTimer({
    sceneId: scene?.id ?? null,
    phase,
    isPlaying,
  });

  if (scene === null) {
    return null;
  }

  const isMorphing = phase === "morphing";

  return (
    <g aria-label="Scene annotations" role="group">
      {scene.annotations.map((annotation, index) => (
        <Annotation
          key={`${scene.id}-annotation-${index}`}
          annotation={annotation}
          sceneElapsedTime={elapsedTime}
          isMorphing={isMorphing}
          trends={scene.trends}
          colorToken={colorToken}
        />
      ))}
    </g>
  );
}
