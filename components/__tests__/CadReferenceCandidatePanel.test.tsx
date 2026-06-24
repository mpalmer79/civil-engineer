import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import CadReferenceCandidatePanel from "@/components/CadReferenceCandidatePanel";
import type { CadReferenceCandidate } from "@/lib/api";

const candidate: CadReferenceCandidate = {
  candidateId: "cadref_1",
  parseRunId: "cadrun_1",
  cadFileId: "cad_1",
  projectId: "proj_brookside_meadows",
  referenceText: "C-3.1",
  normalizedReference: "C-3.1",
  referenceType: "sheet_reference",
  sourceEntityId: null,
  sourceTextId: "cadtxt_1",
  matchedPlanSheetId: "sheet_c31",
  matchedPlanReferenceId: null,
  confidenceLabel: "high",
  matchReason: "Sheet C-3.1 matches seeded plan sheet.",
  requiresHumanReview: false,
};

describe("CadReferenceCandidatePanel", () => {
  it("renders a candidate with its confidence label", () => {
    render(<CadReferenceCandidatePanel candidates={[candidate]} />);
    expect(screen.getByText("C-3.1")).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it("shows an empty state when there are no candidates", () => {
    render(<CadReferenceCandidatePanel candidates={[]} />);
    expect(
      screen.getByText("No reference candidates detected."),
    ).toBeInTheDocument();
  });
});
