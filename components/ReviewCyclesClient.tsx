"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  carryForwardUnresolvedItems,
  createApplicantResponse,
  createResponseResolutionRecord,
  createResubmittalPackage,
  createReviewCycle,
  getApplicantResponses,
  getCadFiles,
  getCadParseRuns,
  getCarryForwards,
  getResolutionSummary,
  getResubmittalPackage,
  getResubmittalPackages,
  getResponseResolutionRecords,
  getReviewCycleDashboard,
  getReviewCycles,
  getRevisionChanges,
  linkCadFileToResubmittal,
  prepareNextCycle,
  runRevisionComparison,
  suggestResponseMappings,
  updateResponseResolutionStatus,
  updateResubmittalPackageStatus,
  type ApplicantResponse,
  type ApplicantResponseMapping,
  type CadFileUpload,
  type CadParseRun,
  type IssueCarryForward,
  type NextCyclePreparation,
  type ResponseResolutionRecord,
  type ResubmittalPackage,
  type RevisionChangeRecord,
  type RevisionComparisonRun,
  type ReviewCycle,
  type ReviewCycleDashboard as ReviewCycleDashboardData,
} from "@/lib/api";
import MultiRoundReviewBoundaryNotice from "@/components/MultiRoundReviewBoundaryNotice";
import ReviewCycleDashboard from "@/components/ReviewCycleDashboard";
import ReviewCycleTimeline from "@/components/ReviewCycleTimeline";
import ReviewCycleSummaryCard from "@/components/ReviewCycleSummaryCard";
import ResubmittalIntakeForm from "@/components/ResubmittalIntakeForm";
import ResubmittalPackagePanel from "@/components/ResubmittalPackagePanel";
import ApplicantResponsePanel from "@/components/ApplicantResponsePanel";
import ApplicantResponseMappingPanel from "@/components/ApplicantResponseMappingPanel";
import RevisionComparisonPanel from "@/components/RevisionComparisonPanel";
import IssueCarryForwardPanel from "@/components/IssueCarryForwardPanel";
import ResponseResolutionPanel from "@/components/ResponseResolutionPanel";
import NextCyclePreparationPanel from "@/components/NextCyclePreparationPanel";

// Orchestrates the Phase 13 multi-round review cycle experience for Brookside
// Meadows. All data is backend-canonical; the browser does not simulate review
// cycle data.
export default function ReviewCyclesClient() {
  const [loaded, setLoaded] = useState(false);
  const [cycles, setCycles] = useState<ReviewCycle[]>([]);
  const [activeCycleId, setActiveCycleId] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<ReviewCycleDashboardData | null>(
    null,
  );
  const [resubmittals, setResubmittals] = useState<ResubmittalPackage[]>([]);
  const [selectedResubmittalId, setSelectedResubmittalId] = useState<
    string | null
  >(null);
  const [responses, setResponses] = useState<ApplicantResponse[]>([]);
  const [mappings, setMappings] = useState<ApplicantResponseMapping[]>([]);
  const [cadFiles, setCadFiles] = useState<CadFileUpload[]>([]);
  const [parseRuns, setParseRuns] = useState<CadParseRun[]>([]);
  const [comparison, setComparison] = useState<RevisionComparisonRun | null>(
    null,
  );
  const [changes, setChanges] = useState<RevisionChangeRecord[]>([]);
  const [carryForwards, setCarryForwards] = useState<IssueCarryForward[]>([]);
  const [resolutions, setResolutions] = useState<ResponseResolutionRecord[]>([]);
  const [preparation, setPreparation] = useState<NextCyclePreparation | null>(
    null,
  );
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [carryMessage, setCarryMessage] = useState<string | null>(null);

  const activeCycle = useMemo(
    () => cycles.find((c) => c.reviewCycleId === activeCycleId) ?? null,
    [cycles, activeCycleId],
  );

  const refreshCycleData = useCallback(async (cycleId: string | null) => {
    const [resubs, resps, resols, cfs] = await Promise.all([
      getResubmittalPackages(),
      getApplicantResponses(),
      getResponseResolutionRecords(),
      getCarryForwards(),
    ]);
    setResubmittals(resubs);
    setResponses(
      cycleId ? resps.filter((r) => r.reviewCycleId === cycleId) : resps,
    );
    setResolutions(
      cycleId ? resols.filter((r) => r.reviewCycleId === cycleId) : resols,
    );
    setCarryForwards(
      cycleId ? cfs.filter((c) => c.reviewCycleId === cycleId) : cfs,
    );
    setDashboard(await getReviewCycleDashboard());
  }, []);

  useEffect(() => {
    (async () => {
      const [cyc, files, runs] = await Promise.all([
        getReviewCycles(),
        getCadFiles(),
        getCadParseRuns(),
      ]);
      setCycles(cyc);
      setCadFiles(files);
      setParseRuns(runs);
      const active =
        cyc.find((c) => c.status === "active")?.reviewCycleId ??
        (cyc.length > 0 ? cyc[cyc.length - 1].reviewCycleId : null);
      setActiveCycleId(active);
      await refreshCycleData(active);
      setLoaded(true);
    })();
  }, [refreshCycleData]);

  const handleCreateCycle = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    const result = await createReviewCycle();
    if (result.ok && result.data) {
      const cyc = await getReviewCycles();
      setCycles(cyc);
      setActiveCycleId(result.data.reviewCycleId);
      await refreshCycleData(result.data.reviewCycleId);
      setMessage(`Created review round ${result.data.cycleNumber}.`);
    } else {
      setMessage(result.error ?? "Could not create the review cycle.");
    }
    setBusy(false);
  }, [refreshCycleData]);

  const handleSelectCycle = useCallback(
    async (cycleId: string) => {
      setActiveCycleId(cycleId);
      setComparison(null);
      setChanges([]);
      setMappings([]);
      setPreparation(null);
      await refreshCycleData(cycleId);
    },
    [refreshCycleData],
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
    [activeCycleId, refreshCycleData],
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
    [activeCycleId, refreshCycleData],
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
    [],
  );

  const handleSelectResubmittal = useCallback(async (id: string) => {
    setSelectedResubmittalId(id);
    const detail = await getResubmittalPackage(id);
    if (detail) {
      setResubmittals((prev) =>
        prev.map((p) => (p.resubmittalPackageId === id ? detail : p)),
      );
    }
  }, []);

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
    [activeCycleId, refreshCycleData, selectedResubmittalId],
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
  }, [activeCycleId, refreshCycleData]);

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
        setChanges(await getRevisionChanges(result.data.comparisonRunId));
        await refreshCycleData(activeCycleId);
      } else {
        setMessage(result.error ?? "Could not run the comparison.");
      }
      setBusy(false);
    },
    [activeCycleId, refreshCycleData, selectedResubmittalId],
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
  }, [activeCycleId, refreshCycleData]);

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
    [activeCycleId, refreshCycleData],
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
    [activeCycleId, refreshCycleData],
  );

  const handlePrepareNextCycle = useCallback(async () => {
    if (!activeCycleId) return;
    setBusy(true);
    const result = await prepareNextCycle(activeCycleId);
    if (result.ok && result.data) {
      setPreparation(result.data);
      const cyc = await getReviewCycles();
      setCycles(cyc);
    } else {
      setMessage(result.error ?? "Could not prepare the next cycle.");
    }
    setBusy(false);
  }, [activeCycleId]);

  const responsesById = useMemo(() => {
    const map: Record<string, ApplicantResponse> = {};
    for (const response of responses) map[response.applicantResponseId] = response;
    return map;
  }, [responses]);

  if (!loaded) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Loading review cycles...
      </div>
    );
  }

  if (cycles.length === 0) {
    return (
      <div className="space-y-6">
        <MultiRoundReviewBoundaryNotice />
        <div className="surface-card p-6">
          <p className="text-sm text-slate-600">
            No review cycle exists yet. Create the first review round for
            Brookside Meadows to begin tracking resubmittals and revisions.
          </p>
          <button
            type="button"
            onClick={handleCreateCycle}
            disabled={busy}
            className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
          >
            {busy ? "Working..." : "Create initial review cycle"}
          </button>
          {message ? (
            <p className="mt-3 text-sm text-slate-600">{message}</p>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <MultiRoundReviewBoundaryNotice />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-slate-500">
          Multi-round review-support tracking. All statuses are review-support
          statuses, not final engineering decisions.
        </p>
        <button
          type="button"
          onClick={handleCreateCycle}
          disabled={busy}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-60"
        >
          {busy ? "Working..." : "Start new review round"}
        </button>
      </div>

      {message ? (
        <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          {message}
        </p>
      ) : null}

      <ReviewCycleDashboard dashboard={dashboard} />

      <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
        <div className="space-y-6">
          <ReviewCycleTimeline
            cycles={cycles}
            activeCycleId={activeCycleId}
            onSelect={handleSelectCycle}
          />
          <ReviewCycleSummaryCard cycle={activeCycle} />
        </div>

        <div className="space-y-6">
          <ResubmittalIntakeForm
            disabled={!activeCycleId}
            onCreate={handleCreateResubmittal}
          />
          <ResubmittalPackagePanel
            packages={resubmittals.filter(
              (p) => p.reviewCycleId === activeCycleId,
            )}
            cadFiles={cadFiles}
            selectedId={selectedResubmittalId}
            onSelect={handleSelectResubmittal}
            onStatusChange={handleResubmittalStatus}
            onLinkCadFile={handleLinkCadFile}
          />
          <ApplicantResponsePanel
            responses={responses}
            canAdd={Boolean(selectedResubmittalId)}
            onAdd={handleAddResponse}
          />
          <ApplicantResponseMappingPanel
            mappings={mappings}
            responsesById={responsesById}
            onSuggest={handleSuggestMappings}
            busy={busy}
          />
        </div>
      </div>

      <RevisionComparisonPanel
        parseRuns={parseRuns}
        run={comparison}
        changes={changes}
        busy={busy}
        onRun={handleRunComparison}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <ResponseResolutionPanel
          records={resolutions}
          busy={busy}
          onCreate={handleCreateResolution}
          onUpdateStatus={handleUpdateResolution}
        />
        <IssueCarryForwardPanel
          carryForwards={carryForwards}
          busy={busy}
          onCarryForward={handleCarryForward}
          message={carryMessage}
        />
      </div>

      <NextCyclePreparationPanel
        preparation={preparation}
        busy={busy}
        onPrepare={handlePrepareNextCycle}
      />
    </div>
  );
}
