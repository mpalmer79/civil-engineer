import CaseStudyFacts from "@/components/home/CaseStudyFacts";
import DxfShowcase from "@/components/home/DxfShowcase";
import FinalCta from "@/components/home/FinalCta";
import HomeHero from "@/components/home/HomeHero";
import HumanDecisionBoundary from "@/components/home/HumanDecisionBoundary";
import ProductPathways from "@/components/home/ProductPathways";
import RealVsSeeded from "@/components/home/RealVsSeeded";
import WorkflowStages from "@/components/home/WorkflowStages";

// Public product entry. This page explains what Civil Engineer AI is, who it
// supports, and how to evaluate it. It intentionally shows no operational
// widgets: every number rendered here is a reference-project fact counted from
// the seeded Brookside Meadows fixture and labeled as such. Section content
// lives in components/home; typed data lives in components/home/content.ts.
// The workflow section locates deterministic DXF metadata parsing in
// CAD Intake, matching the capability copy on the CAD pages. Live operational
// data lives behind sign-in on /dashboard, and deployment health lives on
// /deployment-status where it is derived from real diagnostics.

export default function HomePage() {
  return (
    <div className="bg-white text-slate-900">
      <HomeHero />
      <CaseStudyFacts />
      <WorkflowStages />
      <DxfShowcase />
      <HumanDecisionBoundary />
      <RealVsSeeded />
      <ProductPathways />
      <FinalCta />
    </div>
  );
}
