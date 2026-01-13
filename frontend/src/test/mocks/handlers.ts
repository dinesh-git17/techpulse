/**
 * MSW request handlers for API mocking in tests.
 *
 * @module test/mocks/handlers
 */

import { http, HttpResponse } from "msw";

import type {
  TechnologiesResponse,
  TrendsResponse,
} from "@/features/trends/schemas";

const API_BASE = "http://localhost:8000";

/**
 * Mock technology catalog data.
 */
export const mockTechnologies: TechnologiesResponse = {
  data: [
    { key: "python", name: "Python", category: "Language" },
    { key: "react", name: "React", category: "Framework" },
    { key: "typescript", name: "TypeScript", category: "Language" },
  ],
  meta: {
    request_id: "test-request-id-123",
    timestamp: "2024-01-15T10:30:00Z",
    total_count: 3,
    page: null,
    page_size: null,
    has_more: null,
  },
};

/**
 * Mock trend data.
 */
export const mockTrends: TrendsResponse = {
  data: [
    {
      tech_key: "python",
      name: "Python",
      data: [
        { month: "2024-01", count: 1523 },
        { month: "2024-02", count: 1412 },
        { month: "2024-03", count: 1650 },
      ],
    },
    {
      tech_key: "react",
      name: "React",
      data: [
        { month: "2024-01", count: 892 },
        { month: "2024-02", count: 945 },
        { month: "2024-03", count: 1020 },
      ],
    },
  ],
  meta: {
    request_id: "test-request-id-456",
    timestamp: "2024-01-15T10:30:00Z",
    total_count: 2,
    page: null,
    page_size: null,
    has_more: null,
  },
};

/**
 * Default MSW handlers for API endpoints.
 */
export const handlers = [
  // GET /api/v1/technologies
  http.get(`${API_BASE}/api/v1/technologies`, () => {
    return HttpResponse.json(mockTechnologies);
  }),

  // GET /api/v1/trends
  http.get(`${API_BASE}/api/v1/trends`, ({ request }) => {
    const url = new URL(request.url);
    const techIds = url.searchParams.get("tech_ids");

    if (!techIds) {
      return HttpResponse.json(
        { code: "VALIDATION_ERROR", message: "tech_ids is required" },
        { status: 400 },
      );
    }

    return HttpResponse.json(mockTrends);
  }),
];
