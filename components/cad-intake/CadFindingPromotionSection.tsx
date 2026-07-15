"use client";

import { useCallback, useState } from "react";

import CadFindingPromotionPanel from "@/components/CadFindingPromotionPanel";
import UnpromotedCadFindingsPanel from "@/components/UnpromotedCadFindingsPanel";
import {
  promoteCadFindingToWorkflow,
  promoteSelectedCadFindingsToWorkflow,
  type UnpromotedCadFinding,
} from "@/lib/api";

// Promotion of selected CAD findings into the workflow board. Owns the
// selection, reviewer attribution, and promotion result state.
export default function CadFindingPromotionSection({
  unpromoted,
  selectedFileId,
  projectId,
  loadForFile,
  refreshIntake,
}: {
  unpromoted: UnpromotedCadFinding[];
  selectedFileId: string | null;
  projectId?: string;
  loadForFile: (cadFileId: string) => Promise<void>;
  refreshIntake: () => Promise<void>;
}) {
  const [selectedFindingIds, setSelectedFindingIds] = useState<Set<string>>(
    new Set(),
  );
  const [reviewerName, setReviewerName] = useState("reviewer");
  const [reviewerNote, setReviewerNote] = useState("");
  const [promoteBusyId, setPromoteBusyId] = useState<string | null>(null);
  const [promoteBusy, setPromoteBusy] = useState(false);
  const [promoteMessage, setPromoteMessage] = useState<string | null>(null);

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

  return (
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
  );
}
