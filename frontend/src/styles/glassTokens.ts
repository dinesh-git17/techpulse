/**
 * @fileoverview Glass Utility Token Configuration
 *
 * Canonical source of truth for TechPulse glass effect tokens.
 * Defines the three-tier glass scale for the "Glass Cockpit" aesthetic.
 * Used for documentation, testing, ESLint rules, and runtime validation.
 */

/**
 * Represents a glass tier in the visual system.
 */
export interface GlassTier {
  /** Semantic tier name */
  name: string;
  /** Tailwind utility class name */
  className: string;
  /** Backdrop blur value */
  blur: string;
  /** Background opacity percentage */
  opacity: number;
  /** Whether the tier includes a shimmer border */
  hasBorder: boolean;
  /** Recommended use case */
  useCase: string;
}

/**
 * Three-tier glass scale. Blur requires noise texture and border to define edges.
 */
export const GLASS_TIERS: readonly GlassTier[] = [
  {
    name: "subtle",
    className: "glass-subtle",
    blur: "backdrop-blur-sm",
    opacity: 90,
    hasBorder: false,
    useCase: "Sticky headers, lightweight frosted surfaces",
  },
  {
    name: "panel",
    className: "glass-panel",
    blur: "backdrop-blur-md",
    opacity: 80,
    hasBorder: true,
    useCase: "Dashboard widgets, cards, floating panels",
  },
  {
    name: "overlay",
    className: "glass-overlay",
    blur: "backdrop-blur-xl",
    opacity: 60,
    hasBorder: true,
    useCase: "Modals, dialogs, maximum translucency surfaces",
  },
] as const;

/**
 * Glass utility class names for validation and ESLint rules.
 */
export const GLASS_CLASS_NAMES = GLASS_TIERS.map(
  (tier) => tier.className,
) as readonly string[];

/**
 * Backdrop blur class names that constitute a "glass layer" for nesting detection.
 * Used by ESLint rule to detect blur violations.
 */
export const BLUR_CLASSES = [
  "backdrop-blur",
  "backdrop-blur-none",
  "backdrop-blur-sm",
  "backdrop-blur-md",
  "backdrop-blur-lg",
  "backdrop-blur-xl",
  "backdrop-blur-2xl",
  "backdrop-blur-3xl",
  ...GLASS_CLASS_NAMES,
] as const;

/**
 * Maximum allowed depth of nested glass/blur layers.
 * Exceeding this causes "muddy" visual effect and GPU performance issues.
 */
export const MAX_GLASS_NESTING_DEPTH = 2;

/**
 * Shimmer border configuration for glass panels.
 */
export const SHIMMER_BORDER = {
  width: "1px",
  cssVar: "--tp-color-border-glass",
  opacity: 0.1,
  tailwindClass: "border-border-glass/10",
} as const;

/**
 * Noise texture configuration for preventing color banding on glass surfaces.
 */
export const NOISE_TEXTURE = {
  className: "glass-noise",
  svgFilter: "fractalNoise",
  baseFrequency: 0.8,
  numOctaves: 4,
  opacity: 0.03,
} as const;

/**
 * Get a glass tier by name.
 *
 * @param name - The tier name (e.g., "subtle", "panel", "overlay").
 * @returns The glass tier or undefined if not found.
 */
export function getGlassTier(name: string): GlassTier | undefined {
  return GLASS_TIERS.find((tier) => tier.name === name);
}

/**
 * Get the Tailwind class for a glass tier.
 *
 * @param name - The tier name.
 * @returns The Tailwind class or undefined if not found.
 */
export function getGlassClassName(name: string): string | undefined {
  return getGlassTier(name)?.className;
}

/**
 * Check if a class name is a glass utility class.
 *
 * @param className - The class name to check.
 * @returns True if the class is a glass utility.
 */
export function isGlassClass(className: string): boolean {
  return GLASS_CLASS_NAMES.includes(className);
}

/**
 * Check if a class name applies backdrop blur (potential glass layer).
 *
 * @param className - The class name to check.
 * @returns True if the class applies backdrop blur.
 */
export function isBlurClass(className: string): boolean {
  return BLUR_CLASSES.includes(className as (typeof BLUR_CLASSES)[number]);
}

/**
 * Extract glass/blur class names from a className string.
 *
 * @param classNameString - Space-separated class names.
 * @returns Array of glass/blur classes found.
 */
export function extractBlurClasses(classNameString: string): string[] {
  return classNameString.split(/\s+/).filter((cls) => isBlurClass(cls));
}
