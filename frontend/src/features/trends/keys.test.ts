/**
 * Tests for Query Key Factory.
 *
 * @module features/trends/keys.test
 */

import { describe, it, expect } from "vitest";

import { trendKeys, technologyKeys, type TrendFilters } from "./keys";

describe("trendKeys", () => {
  describe("all", () => {
    it("returns the root key for all trend queries", () => {
      expect(trendKeys.all).toEqual(["trends"]);
    });

    it("returns a readonly tuple at type level", () => {
      const key = trendKeys.all;
      // The `as const` assertion makes the type readonly at compile time
      // At runtime, it's a regular array but TypeScript prevents mutation
      expect(Array.isArray(key)).toBe(true);
      expect(key.length).toBe(1);
    });
  });

  describe("lists", () => {
    it("returns the key prefix for trend list queries", () => {
      expect(trendKeys.lists()).toEqual(["trends", "list"]);
    });

    it("includes the root key", () => {
      const listKey = trendKeys.lists();
      expect(listKey[0]).toBe(trendKeys.all[0]);
    });
  });

  describe("list", () => {
    it("returns key with empty filters when no filters provided", () => {
      expect(trendKeys.list()).toEqual(["trends", "list", {}]);
    });

    it("returns key with filters when provided", () => {
      const filters: TrendFilters = { techIds: "python,react" };
      expect(trendKeys.list(filters)).toEqual([
        "trends",
        "list",
        { techIds: "python,react" },
      ]);
    });

    it("includes all filter properties in the key", () => {
      const filters: TrendFilters = {
        techIds: "python",
        startDate: "2024-01-01",
        endDate: "2024-12-31",
      };
      const key = trendKeys.list(filters);
      expect(key[2]).toEqual(filters);
    });
  });

  describe("details", () => {
    it("returns the key prefix for trend detail queries", () => {
      expect(trendKeys.details()).toEqual(["trends", "detail"]);
    });
  });

  describe("detail", () => {
    it("returns key with specific id", () => {
      expect(trendKeys.detail("python")).toEqual([
        "trends",
        "detail",
        "python",
      ]);
    });

    it("handles different id formats", () => {
      expect(trendKeys.detail("react-native")).toEqual([
        "trends",
        "detail",
        "react-native",
      ]);
    });
  });
});

describe("technologyKeys", () => {
  describe("all", () => {
    it("returns the root key for all technology queries", () => {
      expect(technologyKeys.all).toEqual(["technologies"]);
    });

    it("is distinct from trendKeys", () => {
      expect(technologyKeys.all).not.toEqual(trendKeys.all);
    });
  });

  describe("lists", () => {
    it("returns the key prefix for technology list queries", () => {
      expect(technologyKeys.lists()).toEqual(["technologies", "list"]);
    });
  });

  describe("list", () => {
    it("returns key with empty filters when no filters provided", () => {
      expect(technologyKeys.list()).toEqual(["technologies", "list", {}]);
    });

    it("returns key with filters when provided", () => {
      expect(technologyKeys.list({})).toEqual(["technologies", "list", {}]);
    });
  });

  describe("details", () => {
    it("returns the key prefix for technology detail queries", () => {
      expect(technologyKeys.details()).toEqual(["technologies", "detail"]);
    });
  });

  describe("detail", () => {
    it("returns key with specific id", () => {
      expect(technologyKeys.detail("python")).toEqual([
        "technologies",
        "detail",
        "python",
      ]);
    });
  });
});

describe("Query Key Hierarchy", () => {
  it("list keys include lists prefix for cache invalidation", () => {
    const listKey = trendKeys.list({ techIds: "python" });
    const listsKey = trendKeys.lists();

    expect(listKey.slice(0, 2)).toEqual(listsKey);
  });

  it("detail keys include details prefix for cache invalidation", () => {
    const detailKey = trendKeys.detail("python");
    const detailsKey = trendKeys.details();

    expect(detailKey.slice(0, 2)).toEqual(detailsKey);
  });

  it("all keys share the same root for full cache invalidation", () => {
    const all = trendKeys.all;
    const list = trendKeys.list({ techIds: "python" });
    const detail = trendKeys.detail("python");

    expect(list[0]).toBe(all[0]);
    expect(detail[0]).toBe(all[0]);
  });
});
