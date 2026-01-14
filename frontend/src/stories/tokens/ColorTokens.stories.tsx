/**
 * @fileoverview Color Tokens Storybook Documentation
 *
 * Documents the TechPulse semantic color system with visual swatches,
 * usage examples, and alpha-value syntax demonstrations.
 */
import type { Meta, StoryObj } from "@storybook/react";

interface ColorSwatchProps {
  name: string;
  cssVar: string;
  tailwindClass: string;
  description: string;
}

/**
 * Renders a color swatch with token information.
 */
function ColorSwatch({
  name,
  cssVar,
  tailwindClass,
  description,
}: ColorSwatchProps) {
  return (
    <div className="flex items-start gap-4 p-4 rounded-lg border border-border-default">
      <div
        className={`w-16 h-16 rounded-md border border-border-strong shrink-0 ${tailwindClass}`}
      />
      <div className="flex flex-col gap-1 min-w-0">
        <span className="font-mono text-sm text-text-primary font-medium">
          {name}
        </span>
        <code className="text-xs text-text-secondary font-mono break-all">
          {cssVar}
        </code>
        <code className="text-xs text-text-muted font-mono">{`.${tailwindClass}`}</code>
        <span className="text-xs text-text-muted mt-1">{description}</span>
      </div>
    </div>
  );
}

interface ColorGroupProps {
  title: string;
  description: string;
  children: React.ReactNode;
}

/**
 * Groups related color tokens with a title and description.
 */
function ColorGroup({ title, description, children }: ColorGroupProps) {
  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-text-primary">{title}</h2>
        <p className="text-sm text-text-secondary mt-1">{description}</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">{children}</div>
    </section>
  );
}

interface AlphaExampleProps {
  baseClass: string;
  label: string;
}

/**
 * Demonstrates alpha-value syntax with opacity modifiers.
 */
function AlphaExample({ baseClass, label }: AlphaExampleProps) {
  const opacities = [100, 80, 60, 40, 20];

  return (
    <div className="space-y-2">
      <span className="text-sm font-mono text-text-secondary">{label}</span>
      <div className="flex gap-2">
        {opacities.map((opacity) => (
          <div key={opacity} className="flex flex-col items-center gap-1">
            <div
              className={`w-12 h-12 rounded border border-border-default ${baseClass}${opacity === 100 ? "" : `/${opacity}`}`}
            />
            <span className="text-xs text-text-muted font-mono">
              {opacity === 100 ? "100" : `/${opacity}`}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Complete color tokens documentation story.
 */
function ColorTokensStory() {
  return (
    <div className="p-8 bg-surface-primary min-h-screen space-y-12">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold text-text-primary">
          TechPulse Color System
        </h1>
        <p className="text-text-secondary max-w-2xl">
          Semantic color tokens with alpha-value support. All colors use the{" "}
          <code className="text-action-primary">--tp-color-*</code> CSS variable
          naming convention and support opacity modifiers via Tailwind&apos;s{" "}
          <code className="text-action-primary">/50</code> syntax.
        </p>
      </header>

      <ColorGroup
        title="Surface Colors"
        description="Background colors for different elevation levels. Primary is the base, with secondary/tertiary for layered surfaces."
      >
        <ColorSwatch
          name="surface-primary"
          cssVar="--tp-color-surface-primary"
          tailwindClass="bg-surface-primary"
          description="Base background color for the application"
        />
        <ColorSwatch
          name="surface-secondary"
          cssVar="--tp-color-surface-secondary"
          tailwindClass="bg-surface-secondary"
          description="Elevated panels and cards"
        />
        <ColorSwatch
          name="surface-tertiary"
          cssVar="--tp-color-surface-tertiary"
          tailwindClass="bg-surface-tertiary"
          description="Higher elevation surfaces"
        />
        <ColorSwatch
          name="surface-elevated"
          cssVar="--tp-color-surface-elevated"
          tailwindClass="bg-surface-elevated"
          description="Floating elements, popovers"
        />
        <ColorSwatch
          name="surface-sunken"
          cssVar="--tp-color-surface-sunken"
          tailwindClass="bg-surface-sunken"
          description="Recessed areas, input backgrounds"
        />
      </ColorGroup>

      <ColorGroup
        title="Text Colors"
        description="Typography colors for content hierarchy. Use primary for main content, secondary for supporting text, muted for de-emphasized content."
      >
        <ColorSwatch
          name="text-primary"
          cssVar="--tp-color-text-primary"
          tailwindClass="text-text-primary"
          description="Primary content, headings, important text"
        />
        <ColorSwatch
          name="text-secondary"
          cssVar="--tp-color-text-secondary"
          tailwindClass="text-text-secondary"
          description="Supporting content, descriptions"
        />
        <ColorSwatch
          name="text-muted"
          cssVar="--tp-color-text-muted"
          tailwindClass="text-text-muted"
          description="De-emphasized text, captions, timestamps"
        />
        <ColorSwatch
          name="text-inverted"
          cssVar="--tp-color-text-inverted"
          tailwindClass="text-text-inverted"
          description="Text on colored backgrounds"
        />
      </ColorGroup>

      <ColorGroup
        title="Border Colors"
        description="Border colors for visual separation and containment."
      >
        <ColorSwatch
          name="border-default"
          cssVar="--tp-color-border-default"
          tailwindClass="border-border-default"
          description="Standard borders for containers"
        />
        <ColorSwatch
          name="border-muted"
          cssVar="--tp-color-border-muted"
          tailwindClass="border-border-muted"
          description="Subtle dividers, de-emphasized borders"
        />
        <ColorSwatch
          name="border-strong"
          cssVar="--tp-color-border-strong"
          tailwindClass="border-border-strong"
          description="Emphasized borders, active states"
        />
        <ColorSwatch
          name="border-glass"
          cssVar="--tp-color-border-glass"
          tailwindClass="border-border-glass"
          description="Glass panel shimmer effect (use with low opacity)"
        />
      </ColorGroup>

      <ColorGroup
        title="Action Colors"
        description="Interactive element colors. The brand cyan/teal is used for primary actions."
      >
        <ColorSwatch
          name="action-primary"
          cssVar="--tp-color-action-primary"
          tailwindClass="bg-action-primary"
          description="Primary buttons, links, active states"
        />
        <ColorSwatch
          name="action-primary-hover"
          cssVar="--tp-color-action-primary-hover"
          tailwindClass="bg-action-primary-hover"
          description="Hover state for primary actions"
        />
        <ColorSwatch
          name="action-primary-active"
          cssVar="--tp-color-action-primary-active"
          tailwindClass="bg-action-primary-active"
          description="Active/pressed state for primary actions"
        />
      </ColorGroup>

      <ColorGroup
        title="Status Colors"
        description="Semantic colors for communicating state and feedback."
      >
        <ColorSwatch
          name="status-success"
          cssVar="--tp-color-status-success"
          tailwindClass="bg-status-success"
          description="Success states, confirmations, positive indicators"
        />
        <ColorSwatch
          name="status-warning"
          cssVar="--tp-color-status-warning"
          tailwindClass="bg-status-warning"
          description="Warning states, caution indicators"
        />
        <ColorSwatch
          name="status-danger"
          cssVar="--tp-color-status-danger"
          tailwindClass="bg-status-danger"
          description="Error states, destructive actions"
        />
      </ColorGroup>

      <ColorGroup
        title="Interactive States"
        description="Colors for focus indicators and highlighted elements."
      >
        <ColorSwatch
          name="focus-ring"
          cssVar="--tp-color-focus-ring"
          tailwindClass="ring-focus-ring"
          description="Focus indicator ring color"
        />
        <ColorSwatch
          name="highlight"
          cssVar="--tp-color-highlight"
          tailwindClass="bg-highlight"
          description="Selection highlight, hover backgrounds"
        />
      </ColorGroup>

      <section className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Brand Color Scale
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Full cyan/teal brand palette from 50-950. Use semantic tokens when
            possible; these are available for edge cases.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {[50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950].map(
            (shade) => (
              <div key={shade} className="flex flex-col items-center gap-1">
                <div
                  className={`w-12 h-12 rounded border border-border-default bg-brand-${shade}`}
                />
                <span className="text-xs text-text-muted font-mono">
                  {shade}
                </span>
              </div>
            ),
          )}
        </div>
      </section>

      <section className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Alpha Value Syntax
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            All semantic colors support Tailwind&apos;s{" "}
            <code className="text-action-primary">/opacity</code> modifier for
            transparency.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <AlphaExample
            baseClass="bg-surface-tertiary"
            label="bg-surface-tertiary"
          />
          <AlphaExample
            baseClass="bg-action-primary"
            label="bg-action-primary"
          />
          <AlphaExample
            baseClass="bg-status-success"
            label="bg-status-success"
          />
          <AlphaExample baseClass="bg-brand-500" label="bg-brand-500" />
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Usage Examples
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            Practical examples of color token usage in components.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Card Component
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<div className="bg-surface-secondary
  border border-border-default
  rounded-lg p-4">
  <h2 className="text-text-primary">
    Title
  </h2>
  <p className="text-text-secondary">
    Description
  </p>
</div>`}
            </pre>
          </div>

          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Glass Panel (with alpha)
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<div className="bg-surface-primary/80
  backdrop-blur-md
  border border-border-glass/10
  rounded-lg p-4">
  Glass content
</div>`}
            </pre>
          </div>

          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Primary Button
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<button className="bg-action-primary
  hover:bg-action-primary-hover
  active:bg-action-primary-active
  text-text-inverted
  px-4 py-2 rounded-md">
  Submit
</button>`}
            </pre>
          </div>

          <div className="p-4 bg-surface-secondary rounded-lg border border-border-default">
            <h3 className="text-sm font-semibold text-text-primary mb-2">
              Status Badge
            </h3>
            <pre className="text-xs text-text-muted font-mono whitespace-pre-wrap">
              {`<span className="bg-status-success/20
  text-status-success
  px-2 py-1 rounded text-sm">
  Active
</span>`}
            </pre>
          </div>
        </div>
      </section>
    </div>
  );
}

const meta: Meta<typeof ColorTokensStory> = {
  title: "Design System/Color Tokens",
  component: ColorTokensStory,
  parameters: {
    layout: "fullscreen",
    backgrounds: { disable: true },
  },
};

export default meta;

type Story = StoryObj<typeof ColorTokensStory>;

/**
 * Complete color system documentation with all semantic tokens,
 * brand palette, alpha-value examples, and usage patterns.
 */
export const Default: Story = {};
