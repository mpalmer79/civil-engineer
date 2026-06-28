import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const root = process.cwd();

function readDoc(relativePath: string): string {
  return readFileSync(join(root, relativePath), "utf8");
}

// Production Phase 4B/4C docs must exist and state the honest posture: Stripe is
// deferred and billing is inactive, email is a no-op, and usage limits are
// advisory. These assertions keep the docs from drifting into claiming an active
// paid product.

describe("Phase 4B/4C documentation", () => {
  it("the auth lifecycle and billing docs exist", () => {
    expect(existsSync(join(root, "docs/AUTH_LIFECYCLE.md"))).toBe(true);
    expect(existsSync(join(root, "docs/BILLING_AND_USAGE.md"))).toBe(true);
  });

  it("the billing doc states Stripe is deferred and billing inactive", () => {
    const doc = readDoc("docs/BILLING_AND_USAGE.md").toLowerCase();
    expect(doc).toContain("stripe status: deferred");
    expect(doc).toContain("no payment is");
    expect(doc).toContain("advisory");
  });

  it("the auth lifecycle doc states email is not sent and tokens are hashed", () => {
    const doc = readDoc("docs/AUTH_LIFECYCLE.md").toLowerCase();
    expect(doc).toContain("no real email is sent");
    expect(doc).toContain("hash");
    expect(doc).toContain("use-once");
  });

  it("neither doc claims an active paid subscription", () => {
    const billing = readDoc("docs/BILLING_AND_USAGE.md").toLowerCase();
    expect(billing).not.toContain("subscription is active");
    expect(billing).not.toContain("billing is active.");
  });

  it("release readiness reflects the account and billing foundation", () => {
    const doc = readDoc("docs/RELEASE_READINESS.md").toLowerCase();
    expect(doc).toContain("team invitation");
    expect(doc).toContain("billing");
  });
});
