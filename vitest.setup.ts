// Registers the jest-dom matchers (toBeInTheDocument and friends) with Vitest
// and augments the expect types so the matchers type-check.
import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Explicit test isolation. Vitest runs without injected globals, so React
// Testing Library's automatic cleanup never registers itself. Without this
// hook, rendered trees and browser storage leak between tests and results
// depend on execution order.
afterEach(() => {
  cleanup();
  window.localStorage.clear();
  window.sessionStorage.clear();
});
