"use client";

import RequestFailureCard from "@/components/RequestFailureCard";
import type { ApiFailure } from "@/lib/api/client";
import { useCallback, useEffect, useState } from "react";
import {
  createCadFileRecord,
  getCadBlocks,
  getCadFileReviewContext,
  getCadFiles,
  getCadIntakeDashboard,
  getCadParseQueue,
  getCadParseSummary,
  getCadReviewFindings,
  getCadText,
  getCadUploadLimits,
  getUnpromotedCadFindings,
  parseCadFile,
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
import CadFileDetailSection from "@/components/cad-intake/CadFileDetailSection";
import CadFindingPromotionSection from "@/components/cad-intake/CadFindingPromotionSection";
import CadIntakeEmptyState from "@/components/cad-intake/CadIntakeEmptyState";
import CadIntakeDashboard from "@/components/CadIntakeDashboard";
import CadLimitationsNotice from "@/components/CadLimitationsNotice";
import CadParseFailurePanel from "@/components/CadParseFailurePanel";
import CadParseQueue from "@/components/CadParseQueue";
import CadUploadLimitsNotice from "@/components/CadUploadLimitsNotice";
import CadUploadPanel from "@/components/CadUploadPanel";

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
  const [parseBusyId, setParseBusyId] = useState<string | null>(null);
  const [failure, setFailure] = useState<ApiFailure | null>(null);

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

      <CadFindingPromotionSection
        unpromoted={unpromoted}
        selectedFileId={selectedFileId}
        projectId={projectId}
        loadForFile={loadForFile}
        refreshIntake={refreshIntake}
      />

      {files.length === 0 ? (
        <CadIntakeEmptyState
          busy={busy}
          message={message}
          onLoadSample={handleLoadSample}
        />
      ) : (
        <CadFileDetailSection
          files={files}
          selectedFileId={selectedFileId}
          onSelect={handleSelect}
          context={context}
          summary={summary}
          layers={layers}
          texts={texts}
          blocks={blocks}
          candidates={candidates}
          findings={findings}
          busy={busy}
          message={message}
          onLoadSample={handleLoadSample}
          onComparisonRun={refreshSummary}
        />
      )}
    </div>
  );
}
