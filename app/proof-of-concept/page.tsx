import type { Metadata } from "next";

import ProofBenefits from "@/components/proof/ProofBenefits";
import ProofCta from "@/components/proof/ProofCta";
import ProofDownloads from "@/components/proof/ProofDownloads";
import ProofFindings from "@/components/proof/ProofFindings";
import ProofHero from "@/components/proof/ProofHero";
import ProofIntegrityAlert from "@/components/proof/ProofIntegrityAlert";
import ProofLayers from "@/components/proof/ProofLayers";
import ProofNext from "@/components/proof/ProofNext";
import ProofPipeline from "@/components/proof/ProofPipeline";
import ProofProves from "@/components/proof/ProofProves";
import ProofReferences from "@/components/proof/ProofReferences";
import ProofRepro from "@/components/proof/ProofRepro";
import ProofResults from "@/components/proof/ProofResults";
import ProofTested from "@/components/proof/ProofTested";

// Public technical validation page. Every metric is read from the generated
// structured test result and the artifact manifest through lib/proof/data;
// nothing is hardcoded separately from the evidence. ProofIntegrityAlert
// re-checks the artifact's own ground-truth checks and renders a visible
// failure when the artifact and the displayed metrics disagree. Section
// components live in components/proof; static prose lives in
// components/proof/content.ts.

export const metadata: Metadata = {
  title: "Proof of Concept: DXF Intake and Review Support | Civil Engineer AI",
  description:
    "Reproducible DXF proof of concept: deterministic CAD metadata extraction, reference identification, and stormwater review support over a synthetic Brookside Meadows test drawing.",
};

export default function ProofOfConceptPage() {
  return (
    <div className="bg-white text-slate-900">
      <ProofHero />
      <ProofIntegrityAlert />
      <ProofTested />
      <ProofPipeline />
      <ProofResults />
      <ProofReferences />
      <ProofLayers />
      <ProofFindings />
      <ProofProves />
      <ProofBenefits />
      <ProofRepro />
      <ProofDownloads />
      <ProofNext />
      <ProofCta />
    </div>
  );
}
