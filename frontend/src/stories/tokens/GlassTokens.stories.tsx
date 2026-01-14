/**
 * @fileoverview Glass Tokens Storybook Documentation
 *
 * Documents the TechPulse glass utility primitives with visual demonstrations,
 * tier comparisons, noise texture, and accessibility fallback states.
 */
import { useState } from "react";

import type { Meta, StoryObj } from "@storybook/react";

import {
  A11Y_MEDIA_QUERIES,
  FORCED_COLORS,
  GLASS_CLASS_NAMES,
  GLASS_CONTRAST_RATIOS,
  GLASS_TIERS,
  type GlassContrastRatio,
  type GlassTier,
  MAX_GLASS_NESTING_DEPTH,
  NOISE_TEXTURE,
  REDUCED_TRANSPARENCY_FALLBACKS,
  SHIMMER_BORDER,
  WCAG_CONTRAST_THRESHOLDS,
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
 * Contrast ratio badge component.
 */
function ContrastBadge({ ratio }: { ratio: GlassContrastRatio }) {
  const getStatusColor = () => {
    if (ratio.meetsAAA) return "bg-status-success/20 text-status-success";
    if (ratio.meetsAA) return "bg-status-warning/20 text-status-warning";
    return "bg-status-danger/20 text-status-danger";
  };

  const getLabel = () => {
    if (ratio.meetsAAA) return "AAA";
    if (ratio.meetsAA) return "AA";
    return "Fail";
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-micro font-medium ${getStatusColor()}`}
    >
      {getLabel()} ({ratio.ratio}:1)
    </span>
  );
}

/**
 * Demonstrates contrast ratios for text on glass surfaces.
 */
function ContrastRatiosDemo() {
  const tiers = ["subtle", "panel", "overlay"] as const;
  const textTokens = ["text-primary", "text-secondary", "text-muted"] as const;

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-medium text-text-primary">
          Contrast Ratios (WCAG Compliance)
        </h4>
        <p className="text-micro text-text-muted mt-1">
          Pre-calculated contrast ratios for text on glass surfaces. WCAG AA
          requires 4.5:1 for normal text, 3:1 for large text.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border-default">
              <th className="text-left py-2 px-3 text-text-secondary font-medium">
                Glass Tier
              </th>
              {textTokens.map((token) => (
                <th
                  key={token}
                  className="text-left py-2 px-3 text-text-secondary font-medium"
                >
                  <code className="text-micro font-mono">{token}</code>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tiers.map((tier) => (
              <tr key={tier} className="border-b border-border-muted">
                <td className="py-2 px-3">
                  <code className="text-action-primary font-mono text-micro">
                    .glass-{tier}
                  </code>
                </td>
                {textTokens.map((token) => {
                  const ratio = GLASS_CONTRAST_RATIOS.find(
                    (r) => r.tier === tier && r.textToken === token,
                  );
                  return (
                    <td key={token} className="py-2 px-3">
                      {ratio && <ContrastBadge ratio={ratio} />}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-micro">
        <div className="p-2 bg-status-success/10 rounded border border-status-success/20">
          <span className="font-medium text-status-success">AAA</span>
          <span className="text-text-secondary ml-1">
            ≥{WCAG_CONTRAST_THRESHOLDS.AAA_NORMAL}:1 (enhanced)
          </span>
        </div>
        <div className="p-2 bg-status-warning/10 rounded border border-status-warning/20">
          <span className="font-medium text-status-warning">AA</span>
          <span className="text-text-secondary ml-1">
            ≥{WCAG_CONTRAST_THRESHOLDS.AA_NORMAL}:1 (minimum)
          </span>
        </div>
        <div className="p-2 bg-status-danger/10 rounded border border-status-danger/20">
          <span className="font-medium text-status-danger">Fail</span>
          <span className="text-text-secondary ml-1">
            &lt;{WCAG_CONTRAST_THRESHOLDS.AA_NORMAL}:1 (non-compliant)
          </span>
        </div>
      </div>

      <div className="p-3 bg-surface-tertiary rounded-lg text-micro text-text-secondary">
        <strong className="text-text-primary">Recommendation:</strong> Use{" "}
        <code className="text-action-primary">text-primary</code> for all body
        text on glass surfaces. Reserve{" "}
        <code className="text-action-primary">text-secondary</code> for
        supplementary labels on subtle/panel tiers only.
      </div>
    </div>
  );
}

type A11yMode = "standard" | "reduced-transparency" | "forced-colors";

/**
 * Demonstrates accessibility fallback states with interactive toggles.
 */
function A11yFallbackDemo() {
  const [mode, setMode] = useState<A11yMode>("standard");

  const getModeStyles = (tier: "subtle" | "panel" | "overlay") => {
    if (mode === "reduced-transparency") {
      const fallback =
        REDUCED_TRANSPARENCY_FALLBACKS[
          tier as keyof typeof REDUCED_TRANSPARENCY_FALLBACKS
        ];
      return {
        background: `rgb(var(${fallback}))`,
        backdropFilter: "none",
        border:
          tier !== "subtle"
            ? "1px solid rgb(var(--tp-color-border-default))"
            : "none",
      };
    }
    if (mode === "forced-colors") {
      return {
        background: FORCED_COLORS.background,
        backdropFilter: "none",
        border: `1px solid ${FORCED_COLORS.border}`,
        color: FORCED_COLORS.text,
      };
    }
    return undefined;
  };

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-medium text-text-primary">
          Accessibility Fallback States
        </h4>
        <p className="text-micro text-text-muted mt-1">
          Toggle between rendering modes to preview how glass surfaces degrade
          for users with accessibility preferences.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {(
          [
            { value: "standard", label: "Standard" },
            { value: "reduced-transparency", label: "Reduced Transparency" },
            { value: "forced-colors", label: "Forced Colors (High Contrast)" },
          ] as const
        ).map(({ value, label }) => (
          <button
            key={value}
            onClick={() => setMode(value)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              mode === value
                ? "bg-action-primary text-text-inverted"
                : "bg-surface-tertiary text-text-secondary hover:bg-surface-elevated"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="relative rounded-xl overflow-hidden">
        <div
          className="absolute inset-0"
          style={{
            background:
              mode === "forced-colors"
                ? FORCED_COLORS.background
                : "linear-gradient(135deg, rgb(var(--tp-primitive-brand-600)) 0%, rgb(var(--tp-primitive-brand-950)) 100%)",
          }}
        />

        <div className="relative p-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          {(["subtle", "panel", "overlay"] as const).map((tier) => {
            const glassClass = `glass-${tier}`;
            const styles = getModeStyles(tier);

            return (
              <div
                key={tier}
                className={`rounded-xl p-4 min-h-32 ${mode === "standard" ? glassClass : ""}`}
                style={styles}
              >
                <div className="relative z-10">
                  <h5
                    className="font-semibold mb-1"
                    style={
                      mode === "forced-colors"
                        ? { color: FORCED_COLORS.text }
                        : undefined
                    }
                  >
                    {tier.charAt(0).toUpperCase() + tier.slice(1)}
                  </h5>
                  <p
                    className="text-micro"
                    style={
                      mode === "forced-colors"
                        ? { color: FORCED_COLORS.text }
                        : undefined
                    }
                  >
                    {mode === "standard" && "Glass effect active"}
                    {mode === "reduced-transparency" && "Solid background"}
                    {mode === "forced-colors" && "System colors"}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-micro">
        <div className="p-3 bg-surface-secondary rounded-lg border border-border-default">
          <h5 className="font-medium text-text-primary mb-1">
            Reduced Transparency
          </h5>
          <p className="text-text-secondary mb-2">
            Triggered by{" "}
            <code className="text-action-primary">
              @media ({A11Y_MEDIA_QUERIES.reducedTransparency})
            </code>
          </p>
          <ul className="text-text-muted space-y-1">
            <li>• Removes backdrop-filter blur</li>
            <li>• Replaces with solid semantic surfaces</li>
            <li>• Hides noise texture pseudo-elements</li>
          </ul>
        </div>
        <div className="p-3 bg-surface-secondary rounded-lg border border-border-default">
          <h5 className="font-medium text-text-primary mb-1">
            Forced Colors (Windows High Contrast)
          </h5>
          <p className="text-text-secondary mb-2">
            Triggered by{" "}
            <code className="text-action-primary">
              @media ({A11Y_MEDIA_QUERIES.forcedColors})
            </code>
          </p>
          <ul className="text-text-muted space-y-1">
            <li>
              • Uses CSS system colors ({FORCED_COLORS.background},{" "}
              {FORCED_COLORS.text})
            </li>
            <li>• Adds visible borders for edge definition</li>
            <li>• Adapts to user&apos;s chosen theme</li>
          </ul>
        </div>
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
            Accessibility
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Glass surfaces gracefully degrade for users with accessibility
            preferences. Toggle between modes to preview fallback states.
          </p>
        </div>
        <A11yFallbackDemo />
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Contrast Compliance
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Text on glass surfaces must meet WCAG AA contrast requirements. Use
            text-primary for body text; reserve muted colors for non-critical
            labels.
          </p>
        </div>
        <ContrastRatiosDemo />
      </section>

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
