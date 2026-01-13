/**
 * MSW server configuration for Node.js test environment.
 *
 * @module test/mocks/server
 */

import { setupServer } from "msw/node";

import { handlers } from "./handlers";

/**
 * MSW server instance for API mocking in tests.
 *
 * Started in test/setup.ts before all tests.
 */
export const server = setupServer(...handlers);
