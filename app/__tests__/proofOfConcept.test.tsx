import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ProofOfConceptPage, { metadata } from "@/app/proof-of-concept/page";
import { proofManifest, proofResult } from "@/lib/proof/data";
import nextConfig from "@/next.config.mjs";

describe("proof of concept page", () => {
  it("renders the hero with the synthetic disclosure", () => {
    render(<ProofOfConceptPage />);
    expect(
      screen.getByRole("heading", {
        name: "Proof of Concept: DXF Intake and Review Support",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/The drawing is synthetic\./),
    ).toBeInTheDocument();
  });

  it("shows the metrics sourced from the structured artifact", () => {
    render(<ProofOfConceptPage />);
    const counts = proofResult.counts;
    const metric = (label: string) => {
      const terms = screen.getAllByText(label, { selector: "dt" });
      expect(terms).toHaveLength(1);
      return terms[0].nextSibling;
    };
    expect(metric("Entities")).toHaveTextContent(String(counts.entities));
    expect(metric("Layers")).toHaveTextContent(String(counts.layers));
    expect(metric("Text records")).toHaveTextContent(
      String(counts.text_records),
    );
    expect(metric("Review-support findings")).toHaveTextContent(
      String(counts.findings),
    );
  });

  it("does not render the consistency alert when the artifact is valid", () => {
    render(<ProofOfConceptPage />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders all pipeline stages from the artifact", () => {
    render(<ProofOfConceptPage />);
    for (const stage of proofResult.pipeline) {
      expect(
        screen.getAllByText(stage.stage).length,
      ).toBeGreaterThanOrEqual(1);
      expect(
        screen.getAllByText(stage.module).length,
      ).toBeGreaterThanOrEqual(1);
    }
  });

  it("features all four artifacts with hashes and download routes", () => {
    render(<ProofOfConceptPage />);
    expect(proofManifest.artifacts).toHaveLength(4);
    for (const artifact of proofManifest.artifacts) {
      expect(screen.getByText(artifact.display_name)).toBeInTheDocument();
      expect(
        screen.getByText(`sha256: ${artifact.sha256}`),
      ).toBeInTheDocument();
      const link = screen.getByRole("link", {
        name: `Download ${artifact.filename}`,
      });
      expect(link).toHaveAttribute("href", artifact.download_route);
    }
  });

  it("shows the limitations and what the test does not prove", () => {
    render(<ProofOfConceptPage />);
    expect(screen.getByText("What this does not prove")).toBeInTheDocument();
    expect(screen.getByText("Regulatory compliance")).toBeInTheDocument();
    expect(screen.getByText("Final plan approval")).toBeInTheDocument();
    for (const limitation of proofResult.limitations) {
      expect(screen.getByText(limitation)).toBeInTheDocument();
    }
  });

  it("uses review-support language, never determination language", () => {
    const { container } = render(<ProofOfConceptPage />);
    const text = container.textContent ?? "";
    expect(text).toContain("needs human review");
    // Forbidden status wording must not appear as a status claim. The page
    // may say what the test does NOT prove, so check the phrases that would
    // assert a determination.
    expect(text).not.toMatch(/design validated/i);
    expect(text).not.toMatch(/\bcertified\b/i);
    expect(text).not.toMatch(/\bapproved\b/i);
    expect(text).not.toMatch(/all systems operational/i);
  });

  it("does not fake live activity", () => {
    const { container } = render(<ProofOfConceptPage />);
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/\blive\b|real[- ]time processing/i);
    expect(text).toContain(proofResult.snapshot_id);
  });

  it("links onward to the demo, overview, project, and CAD intake", () => {
    render(<ProofOfConceptPage />);
    const hrefs = screen
      .getAllByRole("link")
      .map((link) => link.getAttribute("href"));
    expect(hrefs).toContain("/guided-demo");
    expect(hrefs).toContain("/start-here");
    expect(hrefs).toContain("/projects/proj_brookside_meadows");
    expect(hrefs).toContain("/projects/proj_brookside_meadows/cad");
  });

  it("declares honest metadata without certification keywords", () => {
    expect(metadata.title).toContain("Proof of Concept");
    const description = String(metadata.description);
    expect(description).toContain("synthetic");
    expect(description).not.toMatch(/certif|approv|complian/i);
  });
});

describe("proof of concept redirects", () => {
  it("permanently redirects /proofofconcept and /poc", async () => {
    expect(nextConfig.redirects).toBeDefined();
    const redirects = await nextConfig.redirects!();
    const bySource = Object.fromEntries(
      redirects.map((redirect) => [redirect.source, redirect]),
    );
    expect(bySource["/proofofconcept"]).toMatchObject({
      destination: "/proof-of-concept",
      permanent: true,
    });
    expect(bySource["/poc"]).toMatchObject({
      destination: "/proof-of-concept",
      permanent: true,
    });
  });
});
