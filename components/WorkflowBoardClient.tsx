"use client";

import { useCallback, useEffect, useState } from "react";
import {
  generateWorkflowBoard,
  getReadyForHandoffSummary,
  getWorkflowBoardSummary,
  getWorkflowItem,
  getWorkflowItems,
  type ReadyForHandoffSummary,
  type WorkflowBoardSummary,
  type WorkflowItem,
  type WorkflowItemDetail,
} from "@/lib/api";
import WorkflowBoardSummaryCard from "@/components/WorkflowBoardSummaryCard";
import WorkflowColumn from "@/components/WorkflowColumn";
import WorkflowItemDetailPanel from "@/components/WorkflowItemDetailPanel";
import WorkflowActionPanel from "@/components/WorkflowActionPanel";
import WorkflowHistoryPanel from "@/components/WorkflowHistoryPanel";
import ReadyForHandoffPanel from "@/components/ReadyForHandoffPanel";
import ProfessionalLimitationsNotice from "@/components/ProfessionalLimitationsNotice";

// Board columns, in workflow order. Each is a workflow position, not an
// approval or certification state.
const COLUMNS: { status: string; label: string }[] = [
  { status: "draft", label: "Draft" },
  { status: "needs_triage", label: "Triage" },
  { status: "needs_follow_up", label: "Follow-up" },
  { status: "needs_more_information", label: "More information" },
  { status: "reviewer_checked", label: "Reviewer checked" },
  { status: "ready_for_handoff", label: "Ready for handoff" },
  { status: "excluded_from_packet", label: "Excluded" },
];

type Tab = "board" | "handoff";

// Orchestrates the reviewer workflow board: load or generate the board, show
// the columns, the selected item detail and history, the reviewer action form,
// and the ready-for-handoff summary.
export default function WorkflowBoardClient({
  initialItemId,
  projectId,
}: {
  initialItemId?: string;
  projectId?: string;
}) {
  const [items, setItems] = useState<WorkflowItem[]>([]);
  const [summary, setSummary] = useState<WorkflowBoardSummary | null>(null);
  const [handoff, setHandoff] = useState<ReadyForHandoffSummary | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(
    initialItemId ?? null,
  );
  const [detail, setDetail] = useState<WorkflowItemDetail | null>(null);
  const [reviewerName, setReviewerName] = useState("Town Engineer");
  const [tab, setTab] = useState<Tab>("board");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const refreshBoard = useCallback(async () => {
    const [boardItems, boardSummary, handoffSummary] = await Promise.all([
      getWorkflowItems(undefined, projectId),
      getWorkflowBoardSummary(projectId),
      getReadyForHandoffSummary(projectId),
    ]);
    setItems(boardItems);
    setSummary(boardSummary);
    setHandoff(handoffSummary);
    return boardItems;
  }, [projectId]);

  const loadDetail = useCallback(async (id: string | null) => {
    if (!id) {
      setDetail(null);
      return;
    }
    setDetail(await getWorkflowItem(id));
  }, []);

  useEffect(() => {
    (async () => {
      const boardItems = await refreshBoard();
      const initial =
        initialItemId ?? (boardItems.length > 0 ? boardItems[0].workflowItemId : null);
      setSelectedId(initial);
      await loadDetail(initial);
      setLoaded(true);
    })();
  }, [refreshBoard, loadDetail, initialItemId]);

  const handleSelect = useCallback(
    async (id: string) => {
      setSelectedId(id);
      await loadDetail(id);
    },
    [loadDetail],
  );

  const handleChanged = useCallback(async () => {
    await refreshBoard();
    await loadDetail(selectedId);
  }, [refreshBoard, loadDetail, selectedId]);

  const handleGenerate = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    const result = await generateWorkflowBoard(projectId);
    if (result.ok) {
      const boardItems = await refreshBoard();
      const first = boardItems.length > 0 ? boardItems[0].workflowItemId : null;
      setSelectedId(first);
      await loadDetail(first);
      setMessage("Workflow board generated from the latest review packet.");
    } else {
      setMessage(result.error ?? "Could not generate the workflow board.");
    }
    setBusy(false);
  }, [refreshBoard, loadDetail, projectId]);

  if (loaded && items.length === 0) {
    return (
      <div className="space-y-4">
        <ProfessionalLimitationsNotice text="This board organizes review-support items for human reviewers. It does not approve plans, certify compliance, verify CAD, validate a design, or replace a licensed Professional Engineer." />
        <div className="surface-card p-6">
          <p className="text-sm text-slate-600">
            No workflow board is loaded yet. Generate the reviewer workflow board
            for this project from the latest review packet to begin.
          </p>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={busy}
            className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
          >
            {busy ? "Generating..." : "Generate workflow board"}
          </button>
          {message ? (
            <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
              {message}
            </p>
          ) : null}
        </div>
      </div>
    );
  }

  if (!loaded) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Loading workflow board...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ProfessionalLimitationsNotice text="This board organizes review-support items for human reviewers. It does not approve plans, certify compliance, verify CAD, validate a design, or replace a licensed Professional Engineer." />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          {(["board", "handoff"] as Tab[]).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={`rounded-lg px-3 py-1.5 text-sm font-semibold transition-colors ${
                tab === t
                  ? "bg-water-600 text-white"
                  : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
              }`}
            >
              {t === "board" ? "Board" : "Ready for handoff"}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={handleGenerate}
          disabled={busy}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-60"
        >
          {busy ? "Regenerating..." : "Regenerate board"}
        </button>
      </div>

      {message ? (
        <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          {message}
        </p>
      ) : null}

      <WorkflowBoardSummaryCard summary={summary} />

      {tab === "board" ? (
        <>
          <div className="overflow-x-auto pb-2">
            <div className="flex gap-3">
              {COLUMNS.map((col) => (
                <WorkflowColumn
                  key={col.status}
                  label={col.label}
                  status={col.status}
                  items={items}
                  selectedItemId={selectedId}
                  onSelectItem={handleSelect}
                />
              ))}
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
            <div className="space-y-6">
              <WorkflowItemDetailPanel item={detail} />
              <WorkflowHistoryPanel actions={detail?.actions ?? []} />
            </div>
            <WorkflowActionPanel
              item={detail}
              reviewerName={reviewerName}
              onReviewerNameChange={setReviewerName}
              onChanged={handleChanged}
            />
          </div>
        </>
      ) : (
        <ReadyForHandoffPanel summary={handoff} />
      )}
    </div>
  );
}
