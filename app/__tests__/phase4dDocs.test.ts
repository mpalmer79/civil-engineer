import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const root = process.cwd();

function readDoc(relativePath: string): string {
  return readFileSync(join(root, relativePath), "utf8");
}

// Production Phase 4D docs must exist and describe the honest posture: email is
// noop by default with an SMTP provider, Stripe checkout/webhooks are inactive
// until configured, webhook signatures are verified, and usage limits are
// advisory by default and enforceable for selected categories.

describe("Phase 4D documentation", () => {
  it("the email and Stripe docs exist", () => {
    expect(existsSync(join(root, "docs/EMAIL_DELIVERY.md"))).toBe(true);
    expect(existsSync(join(root, "docs/STRIPE_BILLING.md"))).toBe(true);
  });

  it("the email doc describes noop default and an smtp provider", () => {
    const doc = readDoc("docs/EMAIL_DELIVERY.md").toLowerCase();
    expect(doc).toContain("noop");
    expect(doc).toContain("smtp");
    expect(doc).toContain("never");
    expect(doc).toContain("token");
  });

  it("the Stripe doc describes signature verification and idempotency", () => {
    const doc = readDoc("docs/STRIPE_BILLING.md").toLowerCase();
    expect(doc).toContain("signature");
    expect(doc).toContain("idempot");
    expect(doc).toContain("inactive until configured");
    expect(doc).toContain("no real payment is processed");
  });

  it("the billing doc describes enforced and advisory categories", () => {
    const doc = readDoc("docs/BILLING_AND_USAGE.md").toLowerCase();
    expect(doc).toContain("enforceable for selected categories");
    expect(doc).toContain("usage_enforcement_enabled");
    expect(doc).toContain("limit_exceeded");
    // The public demo is never enforced.
    expect(doc).toContain("never enforced");
  });

  it("no doc claims an active paid subscription by default", () => {
    const stripe = readDoc("docs/STRIPE_BILLING.md").toLowerCase();
    expect(stripe).not.toContain("billing is active by default");
    expect(stripe).not.toContain("payment is processed by default");
  });
});
