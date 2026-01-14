/**
 * @fileoverview Toast notification utilities.
 *
 * Provides typed wrapper functions around Sonner's toast API for
 * consistent messaging across the application. Uses Sonner's default
 * timing (4s standard, 6s errors) and accessibility settings.
 */

import { toast } from "sonner";

/**
 * Display a success toast notification.
 *
 * @param message - The message to display.
 *
 * @example
 * ```ts
 * showSuccessToast("Link copied to clipboard");
 * ```
 */
export function showSuccessToast(message: string): void {
  toast.success(message);
}

/**
 * Display an error toast notification.
 *
 * Uses Sonner's default 6-second duration for error messages.
 *
 * @param message - The error message to display.
 *
 * @example
 * ```ts
 * showErrorToast("Failed to refresh trend data");
 * ```
 */
export function showErrorToast(message: string): void {
  toast.error(message);
}

/**
 * Display an info toast notification.
 *
 * Used for non-critical information such as URL auto-corrections.
 *
 * @param message - The informational message to display.
 *
 * @example
 * ```ts
 * showInfoToast("Date range adjusted to valid period");
 * ```
 */
export function showInfoToast(message: string): void {
  toast.info(message);
}
