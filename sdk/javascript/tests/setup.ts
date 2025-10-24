/**
 * Jest setup file for LipService SDK tests
 */

// Mock console methods to avoid noise in tests
const originalConsole = { ...console };

beforeEach(() => {
  // Suppress console output during tests
  console.log = jest.fn();
  console.warn = jest.fn();
  console.error = jest.fn();
  console.info = jest.fn();
  console.debug = jest.fn();
});

afterEach(() => {
  // Restore original console methods
  Object.assign(console, originalConsole);
});

// Global test timeout
jest.setTimeout(10000);
