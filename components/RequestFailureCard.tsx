import Link from "next/link";

import type { ApiFailure } from "@/lib/api/client";

// One consistent presentation for every API failure category. Authenticated
// surfaces render this instead of empty screens or substituted demo data, so
// a 401, a 403, a missing record, a validation problem, a timeout, and a
// backend outage are visibly different states. The correlation ID gives a
// support handle without exposing anything sensitive.

const COPY: Record<
  ApiFailure["kind"],
  { title: string; detail: string }
> = {
  unauthenticated: {
    title: "Sign in required",
    detail:
      "Your session has ended or you are not signed in. Sign in to view this content.",
  },
  forbidden: {
    title: "You do not have access to this content",
    detail:
      "Your account does not have permission for this project or organization. Ask a project administrator for access if you believe this is wrong.",
  },
  not_found: {
    title: "Record not found",
    detail:
      "This record does not exist or is no longer available.",
  },
  validation: {
    title: "The request could not be processed",
    detail:
      "The backend rejected the request as invalid. Review the input and try again.",
  },
  conflict: {
    title: "This change conflicts with the current state",
    detail:
      "Another update happened first. Reload the page and try again.",
  },
  rate_limited: {
    title: "Too many requests",
    detail: "Please wait a moment before trying again.",
  },
  timeout: {
    title: "The backend did not respond in time",
    detail:
      "The request timed out. The backend may be busy; try again shortly.",
  },
  unavailable: {
    title: "The backend is not available",
    detail:
      "The review-support backend cannot be reached right now. No demo data is substituted for real records.",
  },
  server: {
    title: "Something went wrong on the backend",
    detail: "An unexpected backend error occurred. Try again shortly.",
  },
  network: {
    title: "The backend is not reachable",
    detail:
      "The review-support backend cannot be reached right now. No demo data is substituted for real records.",
  },
  invalid_response: {
    title: "The backend returned an unexpected response",
    detail:
      "The response did not match the expected format, so it was not displayed.",
  },
};

export default function RequestFailureCard({
  failure,
  signInHref = "/login",
}: {
  failure: ApiFailure;
  signInHref?: string;
}) {
  const copy = COPY[failure.kind] ?? COPY.server;
  return (
    <div
      role="status"
      data-testid="request-failure"
      data-failure-kind={failure.kind}
      className="rounded-xl border border-slate-200 bg-slate-50 p-5"
    >
      <h2 className="text-sm font-semibold text-slate-900">{copy.title}</h2>
      <p className="mt-1 text-sm text-slate-600">{copy.detail}</p>
      {failure.kind === "unauthenticated" ? (
        <Link
          href={signInHref}
          className="mt-3 inline-block rounded-lg bg-water-600 px-4 py-2 text-sm font-medium text-white hover:bg-water-700"
        >
          Sign in
        </Link>
      ) : null}
      {failure.retryable ? (
        <p className="mt-2 text-xs text-slate-500">
          This request can be retried.
        </p>
      ) : null}
      {failure.requestId ? (
        <p className="mt-2 text-xs text-slate-400">
          Support reference: {failure.requestId}
        </p>
      ) : null}
    </div>
  );
}
