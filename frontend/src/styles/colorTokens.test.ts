/**
 * @fileoverview Color Token Validation Tests
 *
 * Validates that the TechPulse color system is correctly configured:
 * - CSS variables follow --tp-color-* naming convention
 * - All expected semantic tokens are defined
 * - Alpha modifier syntax produces valid CSS
 */
import fs from "node:fs";
import path from "node:path";

import { beforeAll, describe, expect, it } from "vitest";

import {
  ALL_SEMANTIC_TOKENS,
  BRAND_SCALE,
  COLOR_TOKENS,
  getCssVarName,
} from "./colorTokens";

const GLOBALS_CSS_PATH = path.resolve(__dirname, "../app/globals.css");

describe("Color Token Configuration", () => {
  describe("Token Registry", () => {
    it("defines all required surface tokens", () => {
      expect(COLOR_TOKENS.surface).toContain("surface-primary");
      expect(COLOR_TOKENS.surface).toContain("surface-secondary");
      expect(COLOR_TOKENS.surface).toContain("surface-tertiary");
      expect(COLOR_TOKENS.surface).toContain("surface-elevated");
      expect(COLOR_TOKENS.surface).toContain("surface-sunken");
    });

    it("defines all required text tokens", () => {
      expect(COLOR_TOKENS.text).toContain("text-primary");
      expect(COLOR_TOKENS.text).toContain("text-secondary");
      expect(COLOR_TOKENS.text).toContain("text-muted");
      expect(COLOR_TOKENS.text).toContain("text-inverted");
    });

    it("defines all required border tokens", () => {
      expect(COLOR_TOKENS.border).toContain("border-default");
      expect(COLOR_TOKENS.border).toContain("border-muted");
      expect(COLOR_TOKENS.border).toContain("border-strong");
      expect(COLOR_TOKENS.border).toContain("border-glass");
    });

    it("defines all required action tokens", () => {
      expect(COLOR_TOKENS.action).toContain("action-primary");
      expect(COLOR_TOKENS.action).toContain("action-primary-hover");
      expect(COLOR_TOKENS.action).toContain("action-primary-active");
    });

    it("defines all required status tokens", () => {
      expect(COLOR_TOKENS.status).toContain("status-success");
      expect(COLOR_TOKENS.status).toContain("status-warning");
      expect(COLOR_TOKENS.status).toContain("status-danger");
    });

    it("defines all required interactive tokens", () => {
      expect(COLOR_TOKENS.interactive).toContain("focus-ring");
      expect(COLOR_TOKENS.interactive).toContain("highlight");
    });

    it("defines complete brand scale from 50-950", () => {
      expect(BRAND_SCALE).toEqual([
        50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950,
      ]);
    });
  });

  describe("CSS Variable Naming Convention", () => {
    it("generates --tp-color-* format for semantic tokens", () => {
      expect(getCssVarName("surface-primary")).toBe(
        "--tp-color-surface-primary",
      );
      expect(getCssVarName("text-muted")).toBe("--tp-color-text-muted");
      expect(getCssVarName("action-primary")).toBe("--tp-color-action-primary");
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

    it("contains --tp-color-* CSS variable declarations", () => {
      expect(globalsContent).toContain("--tp-color-surface-primary:");
      expect(globalsContent).toContain("--tp-color-text-primary:");
      expect(globalsContent).toContain("--tp-color-border-default:");
      expect(globalsContent).toContain("--tp-color-action-primary:");
      expect(globalsContent).toContain("--tp-color-status-success:");
    });

    it("contains --tp-primitive-brand-* CSS variable declarations", () => {
      expect(globalsContent).toContain("--tp-primitive-brand-500:");
      expect(globalsContent).toContain("--tp-primitive-brand-400:");
      expect(globalsContent).toContain("--tp-primitive-brand-600:");
    });

    it("configures Tailwind @theme with alpha-value syntax", () => {
      expect(globalsContent).toContain("@theme inline");
      expect(globalsContent).toContain("<alpha-value>");
      expect(globalsContent).toContain("--color-surface-primary:");
      expect(globalsContent).toContain("--color-text-primary:");
    });

    it("uses RGB channel format for alpha compatibility", () => {
      const rgbPattern = /--tp-color-surface-primary:\s*\d+\s+\d+\s+\d+\s*[;,]/;
      expect(rgbPattern.test(globalsContent)).toBe(true);
    });

    it("defines dark mode as active implementation", () => {
      expect(globalsContent).toContain("color-scheme: dark");
    });

    it("structures light mode tokens for future activation", () => {
      expect(globalsContent).toContain("Light");
      expect(globalsContent).toContain("--tp-primitive-neutral-50:");
    });

    describe("Token Coverage", () => {
      it.each(ALL_SEMANTIC_TOKENS)(
        "declares CSS variable for %s",
        (token: string) => {
          const cssVarName = getCssVarName(token);
          expect(globalsContent).toContain(`${cssVarName}:`);
        },
      );

      it.each(BRAND_SCALE)(
        "declares primitive brand-%i in palette",
        (shade: number) => {
          expect(globalsContent).toContain(`--tp-primitive-brand-${shade}:`);
        },
      );
    });

    describe("Tailwind Theme Integration", () => {
      const tailwindColorMappings = [
        ["--color-surface-primary", "bg-surface-primary"],
        ["--color-text-primary", "text-text-primary"],
        ["--color-border-default", "border-border-default"],
        ["--color-action-primary", "bg-action-primary"],
        ["--color-status-success", "bg-status-success"],
      ];

      it.each(tailwindColorMappings)(
        "maps %s for Tailwind consumption",
        (cssVar) => {
          expect(globalsContent).toContain(`${cssVar}:`);
        },
      );
    });
  });
});
