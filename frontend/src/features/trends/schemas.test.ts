/**
 * Tests for API response Zod schemas.
 *
 * @module features/trends/schemas.test
 */

import { describe, it, expect } from "vitest";

import {
  MetaSchema,
  TechnologySchema,
  TrendDataPointSchema,
  TechnologyTrendSchema,
  TechnologiesResponseSchema,
  TrendsResponseSchema,
} from "./schemas";

describe("MetaSchema", () => {
  const validMeta = {
    request_id: "test-123",
    timestamp: "2024-01-15T10:30:00Z",
    total_count: 10,
    page: null,
    page_size: null,
    has_more: null,
  };

  it("validates correct metadata", () => {
    const result = MetaSchema.safeParse(validMeta);
    expect(result.success).toBe(true);
  });

  it("allows optional pagination fields to be null", () => {
    const result = MetaSchema.safeParse(validMeta);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.page).toBeNull();
      expect(result.data.page_size).toBeNull();
      expect(result.data.has_more).toBeNull();
    }
  });

  it("validates pagination fields when present", () => {
    const metaWithPagination = {
      ...validMeta,
      page: 1,
      page_size: 20,
      has_more: true,
    };
    const result = MetaSchema.safeParse(metaWithPagination);
    expect(result.success).toBe(true);
  });

  it("rejects missing required fields", () => {
    const invalidMeta = { request_id: "test-123" };
    const result = MetaSchema.safeParse(invalidMeta);
    expect(result.success).toBe(false);
  });

  it("rejects negative total_count", () => {
    const invalidMeta = { ...validMeta, total_count: -1 };
    const result = MetaSchema.safeParse(invalidMeta);
    expect(result.success).toBe(false);
  });
});

describe("TechnologySchema", () => {
  it("validates correct technology object", () => {
    const technology = { key: "python", name: "Python", category: "Language" };
    const result = TechnologySchema.safeParse(technology);
    expect(result.success).toBe(true);
  });

  it("rejects empty key", () => {
    const technology = { key: "", name: "Python", category: "Language" };
    const result = TechnologySchema.safeParse(technology);
    expect(result.success).toBe(false);
  });

  it("rejects empty name", () => {
    const technology = { key: "python", name: "", category: "Language" };
    const result = TechnologySchema.safeParse(technology);
    expect(result.success).toBe(false);
  });

  it("rejects missing fields", () => {
    const technology = { key: "python" };
    const result = TechnologySchema.safeParse(technology);
    expect(result.success).toBe(false);
  });
});

describe("TrendDataPointSchema", () => {
  it("validates correct data point", () => {
    const dataPoint = { month: "2024-01", count: 1523 };
    const result = TrendDataPointSchema.safeParse(dataPoint);
    expect(result.success).toBe(true);
  });

  it("validates zero count", () => {
    const dataPoint = { month: "2024-01", count: 0 };
    const result = TrendDataPointSchema.safeParse(dataPoint);
    expect(result.success).toBe(true);
  });

  it("rejects invalid month format", () => {
    const dataPoint = { month: "2024/01", count: 100 };
    const result = TrendDataPointSchema.safeParse(dataPoint);
    expect(result.success).toBe(false);
  });

  it("rejects month without leading zero", () => {
    const dataPoint = { month: "2024-1", count: 100 };
    const result = TrendDataPointSchema.safeParse(dataPoint);
    expect(result.success).toBe(false);
  });

  it("rejects negative count", () => {
    const dataPoint = { month: "2024-01", count: -1 };
    const result = TrendDataPointSchema.safeParse(dataPoint);
    expect(result.success).toBe(false);
  });

  it("rejects non-integer count", () => {
    const dataPoint = { month: "2024-01", count: 1.5 };
    const result = TrendDataPointSchema.safeParse(dataPoint);
    expect(result.success).toBe(false);
  });
});

describe("TechnologyTrendSchema", () => {
  const validTrend = {
    tech_key: "python",
    name: "Python",
    data: [
      { month: "2024-01", count: 1523 },
      { month: "2024-02", count: 1412 },
    ],
  };

  it("validates correct trend object", () => {
    const result = TechnologyTrendSchema.safeParse(validTrend);
    expect(result.success).toBe(true);
  });

  it("validates empty data array", () => {
    const trend = { ...validTrend, data: [] };
    const result = TechnologyTrendSchema.safeParse(trend);
    expect(result.success).toBe(true);
  });

  it("rejects invalid data point in array", () => {
    const trend = {
      ...validTrend,
      data: [{ month: "invalid", count: 100 }],
    };
    const result = TechnologyTrendSchema.safeParse(trend);
    expect(result.success).toBe(false);
  });
});

describe("TechnologiesResponseSchema", () => {
  const validResponse = {
    data: [
      { key: "python", name: "Python", category: "Language" },
      { key: "react", name: "React", category: "Framework" },
    ],
    meta: {
      request_id: "test-123",
      timestamp: "2024-01-15T10:30:00Z",
      total_count: 2,
      page: null,
      page_size: null,
      has_more: null,
    },
  };

  it("validates correct response envelope", () => {
    const result = TechnologiesResponseSchema.safeParse(validResponse);
    expect(result.success).toBe(true);
  });

  it("validates empty data array", () => {
    const response = { ...validResponse, data: [] };
    const result = TechnologiesResponseSchema.safeParse(response);
    expect(result.success).toBe(true);
  });

  it("rejects missing meta", () => {
    const response = { data: validResponse.data };
    const result = TechnologiesResponseSchema.safeParse(response);
    expect(result.success).toBe(false);
  });

  it("rejects invalid technology in data array", () => {
    const response = {
      ...validResponse,
      data: [{ key: "", name: "Invalid", category: "Test" }],
    };
    const result = TechnologiesResponseSchema.safeParse(response);
    expect(result.success).toBe(false);
  });
});

describe("TrendsResponseSchema", () => {
  const validResponse = {
    data: [
      {
        tech_key: "python",
        name: "Python",
        data: [{ month: "2024-01", count: 1523 }],
      },
    ],
    meta: {
      request_id: "test-456",
      timestamp: "2024-01-15T10:30:00Z",
      total_count: 1,
      page: null,
      page_size: null,
      has_more: null,
    },
  };

  it("validates correct response envelope", () => {
    const result = TrendsResponseSchema.safeParse(validResponse);
    expect(result.success).toBe(true);
  });

  it("validates multiple trends in data array", () => {
    const response = {
      ...validResponse,
      data: [
        ...validResponse.data,
        {
          tech_key: "react",
          name: "React",
          data: [{ month: "2024-01", count: 892 }],
        },
      ],
    };
    const result = TrendsResponseSchema.safeParse(response);
    expect(result.success).toBe(true);
  });

  it("rejects invalid trend data point", () => {
    const response = {
      ...validResponse,
      data: [
        {
          tech_key: "python",
          name: "Python",
          data: [{ month: "invalid-format", count: 100 }],
        },
      ],
    };
    const result = TrendsResponseSchema.safeParse(response);
    expect(result.success).toBe(false);
  });
});
