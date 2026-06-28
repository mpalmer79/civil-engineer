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

- CAD and DXF intake that parses real DXF files with the ezdxf library and
  organizes the extracted layer, entity, block, and text metadata into
  review-support findings. Browser DXF uploads are accepted, validated, and
  parsed the same way as the bundled sample file.
- PDF text-layer indexing with the pypdf library, where extractable text exists.
  Scanned pages without a text layer are recorded as having no extractable text.
- Plan and report consistency checks that flag conflicts across the package.
- Evidence traceability that ties each finding back to a specific page or sheet.
- A workflow board for tracking review-support items.
- A draft reviewer handoff package assembled from reviewer-selected records.
- A guided demo over the Brookside Meadows sample project, using seeded demo data
  plus CAD review findings produced by really parsing a bundled sample DXF file.

## Implementation reality (current capability wording)

This is the canonical, code-checked statement of what is and is not implemented.
Use this wording in public copy so the roadmap and positioning do not drift apart.

- Real DXF parsing: yes. The backend parses DXF files with ezdxf and extracts
  layers, entities, blocks, text, and reference candidates. This is metadata
  extraction, not geometry validation or compliance certification.
- Real PDF indexing: yes, text-layer only. pypdf extracts embedded page text
  where it exists. There is no OCR, so scanned-image pages are not read.
- OCR: not currently included.
- DWG parsing: not supported. Uploads are limited to the .dxf extension.
- GIS integration and georeferencing: not supported. DXF bounds are treated as
  local drawing coordinates, not georeferenced data.
- Computer vision and vector search: not included.
- Live AI calls: disabled by default. The default provider is a deterministic
  mock; live calls require an explicit provider, an enable flag, and a key.
- Brookside Meadows review findings and project records are seeded demo data and
  are not presented as extracted from a real submission. The bundled sample DXF
  is the exception that is actually parsed, and its CAD findings come from that
  real parse.

## What the product does not claim

The product does not approve plans, certify compliance, stamp drawings, verify,
validate, or make final engineering decisions. It does not guarantee compliance,
declare a project safe, promise passing review, or guarantee first-pass
acceptance. The human reviewer remains responsible for every item, and source
context stays visible so the reviewer can check the basis for each finding.

Seeded demo data is labeled as seeded review-support demo data, and seeded
records are not presented as extracted from a real submission. The bundled
sample DXF file is the exception: it is really parsed with ezdxf, so the CAD
intake surface shows findings produced from that file rather than from seed data.

## Demo flow

Brookside Meadows is the sample project. The public guided demo at `/guided-demo`
is the front door: a no-login, self-running pre-submittal QA product tour reached
from the homepage primary CTA ("Run the sample review"). It walks a focused
civil/AEC story over five steps, each linking to the real Brookside Meadows
surface:

1. CAD / DXF intake: `/projects/proj_brookside_meadows/cad`
2. Plan and report consistency: `/projects/proj_brookside_meadows/plan-consistency`
3. Evidence traceability: `/projects/proj_brookside_meadows/traceability`
4. Workflow board: `/projects/proj_brookside_meadows/workflow-board`
5. Draft reviewer handoff: `/projects/proj_brookside_meadows/review-packets`

The demo opens with a fixture-backed proof band (CAD findings, plan consistency
findings, traceability rows, workflow items, and review packet items counted from
the seeded demo data, falling back to qualitative cards when a count is not
available) and ends with next-step CTAs to the full demo project and the command
center (`/projects/proj_brookside_meadows/command-center`). The boundary statement
is present as reassurance below the tour, not as the lead message. The focused
demo steps live in `aecDemoSteps` and the demo project id is centralized as
`BROOKSIDE_PROJECT_ID`, both in `lib/demoJourney.ts`. The older twelve-step
reviewer journey (`demoJourneySteps`) still powers the `/start-here` overview.

## Demo analytics

The guided demo uses a local, no-op analytics helper in `lib/analytics.ts`. It
tracks `demo_started`, `demo_step_viewed`, `demo_completed`, `demo_cta_clicked`,
and `pilot_cta_clicked`. It loads no third-party package and sends no data to any
external service; in development it logs events to the console and in production
it is a no-op. Only non-sensitive demo-shape properties are passed (step index,
step id, CTA label, sample project id). No user data, file content, or secrets are
captured. Future work: route these stable event names through a real analytics
sink behind an explicit opt-in.

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
- DXF parsing (ezdxf) and PDF text-layer indexing (pypdf) are implemented; DWG
  parsing, GIS integration, OCR, computer vision, and vector search are not.
- No full authentication lifecycle (no team invitations or password reset),
  billing, or production database provider in this phase.
- Demo content is seeded review-support data, except the bundled sample DXF that
  is really parsed; seeded records are not a real submission.
- The product is review support only and does not make final engineering decisions.
