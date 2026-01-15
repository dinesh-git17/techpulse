/**
 * Tests for the CinemaStage SVG container component.
 *
 * Validates responsive rendering, viewBox configuration, and accessibility
 * attributes for the Cinema visualization coordinate system.
 *
 * @module components/cinema/CinemaStage.test
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { CINEMA_VIEWBOX_STRING } from "@/hooks/useScale";

import { CinemaStage } from "./CinemaStage";

describe("CinemaStage", () => {
  describe("SVG container", () => {
    it("renders an SVG element", () => {
      render(<CinemaStage aria-label="Test visualization" />);

      const svg = screen.getByRole("img", { name: "Test visualization" });
      expect(svg.tagName.toLowerCase()).toBe("svg");
    });

    it("applies correct viewBox for 2:1 coordinate system", () => {
      render(<CinemaStage aria-label="Test visualization" />);

      const svg = screen.getByRole("img", { name: "Test visualization" });
      expect(svg.getAttribute("viewBox")).toBe(CINEMA_VIEWBOX_STRING);
      expect(svg.getAttribute("viewBox")).toBe("0 0 200 100");
    });

    it("uses xMidYMid meet for centered scaling", () => {
      render(<CinemaStage aria-label="Test visualization" />);

      const svg = screen.getByRole("img", { name: "Test visualization" });
      expect(svg.getAttribute("preserveAspectRatio")).toBe("xMidYMid meet");
    });
  });

  describe("aspect ratio", () => {
    it("container has 2:1 aspect ratio style", () => {
      const { container } = render(<CinemaStage />);

      const wrapper = container.firstElementChild;
      expect(wrapper).toHaveStyle({ aspectRatio: "2 / 1" });
    });

    it("container has relative positioning for SVG overlay", () => {
      const { container } = render(<CinemaStage />);

      const wrapper = container.firstElementChild;
      expect(wrapper).toHaveClass("relative");
    });

    it("SVG fills container absolutely", () => {
      render(<CinemaStage aria-label="Test visualization" />);

      const svg = screen.getByRole("img", { name: "Test visualization" });
      expect(svg).toHaveClass("absolute", "inset-0", "h-full", "w-full");
    });
  });

  describe("children rendering", () => {
    it("renders child elements within SVG", () => {
      render(
        <CinemaStage aria-label="Test visualization">
          <circle data-testid="test-circle" cx={100} cy={50} r={10} />
        </CinemaStage>,
      );

      expect(screen.getByTestId("test-circle")).toBeInTheDocument();
    });

    it("renders multiple child elements", () => {
      render(
        <CinemaStage aria-label="Test visualization">
          <circle data-testid="circle-1" cx={50} cy={50} r={5} />
          <circle data-testid="circle-2" cx={150} cy={50} r={5} />
          <path data-testid="test-path" d="M0,100 L200,0" />
        </CinemaStage>,
      );

      expect(screen.getByTestId("circle-1")).toBeInTheDocument();
      expect(screen.getByTestId("circle-2")).toBeInTheDocument();
      expect(screen.getByTestId("test-path")).toBeInTheDocument();
    });

    it("renders with no children", () => {
      const { container } = render(<CinemaStage />);
      expect(container.querySelector("svg")).toBeInTheDocument();
    });
  });

  describe("accessibility", () => {
    it("applies aria-label to SVG element", () => {
      render(<CinemaStage aria-label="Technology trend comparison" />);

      const svg = screen.getByRole("img", {
        name: "Technology trend comparison",
      });
      expect(svg).toBeInTheDocument();
    });

    it("has img role for screen readers", () => {
      render(<CinemaStage aria-label="Chart visualization" />);

      const svg = screen.getByRole("img");
      expect(svg).toBeInTheDocument();
    });
  });

  describe("className prop", () => {
    it("applies custom className to container", () => {
      const { container } = render(<CinemaStage className="custom-class" />);

      const wrapper = container.firstElementChild;
      expect(wrapper).toHaveClass("custom-class");
    });

    it("preserves default classes with custom className", () => {
      const { container } = render(<CinemaStage className="custom-class" />);

      const wrapper = container.firstElementChild;
      expect(wrapper).toHaveClass("relative", "w-full", "custom-class");
    });

    it("handles undefined className gracefully", () => {
      const { container } = render(<CinemaStage />);

      const wrapper = container.firstElementChild;
      expect(wrapper).toHaveClass("relative", "w-full");
    });
  });

  describe("coordinate system verification", () => {
    it("viewBox width is 200 (2x multiplier for 2:1 ratio)", () => {
      render(<CinemaStage aria-label="Test" />);

      const svg = screen.getByRole("img", { name: "Test" });
      const viewBox = svg.getAttribute("viewBox");
      expect(viewBox).not.toBeNull();
      const [, , width] = (viewBox ?? "").split(" ").map(Number);
      expect(width).toBe(200);
    });

    it("viewBox height is 100 (base unit for 2:1 ratio)", () => {
      render(<CinemaStage aria-label="Test" />);

      const svg = screen.getByRole("img", { name: "Test" });
      const viewBox = svg.getAttribute("viewBox");
      expect(viewBox).not.toBeNull();
      const [, , , height] = (viewBox ?? "").split(" ").map(Number);
      expect(height).toBe(100);
    });

    it("viewBox origin is (0,0)", () => {
      render(<CinemaStage aria-label="Test" />);

      const svg = screen.getByRole("img", { name: "Test" });
      const viewBox = svg.getAttribute("viewBox");
      expect(viewBox).not.toBeNull();
      const [minX, minY] = (viewBox ?? "").split(" ").map(Number);
      expect(minX).toBe(0);
      expect(minY).toBe(0);
    });
  });
});
