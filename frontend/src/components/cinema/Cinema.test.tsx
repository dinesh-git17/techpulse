/**
 * Tests for the Cinema orchestrator component.
 *
 * Validates reduced motion support, fallback rendering, and animated
 * playback mode. SSR hydration behavior is tested via integration tests.
 *
 * @module components/cinema/Cinema.test
 */

import { render, screen, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { Cinema } from "./Cinema";
import type { CinemaScene } from "./types";

const mockScene: CinemaScene = {
  id: "test-scene",
  title: "Test Scene",
  duration: 5000,
  morphDuration: 1000,
  trends: [
    {
      id: "trend-1",
      label: "Rust",
      colorToken: "action-primary",
      points: [
        { x: 0, y: 0.2 },
        { x: 0.5, y: 0.6 },
        { x: 1, y: 0.8 },
      ],
    },
  ],
  annotations: [
    {
      text: "Growth trend",
      anchor: { x: 0.7, y: 0.65 },
      enterDelay: 500,
      duration: 4000,
    },
  ],
};

const mockScenes: CinemaScene[] = [
  mockScene,
  {
    ...mockScene,
    id: "test-scene-2",
    title: "Test Scene 2",
  },
];

interface MockMediaQueryList {
  matches: boolean;
  media: string;
  onchange: ((event: MediaQueryListEvent) => void) | null;
  addEventListener: ReturnType<typeof vi.fn>;
  removeEventListener: ReturnType<typeof vi.fn>;
  addListener: ReturnType<typeof vi.fn>;
  removeListener: ReturnType<typeof vi.fn>;
  dispatchEvent: ReturnType<typeof vi.fn>;
}

describe("Cinema", () => {
  let mockMatchMedia: ReturnType<typeof vi.fn>;
  let mockMediaQueryList: MockMediaQueryList;
  let _mockIntersectionObserver: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    mockMediaQueryList = {
      matches: false,
      media: "(prefers-reduced-motion: reduce)",
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    };

    mockMatchMedia = vi.fn().mockReturnValue(mockMediaQueryList);
    window.matchMedia = mockMatchMedia as unknown as typeof window.matchMedia;

    class MockIntersectionObserver {
      observe = vi.fn();
      unobserve = vi.fn();
      disconnect = vi.fn();
    }
    _mockIntersectionObserver = vi
      .fn()
      .mockImplementation(() => new MockIntersectionObserver());
    window.IntersectionObserver =
      MockIntersectionObserver as unknown as typeof IntersectionObserver;
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  describe("fallback rendering", () => {
    it("renders StaticFallback when scenes array is empty", () => {
      render(<Cinema scenes={[]} />);

      expect(
        screen.getByLabelText("Trend visualization temporarily unavailable"),
      ).toBeInTheDocument();
    });

    it("renders StaticFallback with loading text", () => {
      render(<Cinema scenes={[]} />);

      const svg = screen.getByLabelText(
        "Trend visualization temporarily unavailable",
      );
      const text = svg.querySelector("text");
      expect(text?.textContent).toBe("Data loading...");
    });
  });

  describe("reduced motion support", () => {
    it("renders static mode when prefers-reduced-motion is set", () => {
      mockMediaQueryList.matches = true;
      mockMatchMedia.mockReturnValue(mockMediaQueryList);

      render(<Cinema scenes={mockScenes} />);

      expect(screen.getByTestId("cinema-static")).toBeInTheDocument();
    });

    it("renders first scene statically with reduced motion", () => {
      mockMediaQueryList.matches = true;
      mockMatchMedia.mockReturnValue(mockMediaQueryList);

      render(<Cinema scenes={mockScenes} />);

      expect(screen.getByLabelText("Scene: Test Scene")).toBeInTheDocument();
    });

    it("renders trend line in reduced motion mode", () => {
      mockMediaQueryList.matches = true;
      mockMatchMedia.mockReturnValue(mockMediaQueryList);

      render(<Cinema scenes={mockScenes} />);

      expect(screen.getByLabelText("Trend line for Rust")).toBeInTheDocument();
    });

    it("renders annotations in reduced motion mode", () => {
      mockMediaQueryList.matches = true;
      mockMatchMedia.mockReturnValue(mockMediaQueryList);

      render(<Cinema scenes={mockScenes} />);

      expect(screen.getByText("Growth trend")).toBeInTheDocument();
    });
  });

  describe("animated mode", () => {
    it("renders in animated mode when motion is allowed", () => {
      render(<Cinema scenes={mockScenes} />);

      expect(screen.getByTestId("cinema-animated")).toBeInTheDocument();
    });

    it("renders trend line in animated mode", () => {
      render(<Cinema scenes={mockScenes} />);

      expect(screen.getByLabelText("Trend line for Rust")).toBeInTheDocument();
    });
  });

  describe("accessibility", () => {
    it("uses default aria-label", () => {
      render(<Cinema scenes={mockScenes} />);

      const container = screen.getByTestId("cinema-animated");
      expect(container).toBeInTheDocument();

      const stage = screen.getByRole("img");
      expect(stage.getAttribute("aria-label")).toBe(
        "Technology trend visualization",
      );
    });

    it("accepts custom aria-label", () => {
      render(
        <Cinema scenes={mockScenes} aria-label="Custom visualization label" />,
      );

      const stage = screen.getByRole("img");
      expect(stage.getAttribute("aria-label")).toBe(
        "Custom visualization label",
      );
    });
  });

  describe("styling", () => {
    it("accepts custom className", () => {
      render(<Cinema scenes={mockScenes} className="custom-cinema-class" />);

      const container = screen.getByTestId("cinema-animated");
      expect(container.className).toContain("custom-cinema-class");
    });
  });

  describe("callbacks", () => {
    it("calls onSceneChange when Director triggers scene change", async () => {
      const onSceneChange = vi.fn();

      render(<Cinema scenes={mockScenes} onSceneChange={onSceneChange} />);

      await waitFor(() => {
        expect(onSceneChange).toHaveBeenCalledWith(0, mockScenes[0]);
      });
    });
  });

  describe("autoPlay", () => {
    it("starts playback by default", async () => {
      const onSceneChange = vi.fn();

      render(<Cinema scenes={mockScenes} onSceneChange={onSceneChange} />);

      await waitFor(() => {
        expect(onSceneChange).toHaveBeenCalled();
      });
    });

    it("does not start playback when autoPlay is false", async () => {
      const onSceneChange = vi.fn();

      render(
        <Cinema
          scenes={mockScenes}
          autoPlay={false}
          onSceneChange={onSceneChange}
        />,
      );

      await act(async () => {
        vi.advanceTimersByTime(10000);
      });

      expect(onSceneChange).not.toHaveBeenCalled();
    });
  });

  describe("memory safety", () => {
    it("cleans up on unmount without errors", () => {
      const { unmount } = render(<Cinema scenes={mockScenes} />);

      expect(() => {
        unmount();
      }).not.toThrow();
    });

    it("handles rapid mount/unmount cycles", () => {
      expect(() => {
        for (let i = 0; i < 5; i++) {
          const { unmount } = render(<Cinema scenes={mockScenes} />);
          unmount();
        }
      }).not.toThrow();
    });

    it("handles StrictMode double-mount pattern", () => {
      expect(() => {
        const { unmount: unmount1 } = render(<Cinema scenes={mockScenes} />);
        unmount1();

        const { unmount: unmount2 } = render(<Cinema scenes={mockScenes} />);
        unmount2();
      }).not.toThrow();
    });
  });
});
