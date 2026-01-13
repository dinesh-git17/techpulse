/**
 * Tests for dashboard URL parameter schemas and parsing.
 *
 * @module lib/url/schemas.test
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  getDefaultEndDate,
  getDefaultStartDate,
  IsoDateSchema,
  MAX_TECH_IDS,
  parseDashboardParams,
  parseTechIdsString,
  serializeTechIds,
  TechIdsSchema,
  toRawParams,
} from "./schemas";

describe("getDefaultStartDate", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns date 12 months ago in ISO format", () => {
    vi.setSystemTime(new Date("2025-06-15T12:00:00Z"));
    const result = getDefaultStartDate();
    expect(result).toBe("2024-06-15");
  });

  it("handles year boundary correctly", () => {
    vi.setSystemTime(new Date("2025-01-15T12:00:00Z"));
    const result = getDefaultStartDate();
    expect(result).toBe("2024-01-15");
  });

  it("handles month boundary correctly", () => {
    vi.setSystemTime(new Date("2025-03-31T12:00:00Z"));
    const result = getDefaultStartDate();
    expect(result).toMatch(/^2024-03-\d{2}$/);
  });
});

describe("getDefaultEndDate", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns today in ISO format", () => {
    vi.setSystemTime(new Date("2025-06-15T12:00:00Z"));
    const result = getDefaultEndDate();
    expect(result).toBe("2025-06-15");
  });

  it("uses UTC date regardless of timezone offset", () => {
    vi.setSystemTime(new Date("2025-06-15T23:00:00Z"));
    const result = getDefaultEndDate();
    expect(result).toBe("2025-06-15");
  });
});

describe("IsoDateSchema", () => {
  it("validates correct ISO date", () => {
    const result = IsoDateSchema.safeParse("2024-06-15");
    expect(result.success).toBe(true);
  });

  it("validates leap year date", () => {
    const result = IsoDateSchema.safeParse("2024-02-29");
    expect(result.success).toBe(true);
  });

  it("rejects invalid leap year date", () => {
    const result = IsoDateSchema.safeParse("2023-02-29");
    expect(result.success).toBe(false);
  });

  it("rejects invalid format - slash separator", () => {
    const result = IsoDateSchema.safeParse("2024/06/15");
    expect(result.success).toBe(false);
  });

  it("rejects invalid format - wrong order", () => {
    const result = IsoDateSchema.safeParse("15-06-2024");
    expect(result.success).toBe(false);
  });

  it("rejects invalid format - missing leading zeros", () => {
    const result = IsoDateSchema.safeParse("2024-6-15");
    expect(result.success).toBe(false);
  });

  it("rejects invalid month", () => {
    const result = IsoDateSchema.safeParse("2024-13-15");
    expect(result.success).toBe(false);
  });

  it("rejects invalid day", () => {
    const result = IsoDateSchema.safeParse("2024-06-32");
    expect(result.success).toBe(false);
  });

  it("rejects garbage input", () => {
    const result = IsoDateSchema.safeParse("hello");
    expect(result.success).toBe(false);
  });

  it("rejects empty string", () => {
    const result = IsoDateSchema.safeParse("");
    expect(result.success).toBe(false);
  });
});

describe("TechIdsSchema", () => {
  it("validates array within limit", () => {
    const result = TechIdsSchema.safeParse(["python", "react", "vue"]);
    expect(result.success).toBe(true);
  });

  it("sorts array alphabetically", () => {
    const result = TechIdsSchema.safeParse(["vue", "react", "python"]);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data).toEqual(["python", "react", "vue"]);
    }
  });

  it("validates empty array", () => {
    const result = TechIdsSchema.safeParse([]);
    expect(result.success).toBe(true);
  });

  it("validates array at max limit", () => {
    const ids = Array.from({ length: MAX_TECH_IDS }, (_, i) => `tech${i}`);
    const result = TechIdsSchema.safeParse(ids);
    expect(result.success).toBe(true);
  });

  it("rejects array exceeding max limit", () => {
    const ids = Array.from({ length: MAX_TECH_IDS + 1 }, (_, i) => `tech${i}`);
    const result = TechIdsSchema.safeParse(ids);
    expect(result.success).toBe(false);
  });

  it("rejects empty strings in array", () => {
    const result = TechIdsSchema.safeParse(["python", "", "react"]);
    expect(result.success).toBe(false);
  });
});

describe("parseTechIdsString", () => {
  it("parses comma-separated string", () => {
    const result = parseTechIdsString("python,react,vue");
    expect(result).toEqual(["python", "react", "vue"]);
  });

  it("trims whitespace from items", () => {
    const result = parseTechIdsString("python , react , vue");
    expect(result).toEqual(["python", "react", "vue"]);
  });

  it("filters empty items", () => {
    const result = parseTechIdsString("python,,react,,,vue");
    expect(result).toEqual(["python", "react", "vue"]);
  });

  it("returns empty array for undefined", () => {
    const result = parseTechIdsString(undefined);
    expect(result).toEqual([]);
  });

  it("returns empty array for empty string", () => {
    const result = parseTechIdsString("");
    expect(result).toEqual([]);
  });

  it("returns empty array for whitespace-only string", () => {
    const result = parseTechIdsString("   ");
    expect(result).toEqual([]);
  });

  it("handles single item", () => {
    const result = parseTechIdsString("python");
    expect(result).toEqual(["python"]);
  });
});

describe("serializeTechIds", () => {
  it("serializes array to comma-separated string", () => {
    const result = serializeTechIds(["python", "react", "vue"]);
    expect(result).toBe("python,react,vue");
  });

  it("sorts array alphabetically", () => {
    const result = serializeTechIds(["vue", "react", "python"]);
    expect(result).toBe("python,react,vue");
  });

  it("returns empty string for empty array", () => {
    const result = serializeTechIds([]);
    expect(result).toBe("");
  });

  it("handles single item", () => {
    const result = serializeTechIds(["python"]);
    expect(result).toBe("python");
  });

  it("does not mutate original array", () => {
    const original = ["vue", "react", "python"];
    serializeTechIds(original);
    expect(original).toEqual(["vue", "react", "python"]);
  });
});

describe("parseDashboardParams", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2025-06-15T12:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("tech_ids parsing", () => {
    it("parses valid tech_ids", () => {
      const result = parseDashboardParams({ tech_ids: "python,react" });
      expect(result.params.techIds).toEqual(["python", "react"]);
      expect(result.corrections).toHaveLength(0);
    });

    it("sorts tech_ids alphabetically", () => {
      const result = parseDashboardParams({ tech_ids: "vue,react,python" });
      expect(result.params.techIds).toEqual(["python", "react", "vue"]);
    });

    it("defaults to empty array when undefined", () => {
      const result = parseDashboardParams({});
      expect(result.params.techIds).toEqual([]);
    });

    it("truncates excess tech_ids with correction", () => {
      const ids = Array.from({ length: 15 }, (_, i) => `tech${i}`).join(",");
      const result = parseDashboardParams({ tech_ids: ids });
      expect(result.params.techIds).toHaveLength(MAX_TECH_IDS);
      expect(result.corrections).toContainEqual({
        type: "excess_tech_ids",
        message: `Selection limited to ${MAX_TECH_IDS} technologies.`,
      });
    });

    it("filters unknown tech_ids when knownTechIds provided", () => {
      const knownTechIds = new Set(["python", "react"]);
      const result = parseDashboardParams(
        { tech_ids: "python,unknown,react" },
        knownTechIds,
      );
      expect(result.params.techIds).toEqual(["python", "react"]);
      expect(result.corrections).toContainEqual({
        type: "unknown_tech_ids",
        message: "Some technologies were not recognized.",
      });
    });

    it("does not filter when knownTechIds is empty", () => {
      const knownTechIds = new Set<string>();
      const result = parseDashboardParams(
        { tech_ids: "python,custom" },
        knownTechIds,
      );
      expect(result.params.techIds).toEqual(["custom", "python"]);
      expect(result.corrections).toHaveLength(0);
    });
  });

  describe("date parsing", () => {
    it("parses valid start and end dates", () => {
      const result = parseDashboardParams({
        start: "2024-01-01",
        end: "2024-12-31",
      });
      expect(result.params.startDate).toBe("2024-01-01");
      expect(result.params.endDate).toBe("2024-12-31");
      expect(result.corrections).toHaveLength(0);
    });

    it("defaults start to 12 months ago", () => {
      const result = parseDashboardParams({});
      expect(result.params.startDate).toBe("2024-06-15");
    });

    it("defaults end to today", () => {
      const result = parseDashboardParams({});
      expect(result.params.endDate).toBe("2025-06-15");
    });

    it("falls back to default for invalid start date", () => {
      const result = parseDashboardParams({ start: "invalid" });
      expect(result.params.startDate).toBe("2024-06-15");
      expect(result.corrections).toContainEqual({
        type: "invalid_date_format",
        message: "Invalid date format. Showing last 12 months.",
      });
    });

    it("falls back to default for invalid end date", () => {
      const result = parseDashboardParams({ end: "hello" });
      expect(result.params.endDate).toBe("2025-06-15");
      expect(result.corrections).toContainEqual({
        type: "invalid_date_format",
        message: "Invalid date format. Showing last 12 months.",
      });
    });

    it("corrects impossible date range (start >= end)", () => {
      const result = parseDashboardParams({
        start: "2025-06-01",
        end: "2025-05-01",
      });
      expect(result.params.startDate).toBe("2025-06-01");
      expect(result.params.endDate).toBe("2025-07-01");
      expect(result.corrections).toContainEqual({
        type: "impossible_date_range",
        message: "End date adjusted to be after start date.",
      });
    });

    it("corrects when start equals end", () => {
      const result = parseDashboardParams({
        start: "2025-06-01",
        end: "2025-06-01",
      });
      expect(result.params.endDate).toBe("2025-07-01");
      expect(result.corrections).toContainEqual({
        type: "impossible_date_range",
        message: "End date adjusted to be after start date.",
      });
    });
  });

  describe("combined corrections", () => {
    it("accumulates multiple corrections", () => {
      const ids = Array.from({ length: 15 }, (_, i) => `tech${i}`).join(",");
      const result = parseDashboardParams({
        tech_ids: ids,
        start: "invalid",
        end: "2024-01-01",
      });
      expect(result.corrections.length).toBeGreaterThanOrEqual(2);
    });
  });
});

describe("toRawParams", () => {
  it("converts parsed params to raw format", () => {
    const parsed = {
      techIds: ["python", "react"],
      startDate: "2024-01-01",
      endDate: "2024-12-31",
    };
    const result = toRawParams(parsed);
    expect(result).toEqual({
      tech_ids: "python,react",
      start: "2024-01-01",
      end: "2024-12-31",
    });
  });

  it("serializes tech_ids alphabetically", () => {
    const parsed = {
      techIds: ["vue", "react", "python"],
      startDate: "2024-01-01",
      endDate: "2024-12-31",
    };
    const result = toRawParams(parsed);
    expect(result.tech_ids).toBe("python,react,vue");
  });

  it("returns empty string for empty tech_ids", () => {
    const parsed = {
      techIds: [],
      startDate: "2024-01-01",
      endDate: "2024-12-31",
    };
    const result = toRawParams(parsed);
    expect(result.tech_ids).toBe("");
  });
});
