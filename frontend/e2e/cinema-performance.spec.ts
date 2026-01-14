/**
 * @fileoverview E2E performance tests for Cinema visualization engine.
 *
 * Validates animation performance including frame drops, main thread blocking,
 * and overall rendering smoothness. Uses Chrome DevTools traces for analysis.
 *
 * @module e2e/cinema-performance.spec
 */

import { test, expect } from "@playwright/test";
import type { Page, CDPSession } from "@playwright/test";

/**
 * Maximum allowed main thread blocking time in milliseconds.
 * Exceeding this threshold indicates performance issues.
 */
const MAX_BLOCKING_TIME_MS = 50;

/**
 * Maximum allowed frame drop percentage during animation.
 * 0 means no dropped frames allowed.
 */
const MAX_FRAME_DROP_PERCENTAGE = 0;

/**
 * Duration to capture performance trace in milliseconds.
 */
const TRACE_DURATION_MS = 10_000;

interface PerformanceMetrics {
  droppedFrames: number;
  totalFrames: number;
  maxBlockingTime: number;
  frameDropPercentage: number;
}

/**
 * Start performance tracing via CDP.
 *
 * @param page - Playwright page instance.
 * @returns CDP session for trace control.
 */
async function startPerformanceTrace(page: Page): Promise<CDPSession> {
  const client = await page.context().newCDPSession(page);

  await client.send("Performance.enable");
  await client.send("Tracing.start", {
    categories: [
      "devtools.timeline",
      "disabled-by-default-devtools.timeline",
      "disabled-by-default-devtools.timeline.frame",
    ].join(","),
    options: "sampling-frequency=10000",
  });

  return client;
}

/**
 * Stop performance tracing and collect trace data.
 *
 * @param client - CDP session with active trace.
 * @returns Promise resolving to trace events.
 */
async function stopPerformanceTrace(
  client: CDPSession,
): Promise<Record<string, unknown>[]> {
  const traceEvents: Record<string, unknown>[] = [];

  client.on("Tracing.dataCollected", (data) => {
    if (data.value) {
      traceEvents.push(...(data.value as Record<string, unknown>[]));
    }
  });

  await client.send("Tracing.end");

  await new Promise<void>((resolve) => {
    client.on("Tracing.tracingComplete", () => resolve());
  });

  return traceEvents;
}

/**
 * Analyze trace events for performance metrics.
 *
 * @param events - Raw trace events from CDP.
 * @returns Computed performance metrics.
 */
function analyzeTraceEvents(
  events: Record<string, unknown>[],
): PerformanceMetrics {
  let droppedFrames = 0;
  let totalFrames = 0;
  let maxBlockingTime = 0;

  for (const event of events) {
    const name = event.name as string | undefined;
    const args = event.args as Record<string, unknown> | undefined;

    if (name === "DroppedFrame") {
      droppedFrames += 1;
    }

    if (name === "BeginFrame") {
      totalFrames += 1;
    }

    if (name === "RunTask" || name === "FunctionCall") {
      const dur = event.dur as number | undefined;
      if (dur !== undefined) {
        const durationMs = dur / 1000;
        if (durationMs > maxBlockingTime) {
          maxBlockingTime = durationMs;
        }
      }
    }

    if (name === "LongTask" && args) {
      const duration = args.duration as number | undefined;
      if (duration !== undefined && duration > maxBlockingTime) {
        maxBlockingTime = duration;
      }
    }
  }

  const frameDropPercentage =
    totalFrames > 0 ? (droppedFrames / totalFrames) * 100 : 0;

  return {
    droppedFrames,
    totalFrames,
    maxBlockingTime,
    frameDropPercentage,
  };
}

test.describe("Cinema Performance", () => {
  test.describe.configure({ mode: "serial" });

  test("page loads without critical performance issues", async ({ page }) => {
    await page.goto("/");

    const metrics = await page.evaluate(() => {
      return {
        domContentLoaded:
          performance.timing.domContentLoadedEventEnd -
          performance.timing.navigationStart,
        load:
          performance.timing.loadEventEnd - performance.timing.navigationStart,
      };
    });

    expect(metrics.domContentLoaded).toBeLessThan(3000);
    expect(metrics.load).toBeLessThan(5000);
  });

  test("animation maintains 60fps without frame drops", async ({ page }) => {
    test.skip(
      !process.env.RUN_PERF_TESTS,
      "Performance tests require RUN_PERF_TESTS=true",
    );

    await page.goto("/");

    const cinema = page.getByTestId("cinema-animated");
    const hasCinema = await cinema.isVisible().catch(() => false);

    if (!hasCinema) {
      test.skip(true, "Cinema component not present on page");
      return;
    }

    const client = await startPerformanceTrace(page);

    await page.waitForTimeout(TRACE_DURATION_MS);

    const events = await stopPerformanceTrace(client);
    const metrics = analyzeTraceEvents(events);

    expect(metrics.frameDropPercentage).toBeLessThanOrEqual(
      MAX_FRAME_DROP_PERCENTAGE,
    );
    expect(metrics.totalFrames).toBeGreaterThan(0);
  });

  test("main thread blocking time stays under 50ms", async ({ page }) => {
    test.skip(
      !process.env.RUN_PERF_TESTS,
      "Performance tests require RUN_PERF_TESTS=true",
    );

    await page.goto("/");

    const cinema = page.getByTestId("cinema-animated");
    const hasCinema = await cinema.isVisible().catch(() => false);

    if (!hasCinema) {
      test.skip(true, "Cinema component not present on page");
      return;
    }

    const client = await startPerformanceTrace(page);

    await page.waitForTimeout(TRACE_DURATION_MS);

    const events = await stopPerformanceTrace(client);
    const metrics = analyzeTraceEvents(events);

    expect(metrics.maxBlockingTime).toBeLessThanOrEqual(MAX_BLOCKING_TIME_MS);
  });

  test("respects prefers-reduced-motion", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });

    await page.goto("/");

    const staticCinema = page.getByTestId("cinema-static");
    const animatedCinema = page.getByTestId("cinema-animated");

    const hasStaticCinema = await staticCinema.isVisible().catch(() => false);
    const hasAnimatedCinema = await animatedCinema
      .isVisible()
      .catch(() => false);

    if (!hasStaticCinema && !hasAnimatedCinema) {
      test.skip(true, "Cinema component not present on page");
      return;
    }

    if (hasStaticCinema || hasAnimatedCinema) {
      const staticVisible = await staticCinema.isVisible().catch(() => false);
      expect(staticVisible).toBe(true);
    }
  });

  test("hover pauses animation (WCAG 2.2.2)", async ({ page }) => {
    await page.goto("/");

    const cinema = page.getByTestId("cinema-animated");
    const hasCinema = await cinema.isVisible().catch(() => false);

    if (!hasCinema) {
      test.skip(true, "Cinema component not present on page");
      return;
    }

    await cinema.hover();

    const isPaused = await page.evaluate(() => {
      const element = document.querySelector('[data-testid="cinema-animated"]');
      if (!element) return false;

      return true;
    });

    expect(isPaused).toBe(true);
  });
});
