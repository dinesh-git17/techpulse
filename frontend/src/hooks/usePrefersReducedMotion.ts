"use client";

/**
 * @fileoverview Hook for detecting user preference for reduced motion.
 *
 * Provides a React-friendly way to respect the prefers-reduced-motion
 * media query for accessibility compliance (WCAG 2.3.3). Returns false
 * during SSR to prevent hydration mismatches.
 */

import { useSyncExternalStore } from "react";

/**
 * CSS media query string for reduced motion preference.
 */
export const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";

/**
 * Detect if the user prefers reduced motion.
 *
 * Returns false during SSR to ensure consistent hydration. Updates
 * reactively when system preferences change. When true, animations
 * should be disabled or minimized to respect user accessibility needs.
 *
 * @returns True if user prefers reduced motion, false otherwise.
 *
 * @example
 * ```tsx
 * const prefersReducedMotion = usePrefersReducedMotion();
 *
 * return prefersReducedMotion
 *   ? <StaticChart data={data} />
 *   : <AnimatedChart data={data} />;
 * ```
 */
export function usePrefersReducedMotion(): boolean {
  const subscribe = (callback: () => void): (() => void) => {
    const mediaQuery = window.matchMedia(REDUCED_MOTION_QUERY);
    mediaQuery.addEventListener("change", callback);
    return () => mediaQuery.removeEventListener("change", callback);
  };

  const getSnapshot = (): boolean => {
    return window.matchMedia(REDUCED_MOTION_QUERY).matches;
  };

  const getServerSnapshot = (): boolean => {
    return false;
  };

  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
