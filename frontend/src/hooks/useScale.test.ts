/**
 * Tests for the useScale coordinate mapping hook.
 *
 * Validates that normalized [0-1] domain values are correctly transformed
 * to Cinema Stage viewBox coordinates (200x100 units) with proper Y-axis inversion.
 *
 * @module hooks/useScale.test
 */

import { renderHook } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { useScale, CINEMA_VIEWBOX, CINEMA_VIEWBOX_STRING } from "./useScale";

describe("useScale", () => {
  describe("constants", () => {
    it("defines viewBox with 2:1 aspect ratio", () => {
      expect(CINEMA_VIEWBOX.width / CINEMA_VIEWBOX.height).toBe(2);
    });

    it("exports correct viewBox dimensions", () => {
      expect(CINEMA_VIEWBOX.minX).toBe(0);
      expect(CINEMA_VIEWBOX.minY).toBe(0);
      expect(CINEMA_VIEWBOX.width).toBe(200);
      expect(CINEMA_VIEWBOX.height).toBe(100);
    });

    it("exports formatted viewBox string", () => {
      expect(CINEMA_VIEWBOX_STRING).toBe("0 0 200 100");
    });
  });

  describe("scaleX", () => {
    it("maps 0 to left edge (0)", () => {
      const { result } = renderHook(() => useScale());
      expect(result.current.scaleX(0)).toBe(0);
    });

    it("maps 1 to right edge (200)", () => {
      const { result } = renderHook(() => useScale());
      expect(result.current.scaleX(1)).toBe(200);
    });

    it("maps 0.5 to center (100)", () => {
      const { result } = renderHook(() => useScale());
      expect(result.current.scaleX(0.5)).toBe(100);
    });

    it("maps 0.25 to quarter position (50)", () => {
      const { result } = renderHook(() => useScale());
      expect(result.current.scaleX(0.25)).toBe(50);
    });

    it("maps 0.75 to three-quarter position (150)", () => {
      const { result } = renderHook(() => useScale());
      expect(result.current.scaleX(0.75)).toBe(150);
    });

    it("handles small fractional values", () => {
      const { result } = renderHook(() => useScale());
      expect(result.current.scaleX(0.1)).toBeCloseTo(20);
      expect(result.current.scaleX(0.01)).toBeCloseTo(2);
    });
  });

  describe("scaleY", () => {
    it("maps 0 (bottom) to viewBox bottom (100)", () => {
      const { result } = renderHook(() => useScale());
      expect(result.current.scaleY(0)).toBe(100);
    });

    it("maps 1 (top) to viewBox top (0)", () => {
      const { result } = renderHook(() => useScale());
      expect(result.current.scaleY(1)).toBe(0);
    });

    it("maps 0.5 to vertical center (50)", () => {
      const { result } = renderHook(() => useScale());
      expect(result.current.scaleY(0.5)).toBe(50);
    });

    it("maps 0.25 to lower quarter (75)", () => {
      const { result } = renderHook(() => useScale());
      expect(result.current.scaleY(0.25)).toBe(75);
    });

    it("maps 0.75 to upper quarter (25)", () => {
      const { result } = renderHook(() => useScale());
      expect(result.current.scaleY(0.75)).toBe(25);
    });

    it("correctly inverts Y-axis for data visualization", () => {
      const { result } = renderHook(() => useScale());
      const lowY = result.current.scaleY(0.2);
      const highY = result.current.scaleY(0.8);
      expect(lowY).toBeGreaterThan(highY);
    });
  });

  describe("scalePoint", () => {
    it("maps origin (0,0) to bottom-left", () => {
      const { result } = renderHook(() => useScale());
      const point = result.current.scalePoint({ x: 0, y: 0 });
      expect(point.x).toBe(0);
      expect(point.y).toBe(100);
    });

    it("maps (1,1) to top-right", () => {
      const { result } = renderHook(() => useScale());
      const point = result.current.scalePoint({ x: 1, y: 1 });
      expect(point.x).toBe(200);
      expect(point.y).toBe(0);
    });

    it("maps (0,1) to top-left", () => {
      const { result } = renderHook(() => useScale());
      const point = result.current.scalePoint({ x: 0, y: 1 });
      expect(point.x).toBe(0);
      expect(point.y).toBe(0);
    });

    it("maps (1,0) to bottom-right", () => {
      const { result } = renderHook(() => useScale());
      const point = result.current.scalePoint({ x: 1, y: 0 });
      expect(point.x).toBe(200);
      expect(point.y).toBe(100);
    });

    it("maps center point (0.5,0.5)", () => {
      const { result } = renderHook(() => useScale());
      const point = result.current.scalePoint({ x: 0.5, y: 0.5 });
      expect(point.x).toBe(100);
      expect(point.y).toBe(50);
    });

    it("handles arbitrary normalized coordinates", () => {
      const { result } = renderHook(() => useScale());
      const point = result.current.scalePoint({ x: 0.3, y: 0.7 });
      expect(point.x).toBeCloseTo(60);
      expect(point.y).toBeCloseTo(30);
    });
  });

  describe("viewBox metadata", () => {
    it("returns viewBox width", () => {
      const { result } = renderHook(() => useScale());
      expect(result.current.viewBoxWidth).toBe(200);
    });

    it("returns viewBox height", () => {
      const { result } = renderHook(() => useScale());
      expect(result.current.viewBoxHeight).toBe(100);
    });

    it("returns viewBox string for SVG attribute", () => {
      const { result } = renderHook(() => useScale());
      expect(result.current.viewBoxString).toBe("0 0 200 100");
    });
  });

  describe("function stability", () => {
    it("scaleX returns consistent results", () => {
      const { result, rerender } = renderHook(() => useScale());
      const firstResult = result.current.scaleX(0.5);
      rerender();
      const secondResult = result.current.scaleX(0.5);
      expect(firstResult).toBe(secondResult);
    });

    it("scaleY returns consistent results", () => {
      const { result, rerender } = renderHook(() => useScale());
      const firstResult = result.current.scaleY(0.5);
      rerender();
      const secondResult = result.current.scaleY(0.5);
      expect(firstResult).toBe(secondResult);
    });

    it("scalePoint returns consistent results", () => {
      const { result, rerender } = renderHook(() => useScale());
      const firstResult = result.current.scalePoint({ x: 0.5, y: 0.5 });
      rerender();
      const secondResult = result.current.scalePoint({ x: 0.5, y: 0.5 });
      expect(firstResult).toEqual(secondResult);
    });
  });

  describe("edge cases", () => {
    it("handles values at exact boundaries", () => {
      const { result } = renderHook(() => useScale());

      expect(result.current.scaleX(0)).toBe(0);
      expect(result.current.scaleX(1)).toBe(200);
      expect(result.current.scaleY(0)).toBe(100);
      expect(result.current.scaleY(1)).toBe(0);
    });

    it("handles very small normalized values", () => {
      const { result } = renderHook(() => useScale());

      expect(result.current.scaleX(0.001)).toBeCloseTo(0.2);
      expect(result.current.scaleY(0.001)).toBeCloseTo(99.9);
    });

    it("handles values very close to 1", () => {
      const { result } = renderHook(() => useScale());

      expect(result.current.scaleX(0.999)).toBeCloseTo(199.8);
      expect(result.current.scaleY(0.999)).toBeCloseTo(0.1);
    });
  });
});
