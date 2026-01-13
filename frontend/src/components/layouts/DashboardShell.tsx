/**
 * @fileoverview Dashboard layout shell using CSS Grid composition pattern.
 *
 * Design rationale: Uses a slot-based composition model to decouple layout
 * structure from content. The sidebar and main content areas are injected
 * via props, enabling flexible reuse across different dashboard views while
 * maintaining consistent responsive behavior.
 */
import type { ReactNode } from "react";

/**
 * Props for the DashboardShell layout component.
 */
export interface DashboardShellProps {
  /**
   * Content rendered in the sidebar region.
   * On desktop (≥768px): Fixed 280px width on the left.
   * On mobile (<768px): Stacks vertically above main content.
   */
  sidebarSlot: ReactNode;

  /**
   * Content rendered in the main content region.
   * Fills remaining horizontal space on desktop.
   */
  mainSlot: ReactNode;
}

/**
 * Renders a responsive dashboard layout with sidebar and main content regions.
 *
 * Uses CSS Grid to create a two-column layout on desktop that collapses to a
 * single-column vertical stack on mobile viewports. The sidebar uses semantic
 * `<aside>` element and main content uses `<main>` for accessibility.
 *
 * @param props.sidebarSlot - Content for the sidebar area (filters, navigation).
 * @param props.mainSlot - Content for the main chart/data area.
 *
 * @example
 * ```tsx
 * <DashboardShell
 *   sidebarSlot={<TechnologySelector {...selectorProps} />}
 *   mainSlot={<TrendChart {...chartProps} />}
 * />
 * ```
 */
export function DashboardShell({
  sidebarSlot,
  mainSlot,
}: DashboardShellProps): ReactNode {
  return (
    <div
      className="
        grid
        min-h-screen
        w-full
        grid-cols-1
        md:grid-cols-[280px_1fr]
      "
    >
      <aside
        className="
          border-b
          border-[var(--border-muted)]
          bg-[var(--bg-secondary)]
          p-4
          md:border-b-0
          md:border-r
          md:p-6
        "
        aria-label="Dashboard filters"
      >
        {sidebarSlot}
      </aside>

      <main
        className="
          min-w-0
          bg-[var(--bg-primary)]
          p-4
          md:p-6
        "
      >
        {mainSlot}
      </main>
    </div>
  );
}
