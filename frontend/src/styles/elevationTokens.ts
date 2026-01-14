/**
 * @fileoverview Elevation Token Configuration
 *
 * Canonical source of truth for TechPulse z-index and elevation tokens.
 * Used for documentation, testing, and runtime validation.
 */

/**
 * Represents a z-index layer in the elevation system.
 */
export interface ElevationLayer {
  /** Semantic layer name */
  name: string;
  /** Z-index value */
  value: number;
  /** CSS variable name */
  cssVar: string;
  /** Tailwind utility class */
  tailwindClass: string;
  /** Recommended use case */
  useCase: string;
}

/**
 * Semantic z-index scale. Exactly 6 named layers.
 * Arbitrary z-indices are prohibited in the codebase.
 */
export const ELEVATION_LAYERS: readonly ElevationLayer[] = [
  {
    name: "base",
    value: 0,
    cssVar: "--z-base",
    tailwindClass: "z-base",
    useCase: "Default content, static elements",
  },
  {
    name: "raised",
    value: 10,
    cssVar: "--z-raised",
    tailwindClass: "z-raised",
    useCase: "Cards, elevated surfaces, interactive elements",
  },
  {
    name: "sticky",
    value: 100,
    cssVar: "--z-sticky",
    tailwindClass: "z-sticky",
    useCase: "Sticky headers, toolbars, fixed navigation",
  },
  {
    name: "overlay",
    value: 200,
    cssVar: "--z-overlay",
    tailwindClass: "z-overlay",
    useCase: "Dropdowns, popovers, menus",
  },
  {
    name: "modal",
    value: 300,
    cssVar: "--z-modal",
    tailwindClass: "z-modal",
    useCase: "Modal dialogs, dialog backdrops",
  },
  {
    name: "toast",
    value: 400,
    cssVar: "--z-toast",
    tailwindClass: "z-toast",
    useCase: "Toast notifications, alerts",
  },
] as const;

/**
 * Default Tailwind z-index utilities that are disabled.
 * These should NOT be used in the codebase.
 */
export const DISABLED_Z_INDEX_UTILITIES = [
  "z-0",
  "z-10",
  "z-20",
  "z-30",
  "z-40",
  "z-50",
  "z-auto",
] as const;

/**
 * Array of all semantic layer names.
 */
export const ELEVATION_LAYER_NAMES = ELEVATION_LAYERS.map(
  (layer) => layer.name,
);

/**
 * Array of all valid z-index Tailwind classes.
 */
export const VALID_Z_INDEX_CLASSES = ELEVATION_LAYERS.map(
  (layer) => layer.tailwindClass,
);

/**
 * Portal configuration for elements that bypass the main stacking context.
 */
export const PORTAL_CONFIG = {
  tooltip: {
    description:
      "Tooltips render via React portals into document.body, bypassing the main stack",
    zIndex: 9999,
    strategy: "createPortal to document.body with inline z-index",
  },
} as const;

/**
 * Stacking context utility class name.
 */
export const STACKING_CONTEXT_CLASS = "stacking-context";

/**
 * Get an elevation layer by name.
 *
 * @param name - The layer name (e.g., "sticky", "modal").
 * @returns The elevation layer or undefined if not found.
 */
export function getElevationLayer(name: string): ElevationLayer | undefined {
  return ELEVATION_LAYERS.find((layer) => layer.name === name);
}

/**
 * Get the Tailwind z-index class for a layer.
 *
 * @param name - The layer name.
 * @returns The Tailwind class or undefined if not found.
 */
export function getZIndexClass(name: string): string | undefined {
  return getElevationLayer(name)?.tailwindClass;
}

/**
 * Get the z-index value for a layer.
 *
 * @param name - The layer name.
 * @returns The z-index value or undefined if not found.
 */
export function getZIndexValue(name: string): number | undefined {
  return getElevationLayer(name)?.value;
}

/**
 * Check if a z-index class is valid (part of the semantic scale).
 *
 * @param className - The class name to validate.
 * @returns True if the class is a valid semantic z-index class.
 */
export function isValidZIndexClass(className: string): boolean {
  return VALID_Z_INDEX_CLASSES.includes(
    className as (typeof VALID_Z_INDEX_CLASSES)[number],
  );
}

/**
 * Check if a z-index class is a disabled default utility.
 *
 * @param className - The class name to check.
 * @returns True if the class is a disabled default utility.
 */
export function isDisabledZIndexClass(className: string): boolean {
  return DISABLED_Z_INDEX_UTILITIES.includes(
    className as (typeof DISABLED_Z_INDEX_UTILITIES)[number],
  );
}
