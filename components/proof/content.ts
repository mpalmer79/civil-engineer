// Typed static content for the public technical validation page at
// /proof-of-concept. Every metric shown on that page is read from the
// generated structured test result and the artifact manifest in
// lib/proof/data; this module holds only the static prose lists that frame
// those results. Nothing here overrides or restates an artifact value.

export const provenPoints: readonly string[] = [
  "A structurally valid DXF is accepted by the real intake validation",
  "The production ezdxf parser executes against the uploaded file",
  "Entities and layers are inventoried with safe local bounds",
  "Text, blocks, and drawing units are extracted",
  "Sheet and detail references are identified and matched against the plan-sheet index",
  "Results persist to the database and are retrieved through reviewer-facing endpoints",
  "Review-support findings come from deterministic rules",
  "The artifacts regenerate byte-identically from the committed scripts",
] as const;

export const notProvenPoints: readonly string[] = [
  "Correct basin sizing",
  "Correct pipe slope",
  "Adequate hydraulic capacity",
  "Correct grading",
  "Regulatory compliance",
  "Construction readiness",
  "Design safety",
  "Final plan approval",
  "Survey accuracy",
  "Complete CAD semantic understanding",
] as const;

export type WorkflowBenefit = {
  title: string;
  detail: string;
};

export const workflowBenefits: readonly WorkflowBenefit[] = [
  {
    title: "Faster drawing inventory",
    detail:
      "A reviewer sees every layer, block, and annotation within seconds of upload instead of opening the file and panning through it.",
  },
  {
    title: "Early missing-reference identification",
    detail:
      "Sheet callouts that point at sheets absent from the submission surface before a reviewer has read a single page.",
  },
  {
    title: "Layer organization at a glance",
    detail:
      "The taxonomy sorts layers into review categories with the rule and confidence shown, and unknown layers stay visible for reviewer categorization.",
  },
  {
    title: "Searchable plan annotations",
    detail:
      "Extracted text is normalized and stored, so labels and notes become searchable evidence rather than pixels.",
  },
  {
    title: "Consistent review preparation",
    detail:
      "Every submission passes the same deterministic checks, so preparation quality does not depend on who picks up the file.",
  },
  {
    title: "Stronger reviewer handoff",
    detail:
      "Findings carry their evidence, rule, and confidence, and every one requires human review. Engineering judgment stays with the licensed reviewer.",
  },
] as const;

export const nextImprovements: readonly string[] = [
  "Configurable per-organization and per-project layer taxonomy overrides with an audit trail",
  "Typed facility identity persisted with the parse run rather than derived at parse time",
  "Broader geometry support, including exact envelopes where only safe overestimates exist today",
  "Reference parsing across more callout conventions without overmatching",
  "A larger DXF evaluation corpus covering more drafting styles",
  "Browser-level upload validation before bytes leave the reviewer's machine",
  "Documented performance limits over large drawings",
  "Additional civil drawing conventions beyond subdivision stormwater plans",
] as const;

export const testedDrawingContents: readonly string[] = [
  "47 conceptual lots with lot number labels",
  "Road alignment with a cul-de-sac",
  "Grading contours with elevation labels",
  "Wetland boundary and 50 ft buffer",
  "Detention and infiltration facilities",
  "Storm pipes and an outfall",
  "Erosion and sediment controls",
  "Utility corridors",
  "Sheet references, including one intentionally missing sheet",
  "Detail references, including one intentionally ambiguous callout",
  "Facility labels that intentionally share numbers across types",
  "Five reusable CAD blocks and a paper-space title layout",
] as const;

export const proofLogicModules: readonly string[] = [
  "scripts/generate_brookside_proof_dxf.py",
  "scripts/run_dxf_proof.py",
  "scripts/dxf_proof_expected.json",
  "backend/app/services/cad/layer_taxonomy.py",
  "backend/app/services/cad/facility_identity.py",
  "backend/app/services/cad/reference_parser.py",
  "backend/app/services/cad/geometry.py",
  "backend/app/services/cad_intake_service.py",
] as const;
