/**
 * @fileoverview Static scene renderer for SSR and reduced motion mode.
 *
 * Renders a CinemaScene without animation, displaying trend lines and
 * annotations in their final state. Used for server-side rendering of
 * the first frame and for users who prefer reduced motion.
 */

import { type ReactNode, useMemo } from "react";

import { useScale, CINEMA_VIEWBOX } from "@/hooks";

import type { CinemaScene, TrendPath, CinemaAnnotation } from "./types";

/**
 * Props for the StaticSceneRenderer component.
 */
export interface StaticSceneRendererProps {
  /** Scene to render statically */
  scene: CinemaScene;
}

/**
 * Props for internal StaticTrendLine component.
 */
interface StaticTrendLineProps {
  /** Trend data to render */
  trend: TrendPath;
  /** Stroke width in SVG units */
  strokeWidth?: number;
}

/**
 * Props for internal StaticAnnotation component.
 */
interface StaticAnnotationProps {
  /** Annotation data to render */
  annotation: CinemaAnnotation;
  /** Semantic color token for text */
  colorToken?: string;
}

/**
 * Minimum distance from edges in viewBox units.
 */
const EDGE_PADDING = 4;

/**
 * Vertical offset in viewBox units for collision avoidance.
 */
const COLLISION_OFFSET_AMOUNT = 8;

/**
 * Static trend line without animation.
 *
 * @param props - Component configuration.
 * @returns SVG path element.
 */
function StaticTrendLine({
  trend,
  strokeWidth = 2,
}: StaticTrendLineProps): ReactNode {
  const { scaleX, scaleY } = useScale();

  const pathData = useMemo(() => {
    if (trend.points.length === 0) {
      return "";
    }

    const first = trend.points[0];
    if (first === undefined) {
      return "";
    }

    const moveCommand = `M ${scaleX(first.x)},${scaleY(first.y)}`;
    const lineCommands = trend.points
      .slice(1)
      .map((point) => `L ${scaleX(point.x)},${scaleY(point.y)}`)
      .join(" ");

    return `${moveCommand} ${lineCommands}`;
  }, [trend.points, scaleX, scaleY]);

  const strokeColor = `rgb(var(--tp-color-${trend.colorToken}))`;

  return (
    <path
      d={pathData}
      fill="none"
      stroke={strokeColor}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-label={`Trend line for ${trend.label}`}
    />
  );
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
 * Determine offset direction based on trend line positions.
 *
 * @param anchor - Normalized annotation anchor position.
 * @param trends - Array of trend paths to check against.
 * @returns Direction to offset the annotation.
 */
function computeCollisionOffset(
  anchor: { x: number; y: number },
  trends: TrendPath[],
): "above" | "below" {
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
 * Static annotation without animation.
 *
 * @param props - Component configuration.
 * @returns SVG text element.
 */
function StaticAnnotation({
  annotation,
  colorToken = "text-primary",
  trends,
}: StaticAnnotationProps & { trends: TrendPath[] }): ReactNode {
  const { scaleX, scaleY } = useScale();

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

  return (
    <text
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
    </text>
  );
}

/**
 * Static scene renderer for SSR and reduced motion mode.
 *
 * Renders all trend lines and annotations in their final positions
 * without animation. All annotations are displayed in static mode
 * since there is no timeline progression.
 *
 * @param props - Component configuration including scene data.
 * @returns SVG group containing static scene elements.
 *
 * @example
 * ```tsx
 * <CinemaStage aria-label="Technology trends">
 *   <StaticSceneRenderer scene={scenes[0]} />
 * </CinemaStage>
 * ```
 */
export function StaticSceneRenderer({
  scene,
}: StaticSceneRendererProps): ReactNode {
  return (
    <g aria-label={`Scene: ${scene.title}`} role="group">
      {scene.trends.map((trend) => (
        <StaticTrendLine key={trend.id} trend={trend} />
      ))}

      <g aria-label="Scene annotations" role="group">
        {scene.annotations.map((annotation, index) => (
          <StaticAnnotation
            key={`${scene.id}-annotation-${index}`}
            annotation={annotation}
            trends={scene.trends}
          />
        ))}
      </g>
    </g>
  );
}
