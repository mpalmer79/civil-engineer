# Civil Engineer AI: SaaS Positioning

A one-page positioning reference for future development sessions and for outreach.
This document complements `docs/civil-engineer-ai-saas-roadmap.md`. The roadmap
sequences the work; this document fixes the message.

## Target buyer

Small to mid-sized civil and AEC firms preparing stormwater, site, and civil
packages for municipal submittal. The buyer is the team running internal
pre-submittal QA before a package leaves the office.

Municipal review departments are a secondary, future audience. The homepage
speaks first to firms trying to reduce avoidable resubmittal cycles, not to
municipalities.

## Primary pain

Avoidable review comments and resubmittal cycles. Every missed item in a review
round costs the firm a resubmittal cycle, which is real schedule slip and real
cost. Catching those items before submittal is a profit-and-loss argument, not
just a workflow improvement.

## Product promise

Catch likely review-support issues earlier, with source-backed traceability.
Civil Engineer AI helps a team review the package before it goes out by
organizing DXF metadata, surfacing plan and report conflicts, keeping evidence
traceable, tracking workflow items, and drafting a reviewer handoff package.

Preferred language: catch review issues before submittal, reduce avoidable
resubmittal risk, pre-submittal QA, review-support findings, evidence-linked
issues, source-backed traceability, draft reviewer handoff package, human
reviewer remains responsible, every finding tied back to source context.

## What the product does today

- CAD and DXF intake that organizes DXF metadata and surfaces review-support findings.
- Plan and report consistency checks that flag conflicts across the package.
- Evidence traceability that ties each finding back to a specific page or sheet.
- A workflow board for tracking review-support items.
- A draft reviewer handoff package assembled from reviewer-selected records.
- A guided demo over the Brookside Meadows sample project, using seeded demo data.

## What the product does not claim

The product does not approve plans, certify compliance, stamp drawings, verify,
validate, or make final engineering decisions. It does not guarantee compliance,
declare a project safe, promise passing review, or guarantee first-pass
acceptance. The human reviewer remains responsible for every item, and source
context stays visible so the reviewer can check the basis for each finding.

Seeded demo data is labeled as seeded review-support demo data. It is not
extracted from a real CAD, PDF, GIS, or plan file.

## Demo flow

Brookside Meadows is the sample project. The public demo path needs no login to
explore the review-support workflow:

1. CAD intake: `/projects/proj_brookside_meadows/cad`
2. Plan and report consistency: `/projects/proj_brookside_meadows/plan-consistency`
3. Evidence traceability: `/projects/proj_brookside_meadows/traceability`
4. Draft reviewer handoff: `/projects/proj_brookside_meadows/review-packets`
5. Command center: `/projects/proj_brookside_meadows/command-center`

The guided demo at `/guided-demo` walks these steps in reviewer order. The demo
project id is centralized as `BROOKSIDE_PROJECT_ID` in `lib/demoJourney.ts`.

## Homepage message

The first screen sells the outcome. Headline: catch stormwater review issues
before submittal. The hero shows real review-support findings from the seeded
demo, with fixture-backed counts. The four capabilities that matter to the buyer
lead the page: CAD and DXF intake, plan and report consistency, evidence
traceability, and the draft reviewer handoff package. The professional boundary
sits below the fold as a single credibility section, reassuring after interest is
created rather than suppressing it before it forms.

## Recommended outreach positioning

Lead with the resubmittal-cost argument: run the package through pre-submittal QA
and catch the review-support issues a municipal reviewer would catch, before the
package goes out. Run a prospect's own demo over the Brookside Meadows fixture in
one click, no sales call required. Offer a design-partner pilot for firms willing
to provide real usage and a quote.

## Future buyer expansion to municipalities

Municipal review departments are a phase-two audience. Once AEC firms are using
the product on their own submissions, the municipal pitch becomes warm: the firms
submitting to that office already run this before they send it. Do not lead with
municipalities and do not pursue government procurement yet.

## Current limitations

- Live AI calls are disabled by default.
- No real PDF, DWG, DXF, or GIS parsing; no OCR, computer vision, or vector search.
- No authentication lifecycle, billing, or production database provider in this phase.
- Demo content is seeded review-support data, not a real submission.
- The product is review support only and does not make final engineering decisions.
