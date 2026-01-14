/**
 * @fileoverview Glass Tokens Storybook Documentation
 *
 * Documents the TechPulse glass utility primitives with visual demonstrations,
 * tier comparisons, noise texture, and accessibility fallback states.
 */
import type { Meta, StoryObj } from "@storybook/react";

import {
  GLASS_CLASS_NAMES,
  GLASS_TIERS,
  MAX_GLASS_NESTING_DEPTH,
  NOISE_TEXTURE,
  SHIMMER_BORDER,
  type GlassTier,
} from "../../styles/glassTokens";

interface GlassTierCardProps {
  tier: GlassTier;
}

/**
 * Renders documentation for a single glass tier.
 */
function GlassTierCard({ tier }: GlassTierCardProps) {
  return (
    <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
      <div className="flex items-center justify-between mb-3">
        <span className="font-semibold text-text-primary">{tier.name}</span>
        <code className="text-micro text-text-muted font-mono px-1.5 py-0.5 bg-surface-tertiary rounded">
          .{tier.className}
        </code>
      </div>
      <div className="grid grid-cols-3 gap-2 text-micro text-text-secondary mb-3">
        <div>
          <span className="text-text-muted">Blur:</span>{" "}
          <span className="font-mono">
            {tier.blur.replace("backdrop-", "")}
          </span>
        </div>
        <div>
          <span className="text-text-muted">Opacity:</span>{" "}
          <span className="font-mono">{tier.opacity}%</span>
        </div>
        <div>
          <span className="text-text-muted">Border:</span>{" "}
          <span className="font-mono">
            {tier.hasBorder ? "shimmer" : "none"}
          </span>
        </div>
      </div>
      <p className="text-sm text-text-muted">{tier.useCase}</p>
    </div>
  );
}

/**
 * Visual demonstration of all three glass tiers against a gradient background.
 */
function GlassTiersDemo() {
  return (
    <div className="relative rounded-xl overflow-hidden">
      <div
        className="absolute inset-0 bg-gradient-to-br from-brand-600 via-brand-800 to-brand-950"
        style={{
          backgroundImage: `
            radial-gradient(ellipse at 30% 20%, rgba(56, 189, 248, 0.3) 0%, transparent 50%),
            radial-gradient(ellipse at 70% 80%, rgba(14, 165, 233, 0.2) 0%, transparent 50%),
            linear-gradient(135deg, rgb(var(--tp-primitive-brand-600)) 0%, rgb(var(--tp-primitive-brand-950)) 100%)
          `,
        }}
      />

      <div className="relative p-8 min-h-96">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {GLASS_TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`${tier.className} rounded-xl p-6 min-h-48 flex flex-col`}
            >
              <div className="relative z-10">
                <h3 className="text-lg font-semibold text-text-primary mb-2">
                  {tier.name.charAt(0).toUpperCase() + tier.name.slice(1)}
                </h3>
                <p className="text-sm text-text-secondary mb-4">
                  {tier.useCase}
                </p>
                <div className="space-y-1 text-micro font-mono text-text-muted">
                  <div>blur: {tier.blur.replace("backdrop-", "")}</div>
                  <div>opacity: {tier.opacity}%</div>
                  <div>border: {tier.hasBorder ? "1px shimmer" : "none"}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * Demonstrates the noise texture effect on glass surfaces.
 */
function NoiseTextureDemo() {
  return (
    <div className="space-y-4">
      <h4 className="text-sm font-medium text-text-primary">
        Noise Texture Comparison
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="relative rounded-xl overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-brand-500 to-brand-800" />
          <div
            className="relative p-6 rounded-xl"
            style={{
              background: "rgb(var(--tp-color-surface-primary) / 0.7)",
              backdropFilter: "blur(12px)",
            }}
          >
            <h5 className="text-sm font-medium text-text-primary mb-2">
              Without Noise
            </h5>
            <p className="text-sm text-text-secondary">
              Smooth glass surface may show color banding artifacts on some
              displays.
            </p>
          </div>
        </div>

        <div className="relative rounded-xl overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-brand-500 to-brand-800" />
          <div className="glass-panel relative p-6 rounded-xl">
            <div className="relative z-10">
              <h5 className="text-sm font-medium text-text-primary mb-2">
                With Noise Texture
              </h5>
              <p className="text-sm text-text-secondary">
                Subtle noise prevents banding and provides optical
                &quot;surface&quot; definition.
              </p>
            </div>
          </div>
        </div>
      </div>
      <div className="p-3 bg-surface-tertiary rounded-lg">
        <code className="text-micro text-text-muted font-mono">
          Noise config: baseFrequency={NOISE_TEXTURE.baseFrequency}, octaves=
          {NOISE_TEXTURE.numOctaves}, opacity={NOISE_TEXTURE.opacity}
        </code>
      </div>
    </div>
  );
}

/**
 * Demonstrates the shimmer border effect.
 */
function ShimmerBorderDemo() {
  return (
    <div className="space-y-4">
      <h4 className="text-sm font-medium text-text-primary">Shimmer Border</h4>
      <div className="relative rounded-xl overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-600 to-brand-900" />
        <div className="relative p-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-surface-primary/80 backdrop-blur-md">
            <span className="text-sm text-text-secondary">No border</span>
          </div>
          <div className="p-4 rounded-lg bg-surface-primary/80 backdrop-blur-md border border-border-default">
            <span className="text-sm text-text-secondary">Default border</span>
          </div>
          <div className="p-4 rounded-lg bg-surface-primary/80 backdrop-blur-md border-shimmer">
            <span className="text-sm text-text-secondary">Shimmer border</span>
          </div>
        </div>
      </div>
      <div className="p-3 bg-surface-tertiary rounded-lg">
        <code className="text-micro text-text-muted font-mono">
          Shimmer: {SHIMMER_BORDER.width} solid rgba(
          {SHIMMER_BORDER.cssVar} / {SHIMMER_BORDER.opacity})
        </code>
      </div>
    </div>
  );
}

/**
 * Demonstrates nesting violation scenario.
 */
function NestingDemo() {
  return (
    <div className="space-y-4">
      <h4 className="text-sm font-medium text-text-primary">
        Nesting Depth Limits
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <span className="text-micro text-text-muted">
            Valid: 2 layers (max allowed)
          </span>
          <div className="relative rounded-xl overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-brand-500 to-brand-800" />
            <div className="glass-subtle relative p-4 rounded-xl">
              <div className="glass-panel relative p-4 rounded-lg">
                <div className="relative z-10 text-sm text-text-secondary">
                  Nested content (2 layers)
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <span className="text-micro text-status-danger">
            Invalid: 3+ layers (ESLint warning)
          </span>
          <div className="relative rounded-xl overflow-hidden border-2 border-status-danger/30">
            <div className="absolute inset-0 bg-gradient-to-br from-brand-500 to-brand-800" />
            <div className="glass-subtle relative p-3 rounded-xl">
              <div className="glass-panel relative p-3 rounded-lg">
                <div className="glass-overlay relative p-3 rounded">
                  <div className="relative z-10 text-sm text-text-secondary">
                    &quot;Muddy&quot; effect (3 layers)
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="p-4 bg-status-warning/10 rounded-lg border border-status-warning/20">
        <p className="text-sm text-text-secondary">
          <strong className="text-status-warning">ESLint Rule:</strong>{" "}
          <code className="text-action-primary font-mono">
            techpulse/no-nested-glass
          </code>{" "}
          warns when glass/blur utilities exceed {MAX_GLASS_NESTING_DEPTH}{" "}
          layers of nesting.
        </p>
      </div>
    </div>
  );
}

/**
 * Complete glass tokens documentation story.
 */
function GlassTokensStory() {
  return (
    <div className="p-8 bg-surface-primary min-h-screen space-y-12">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold text-text-primary">
          TechPulse Glass Primitives
        </h1>
        <p className="text-text-secondary max-w-2xl">
          Three-tier glass scale for the &quot;Glass Cockpit&quot; aesthetic.
          Each tier combines blur, opacity, border, and noise texture. Use
          restraint: glass effects are GPU-intensive and should only be applied
          to floating layers.
        </p>
      </header>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Glass Tiers
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Three semantic tiers from subtle (headers) to overlay (modals). Each
            tier combines blur intensity, background opacity, and optional
            shimmer border.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {GLASS_TIERS.map((tier) => (
            <GlassTierCard key={tier.name} tier={tier} />
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Visual Demonstration
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            All three glass tiers rendered against a gradient background showing
            relative translucency and blur intensity.
          </p>
        </div>
        <GlassTiersDemo />
      </section>

      <NoiseTextureDemo />

      <ShimmerBorderDemo />

      <NestingDemo />

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Available Classes
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Use these utility classes to apply glass effects. Each class is
            self-contained with blur, opacity, border, and noise.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {GLASS_CLASS_NAMES.map((className) => (
            <code
              key={className}
              className="text-sm text-action-primary font-mono px-3 py-1.5 bg-surface-tertiary rounded-lg border border-border-default"
            >
              .{className}
            </code>
          ))}
          <code className="text-sm text-action-primary font-mono px-3 py-1.5 bg-surface-tertiary rounded-lg border border-border-default">
            .glass-noise
          </code>
          <code className="text-sm text-action-primary font-mono px-3 py-1.5 bg-surface-tertiary rounded-lg border border-border-default">
            .border-shimmer
          </code>
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Usage Examples
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Practical examples of glass utility usage in components.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Sticky Header
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<header className="sticky top-0
  z-sticky glass-subtle">
  Navigation content
</header>`}
            </pre>
          </div>

          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Dashboard Widget
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<div className="glass-panel
  rounded-xl p-6">
  <h2>Metrics</h2>
  <MetricChart />
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
  <div className="glass-overlay
    rounded-2xl p-8">
    Modal content
  </div>
</div>`}
            </pre>
          </div>

          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Custom Noise Only
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<div className="relative
  bg-surface-secondary/80
  backdrop-blur-sm glass-noise">
  Custom glass surface
</div>`}
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
              <li>
                &bull; Use glass-subtle for headers, glass-panel for widgets
              </li>
              <li>&bull; Apply glass only to floating/overlapping surfaces</li>
              <li>&bull; Keep glass nesting to 2 layers maximum</li>
              <li>&bull; Ensure sufficient contrast for text on glass</li>
            </ul>
          </div>
          <div className="p-4 bg-status-danger/10 rounded-lg border border-status-danger/20">
            <h4 className="text-sm font-semibold text-status-danger mb-2">
              Don&apos;t
            </h4>
            <ul className="text-sm text-text-secondary space-y-1">
              <li>&bull; Apply glass to entire page backgrounds</li>
              <li>&bull; Nest more than 2 glass layers (ESLint enforced)</li>
              <li>&bull; Mix glass classes with manual backdrop-blur</li>
              <li>&bull; Use glass on content-heavy areas without contrast</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}

const meta: Meta<typeof GlassTokensStory> = {
  title: "Design System/Glass Tokens",
  component: GlassTokensStory,
  parameters: {
    layout: "fullscreen",
    backgrounds: { disable: true },
  },
};

export default meta;

type Story = StoryObj<typeof GlassTokensStory>;

/**
 * Complete glass primitives documentation with tier comparison,
 * noise texture, shimmer border, and nesting rules.
 */
export const Default: Story = {};
