/**
 * @fileoverview Cinema visualization engine exports.
 *
 * Cinematic SVG renderer for the landing page Hero section, providing
 * motion-first data storytelling with auto-playing narrative sequences.
 */

export { Cinema, type CinemaProps } from "./Cinema";

export { CinemaStage, type CinemaStageProps } from "./CinemaStage";

export { TrendLine, SPRING_CONFIG, type TrendLineProps } from "./TrendLine";

export { Annotation, type AnnotationProps } from "./Annotation";

export { AnnotationLayer, type AnnotationLayerProps } from "./AnnotationLayer";

export {
  StaticSceneRenderer,
  type StaticSceneRendererProps,
} from "./StaticSceneRenderer";

export { StaticFallback, type StaticFallbackProps } from "./StaticFallback";

export type {
  NormalizedPoint,
  TrendPath,
  CinemaAnnotation,
  CinemaScene,
} from "./types";
