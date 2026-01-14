/**
 * Tests for the StaticFallback placeholder component.
 *
 * Validates rendering, accessibility, and visual consistency
 * of the branded fallback for data loading failures.
 *
 * @module components/cinema/StaticFallback.test
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { StaticFallback } from "./StaticFallback";

describe("StaticFallback", () => {
  describe("rendering", () => {
    it("renders an SVG element", () => {
      render(<StaticFallback />);

      const svg = screen.getByRole("img");
      expect(svg.tagName.toLowerCase()).toBe("svg");
    });

    it("renders a path element for the trend line", () => {
      render(<StaticFallback />);

      const svg = screen.getByRole("img");
      const path = svg.querySelector("path");
      expect(path).toBeInTheDocument();
    });

    it("renders with dashed stroke for visual distinction", () => {
      render(<StaticFallback />);

      const svg = screen.getByRole("img");
      const path = svg.querySelector("path");
      expect(path?.getAttribute("stroke-dasharray")).toBe("6 4");
    });

    it("renders loading text", () => {
      render(<StaticFallback />);

      const svg = screen.getByRole("img");
      const text = svg.querySelector("text");
      expect(text?.textContent).toBe("Data loading...");
    });
  });

  describe("aspect ratio", () => {
    it("maintains 2:1 aspect ratio", () => {
      render(<StaticFallback />);

      const container = screen.getByRole("img").parentElement;
      expect(container?.style.aspectRatio).toBe("2 / 1");
    });
  });

  describe("viewBox", () => {
    it("uses correct viewBox dimensions", () => {
      render(<StaticFallback />);

      const svg = screen.getByRole("img");
      expect(svg.getAttribute("viewBox")).toBe("0 0 200 100");
    });

    it("uses centered aspect ratio preservation", () => {
      render(<StaticFallback />);

      const svg = screen.getByRole("img");
      expect(svg.getAttribute("preserveAspectRatio")).toBe("xMidYMid meet");
    });
  });

  describe("accessibility", () => {
    it("has role img", () => {
      render(<StaticFallback />);

      expect(screen.getByRole("img")).toBeInTheDocument();
    });

    it("has default aria-label", () => {
      render(<StaticFallback />);

      expect(
        screen.getByLabelText("Trend visualization temporarily unavailable"),
      ).toBeInTheDocument();
    });

    it("accepts custom aria-label", () => {
      render(<StaticFallback aria-label="Custom fallback message" />);

      expect(
        screen.getByLabelText("Custom fallback message"),
      ).toBeInTheDocument();
    });
  });

  describe("styling", () => {
    it("accepts custom className", () => {
      render(<StaticFallback className="custom-class" />);

      const container = screen.getByRole("img").parentElement;
      expect(container?.className).toContain("custom-class");
    });

    it("includes relative positioning class", () => {
      render(<StaticFallback />);

      const container = screen.getByRole("img").parentElement;
      expect(container?.className).toContain("relative");
    });

    it("includes full width class", () => {
      render(<StaticFallback />);

      const container = screen.getByRole("img").parentElement;
      expect(container?.className).toContain("w-full");
    });
  });

  describe("gradient", () => {
    it("defines a linear gradient for the path", () => {
      render(<StaticFallback />);

      const svg = screen.getByRole("img");
      const gradient = svg.querySelector("#fallback-gradient");
      expect(gradient).toBeInTheDocument();
      expect(gradient?.tagName.toLowerCase()).toBe("lineargradient");
    });

    it("uses gradient for path stroke", () => {
      render(<StaticFallback />);

      const svg = screen.getByRole("img");
      const path = svg.querySelector("path");
      expect(path?.getAttribute("stroke")).toBe("url(#fallback-gradient)");
    });
  });
});
