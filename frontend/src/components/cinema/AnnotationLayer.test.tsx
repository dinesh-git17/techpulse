/**
 * Tests for the AnnotationLayer component.
 *
 * Validates coordinated rendering of multiple annotations,
 * scene timer integration, and phase handling.
 *
 * @module components/cinema/AnnotationLayer.test
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { AnnotationLayer } from "./AnnotationLayer";
import { CinemaStage } from "./CinemaStage";
import type { CinemaScene } from "./types";

/**
 * Factory to create valid test scenes with annotations.
 */
function createTestScene(overrides: Partial<CinemaScene> = {}): CinemaScene {
  return {
    id: `scene-${Math.random().toString(36).slice(2, 9)}`,
    title: "Test Scene",
    duration: 5000,
    morphDuration: 500,
    trends: [
      {
        id: "trend-1",
        label: "Test Trend",
        colorToken: "action-primary",
        points: [
          { x: 0, y: 0.2 },
          { x: 0.5, y: 0.6 },
          { x: 1, y: 0.4 },
        ],
      },
    ],
    annotations: [
      {
        text: "First annotation",
        anchor: { x: 0.3, y: 0.5 },
        enterDelay: 0,
        duration: 2000,
      },
      {
        text: "Second annotation",
        anchor: { x: 0.7, y: 0.5 },
        enterDelay: 1000,
        duration: 2000,
      },
    ],
    ...overrides,
  };
}

describe("AnnotationLayer", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("rendering", () => {
    it("renders null when scene is null", () => {
      const { container } = render(
        <CinemaStage aria-label="Test">
          <AnnotationLayer scene={null} phase="displaying" isPlaying={true} />
        </CinemaStage>,
      );

      const groups = container.querySelectorAll("g[aria-label]");
      expect(groups.length).toBe(0);
    });

    it("renders a group element for annotations", () => {
      const scene = createTestScene();

      const { container } = render(
        <CinemaStage aria-label="Test">
          <AnnotationLayer scene={scene} phase="displaying" isPlaying={true} />
        </CinemaStage>,
      );

      const group = container.querySelector(
        "g[aria-label='Scene annotations']",
      );
      expect(group).toBeInTheDocument();
    });

    it("renders annotations with zero enterDelay immediately", async () => {
      const scene = createTestScene({
        annotations: [
          {
            text: "Immediate annotation",
            anchor: { x: 0.5, y: 0.5 },
            enterDelay: 0,
            duration: 2000,
          },
        ],
      });

      render(
        <CinemaStage aria-label="Test">
          <AnnotationLayer scene={scene} phase="displaying" isPlaying={true} />
        </CinemaStage>,
      );

      expect(screen.getByText("Immediate annotation")).toBeInTheDocument();
    });

    it("renders multiple annotations from scene", async () => {
      const scene = createTestScene({
        annotations: [
          {
            text: "Annotation A",
            anchor: { x: 0.3, y: 0.5 },
            enterDelay: 0,
            duration: 5000,
          },
          {
            text: "Annotation B",
            anchor: { x: 0.7, y: 0.5 },
            enterDelay: 0,
            duration: 5000,
          },
        ],
      });

      render(
        <CinemaStage aria-label="Test">
          <AnnotationLayer scene={scene} phase="displaying" isPlaying={true} />
        </CinemaStage>,
      );

      expect(screen.getByText("Annotation A")).toBeInTheDocument();
      expect(screen.getByText("Annotation B")).toBeInTheDocument();
    });

    it("handles scene with no annotations", () => {
      const scene = createTestScene({ annotations: [] });

      const { container } = render(
        <CinemaStage aria-label="Test">
          <AnnotationLayer scene={scene} phase="displaying" isPlaying={true} />
        </CinemaStage>,
      );

      const group = container.querySelector(
        "g[aria-label='Scene annotations']",
      );
      expect(group).toBeInTheDocument();
      expect(group?.children.length).toBe(0);
    });
  });

  describe("morphing phase", () => {
    it("hides all annotations during morphing phase", () => {
      const scene = createTestScene({
        annotations: [
          {
            text: "Should be hidden",
            anchor: { x: 0.5, y: 0.5 },
            enterDelay: 0,
            duration: 5000,
          },
        ],
      });

      render(
        <CinemaStage aria-label="Test">
          <AnnotationLayer scene={scene} phase="morphing" isPlaying={true} />
        </CinemaStage>,
      );

      expect(screen.queryByText("Should be hidden")).not.toBeInTheDocument();
    });
  });

  describe("color token", () => {
    it("applies custom colorToken to annotations", () => {
      const scene = createTestScene({
        annotations: [
          {
            text: "Colored annotation",
            anchor: { x: 0.5, y: 0.5 },
            enterDelay: 0,
            duration: 5000,
          },
        ],
      });

      render(
        <CinemaStage aria-label="Test">
          <AnnotationLayer
            scene={scene}
            phase="displaying"
            isPlaying={true}
            colorToken="status-success"
          />
        </CinemaStage>,
      );

      const text = screen.getByText("Colored annotation");
      expect(text.getAttribute("fill")).toBe(
        "rgb(var(--tp-color-status-success))",
      );
    });

    it("uses text-primary as default colorToken", () => {
      const scene = createTestScene({
        annotations: [
          {
            text: "Default colored",
            anchor: { x: 0.5, y: 0.5 },
            enterDelay: 0,
            duration: 5000,
          },
        ],
      });

      render(
        <CinemaStage aria-label="Test">
          <AnnotationLayer scene={scene} phase="displaying" isPlaying={true} />
        </CinemaStage>,
      );

      const text = screen.getByText("Default colored");
      expect(text.getAttribute("fill")).toBe(
        "rgb(var(--tp-color-text-primary))",
      );
    });
  });

  describe("accessibility", () => {
    it("renders annotation group with proper role", () => {
      const scene = createTestScene();

      const { container } = render(
        <CinemaStage aria-label="Test">
          <AnnotationLayer scene={scene} phase="displaying" isPlaying={true} />
        </CinemaStage>,
      );

      const group = container.querySelector("g[role='group']");
      expect(group).toBeInTheDocument();
    });

    it("provides accessible label for annotation group", () => {
      const scene = createTestScene();

      const { container } = render(
        <CinemaStage aria-label="Test">
          <AnnotationLayer scene={scene} phase="displaying" isPlaying={true} />
        </CinemaStage>,
      );

      const group = container.querySelector(
        "g[aria-label='Scene annotations']",
      );
      expect(group).toBeInTheDocument();
    });
  });

  describe("scene changes", () => {
    it("resets timer when scene changes", async () => {
      const scene1 = createTestScene({
        id: "scene-1",
        annotations: [
          {
            text: "Scene 1 annotation",
            anchor: { x: 0.5, y: 0.5 },
            enterDelay: 0,
            duration: 5000,
          },
        ],
      });

      const scene2 = createTestScene({
        id: "scene-2",
        annotations: [
          {
            text: "Scene 2 annotation",
            anchor: { x: 0.5, y: 0.5 },
            enterDelay: 0,
            duration: 5000,
          },
        ],
      });

      const { rerender } = render(
        <CinemaStage aria-label="Test">
          <AnnotationLayer scene={scene1} phase="displaying" isPlaying={true} />
        </CinemaStage>,
      );

      expect(screen.getByText("Scene 1 annotation")).toBeInTheDocument();

      rerender(
        <CinemaStage aria-label="Test">
          <AnnotationLayer scene={scene2} phase="displaying" isPlaying={true} />
        </CinemaStage>,
      );

      expect(screen.queryByText("Scene 1 annotation")).not.toBeInTheDocument();
      expect(screen.getByText("Scene 2 annotation")).toBeInTheDocument();
    });
  });

  describe("playing state", () => {
    it("handles isPlaying false without error", () => {
      const scene = createTestScene({
        annotations: [
          {
            text: "Paused annotation",
            anchor: { x: 0.5, y: 0.5 },
            enterDelay: 0,
            duration: 5000,
          },
        ],
      });

      expect(() => {
        render(
          <CinemaStage aria-label="Test">
            <AnnotationLayer
              scene={scene}
              phase="displaying"
              isPlaying={false}
            />
          </CinemaStage>,
        );
      }).not.toThrow();
    });
  });
});
