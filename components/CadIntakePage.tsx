"use client";

import RequestFailureCard from "@/components/RequestFailureCard";
import type { ApiFailure } from "@/lib/api/client";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createCadFileRecord,
  getCadBlocks,
  getCadFileReviewContext,
  getCadFiles,
  getCadIntakeDashboard,
  getCadParseQueue,
  getCadParseSummary,
  getCadReferenceCandidates,
  getCadReviewFindings,
  getCadText,
  getCadUploadLimits,
  getUnpromotedCadFindings,
  parseCadFile,
  promoteCadFindingToWorkflow,
  promoteSelectedCadFindingsToWorkflow,
  requestCadParse,
  type CadBlockExtract,
  type CadFileReviewContext,
  type CadFileUpload,
  type CadIntakeDashboard as CadIntakeDashboardData,
  type CadLayerExtract,
  type CadParseQueueItem,
  type CadParseSummary,
  type CadReferenceCandidate,
  type CadReviewFinding,
  type CadTextExtract,
  type CadUploadLimits,
  type UnpromotedCadFinding,
} from "@/lib/api";
import CadLimitationsNotice from "@/components/CadLimitationsNotice";
import CadFileList from "@/components/CadFileList";
import CadParseSummaryCard from "@/components/CadParseSummaryCard";
import CadLayerTable from "@/components/CadLayerTable";
import CadTextExtractTable from "@/components/CadTextExtractTable";
import CadReferenceCandidatePanel from "@/components/CadReferenceCandidatePanel";
import CadReviewFindingPanel from "@/components/CadReviewFindingPanel";
import CadPlanSheetComparisonPanel from "@/components/CadPlanSheetComparisonPanel";
import CadReviewContextPanel from "@/components/CadReviewContextPanel";
import CadUploadLimitsNotice from "@/components/CadUploadLimitsNotice";
import CadUploadPanel from "@/components/CadUploadPanel";
import CadIntakeDashboard from "@/components/CadIntakeDashboard";
import CadParseQueue from "@/components/CadParseQueue";
import CadParseFailurePanel from "@/components/CadParseFailurePanel";
import UnpromotedCadFindingsPanel from "@/components/UnpromotedCadFindingsPanel";
import CadFindingPromotionPanel from "@/components/CadFindingPromotionPanel";

type Tab = "layers" | "text" | "blocks" | "references" | "findings" | "compare";

// Orchestrates the CAD intake experience. Phase 12 adds browser DXF upload, a
// parse review queue, a CAD intake dashboard, and promotion of selected CAD
// findings into the workflow board. The per-file detail (parse summary, layers,
// text, blocks, reference candidates, plan sheet comparison, and findings) from
// Phase 11 remains below. All data is backend-canonical; nothing is simulated in
// the browser.
export default function CadIntakePage({
  initialCadFileId,
  projectId,
}: {
  initialCadFileId?: string;
  projectId?: string;
}) {
  const [files, setFiles] = useState<CadFileUpload[]>([]);
  const [selectedFileId, setSelectedFileId] = useState<string | null>(
    initialCadFileId ?? null,
  );
  const [context, setContext] = useState<CadFileReviewContext | null>(null);
  const [summary, setSummary] = useState<CadParseSummary | null>(null);
  const [layers, setLayers] = useState<CadLayerExtract[]>([]);
  const [texts, setTexts] = useState<CadTextExtract[]>([]);
  const [blocks, setBlocks] = useState<CadBlockExtract[]>([]);
  const [candidates, setCandidates] = useState<CadReferenceCandidate[]>([]);
  const [findings, setFindings] = useState<CadReviewFinding[]>([]);
  const [tab, setTab] = useState<Tab>("layers");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  // Phase 12 intake state.
  const [limits, setLimits] = useState<CadUploadLimits | null>(null);
  const [dashboard, setDashboard] = useState<CadIntakeDashboardData | null>(
    null,
  );
  const [queue, setQueue] = useState<CadParseQueueItem[]>([]);
  const [unpromoted, setUnpromoted] = useState<UnpromotedCadFinding[]>([]);
  const [selectedFindingIds, setSelectedFindingIds] = useState<Set<string>>(
    new Set(),
  );
  const [reviewerName, setReviewerName] = useState("reviewer");
  const [reviewerNote, setReviewerNote] = useState("");
  const [parseBusyId, setParseBusyId] = useState<string | null>(null);
  const [promoteBusyId, setPromoteBusyId] = useState<string | null>(null);
  const [failure, setFailure] = useState<ApiFailure | null>(null);
  const [promoteBusy, setPromoteBusy] = useState(false);
  const [promoteMessage, setPromoteMessage] = useState<string | null>(null);

  const loadForFile = useCallback(async (cadFileId: string) => {
    const ctxResult = await getCadFileReviewContext(cadFileId);
    if (!ctxResult.ok) setFailure(ctxResult);
    const ctx = ctxResult.ok ? ctxResult.data : null;
    setContext(ctx);
    setSummary(ctx?.summary ?? null);
    setLayers(ctx?.layers ?? []);
    setCandidates(ctx?.referenceCandidates ?? []);
    const runId = ctx?.parseRun?.parseRunId;
    if (runId) {
      const [textResult, blockResult] = await Promise.all([
        getCadText(runId),
        getCadBlocks(runId),
      ]);
      setTexts(textResult.ok ? textResult.data : []);
      setBlocks(blockResult.ok ? blockResult.data : []);
    } else {
      setTexts([]);
      setBlocks([]);
    }
    const findingsResult = await getCadReviewFindings(projectId);
    setFindings(findingsResult.ok ? findingsResult.data : []);
  }, [projectId]);

  const refreshIntake = useCallback(async () => {
    const [dResult, qResult, uResult] = await Promise.all([
      getCadIntakeDashboard(projectId),
      getCadParseQueue(projectId),
      getUnpromotedCadFindings(projectId),
    ]);
    setDashboard(dResult.ok ? dResult.data : null);
    setQueue(qResult.ok ? qResult.data : []);
    setUnpromoted(uResult.ok ? uResult.data : []);
    const intakeFailure = [dResult, qResult, uResult].find((r) => !r.ok);
    if (intakeFailure && !intakeFailure.ok) setFailure(intakeFailure);
  }, [projectId]);

  useEffect(() => {
    (async () => {
      const [cadFilesResult, uploadLimitsResult] = await Promise.all([
        getCadFiles(projectId),
        getCadUploadLimits(),
      ]);
      if (!cadFilesResult.ok) setFailure(cadFilesResult);
      const cadFiles = cadFilesResult.ok ? cadFilesResult.data : [];
      setFiles(cadFiles);
      setLimits(uploadLimitsResult.ok ? uploadLimitsResult.data : null);
      const initial =
        initialCadFileId ?? (cadFiles.length > 0 ? cadFiles[0].cadFileId : null);
      setSelectedFileId(initial);
      if (initial) await loadForFile(initial);
      await refreshIntake();
      setLoaded(true);
    })();
  }, [initialCadFileId, loadForFile, refreshIntake, projectId]);

  const handleSelect = useCallback(
    async (cadFileId: string) => {
      setSelectedFileId(cadFileId);
      await loadForFile(cadFileId);
    },
    [loadForFile],
  );

  const refreshSummary = useCallback(async () => {
    if (context?.parseRun?.parseRunId) {
      const [sResult, fResult] = await Promise.all([
        getCadParseSummary(context.parseRun.parseRunId),
        getCadReviewFindings(projectId),
      ]);
      setSummary(sResult.ok ? sResult.data : null);
      setFindings(fResult.ok ? fResult.data : []);
    }
    await refreshIntake();
  }, [context, refreshIntake, projectId]);

  const handleUploaded = useCallback(
    async (cadFileId: string) => {
      const cadFilesResult = await getCadFiles(projectId);
      setFiles(cadFilesResult.ok ? cadFilesResult.data : []);
      setSelectedFileId(cadFileId);
      await loadForFile(cadFileId);
      await refreshIntake();
    },
    [loadForFile, refreshIntake, projectId],
  );

  const handleRequestParse = useCallback(
    async (cadFileId: string) => {
      setParseBusyId(cadFileId);
      setMessage(null);
      const result = await requestCadParse(cadFileId);
      if (!result.ok) {
        setMessage(result.error ?? "Could not request a parse.");
      } else {
        setMessage(
          `Parse ${result.run?.status?.replace(/_/g, " ") ?? "requested"} for the DXF file.`,
        );
        const cadFilesResult = await getCadFiles(projectId);
        setFiles(cadFilesResult.ok ? cadFilesResult.data : []);
        if (cadFileId === selectedFileId) await loadForFile(cadFileId);
      }
      await refreshIntake();
      setParseBusyId(null);
    },
    [loadForFile, refreshIntake, selectedFileId, projectId],
  );

  const handleLoadSample = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    const created = await createCadFileRecord(undefined, undefined, projectId);
    if (!created.ok || !created.cadFile) {
      setMessage(created.error ?? "Could not register the sample DXF.");
      setBusy(false);
      return;
    }
    const parsed = await parseCadFile(created.cadFile.cadFileId);
    if (!parsed.ok) {
      setMessage(parsed.error ?? "Could not parse the DXF file.");
      setBusy(false);
      return;
    }
    const cadFilesResult = await getCadFiles(projectId);
    setFiles(cadFilesResult.ok ? cadFilesResult.data : []);
    setSelectedFileId(created.cadFile.cadFileId);
    await loadForFile(created.cadFile.cadFileId);
    await refreshIntake();
    setMessage("Sample DXF registered and parsed.");
    setBusy(false);
  }, [loadForFile, refreshIntake, projectId]);

  const toggleFinding = useCallback((id: string) => {
    setSelectedFindingIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const toggleAllFindings = useCallback(() => {
    setSelectedFindingIds((prev) => {
      if (unpromoted.every((f) => prev.has(f.cadReviewFindingId))) {
        return new Set();
      }
      return new Set(unpromoted.map((f) => f.cadReviewFindingId));
    });
  }, [unpromoted]);

  const handlePromoteOne = useCallback(
    async (id: string) => {
      setPromoteBusyId(id);
      setPromoteMessage(null);
      const result = await promoteCadFindingToWorkflow(
        id,
        reviewerName || "reviewer",
        reviewerNote || undefined,
      );
      if (!result.ok) {
        setPromoteMessage(result.error ?? "Could not promote the finding.");
      } else if (result.alreadyPromoted) {
        setPromoteMessage(
          "That finding is already promoted. No duplicate workflow item was created.",
        );
      } else {
        setPromoteMessage("Workflow item created from the CAD finding.");
      }
      setSelectedFindingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
      await loadForFile(selectedFileId ?? "");
      await refreshIntake();
      setPromoteBusyId(null);
    },
    [loadForFile, refreshIntake, reviewerName, reviewerNote, selectedFileId],
  );

  const handlePromoteSelected = useCallback(async () => {
    if (selectedFindingIds.size === 0) return;
    setPromoteBusy(true);
    setPromoteMessage(null);
    const result = await promoteSelectedCadFindingsToWorkflow(
      Array.from(selectedFindingIds),
      reviewerName || "reviewer",
      reviewerNote || undefined,
      projectId,
    );
    if (!result.ok) {
      setPromoteMessage(result.error ?? "Could not promote the findings.");
    } else {
      setPromoteMessage(
        `${result.createdCount ?? 0} workflow item(s) created. ${
          result.alreadyPromotedCount ?? 0
        } already promoted.`,
      );
    }
    setSelectedFindingIds(new Set());
    if (selectedFileId) await loadForFile(selectedFileId);
    await refreshIntake();
    setPromoteBusy(false);
  }, [
    loadForFile,
    refreshIntake,
    reviewerName,
    reviewerNote,
    selectedFileId,
    selectedFindingIds,
    projectId,
  ]);

  const tabs: Tab[] = useMemo(
    () => ["layers", "text", "blocks", "references", "findings", "compare"],
    [],
  );

  if (!loaded) {
    return (
      <div className="surface-card p-6 text-sm text-slate-600">
        Loading CAD intake...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <CadLimitationsNotice />
      {failure ? <RequestFailureCard failure={failure} /> : null}

      {/* Phase 12 intake: upload, dashboard, parse queue, and promotion. */}
      <CadUploadLimitsNotice limits={limits} />
      <CadUploadPanel limits={limits} onUploaded={handleUploaded} projectId={projectId} />
      <CadIntakeDashboard dashboard={dashboard} />
      <CadParseFailurePanel items={queue} />
      <CadParseQueue
        items={queue}
        busyFileId={parseBusyId}
        onRequestParse={handleRequestParse}
        onSelect={handleSelect}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <UnpromotedCadFindingsPanel
          findings={unpromoted}
          selectedIds={selectedFindingIds}
          onToggle={toggleFinding}
          onToggleAll={toggleAllFindings}
          onPromoteOne={handlePromoteOne}
          busyId={promoteBusyId}
        />
        <CadFindingPromotionPanel
          reviewerName={reviewerName}
          reviewerNote={reviewerNote}
          onReviewerNameChange={setReviewerName}
          onReviewerNoteChange={setReviewerNote}
          selectedCount={selectedFindingIds.size}
          busy={promoteBusy}
          onPromoteSelected={handlePromoteSelected}
          resultMessage={promoteMessage}
        />
      </div>

      {files.length === 0 ? (
        <div className="surface-card p-6">
          <p className="text-sm text-slate-600">
            No CAD file is loaded yet. Upload a DXF file above, or register and
            parse the bundled Brookside Meadows sample DXF.
          </p>
          <button
            type="button"
            onClick={handleLoadSample}
            disabled={busy}
            className="mt-4 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition-colors hover:bg-slate-50 disabled:opacity-60"
          >
            {busy ? "Working..." : "Load and parse sample DXF"}
          </button>
          {message ? (
            <p className="mt-4 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
              {message}
            </p>
          ) : null}
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-slate-600">
              DXF parsing extracts metadata and references only. It does not
              verify CAD or validate the design.
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleLoadSample}
                disabled={busy}
                className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-60"
              >
                {busy ? "Working..." : "Load sample DXF"}
              </button>
            </div>
          </div>

          {message ? (
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
              {message}
            </p>
          ) : null}

          <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
            <div className="space-y-6">
              <CadFileList
                files={files}
                selectedId={selectedFileId}
                onSelect={handleSelect}
              />
              <CadReviewContextPanel context={context} />
            </div>

            <div className="space-y-6">
              <CadParseSummaryCard
                run={context?.parseRun ?? null}
                summary={summary}
              />

              <div className="flex flex-wrap gap-2">
                {tabs.map((t) => (
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
                    {t === "compare" ? "Plan sheet comparison" : t}
                  </button>
                ))}
              </div>

              {tab === "layers" ? <CadLayerTable layers={layers} /> : null}
              {tab === "text" ? <CadTextExtractTable texts={texts} /> : null}
              {tab === "blocks" ? (
                <div className="surface-card p-6">
                  <h3 className="text-lg font-semibold text-slate-900">
                    Blocks
                  </h3>
                  {blocks.length === 0 ? (
                    <p className="mt-2 text-sm text-slate-600">
                      No blocks extracted.
                    </p>
                  ) : (
                    <ul className="mt-3 space-y-2">
                      {blocks.map((block) => (
                        <li
                          key={block.blockExtractId}
                          className="rounded-md border border-slate-200 px-3 py-2 text-sm"
                        >
                          <span className="font-medium text-slate-800">
                            {block.blockName}
                          </span>
                          <span className="ml-2 text-xs text-slate-600">
                            {block.insertCount} insert(s)
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : null}
              {tab === "references" ? (
                <CadReferenceCandidatePanel candidates={candidates} />
              ) : null}
              {tab === "findings" ? (
                <CadReviewFindingPanel findings={findings} />
              ) : null}
              {tab === "compare" && context?.parseRun ? (
                <CadPlanSheetComparisonPanel
                  parseRunId={context.parseRun.parseRunId}
                  onComparisonRun={refreshSummary}
                />
              ) : null}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
