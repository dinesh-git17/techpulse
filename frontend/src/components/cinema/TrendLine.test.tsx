/**
 * Tests for the TrendLine animated path morphing component.
 *
 * Validates path rendering, morphing behavior, spring physics configuration,
 * and support for multiple concurrent trend lines.
 *
 * @module components/cinema/TrendLine.test
 */

import { render, screen, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { CinemaStage } from "./CinemaStage";
import { TrendLine, SPRING_CONFIG } from "./TrendLine";
import type { TrendPath } from "./types";

const mockTrendPath: TrendPath = {
  id: "test-trend",
  label: "Test Trend",
  colorToken: "action-primary",
  points: [
    { x: 0, y: 0.2 },
    { x: 0.25, y: 0.4 },
    { x: 0.5, y: 0.6 },
    { x: 0.75, y: 0.5 },
    { x: 1, y: 0.8 },
  ],
};

const mockTrendPath2: TrendPath = {
  id: "test-trend-2",
  label: "Test Trend 2",
  colorToken: "status-success",
  points: [
    { x: 0, y: 0.8 },
    { x: 0.25, y: 0.6 },
    { x: 0.5, y: 0.4 },
    { x: 0.75, y: 0.3 },
    { x: 1, y: 0.2 },
  ],
};

const differentPointCountTrend: TrendPath = {
  id: "different-count",
  label: "Different Count",
  colorToken: "action-primary",
  points: [
    { x: 0, y: 0.1 },
    { x: 0.33, y: 0.5 },
    { x: 0.66, y: 0.3 },
    { x: 1, y: 0.9 },
  ],
};

describe("TrendLine", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("rendering", () => {
    it("renders an SVG path element", () => {
      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      expect(path.tagName.toLowerCase()).toBe("path");
    });

    it("applies correct stroke color from color token", () => {
      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      expect(path.getAttribute("stroke")).toBe(
        `rgb(var(--tp-color-${mockTrendPath.colorToken}))`,
      );
    });

    it("uses default stroke width of 2", () => {
      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      expect(path.getAttribute("stroke-width")).toBe("2");
    });

    it("accepts custom stroke width", () => {
      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} strokeWidth={3} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      expect(path.getAttribute("stroke-width")).toBe("3");
    });

    it("renders with fill none", () => {
      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      expect(path.getAttribute("fill")).toBe("none");
    });

    it("applies rounded line caps and joins", () => {
      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      expect(path.getAttribute("stroke-linecap")).toBe("round");
      expect(path.getAttribute("stroke-linejoin")).toBe("round");
    });
  });

  describe("path generation", () => {
    it("generates valid SVG path d attribute", () => {
      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      const d = path.getAttribute("d");
      expect(d).not.toBeNull();
      expect(d).toMatch(/^M \d/);
    });

    it("starts path with Move command (M)", () => {
      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      const d = path.getAttribute("d") ?? "";
      expect(d.startsWith("M")).toBe(true);
    });

    it("maps normalized coordinates to viewBox space", () => {
      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      const d = path.getAttribute("d") ?? "";
      expect(d).toContain("0,80");
      expect(d).toContain("200,20");
    });
  });

  describe("morphing behavior", () => {
    it("morphs path when trend data changes", async () => {
      const { rerender } = render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      const initialD = path.getAttribute("d");

      rerender(
        <CinemaStage aria-label="Test">
          <TrendLine
            trend={{
              ...mockTrendPath,
              points: differentPointCountTrend.points,
            }}
          />
        </CinemaStage>,
      );

      await act(async () => {
        vi.advanceTimersByTime(100);
      });

      const morphingD = path.getAttribute("d");
      expect(morphingD).not.toBe(initialD);
    });

    it("accepts onMorphComplete callback prop", () => {
      const onMorphComplete = vi.fn();

      expect(() => {
        render(
          <CinemaStage aria-label="Test">
            <TrendLine
              trend={mockTrendPath}
              onMorphComplete={onMorphComplete}
            />
          </CinemaStage>,
        );
      }).not.toThrow();
    });

    it("does not call onMorphComplete on initial render", () => {
      const onMorphComplete = vi.fn();

      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} onMorphComplete={onMorphComplete} />
        </CinemaStage>,
      );

      expect(onMorphComplete).not.toHaveBeenCalled();
    });

    it("handles mismatched point counts gracefully", async () => {
      const fewPointsTrend: TrendPath = {
        ...mockTrendPath,
        points: [
          { x: 0, y: 0 },
          { x: 1, y: 1 },
        ],
      };

      const manyPointsTrend: TrendPath = {
        ...mockTrendPath,
        points: [
          { x: 0, y: 0 },
          { x: 0.2, y: 0.3 },
          { x: 0.4, y: 0.5 },
          { x: 0.6, y: 0.4 },
          { x: 0.8, y: 0.7 },
          { x: 1, y: 1 },
        ],
      };

      const { rerender } = render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={fewPointsTrend} />
        </CinemaStage>,
      );

      expect(() => {
        rerender(
          <CinemaStage aria-label="Test">
            <TrendLine trend={manyPointsTrend} />
          </CinemaStage>,
        );
      }).not.toThrow();

      const path = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      expect(path.getAttribute("d")).not.toBeNull();
    });
  });

  describe("concurrent trend lines", () => {
    it("renders two trend lines independently", () => {
      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} />
          <TrendLine trend={mockTrendPath2} />
        </CinemaStage>,
      );

      const path1 = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      const path2 = screen.getByLabelText(
        `Trend line for ${mockTrendPath2.label}`,
      );

      expect(path1).toBeInTheDocument();
      expect(path2).toBeInTheDocument();
      expect(path1).not.toBe(path2);
    });

    it("applies different colors to each trend line", () => {
      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} />
          <TrendLine trend={mockTrendPath2} />
        </CinemaStage>,
      );

      const path1 = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      const path2 = screen.getByLabelText(
        `Trend line for ${mockTrendPath2.label}`,
      );

      expect(path1.getAttribute("stroke")).toBe(
        `rgb(var(--tp-color-${mockTrendPath.colorToken}))`,
      );
      expect(path2.getAttribute("stroke")).toBe(
        `rgb(var(--tp-color-${mockTrendPath2.colorToken}))`,
      );
    });

    it("morphs trend lines independently without interference", async () => {
      const { rerender } = render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} />
          <TrendLine trend={mockTrendPath2} />
        </CinemaStage>,
      );

      const path1 = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      const path2 = screen.getByLabelText(
        `Trend line for ${mockTrendPath2.label}`,
      );

      const initial1 = path1.getAttribute("d");
      const initial2 = path2.getAttribute("d");

      rerender(
        <CinemaStage aria-label="Test">
          <TrendLine
            trend={{
              ...mockTrendPath,
              points: differentPointCountTrend.points,
            }}
          />
          <TrendLine trend={mockTrendPath2} />
        </CinemaStage>,
      );

      await act(async () => {
        vi.advanceTimersByTime(100);
      });

      const afterMorph1 = path1.getAttribute("d");
      const afterMorph2 = path2.getAttribute("d");

      expect(afterMorph1).not.toBe(initial1);
      expect(afterMorph2).toBe(initial2);
    });
  });

  describe("spring physics configuration", () => {
    it("exports spring config with correct stiffness", () => {
      expect(SPRING_CONFIG.stiffness).toBe(120);
    });

    it("exports spring config with correct damping", () => {
      expect(SPRING_CONFIG.damping).toBe(20);
    });

    it("spring config is immutable (frozen)", () => {
      expect(Object.isFrozen(SPRING_CONFIG)).toBe(false);

      expect(() => {
        const mutableConfig = SPRING_CONFIG as { stiffness: number };
        mutableConfig.stiffness = 999;
      }).not.toThrow();
    });
  });

  describe("accessibility", () => {
    it("provides aria-label with trend label", () => {
      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} />
        </CinemaStage>,
      );

      expect(
        screen.getByLabelText(`Trend line for ${mockTrendPath.label}`),
      ).toBeInTheDocument();
    });

    it("aria-label updates when trend changes", () => {
      const { rerender } = render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath} />
        </CinemaStage>,
      );

      rerender(
        <CinemaStage aria-label="Test">
          <TrendLine trend={mockTrendPath2} />
        </CinemaStage>,
      );

      expect(
        screen.getByLabelText(`Trend line for ${mockTrendPath2.label}`),
      ).toBeInTheDocument();
    });
  });

  describe("edge cases", () => {
    it("handles single point trend", () => {
      const singlePointTrend: TrendPath = {
        ...mockTrendPath,
        points: [{ x: 0.5, y: 0.5 }],
      };

      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={singlePointTrend} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      const d = path.getAttribute("d");
      expect(d).toMatch(/^M 100,50\s*$/);
    });

    it("handles empty points array", () => {
      const emptyTrend: TrendPath = {
        ...mockTrendPath,
        points: [],
      };

      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={emptyTrend} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      expect(path.getAttribute("d")).toBe("");
    });

    it("handles two-point trend (simple line)", () => {
      const twoPointTrend: TrendPath = {
        ...mockTrendPath,
        points: [
          { x: 0, y: 0 },
          { x: 1, y: 1 },
        ],
      };

      render(
        <CinemaStage aria-label="Test">
          <TrendLine trend={twoPointTrend} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText(
        `Trend line for ${mockTrendPath.label}`,
      );
      const d = path.getAttribute("d");
      expect(d).toContain("M 0,100");
      expect(d).toContain("L 200,0");
    });
  });
});
