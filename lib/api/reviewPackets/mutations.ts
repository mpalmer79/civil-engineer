import { PROJECT_ID, apiMutate } from "../client";
import {
  mapPacketAction,
  mapPacketItem,
  mapReviewPacketDetail,
  type ApiPacketAction,
  type ApiPacketItem,
  type ApiReviewPacket,
} from "./mappers";
import type {
  ReviewPacketActionInput,
  ReviewPacketDetail,
  ReviewPacketMutationResult,
} from "./types";

// Mutating calls return a clear backend-required result. Packet data is not
// simulated in the browser, so an unreachable backend surfaces as
// backendReachable: false with a reviewer-facing message.

export async function generateReviewPacket(
  projectId: string = PROJECT_ID,
): Promise<{
  ok: boolean;
  backendReachable: boolean;
  packet?: ReviewPacketDetail;
  error?: string;
}> {
  const result = await apiMutate<ReviewPacketDetail>(
    "POST",
    `/api/v1/projects/${projectId}/review-packets/generate`,
    {
      map: (raw) => mapReviewPacketDetail(raw as unknown as ApiReviewPacket),
      parseErrorDetail: false,
      unavailableMessage:
        "The backend is not reachable. Start the API to generate a review packet. Packet data is not simulated in the browser.",
    },
  );
  return {
    ok: result.ok,
    backendReachable: result.backendReachable,
    packet: result.data,
    error: result.error,
  };
}

export async function createReviewPacketReviewerAction(
  packetId: string,
  itemId: string,
  input: ReviewPacketActionInput,
): Promise<ReviewPacketMutationResult> {
  const result = await apiMutate<{
    action: ApiPacketAction;
    item: ApiPacketItem;
  }>(
    "POST",
    `/api/v1/review-packets/${packetId}/items/${itemId}/review-actions`,
    {
      body: {
        action_type: input.actionType,
        reviewer_note: input.reviewerNote,
        reviewer_name: input.reviewerName,
      },
      unavailableMessage:
        "The backend is not reachable. Start the API to record a reviewer action. Packet actions are not simulated in the browser.",
    },
  );
  if (!result.ok || !result.data) {
    return {
      ok: result.ok,
      status: result.status,
      backendReachable: result.backendReachable,
      error: result.error,
    };
  }
  return {
    ok: true,
    status: result.status,
    backendReachable: true,
    action: mapPacketAction(result.data.action),
    item: mapPacketItem(result.data.item),
  };
}

export async function updateReviewPacketItemStatus(
  packetId: string,
  itemId: string,
  newStatus: string,
  reviewerNote?: string,
  reviewerName?: string,
): Promise<ReviewPacketMutationResult> {
  const result = await apiMutate<ApiPacketItem>(
    "PATCH",
    `/api/v1/review-packets/${packetId}/items/${itemId}/status`,
    {
      body: {
        new_status: newStatus,
        reviewer_note: reviewerNote,
        reviewer_name: reviewerName,
      },
      unavailableMessage:
        "The backend is not reachable. Start the API to update a packet item status.",
    },
  );
  if (!result.ok || !result.data) {
    return {
      ok: result.ok,
      status: result.status,
      backendReachable: result.backendReachable,
      error: result.error,
    };
  }
  return {
    ok: true,
    status: result.status,
    backendReachable: true,
    item: mapPacketItem(result.data),
  };
}
