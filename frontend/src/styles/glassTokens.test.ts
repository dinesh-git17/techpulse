/**
 * @fileoverview Glass Token Validation Tests
 *
 * Validates that the TechPulse glass utility system is correctly configured:
 * - Glass tier definitions are complete
 * - CSS utilities are defined in globals.css
 * - Backdrop-filter values are correctly applied
 * - Accessibility fallbacks are configured
 */
import fs from "node:fs";
import path from "node:path";

import { beforeAll, describe, expect, it } from "vitest";

import {
  A11Y_MEDIA_QUERIES,
  BLUR_CLASSES,
  extractBlurClasses,
  FORCED_COLORS,
  getContrastRatiosForTier,
  getGlassClassName,
  getGlassContrastRatio,
  getGlassTier,
  GLASS_CLASS_NAMES,
  GLASS_CONTRAST_RATIOS,
  GLASS_TIERS,
  isBlurClass,
  isGlassClass,
  MAX_GLASS_NESTING_DEPTH,
  meetsWCAG_AA,
  meetsWCAG_AA_Large,
  NOISE_TEXTURE,
  REDUCED_TRANSPARENCY_FALLBACKS,
  SHIMMER_BORDER,
  WCAG_CONTRAST_THRESHOLDS,
} from "./glassTokens";

const GLOBALS_CSS_PATH = path.resolve(__dirname, "../app/globals.css");

describe("Glass Token Configuration", () => {
  describe("Token Registry", () => {
    it("defines exactly 3 glass tiers", () => {
      expect(GLASS_TIERS).toHaveLength(3);
    });

    it("defines all required tiers: subtle, panel, overlay", () => {
      const tierNames = GLASS_TIERS.map((tier) => tier.name);
      expect(tierNames).toContain("subtle");
      expect(tierNames).toContain("panel");
      expect(tierNames).toContain("overlay");
    });

    it("defines correct class names for each tier", () => {
      expect(getGlassClassName("subtle")).toBe("glass-subtle");
      expect(getGlassClassName("panel")).toBe("glass-panel");
      expect(getGlassClassName("overlay")).toBe("glass-overlay");
    });

    it("tiers have decreasing opacity (more blur = less opacity)", () => {
      const subtle = getGlassTier("subtle");
      const panel = getGlassTier("panel");
      const overlay = getGlassTier("overlay");

      expect(subtle?.opacity).toBeGreaterThan(panel?.opacity ?? 0);
      expect(panel?.opacity).toBeGreaterThan(overlay?.opacity ?? 0);
    });

    it("tiers have increasing blur intensity", () => {
      const blurOrder = [
        "backdrop-blur-sm",
        "backdrop-blur-md",
        "backdrop-blur-xl",
      ];
      const tierBlurs = GLASS_TIERS.map((tier) => tier.blur);

      expect(tierBlurs).toEqual(blurOrder);
    });

    it("panel and overlay tiers have shimmer border", () => {
      expect(getGlassTier("subtle")?.hasBorder).toBe(false);
      expect(getGlassTier("panel")?.hasBorder).toBe(true);
      expect(getGlassTier("overlay")?.hasBorder).toBe(true);
    });

    it("defines maximum nesting depth of 2", () => {
      expect(MAX_GLASS_NESTING_DEPTH).toBe(2);
    });

    it("defines shimmer border configuration", () => {
      expect(SHIMMER_BORDER.width).toBe("1px");
      expect(SHIMMER_BORDER.cssVar).toBe("--tp-color-border-glass");
      expect(SHIMMER_BORDER.opacity).toBe(0.1);
    });

    it("defines noise texture configuration", () => {
      expect(NOISE_TEXTURE.className).toBe("glass-noise");
      expect(NOISE_TEXTURE.svgFilter).toBe("fractalNoise");
      expect(NOISE_TEXTURE.baseFrequency).toBe(0.8);
      expect(NOISE_TEXTURE.numOctaves).toBe(4);
      expect(NOISE_TEXTURE.opacity).toBe(0.03);
    });
  });

  describe("Tier Properties", () => {
    it.each(GLASS_TIERS)("$name has valid class name", ({ className }) => {
      expect(className).toMatch(/^glass-[\w-]+$/);
    });

    it.each(GLASS_TIERS)("$name has blur configuration", ({ blur }) => {
      expect(blur).toMatch(/^backdrop-blur(-\w+)?$/);
    });

    it.each(GLASS_TIERS)(
      "$name has opacity between 0 and 100",
      ({ opacity }) => {
        expect(opacity).toBeGreaterThanOrEqual(0);
        expect(opacity).toBeLessThanOrEqual(100);
      },
    );

    it.each(GLASS_TIERS)("$name has a use case description", ({ useCase }) => {
      expect(useCase.length).toBeGreaterThan(0);
    });
  });

  describe("Helper Functions", () => {
    it("getGlassTier returns correct tier for valid name", () => {
      const tier = getGlassTier("panel");
      expect(tier?.className).toBe("glass-panel");
      expect(tier?.opacity).toBe(80);
    });

    it("getGlassTier returns undefined for invalid name", () => {
      const tier = getGlassTier("invalid");
      expect(tier).toBeUndefined();
    });

    it("getGlassClassName returns correct class for valid name", () => {
      expect(getGlassClassName("subtle")).toBe("glass-subtle");
      expect(getGlassClassName("overlay")).toBe("glass-overlay");
    });

    it("getGlassClassName returns undefined for invalid name", () => {
      expect(getGlassClassName("invalid")).toBeUndefined();
    });

    it("isGlassClass returns true for glass utility classes", () => {
      expect(isGlassClass("glass-subtle")).toBe(true);
      expect(isGlassClass("glass-panel")).toBe(true);
      expect(isGlassClass("glass-overlay")).toBe(true);
    });

    it("isGlassClass returns false for non-glass classes", () => {
      expect(isGlassClass("bg-red-500")).toBe(false);
      expect(isGlassClass("backdrop-blur")).toBe(false);
    });

    it("isBlurClass returns true for blur and glass classes", () => {
      expect(isBlurClass("backdrop-blur")).toBe(true);
      expect(isBlurClass("backdrop-blur-md")).toBe(true);
      expect(isBlurClass("glass-panel")).toBe(true);
    });

    it("isBlurClass returns false for non-blur classes", () => {
      expect(isBlurClass("bg-red-500")).toBe(false);
      expect(isBlurClass("text-primary")).toBe(false);
    });

    it("extractBlurClasses finds glass/blur classes in string", () => {
      const classes = extractBlurClasses("p-4 glass-panel rounded-lg");
      expect(classes).toContain("glass-panel");
      expect(classes).not.toContain("p-4");
    });

    it("extractBlurClasses returns empty array for no matches", () => {
      const classes = extractBlurClasses("p-4 rounded-lg bg-red-500");
      expect(classes).toHaveLength(0);
    });
  });

  describe("Blur Classes Registry", () => {
    it("includes all Tailwind backdrop-blur utilities", () => {
      expect(BLUR_CLASSES).toContain("backdrop-blur");
      expect(BLUR_CLASSES).toContain("backdrop-blur-none");
      expect(BLUR_CLASSES).toContain("backdrop-blur-sm");
      expect(BLUR_CLASSES).toContain("backdrop-blur-md");
      expect(BLUR_CLASSES).toContain("backdrop-blur-lg");
      expect(BLUR_CLASSES).toContain("backdrop-blur-xl");
      expect(BLUR_CLASSES).toContain("backdrop-blur-2xl");
      expect(BLUR_CLASSES).toContain("backdrop-blur-3xl");
    });

    it("includes all glass utility classes", () => {
      for (const className of GLASS_CLASS_NAMES) {
        expect(BLUR_CLASSES).toContain(className);
      }
    });
  });

  describe("Glass Class Names Registry", () => {
    it("includes all tier class names", () => {
      expect(GLASS_CLASS_NAMES).toContain("glass-subtle");
      expect(GLASS_CLASS_NAMES).toContain("glass-panel");
      expect(GLASS_CLASS_NAMES).toContain("glass-overlay");
    });

    it("has exactly 3 glass class names", () => {
      expect(GLASS_CLASS_NAMES).toHaveLength(3);
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

    describe("Glass Utility Classes", () => {
      it.each(GLASS_CLASS_NAMES)("defines .%s class", (className) => {
        expect(globalsContent).toContain(`.${className}`);
      });

      it("defines .glass-noise utility", () => {
        expect(globalsContent).toContain(".glass-noise");
      });

      it("defines .border-shimmer utility", () => {
        expect(globalsContent).toContain(".border-shimmer");
      });
    });

    describe("Backdrop Filter Values", () => {
      it("glass-subtle applies blur(4px)", () => {
        expect(globalsContent).toContain(".glass-subtle");
        expect(globalsContent).toContain("backdrop-filter: blur(4px)");
      });

      it("glass-panel applies blur(12px)", () => {
        expect(globalsContent).toContain(".glass-panel");
        expect(globalsContent).toContain("backdrop-filter: blur(12px)");
      });

      it("glass-overlay applies blur(24px)", () => {
        expect(globalsContent).toContain(".glass-overlay");
        expect(globalsContent).toContain("backdrop-filter: blur(24px)");
      });

      it("includes -webkit-backdrop-filter for Safari support", () => {
        expect(globalsContent).toContain("-webkit-backdrop-filter");
      });
    });

    describe("Background Opacity", () => {
      it("glass-subtle uses 90% opacity (0.9)", () => {
        expect(globalsContent).toContain("/ 0.9)");
      });

      it("glass-panel uses 80% opacity (0.8)", () => {
        expect(globalsContent).toContain("/ 0.8)");
      });

      it("glass-overlay uses 60% opacity (0.6)", () => {
        expect(globalsContent).toContain("/ 0.6)");
      });
    });

    describe("Shimmer Border", () => {
      it("glass-panel includes shimmer border", () => {
        expect(globalsContent).toContain("border-glass");
      });

      it("border-shimmer utility uses correct opacity", () => {
        expect(globalsContent).toContain("border-glass) / 0.1)");
      });
    });

    describe("Noise Texture", () => {
      it("noise texture uses SVG feTurbulence filter", () => {
        expect(globalsContent).toContain("feTurbulence");
        expect(globalsContent).toContain("fractalNoise");
      });

      it("noise texture has low opacity for subtlety", () => {
        expect(globalsContent).toContain("opacity: 0.03");
      });

      it("noise texture uses pointer-events: none", () => {
        expect(globalsContent).toContain("pointer-events: none");
      });

      it("glass-panel and glass-overlay include noise ::before pseudo-element", () => {
        expect(globalsContent).toContain(".glass-panel::before");
        expect(globalsContent).toContain(".glass-overlay::before");
      });
    });

    describe("Accessibility Fallbacks", () => {
      it("defines prefers-reduced-transparency media query", () => {
        expect(globalsContent).toContain(
          "prefers-reduced-transparency: reduce",
        );
      });

      it("removes backdrop-filter in reduced transparency mode", () => {
        expect(globalsContent).toContain("backdrop-filter: none");
      });

      it("provides solid fallback backgrounds", () => {
        expect(globalsContent).toContain(
          "rgb(var(--tp-color-surface-secondary))",
        );
        expect(globalsContent).toContain(
          "rgb(var(--tp-color-surface-tertiary))",
        );
        expect(globalsContent).toContain(
          "rgb(var(--tp-color-surface-elevated))",
        );
      });

      it("hides noise pseudo-elements in reduced transparency mode", () => {
        expect(globalsContent).toContain("display: none");
      });
    });

    describe("CSS Architecture", () => {
      it("uses --tp-color-* CSS variables", () => {
        expect(globalsContent).toContain("var(--tp-color-surface-primary)");
        expect(globalsContent).toContain("var(--tp-color-border-glass)");
      });

      it("glass classes set position: relative for ::before context", () => {
        expect(globalsContent).toContain("position: relative");
      });

      it("::before pseudo-elements use border-radius: inherit", () => {
        expect(globalsContent).toContain("border-radius: inherit");
      });
    });
  });

  describe("Design System Compliance", () => {
    it("tier opacity values follow the 90/80/60 scale", () => {
      expect(getGlassTier("subtle")?.opacity).toBe(90);
      expect(getGlassTier("panel")?.opacity).toBe(80);
      expect(getGlassTier("overlay")?.opacity).toBe(60);
    });

    it("tier blur values correspond to Tailwind's sm/md/xl scale", () => {
      expect(getGlassTier("subtle")?.blur).toBe("backdrop-blur-sm");
      expect(getGlassTier("panel")?.blur).toBe("backdrop-blur-md");
      expect(getGlassTier("overlay")?.blur).toBe("backdrop-blur-xl");
    });

    it("shimmer border uses --tp-color-border-glass variable", () => {
      expect(SHIMMER_BORDER.cssVar).toBe("--tp-color-border-glass");
    });
  });

  describe("Accessibility Configuration", () => {
    describe("A11y Media Queries", () => {
      it("defines reduced-transparency media query", () => {
        expect(A11Y_MEDIA_QUERIES.reducedTransparency).toBe(
          "prefers-reduced-transparency: reduce",
        );
      });

      it("defines forced-colors media query", () => {
        expect(A11Y_MEDIA_QUERIES.forcedColors).toBe("forced-colors: active");
      });
    });

    describe("Reduced Transparency Fallbacks", () => {
      it("defines fallback for each glass tier", () => {
        expect(REDUCED_TRANSPARENCY_FALLBACKS.subtle).toBe(
          "--tp-color-surface-secondary",
        );
        expect(REDUCED_TRANSPARENCY_FALLBACKS.panel).toBe(
          "--tp-color-surface-tertiary",
        );
        expect(REDUCED_TRANSPARENCY_FALLBACKS.overlay).toBe(
          "--tp-color-surface-elevated",
        );
      });

      it("fallback colors use --tp-color-* prefix", () => {
        for (const fallback of Object.values(REDUCED_TRANSPARENCY_FALLBACKS)) {
          expect(fallback).toMatch(/^--tp-color-/);
        }
      });
    });

    describe("Forced Colors Configuration", () => {
      it("uses CSS system color keywords", () => {
        expect(FORCED_COLORS.background).toBe("Canvas");
        expect(FORCED_COLORS.text).toBe("CanvasText");
        expect(FORCED_COLORS.border).toBe("CanvasText");
      });
    });

    describe("globals.css Forced Colors Integration", () => {
      let globalsContent: string;

      beforeAll(() => {
        globalsContent = fs.readFileSync(GLOBALS_CSS_PATH, "utf-8");
      });

      it("defines forced-colors media query", () => {
        expect(globalsContent).toContain("forced-colors: active");
      });

      it("removes backdrop-filter in forced-colors mode", () => {
        expect(globalsContent).toContain("forced-colors: active");
        expect(globalsContent).toContain("backdrop-filter: none");
      });

      it("uses Canvas system color for background", () => {
        expect(globalsContent).toContain("background: Canvas");
      });

      it("uses CanvasText for borders in forced-colors", () => {
        expect(globalsContent).toContain("1px solid CanvasText");
      });

      it("hides noise pseudo-elements in forced-colors mode", () => {
        const forcedColorsSection = globalsContent.slice(
          globalsContent.indexOf("forced-colors: active"),
        );
        expect(forcedColorsSection).toContain("display: none");
      });
    });
  });

  describe("Contrast Ratio Configuration", () => {
    describe("WCAG Thresholds", () => {
      it("defines AA normal text threshold as 4.5:1", () => {
        expect(WCAG_CONTRAST_THRESHOLDS.AA_NORMAL).toBe(4.5);
      });

      it("defines AA large text threshold as 3:1", () => {
        expect(WCAG_CONTRAST_THRESHOLDS.AA_LARGE).toBe(3.0);
      });

      it("defines AAA normal text threshold as 7:1", () => {
        expect(WCAG_CONTRAST_THRESHOLDS.AAA_NORMAL).toBe(7.0);
      });

      it("defines AAA large text threshold as 4.5:1", () => {
        expect(WCAG_CONTRAST_THRESHOLDS.AAA_LARGE).toBe(4.5);
      });
    });

    describe("Pre-calculated Contrast Ratios", () => {
      it("defines contrast ratios for all glass tiers", () => {
        const tiers = ["subtle", "panel", "overlay"];
        for (const tier of tiers) {
          const ratios = getContrastRatiosForTier(tier);
          expect(ratios.length).toBeGreaterThan(0);
        }
      });

      it("defines contrast ratios for text-primary on all tiers", () => {
        expect(getGlassContrastRatio("subtle", "text-primary")).toBeDefined();
        expect(getGlassContrastRatio("panel", "text-primary")).toBeDefined();
        expect(getGlassContrastRatio("overlay", "text-primary")).toBeDefined();
      });

      it("text-primary meets WCAG AA on all glass tiers", () => {
        for (const tier of ["subtle", "panel", "overlay"]) {
          const ratio = getGlassContrastRatio(tier, "text-primary");
          expect(ratio?.meetsAA).toBe(true);
        }
      });

      it("text-primary meets WCAG AAA on all glass tiers", () => {
        for (const tier of ["subtle", "panel", "overlay"]) {
          const ratio = getGlassContrastRatio(tier, "text-primary");
          expect(ratio?.meetsAAA).toBe(true);
        }
      });

      it("contrast ratios decrease with increased blur/transparency", () => {
        const subtle = getGlassContrastRatio("subtle", "text-primary");
        const panel = getGlassContrastRatio("panel", "text-primary");
        const overlay = getGlassContrastRatio("overlay", "text-primary");

        expect(subtle?.ratio).toBeGreaterThan(panel?.ratio ?? 0);
        expect(panel?.ratio).toBeGreaterThan(overlay?.ratio ?? 0);
      });

      it("has exactly 9 contrast ratio entries (3 tiers x 3 text colors)", () => {
        expect(GLASS_CONTRAST_RATIOS).toHaveLength(9);
      });
    });

    describe("Contrast Helper Functions", () => {
      it("meetsWCAG_AA returns true for ratios >= 4.5", () => {
        expect(meetsWCAG_AA(4.5)).toBe(true);
        expect(meetsWCAG_AA(7.0)).toBe(true);
        expect(meetsWCAG_AA(11.0)).toBe(true);
      });

      it("meetsWCAG_AA returns false for ratios < 4.5", () => {
        expect(meetsWCAG_AA(4.4)).toBe(false);
        expect(meetsWCAG_AA(3.0)).toBe(false);
        expect(meetsWCAG_AA(1.0)).toBe(false);
      });

      it("meetsWCAG_AA_Large returns true for ratios >= 3.0", () => {
        expect(meetsWCAG_AA_Large(3.0)).toBe(true);
        expect(meetsWCAG_AA_Large(4.5)).toBe(true);
        expect(meetsWCAG_AA_Large(7.0)).toBe(true);
      });

      it("meetsWCAG_AA_Large returns false for ratios < 3.0", () => {
        expect(meetsWCAG_AA_Large(2.9)).toBe(false);
        expect(meetsWCAG_AA_Large(2.0)).toBe(false);
        expect(meetsWCAG_AA_Large(1.0)).toBe(false);
      });

      it("getGlassContrastRatio returns undefined for invalid tier", () => {
        expect(
          getGlassContrastRatio("invalid", "text-primary"),
        ).toBeUndefined();
      });

      it("getGlassContrastRatio returns undefined for invalid text token", () => {
        expect(getGlassContrastRatio("subtle", "invalid")).toBeUndefined();
      });

      it("getContrastRatiosForTier returns 3 entries per tier", () => {
        expect(getContrastRatiosForTier("subtle")).toHaveLength(3);
        expect(getContrastRatiosForTier("panel")).toHaveLength(3);
        expect(getContrastRatiosForTier("overlay")).toHaveLength(3);
      });

      it("getContrastRatiosForTier returns empty array for invalid tier", () => {
        expect(getContrastRatiosForTier("invalid")).toHaveLength(0);
      });
    });

    describe("Contrast Ratio Validation", () => {
      it.each(GLASS_CONTRAST_RATIOS)(
        "$tier + $textToken has valid ratio structure",
        (ratio) => {
          expect(ratio.tier).toMatch(/^(subtle|panel|overlay)$/);
          expect(ratio.textToken).toMatch(/^text-(primary|secondary|muted)$/);
          expect(ratio.ratio).toBeGreaterThan(0);
          expect(typeof ratio.meetsAA).toBe("boolean");
          expect(typeof ratio.meetsAAA).toBe("boolean");
        },
      );

      it.each(GLASS_CONTRAST_RATIOS)(
        "$tier + $textToken meetsAA is consistent with ratio value",
        (ratio) => {
          const shouldMeetAA =
            ratio.ratio >= WCAG_CONTRAST_THRESHOLDS.AA_NORMAL;
          expect(ratio.meetsAA).toBe(shouldMeetAA);
        },
      );

      it.each(GLASS_CONTRAST_RATIOS)(
        "$tier + $textToken meetsAAA is consistent with ratio value",
        (ratio) => {
          const shouldMeetAAA =
            ratio.ratio >= WCAG_CONTRAST_THRESHOLDS.AAA_NORMAL;
          expect(ratio.meetsAAA).toBe(shouldMeetAAA);
        },
      );
    });
  });
});
