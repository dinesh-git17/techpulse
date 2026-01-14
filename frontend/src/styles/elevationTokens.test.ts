/**
 * @fileoverview Elevation Token Validation Tests
 *
 * Validates that the TechPulse z-index and elevation system is correctly configured:
 * - Semantic z-index scale is defined
 * - Default Tailwind utilities are disabled
 * - Only named z-index utilities exist
 * - Stacking context utility is available
 */
import fs from "node:fs";
import path from "node:path";

import { beforeAll, describe, expect, it } from "vitest";

import {
  DISABLED_Z_INDEX_UTILITIES,
  ELEVATION_LAYER_NAMES,
  ELEVATION_LAYERS,
  PORTAL_CONFIG,
  STACKING_CONTEXT_CLASS,
  VALID_Z_INDEX_CLASSES,
  getElevationLayer,
  getZIndexClass,
  getZIndexValue,
  isDisabledZIndexClass,
  isValidZIndexClass,
} from "./elevationTokens";

const GLOBALS_CSS_PATH = path.resolve(__dirname, "../app/globals.css");

describe("Elevation Token Configuration", () => {
  describe("Token Registry", () => {
    it("defines exactly 6 elevation layers", () => {
      expect(ELEVATION_LAYERS).toHaveLength(6);
    });

    it("defines all required layers: base, raised, sticky, overlay, modal, toast", () => {
      const expectedLayers = [
        "base",
        "raised",
        "sticky",
        "overlay",
        "modal",
        "toast",
      ];
      expect(ELEVATION_LAYER_NAMES).toEqual(expectedLayers);
    });

    it("assigns correct z-index values to each layer", () => {
      expect(getZIndexValue("base")).toBe(0);
      expect(getZIndexValue("raised")).toBe(10);
      expect(getZIndexValue("sticky")).toBe(100);
      expect(getZIndexValue("overlay")).toBe(200);
      expect(getZIndexValue("modal")).toBe(300);
      expect(getZIndexValue("toast")).toBe(400);
    });

    it("layers have increasing z-index values", () => {
      for (let i = 1; i < ELEVATION_LAYERS.length; i++) {
        const prevLayer = ELEVATION_LAYERS[i - 1];
        const currentLayer = ELEVATION_LAYERS[i];
        expect(currentLayer?.value).toBeGreaterThan(prevLayer?.value ?? 0);
      }
    });

    it("defines disabled default utilities", () => {
      expect(DISABLED_Z_INDEX_UTILITIES).toContain("z-0");
      expect(DISABLED_Z_INDEX_UTILITIES).toContain("z-10");
      expect(DISABLED_Z_INDEX_UTILITIES).toContain("z-20");
      expect(DISABLED_Z_INDEX_UTILITIES).toContain("z-50");
      expect(DISABLED_Z_INDEX_UTILITIES).toContain("z-auto");
    });

    it("defines portal configuration for tooltips", () => {
      expect(PORTAL_CONFIG.tooltip).toBeDefined();
      expect(PORTAL_CONFIG.tooltip.zIndex).toBe(9999);
    });

    it("defines stacking context class", () => {
      expect(STACKING_CONTEXT_CLASS).toBe("stacking-context");
    });
  });

  describe("Layer Properties", () => {
    it.each(ELEVATION_LAYERS)("$name has valid CSS variable", ({ cssVar }) => {
      expect(cssVar).toMatch(/^--z-[\w-]+$/);
    });

    it.each(ELEVATION_LAYERS)(
      "$name has valid Tailwind class",
      ({ tailwindClass }) => {
        expect(tailwindClass).toMatch(/^z-[\w-]+$/);
      },
    );

    it.each(ELEVATION_LAYERS)(
      "$name has a use case description",
      ({ useCase }) => {
        expect(useCase.length).toBeGreaterThan(0);
      },
    );
  });

  describe("Helper Functions", () => {
    it("getElevationLayer returns correct layer for valid name", () => {
      const layer = getElevationLayer("modal");
      expect(layer?.value).toBe(300);
      expect(layer?.tailwindClass).toBe("z-modal");
    });

    it("getElevationLayer returns undefined for invalid name", () => {
      const layer = getElevationLayer("invalid");
      expect(layer).toBeUndefined();
    });

    it("getZIndexClass returns correct class for valid name", () => {
      expect(getZIndexClass("sticky")).toBe("z-sticky");
      expect(getZIndexClass("overlay")).toBe("z-overlay");
    });

    it("getZIndexClass returns undefined for invalid name", () => {
      expect(getZIndexClass("invalid")).toBeUndefined();
    });

    it("getZIndexValue returns correct value for valid name", () => {
      expect(getZIndexValue("toast")).toBe(400);
    });

    it("getZIndexValue returns undefined for invalid name", () => {
      expect(getZIndexValue("invalid")).toBeUndefined();
    });

    it("isValidZIndexClass returns true for semantic classes", () => {
      expect(isValidZIndexClass("z-base")).toBe(true);
      expect(isValidZIndexClass("z-modal")).toBe(true);
      expect(isValidZIndexClass("z-toast")).toBe(true);
    });

    it("isValidZIndexClass returns false for non-semantic classes", () => {
      expect(isValidZIndexClass("z-50")).toBe(false);
      expect(isValidZIndexClass("z-[9999]")).toBe(false);
    });

    it("isDisabledZIndexClass returns true for disabled utilities", () => {
      expect(isDisabledZIndexClass("z-0")).toBe(true);
      expect(isDisabledZIndexClass("z-50")).toBe(true);
      expect(isDisabledZIndexClass("z-auto")).toBe(true);
    });

    it("isDisabledZIndexClass returns false for semantic utilities", () => {
      expect(isDisabledZIndexClass("z-base")).toBe(false);
      expect(isDisabledZIndexClass("z-modal")).toBe(false);
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

    describe("Semantic Z-Index Variables", () => {
      it.each([
        ["--z-base", "0"],
        ["--z-raised", "10"],
        ["--z-sticky", "100"],
        ["--z-overlay", "200"],
        ["--z-modal", "300"],
        ["--z-toast", "400"],
      ])("declares %s with value %s", (varName, expectedValue) => {
        expect(globalsContent).toContain(`${varName}: ${expectedValue}`);
      });
    });

    describe("Disabled Default Utilities", () => {
      it.each([
        "--z-0",
        "--z-10",
        "--z-20",
        "--z-30",
        "--z-40",
        "--z-50",
        "--z-auto",
      ])("disables default %s utility", (varName) => {
        expect(globalsContent).toContain(`${varName}: initial`);
      });
    });

    describe("Stacking Context Utility", () => {
      it("defines .stacking-context class", () => {
        expect(globalsContent).toContain(".stacking-context");
      });

      it("applies isolation: isolate to stacking-context", () => {
        expect(globalsContent).toContain("isolation: isolate");
      });
    });

    describe("Portal Strategy Documentation", () => {
      it("documents portal strategy for tooltips", () => {
        expect(globalsContent).toContain("Portal Strategy");
        expect(globalsContent).toContain("Tooltip");
      });
    });

    describe("Tailwind Theme Integration", () => {
      it("configures z-index in @theme inline block", () => {
        expect(globalsContent).toContain("@theme inline");
        expect(globalsContent).toContain("Z-INDEX");
      });
    });
  });

  describe("Z-Index Scale Requirements", () => {
    it("base layer is at z-index 0", () => {
      expect(getZIndexValue("base")).toBe(0);
    });

    it("toast layer is highest at z-index 400", () => {
      const firstLayer = ELEVATION_LAYERS[0];
      expect(firstLayer).toBeDefined();
      if (!firstLayer) return;

      const maxLayer = ELEVATION_LAYERS.reduce(
        (max, layer) => (layer.value > max.value ? layer : max),
        firstLayer,
      );
      expect(maxLayer.name).toBe("toast");
      expect(maxLayer.value).toBe(400);
    });

    it("sticky layer is below overlay for correct popover behavior", () => {
      expect(getZIndexValue("sticky")).toBeLessThan(
        getZIndexValue("overlay") ?? 0,
      );
    });

    it("modal layer is above overlay for dialog precedence", () => {
      expect(getZIndexValue("modal")).toBeGreaterThan(
        getZIndexValue("overlay") ?? 0,
      );
    });

    it("toast layer is above modal for notification visibility", () => {
      expect(getZIndexValue("toast")).toBeGreaterThan(
        getZIndexValue("modal") ?? 0,
      );
    });
  });

  describe("Valid Z-Index Classes", () => {
    it("includes all semantic layer classes", () => {
      expect(VALID_Z_INDEX_CLASSES).toContain("z-base");
      expect(VALID_Z_INDEX_CLASSES).toContain("z-raised");
      expect(VALID_Z_INDEX_CLASSES).toContain("z-sticky");
      expect(VALID_Z_INDEX_CLASSES).toContain("z-overlay");
      expect(VALID_Z_INDEX_CLASSES).toContain("z-modal");
      expect(VALID_Z_INDEX_CLASSES).toContain("z-toast");
    });

    it("does not include disabled default utilities", () => {
      for (const disabled of DISABLED_Z_INDEX_UTILITIES) {
        expect(VALID_Z_INDEX_CLASSES).not.toContain(disabled);
      }
    });
  });
});
