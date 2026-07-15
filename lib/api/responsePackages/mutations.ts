import { PROJECT_ID, apiMutate } from "../client";
import {
  mapAction,
  mapItem,
  mapPackage,
  mapPackageDetail,
  type ApiAction,
  type ApiItem,
  type ApiPackage,
} from "./mappers";
import type {
  ResponsePackageDetail,
  ResponsePackageMutationResult,
} from "./types";

// Mutating calls return a clear backend-required result. Response package data
// is not simulated in the browser, so an unreachable backend surfaces as
// backendReachable: false with a reviewer-facing message.

export async function generateResponsePackage(): Promise<{
  ok: boolean;
  backendReachable: boolean;
  package?: ResponsePackageDetail;
  error?: string;
}> {
  const result = await apiMutate<ResponsePackageDetail>(
    "POST",
    `/api/v1/projects/${PROJECT_ID}/response-packages/generate`,
    {
      map: (raw) => mapPackageDetail(raw as unknown as ApiPackage),
      unavailableMessage:
        "The backend is not reachable. Start the API to generate a response package. Response package data is not simulated in the browser.",
    },
  );
  return {
    ok: result.ok,
    backendReachable: result.backendReachable,
    package: result.data,
    error: result.error,
  };
}

async function mutate(
  path: string,
  method: "POST" | "PATCH",
  body: Record<string, unknown>,
  unreachableMessage: string,
): Promise<{ ok: boolean; status: number; backendReachable: boolean; data?: unknown; error?: string }> {
  return apiMutate<unknown>(method, path, {
    body,
    unavailableMessage: unreachableMessage,
  });
}

export async function updateResponsePackageStatus(
  responsePackageId: string,
  newStatus: string,
  reviewerNote?: string,
  reviewerName?: string,
): Promise<ResponsePackageMutationResult> {
  const result = await mutate(
    `/api/v1/response-packages/${responsePackageId}/status`,
    "PATCH",
    { new_status: newStatus, reviewer_note: reviewerNote, reviewer_name: reviewerName },
    "The backend is not reachable. Start the API to update the package status.",
  );
  return {
    ok: result.ok,
    status: result.status,
    backendReachable: result.backendReachable,
    package: result.data ? mapPackage(result.data as ApiPackage) : undefined,
    error: result.error,
  };
}

export async function updateResponseItemStatus(
  responsePackageId: string,
  responseItemId: string,
  newStatus: string,
  reviewerNote?: string,
  reviewerName?: string,
): Promise<ResponsePackageMutationResult> {
  const result = await mutate(
    `/api/v1/response-packages/${responsePackageId}/items/${responseItemId}/status`,
    "PATCH",
    { new_status: newStatus, reviewer_note: reviewerNote, reviewer_name: reviewerName },
    "The backend is not reachable. Start the API to update the item status.",
  );
  return {
    ok: result.ok,
    status: result.status,
    backendReachable: result.backendReachable,
    item: result.data ? mapItem(result.data as ApiItem) : undefined,
    error: result.error,
  };
}

export async function updateResponseItemDraftText(
  responsePackageId: string,
  responseItemId: string,
  draftText: string,
  reviewerNote?: string,
  reviewerName?: string,
): Promise<ResponsePackageMutationResult> {
  const result = await mutate(
    `/api/v1/response-packages/${responsePackageId}/items/${responseItemId}/draft-text`,
    "PATCH",
    { draft_text: draftText, reviewer_note: reviewerNote, reviewer_name: reviewerName },
    "The backend is not reachable. Start the API to edit the draft text.",
  );
  return {
    ok: result.ok,
    status: result.status,
    backendReachable: result.backendReachable,
    item: result.data ? mapItem(result.data as ApiItem) : undefined,
    error: result.error,
  };
}

export async function addResponsePackageNote(
  responsePackageId: string,
  responseItemId: string,
  reviewerNote: string,
  reviewerName: string,
): Promise<ResponsePackageMutationResult> {
  const result = await mutate(
    `/api/v1/response-packages/${responsePackageId}/items/${responseItemId}/notes`,
    "POST",
    { reviewer_note: reviewerNote, reviewer_name: reviewerName },
    "The backend is not reachable. Start the API to add a reviewer note.",
  );
  return {
    ok: result.ok,
    status: result.status,
    backendReachable: result.backendReachable,
    action: result.data ? mapAction(result.data as ApiAction) : undefined,
    error: result.error,
  };
}
