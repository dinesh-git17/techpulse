/**
 * @fileoverview Color Token Configuration
 *
 * Canonical source of truth for TechPulse color tokens.
 * Used for documentation, testing, and runtime validation.
 */

/**
 * Token categories and their semantic colors.
 * Each token maps to a --tp-color-* CSS variable.
 */
export const COLOR_TOKENS = {
  surface: [
    "surface-primary",
    "surface-secondary",
    "surface-tertiary",
    "surface-elevated",
    "surface-sunken",
  ],
  text: ["text-primary", "text-secondary", "text-muted", "text-inverted"],
  border: ["border-default", "border-muted", "border-strong", "border-glass"],
  action: ["action-primary", "action-primary-hover", "action-primary-active"],
  status: [
    "status-success",
    "status-success-muted",
    "status-warning",
    "status-warning-muted",
    "status-danger",
    "status-danger-muted",
  ],
  interactive: ["focus-ring", "highlight"],
} as const;

/**
 * Brand color scale from 50-950.
 */
export const BRAND_SCALE = [
  50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950,
] as const;

/**
 * All semantic color tokens flattened into a single array.
 */
export const ALL_SEMANTIC_TOKENS = Object.values(COLOR_TOKENS).flat();

/**
 * Expected CSS variable format: --tp-color-{token}
 */
export function getCssVarName(token: string): string {
  return `--tp-color-${token}`;
}

/**
 * Expected Tailwind class for background colors.
 */
export function getBgClassName(token: string): string {
  return `bg-${token}`;
}

/**
 * Expected Tailwind class for text colors.
 */
export function getTextClassName(token: string): string {
  return `text-${token}`;
}

/**
 * Expected Tailwind class for border colors.
 */
export function getBorderClassName(token: string): string {
  return `border-${token}`;
}
