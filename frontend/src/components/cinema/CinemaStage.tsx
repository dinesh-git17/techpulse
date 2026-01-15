/**
 * @fileoverview Cinema Stage SVG container for the visualization engine.
 *
 * Provides a responsive 2:1 aspect ratio SVG canvas that decouples normalized
 * data coordinates [0-1] from screen pixels. The viewBox coordinate system
 * ensures consistent rendering across all viewport sizes without layout shift.
 */

import { type ReactNode } from "react";

import { CINEMA_VIEWBOX_STRING } from "@/hooks/useScale";

/**
 * Props for the CinemaStage component.
 */
export interface CinemaStageProps {
  /** Child elements to render within the SVG coordinate space */
  children?: ReactNode;
  /** Additional CSS classes for the container wrapper */
  className?: string;
  /** Accessible label describing the visualization content */
  "aria-label"?: string;
}

/**
 * Responsive SVG container for cinematic data visualization.
 *
 * Renders a 2:1 ultrawide SVG canvas with a fixed viewBox coordinate system
 * (200x100 units). The container maintains aspect ratio via CSS, eliminating
 * layout shift during hydration or resize. Child components use normalized
 * [0-1] coordinates mapped through the useScale hook.
 *
 * @param props - Component configuration.
 * @returns SVG container element with coordinate system established.
 *
 * @example
 * ```tsx
 * import { CinemaStage } from "@/components/cinema";
 * import { useScale } from "@/hooks";
 *
 * function TrendVisualization() {
 *   const { scaleX, scaleY } = useScale();
 *
 *   return (
 *     <CinemaStage aria-label="Technology trend comparison">
 *       <circle cx={scaleX(0.5)} cy={scaleY(0.5)} r={4} />
 *     </CinemaStage>
 *   );
 * }
 * ```
 */
export function CinemaStage({
  children,
  className,
  "aria-label": ariaLabel,
}: CinemaStageProps): ReactNode {
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
        {children}
      </svg>
    </div>
  );
}
