import { afterEach, describe, expect, it } from "vitest";

import {
  MUTATING_METHODS,
  correlationId,
  csrfViolation,
  sessionMaxAgeSeconds,
} from "@/lib/server/session";

function makeRequest(headers: Record<string, string>): Request {
  return new Request("https://app.example.com/api/session/login", {
    method: "POST",
    headers,
  });
}

afterEach(() => {
  delete process.env.TRUSTED_APP_ORIGIN;
});

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

  it("validates against the configured trusted origin exactly, ignoring Host", () => {
    // Behind a reverse proxy the Host header is proxy-controlled, so the
    // deployment configures the exact public origin instead.
    process.env.TRUSTED_APP_ORIGIN = "https://civil-engineer.up.railway.app";
    const good = makeRequest({
      origin: "https://civil-engineer.up.railway.app",
      host: "internal-proxy:8080",
      "x-csrf-protection": "1",
    });
    expect(csrfViolation(good)).toBeNull();

    const badPort = makeRequest({
      origin: "https://civil-engineer.up.railway.app:8443",
      host: "internal-proxy:8080",
      "x-csrf-protection": "1",
    });
    expect(csrfViolation(badPort)).toBe("Cross-origin request rejected.");

    const badScheme = makeRequest({
      origin: "http://civil-engineer.up.railway.app",
      host: "internal-proxy:8080",
      "x-csrf-protection": "1",
    });
    expect(csrfViolation(badScheme)).toBe("Cross-origin request rejected.");
  });

  it("fails closed when the trusted origin configuration is malformed", () => {
    process.env.TRUSTED_APP_ORIGIN = "not a url";
    const req = makeRequest({
      origin: "https://app.example.com",
      host: "app.example.com",
      "x-csrf-protection": "1",
    });
    expect(csrfViolation(req)).toBe("Cross-origin request rejected.");
  });
});

describe("sessionMaxAgeSeconds", () => {
  it("converts backend minutes to seconds", () => {
    expect(sessionMaxAgeSeconds(120)).toBe(7200);
    expect(sessionMaxAgeSeconds(1)).toBe(60);
    expect(sessionMaxAgeSeconds(15.5)).toBe(930);
  });

  it("rejects missing, nonnumeric, zero, negative, and unreasonable values", () => {
    expect(sessionMaxAgeSeconds(undefined)).toBeNull();
    expect(sessionMaxAgeSeconds(null)).toBeNull();
    expect(sessionMaxAgeSeconds("120")).toBeNull();
    expect(sessionMaxAgeSeconds(0)).toBeNull();
    expect(sessionMaxAgeSeconds(-5)).toBeNull();
    expect(sessionMaxAgeSeconds(Number.NaN)).toBeNull();
    expect(sessionMaxAgeSeconds(Number.POSITIVE_INFINITY)).toBeNull();
    expect(sessionMaxAgeSeconds(60 * 24 * 31)).toBeNull();
  });
});

describe("correlationId", () => {
  it("accepts a short alphabet-safe client identifier", () => {
    const req = makeRequest({ "x-request-id": "req_1.two-THREE" });
    expect(correlationId(req)).toBe("req_1.two-THREE");
  });

  it("replaces unsafe or oversized identifiers with a UUID", () => {
    const long = makeRequest({ "x-request-id": "a".repeat(65) });
    expect(correlationId(long)).toMatch(/^[0-9a-f-]{36}$/);
    const unsafe = makeRequest({ "x-request-id": "<script>" });
    expect(correlationId(unsafe)).toMatch(/^[0-9a-f-]{36}$/);
    const missing = makeRequest({});
    expect(correlationId(missing)).toMatch(/^[0-9a-f-]{36}$/);
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
