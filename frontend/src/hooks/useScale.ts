/**
 * @fileoverview Coordinate scaling hook for the Cinema visualization engine.
 *
 * Maps normalized domain [0-1] to SVG viewBox pixel coordinates, handling
 * the Y-axis inversion required for data visualization (where y=0 is bottom).
 */

/**
 * ViewBox dimensions for the Cinema Stage coordinate system.
 * 2:1 ultrawide aspect ratio optimized for time-series visualization.
 */
export const CINEMA_VIEWBOX = {
  /** Minimum X coordinate */
  minX: 0,
  /** Minimum Y coordinate */
  minY: 0,
  /** ViewBox width in SVG units */
  width: 200,
  /** ViewBox height in SVG units */
  height: 100,
} as const;

/**
 * Formatted viewBox string for SVG element attribute.
 */
export const CINEMA_VIEWBOX_STRING = `${CINEMA_VIEWBOX.minX} ${CINEMA_VIEWBOX.minY} ${CINEMA_VIEWBOX.width} ${CINEMA_VIEWBOX.height}`;

/**
 * Scale functions for coordinate transformation.
 */
export interface ScaleFunctions {
  /**
   * Map normalized X value [0-1] to viewBox X coordinate.
   *
   * @param normalizedX - Value between 0 (left) and 1 (right).
   * @returns X coordinate in viewBox units.
   */
  scaleX: (normalizedX: number) => number;

  /**
   * Map normalized Y value [0-1] to viewBox Y coordinate.
   * Handles Y-axis inversion: 0 maps to bottom, 1 maps to top.
   *
   * @param normalizedY - Value between 0 (bottom) and 1 (top).
   * @returns Y coordinate in viewBox units.
   */
  scaleY: (normalizedY: number) => number;

  /**
   * Map a normalized point to viewBox coordinates.
   *
   * @param point - Normalized point with x and y in [0-1] range.
   * @returns Point in viewBox coordinates.
   */
  scalePoint: (point: { x: number; y: number }) => { x: number; y: number };
}

/**
 * Return value from the useScale hook.
 */
export interface UseScaleResult extends ScaleFunctions {
  /** ViewBox width in SVG units */
  viewBoxWidth: number;
  /** ViewBox height in SVG units */
  viewBoxHeight: number;
  /** Formatted viewBox string for SVG attribute */
  viewBoxString: string;
}

/**
 * Map normalized domain [0-1] to Cinema Stage viewBox coordinates.
 *
 * This hook provides scale functions that transform normalized data points
 * (where both axes range from 0 to 1) into SVG viewBox pixel coordinates.
 * The Y-axis is inverted to match standard chart conventions where y=0
 * represents the bottom of the chart.
 *
 * @returns Scale functions and viewBox configuration.
 *
 * @example
 * ```tsx
 * const { scaleX, scaleY, scalePoint } = useScale();
 *
 * // Map individual coordinates
 * const pixelX = scaleX(0.5); // Returns 100 (center)
 * const pixelY = scaleY(0);   // Returns 100 (bottom)
 *
 * // Map a data point
 * const point = scalePoint({ x: 0, y: 1 }); // Returns { x: 0, y: 0 } (top-left)
 * ```
 */
export function useScale(): UseScaleResult {
  const scaleX = (normalizedX: number): number => {
    return normalizedX * CINEMA_VIEWBOX.width;
  };

  const scaleY = (normalizedY: number): number => {
    // Invert Y-axis: normalized 0 (bottom) → viewBox height, normalized 1 (top) → 0
    return CINEMA_VIEWBOX.height - normalizedY * CINEMA_VIEWBOX.height;
  };

  const scalePoint = (point: {
    x: number;
    y: number;
  }): { x: number; y: number } => {
    return {
      x: scaleX(point.x),
      y: scaleY(point.y),
    };
  };

  return {
    scaleX,
    scaleY,
    scalePoint,
    viewBoxWidth: CINEMA_VIEWBOX.width,
    viewBoxHeight: CINEMA_VIEWBOX.height,
    viewBoxString: CINEMA_VIEWBOX_STRING,
  };
}
