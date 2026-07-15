"use client";

import ApplicantResponseMappingPanel from "@/components/ApplicantResponseMappingPanel";
import ApplicantResponsePanel from "@/components/ApplicantResponsePanel";
import IssueCarryForwardPanel from "@/components/IssueCarryForwardPanel";
import MultiRoundReviewBoundaryNotice from "@/components/MultiRoundReviewBoundaryNotice";
import NextCyclePreparationPanel from "@/components/NextCyclePreparationPanel";
import RequestFailureCard from "@/components/RequestFailureCard";
import ResponseResolutionPanel from "@/components/ResponseResolutionPanel";
import ResubmittalIntakeForm from "@/components/ResubmittalIntakeForm";
import ResubmittalPackagePanel from "@/components/ResubmittalPackagePanel";
import ReviewCycleDashboard from "@/components/ReviewCycleDashboard";
import ReviewCycleSummaryCard from "@/components/ReviewCycleSummaryCard";
import ReviewCycleTimeline from "@/components/ReviewCycleTimeline";
import RevisionComparisonPanel from "@/components/RevisionComparisonPanel";
import { useReviewCycleActions } from "@/components/review-cycles/useReviewCycleActions";
import { useReviewCyclesData } from "@/components/review-cycles/useReviewCyclesData";

// Orchestrates the Phase 13 multi-round review cycle experience for Brookside
// Meadows. All data is backend-canonical; the browser does not simulate review
// cycle data.
export default function ReviewCyclesClient() {
  const data = useReviewCyclesData();
  const {
    loaded,
    cycles,
    activeCycleId,
    dashboard,
    resubmittals,
    selectedResubmittalId,
    responses,
    mappings,
    cadFiles,
    parseRuns,
    comparison,
    changes,
    carryForwards,
    resolutions,
    preparation,
    busy,
    failure,
    message,
    carryMessage,
    activeCycle,
    responsesById,
  } = data;
  const {
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
  } = useReviewCycleActions(data);

  if (!loaded) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Loading review cycles...
      </div>
    );
  }

  if (cycles.length === 0 && failure) {
    return (
      <div className="space-y-6">
        <MultiRoundReviewBoundaryNotice />
        <RequestFailureCard failure={failure} />
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
