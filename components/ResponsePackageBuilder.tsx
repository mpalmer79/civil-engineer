"use client";

import RequestFailureCard from "@/components/RequestFailureCard";
import type { ApiFailure } from "@/lib/api/client";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  generateResponsePackage,
  getResponsePackage,
  getResponsePackageHistory,
  getResponsePackages,
  getResponsePackageSummary,
  updateResponsePackageStatus,
  type ResponsePackageAction,
  type ResponsePackageDetail,
  type ResponsePackageItem,
  type ResponsePackageSummary,
} from "@/lib/api";
import ResponsePackageSummaryCard from "@/components/ResponsePackageSummaryCard";
import ResponsePackageSectionList from "@/components/ResponsePackageSectionList";
import ResponsePackageItemPanel from "@/components/ResponsePackageItemPanel";
import ResponseDraftEditor from "@/components/ResponseDraftEditor";
import ResponseEvidencePanel from "@/components/ResponseEvidencePanel";
import ResponseAttachmentChecklist from "@/components/ResponseAttachmentChecklist";
import ResponsePackagePrintPreview from "@/components/ResponsePackagePrintPreview";
import ResponsePackageHistoryTimeline from "@/components/ResponsePackageHistoryTimeline";
import ExternalCommunicationBoundaryNotice from "@/components/ExternalCommunicationBoundaryNotice";

type Tab = "items" | "attachments" | "history" | "print";

// Manual package status transitions. draft is the seeded status and is not a
// manual target. There is no approve status.
const PACKAGE_STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "needs_revision", label: "Needs revision" },
  { value: "reviewer_checked", label: "Reviewer checked" },
  { value: "ready_for_handoff", label: "Ready for handoff" },
  { value: "archived", label: "Archived" },
];

// Orchestrates the response package experience: generate or load the package,
// show its sections and items, the draft editor, linked evidence, attachments,
// history, and a printable draft preview.
export default function ResponsePackageBuilder({
  responsePackageId,
}: {
  responsePackageId?: string;
}) {
  const [pkg, setPkg] = useState<ResponsePackageDetail | null>(null);
  const [summary, setSummary] = useState<ResponsePackageSummary | null>(null);
  const [history, setHistory] = useState<ResponsePackageAction[]>([]);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [reviewerName, setReviewerName] = useState("Town Engineer");
  const [packageStatus, setPackageStatus] = useState("reviewer_checked");
  const [tab, setTab] = useState<Tab>("items");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [failure, setFailure] = useState<ApiFailure | null>(null);

  const loadPackage = useCallback(async (id: string) => {
    const [detailResult, sumResult, histResult] = await Promise.all([
      getResponsePackage(id),
      getResponsePackageSummary(id),
      getResponsePackageHistory(id),
    ]);
    if (!detailResult.ok) setFailure(detailResult);
    const detail = detailResult.ok ? detailResult.data : null;
    setPkg(detail);
    setSummary(sumResult.ok ? sumResult.data : null);
    setHistory(histResult.ok ? histResult.data.actions : []);
    if (detail) {
      const firstWithItems = detail.sections.find((s) => s.items.length > 0);
      if (firstWithItems) setSelectedItemId(firstWithItems.items[0].itemId);
    }
  }, []);

  useEffect(() => {
    (async () => {
      if (responsePackageId) {
        await loadPackage(responsePackageId);
      } else {
        const packagesResult = await getResponsePackages();
        if (packagesResult.ok && packagesResult.data.length > 0) {
          await loadPackage(packagesResult.data[0].responsePackageId);
        } else if (!packagesResult.ok) {
          setFailure(packagesResult);
        }
      }
      setLoaded(true);
    })();
  }, [responsePackageId, loadPackage]);

  const refresh = useCallback(async () => {
    if (pkg) {
      const [sumResult, histResult] = await Promise.all([
        getResponsePackageSummary(pkg.responsePackageId),
        getResponsePackageHistory(pkg.responsePackageId),
      ]);
      setSummary(sumResult.ok ? sumResult.data : null);
      setHistory(histResult.ok ? histResult.data.actions : []);
    }
  }, [pkg]);

  const handleGenerate = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    const result = await generateResponsePackage();
    if (result.ok && result.package) {
      setPkg(result.package);
      await loadPackage(result.package.responsePackageId);
      setMessage("Draft response package generated.");
    } else {
      setMessage(result.error ?? "Could not generate the response package.");
    }
    setBusy(false);
  }, [loadPackage]);

  const handleItemUpdated = useCallback(
    (updated: ResponsePackageItem) => {
      setPkg((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          sections: prev.sections.map((s) => ({
            ...s,
            items: s.items.map((i) =>
              i.itemId === updated.itemId ? { ...i, ...updated } : i,
            ),
          })),
        };
      });
      refresh();
    },
    [refresh],
  );

  const handlePackageStatus = useCallback(async () => {
    if (!pkg) return;
    setBusy(true);
    setMessage(null);
    const result = await updateResponsePackageStatus(
      pkg.responsePackageId,
      packageStatus,
      undefined,
      reviewerName,
    );
    if (result.ok && result.package) {
      setPkg((prev) => (prev ? { ...prev, status: result.package!.status } : prev));
      await refresh();
      setMessage(`Package marked ${packageStatus.replace(/_/g, " ")}.`);
    } else {
      setMessage(result.error ?? "Could not update the package status.");
    }
    setBusy(false);
  }, [pkg, packageStatus, reviewerName, refresh]);

  const selectedItem = useMemo(() => {
    if (!pkg) return null;
    for (const section of pkg.sections) {
      const found = section.items.find((i) => i.itemId === selectedItemId);
      if (found) return found;
    }
    return null;
  }, [pkg, selectedItemId]);

  if (loaded && !pkg && failure) {
    return (
      <div className="space-y-4">
        <ExternalCommunicationBoundaryNotice />
        <RequestFailureCard failure={failure} />
      </div>
    );
  }

  if (loaded && !pkg) {
    return (
      <div className="space-y-4">
        <ExternalCommunicationBoundaryNotice />
        <div className="surface-card p-6">
          <p className="text-sm text-slate-600">
            No response package is loaded yet. Generate a Brookside Meadows draft
            external response package to begin.
          </p>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={busy}
            className="mt-4 rounded-lg bg-water-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-water-700 disabled:opacity-60"
          >
            {busy ? "Generating..." : "Generate response package"}
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

  if (!pkg) {
    return (
      <div className="surface-card p-6 text-sm text-slate-500">
        Loading response package...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ExternalCommunicationBoundaryNotice />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          {(["items", "attachments", "history", "print"] as Tab[]).map((t) => (
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
              {t === "items"
                ? "Sections and items"
                : t === "attachments"
                  ? "Attachments"
                  : t === "history"
                    ? "History"
                    : "Printable draft"}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={handleGenerate}
          disabled={busy}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-60"
        >
          {busy ? "Regenerating..." : "Regenerate draft"}
        </button>
      </div>

      {message ? (
        <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">
          {message}
        </p>
      ) : null}

      <ResponsePackageSummaryCard pkg={pkg} summary={summary} />

      <div className="surface-card flex flex-wrap items-end gap-3 p-4">
        <label className="text-sm font-medium text-slate-700">
          Package status
          <select
            value={packageStatus}
            onChange={(e) => setPackageStatus(e.target.value)}
            className="mt-1 block rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-water-500 focus:outline-none focus:ring-1 focus:ring-water-500"
          >
            {PACKAGE_STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          onClick={handlePackageStatus}
          disabled={busy}
          className="rounded-lg bg-water-600 px-4 py-2 text-sm font-semibold text-white hover:bg-water-700 disabled:opacity-60"
        >
          Update package status
        </button>
      </div>

      {tab === "items" ? (
        <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
          <ResponsePackageSectionList
            sections={pkg.sections}
            selectedItemId={selectedItemId}
            onSelectItem={setSelectedItemId}
          />
          <div className="space-y-6">
            <ResponsePackageItemPanel
              packageId={pkg.responsePackageId}
              item={selectedItem}
              reviewerName={reviewerName}
              onReviewerNameChange={setReviewerName}
              onItemUpdated={handleItemUpdated}
            />
            <ResponseDraftEditor
              packageId={pkg.responsePackageId}
              item={selectedItem}
              reviewerName={reviewerName}
              onItemUpdated={handleItemUpdated}
            />
            <ResponseEvidencePanel item={selectedItem} />
          </div>
        </div>
      ) : null}

      {tab === "attachments" ? (
        <ResponseAttachmentChecklist attachments={pkg.attachments} />
      ) : null}

      {tab === "history" ? (
        <ResponsePackageHistoryTimeline actions={history} />
      ) : null}

      {tab === "print" ? (
        <ResponsePackagePrintPreview packageId={pkg.responsePackageId} />
      ) : null}
    </div>
  );
}
