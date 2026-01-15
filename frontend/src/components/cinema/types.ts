/**
 * @fileoverview Type definitions for the Cinema visualization engine.
 *
 * Defines the data schemas for trend visualization including path data,
 * annotations, and scene configuration. These interfaces are consumed
 * by the rendering components and Director state machine.
 */

/**
 * Normalized point in the [0-1] coordinate space.
 * Both x and y values must be between 0 and 1 inclusive.
 */
export interface NormalizedPoint {
  /** Horizontal position: 0 = left edge, 1 = right edge */
  x: number;
  /** Vertical position: 0 = bottom, 1 = top */
  y: number;
}

/**
 * A single trend line dataset for visualization.
 *
 * Represents one technology or metric's time-series data normalized
 * to the [0-1] coordinate space for rendering within the Cinema Stage.
 */
export interface TrendPath {
  /** Unique identifier for morphing continuity across scene transitions */
  id: string;
  /** Display label for the trend (e.g., "Rust", "Python") */
  label: string;
  /** Semantic color token from Glass Design System (e.g., "action-primary") */
  colorToken: string;
  /** Normalized data points with x and y in [0-1] range */
  points: NormalizedPoint[];
}

/**
 * Text annotation synchronized to scene playback.
 *
 * Annotations appear at specific positions and timing relative to
 * the scene start, providing narrative context for the visualization.
 */
export interface CinemaAnnotation {
  /** Text content to display */
  text: string;
  /** Normalized position anchor in [0-1] coordinate space */
  anchor: NormalizedPoint;
  /** Delay from scene start before annotation appears (ms) */
  enterDelay: number;
  /** Duration the annotation remains visible (ms) */
  duration: number;
}

/**
 * A complete scene in the cinematic narrative sequence.
 *
 * Scenes define what data is displayed and for how long, forming
 * the playlist that the Director cycles through automatically.
 */
export interface CinemaScene {
  /** Unique scene identifier */
  id: string;
  /** Narrative title (e.g., "The Overtake", "10-Year Growth") */
  title: string;
  /** Scene display duration before transitioning (ms) */
  duration: number;
  /** Morph transition duration to next scene (ms) */
  morphDuration: number;
  /** 1-2 trend lines to render in this scene */
  trends: [TrendPath] | [TrendPath, TrendPath];
  /** Synchronized text annotations for narrative context */
  annotations: CinemaAnnotation[];
}
