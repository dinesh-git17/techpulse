/**
 * @fileoverview TechPulse ESLint Plugin
 *
 * Custom ESLint rules for enforcing TechPulse design system constraints.
 */

const noNestedGlass = require("./no-nested-glass.js");

/** @type {import('eslint').ESLint.Plugin} */
module.exports = {
  meta: {
    name: "eslint-plugin-techpulse",
    version: "1.0.0",
  },
  rules: {
    "no-nested-glass": noNestedGlass,
  },
};
