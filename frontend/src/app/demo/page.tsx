"use client";

/**
 * @fileoverview Demo page for component integration verification.
 *
 * This page demonstrates the composition model for the dashboard UI
 * components. It serves as both visual documentation and an integration
 * test for the DashboardShell, TechnologySelector, DateRangePicker,
 * and TrendChart components.
 *
 * Development only - not deployed to production.
 */
import { useCallback, useMemo, useState } from "react";

import { DashboardShell } from "@/components/layouts";
import {
  DateRangePicker,
  TechnologySelector,
  TrendChart,
  type DateRange,
  type SeriesConfig,
  type TimeSeriesPoint,
} from "@/components/ui";

/**
 * Available technology options for the demo.
 */
const DEMO_TECHNOLOGIES = [
  { id: "python", name: "Python" },
  { id: "typescript", name: "TypeScript" },
  { id: "rust", name: "Rust" },
  { id: "go", name: "Go" },
  { id: "java", name: "Java" },
  { id: "csharp", name: "C#" },
  { id: "kotlin", name: "Kotlin" },
  { id: "swift", name: "Swift" },
  { id: "ruby", name: "Ruby" },
  { id: "php", name: "PHP" },
  { id: "scala", name: "Scala" },
  { id: "elixir", name: "Elixir" },
] as const;

/**
 * Color palette for chart series (colorblind-friendly).
 */
const SERIES_COLORS: Record<string, string> = {
  python: "#3776ab",
  typescript: "#3178c6",
  rust: "#dea584",
  go: "#00add8",
  java: "#ed8b00",
  csharp: "#512bd4",
  kotlin: "#7f52ff",
  swift: "#f05138",
  ruby: "#cc342d",
  php: "#777bb4",
  scala: "#dc322f",
  elixir: "#6e4a7e",
};

/**
 * Chart display state options.
 */
type ChartState = "success" | "loading" | "error" | "empty";

/**
 * Formats a date as ISO date string (YYYY-MM-DD) in local timezone.
 */
function formatLocalDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/**
 * Generates dummy time series data for selected technologies.
 */
function generateDummyData(
  selectedIds: string[],
  startDate: string,
  endDate: string,
): TimeSeriesPoint[] {
  if (selectedIds.length === 0) return [];

  const [startYear, startMonth, startDay] = startDate.split("-").map(Number);
  const [endYear, endMonth, endDay] = endDate.split("-").map(Number);

  const start = new Date(startYear ?? 0, (startMonth ?? 1) - 1, startDay ?? 1);
  const end = new Date(endYear ?? 0, (endMonth ?? 1) - 1, endDay ?? 1);
  const days: TimeSeriesPoint[] = [];

  let dayIndex = 0;
  const currentDate = new Date(start);

  while (currentDate <= end) {
    const point: TimeSeriesPoint = {
      date: formatLocalDate(currentDate),
    };

    selectedIds.forEach((id, index) => {
      // Generate pseudo-random but deterministic values
      const baseValue = 100 + index * 50;
      const variation = Math.sin(dayIndex * 0.3 + index) * 30;
      const trend = dayIndex * (index % 2 === 0 ? 2 : -1);
      point[id] = Math.max(0, Math.round(baseValue + variation + trend));
    });

    days.push(point);
    currentDate.setDate(currentDate.getDate() + 1);
    dayIndex++;
  }

  return days;
}

/**
 * Builds series configuration from selected technology IDs.
 */
function buildSeriesConfig(selectedIds: string[]): SeriesConfig[] {
  return selectedIds.map((id) => {
    const tech = DEMO_TECHNOLOGIES.find((t) => t.id === id);
    return {
      key: id,
      name: tech?.name ?? id,
      color: SERIES_COLORS[id] ?? "#888888",
    };
  });
}

/**
 * Demo page component demonstrating dashboard UI composition.
 */
export default function DemoPage() {
  // Technology selection state
  const [selectedTechIds, setSelectedTechIds] = useState<string[]>([
    "python",
    "typescript",
    "rust",
  ]);

  // Date range state
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: "2024-01-01",
    endDate: "2024-03-31",
  });

  // Chart display state for demo purposes
  const [chartState, setChartState] = useState<ChartState>("success");

  // Generate chart data based on selections
  const chartData = useMemo(() => {
    if (chartState !== "success") return [];
    return generateDummyData(
      selectedTechIds,
      dateRange.startDate,
      dateRange.endDate,
    );
  }, [selectedTechIds, dateRange, chartState]);

  const seriesConfig = useMemo(
    () => buildSeriesConfig(selectedTechIds),
    [selectedTechIds],
  );

  // Retry handler for error state
  const handleRetry = useCallback(() => {
    setChartState("success");
  }, []);

  // Date range change handler
  const handleDateRangeChange = useCallback((range: DateRange) => {
    setDateRange(range);
  }, []);

  // Technology selection change handler
  const handleTechChange = useCallback((ids: string[]) => {
    setSelectedTechIds(ids);
  }, []);

  // Sidebar content with filters
  const sidebarContent = (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="mb-4 text-lg font-semibold text-[var(--text-primary)]">
          Dashboard Demo
        </h1>
        <p className="text-sm text-[var(--text-secondary)]">
          Component integration verification page.
        </p>
      </div>

      <TechnologySelector
        selectedIds={selectedTechIds}
        availableOptions={[...DEMO_TECHNOLOGIES]}
        onChange={handleTechChange}
      />

      <DateRangePicker
        startDate={dateRange.startDate}
        endDate={dateRange.endDate}
        minDate="2020-01-01"
        maxDate="2024-12-31"
        onChange={handleDateRangeChange}
      />

      {/* Chart State Controls */}
      <div className="border-t border-[var(--border-default)] pt-4">
        <p className="mb-3 text-sm font-medium text-[var(--text-primary)]">
          Chart State (Demo Controls)
        </p>
        <div className="flex flex-wrap gap-2">
          {(["success", "loading", "error", "empty"] as const).map((state) => (
            <button
              key={state}
              type="button"
              onClick={() => setChartState(state)}
              aria-pressed={chartState === state}
              className={`
                rounded-md
                px-3
                py-1.5
                text-sm
                font-medium
                transition-colors
                focus:outline
                focus:outline-2
                focus:outline-offset-2
                focus:outline-[var(--accent-primary)]
                ${
                  chartState === state
                    ? "bg-[var(--accent-primary)] text-white"
                    : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--border-default)]"
                }
              `}
            >
              {state.charAt(0).toUpperCase() + state.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Props Documentation */}
      <div className="border-t border-[var(--border-default)] pt-4">
        <details className="text-sm">
          <summary className="cursor-pointer font-medium text-[var(--text-primary)]">
            Component Props Reference
          </summary>
          <div className="mt-3 space-y-4 text-[var(--text-secondary)]">
            <div>
              <p className="font-medium text-[var(--text-primary)]">
                TechnologySelector
              </p>
              <ul className="mt-1 list-inside list-disc space-y-1">
                <li>
                  <code>selectedIds: string[]</code>
                </li>
                <li>
                  <code>availableOptions: TechnologyOption[]</code>
                </li>
                <li>
                  <code>onChange: (ids: string[]) =&gt; void</code>
                </li>
                <li>
                  <code>disabled?: boolean</code>
                </li>
              </ul>
            </div>
            <div>
              <p className="font-medium text-[var(--text-primary)]">
                DateRangePicker
              </p>
              <ul className="mt-1 list-inside list-disc space-y-1">
                <li>
                  <code>startDate: string | null</code>
                </li>
                <li>
                  <code>endDate: string | null</code>
                </li>
                <li>
                  <code>minDate?: string</code>
                </li>
                <li>
                  <code>maxDate?: string</code>
                </li>
                <li>
                  <code>onChange: (range: DateRange) =&gt; void</code>
                </li>
              </ul>
            </div>
            <div>
              <p className="font-medium text-[var(--text-primary)]">
                TrendChart
              </p>
              <ul className="mt-1 list-inside list-disc space-y-1">
                <li>
                  <code>data: TimeSeriesPoint[]</code>
                </li>
                <li>
                  <code>series: SeriesConfig[]</code>
                </li>
                <li>
                  <code>isLoading?: boolean</code>
                </li>
                <li>
                  <code>error?: string | null</code>
                </li>
                <li>
                  <code>isEmpty?: boolean</code>
                </li>
                <li>
                  <code>onRetry?: () =&gt; void</code>
                </li>
              </ul>
            </div>
          </div>
        </details>
      </div>
    </div>
  );

  // Main content with chart
  const mainContent = (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">
          Technology Trends
        </h2>
        <p className="text-sm text-[var(--text-muted)]">
          {selectedTechIds.length} technolog
          {selectedTechIds.length === 1 ? "y" : "ies"} selected
        </p>
      </div>

      <TrendChart
        data={chartData}
        series={seriesConfig}
        isLoading={chartState === "loading"}
        error={
          chartState === "error"
            ? "Failed to load trend data. Please try again."
            : null
        }
        isEmpty={chartState === "empty"}
        onRetry={handleRetry}
      />

      {/* Current State Display */}
      <div className="rounded-md border border-[var(--border-default)] bg-[var(--bg-secondary)] p-4">
        <p className="mb-2 text-sm font-medium text-[var(--text-primary)]">
          Current State
        </p>
        <pre className="overflow-x-auto text-xs text-[var(--text-secondary)]">
          {JSON.stringify(
            {
              selectedTechnologies: selectedTechIds,
              dateRange,
              chartState,
              dataPoints: chartData.length,
            },
            null,
            2,
          )}
        </pre>
      </div>
    </div>
  );

  return <DashboardShell sidebarSlot={sidebarContent} mainSlot={mainContent} />;
}
