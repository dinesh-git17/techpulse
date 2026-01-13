"use client";

/**
 * @fileoverview Dashboard container component with URL state management.
 *
 * Implements the "container/presentational" pattern where this container
 * handles URL state and data fetching, while the UI components remain
 * stateless and receive all data via props.
 *
 * URL parameters drive the dashboard state, enabling deep linking and
 * shareable dashboard configurations.
 */

import { type ReactNode, useCallback, useMemo } from "react";

import { DashboardShell } from "@/components/layouts";
import {
  DateRangePicker,
  TechnologySelector,
  TrendChart,
  type DateRange as DateRangeValue,
  type SeriesConfig,
  type TimeSeriesPoint,
  type TechnologyOption,
} from "@/components/ui";
import { useTechnologies, useTrends } from "@/features/trends/queries";
import { useDashboardParams, useUrlValidation } from "@/hooks";
import {
  parseTechIdsString,
  serializeTechIds,
  type RawDashboardParams,
} from "@/lib/url";

/**
 * Color palette for chart series (colorblind-friendly).
 */
const SERIES_COLORS: Record<string, string> = {
  python: "#3776ab",
  typescript: "#3178c6",
  javascript: "#f7df1e",
  rust: "#dea584",
  go: "#00add8",
  java: "#ed8b00",
  csharp: "#512bd4",
  kotlin: "#7f52ff",
  swift: "#f05138",
  ruby: "#cc342d",
  php: "#777bb4",
  scala: "#dc322f",
  react: "#61dafb",
  vue: "#4fc08d",
  angular: "#dd0031",
  nodejs: "#339933",
  django: "#092e20",
  rails: "#cc0000",
  spring: "#6db33f",
  docker: "#2496ed",
  kubernetes: "#326ce5",
  aws: "#ff9900",
  azure: "#0078d4",
  gcp: "#4285f4",
};

/**
 * Default color for technologies without a defined color.
 */
const DEFAULT_SERIES_COLOR = "#6b7280";

/**
 * Transform API trend data to chart-compatible format.
 *
 * Pivots from per-technology arrays to per-date objects.
 *
 * @param trends - Raw trend data from API.
 * @returns Pivoted time series data for charting.
 */
function transformTrendData(
  trends: Array<{
    tech_key: string;
    name: string;
    data: Array<{ month: string; count: number }>;
  }>,
): TimeSeriesPoint[] {
  if (trends.length === 0) return [];

  const dateMap = new Map<string, TimeSeriesPoint>();

  for (const tech of trends) {
    for (const point of tech.data) {
      const existing = dateMap.get(point.month);
      if (existing) {
        existing[tech.tech_key] = point.count;
      } else {
        dateMap.set(point.month, {
          date: point.month,
          [tech.tech_key]: point.count,
        });
      }
    }
  }

  return Array.from(dateMap.values()).sort((a, b) =>
    a.date.localeCompare(b.date),
  );
}

/**
 * Build series configuration from selected technologies.
 *
 * @param selectedIds - Selected technology IDs.
 * @param technologies - Available technologies with names.
 * @returns Series configuration for chart rendering.
 */
function buildSeriesConfig(
  selectedIds: readonly string[],
  technologies: Array<{ key: string; name: string }>,
): SeriesConfig[] {
  const techMap = new Map(technologies.map((t) => [t.key, t.name]));

  return selectedIds.map((id) => ({
    key: id,
    name: techMap.get(id) ?? id,
    color: SERIES_COLORS[id] ?? DEFAULT_SERIES_COLOR,
  }));
}

/**
 * Dashboard container component with URL-driven state.
 *
 * Manages filter state via URL parameters using the useDashboardParams hook,
 * fetches data via React Query hooks, and passes everything to the
 * presentational components.
 *
 * Features:
 * - URL state drives TechnologySelector and DateRangePicker
 * - TrendChart displays data based on URL filters
 * - Reload/share preserves exact dashboard state
 *
 * @example
 * ```tsx
 * // In a page component
 * export default function DashboardPage() {
 *   return <DashboardContainer />;
 * }
 * ```
 */
export function DashboardContainer(): ReactNode {
  const { selectedTechs, setTechs, dateRange, setDateRange } =
    useDashboardParams();

  const {
    data: technologiesData,
    isLoading: isTechLoading,
    error: techError,
  } = useTechnologies();

  const knownTechIds = useMemo(() => {
    if (!technologiesData?.data) {
      return new Set<string>();
    }
    return new Set(technologiesData.data.map((tech) => tech.key));
  }, [technologiesData]);

  const rawParams: RawDashboardParams = useMemo(
    () => ({
      tech_ids: serializeTechIds(selectedTechs),
      start: dateRange.startDate,
      end: dateRange.endDate,
    }),
    [selectedTechs, dateRange],
  );

  const handleCorrection = useCallback(
    (correctedParams: RawDashboardParams) => {
      const correctedTechs = parseTechIdsString(correctedParams.tech_ids);
      setTechs(correctedTechs);
      if (correctedParams.start && correctedParams.end) {
        setDateRange({
          startDate: correctedParams.start,
          endDate: correctedParams.end,
        });
      }
    },
    [setTechs, setDateRange],
  );

  useUrlValidation({
    rawParams,
    knownTechIds,
    onCorrect: handleCorrection,
    enabled: !isTechLoading && knownTechIds.size > 0,
  });

  const techIdsString = serializeTechIds(selectedTechs);

  const {
    data: trendsData,
    isLoading: isTrendsLoading,
    error: trendsError,
    refetch: refetchTrends,
  } = useTrends({
    filters: {
      techIds: techIdsString,
      startDate: dateRange.startDate,
      endDate: dateRange.endDate,
    },
    enabled: selectedTechs.length > 0,
  });

  const availableOptions: TechnologyOption[] = useMemo(() => {
    if (!technologiesData?.data) return [];
    return technologiesData.data.map((tech) => ({
      id: tech.key,
      name: tech.name,
    }));
  }, [technologiesData]);

  const chartData = useMemo(() => {
    if (!trendsData?.data) return [];
    return transformTrendData(trendsData.data);
  }, [trendsData]);

  const seriesConfig = useMemo(() => {
    if (!technologiesData?.data) return [];
    return buildSeriesConfig(selectedTechs, technologiesData.data);
  }, [selectedTechs, technologiesData]);

  const handleDateRangeChange = useCallback(
    (range: DateRangeValue) => {
      setDateRange({
        startDate: range.startDate,
        endDate: range.endDate,
      });
    },
    [setDateRange],
  );

  const handleRetry = useCallback(() => {
    void refetchTrends();
  }, [refetchTrends]);

  const chartError = trendsError instanceof Error ? trendsError.message : null;
  const chartIsEmpty = selectedTechs.length === 0 || chartData.length === 0;

  const sidebarContent = (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="mb-2 text-lg font-semibold text-[var(--text-primary)]">
          Technology Trends
        </h1>
        <p className="text-sm text-[var(--text-secondary)]">
          Explore job market demand across technologies.
        </p>
      </div>

      <TechnologySelector
        selectedIds={[...selectedTechs]}
        availableOptions={availableOptions}
        onChange={setTechs}
        disabled={isTechLoading || !!techError}
      />

      <DateRangePicker
        startDate={dateRange.startDate}
        endDate={dateRange.endDate}
        onChange={handleDateRangeChange}
      />

      {techError && (
        <div className="rounded-md border border-[var(--accent-danger)]/30 bg-[var(--accent-danger)]/5 p-3">
          <p className="text-sm text-[var(--accent-danger)]">
            Failed to load technologies. Please refresh the page.
          </p>
        </div>
      )}
    </div>
  );

  const mainContent = (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">
          Trend Analysis
        </h2>
        <p className="text-sm text-[var(--text-muted)]">
          {selectedTechs.length} technolog
          {selectedTechs.length === 1 ? "y" : "ies"} selected
        </p>
      </div>

      <TrendChart
        data={chartData}
        series={seriesConfig}
        isLoading={isTrendsLoading && selectedTechs.length > 0}
        error={chartError}
        isEmpty={chartIsEmpty && !isTrendsLoading}
        onRetry={handleRetry}
      />
    </div>
  );

  return <DashboardShell sidebarSlot={sidebarContent} mainSlot={mainContent} />;
}
