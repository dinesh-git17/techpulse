/**
 * @fileoverview Elevation Tokens Storybook Documentation
 *
 * Documents the TechPulse z-index and elevation system with visual stacking
 * demonstrations, layer hierarchy, and portal strategy documentation.
 */
import type { Meta, StoryObj } from "@storybook/react";

import {
  DISABLED_Z_INDEX_UTILITIES,
  ELEVATION_LAYERS,
  PORTAL_CONFIG,
  STACKING_CONTEXT_CLASS,
  type ElevationLayer,
} from "../../styles/elevationTokens";

interface LayerCardProps {
  layer: ElevationLayer;
  index: number;
}

/**
 * Renders documentation for a single elevation layer.
 */
function LayerCard({ layer, index }: LayerCardProps) {
  return (
    <div className="flex items-center gap-4 p-4 bg-surface-secondary rounded-lg border border-border-default">
      <div className="w-12 h-12 flex items-center justify-center bg-surface-tertiary rounded-md border border-border-strong">
        <span className="text-lg font-mono text-action-primary font-bold">
          {layer.value}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-text-primary">{layer.name}</span>
          <code className="text-micro text-text-muted font-mono px-1.5 py-0.5 bg-surface-tertiary rounded">
            {layer.tailwindClass}
          </code>
        </div>
        <p className="text-sm text-text-secondary mt-1">{layer.useCase}</p>
        <code className="text-micro text-text-muted font-mono">
          {layer.cssVar}
        </code>
      </div>
      <div className="text-micro text-text-muted">Layer {index + 1}</div>
    </div>
  );
}

/**
 * Interactive stacking demonstration showing how layers overlap.
 */
function StackingDemo() {
  const layerColors = [
    "bg-brand-950",
    "bg-brand-900",
    "bg-brand-800",
    "bg-brand-700",
    "bg-brand-600",
    "bg-brand-500",
  ];

  return (
    <div className="relative h-80 bg-surface-sunken rounded-lg border border-border-default overflow-hidden">
      {ELEVATION_LAYERS.map((layer, index) => {
        const offset = index * 40;
        const width = 280 - index * 20;

        return (
          <div
            key={layer.name}
            className={`absolute ${layer.tailwindClass} ${layerColors[index]} rounded-lg border border-border-glass/20 p-3 shadow-lg`}
            style={{
              top: offset + 20,
              left: offset + 20,
              width: width,
              height: 80,
            }}
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-white">
                {layer.name}
              </span>
              <code className="text-micro text-white/70 font-mono">
                z-{layer.value}
              </code>
            </div>
            <p className="text-micro text-white/60 mt-1">{layer.useCase}</p>
          </div>
        );
      })}
    </div>
  );
}

/**
 * Demonstrates the stacking context isolation utility.
 */
function StackingContextDemo() {
  return (
    <div className="space-y-4">
      <h4 className="text-sm font-medium text-text-primary">
        Stacking Context Isolation
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <span className="text-micro text-text-muted">
            Without isolation (z-index leaks)
          </span>
          <div className="relative h-32 bg-surface-secondary rounded-lg border border-border-default p-4">
            <div className="absolute top-4 left-4 w-24 h-16 bg-status-danger/80 rounded z-raised flex items-center justify-center">
              <span className="text-micro text-white font-mono">z-raised</span>
            </div>
            <div className="absolute top-8 left-12 w-24 h-16 bg-status-success/80 rounded z-sticky flex items-center justify-center">
              <span className="text-micro text-white font-mono">z-sticky</span>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <span className="text-micro text-text-muted">
            With <code className="text-action-primary">.stacking-context</code>
          </span>
          <div className="relative h-32 bg-surface-secondary rounded-lg border border-border-default p-4">
            <div className="stacking-context absolute top-4 left-4">
              <div className="relative w-24 h-16 bg-status-danger/80 rounded z-raised flex items-center justify-center">
                <span className="text-micro text-white font-mono">
                  isolated
                </span>
              </div>
            </div>
            <div className="stacking-context absolute top-8 left-12">
              <div className="relative w-24 h-16 bg-status-success/80 rounded z-raised flex items-center justify-center">
                <span className="text-micro text-white font-mono">
                  isolated
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Visual representation of the layer stack.
 */
function LayerStackVisualization() {
  return (
    <div className="space-y-4">
      <h4 className="text-sm font-medium text-text-primary">Layer Stack</h4>
      <div className="flex items-end gap-1 h-48 p-4 bg-surface-secondary rounded-lg border border-border-default">
        {ELEVATION_LAYERS.map((layer, index) => {
          const height = ((index + 1) / ELEVATION_LAYERS.length) * 100;
          return (
            <div
              key={layer.name}
              className="flex-1 flex flex-col items-center justify-end"
            >
              <div
                className="w-full bg-gradient-to-t from-action-primary to-brand-300 rounded-t opacity-80 flex items-end justify-center pb-2"
                style={{ height: `${height}%` }}
              >
                <span className="text-micro font-mono text-white/90 font-medium">
                  {layer.value}
                </span>
              </div>
              <span className="text-micro text-text-muted mt-2 font-mono">
                {layer.name}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Complete elevation tokens documentation story.
 */
function ElevationTokensStory() {
  return (
    <div className="p-8 bg-surface-primary min-h-screen space-y-12">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold text-text-primary">
          TechPulse Elevation System
        </h1>
        <p className="text-text-secondary max-w-2xl">
          A strict, semantic z-index scale with exactly 6 named layers.
          Arbitrary z-indices like{" "}
          <code className="text-status-danger">z-[9999]</code> or{" "}
          <code className="text-status-danger">z-50</code> are prohibited. Use
          the semantic classes to ensure predictable stacking behavior.
        </p>
      </header>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Elevation Layers
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Six semantic layers from base (0) to toast (400). Each layer has a
            specific purpose and use case.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-3">
          {ELEVATION_LAYERS.map((layer, index) => (
            <LayerCard key={layer.name} layer={layer} index={index} />
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Visual Stacking Demo
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Interactive visualization showing how layers stack on top of each
            other. Lower layers are rendered behind higher layers.
          </p>
        </div>
        <StackingDemo />
      </section>

      <LayerStackVisualization />

      <StackingContextDemo />

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Portal Strategy
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Elements that need to bypass the main stacking context use React
            portals.
          </p>
        </div>
        <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
          <div className="flex items-center gap-3 mb-3">
            <span className="font-semibold text-text-primary">Tooltips</span>
            <code className="text-micro text-action-primary font-mono px-1.5 py-0.5 bg-surface-tertiary rounded">
              z-index: {PORTAL_CONFIG.tooltip.zIndex}
            </code>
          </div>
          <p className="text-sm text-text-secondary mb-3">
            {PORTAL_CONFIG.tooltip.description}
          </p>
          <pre className="text-xs text-text-muted font-mono bg-surface-sunken p-3 rounded overflow-x-auto">
            {`import { createPortal } from 'react-dom';

// Tooltip component renders via portal
createPortal(
  <div style={{ zIndex: ${PORTAL_CONFIG.tooltip.zIndex} }}>
    <Tooltip content={content} />
  </div>,
  document.body
);`}
          </pre>
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Disabled Utilities
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Default Tailwind z-index utilities are disabled. Using these will
            have no effect.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {DISABLED_Z_INDEX_UTILITIES.map((utility) => (
            <code
              key={utility}
              className="text-sm text-status-danger font-mono px-2 py-1 bg-status-danger/10 rounded border border-status-danger/20 line-through"
            >
              {utility}
            </code>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Usage Examples
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Practical examples of elevation token usage in components.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Sticky Header
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<header className="sticky top-0
  z-sticky bg-surface-primary/90
  backdrop-blur-sm border-b
  border-border-default">
  Navigation
</header>`}
            </pre>
          </div>

          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Dropdown Menu
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<div className="relative">
  <button>Open</button>
  <div className="absolute z-overlay
    bg-surface-elevated
    border border-border-default
    rounded-lg shadow-lg">
    Menu items
  </div>
</div>`}
            </pre>
          </div>

          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Modal Dialog
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<div className="fixed inset-0
  z-modal bg-black/50">
  <div className="bg-surface-elevated
    rounded-xl p-6">
    Modal content
  </div>
</div>`}
            </pre>
          </div>

          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Stacking Context
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<section className="stacking-context">
  {/* z-index values inside this
      section won't affect siblings */}
  <Card className="z-raised" />
  <Overlay className="z-overlay" />
</section>`}
            </pre>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Best Practices
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-status-success/10 rounded-lg border border-status-success/20">
            <h4 className="text-sm font-semibold text-status-success mb-2">
              Do
            </h4>
            <ul className="text-sm text-text-secondary space-y-1">
              <li>• Use semantic classes: z-sticky, z-overlay, z-modal</li>
              <li>• Create stacking contexts with .{STACKING_CONTEXT_CLASS}</li>
              <li>• Use portals for tooltips that need to escape containers</li>
              <li>• Keep related elements in the same stacking context</li>
            </ul>
          </div>
          <div className="p-4 bg-status-danger/10 rounded-lg border border-status-danger/20">
            <h4 className="text-sm font-semibold text-status-danger mb-2">
              Don&apos;t
            </h4>
            <ul className="text-sm text-text-secondary space-y-1">
              <li>• Use arbitrary values: z-[9999], z-[100]</li>
              <li>• Use default utilities: z-50, z-10, z-auto</li>
              <li>• Mix semantic and numeric z-index values</li>
              <li>• Nest overlays within overlays without isolation</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}

const meta: Meta<typeof ElevationTokensStory> = {
  title: "Design System/Elevation Tokens",
  component: ElevationTokensStory,
  parameters: {
    layout: "fullscreen",
    backgrounds: { disable: true },
  },
};

export default meta;

type Story = StoryObj<typeof ElevationTokensStory>;

/**
 * Complete elevation system documentation with layer hierarchy,
 * visual stacking demo, portal strategy, and usage examples.
 */
export const Default: Story = {};
