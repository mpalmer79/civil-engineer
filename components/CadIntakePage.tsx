"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createCadFileRecord,
  createWorkflowItemsFromCadFindings,
  getCadBlocks,
  getCadFileReviewContext,
  getCadFiles,
  getCadLayers,
  getCadParseSummary,
  getCadReferenceCandidates,
  getCadReviewFindings,
  getCadText,
  parseCadFile,
  type CadBlockExtract,
  type CadFileReviewContext,
  type CadFileUpload,
  type CadLayerExtract,
  type CadParseSummary,
  type CadReferenceCandidate,
  type CadReviewFinding,
  type CadTextExtract,
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

type Tab = "layers" | "text" | "blocks" | "references" | "findings" | "compare";

// Orchestrates the CAD intake experience: load or register and parse the sample
// Brookside Meadows DXF, then show the parse summary, extracted layers, text,
// blocks, reference candidates, plan sheet comparison, and CAD review findings.
export default function CadIntakePage({
  initialCadFileId,
}: {
  initialCadFileId?: string;
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

  const loadForFile = useCallback(async (cadFileId: string) => {
    const ctx = await getCadFileReviewContext(cadFileId);
    setContext(ctx);
    setSummary(ctx?.summary ?? null);
    setLayers(ctx?.layers ?? []);
    setCandidates(ctx?.referenceCandidates ?? []);
    const runId = ctx?.parseRun?.parseRunId;
    if (runId) {
      const [textData, blockData] = await Promise.all([
        getCadText(runId),
        getCadBlocks(runId),
      ]);
      setTexts(textData);
      setBlocks(blockData);
    } else {
      setTexts([]);
      setBlocks([]);
    }
    setFindings(await getCadReviewFindings());
  }, []);

  useEffect(() => {
    (async () => {
      const cadFiles = await getCadFiles();
      setFiles(cadFiles);
      const initial =
        initialCadFileId ?? (cadFiles.length > 0 ? cadFiles[0].cadFileId : null);
      setSelectedFileId(initial);
      if (initial) await loadForFile(initial);
      setLoaded(true);
    })();
  }, [initialCadFileId, loadForFile]);

  const handleSelect = useCallback(
    async (cadFileId: string) => {
      setSelectedFileId(cadFileId);
      await loadForFile(cadFileId);
    },
    [loadForFile],
  );

  const refreshSummary = useCallback(async () => {
    if (context?.parseRun?.parseRunId) {
      const [s, f] = await Promise.all([
        getCadParseSummary(context.parseRun.parseRunId),
        getCadReviewFindings(),
      ]);
      setSummary(s);
      setFindings(f);
    }
  }, [context]);

  const handleLoadSample = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    const created = await createCadFileRecord();
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
    const cadFiles = await getCadFiles();
    setFiles(cadFiles);
    setSelectedFileId(created.cadFile.cadFileId);
    await loadForFile(created.cadFile.cadFileId);
    setMessage("Sample DXF registered and parsed.");
    setBusy(false);
  }, [loadForFile]);

  const handleCreateWorkflowItems = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    const result = await createWorkflowItemsFromCadFindings();
    if (result.ok) {
      setMessage(
        `${result.createdCount} workflow item(s) created from CAD findings.`,
      );
      await loadForFile(selectedFileId ?? "");
    } else {
      setMessage(result.error ?? "Could not create workflow items.");
    }
    setBusy(false);
  }, [loadForFile, selectedFileId]);

  const tabs: Tab[] = useMemo(
    () => ["layers", "text", "blocks", "references", "findings", "compare"],
    [],
  );

  if (loaded && files.length === 0) {
    return (
      <div className="space-y-4">
        <CadLimitationsNotice />
        <div className="surface-card p-6">
          <p className="text-sm text-slate-600">
            No CAD file is loaded yet. Register and parse the bundled Brookside
            Meadows sample DXF to begin. This phase is backend fixture-based DXF
            parsing; browser file upload is a later enhancement.
          </p>
          <button
            type="button"
            onClick={handleLoadSample}
            disabled={busy}
            className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
          >
            {busy ? "Working..." : "Load and parse sample DXF"}
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
        Loading CAD intake...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <CadLimitationsNotice />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-slate-500">
          Backend fixture-based DXF parsing. Browser upload is a later
          enhancement.
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleLoadSample}
            disabled={busy}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-60"
          >
            {busy ? "Working..." : "Reparse sample DXF"}
          </button>
          <button
            type="button"
            onClick={handleCreateWorkflowItems}
            disabled={busy}
            className="rounded-lg bg-water-600 px-3 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-water-700 disabled:opacity-60"
          >
            Create workflow items from findings
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
              <h3 className="text-lg font-semibold text-slate-900">Blocks</h3>
              {blocks.length === 0 ? (
                <p className="mt-2 text-sm text-slate-500">No blocks extracted.</p>
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
                      <span className="ml-2 text-xs text-slate-500">
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
    </div>
  );
}
