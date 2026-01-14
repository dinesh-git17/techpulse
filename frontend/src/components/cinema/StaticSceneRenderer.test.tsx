/**
 * Tests for the StaticSceneRenderer component.
 *
 * Validates static rendering of trend lines and annotations
 * for SSR and reduced motion accessibility mode.
 *
 * @module components/cinema/StaticSceneRenderer.test
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { CinemaStage } from "./CinemaStage";
import { StaticSceneRenderer } from "./StaticSceneRenderer";
import type { CinemaScene } from "./types";

const mockScene: CinemaScene = {
  id: "test-scene",
  title: "Test Scene",
  duration: 5000,
  morphDuration: 1000,
  trends: [
    {
      id: "trend-1",
      label: "Rust",
      colorToken: "action-primary",
      points: [
        { x: 0, y: 0.2 },
        { x: 0.5, y: 0.6 },
        { x: 1, y: 0.8 },
      ],
    },
  ],
  annotations: [
    {
      text: "Growth trend",
      anchor: { x: 0.7, y: 0.65 },
      enterDelay: 500,
      duration: 4000,
    },
  ],
};

const mockSceneTwoTrends: CinemaScene = {
  ...mockScene,
  id: "test-scene-two",
  trends: [
    {
      id: "trend-1",
      label: "Rust",
      colorToken: "action-primary",
      points: [
        { x: 0, y: 0.2 },
        { x: 0.5, y: 0.6 },
        { x: 1, y: 0.8 },
      ],
    },
    {
      id: "trend-2",
      label: "C++",
      colorToken: "status-warning",
      points: [
        { x: 0, y: 0.8 },
        { x: 0.5, y: 0.5 },
        { x: 1, y: 0.3 },
      ],
    },
  ],
};

describe("StaticSceneRenderer", () => {
  describe("trend line rendering", () => {
    it("renders single trend line", () => {
      render(
        <CinemaStage aria-label="Test">
          <StaticSceneRenderer scene={mockScene} />
        </CinemaStage>,
      );

      expect(screen.getByLabelText("Trend line for Rust")).toBeInTheDocument();
    });

    it("renders two trend lines", () => {
      render(
        <CinemaStage aria-label="Test">
          <StaticSceneRenderer scene={mockSceneTwoTrends} />
        </CinemaStage>,
      );

      expect(screen.getByLabelText("Trend line for Rust")).toBeInTheDocument();
      expect(screen.getByLabelText("Trend line for C++")).toBeInTheDocument();
    });

    it("generates valid SVG path for trend line", () => {
      render(
        <CinemaStage aria-label="Test">
          <StaticSceneRenderer scene={mockScene} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText("Trend line for Rust");
      const d = path.getAttribute("d");
      expect(d).not.toBeNull();
      expect(d).toMatch(/^M \d/);
    });

    it("applies correct stroke color from color token", () => {
      render(
        <CinemaStage aria-label="Test">
          <StaticSceneRenderer scene={mockScene} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText("Trend line for Rust");
      expect(path.getAttribute("stroke")).toBe(
        "rgb(var(--tp-color-action-primary))",
      );
    });

    it("maps normalized coordinates to viewBox space", () => {
      render(
        <CinemaStage aria-label="Test">
          <StaticSceneRenderer scene={mockScene} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText("Trend line for Rust");
      const d = path.getAttribute("d") ?? "";
      expect(d).toContain("0,80");
      expect(d).toContain("200,20");
    });
  });

  describe("annotation rendering", () => {
    it("renders annotations visible at scene end", () => {
      render(
        <CinemaStage aria-label="Test">
          <StaticSceneRenderer scene={mockScene} />
        </CinemaStage>,
      );

      expect(screen.getByText("Growth trend")).toBeInTheDocument();
    });

    it("renders all annotations regardless of timing", () => {
      const sceneWithMultipleAnnotations: CinemaScene = {
        ...mockScene,
        annotations: [
          {
            text: "Early annotation",
            anchor: { x: 0.3, y: 0.5 },
            enterDelay: 100,
            duration: 1000,
          },
          {
            text: "Late annotation",
            anchor: { x: 0.7, y: 0.7 },
            enterDelay: 3000,
            duration: 2000,
          },
        ],
      };

      render(
        <CinemaStage aria-label="Test">
          <StaticSceneRenderer scene={sceneWithMultipleAnnotations} />
        </CinemaStage>,
      );

      expect(screen.getByText("Early annotation")).toBeInTheDocument();
      expect(screen.getByText("Late annotation")).toBeInTheDocument();
    });

    it("applies correct text color from color token", () => {
      render(
        <CinemaStage aria-label="Test">
          <StaticSceneRenderer scene={mockScene} />
        </CinemaStage>,
      );

      const text = screen.getByText("Growth trend");
      expect(text.getAttribute("fill")).toBe(
        "rgb(var(--tp-color-text-primary))",
      );
    });
  });

  describe("accessibility", () => {
    it("has scene group with aria-label", () => {
      render(
        <CinemaStage aria-label="Test">
          <StaticSceneRenderer scene={mockScene} />
        </CinemaStage>,
      );

      expect(screen.getByLabelText("Scene: Test Scene")).toBeInTheDocument();
    });

    it("has annotations group with aria-label", () => {
      render(
        <CinemaStage aria-label="Test">
          <StaticSceneRenderer scene={mockScene} />
        </CinemaStage>,
      );

      expect(screen.getByLabelText("Scene annotations")).toBeInTheDocument();
    });

    it("annotation text has role status", () => {
      render(
        <CinemaStage aria-label="Test">
          <StaticSceneRenderer scene={mockScene} />
        </CinemaStage>,
      );

      const text = screen.getByText("Growth trend");
      expect(text.getAttribute("role")).toBe("status");
    });
  });

  describe("edge cases", () => {
    it("handles empty annotations array", () => {
      const sceneNoAnnotations: CinemaScene = {
        ...mockScene,
        annotations: [],
      };

      render(
        <CinemaStage aria-label="Test">
          <StaticSceneRenderer scene={sceneNoAnnotations} />
        </CinemaStage>,
      );

      expect(screen.getByLabelText("Trend line for Rust")).toBeInTheDocument();
    });

    it("handles empty points array", () => {
      const sceneEmptyPoints: CinemaScene = {
        ...mockScene,
        trends: [
          {
            id: "empty",
            label: "Empty",
            colorToken: "action-primary",
            points: [],
          },
        ],
      };

      render(
        <CinemaStage aria-label="Test">
          <StaticSceneRenderer scene={sceneEmptyPoints} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText("Trend line for Empty");
      expect(path.getAttribute("d")).toBe("");
    });

    it("handles single point trend", () => {
      const sceneSinglePoint: CinemaScene = {
        ...mockScene,
        trends: [
          {
            id: "single",
            label: "Single",
            colorToken: "action-primary",
            points: [{ x: 0.5, y: 0.5 }],
          },
        ],
      };

      render(
        <CinemaStage aria-label="Test">
          <StaticSceneRenderer scene={sceneSinglePoint} />
        </CinemaStage>,
      );

      const path = screen.getByLabelText("Trend line for Single");
      expect(path.getAttribute("d")).toMatch(/^M 100,50\s*$/);
    });
  });
});
