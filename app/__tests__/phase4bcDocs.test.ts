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
    expect(existsSync(join(root, "docs/SECURITY.md"))).toBe(true);
    expect(existsSync(join(root, "docs/OPERATIONS.md"))).toBe(true);
  });

  it("the billing doc states billing is inactive until configured", () => {
    const doc = readDoc("docs/OPERATIONS.md").toLowerCase();
    expect(doc).toContain("configured by environment");
    expect(doc).toContain("no payment is");
    expect(doc).toContain("advisory");
  });

  it("the auth lifecycle doc states tokens are hashed and use-once", () => {
    const doc = readDoc("docs/SECURITY.md").toLowerCase();
    expect(doc).toContain("hash");
    expect(doc).toContain("use-once");
    // Real email is available via smtp; noop is the default.
    expect(doc).toContain("smtp");
    expect(doc).toContain("noop");
  });

  it("neither doc claims an active paid subscription", () => {
    const billing = readDoc("docs/OPERATIONS.md").toLowerCase();
    expect(billing).not.toContain("subscription is active");
    expect(billing).not.toContain("billing is active.");
  });

  it("release readiness reflects the account and billing foundation", () => {
    const doc = readDoc("docs/OPERATIONS.md").toLowerCase();
    expect(doc).toContain("team invitation");
    expect(doc).toContain("billing");
  });
});
