"use client";

/**
 * @fileoverview Animated annotation component for Cinema visualization.
 *
 * Renders synchronized text overlays that appear at specific positions
 * and timing relative to scene playback. Uses framer-motion for smooth
 * fade/slide entrance animations and includes collision detection to
 * prevent overlapping trend lines.
 */

import { useMemo } from "react";

import { motion, AnimatePresence } from "framer-motion";

import { useScale, CINEMA_VIEWBOX } from "@/hooks";

import type { CinemaAnnotation, TrendPath } from "./types";

/**
 * Direction for annotation offset to avoid collision.
 */
type CollisionOffset = "above" | "below";

/**
 * Spring configuration for annotation entrance animation.
 * Softer than trend line morphing for text readability.
 */
const ANNOTATION_SPRING = {
  stiffness: 100,
  damping: 18,
} as const;

/**
 * Vertical offset in viewBox units to avoid trend line overlap.
 */
const COLLISION_OFFSET_AMOUNT = 8;

/**
 * Minimum distance from edges in viewBox units.
 */
const EDGE_PADDING = 4;

/**
 * Props for the Annotation component.
 */
export interface AnnotationProps {
  /** Annotation data including text, position, and timing */
  annotation: CinemaAnnotation;
  /** Milliseconds elapsed since scene started (for timing synchronization) */
  sceneElapsedTime: number;
  /** Whether the scene is currently in morphing phase (annotations should exit) */
  isMorphing: boolean;
  /** Trend paths in current scene for collision detection */
  trends: TrendPath[];
  /** Semantic color token for text (default: "text-primary") */
  colorToken?: string;
}

/**
 * Determine offset direction based on trend line positions.
 *
 * Checks the y-value of nearby trend points and offsets annotation
 * in the opposite direction to avoid overlap.
 *
 * @param anchor - Normalized annotation anchor position.
 * @param trends - Array of trend paths to check against.
 * @returns Direction to offset the annotation.
 */
function computeCollisionOffset(
  anchor: { x: number; y: number },
  trends: TrendPath[],
): CollisionOffset {
  if (trends.length === 0) {
    return "above";
  }

  let trendYSum = 0;
  let sampleCount = 0;

  for (const trend of trends) {
    for (const point of trend.points) {
      const xDistance = Math.abs(point.x - anchor.x);
      if (xDistance < 0.15) {
        trendYSum += point.y;
        sampleCount += 1;
      }
    }
  }

  if (sampleCount === 0) {
    return "above";
  }

  const averageTrendY = trendYSum / sampleCount;
  return anchor.y >= averageTrendY ? "above" : "below";
}

/**
 * Check if annotation should be visible based on timing.
 *
 * @param elapsedTime - Time since scene started (ms).
 * @param enterDelay - Delay before annotation appears (ms).
 * @param duration - How long annotation stays visible (ms).
 * @param isMorphing - Whether scene is transitioning.
 * @returns Whether annotation should be displayed.
 */
function shouldBeVisible(
  elapsedTime: number,
  enterDelay: number,
  duration: number,
  isMorphing: boolean,
): boolean {
  if (isMorphing) {
    return false;
  }

  const hasEntered = elapsedTime >= enterDelay;
  const hasExited = elapsedTime >= enterDelay + duration;

  return hasEntered && !hasExited;
}

/**
 * Clamp value to viewBox bounds with padding.
 *
 * @param value - Coordinate value to clamp.
 * @param min - Minimum allowed value.
 * @param max - Maximum allowed value.
 * @returns Clamped value within bounds.
 */
function clampToViewBox(value: number, min: number, max: number): number {
  return Math.max(min + EDGE_PADDING, Math.min(max - EDGE_PADDING, value));
}

/**
 * Animated annotation with synchronized timing and collision avoidance.
 *
 * Renders a text label at the specified anchor position, using framer-motion
 * for smooth fade/slide entrance. Automatically offsets position to avoid
 * overlapping trend lines and respects scene timing configuration.
 *
 * @param props - Component configuration including annotation data and timing.
 * @returns SVG group with animated text element, or null if not visible.
 *
 * @example
 * ```tsx
 * <CinemaStage>
 *   <TrendLine trend={trend} />
 *   <Annotation
 *     annotation={{
 *       text: "Rust overtakes C++",
 *       anchor: { x: 0.7, y: 0.65 },
 *       enterDelay: 500,
 *       duration: 2000,
 *     }}
 *     sceneElapsedTime={1000}
 *     isMorphing={false}
 *     trends={[trend]}
 *   />
 * </CinemaStage>
 * ```
 */
export function Annotation({
  annotation,
  sceneElapsedTime,
  isMorphing,
  trends,
  colorToken = "text-primary",
}: AnnotationProps) {
  const { scaleX, scaleY } = useScale();

  const isVisible = shouldBeVisible(
    sceneElapsedTime,
    annotation.enterDelay,
    annotation.duration,
    isMorphing,
  );

  const offsetDirection = useMemo(
    () => computeCollisionOffset(annotation.anchor, trends),
    [annotation.anchor, trends],
  );

  const position = useMemo(() => {
    const baseX = scaleX(annotation.anchor.x);
    const baseY = scaleY(annotation.anchor.y);

    const offsetY =
      offsetDirection === "above"
        ? -COLLISION_OFFSET_AMOUNT
        : COLLISION_OFFSET_AMOUNT;

    return {
      x: clampToViewBox(baseX, 0, CINEMA_VIEWBOX.width),
      y: clampToViewBox(baseY + offsetY, 0, CINEMA_VIEWBOX.height),
    };
  }, [annotation.anchor, scaleX, scaleY, offsetDirection]);

  const textAnchor = useMemo(() => {
    const normalizedX = annotation.anchor.x;
    if (normalizedX < 0.3) {
      return "start";
    }
    if (normalizedX > 0.7) {
      return "end";
    }
    return "middle";
  }, [annotation.anchor.x]);

  const textColor = `rgb(var(--tp-color-${colorToken}))`;

  const slideDirection = offsetDirection === "above" ? 6 : -6;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.g
          initial={{ opacity: 0, y: slideDirection }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: slideDirection }}
          transition={{
            type: "spring",
            ...ANNOTATION_SPRING,
          }}
          aria-live="polite"
        >
          <motion.text
            x={position.x}
            y={position.y}
            fill={textColor}
            textAnchor={textAnchor}
            dominantBaseline="middle"
            fontSize="5"
            fontFamily="var(--font-sans)"
            fontWeight="500"
            style={{ pointerEvents: "none" }}
            role="status"
          >
            {annotation.text}
          </motion.text>
        </motion.g>
      )}
    </AnimatePresence>
  );
}
