"use client";

import { useCallback } from "react";

import type { ReviewCyclesData } from "@/components/review-cycles/useReviewCyclesData";
import {
  carryForwardUnresolvedItems,
  createApplicantResponse,
  createResponseResolutionRecord,
  createResubmittalPackage,
  createReviewCycle,
  getResubmittalPackage,
  getReviewCycles,
  getRevisionChanges,
  linkCadFileToResubmittal,
  prepareNextCycle,
  runRevisionComparison,
  suggestResponseMappings,
  updateResponseResolutionStatus,
  updateResubmittalPackageStatus,
} from "@/lib/api";

// Reviewer-facing actions for the multi-round review cycle experience. Each
// action calls the backend and refreshes backend-canonical state.
export function useReviewCycleActions(data: ReviewCyclesData) {
  const {
    activeCycleId,
    selectedResubmittalId,
    refreshCycleData,
    setActiveCycleId,
    setBusy,
    setCarryMessage,
    setChanges,
    setComparison,
    setCycles,
    setFailure,
    setMappings,
    setMessage,
    setPreparation,
    setResubmittals,
    setSelectedResubmittalId,
  } = data;

  const handleCreateCycle = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    const result = await createReviewCycle();
    if (result.ok && result.data) {
      const cycResult = await getReviewCycles();
      setCycles(cycResult.ok ? cycResult.data : []);
      setActiveCycleId(result.data.reviewCycleId);
      await refreshCycleData(result.data.reviewCycleId);
      setMessage(`Created review round ${result.data.cycleNumber}.`);
    } else {
      setMessage(result.error ?? "Could not create the review cycle.");
    }
    setBusy(false);
  }, [refreshCycleData, setActiveCycleId, setBusy, setCycles, setMessage]);

  const handleSelectCycle = useCallback(
    async (cycleId: string) => {
      setActiveCycleId(cycleId);
      setComparison(null);
      setChanges([]);
      setMappings([]);
      setPreparation(null);
      await refreshCycleData(cycleId);
    },
    [
      refreshCycleData,
      setActiveCycleId,
      setChanges,
      setComparison,
      setMappings,
      setPreparation,
    ],
  );

  const handleCreateResubmittal = useCallback(
    async (packageName: string, submittedBy: string) => {
      if (!activeCycleId) return;
      const result = await createResubmittalPackage(
        activeCycleId,
        packageName,
        submittedBy,
      );
      if (result.ok && result.data) {
        setSelectedResubmittalId(result.data.resubmittalPackageId);
        await refreshCycleData(activeCycleId);
      } else {
        setMessage(result.error ?? "Could not create the resubmittal.");
      }
    },
    [activeCycleId, refreshCycleData, setMessage, setSelectedResubmittalId],
  );

  const handleResubmittalStatus = useCallback(
    async (resubmittalPackageId: string, status: string) => {
      const result = await updateResubmittalPackageStatus(
        resubmittalPackageId,
        status,
      );
      if (!result.ok) {
        setMessage(result.error ?? "Could not update status.");
      }
      await refreshCycleData(activeCycleId);
    },
    [activeCycleId, refreshCycleData, setMessage],
  );

  const handleLinkCadFile = useCallback(
    async (resubmittalPackageId: string, cadFileId: string) => {
      const result = await linkCadFileToResubmittal(
        resubmittalPackageId,
        cadFileId,
      );
      if (result.ok && result.data) {
        setResubmittals((prev) =>
          prev.map((p) =>
            p.resubmittalPackageId === resubmittalPackageId ? result.data! : p,
          ),
        );
      } else {
        setMessage(result.error ?? "Could not link the CAD file.");
      }
    },
    [setMessage, setResubmittals],
  );

  const handleSelectResubmittal = useCallback(
    async (id: string) => {
      setSelectedResubmittalId(id);
      const detailResult = await getResubmittalPackage(id);
      if (detailResult.ok) {
        const detail = detailResult.data;
        setResubmittals((prev) =>
          prev.map((p) => (p.resubmittalPackageId === id ? detail : p)),
        );
      } else {
        setFailure(detailResult);
      }
    },
    [setFailure, setResubmittals, setSelectedResubmittalId],
  );

  const handleAddResponse = useCallback(
    async (text: string, topic: string) => {
      if (!selectedResubmittalId) {
        setMessage("Select a resubmittal package first.");
        return;
      }
      const result = await createApplicantResponse(
        selectedResubmittalId,
        text,
        topic,
      );
      if (result.ok) {
        await refreshCycleData(activeCycleId);
      } else {
        setMessage(result.error ?? "Could not add the response.");
      }
    },
    [activeCycleId, refreshCycleData, selectedResubmittalId, setMessage],
  );

  const handleSuggestMappings = useCallback(async () => {
    if (!activeCycleId) return;
    setBusy(true);
    const result = await suggestResponseMappings(activeCycleId);
    if (result.ok && result.data) {
      setMappings((prev) => [...prev, ...result.data!]);
      await refreshCycleData(activeCycleId);
    } else {
      setMessage(result.error ?? "Could not suggest mappings.");
    }
    setBusy(false);
  }, [activeCycleId, refreshCycleData, setBusy, setMappings, setMessage]);

  const handleRunComparison = useCallback(
    async (previousParseRunId: string, currentParseRunId: string) => {
      if (!activeCycleId) return;
      setBusy(true);
      const result = await runRevisionComparison(
        activeCycleId,
        previousParseRunId,
        currentParseRunId,
        selectedResubmittalId ?? undefined,
      );
      if (result.ok && result.data) {
        setComparison(result.data);
        const changesResult = await getRevisionChanges(result.data.comparisonRunId);
        setChanges(changesResult.ok ? changesResult.data : []);
        await refreshCycleData(activeCycleId);
      } else {
        setMessage(result.error ?? "Could not run the comparison.");
      }
      setBusy(false);
    },
    [
      activeCycleId,
      refreshCycleData,
      selectedResubmittalId,
      setBusy,
      setChanges,
      setComparison,
      setMessage,
    ],
  );

  const handleCarryForward = useCallback(async () => {
    if (!activeCycleId) return;
    setBusy(true);
    const result = await carryForwardUnresolvedItems(activeCycleId);
    if (result.ok) {
      setCarryMessage(
        `${result.createdCount ?? 0} item(s) carried forward, ${
          result.skippedCount ?? 0
        } already present.`,
      );
      await refreshCycleData(activeCycleId);
    } else {
      setCarryMessage(result.error ?? "Could not carry items forward.");
    }
    setBusy(false);
  }, [activeCycleId, refreshCycleData, setBusy, setCarryMessage]);

  const handleCreateResolution = useCallback(
    async (status: string, reviewerNote: string) => {
      if (!activeCycleId) return;
      const result = await createResponseResolutionRecord(activeCycleId, status, {
        reviewerNote: reviewerNote || undefined,
        reviewerName: "Town Engineer",
      });
      if (result.ok) {
        await refreshCycleData(activeCycleId);
      } else {
        setMessage(result.error ?? "Could not create the resolution record.");
      }
    },
    [activeCycleId, refreshCycleData, setMessage],
  );

  const handleUpdateResolution = useCallback(
    async (resolutionRecordId: string, status: string) => {
      const result = await updateResponseResolutionStatus(
        resolutionRecordId,
        status,
        "Town Engineer",
      );
      if (result.ok) {
        await refreshCycleData(activeCycleId);
      } else {
        setMessage(result.error ?? "Could not update the resolution status.");
      }
    },
    [activeCycleId, refreshCycleData, setMessage],
  );

  const handlePrepareNextCycle = useCallback(async () => {
    if (!activeCycleId) return;
    setBusy(true);
    const result = await prepareNextCycle(activeCycleId);
    if (result.ok && result.data) {
      setPreparation(result.data);
      const cycResult = await getReviewCycles();
      setCycles(cycResult.ok ? cycResult.data : []);
    } else {
      setMessage(result.error ?? "Could not prepare the next cycle.");
    }
    setBusy(false);
  }, [activeCycleId, setBusy, setCycles, setMessage, setPreparation]);

  return {
    handleCreateCycle,
    handleSelectCycle,
    handleCreateResubmittal,
    handleResubmittalStatus,
    handleLinkCadFile,
    handleSelectResubmittal,
    handleAddResponse,
    handleSuggestMappings,
    handleRunComparison,
    handleCarryForward,
    handleCreateResolution,
    handleUpdateResolution,
    handlePrepareNextCycle,
  };
}
