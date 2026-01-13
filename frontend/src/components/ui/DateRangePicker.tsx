"use client";

/**
 * @fileoverview Accessible date range picker with calendar UI.
 *
 * Design rationale: Uses Radix UI Popover for dropdown positioning with a
 * custom calendar grid implementing WAI-ARIA grid pattern. Supports full
 * keyboard navigation and validates that end date follows start date.
 */
import {
  type KeyboardEvent,
  type ReactNode,
  useCallback,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";

import * as Popover from "@radix-ui/react-popover";

/**
 * Date range value with ISO 8601 date strings.
 */
export interface DateRange {
  /** Start date in ISO 8601 format (YYYY-MM-DD). */
  startDate: string;
  /** End date in ISO 8601 format (YYYY-MM-DD). */
  endDate: string;
}

/**
 * Props for the DateRangePicker component.
 */
export interface DateRangePickerProps {
  /** Start date in ISO 8601 format (YYYY-MM-DD), or null if not set. */
  startDate: string | null;

  /** End date in ISO 8601 format (YYYY-MM-DD), or null if not set. */
  endDate: string | null;

  /** Earliest selectable date in ISO 8601 format. */
  minDate?: string;

  /** Latest selectable date in ISO 8601 format. */
  maxDate?: string;

  /** Callback fired when the date range changes. */
  onChange: (range: DateRange) => void;

  /** Disables the picker when true. */
  disabled?: boolean;
}

const DAYS_OF_WEEK = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"] as const;
const MONTH_NAMES = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
] as const;

/**
 * Parses an ISO date string to a Date object in local timezone.
 */
function parseDate(dateStr: string): Date {
  const [year, month, day] = dateStr.split("-").map(Number);
  return new Date(year ?? 0, (month ?? 1) - 1, day ?? 1);
}

/**
 * Formats a Date object to ISO 8601 date string (YYYY-MM-DD).
 */
function formatDateToISO(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/**
 * Formats a date for display (e.g., "Jan 15, 2024").
 */
function formatDateForDisplay(dateStr: string | null): string {
  if (!dateStr) return "";
  const date = parseDate(dateStr);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/**
 * Gets all days in a month as a 2D array (weeks × days).
 */
function getCalendarDays(year: number, month: number): (Date | null)[][] {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const daysInMonth = lastDay.getDate();
  const startDayOfWeek = firstDay.getDay();

  const weeks: (Date | null)[][] = [];
  let currentWeek: (Date | null)[] = [];

  // Fill in empty days before the first day of the month
  for (let i = 0; i < startDayOfWeek; i++) {
    currentWeek.push(null);
  }

  // Fill in the days of the month
  for (let day = 1; day <= daysInMonth; day++) {
    currentWeek.push(new Date(year, month, day));
    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  }

  // Fill in empty days after the last day of the month
  if (currentWeek.length > 0) {
    while (currentWeek.length < 7) {
      currentWeek.push(null);
    }
    weeks.push(currentWeek);
  }

  return weeks;
}

/**
 * Checks if two dates are the same day.
 */
function isSameDay(a: Date | null, b: Date | null): boolean {
  if (!a || !b) return false;
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

/**
 * Checks if a date is within a range (inclusive).
 */
function isInRange(date: Date, start: Date | null, end: Date | null): boolean {
  if (!start || !end) return false;
  return date >= start && date <= end;
}

/**
 * Renders an accessible date range picker with calendar UI.
 *
 * Implements a two-step selection flow: first click sets start date,
 * second click sets end date. Validates that end date is after start date.
 * Full keyboard navigation with Arrow keys, Enter, and Escape.
 *
 * @param props.startDate - Start date in ISO format, or null.
 * @param props.endDate - End date in ISO format, or null.
 * @param props.minDate - Earliest selectable date.
 * @param props.maxDate - Latest selectable date.
 * @param props.onChange - Callback when range changes.
 * @param props.disabled - Disables the picker when true.
 *
 * @example
 * ```tsx
 * <DateRangePicker
 *   startDate="2024-01-01"
 *   endDate="2024-01-31"
 *   minDate="2020-01-01"
 *   maxDate="2024-12-31"
 *   onChange={({ startDate, endDate }) => {
 *     setStartDate(startDate);
 *     setEndDate(endDate);
 *   }}
 * />
 * ```
 */
export function DateRangePicker({
  startDate,
  endDate,
  minDate,
  maxDate,
  onChange,
  disabled = false,
}: DateRangePickerProps): ReactNode {
  const [isOpen, setIsOpen] = useState(false);
  const [viewDate, setViewDate] = useState(() => {
    if (startDate) return parseDate(startDate);
    return new Date();
  });
  const [selectionPhase, setSelectionPhase] = useState<"start" | "end">(
    "start",
  );
  const [pendingStart, setPendingStart] = useState<string | null>(null);
  const [focusedDate, setFocusedDate] = useState<Date | null>(null);

  const gridRef = useRef<HTMLDivElement>(null);
  const instanceId = useId();

  const parsedStartDate = useMemo(
    () => (startDate ? parseDate(startDate) : null),
    [startDate],
  );
  const parsedEndDate = useMemo(
    () => (endDate ? parseDate(endDate) : null),
    [endDate],
  );
  const parsedMinDate = useMemo(
    () => (minDate ? parseDate(minDate) : null),
    [minDate],
  );
  const parsedMaxDate = useMemo(
    () => (maxDate ? parseDate(maxDate) : null),
    [maxDate],
  );
  const parsedPendingStart = useMemo(
    () => (pendingStart ? parseDate(pendingStart) : null),
    [pendingStart],
  );

  const calendarDays = useMemo(
    () => getCalendarDays(viewDate.getFullYear(), viewDate.getMonth()),
    [viewDate],
  );

  const isDateDisabled = useCallback(
    (date: Date): boolean => {
      if (parsedMinDate && date < parsedMinDate) return true;
      if (parsedMaxDate && date > parsedMaxDate) return true;
      return false;
    },
    [parsedMinDate, parsedMaxDate],
  );

  const handleDateSelect = useCallback(
    (date: Date) => {
      if (isDateDisabled(date)) return;

      const dateStr = formatDateToISO(date);

      if (selectionPhase === "start") {
        setPendingStart(dateStr);
        setSelectionPhase("end");
      } else {
        const start = pendingStart ?? startDate;
        if (!start) {
          setPendingStart(dateStr);
          setSelectionPhase("end");
          return;
        }

        const startDateObj = parseDate(start);
        if (date < startDateObj) {
          // User selected a date before start, swap them
          onChange({ startDate: dateStr, endDate: start });
        } else {
          onChange({ startDate: start, endDate: dateStr });
        }
        setPendingStart(null);
        setSelectionPhase("start");
        setIsOpen(false);
      }
    },
    [selectionPhase, pendingStart, startDate, onChange, isDateDisabled],
  );

  const handlePrevMonth = useCallback(() => {
    setViewDate((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  }, []);

  const handleNextMonth = useCallback(() => {
    setViewDate((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
  }, []);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>) => {
      const currentFocus = focusedDate ?? parsedStartDate ?? new Date();
      let newFocus: Date | null = null;

      switch (event.key) {
        case "ArrowLeft":
          event.preventDefault();
          newFocus = new Date(currentFocus);
          newFocus.setDate(newFocus.getDate() - 1);
          break;
        case "ArrowRight":
          event.preventDefault();
          newFocus = new Date(currentFocus);
          newFocus.setDate(newFocus.getDate() + 1);
          break;
        case "ArrowUp":
          event.preventDefault();
          newFocus = new Date(currentFocus);
          newFocus.setDate(newFocus.getDate() - 7);
          break;
        case "ArrowDown":
          event.preventDefault();
          newFocus = new Date(currentFocus);
          newFocus.setDate(newFocus.getDate() + 7);
          break;
        case "Enter":
        case " ":
          event.preventDefault();
          if (focusedDate && !isDateDisabled(focusedDate)) {
            handleDateSelect(focusedDate);
          }
          break;
        case "Escape":
          event.preventDefault();
          setIsOpen(false);
          setPendingStart(null);
          setSelectionPhase("start");
          break;
      }

      if (newFocus) {
        // Update view if focus moves to different month
        if (
          newFocus.getMonth() !== viewDate.getMonth() ||
          newFocus.getFullYear() !== viewDate.getFullYear()
        ) {
          setViewDate(new Date(newFocus.getFullYear(), newFocus.getMonth(), 1));
        }
        setFocusedDate(newFocus);
      }
    },
    [focusedDate, parsedStartDate, viewDate, isDateDisabled, handleDateSelect],
  );

  const handleOpenChange = useCallback((open: boolean) => {
    setIsOpen(open);
    if (!open) {
      setPendingStart(null);
      setSelectionPhase("start");
      setFocusedDate(null);
    }
  }, []);

  const displayValue = useMemo(() => {
    if (startDate && endDate) {
      return `${formatDateForDisplay(startDate)} – ${formatDateForDisplay(endDate)}`;
    }
    if (pendingStart) {
      return `${formatDateForDisplay(pendingStart)} – Select end date`;
    }
    return "Select date range";
  }, [startDate, endDate, pendingStart]);

  // Determine which dates to highlight as the active range
  const activeStart = parsedPendingStart ?? parsedStartDate;
  const activeEnd = parsedPendingStart ? null : parsedEndDate;

  return (
    <div className="w-full">
      <span
        id={`${instanceId}-label`}
        className="mb-2 block text-sm font-medium text-[var(--text-primary)]"
      >
        Date Range
      </span>

      <Popover.Root open={isOpen} onOpenChange={handleOpenChange}>
        <Popover.Trigger asChild>
          <button
            type="button"
            disabled={disabled}
            aria-labelledby={`${instanceId}-label`}
            aria-haspopup="dialog"
            className={`
              flex
              min-h-[44px]
              w-full
              items-center
              justify-between
              rounded-md
              border
              border-[var(--border-default)]
              bg-[var(--bg-primary)]
              px-3
              py-2
              text-left
              text-sm
              transition-colors
              focus:border-[var(--accent-primary)]
              focus:outline
              focus:outline-2
              focus:outline-offset-2
              focus:outline-[var(--accent-primary)]
              ${disabled ? "cursor-not-allowed opacity-50" : "hover:border-[var(--border-default)]"}
              ${startDate && endDate ? "text-[var(--text-primary)]" : "text-[var(--text-muted)]"}
            `}
          >
            <span>{displayValue}</span>
            <svg
              className="h-4 w-4 text-[var(--text-muted)]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </button>
        </Popover.Trigger>

        <Popover.Portal>
          <Popover.Content
            className="
              z-50
              mt-1
              rounded-md
              border
              border-[var(--border-default)]
              bg-[var(--bg-primary)]
              p-4
              shadow-lg
            "
            sideOffset={4}
            align="start"
            onKeyDown={handleKeyDown}
            aria-label="Date range picker calendar"
          >
            {/* Calendar header with navigation */}
            <div className="mb-4 flex items-center justify-between">
              <button
                type="button"
                onClick={handlePrevMonth}
                aria-label="Previous month"
                className="
                    inline-flex
                    h-11
                    w-11
                    items-center
                    justify-center
                    rounded
                    text-[var(--text-secondary)]
                    transition-colors
                    hover:bg-[var(--bg-secondary)]
                    focus:outline
                    focus:outline-2
                    focus:outline-[var(--accent-primary)]
                  "
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </button>

              <span
                className="text-sm font-medium text-[var(--text-primary)]"
                aria-live="polite"
              >
                {MONTH_NAMES[viewDate.getMonth()]} {viewDate.getFullYear()}
              </span>

              <button
                type="button"
                onClick={handleNextMonth}
                aria-label="Next month"
                className="
                    inline-flex
                    h-11
                    w-11
                    items-center
                    justify-center
                    rounded
                    text-[var(--text-secondary)]
                    transition-colors
                    hover:bg-[var(--bg-secondary)]
                    focus:outline
                    focus:outline-2
                    focus:outline-[var(--accent-primary)]
                  "
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </button>
            </div>

            {/* Selection phase indicator */}
            <div className="mb-3 text-center text-xs text-[var(--text-muted)]">
              {selectionPhase === "start"
                ? "Select start date"
                : "Select end date"}
            </div>

            {/* Calendar grid */}
            <div
              ref={gridRef}
              role="grid"
              aria-label={`${MONTH_NAMES[viewDate.getMonth()]} ${viewDate.getFullYear()}`}
              className="select-none"
            >
              {/* Day headers */}
              <div role="row" className="mb-1 grid grid-cols-7 gap-1">
                {DAYS_OF_WEEK.map((day) => (
                  <div
                    key={day}
                    role="columnheader"
                    aria-label={day}
                    className="
                        flex
                        h-11
                        w-11
                        items-center
                        justify-center
                        text-xs
                        font-medium
                        text-[var(--text-muted)]
                      "
                  >
                    {day}
                  </div>
                ))}
              </div>

              {/* Date cells */}
              {calendarDays.map((week, weekIndex) => (
                <div
                  key={weekIndex}
                  role="row"
                  className="grid grid-cols-7 gap-1"
                >
                  {week.map((date, dayIndex) => {
                    if (!date) {
                      return (
                        <div
                          key={`empty-${dayIndex}`}
                          role="gridcell"
                          className="h-11 w-11"
                        />
                      );
                    }

                    const dateStr = formatDateToISO(date);
                    const isDisabled = isDateDisabled(date);
                    const isStart = isSameDay(date, activeStart);
                    const isEnd = isSameDay(date, activeEnd);
                    const isWithinRange = isInRange(
                      date,
                      activeStart,
                      activeEnd,
                    );
                    const isFocused = isSameDay(date, focusedDate);
                    const isToday = isSameDay(date, new Date());

                    return (
                      <button
                        key={dateStr}
                        type="button"
                        role="gridcell"
                        tabIndex={isFocused ? 0 : -1}
                        aria-selected={isStart || isEnd}
                        aria-disabled={isDisabled}
                        aria-label={date.toLocaleDateString("en-US", {
                          weekday: "long",
                          year: "numeric",
                          month: "long",
                          day: "numeric",
                        })}
                        onClick={() => handleDateSelect(date)}
                        onFocus={() => setFocusedDate(date)}
                        disabled={isDisabled}
                        className={`
                            inline-flex
                            h-11
                            w-11
                            items-center
                            justify-center
                            rounded
                            text-sm
                            transition-colors
                            focus:outline
                            focus:outline-2
                            focus:outline-[var(--accent-primary)]
                            ${isDisabled ? "cursor-not-allowed text-[var(--text-muted)] opacity-50" : "cursor-pointer"}
                            ${isStart || isEnd ? "bg-[var(--accent-primary)] text-white" : ""}
                            ${isWithinRange && !isStart && !isEnd ? "bg-[var(--accent-primary)]/20 text-[var(--text-primary)]" : ""}
                            ${!isStart && !isEnd && !isWithinRange && !isDisabled ? "hover:bg-[var(--bg-secondary)] text-[var(--text-primary)]" : ""}
                            ${isToday && !isStart && !isEnd ? "font-bold" : ""}
                          `}
                      >
                        {date.getDate()}
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>
    </div>
  );
}
