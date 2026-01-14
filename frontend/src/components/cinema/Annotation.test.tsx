/**
 * Tests for the Annotation component.
 *
 * Validates positioning, timing synchronization, collision avoidance,
 * and framer-motion animation behavior for narrative overlays.
 *
 * @module components/cinema/Annotation.test
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { Annotation } from "./Annotation";
import { CinemaStage } from "./CinemaStage";
import type { CinemaAnnotation, TrendPath } from "./types";

const mockAnnotation: CinemaAnnotation = {
  text: "Test annotation",
  anchor: { x: 0.5, y: 0.5 },
  enterDelay: 500,
  duration: 2000,
};

const mockTrendAbove: TrendPath = {
  id: "trend-above",
  label: "Trend Above",
  colorToken: "action-primary",
  points: [
    { x: 0.4, y: 0.7 },
    { x: 0.5, y: 0.8 },
    { x: 0.6, y: 0.75 },
  ],
};

const mockTrendBelow: TrendPath = {
  id: "trend-below",
  label: "Trend Below",
  colorToken: "action-primary",
  points: [
    { x: 0.4, y: 0.3 },
    { x: 0.5, y: 0.2 },
    { x: 0.6, y: 0.25 },
  ],
};

describe("Annotation", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("visibility timing", () => {
    it("is hidden when sceneElapsedTime is less than enterDelay", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={mockAnnotation}
            sceneElapsedTime={400}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      expect(screen.queryByText(mockAnnotation.text)).not.toBeInTheDocument();
    });

    it("is visible when sceneElapsedTime is between enterDelay and enterDelay + duration", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={mockAnnotation}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      expect(screen.getByText(mockAnnotation.text)).toBeInTheDocument();
    });

    it("is hidden when sceneElapsedTime exceeds enterDelay + duration", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={mockAnnotation}
            sceneElapsedTime={2600}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      expect(screen.queryByText(mockAnnotation.text)).not.toBeInTheDocument();
    });

    it("is hidden during morphing phase regardless of timing", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={mockAnnotation}
            sceneElapsedTime={1000}
            isMorphing={true}
            trends={[]}
          />
        </CinemaStage>,
      );

      expect(screen.queryByText(mockAnnotation.text)).not.toBeInTheDocument();
    });

    it("respects exact enterDelay boundary", () => {
      const { rerender } = render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={mockAnnotation}
            sceneElapsedTime={499}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      expect(screen.queryByText(mockAnnotation.text)).not.toBeInTheDocument();

      rerender(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={mockAnnotation}
            sceneElapsedTime={500}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      expect(screen.getByText(mockAnnotation.text)).toBeInTheDocument();
    });
  });

  describe("positioning", () => {
    it("renders SVG text element when visible", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={mockAnnotation}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      const text = screen.getByText(mockAnnotation.text);
      expect(text.tagName.toLowerCase()).toBe("text");
    });

    it("positions annotation using scaled coordinates", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={{
              ...mockAnnotation,
              anchor: { x: 0.5, y: 0.5 },
            }}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      const text = screen.getByText(mockAnnotation.text);
      const xAttr = text.getAttribute("x");

      expect(xAttr).toBe("100");
    });

    it("uses middle text-anchor for center-positioned annotations", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={{
              ...mockAnnotation,
              anchor: { x: 0.5, y: 0.5 },
            }}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      const text = screen.getByText(mockAnnotation.text);
      expect(text.getAttribute("text-anchor")).toBe("middle");
    });

    it("uses start text-anchor for left-positioned annotations", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={{
              ...mockAnnotation,
              anchor: { x: 0.1, y: 0.5 },
            }}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      const text = screen.getByText(mockAnnotation.text);
      expect(text.getAttribute("text-anchor")).toBe("start");
    });

    it("uses end text-anchor for right-positioned annotations", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={{
              ...mockAnnotation,
              anchor: { x: 0.9, y: 0.5 },
            }}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      const text = screen.getByText(mockAnnotation.text);
      expect(text.getAttribute("text-anchor")).toBe("end");
    });
  });

  describe("collision avoidance", () => {
    it("offsets annotation above when trend line is below anchor", () => {
      const { container } = render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={{
              ...mockAnnotation,
              anchor: { x: 0.5, y: 0.5 },
            }}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[mockTrendBelow]}
          />
        </CinemaStage>,
      );

      const text = container.querySelector("text");
      const yValue = parseFloat(text?.getAttribute("y") ?? "0");

      expect(yValue).toBeLessThan(50);
    });

    it("offsets annotation below when trend line is above anchor", () => {
      const { container } = render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={{
              ...mockAnnotation,
              anchor: { x: 0.5, y: 0.5 },
            }}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[mockTrendAbove]}
          />
        </CinemaStage>,
      );

      const text = container.querySelector("text");
      const yValue = parseFloat(text?.getAttribute("y") ?? "0");

      expect(yValue).toBeGreaterThan(50);
    });

    it("defaults to above offset when no trends provided", () => {
      const { container } = render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={{
              ...mockAnnotation,
              anchor: { x: 0.5, y: 0.5 },
            }}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      const text = container.querySelector("text");
      const yValue = parseFloat(text?.getAttribute("y") ?? "0");

      expect(yValue).toBeLessThan(50);
    });
  });

  describe("styling", () => {
    it("applies color from colorToken prop", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={mockAnnotation}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[]}
            colorToken="status-success"
          />
        </CinemaStage>,
      );

      const text = screen.getByText(mockAnnotation.text);
      expect(text.getAttribute("fill")).toBe(
        "rgb(var(--tp-color-status-success))",
      );
    });

    it("uses text-primary as default color token", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={mockAnnotation}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      const text = screen.getByText(mockAnnotation.text);
      expect(text.getAttribute("fill")).toBe(
        "rgb(var(--tp-color-text-primary))",
      );
    });

    it("disables pointer events on annotation text", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={mockAnnotation}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      const text = screen.getByText(mockAnnotation.text);
      expect(text.style.pointerEvents).toBe("none");
    });
  });

  describe("accessibility", () => {
    it("renders with role status for screen readers", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={mockAnnotation}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      const text = screen.getByText(mockAnnotation.text);
      expect(text.getAttribute("role")).toBe("status");
    });

    it("wraps annotation in aria-live polite group", () => {
      const { container } = render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={mockAnnotation}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      const group = container.querySelector("g[aria-live='polite']");
      expect(group).toBeInTheDocument();
    });
  });

  describe("edge cases", () => {
    it("handles zero enterDelay", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={{
              ...mockAnnotation,
              enterDelay: 0,
            }}
            sceneElapsedTime={0}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      expect(screen.getByText(mockAnnotation.text)).toBeInTheDocument();
    });

    it("handles annotation at viewBox edges", () => {
      const { container } = render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={{
              ...mockAnnotation,
              anchor: { x: 0, y: 0 },
            }}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      const text = container.querySelector("text");
      const xValue = parseFloat(text?.getAttribute("x") ?? "-1");
      const yValue = parseFloat(text?.getAttribute("y") ?? "-1");

      expect(xValue).toBeGreaterThanOrEqual(4);
      expect(yValue).toBeLessThanOrEqual(96);
    });

    it("handles empty text annotation", () => {
      render(
        <CinemaStage aria-label="Test">
          <Annotation
            annotation={{
              ...mockAnnotation,
              text: "",
            }}
            sceneElapsedTime={1000}
            isMorphing={false}
            trends={[]}
          />
        </CinemaStage>,
      );

      const textElements = document.querySelectorAll("text");
      expect(textElements.length).toBe(1);
    });
  });
});
