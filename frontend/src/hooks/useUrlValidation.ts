/**
 * Hook for validating and auto-correcting URL search parameters.
 *
 * Detects invalid URL state combinations, applies corrections via replaceState,
 * and displays toast notifications to inform users of auto-corrections.
 *
 * @module hooks/useUrlValidation
 */

"use client";

import { useEffect, useRef } from "react";

import { toast } from "sonner";

import {
  parseDashboardParams,
  serializeTechIds,
  type ParamCorrection,
  type RawDashboardParams,
} from "@/lib/url";

/**
 * Options for configuring URL validation behavior.
 */
export interface UseUrlValidationOptions {
  /** Current raw URL parameters from the search string. */
  readonly rawParams: RawDashboardParams;
  /** Set of known valid technology IDs for filtering unknown entries. */
  readonly knownTechIds: ReadonlySet<string>;
  /** Callback to update URL parameters when corrections are applied. */
  readonly onCorrect: (correctedParams: RawDashboardParams) => void;
  /** Whether validation is ready to run (e.g., after tech catalog loads). */
  readonly enabled: boolean;
}

/**
 * Map correction types to user-friendly toast messages.
 *
 * @param correction - The correction that was applied.
 * @returns Toast configuration with title and description.
 */
function getCorrectionToast(correction: ParamCorrection): {
  title: string;
  description: string;
} {
  switch (correction.type) {
    case "invalid_date_format":
      return {
        title: "Invalid date format",
        description: correction.message,
      };
    case "impossible_date_range":
      return {
        title: "Date range adjusted",
        description: correction.message,
      };
    case "excess_tech_ids":
      return {
        title: "Selection trimmed",
        description: correction.message,
      };
    case "unknown_tech_ids":
      return {
        title: "Unknown technologies removed",
        description: correction.message,
      };
  }
}

/**
 * Validate URL parameters and auto-correct invalid values.
 *
 * Runs validation when enabled and displays toast notifications for any
 * corrections applied. Uses replaceState to update the URL without creating
 * browser history entries.
 *
 * Validation scenarios:
 * - Invalid date formats revert to 12-month default range
 * - Impossible date ranges (start >= end) adjust end date
 * - Excess tech_ids (>10) truncate to first 10
 * - Unknown tech_ids are filtered out
 *
 * @param options - Configuration for validation behavior.
 * @returns Validation state including whether validation is complete.
 *
 * @example
 * ```tsx
 * function DashboardContainer() {
 *   const { data: techData } = useTechnologies();
 *   const [params, setParams] = useQueryStates(dashboardSearchParams);
 *
 *   const knownTechIds = useMemo(
 *     () => new Set(techData?.data.map(t => t.key) ?? []),
 *     [techData]
 *   );
 *
 *   useUrlValidation({
 *     rawParams: {
 *       tech_ids: params.tech_ids.join(','),
 *       start: params.start,
 *       end: params.end,
 *     },
 *     knownTechIds,
 *     onCorrect: (corrected) => {
 *       setParams({
 *         tech_ids: corrected.tech_ids?.split(',').filter(Boolean) ?? [],
 *         start: corrected.start,
 *         end: corrected.end,
 *       });
 *     },
 *     enabled: !!techData,
 *   });
 * }
 * ```
 */
export function useUrlValidation(options: UseUrlValidationOptions): void {
  const { rawParams, knownTechIds, onCorrect, enabled } = options;

  const prevParamsRef = useRef<string>("");
  const hasProcessedRef = useRef(false);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const paramsKey = JSON.stringify(rawParams);
    if (paramsKey === prevParamsRef.current && hasProcessedRef.current) {
      return;
    }
    prevParamsRef.current = paramsKey;

    const { params: correctedParams, corrections } = parseDashboardParams(
      rawParams,
      knownTechIds,
    );

    if (corrections.length === 0) {
      hasProcessedRef.current = true;
      return;
    }

    const correctedRaw: RawDashboardParams = {
      tech_ids: serializeTechIds(correctedParams.techIds),
      start: correctedParams.startDate,
      end: correctedParams.endDate,
    };

    onCorrect(correctedRaw);

    for (const correction of corrections) {
      const { title, description } = getCorrectionToast(correction);
      toast.info(title, { description });
    }

    hasProcessedRef.current = true;
  }, [rawParams, knownTechIds, onCorrect, enabled]);
}
