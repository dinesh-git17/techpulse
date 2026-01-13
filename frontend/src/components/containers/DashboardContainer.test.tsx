/**
 * Integration tests for DashboardContainer URL-UI synchronization.
 *
 * @module components/containers/DashboardContainer.test
 */

import { type ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { describe, it, expect, beforeEach } from "vitest";

import { server } from "@/test/mocks/server";

import { DashboardContainer } from "./DashboardContainer";

/**
 * Create test wrapper with QueryClient and NuqsTestingAdapter.
 */
function createWrapper(initialParams?: Record<string, string>) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <NuqsTestingAdapter searchParams={initialParams}>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </NuqsTestingAdapter>
    );
  };
}

describe("DashboardContainer", () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  describe("URL state initialization", () => {
    it("renders without URL parameters", () => {
      render(<DashboardContainer />, {
        wrapper: createWrapper(),
      });

      expect(
        screen.getByRole("heading", { name: /technology trends/i }),
      ).toBeInTheDocument();
    });

    it("parses tech_ids from URL", async () => {
      render(<DashboardContainer />, {
        wrapper: createWrapper({ tech_ids: "python,react" }),
      });

      expect(screen.getByText(/2 technologies selected/i)).toBeInTheDocument();
    });

    it("parses date range from URL", () => {
      render(<DashboardContainer />, {
        wrapper: createWrapper({
          start: "2024-01-01",
          end: "2024-06-30",
        }),
      });

      const dateButton = screen.getByRole("button", {
        name: /date range/i,
      });
      expect(dateButton).toHaveTextContent(/jan 1, 2024/i);
      expect(dateButton).toHaveTextContent(/jun 30, 2024/i);
    });
  });

  describe("component structure", () => {
    it("renders sidebar with filters", () => {
      render(<DashboardContainer />, {
        wrapper: createWrapper(),
      });

      const sidebar = screen.getByRole("complementary", {
        name: /dashboard filters/i,
      });
      expect(sidebar).toBeInTheDocument();

      expect(
        within(sidebar).getByLabelText(/technologies/i),
      ).toBeInTheDocument();
      expect(within(sidebar).getByLabelText(/date range/i)).toBeInTheDocument();
    });

    it("renders main content area with chart", () => {
      render(<DashboardContainer />, {
        wrapper: createWrapper(),
      });

      const main = screen.getByRole("main");
      expect(main).toBeInTheDocument();

      expect(
        within(main).getByRole("heading", { name: /trend analysis/i }),
      ).toBeInTheDocument();
    });
  });

  describe("filter display", () => {
    it("shows selected technologies from URL", async () => {
      render(<DashboardContainer />, {
        wrapper: createWrapper({ tech_ids: "python,typescript,rust" }),
      });

      expect(screen.getByText(/3 technologies selected/i)).toBeInTheDocument();
    });

    it("shows zero technologies when none selected", () => {
      render(<DashboardContainer />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/0 technologies selected/i)).toBeInTheDocument();
    });
  });

  describe("chart states", () => {
    it("shows empty state when no technologies selected", () => {
      render(<DashboardContainer />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/no data found/i)).toBeInTheDocument();
    });

    it("shows loading state while fetching data", () => {
      render(<DashboardContainer />, {
        wrapper: createWrapper({ tech_ids: "python" }),
      });

      expect(
        screen.getByRole("status", { name: /loading chart data/i }),
      ).toBeInTheDocument();
    });
  });
});
