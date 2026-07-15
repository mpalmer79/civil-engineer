"use client";

import { useMemo, useState } from "react";

import CadFileList from "@/components/CadFileList";
import CadLayerTable from "@/components/CadLayerTable";
import CadParseSummaryCard from "@/components/CadParseSummaryCard";
import CadPlanSheetComparisonPanel from "@/components/CadPlanSheetComparisonPanel";
import CadReferenceCandidatePanel from "@/components/CadReferenceCandidatePanel";
import CadReviewContextPanel from "@/components/CadReviewContextPanel";
import CadReviewFindingPanel from "@/components/CadReviewFindingPanel";
import CadTextExtractTable from "@/components/CadTextExtractTable";
import type {
  CadBlockExtract,
  CadFileReviewContext,
  CadFileUpload,
  CadLayerExtract,
  CadParseSummary,
  CadReferenceCandidate,
  CadReviewFinding,
  CadTextExtract,
} from "@/lib/api";

type Tab = "layers" | "text" | "blocks" | "references" | "findings" | "compare";

// Per-file CAD detail from Phase 11: parse summary, layers, text, blocks,
// reference candidates, plan sheet comparison, and findings. DXF parsing
// extracts metadata and references only.
export default function CadFileDetailSection({
  files,
  selectedFileId,
  onSelect,
  context,
  summary,
  layers,
  texts,
  blocks,
  candidates,
  findings,
  busy,
  message,
  onLoadSample,
  onComparisonRun,
}: {
  files: CadFileUpload[];
  selectedFileId: string | null;
  onSelect: (cadFileId: string) => Promise<void>;
  context: CadFileReviewContext | null;
  summary: CadParseSummary | null;
  layers: CadLayerExtract[];
  texts: CadTextExtract[];
  blocks: CadBlockExtract[];
  candidates: CadReferenceCandidate[];
  findings: CadReviewFinding[];
  busy: boolean;
  message: string | null;
  onLoadSample: () => Promise<void>;
  onComparisonRun: () => Promise<void>;
}) {
  const [tab, setTab] = useState<Tab>("layers");

  const tabs: Tab[] = useMemo(
    () => ["layers", "text", "blocks", "references", "findings", "compare"],
    [],
  );

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-slate-600">
          DXF parsing extracts metadata and references only. It does not
          verify CAD or validate the design.
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={onLoadSample}
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
            onSelect={onSelect}
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
              onComparisonRun={onComparisonRun}
            />
          ) : null}
        </div>
      </div>
    </>
  );
}
