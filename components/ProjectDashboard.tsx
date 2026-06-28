"use client";

import { useCallback, useEffect, useState } from "react";
import {
  addDashboardReviewerNote,
  generateCommandCenterSnapshot,
  getProjectCommandCenter,
  getProjectHealthSummary,
  updateAttentionItemStatus,
  type ProjectCommandCenterPayload,
  type ProjectHealthSummary,
  type ReviewerAttentionItem,
} from "@/lib/api";
import CommandCenterBoundaryNotice from "@/components/CommandCenterBoundaryNotice";
import CommandCenterSummaryCard from "@/components/CommandCenterSummaryCard";
import ProjectHealthMetricGrid from "@/components/ProjectHealthMetricGrid";
import ReviewerAttentionQueue from "@/components/ReviewerAttentionQueue";
import AttentionItemDetailPanel from "@/components/AttentionItemDetailPanel";
import ProjectTimeline from "@/components/ProjectTimeline";
import ReviewReadinessChecklist from "@/components/ReviewReadinessChecklist";
import ReviewerNextStepsPanel from "@/components/ReviewerNextStepsPanel";
import ProjectModuleLinksPanel from "@/components/ProjectModuleLinksPanel";
import DashboardReviewerNotesPanel from "@/components/DashboardReviewerNotesPanel";
import ProjectHealthSummaryPanel from "@/components/ProjectHealthSummaryPanel";

// Orchestrates the Phase 14 reviewer command center. All data is
// backend-canonical; the browser does not simulate command center data. The
// projectId prop scopes the command center to a project; it defaults to the
// seeded demo project so the existing demo dashboard keeps working.
export default function ProjectDashboard({
  projectId,
}: {
  projectId?: string;
}) {
  const [loaded, setLoaded] = useState(false);
  const [payload, setPayload] = useState<ProjectCommandCenterPayload | null>(
    null,
  );
  const [healthSummary, setHealthSummary] = useState<ProjectHealthSummary | null>(
    null,
  );
  const [selected, setSelected] = useState<ReviewerAttentionItem | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [data, summary] = await Promise.all([
      getProjectCommandCenter(projectId),
      getProjectHealthSummary(projectId),
    ]);
    setPayload(data);
    setHealthSummary(summary);
  }, [projectId]);

  useEffect(() => {
    (async () => {
      await load();
      setLoaded(true);
    })();
  }, [load]);

  const handleRefresh = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    const result = await generateCommandCenterSnapshot(projectId);
    if (!result.ok) {
      setMessage(result.error ?? "Could not refresh the snapshot.");
    } else {
      setMessage("Command center snapshot refreshed.");
      setSelected(null);
      await load();
    }
    setBusy(false);
  }, [load, projectId]);

  const handleStatusChange = useCallback(
    async (attentionItemId: string, status: string) => {
      setBusy(true);
      const result = await updateAttentionItemStatus(
        attentionItemId,
        status,
        "Town Engineer",
      );
      if (!result.ok) {
        setMessage(result.error ?? "Could not update the attention item.");
      } else {
        await load();
      }
      setBusy(false);
    },
    [load],
  );

  const handleAddNote = useCallback(
    async (noteText: string) => {
      setBusy(true);
      const result = await addDashboardReviewerNote(
        noteText,
        "Town Engineer",
        "dashboard",
        projectId,
      );
      if (!result.ok) {
        setMessage(result.error ?? "Could not add the note.");
      } else {
        await load();
      }
      setBusy(false);
    },
    [load, projectId],
  );

  if (!loaded) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Loading project dashboard...
      </div>
    );
  }

  if (!payload) {
    return (
      <div className="space-y-6">
        <CommandCenterBoundaryNotice />
        <div className="surface-card p-6">
          <p className="text-sm text-slate-600">
            The command center is unavailable. Start the backend API to load the
            Brookside Meadows project dashboard. Command center data is not
            simulated in the browser.
          </p>
          <button
            type="button"
            onClick={handleRefresh}
            disabled={busy}
            className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
          >
            {busy ? "Working..." : "Generate snapshot"}
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
      <CommandCenterBoundaryNotice />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-slate-500">
          Aggregated review-support state. All statuses are review-support
          statuses, not final engineering decisions.
        </p>
        <button
          type="button"
          onClick={handleRefresh}
          disabled={busy}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-60"
        >
          {busy ? "Working..." : "Refresh snapshot"}
        </button>
      </div>

      {message ? (
        <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          {message}
        </p>
      ) : null}

      <CommandCenterSummaryCard snapshot={payload.snapshot} />
      <ProjectHealthMetricGrid metrics={payload.healthMetrics} />

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <ReviewerAttentionQueue
          items={payload.attentionItems}
          busy={busy}
          onStatusChange={handleStatusChange}
          onSelect={setSelected}
        />
        <div className="space-y-6">
          <ReviewerNextStepsPanel nextSteps={payload.nextSteps} />
          <AttentionItemDetailPanel item={selected} />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ReviewReadinessChecklist checks={payload.readinessChecks} />
        <ProjectHealthSummaryPanel summary={healthSummary} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ProjectTimeline events={payload.timeline} />
        <ProjectModuleLinksPanel moduleLinks={payload.moduleLinks} />
      </div>

      <DashboardReviewerNotesPanel
        notes={payload.reviewerNotes}
        busy={busy}
        onAdd={handleAddNote}
      />
    </div>
  );
}
