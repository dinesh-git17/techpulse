/**
 * @fileoverview Typography Token Configuration
 *
 * Canonical source of truth for TechPulse typography tokens.
 * Used for documentation, testing, and runtime validation.
 */

/**
 * Represents a type scale step with size and line-height.
 */
export interface TypeScaleStep {
  /** Token name (e.g., "micro-xs", "base") */
  name: string;
  /** CSS variable name for font-size */
  sizeVar: string;
  /** Font size in rem */
  sizeRem: string;
  /** Font size in px (approximate) */
  sizePx: number;
  /** Line height in rem or unitless */
  lineHeight: string;
  /** Tailwind utility class */
  tailwindClass: string;
  /** Recommended use case */
  useCase: string;
}

/**
 * Type scale tokens from micro to 5xl.
 * Optimized for data-dense analytical dashboards.
 */
export const TYPE_SCALE: readonly TypeScaleStep[] = [
  {
    name: "micro-xs",
    sizeVar: "--text-micro-xs",
    sizeRem: "0.6875rem",
    sizePx: 11,
    lineHeight: "1rem",
    tailwindClass: "text-micro-xs",
    useCase: "Extremely dense data tables, secondary metadata",
  },
  {
    name: "micro",
    sizeVar: "--text-micro",
    sizeRem: "0.75rem",
    sizePx: 12,
    lineHeight: "1.125rem",
    tailwindClass: "text-micro",
    useCase: "Dense data tables, timestamps, IDs",
  },
  {
    name: "xs",
    sizeVar: "--text-xs",
    sizeRem: "0.8125rem",
    sizePx: 13,
    lineHeight: "1.25rem",
    tailwindClass: "text-xs",
    useCase: "Captions, helper text, badges",
  },
  {
    name: "sm",
    sizeVar: "--text-sm",
    sizeRem: "0.875rem",
    sizePx: 14,
    lineHeight: "1.375rem",
    tailwindClass: "text-sm",
    useCase: "Secondary content, descriptions",
  },
  {
    name: "base",
    sizeVar: "--text-base",
    sizeRem: "1rem",
    sizePx: 16,
    lineHeight: "1.5rem",
    tailwindClass: "text-base",
    useCase: "Primary body text, default",
  },
  {
    name: "lg",
    sizeVar: "--text-lg",
    sizeRem: "1.125rem",
    sizePx: 18,
    lineHeight: "1.75rem",
    tailwindClass: "text-lg",
    useCase: "Emphasized body text, lead paragraphs",
  },
  {
    name: "xl",
    sizeVar: "--text-xl",
    sizeRem: "1.25rem",
    sizePx: 20,
    lineHeight: "1.75rem",
    tailwindClass: "text-xl",
    useCase: "Small headings, card titles",
  },
  {
    name: "2xl",
    sizeVar: "--text-2xl",
    sizeRem: "1.5rem",
    sizePx: 24,
    lineHeight: "2rem",
    tailwindClass: "text-2xl",
    useCase: "Section headings",
  },
  {
    name: "3xl",
    sizeVar: "--text-3xl",
    sizeRem: "1.875rem",
    sizePx: 30,
    lineHeight: "2.25rem",
    tailwindClass: "text-3xl",
    useCase: "Page headings",
  },
  {
    name: "4xl",
    sizeVar: "--text-4xl",
    sizeRem: "2.25rem",
    sizePx: 36,
    lineHeight: "2.5rem",
    tailwindClass: "text-4xl",
    useCase: "Large display headings",
  },
  {
    name: "5xl",
    sizeVar: "--text-5xl",
    sizeRem: "3rem",
    sizePx: 48,
    lineHeight: "1",
    tailwindClass: "text-5xl",
    useCase: "Hero headings, display text",
  },
] as const;

/**
 * Font stack configuration.
 */
export const FONT_STACKS = {
  sans: {
    name: "Geist Sans",
    cssVar: "--font-sans",
    tailwindClass: "font-sans",
    useCase: "UI labels, headings, body text",
  },
  mono: {
    name: "Geist Mono",
    cssVar: "--font-mono",
    tailwindClass: "font-mono",
    useCase: "IDs, hashes, code, numeric data, tabular figures",
  },
} as const;

/**
 * Font feature settings applied globally.
 */
export const FONT_FEATURES = {
  tnum: {
    feature: "tnum",
    description: "Tabular numbers — fixed-width digits for aligned columns",
  },
  zero: {
    feature: "zero",
    description: "Slashed zero — distinguishes 0 from O",
  },
  ss01: {
    feature: "ss01",
    description: "Stylistic set 01 — disambiguates 1/l/I in supported fonts",
  },
} as const;

/**
 * Array of all type scale names for iteration.
 */
export const TYPE_SCALE_NAMES = TYPE_SCALE.map((step) => step.name);

/**
 * Micro sizes (11px and 12px) specifically for dense data.
 */
export const MICRO_SIZES = TYPE_SCALE.filter(
  (step) => step.sizePx <= 12,
) as readonly TypeScaleStep[];

/**
 * Get a type scale step by name.
 *
 * @param name - The type scale name (e.g., "micro", "base").
 * @returns The type scale step or undefined if not found.
 */
export function getTypeScaleStep(name: string): TypeScaleStep | undefined {
  return TYPE_SCALE.find((step) => step.name === name);
}

/**
 * Get the Tailwind class for a type scale size.
 *
 * @param name - The type scale name.
 * @returns The Tailwind class or undefined if not found.
 */
export function getTextClassName(name: string): string | undefined {
  return getTypeScaleStep(name)?.tailwindClass;
}
