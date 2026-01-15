/**
 * @fileoverview Static fallback SVG for Cinema visualization.
 *
 * Displays a branded placeholder when data loading fails or during
 * error states. Shows a generic upward trend pattern with TechPulse
 * styling to maintain visual consistency without real data.
 */

import { type ReactNode } from "react";

import { CINEMA_VIEWBOX_STRING } from "@/hooks/useScale";

/**
 * Props for the StaticFallback component.
 */
export interface StaticFallbackProps {
  /** Additional CSS classes for the container wrapper */
  className?: string;
  /** Accessible label describing the fallback state */
  "aria-label"?: string;
}

/**
 * Pre-defined path representing a generic growth trend.
 * Coordinates are in viewBox units (200x100).
 */
const FALLBACK_PATH = "M 0,75 L 40,65 L 80,70 L 120,50 L 160,40 L 200,25";

/**
 * Branded placeholder for Cinema data loading failures.
 *
 * Renders a static SVG showing a generic upward trend line with
 * subtle styling. Maintains the 2:1 aspect ratio and visual
 * language of the Cinema engine while indicating data unavailability.
 *
 * @param props - Component configuration.
 * @returns Static SVG element with branded fallback visualization.
 *
 * @example
 * ```tsx
 * if (dataError) {
 *   return <StaticFallback aria-label="Data temporarily unavailable" />;
 * }
 * ```
 */
export function StaticFallback({
  className,
  "aria-label": ariaLabel = "Trend visualization temporarily unavailable",
}: StaticFallbackProps): ReactNode {
  return (
    <div
      className={`relative w-full ${className ?? ""}`.trim()}
      style={{ aspectRatio: "2 / 1" }}
    >
      <svg
        viewBox={CINEMA_VIEWBOX_STRING}
        preserveAspectRatio="xMidYMid meet"
        className="absolute inset-0 h-full w-full"
        role="img"
        aria-label={ariaLabel}
      >
        <defs>
          <linearGradient
            id="fallback-gradient"
            x1="0%"
            y1="0%"
            x2="100%"
            y2="0%"
          >
            <stop
              offset="0%"
              stopColor="rgb(var(--tp-color-surface-tertiary))"
              stopOpacity="0.3"
            />
            <stop
              offset="100%"
              stopColor="rgb(var(--tp-color-surface-tertiary))"
              stopOpacity="0.6"
            />
          </linearGradient>
        </defs>

        <path
          d={FALLBACK_PATH}
          fill="none"
          stroke="url(#fallback-gradient)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray="6 4"
        />

        <text
          x="100"
          y="90"
          fill="rgb(var(--tp-color-text-tertiary))"
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="4"
          fontFamily="var(--font-sans)"
          fontWeight="400"
        >
          Data loading...
        </text>
      </svg>
    </div>
  );
}
