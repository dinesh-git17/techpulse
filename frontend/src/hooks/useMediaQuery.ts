"use client";

/**
 * @fileoverview Custom hook for responsive media query detection.
 *
 * Design rationale: Provides a React-friendly way to detect viewport
 * changes for components that need programmatic responsive behavior
 * (e.g., Recharts configuration that can't use CSS media queries).
 */
import { useSyncExternalStore } from "react";

/**
 * Detects whether the viewport matches a given media query.
 *
 * Returns false during SSR to prevent hydration mismatches.
 * Updates reactively when the viewport changes.
 *
 * @param query - CSS media query string (e.g., "(max-width: 600px)").
 * @returns True if the viewport matches the query, false otherwise.
 *
 * @example
 * ```tsx
 * const isMobile = useMediaQuery("(max-width: 600px)");
 * return isMobile ? <MobileView /> : <DesktopView />;
 * ```
 */
export function useMediaQuery(query: string): boolean {
  const subscribe = (callback: () => void): (() => void) => {
    const mediaQuery = window.matchMedia(query);
    mediaQuery.addEventListener("change", callback);
    return () => mediaQuery.removeEventListener("change", callback);
  };

  const getSnapshot = (): boolean => {
    return window.matchMedia(query).matches;
  };

  const getServerSnapshot = (): boolean => {
    return false;
  };

  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

/** Breakpoint for mobile chart adaptations (600px). */
export const MOBILE_CHART_BREAKPOINT = "(max-width: 599px)";

/** Breakpoint for tablet/mobile layout (768px). */
export const TABLET_BREAKPOINT = "(max-width: 767px)";
