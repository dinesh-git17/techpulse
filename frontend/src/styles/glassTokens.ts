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

/* ═══════════════════════════════════════════════════════════════════════════
 * ACCESSIBILITY CONFIGURATION
 *
 * Defines fallback behavior and contrast requirements for glass surfaces.
 * WCAG AA requires 4.5:1 for normal text, 3:1 for large text (≥18pt/14pt bold).
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * Media query names for accessibility fallback modes.
 */
export const A11Y_MEDIA_QUERIES = {
  reducedTransparency: "prefers-reduced-transparency: reduce",
  forcedColors: "forced-colors: active",
} as const;

/**
 * Fallback background color for each glass tier in reduced transparency mode.
 * Maps to solid semantic surface colors.
 */
export const REDUCED_TRANSPARENCY_FALLBACKS = {
  subtle: "--tp-color-surface-secondary",
  panel: "--tp-color-surface-tertiary",
  overlay: "--tp-color-surface-elevated",
} as const;

/**
 * System color keywords used in forced-colors mode.
 * These are CSS system color keywords that adapt to Windows High Contrast themes.
 */
export const FORCED_COLORS = {
  background: "Canvas",
  text: "CanvasText",
  border: "CanvasText",
} as const;

/**
 * Represents a contrast ratio measurement for text on a glass surface.
 */
export interface GlassContrastRatio {
  /** Glass tier name */
  tier: string;
  /** Text color token */
  textToken: string;
  /** Calculated contrast ratio */
  ratio: number;
  /** Whether it meets WCAG AA for normal text (4.5:1) */
  meetsAA: boolean;
  /** Whether it meets WCAG AAA for normal text (7:1) */
  meetsAAA: boolean;
}

/**
 * Pre-calculated contrast ratios for text on glass surfaces in dark mode.
 * Background: surface-primary at specified opacity over pure black (#000).
 * Text: text-primary (#E6EDF3 / rgb(230, 237, 243))
 *
 * Methodology:
 * 1. Glass background = blend(surface-primary @ opacity, black background)
 * 2. Contrast ratio = (L1 + 0.05) / (L2 + 0.05) where L1, L2 are relative luminance
 *
 * These values assume worst-case (pure black background behind glass).
 */
export const GLASS_CONTRAST_RATIOS: readonly GlassContrastRatio[] = [
  {
    tier: "subtle",
    textToken: "text-primary",
    ratio: 11.2,
    meetsAA: true,
    meetsAAA: true,
  },
  {
    tier: "panel",
    textToken: "text-primary",
    ratio: 10.1,
    meetsAA: true,
    meetsAAA: true,
  },
  {
    tier: "overlay",
    textToken: "text-primary",
    ratio: 7.8,
    meetsAA: true,
    meetsAAA: true,
  },
  {
    tier: "subtle",
    textToken: "text-secondary",
    ratio: 5.1,
    meetsAA: true,
    meetsAAA: false,
  },
  {
    tier: "panel",
    textToken: "text-secondary",
    ratio: 4.6,
    meetsAA: true,
    meetsAAA: false,
  },
  {
    tier: "overlay",
    textToken: "text-secondary",
    ratio: 3.5,
    meetsAA: false,
    meetsAAA: false,
  },
  {
    tier: "subtle",
    textToken: "text-muted",
    ratio: 4.0,
    meetsAA: false,
    meetsAAA: false,
  },
  {
    tier: "panel",
    textToken: "text-muted",
    ratio: 3.6,
    meetsAA: false,
    meetsAAA: false,
  },
  {
    tier: "overlay",
    textToken: "text-muted",
    ratio: 2.8,
    meetsAA: false,
    meetsAAA: false,
  },
] as const;

/**
 * WCAG contrast ratio thresholds.
 */
export const WCAG_CONTRAST_THRESHOLDS = {
  AA_NORMAL: 4.5,
  AA_LARGE: 3.0,
  AAA_NORMAL: 7.0,
  AAA_LARGE: 4.5,
} as const;

/**
 * Get contrast ratio data for a specific glass tier and text color.
 *
 * @param tier - The glass tier name.
 * @param textToken - The text color token name.
 * @returns The contrast ratio data or undefined if not found.
 */
export function getGlassContrastRatio(
  tier: string,
  textToken: string,
): GlassContrastRatio | undefined {
  return GLASS_CONTRAST_RATIOS.find(
    (ratio) => ratio.tier === tier && ratio.textToken === textToken,
  );
}

/**
 * Get all contrast ratios for a specific glass tier.
 *
 * @param tier - The glass tier name.
 * @returns Array of contrast ratio data for the tier.
 */
export function getContrastRatiosForTier(tier: string): GlassContrastRatio[] {
  return GLASS_CONTRAST_RATIOS.filter((ratio) => ratio.tier === tier);
}

/**
 * Check if a contrast ratio meets WCAG AA for normal text.
 *
 * @param ratio - The contrast ratio value.
 * @returns True if the ratio meets WCAG AA (4.5:1).
 */
export function meetsWCAG_AA(ratio: number): boolean {
  return ratio >= WCAG_CONTRAST_THRESHOLDS.AA_NORMAL;
}

/**
 * Check if a contrast ratio meets WCAG AA for large text.
 *
 * @param ratio - The contrast ratio value.
 * @returns True if the ratio meets WCAG AA for large text (3:1).
 */
export function meetsWCAG_AA_Large(ratio: number): boolean {
  return ratio >= WCAG_CONTRAST_THRESHOLDS.AA_LARGE;
}
