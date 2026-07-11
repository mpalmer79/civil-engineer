"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import SectionCard from "@/components/SectionCard";
import StatusChip from "@/components/StatusChip";
import {
  getOrganizationBilling,
  isSignedIn,
  listMyOrganizations,
  startCheckout,
  type OrganizationBilling,
  type Organization,
} from "@/lib/api";

// Workspace billing. Shows the organization's current plan, an honest billing
// status, and the plan catalog. Billing is deferred in this phase, so the
// checkout action reports an inactive state rather than starting a charge. No
// active paid subscription is ever claimed unless the backend reports it.
export default function WorkspaceBillingClient() {
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  const [orgs, setOrgs] = useState<Organization[] | null>(null);
  const [billing, setBilling] = useState<OrganizationBilling | null>(null);
  const [checkoutMessage, setCheckoutMessage] = useState<string | null>(null);

  const primaryOrg = (orgs ?? []).find((o) => o.role === "org_admin") ?? (orgs ?? [])[0];
  const orgId = primaryOrg?.organizationId ?? null;

  useEffect(() => {
    const authed = isSignedIn();
    setSignedIn(authed);
    if (!authed) return;
    listMyOrganizations().then((o) => setOrgs(o.ok ? o.data : null));
  }, []);

  useEffect(() => {
    if (orgId) getOrganizationBilling(orgId).then((b) => setBilling(b.ok ? b.data : null));
  }, [orgId]);

  const handleCheckout = async () => {
    if (!orgId) return;
    const result = await startCheckout(orgId);
    if (result?.available && result.checkoutUrl) {
      // Redirect to the Stripe-hosted checkout page.
      window.location.href = result.checkoutUrl;
      return;
    }
    setCheckoutMessage(result?.detail ?? "Checkout is unavailable.");
  };

  if (signedIn === false) {
    return (
      <SectionCard title="Sign in to view billing">
        <p className="text-sm text-slate-600">
          Sign in to see your plan and billing status.
        </p>
        <Link href="/login" className="btn btn-primary btn-sm mt-4">
          Sign in
        </Link>
      </SectionCard>
    );
  }

  if (orgs !== null && !primaryOrg) {
    return (
      <SectionCard title="No organization yet">
        <p className="text-sm text-slate-600">
          Billing applies to an organization. Create or join one to see plan
          options.
        </p>
      </SectionCard>
    );
  }

  return (
    <div className="space-y-6">
      <SectionCard title="Current plan">
        {billing ? (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span className="text-lg font-semibold text-slate-800">
                {billing.subscription.planName}
              </span>
              <span className="flex items-center gap-2">
                <span className="chip chip-neutral">
                  mode: {billing.billing.mode}
                </span>
                <StatusChip
                  label={billing.subscription.status}
                  prefix="billing"
                />
              </span>
            </div>
            <div
              className={
                billing.billing.enabled
                  ? "alert alert-info text-sm"
                  : "alert alert-warning text-sm"
              }
            >
              {billing.billing.message}
            </div>
            <p className="text-xs text-slate-500">
              Billing is required only for production SaaS use. The public
              Brookside Meadows demo never requires billing.
            </p>
            <div>
              {billing.checkoutAvailable ? (
                <button
                  type="button"
                  onClick={handleCheckout}
                  className="btn btn-primary btn-sm"
                >
                  Subscribe to Professional
                </button>
              ) : (
                <button
                  type="button"
                  disabled
                  className="btn btn-primary btn-sm"
                  title="Billing is not active in this environment"
                >
                  Billing is not active in this environment
                </button>
              )}
              {checkoutMessage ? (
                <p className="mt-2 text-sm text-slate-600">{checkoutMessage}</p>
              ) : null}
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-600">Loading billing status...</p>
        )}
      </SectionCard>

      <SectionCard title="Plans">
        <div className="grid gap-3 sm:grid-cols-2">
          {(billing?.plans ?? []).map((plan) => {
            const current = plan.planCode === billing?.subscription.planCode;
            return (
              <div
                key={plan.planCode}
                className={
                  current
                    ? "interactive-card border-water-300 p-4"
                    : "interactive-card p-4"
                }
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold text-slate-800">
                    {plan.name}
                  </span>
                  <span className="chip chip-neutral">{plan.priceDisplay}</span>
                </div>
                <p className="mt-1 text-xs text-slate-500">{plan.description}</p>
                {current ? (
                  <span className="mt-2 inline-block text-xs font-semibold text-water-700">
                    Current plan
                  </span>
                ) : null}
              </div>
            );
          })}
        </div>
      </SectionCard>
    </div>
  );
}
