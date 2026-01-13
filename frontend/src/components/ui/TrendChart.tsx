"use client";

/**
 * @fileoverview Multi-line trend chart with four-state handling.
 *
 * Design rationale: Wraps Recharts primitives with explicit state handling
 * for Loading, Error, Empty, and Success states. Includes a visually hidden
 * HTML table for screen reader accessibility. Uses fixed aspect ratio
 * container to prevent layout shift during loading.
 *
 * Responsive behavior: On viewports < 600px, the Legend is hidden and
 * axis tick counts are reduced for better mobile readability.
 */
import { type ReactNode, useMemo } from "react";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { MOBILE_CHART_BREAKPOINT, useMediaQuery } from "@/hooks";

/**
 * A single data point in the time series (pivoted format).
 * The `date` field is required; all other keys are technology values.
 */
export interface TimeSeriesPoint {
  /** ISO 8601 date string (YYYY-MM-DD). */
  date: string;
  /** Dynamic keys mapping technology IDs to their numeric values. */
  [technologyId: string]: number | string;
}

/**
 * Configuration for a single data series in the chart.
 */
export interface SeriesConfig {
  /** Unique key matching a property in TimeSeriesPoint. */
  key: string;
  /** Display color for the line (CSS color value). */
  color: string;
  /** Human-readable name for the legend. */
  name: string;
}

/**
 * Props for the TrendChart component.
 */
export interface TrendChartProps {
  /** Array of time series data points in pivoted format. */
  data: TimeSeriesPoint[];

  /** Configuration for each data series to render. */
  series: SeriesConfig[];

  /** Shows skeleton loading state when true. */
  isLoading?: boolean;

  /** Error message to display; shows error state when non-null. */
  error?: string | null;

  /** Shows empty state when true. */
  isEmpty?: boolean;

  /** Callback when user clicks retry in error state. */
  onRetry?: () => void;
}

/** Aspect ratio for the chart container (width:height). */
const ASPECT_RATIO = 16 / 9;

/**
 * Formats an ISO date string for display in tooltips.
 */
function formatDateForDisplay(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/**
 * Formats an ISO date string for axis display.
 */
function formatDateForAxis(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

/**
 * Renders a loading skeleton with pulse animation.
 */
function LoadingSkeleton(): ReactNode {
  return (
    <div
      className="
        h-full
        w-full
        animate-pulse
        rounded-md
        bg-[var(--bg-secondary)]
      "
      role="status"
      aria-label="Loading chart data"
    >
      <span className="sr-only">Loading chart data...</span>
    </div>
  );
}

/**
 * Props for the ErrorState component.
 */
interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

/**
 * Renders an error state with message and optional retry button.
 */
function ErrorState({ message, onRetry }: ErrorStateProps): ReactNode {
  return (
    <div
      className="
        flex
        h-full
        w-full
        flex-col
        items-center
        justify-center
        gap-4
        rounded-md
        border
        border-[var(--accent-danger)]/30
        bg-[var(--accent-danger)]/5
        p-6
      "
      role="alert"
    >
      <svg
        className="h-10 w-10 text-[var(--accent-danger)]"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
      <p className="text-center text-sm text-[var(--text-primary)]">
        {message}
      </p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="
            rounded-md
            bg-[var(--accent-primary)]
            px-4
            py-2
            text-sm
            font-medium
            text-white
            transition-colors
            hover:bg-[var(--accent-primary)]/90
            focus:outline
            focus:outline-2
            focus:outline-offset-2
            focus:outline-[var(--accent-primary)]
          "
        >
          Retry
        </button>
      )}
    </div>
  );
}

/**
 * Renders an empty state when no data is available.
 */
function EmptyState(): ReactNode {
  return (
    <div
      className="
        flex
        h-full
        w-full
        flex-col
        items-center
        justify-center
        gap-3
        rounded-md
        border
        border-[var(--border-default)]
        bg-[var(--bg-secondary)]
        p-6
      "
    >
      <svg
        className="h-10 w-10 text-[var(--text-muted)]"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
      <p className="text-center text-sm text-[var(--text-muted)]">
        No data found for this range
      </p>
    </div>
  );
}

/**
 * Props for the accessible data table.
 */
interface AccessibleTableProps {
  data: TimeSeriesPoint[];
  series: SeriesConfig[];
}

/**
 * Renders a visually hidden HTML table for screen reader accessibility.
 */
function AccessibleTable({ data, series }: AccessibleTableProps): ReactNode {
  if (data.length === 0 || series.length === 0) return null;

  return (
    <table className="sr-only" aria-label="Trend data table">
      <caption>Technology trend data over time</caption>
      <thead>
        <tr>
          <th scope="col">Date</th>
          {series.map((s) => (
            <th key={s.key} scope="col">
              {s.name}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((point) => (
          <tr key={point.date}>
            <td>{formatDateForDisplay(point.date)}</td>
            {series.map((s) => (
              <td key={s.key}>{point[s.key] ?? "N/A"}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/**
 * Custom tooltip content component for Recharts.
 */
interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  label?: string;
}

/**
 * Renders a custom tooltip with formatted date and values.
 */
function CustomTooltip({
  active,
  payload,
  label,
}: CustomTooltipProps): ReactNode {
  if (!active || !payload || !label) return null;

  return (
    <div
      className="
        rounded-md
        border
        border-[var(--border-default)]
        bg-[var(--bg-primary)]
        p-3
        shadow-lg
      "
    >
      <p className="mb-2 text-sm font-medium text-[var(--text-primary)]">
        {formatDateForDisplay(label)}
      </p>
      <ul className="space-y-1">
        {payload.map((entry) => (
          <li
            key={entry.name}
            className="flex items-center gap-2 text-sm text-[var(--text-secondary)]"
          >
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: entry.color }}
              aria-hidden="true"
            />
            <span>{entry.name}:</span>
            <span className="font-medium text-[var(--text-primary)]">
              {entry.value.toLocaleString()}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * Renders a multi-line trend chart with explicit state handling.
 *
 * Handles four states: Loading (skeleton), Error (with retry), Empty
 * (no data message), and Success (actual chart). Includes a visually
 * hidden HTML table for screen reader accessibility.
 *
 * @param props.data - Time series data in pivoted format.
 * @param props.series - Configuration for each line series.
 * @param props.isLoading - Shows loading skeleton when true.
 * @param props.error - Shows error state with this message when non-null.
 * @param props.isEmpty - Shows empty state when true.
 * @param props.onRetry - Callback for retry button in error state.
 *
 * @example
 * ```tsx
 * <TrendChart
 *   data={[
 *     { date: "2024-01-01", python: 150, typescript: 120 },
 *     { date: "2024-01-02", python: 160, typescript: 125 },
 *   ]}
 *   series={[
 *     { key: "python", color: "#3776ab", name: "Python" },
 *     { key: "typescript", color: "#3178c6", name: "TypeScript" },
 *   ]}
 * />
 * ```
 */
export function TrendChart({
  data,
  series,
  isLoading = false,
  error = null,
  isEmpty = false,
  onRetry,
}: TrendChartProps): ReactNode {
  const isMobileViewport = useMediaQuery(MOBILE_CHART_BREAKPOINT);

  // Memoize the chart content to prevent unnecessary re-renders
  const chartContent = useMemo(() => {
    if (isLoading) {
      return <LoadingSkeleton />;
    }

    if (error) {
      return <ErrorState message={error} onRetry={onRetry} />;
    }

    if (isEmpty || data.length === 0) {
      return <EmptyState />;
    }

    // Responsive chart configuration (inside useMemo to avoid dependency issues)
    const chartMargin = isMobileViewport
      ? { top: 5, right: 10, left: 0, bottom: 5 }
      : { top: 5, right: 30, left: 20, bottom: 5 };
    const xAxisTickCount = isMobileViewport ? 4 : undefined;
    const yAxisTickCount = isMobileViewport ? 5 : undefined;

    return (
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={chartMargin}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--border-muted)"
            vertical={false}
          />
          <XAxis
            dataKey="date"
            tickFormatter={formatDateForAxis}
            stroke="var(--text-muted)"
            fontSize={isMobileViewport ? 10 : 12}
            tickLine={false}
            axisLine={{ stroke: "var(--border-default)" }}
            tickCount={xAxisTickCount}
            interval="preserveStartEnd"
          />
          <YAxis
            stroke="var(--text-muted)"
            fontSize={isMobileViewport ? 10 : 12}
            tickLine={false}
            axisLine={{ stroke: "var(--border-default)" }}
            tickFormatter={(value: number) =>
              isMobileViewport
                ? value >= 1000
                  ? `${(value / 1000).toFixed(0)}k`
                  : value.toString()
                : value.toLocaleString()
            }
            tickCount={yAxisTickCount}
            width={isMobileViewport ? 35 : 60}
          />
          <Tooltip content={<CustomTooltip />} />
          {!isMobileViewport && (
            <Legend
              wrapperStyle={{ paddingTop: 16 }}
              iconType="circle"
              iconSize={8}
            />
          )}
          {series.map((s) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }, [data, series, isLoading, error, isEmpty, onRetry, isMobileViewport]);

  return (
    <div className="w-full">
      {/* Fixed aspect ratio container prevents layout shift */}
      <div
        className="relative w-full"
        style={{ paddingBottom: `${(1 / ASPECT_RATIO) * 100}%` }}
      >
        <div className="absolute inset-0">{chartContent}</div>
      </div>

      {/* Visually hidden table for screen readers */}
      {!isLoading && !error && !isEmpty && data.length > 0 && (
        <AccessibleTable data={data} series={series} />
      )}
    </div>
  );
}
