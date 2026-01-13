/**
 * Tests for nuqs URL parameter parsers.
 *
 * @module lib/url/parsers.test
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  dashboardSearchParams,
  defaultParserOptions,
  parseAsTechIds,
  searchParamKeys,
} from "./parsers";
import { MAX_TECH_IDS } from "./schemas";

describe("parseAsTechIds", () => {
  describe("parse", () => {
    it("parses comma-separated string to array", () => {
      const result = parseAsTechIds.parse("python,react,vue");
      expect(result).toEqual(["python", "react", "vue"]);
    });

    it("sorts array alphabetically", () => {
      const result = parseAsTechIds.parse("vue,react,python");
      expect(result).toEqual(["python", "react", "vue"]);
    });

    it("returns empty array for empty string", () => {
      const result = parseAsTechIds.parse("");
      expect(result).toEqual([]);
    });

    it("handles single item", () => {
      const result = parseAsTechIds.parse("python");
      expect(result).toEqual(["python"]);
    });

    it("trims whitespace from items", () => {
      const result = parseAsTechIds.parse("python , react , vue");
      expect(result).toEqual(["python", "react", "vue"]);
    });

    it("filters empty items from input", () => {
      const result = parseAsTechIds.parse("python,,react,,,vue");
      expect(result).toEqual(["python", "react", "vue"]);
    });

    it("truncates to max items", () => {
      const ids = Array.from({ length: 15 }, (_, i) => `tech${i}`).join(",");
      const result = parseAsTechIds.parse(ids);
      expect(result).toHaveLength(MAX_TECH_IDS);
    });
  });

  describe("serialize", () => {
    it("serializes array to comma-separated string", () => {
      const result = parseAsTechIds.serialize(["python", "react", "vue"]);
      expect(result).toBe("python,react,vue");
    });

    it("sorts array alphabetically", () => {
      const result = parseAsTechIds.serialize(["vue", "react", "python"]);
      expect(result).toBe("python,react,vue");
    });

    it("returns empty string for empty array", () => {
      const result = parseAsTechIds.serialize([]);
      expect(result).toBe("");
    });
  });

  describe("eq (equality check)", () => {
    it("returns true for equal arrays", () => {
      const result = parseAsTechIds.eq(
        ["python", "react"],
        ["python", "react"],
      );
      expect(result).toBe(true);
    });

    it("returns true for same items in different order", () => {
      const result = parseAsTechIds.eq(
        ["vue", "react", "python"],
        ["python", "react", "vue"],
      );
      expect(result).toBe(true);
    });

    it("returns false for different lengths", () => {
      const result = parseAsTechIds.eq(["python", "react"], ["python"]);
      expect(result).toBe(false);
    });

    it("returns false for different items", () => {
      const result = parseAsTechIds.eq(["python", "react"], ["python", "vue"]);
      expect(result).toBe(false);
    });

    it("returns true for empty arrays", () => {
      const result = parseAsTechIds.eq([], []);
      expect(result).toBe(true);
    });
  });
});

describe("searchParamKeys", () => {
  it("defines techIds key as tech_ids", () => {
    expect(searchParamKeys.techIds).toBe("tech_ids");
  });

  it("defines start key", () => {
    expect(searchParamKeys.start).toBe("start");
  });

  it("defines end key", () => {
    expect(searchParamKeys.end).toBe("end");
  });
});

describe("defaultParserOptions", () => {
  it("uses replace history strategy", () => {
    expect(defaultParserOptions.history).toBe("replace");
  });

  it("enables shallow routing", () => {
    expect(defaultParserOptions.shallow).toBe(true);
  });
});

describe("dashboardSearchParams", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2025-06-15T12:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("defines tech_ids parameter with empty array default", () => {
    const parser = dashboardSearchParams[searchParamKeys.techIds];
    expect(parser).toBeDefined();
  });

  it("defines start parameter", () => {
    const parser = dashboardSearchParams[searchParamKeys.start];
    expect(parser).toBeDefined();
  });

  it("defines end parameter", () => {
    const parser = dashboardSearchParams[searchParamKeys.end];
    expect(parser).toBeDefined();
  });
});
