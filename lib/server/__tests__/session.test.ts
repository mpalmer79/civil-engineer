import { describe, expect, it } from "vitest";

import { MUTATING_METHODS, csrfViolation } from "@/lib/server/session";

function makeRequest(headers: Record<string, string>): Request {
  return new Request("https://app.example.com/api/session/login", {
    method: "POST",
    headers,
  });
}

describe("csrfViolation", () => {
  it("accepts a same-origin request carrying the CSRF header", () => {
    const req = makeRequest({
      origin: "https://app.example.com",
      host: "app.example.com",
      "x-csrf-protection": "1",
    });
    expect(csrfViolation(req)).toBeNull();
  });

  it("accepts a request without an Origin header when the CSRF header is present", () => {
    // Non-browser clients and some same-origin navigations omit Origin; the
    // custom header requirement still holds.
    const req = makeRequest({ "x-csrf-protection": "1" });
    expect(csrfViolation(req)).toBeNull();
  });

  it("rejects a cross-origin request even when the CSRF header is present", () => {
    const req = makeRequest({
      origin: "https://evil.example.net",
      host: "app.example.com",
      "x-csrf-protection": "1",
    });
    expect(csrfViolation(req)).toBe("Cross-origin request rejected.");
  });

  it("rejects a request missing the CSRF header", () => {
    const req = makeRequest({
      origin: "https://app.example.com",
      host: "app.example.com",
    });
    expect(csrfViolation(req)).toBe("Missing CSRF protection header.");
  });

  it("rejects a malformed Origin header", () => {
    const req = makeRequest({
      origin: "not a url",
      host: "app.example.com",
      "x-csrf-protection": "1",
    });
    expect(csrfViolation(req)).toBe("Malformed Origin header.");
  });
});

describe("MUTATING_METHODS", () => {
  it("covers every state-changing HTTP method and no read method", () => {
    for (const method of ["POST", "PUT", "PATCH", "DELETE"]) {
      expect(MUTATING_METHODS.has(method)).toBe(true);
    }
    expect(MUTATING_METHODS.has("GET")).toBe(false);
    expect(MUTATING_METHODS.has("HEAD")).toBe(false);
  });
});
