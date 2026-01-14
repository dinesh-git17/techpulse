/**
 * @fileoverview ESLint rule to prevent excessive glass/blur nesting
 *
 * Glass effects with backdrop-filter are GPU-intensive. Nesting more than
 * 2 glass layers causes:
 * 1. "Muddy" visual effect (grey soup)
 * 2. Scroll jank on lower-end devices
 * 3. Unpredictable rendering behavior
 *
 * This rule warns when glass utilities are nested beyond the allowed depth.
 */

/**
 * Glass utility class names that constitute a "glass layer".
 */
const GLASS_CLASSES = ["glass-subtle", "glass-panel", "glass-overlay"];

/**
 * Backdrop blur classes that also count as glass layers.
 */
const BLUR_CLASSES = [
  "backdrop-blur",
  "backdrop-blur-none",
  "backdrop-blur-sm",
  "backdrop-blur-md",
  "backdrop-blur-lg",
  "backdrop-blur-xl",
  "backdrop-blur-2xl",
  "backdrop-blur-3xl",
];

/**
 * All classes that constitute a glass/blur layer.
 */
const ALL_GLASS_BLUR_CLASSES = [...GLASS_CLASSES, ...BLUR_CLASSES];

/**
 * Maximum allowed depth of nested glass/blur layers.
 */
const MAX_NESTING_DEPTH = 2;

/**
 * Check if a className string contains any glass/blur classes.
 *
 * @param {string} classNameValue - The className attribute value.
 * @returns {string[]} Array of glass/blur classes found.
 */
function extractGlassClasses(classNameValue) {
  if (typeof classNameValue !== "string") {
    return [];
  }
  return classNameValue
    .split(/\s+/)
    .filter((cls) => ALL_GLASS_BLUR_CLASSES.some((gc) => cls.startsWith(gc)));
}

/**
 * Get the className value from a JSX attribute node.
 *
 * @param {object} node - AST node for the className attribute.
 * @returns {string|null} The className string value or null.
 */
function getClassNameValue(node) {
  if (!node || !node.value) {
    return null;
  }

  if (node.value.type === "Literal") {
    return node.value.value;
  }

  if (
    node.value.type === "JSXExpressionContainer" &&
    node.value.expression.type === "Literal"
  ) {
    return node.value.expression.value;
  }

  if (
    node.value.type === "JSXExpressionContainer" &&
    node.value.expression.type === "TemplateLiteral" &&
    node.value.expression.quasis.length === 1
  ) {
    return node.value.expression.quasis[0].value.raw;
  }

  return null;
}

/**
 * Check if a JSX element has glass/blur classes.
 *
 * @param {object} node - JSXOpeningElement AST node.
 * @returns {string[]} Array of glass/blur classes found.
 */
function getGlassClassesFromElement(node) {
  const classNameAttr = node.attributes.find(
    (attr) =>
      attr.type === "JSXAttribute" &&
      attr.name &&
      attr.name.name === "className",
  );

  if (!classNameAttr) {
    return [];
  }

  const classNameValue = getClassNameValue(classNameAttr);
  return extractGlassClasses(classNameValue);
}

/** @type {import('eslint').Rule.RuleModule} */
module.exports = {
  meta: {
    type: "suggestion",
    docs: {
      description:
        "Warn when glass/blur utilities are nested beyond allowed depth",
      category: "Best Practices",
      recommended: true,
    },
    messages: {
      nestedGlass:
        "Glass/blur nesting depth exceeds {{max}} layers (found {{depth}}). Nesting glass effects causes 'muddy' visuals and GPU performance issues. Consider flattening the component hierarchy or removing intermediate glass layers.",
    },
    schema: [
      {
        type: "object",
        properties: {
          maxDepth: {
            type: "integer",
            minimum: 1,
            default: MAX_NESTING_DEPTH,
          },
        },
        additionalProperties: false,
      },
    ],
  },
  create(context) {
    const options = context.options[0] || {};
    const maxDepth = options.maxDepth || MAX_NESTING_DEPTH;

    const ancestorGlassStack = [];

    return {
      JSXOpeningElement(node) {
        const glassClasses = getGlassClassesFromElement(node);

        if (glassClasses.length > 0) {
          const currentDepth = ancestorGlassStack.length + 1;

          if (currentDepth > maxDepth) {
            context.report({
              node,
              messageId: "nestedGlass",
              data: {
                max: maxDepth,
                depth: currentDepth,
              },
            });
          }

          ancestorGlassStack.push({
            node,
            classes: glassClasses,
          });
        }
      },

      "JSXOpeningElement:exit"(node) {
        const stackTop = ancestorGlassStack[ancestorGlassStack.length - 1];
        if (stackTop && stackTop.node === node) {
          ancestorGlassStack.pop();
        }
      },
    };
  },
};
