/**
 * @fileoverview Typography Token Validation Tests
 *
 * Validates that the TechPulse typography system is correctly configured:
 * - Type scale includes micro sizes (11px, 12px)
 * - Font-feature-settings are applied globally
 * - CSS variables follow proper naming conventions
 * - All expected type scale steps are defined
 */
import fs from "node:fs";
import path from "node:path";

import { beforeAll, describe, expect, it } from "vitest";

import {
  FONT_FEATURES,
  FONT_STACKS,
  MICRO_SIZES,
  TYPE_SCALE,
  TYPE_SCALE_NAMES,
  getTextClassName,
  getTypeScaleStep,
} from "./typographyTokens";

const GLOBALS_CSS_PATH = path.resolve(__dirname, "../app/globals.css");

describe("Typography Token Configuration", () => {
  describe("Token Registry", () => {
    it("defines all required type scale steps", () => {
      const expectedSteps = [
        "micro-xs",
        "micro",
        "xs",
        "sm",
        "base",
        "lg",
        "xl",
        "2xl",
        "3xl",
        "4xl",
        "5xl",
      ];
      expect(TYPE_SCALE_NAMES).toEqual(expectedSteps);
    });

    it("includes micro sizes at 11px and 12px", () => {
      expect(MICRO_SIZES).toHaveLength(2);
      const microXs = MICRO_SIZES.find((s) => s.name === "micro-xs");
      const micro = MICRO_SIZES.find((s) => s.name === "micro");

      expect(microXs?.sizePx).toBe(11);
      expect(micro?.sizePx).toBe(12);
    });

    it("defines both font stacks (sans and mono)", () => {
      expect(FONT_STACKS.sans).toBeDefined();
      expect(FONT_STACKS.mono).toBeDefined();
      expect(FONT_STACKS.sans.name).toBe("Geist Sans");
      expect(FONT_STACKS.mono.name).toBe("Geist Mono");
    });

    it("defines required font features (tnum, zero, ss01)", () => {
      expect(FONT_FEATURES.tnum).toBeDefined();
      expect(FONT_FEATURES.zero).toBeDefined();
      expect(FONT_FEATURES.ss01).toBeDefined();
    });
  });

  describe("Type Scale Properties", () => {
    it.each(TYPE_SCALE)("$name has valid rem size", ({ sizeRem }) => {
      expect(sizeRem).toMatch(/^\d+(\.\d+)?rem$/);
    });

    it.each(TYPE_SCALE)("$name has valid line height", ({ lineHeight }) => {
      expect(lineHeight).toMatch(/^(\d+(\.\d+)?rem|\d+(\.\d+)?)$/);
    });

    it.each(TYPE_SCALE)(
      "$name has valid Tailwind class",
      ({ tailwindClass }) => {
        expect(tailwindClass).toMatch(/^text-[\w-]+$/);
      },
    );

    it.each(TYPE_SCALE)("$name has CSS variable defined", ({ sizeVar }) => {
      expect(sizeVar).toMatch(/^--text-[\w-]+$/);
    });
  });

  describe("Helper Functions", () => {
    it("getTypeScaleStep returns correct step for valid name", () => {
      const step = getTypeScaleStep("base");
      expect(step?.sizePx).toBe(16);
      expect(step?.tailwindClass).toBe("text-base");
    });

    it("getTypeScaleStep returns undefined for invalid name", () => {
      const step = getTypeScaleStep("invalid");
      expect(step).toBeUndefined();
    });

    it("getTextClassName returns correct class for valid name", () => {
      expect(getTextClassName("micro")).toBe("text-micro");
      expect(getTextClassName("2xl")).toBe("text-2xl");
    });

    it("getTextClassName returns undefined for invalid name", () => {
      expect(getTextClassName("invalid")).toBeUndefined();
    });
  });

  describe("globals.css Integration", () => {
    let globalsContent: string;

    beforeAll(() => {
      globalsContent = fs.readFileSync(GLOBALS_CSS_PATH, "utf-8");
    });

    it("exists and is readable", () => {
      expect(globalsContent).toBeDefined();
      expect(globalsContent.length).toBeGreaterThan(0);
    });

    describe("Font Feature Settings", () => {
      it("applies tnum (tabular numbers) globally", () => {
        expect(globalsContent).toContain('"tnum" on');
      });

      it("applies zero (slashed zero) globally", () => {
        expect(globalsContent).toContain('"zero" on');
      });

      it("applies ss01 (stylistic set) globally", () => {
        expect(globalsContent).toContain('"ss01" on');
      });

      it("sets font-feature-settings on html element", () => {
        const pattern = /html\s*\{[^}]*font-feature-settings:/;
        expect(pattern.test(globalsContent)).toBe(true);
      });

      it("applies tabular-nums to numeric elements", () => {
        expect(globalsContent).toContain("font-variant-numeric: tabular-nums");
      });
    });

    describe("Type Scale CSS Variables", () => {
      it.each([
        ["--text-micro-xs", "0.6875rem"],
        ["--text-micro", "0.75rem"],
        ["--text-xs", "0.8125rem"],
        ["--text-sm", "0.875rem"],
        ["--text-base", "1rem"],
        ["--text-lg", "1.125rem"],
        ["--text-xl", "1.25rem"],
        ["--text-2xl", "1.5rem"],
        ["--text-3xl", "1.875rem"],
        ["--text-4xl", "2.25rem"],
        ["--text-5xl", "3rem"],
      ])("declares %s with value %s", (varName, expectedValue) => {
        expect(globalsContent).toContain(`${varName}: ${expectedValue}`);
      });

      it.each([
        ["--text-micro-xs--line-height", "1rem"],
        ["--text-micro--line-height", "1.125rem"],
        ["--text-base--line-height", "1.5rem"],
      ])("declares line-height %s with value %s", (varName, expectedValue) => {
        expect(globalsContent).toContain(`${varName}: ${expectedValue}`);
      });
    });

    describe("Font Stack Configuration", () => {
      it("maps --font-sans to Geist Sans variable", () => {
        expect(globalsContent).toContain("--font-sans: var(--font-geist-sans)");
      });

      it("maps --font-mono to Geist Mono variable", () => {
        expect(globalsContent).toContain("--font-mono: var(--font-geist-mono)");
      });
    });

    describe("Tailwind Theme Integration", () => {
      it("configures @theme inline block", () => {
        expect(globalsContent).toContain("@theme inline");
      });

      it("includes typography section comment", () => {
        expect(globalsContent).toContain("Data Dense");
      });
    });
  });

  describe("Data Density Requirements", () => {
    it("micro-xs (11px) has generous line-height for readability", () => {
      const microXs = getTypeScaleStep("micro-xs");
      expect(microXs).toBeDefined();
      if (!microXs) return;

      const lineHeightRem = parseFloat(microXs.lineHeight);
      const fontSizeRem = parseFloat(microXs.sizeRem);
      const ratio = lineHeightRem / fontSizeRem;

      expect(ratio).toBeGreaterThanOrEqual(1.4);
    });

    it("micro (12px) has generous line-height for readability", () => {
      const micro = getTypeScaleStep("micro");
      expect(micro).toBeDefined();
      if (!micro) return;

      const lineHeightRem = parseFloat(micro.lineHeight);
      const fontSizeRem = parseFloat(micro.sizeRem);
      const ratio = lineHeightRem / fontSizeRem;

      expect(ratio).toBeGreaterThanOrEqual(1.4);
    });

    it("heading sizes have tighter line-heights", () => {
      const heading4xl = getTypeScaleStep("4xl");
      expect(heading4xl).toBeDefined();
      if (!heading4xl) return;

      const lineHeightRem = parseFloat(heading4xl.lineHeight);
      const fontSizeRem = parseFloat(heading4xl.sizeRem);
      const ratio = lineHeightRem / fontSizeRem;

      expect(ratio).toBeLessThanOrEqual(1.2);
    });
  });
});
