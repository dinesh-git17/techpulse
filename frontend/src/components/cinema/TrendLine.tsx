"use client";

/**
 * @fileoverview Animated trend line component with path morphing.
 *
 * Renders a single trend line that smoothly morphs between data states
 * using flubber for path interpolation and framer-motion for spring physics.
 * Designed for the Cinema visualization engine's narrative animations.
 */

import { useEffect, useRef, useMemo, useCallback } from "react";

import { interpolate } from "flubber";
import { useMotionValue, animate } from "framer-motion";

import { useScale } from "@/hooks";

import type { TrendPath, NormalizedPoint } from "./types";

/**
 * Spring physics configuration for path morphing.
 * Creates a "heavy" feel that makes data transitions feel substantial.
 */
export const SPRING_CONFIG = {
  stiffness: 120,
  damping: 20,
} as const;

/**
 * Props for the TrendLine component.
 */
export interface TrendLineProps {
  /** Trend data including points, label, and color configuration */
  trend: TrendPath;
  /** Stroke width in SVG units (default: 2) */
  strokeWidth?: number;
  /** Callback when morph animation completes */
  onMorphComplete?: () => void;
}

/**
 * Convert normalized points to SVG path coordinates.
 *
 * @param points - Array of normalized [0-1] coordinate points.
 * @param scaleX - Function to scale x coordinate to viewBox units.
 * @param scaleY - Function to scale y coordinate to viewBox units.
 * @returns Array of [x, y] tuples in viewBox coordinates.
 */
function pointsToCoordinates(
  points: NormalizedPoint[],
  scaleX: (value: number) => number,
  scaleY: (value: number) => number,
): Array<[number, number]> {
  return points.map((point) => [scaleX(point.x), scaleY(point.y)]);
}

/**
 * Generate SVG path string from coordinate array.
 *
 * @param coordinates - Array of [x, y] coordinate tuples.
 * @returns SVG path d attribute string.
 */
function coordinatesToPath(coordinates: Array<[number, number]>): string {
  const first = coordinates[0];
  if (first === undefined) {
    return "";
  }

  const rest = coordinates.slice(1);
  const moveCommand = `M ${first[0]},${first[1]}`;
  const lineCommands = rest.map(([x, y]) => `L ${x},${y}`).join(" ");

  return `${moveCommand} ${lineCommands}`;
}

/**
 * Animated trend line with smooth path morphing.
 *
 * Renders an SVG path that morphs between data states using flubber
 * for topological interpolation and framer-motion spring physics for
 * natural, weighted animation feel.
 *
 * @param props - Component configuration including trend data.
 * @returns SVG path element with animated d attribute.
 *
 * @example
 * ```tsx
 * <CinemaStage>
 *   <TrendLine
 *     trend={{
 *       id: "rust",
 *       label: "Rust",
 *       colorToken: "action-primary",
 *       points: [{ x: 0, y: 0.2 }, { x: 0.5, y: 0.6 }, { x: 1, y: 0.8 }]
 *     }}
 *   />
 * </CinemaStage>
 * ```
 */
export function TrendLine({
  trend,
  strokeWidth = 2,
  onMorphComplete,
}: TrendLineProps) {
  const { scaleX, scaleY } = useScale();
  const pathRef = useRef<SVGPathElement>(null);
  const previousPathRef = useRef<string | null>(null);
  const animationRef = useRef<ReturnType<typeof animate> | null>(null);

  const currentCoordinates = useMemo(
    () => pointsToCoordinates(trend.points, scaleX, scaleY),
    [trend.points, scaleX, scaleY],
  );

  const currentPath = useMemo(
    () => coordinatesToPath(currentCoordinates),
    [currentCoordinates],
  );

  const progress = useMotionValue(1);

  const updatePath = useCallback(
    (interpolator: ((t: number) => string) | null, progressValue: number) => {
      if (pathRef.current) {
        if (interpolator) {
          pathRef.current.setAttribute("d", interpolator(progressValue));
        } else {
          pathRef.current.setAttribute("d", currentPath);
        }
      }
    },
    [currentPath],
  );

  useEffect(() => {
    const previousPath = previousPathRef.current;

    if (previousPath === null) {
      previousPathRef.current = currentPath;
      if (pathRef.current) {
        pathRef.current.setAttribute("d", currentPath);
      }
      return;
    }

    if (previousPath === currentPath) {
      return;
    }

    if (animationRef.current) {
      animationRef.current.stop();
    }

    const interpolator = interpolate(previousPath, currentPath, {
      maxSegmentLength: 10,
    });

    progress.set(0);

    animationRef.current = animate(progress, 1, {
      type: "spring",
      ...SPRING_CONFIG,
      onUpdate: (value) => updatePath(interpolator, value),
      onComplete: () => {
        previousPathRef.current = currentPath;
        onMorphComplete?.();
      },
    });

    return () => {
      if (animationRef.current) {
        animationRef.current.stop();
      }
    };
  }, [currentPath, progress, updatePath, onMorphComplete]);

  const strokeColor = `rgb(var(--tp-color-${trend.colorToken}))`;

  return (
    <path
      ref={pathRef}
      d={currentPath}
      fill="none"
      stroke={strokeColor}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-label={`Trend line for ${trend.label}`}
    />
  );
}
