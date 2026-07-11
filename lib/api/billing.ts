// Production Phase 4B/4C billing and usage client.
//
// Billing is deferred: the UI shows an honest inactive state until Stripe is
// configured. Nothing here implies an active paid subscription, and no secret or
// Stripe key is ever read on the client. A plan or subscription status is an
// account-posture label, not a review outcome.

import {
  API_BASE_URL,
  apiGetMapped,
  authHeaders,
  type ApiResult,
} from "./client";

export type Plan = {
  planCode: string;
  name: string;
  description: string;
  priceDisplay: string;
  sortOrder: number;
  limits: Record<string, number | null>;
};

export type BillingStatus = {
  enabled: boolean;
  mode: string;
  message: string;
};

export type Subscription = {
  subscriptionId: string;
  organizationId: string;
  planCode: string;
  planName: string;
  status: string;
  currentPeriodEnd: string | null;
  limits: Record<string, number | null>;
};

export type OrganizationBilling = {
  subscription: Subscription;
  billing: BillingStatus;
  plans: Plan[];
  checkoutAvailable: boolean;
};

export type UsageLimit = {
  key: string;
  category: string;
  used: number;
  limit: number | null;
  status: string;
  enforced: boolean;
};

export type UsageSummary = {
  organizationId: string;
  planCode: string;
  planName: string;
  subscriptionStatus: string;
  enforcement: string;
  limits: UsageLimit[];
  totals: Record<string, number>;
};

export type CheckoutResult = {
  available: boolean;
  detail: string;
  checkoutUrl: string | null;
};

function mapPlan(raw: Record<string, unknown>): Plan {
  return {
    planCode: raw.plan_code as string,
    name: raw.name as string,
    description: raw.description as string,
    priceDisplay: raw.price_display as string,
    sortOrder: (raw.sort_order as number) ?? 0,
    limits: (raw.limits as Record<string, number | null>) ?? {},
  };
}

function mapStatus(raw: Record<string, unknown>): BillingStatus {
  return {
    enabled: (raw.enabled as boolean) ?? false,
    mode: (raw.mode as string) ?? "inactive",
    message: (raw.message as string) ?? "",
  };
}

function mapSubscription(raw: Record<string, unknown>): Subscription {
  return {
    subscriptionId: raw.subscription_id as string,
    organizationId: raw.organization_id as string,
    planCode: raw.plan_code as string,
    planName: raw.plan_name as string,
    status: raw.status as string,
    currentPeriodEnd: (raw.current_period_end as string) ?? null,
    limits: (raw.limits as Record<string, number | null>) ?? {},
  };
}

function mapUsageLimit(raw: Record<string, unknown>): UsageLimit {
  return {
    key: raw.key as string,
    category: raw.category as string,
    used: (raw.used as number) ?? 0,
    limit: (raw.limit as number) ?? null,
    status: raw.status as string,
    enforced: (raw.enforced as boolean) ?? false,
  };
}

export async function listPlans(): Promise<ApiResult<Plan[]>> {
  return apiGetMapped<Record<string, unknown>[], Plan[]>(
    "/api/v1/billing/plans",
    (data) => data.map(mapPlan),
  );
}

export async function getBillingStatus(): Promise<ApiResult<BillingStatus>> {
  return apiGetMapped<Record<string, unknown>, BillingStatus>(
    "/api/v1/billing/status",
    mapStatus,
  );
}

export async function getOrganizationBilling(
  organizationId: string,
): Promise<ApiResult<OrganizationBilling>> {
  return apiGetMapped<Record<string, unknown>, OrganizationBilling>(
    `/api/v1/organizations/${organizationId}/billing`,
    (data) => ({
      subscription: mapSubscription(
        data.subscription as Record<string, unknown>,
      ),
      billing: mapStatus(data.billing as Record<string, unknown>),
      plans: (data.plans as Record<string, unknown>[]).map(mapPlan),
      checkoutAvailable: (data.checkout_available as boolean) ?? false,
    }),
  );
}

export async function getOrganizationUsage(
  organizationId: string,
): Promise<ApiResult<UsageSummary>> {
  return apiGetMapped<Record<string, unknown>, UsageSummary>(
    `/api/v1/organizations/${organizationId}/usage`,
    (data) => ({
      organizationId: data.organization_id as string,
      planCode: data.plan_code as string,
      planName: data.plan_name as string,
      subscriptionStatus: data.subscription_status as string,
      enforcement: data.enforcement as string,
      limits: (data.limits as Record<string, unknown>[]).map(mapUsageLimit),
      totals: (data.totals as Record<string, number>) ?? {},
    }),
  );
}

export async function startCheckout(
  organizationId: string,
): Promise<CheckoutResult | null> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/organizations/${organizationId}/billing/checkout`,
      {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        cache: "no-store",
      },
    );
    if (!res.ok) return null;
    const raw = (await res.json()) as Record<string, unknown>;
    return {
      available: (raw.available as boolean) ?? false,
      detail: raw.detail as string,
      checkoutUrl: (raw.checkout_url as string) ?? null,
    };
  } catch {
    return null;
  }
}
