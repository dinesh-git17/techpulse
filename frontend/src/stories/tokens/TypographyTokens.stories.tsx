/**
 * @fileoverview Typography Tokens Storybook Documentation
 *
 * Documents the TechPulse "Data Dense" typography system with visual examples,
 * type scale demonstrations, font feature settings, and numeric data samples.
 */
import type { Meta, StoryObj } from "@storybook/react";

import {
  FONT_FEATURES,
  FONT_STACKS,
  MICRO_SIZES,
  TYPE_SCALE,
  type TypeScaleStep,
} from "../../styles/typographyTokens";

interface TypeScaleSampleProps {
  step: TypeScaleStep;
}

/**
 * Renders a type scale sample with metadata.
 */
function TypeScaleSample({ step }: TypeScaleSampleProps) {
  return (
    <div className="flex items-baseline gap-6 py-4 border-b border-border-muted">
      <div className="w-24 shrink-0">
        <span className="font-mono text-xs text-text-muted">{step.name}</span>
        <div className="text-micro text-text-secondary">
          {step.sizePx}px / {step.lineHeight}
        </div>
      </div>
      <div className="flex-1 min-w-0">
        <p className={`${step.tailwindClass} text-text-primary truncate`}>
          The quick brown fox jumps over the lazy dog
        </p>
      </div>
      <div className="w-32 shrink-0 text-right">
        <code className="text-micro text-text-muted font-mono">
          {step.tailwindClass}
        </code>
      </div>
    </div>
  );
}

interface NumericDataTableProps {
  title: string;
  fontClass: string;
}

/**
 * Demonstrates numeric alignment with tabular figures.
 */
function NumericDataTable({ title, fontClass }: NumericDataTableProps) {
  const sampleData = [
    { id: "TXN-001234", amount: 12345.67, change: "+12.5%" },
    { id: "TXN-005678", amount: 987.0, change: "-3.2%" },
    { id: "TXN-009012", amount: 45678.9, change: "+0.8%" },
    { id: "TXN-003456", amount: 1234.56, change: "-15.7%" },
  ];

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-text-primary">{title}</h4>
      <table className={`w-full text-micro ${fontClass}`}>
        <thead>
          <tr className="text-left text-text-muted border-b border-border-default">
            <th className="pb-2 pr-4">Transaction ID</th>
            <th className="pb-2 pr-4 text-right">Amount</th>
            <th className="pb-2 text-right">Change</th>
          </tr>
        </thead>
        <tbody className="text-text-secondary">
          {sampleData.map((row) => (
            <tr key={row.id} className="border-b border-border-muted">
              <td className="py-2 pr-4">{row.id}</td>
              <td className="py-2 pr-4 text-right">
                $
                {row.amount.toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                })}
              </td>
              <td
                className={`py-2 text-right ${row.change.startsWith("+") ? "text-status-success" : "text-status-danger"}`}
              >
                {row.change}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Demonstrates micro sizes with dense data.
 */
function MicroSizeDemo() {
  const metrics = [
    { label: "Total Users", value: "1,234,567", trend: "+5.2%" },
    { label: "Active Sessions", value: "89,012", trend: "+12.8%" },
    { label: "Avg. Response", value: "142ms", trend: "-8.3%" },
    { label: "Error Rate", value: "0.023%", trend: "-15.1%" },
  ];

  return (
    <div className="space-y-4">
      <h4 className="text-sm font-medium text-text-primary">
        Micro Sizes in Context
      </h4>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className="p-3 bg-surface-secondary rounded-lg border border-border-default"
          >
            <div className="text-micro-xs text-text-muted uppercase tracking-wide">
              {metric.label}
            </div>
            <div className="text-xl font-mono text-text-primary mt-1">
              {metric.value}
            </div>
            <div
              className={`text-micro font-mono mt-1 ${metric.trend.startsWith("+") ? "text-status-success" : "text-status-danger"}`}
            >
              {metric.trend}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Demonstrates font feature settings with comparison.
 */
function FontFeaturesDemo() {
  const testStrings = [
    { label: "Tabular figures", text: "1234567890" },
    { label: "Slashed zero", text: "O0 l1 I1" },
    { label: "Amount alignment", text: "$1,234.56" },
    { label: "Mixed content", text: "ID: 0l1O 1I1l" },
  ];

  return (
    <div className="space-y-4">
      <h4 className="text-sm font-medium text-text-primary">
        Font Feature Settings
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {testStrings.map((item) => (
          <div key={item.label} className="space-y-2">
            <span className="text-micro text-text-muted">{item.label}</span>
            <div className="flex gap-4 items-center">
              <div className="flex-1 p-3 bg-surface-secondary rounded border border-border-default">
                <div className="text-micro text-text-muted mb-1">Sans</div>
                <div className="text-lg font-sans text-text-primary">
                  {item.text}
                </div>
              </div>
              <div className="flex-1 p-3 bg-surface-secondary rounded border border-border-default">
                <div className="text-micro text-text-muted mb-1">Mono</div>
                <div className="text-lg font-mono text-text-primary">
                  {item.text}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Demonstrates dense data table with micro-xs size.
 */
function DenseDataDemo() {
  // pragma: allowlist nextline secret
  const rows = [
    {
      timestamp: "2026-01-14 09:15:23",
      hash: "a1b2c3d4e5f6", // pragma: allowlist secret
      status: "success",
      latency: "23ms",
    },
    {
      timestamp: "2026-01-14 09:15:24",
      hash: "f6e5d4c3b2a1", // pragma: allowlist secret
      status: "success",
      latency: "45ms",
    },
    {
      timestamp: "2026-01-14 09:15:25",
      hash: "1a2b3c4d5e6f", // pragma: allowlist secret
      status: "error",
      latency: "892ms",
    },
    {
      timestamp: "2026-01-14 09:15:26",
      hash: "6f5e4d3c2b1a", // pragma: allowlist secret
      status: "success",
      latency: "31ms",
    },
    {
      timestamp: "2026-01-14 09:15:27",
      hash: "0f1e2d3c4b5a", // pragma: allowlist secret
      status: "success",
      latency: "28ms",
    },
  ];

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-text-primary">
        Dense Data Table (11px / micro-xs)
      </h4>
      <div className="overflow-x-auto">
        <table className="w-full text-micro-xs font-mono">
          <thead>
            <tr className="text-left text-text-muted border-b border-border-default">
              <th className="pb-2 pr-4">Timestamp</th>
              <th className="pb-2 pr-4">Hash</th>
              <th className="pb-2 pr-4">Status</th>
              <th className="pb-2 text-right">Latency</th>
            </tr>
          </thead>
          <tbody className="text-text-secondary">
            {rows.map((row, index) => (
              <tr key={index} className="border-b border-border-muted">
                <td className="py-1.5 pr-4">{row.timestamp}</td>
                <td className="py-1.5 pr-4 text-text-muted">{row.hash}</td>
                <td className="py-1.5 pr-4">
                  <span
                    className={
                      row.status === "success"
                        ? "text-status-success"
                        : "text-status-danger"
                    }
                  >
                    {row.status}
                  </span>
                </td>
                <td className="py-1.5 text-right">{row.latency}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * Complete typography tokens documentation story.
 */
function TypographyTokensStory() {
  return (
    <div className="p-8 bg-surface-primary min-h-screen space-y-12">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold text-text-primary">
          TechPulse Typography System
        </h1>
        <p className="text-text-secondary max-w-2xl">
          A &quot;Data Dense&quot; type scale optimized for analytical
          dashboards. Includes micro sizes (11px, 12px) for dense data tables
          and configures tabular figures by default for aligned numeric columns.
        </p>
      </header>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Font Stacks
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Geist Sans for UI and Geist Mono for data. Both support the full
            font-feature-settings configuration.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(FONT_STACKS).map(([key, stack]) => (
            <div
              key={key}
              className="p-4 bg-surface-secondary rounded-lg border border-border-default"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-text-primary">
                  {stack.name}
                </span>
                <code className="text-micro text-text-muted font-mono">
                  {stack.tailwindClass}
                </code>
              </div>
              <p
                className={`text-lg text-text-secondary ${stack.tailwindClass}`}
              >
                ABCDEFGHIJKLMNOPQRSTUVWXYZ
                <br />
                abcdefghijklmnopqrstuvwxyz
                <br />
                0123456789 !@#$%^&*()
              </p>
              <p className="text-micro text-text-muted mt-3">{stack.useCase}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Type Scale
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Complete scale from micro-xs (11px) to 5xl (48px). Line heights are
            tuned for data density and readability.
          </p>
        </div>
        <div className="bg-surface-secondary rounded-lg border border-border-default p-4">
          {TYPE_SCALE.map((step) => (
            <TypeScaleSample key={step.name} step={step} />
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Micro Sizes
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            11px and 12px sizes for dense data tables. These sizes maintain
            legibility with generous line heights.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {MICRO_SIZES.map((step) => (
            <div
              key={step.name}
              className="p-4 bg-surface-secondary rounded-lg border border-border-default"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-sm text-text-primary">
                  {step.name}
                </span>
                <code className="text-micro text-text-muted">
                  {step.sizePx}px / {step.lineHeight}
                </code>
              </div>
              <p className={`${step.tailwindClass} text-text-secondary mb-2`}>
                The quick brown fox jumps over the lazy dog. 0123456789
              </p>
              <p className="text-micro text-text-muted">{step.useCase}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Font Features
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Global font-feature-settings ensure consistent numeric rendering
            across the application.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(FONT_FEATURES).map(([key, feature]) => (
            <div
              key={key}
              className="p-4 bg-surface-secondary rounded-lg border border-border-default"
            >
              <code className="text-action-primary font-mono">
                &quot;{feature.feature}&quot;
              </code>
              <p className="text-sm text-text-secondary mt-2">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      <FontFeaturesDemo />

      <section className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Numeric Data Examples
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Tabular figures ensure columns align regardless of digit width.
            Compare mono vs sans rendering.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <NumericDataTable title="Sans Font" fontClass="font-sans" />
          <NumericDataTable
            title="Mono Font (Recommended)"
            fontClass="font-mono"
          />
        </div>
      </section>

      <MicroSizeDemo />

      <DenseDataDemo />

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Usage Examples
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Practical examples of typography token usage in components.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Data Table Cell
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<td className="text-micro font-mono">
  {value.toLocaleString()}
</td>`}
            </pre>
          </div>

          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Metric Card
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<div className="text-micro-xs
  text-text-muted uppercase">
  {label}
</div>
<div className="text-xl font-mono">
  {value}
</div>`}
            </pre>
          </div>

          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Timestamp Display
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<time
  className="text-micro font-mono
    text-text-muted"
  data-numeric>
  {formatTimestamp(date)}
</time>`}
            </pre>
          </div>

          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              ID/Hash Display
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<code className="text-micro-xs
  font-mono text-text-secondary">
  {transactionHash}
</code>`}
            </pre>
          </div>
        </div>
      </section>
    </div>
  );
}

const meta: Meta<typeof TypographyTokensStory> = {
  title: "Design System/Typography Tokens",
  component: TypographyTokensStory,
  parameters: {
    layout: "fullscreen",
    backgrounds: { disable: true },
  },
};

export default meta;

type Story = StoryObj<typeof TypographyTokensStory>;

/**
 * Complete typography system documentation with type scale,
 * font stacks, font features, and numeric data examples.
 */
export const Default: Story = {};
