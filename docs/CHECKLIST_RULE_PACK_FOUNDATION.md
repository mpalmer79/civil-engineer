# Checklist Rule Pack Foundation

This document describes the reusable rule pack and checklist-driven review
foundation added in Production Foundations Sprint 4.

Everything here is review-support only. A rule pack is a reusable review-support
template, not a legal ordinance, not a compliance standard, and not a binding
requirement set. Checklist status is review-support only. The system never
decides that a project satisfies a requirement, is compliant, or is approved; a
reviewer decides, item by item.

## Rule-pack concept

A rule pack is a reusable, versioned checklist template. It groups stormwater
review requirements into categories and, for each requirement, records the
evidence a reviewer would expect to find. A rule pack can be applied to many
projects. The seeded "Brookside Stormwater Review Starter Pack" is a starter
template labeled "Starter template, not ordinance." A rule pack carries a source
mode (`seeded_demo`, `user_created`, or `imported_template`) and a version label
so future versions can coexist.

## Jurisdiction checklist concept

A rule pack names a jurisdiction for organization, but it does not encode that
jurisdiction's legal ordinance. The starter pack uses "Starter template (no
jurisdiction)." Real jurisdiction-specific ordinance encoding is future work and
is intentionally out of scope here. Nothing in a rule pack is a legal
determination.

## Checklist item structure

Each rule pack item has an item code, a category, a requirement text, the
expected evidence, an applicability note, a risk level, a review domain, and a
reference label. When a rule pack is applied to a project, each rule pack item is
copied into a project checklist item that adds reviewer-controlled status fields.

## Expected evidence

Expected evidence describes what a reviewer would look for to review a
requirement (for example, a detention basin stage storage table for the
detention and outlet control category). It is a review prompt, not a statement
that the evidence exists or is sufficient. The checklist evidence search uses the
expected evidence text as the default query against indexed PDF page text.

## Applicability

A reviewer decides whether each item applies to a project: applies, not
applicable by reviewer, applicability unclear, or needs reviewer confirmation.
The system never decides applicability. Marking an item not applicable by
reviewer is recorded with a dedicated audit event.

## Evidence status

A reviewer assigns an evidence status to each item: not reviewed, evidence found,
missing evidence, conflicting evidence, unclear evidence, extraction unavailable,
or needs reviewer confirmation. Evidence found records that a reviewer located
relevant evidence; it does not certify or validate the design. There is
intentionally no compliant, noncompliant, approved, verified, passed, or failed
value.

## Citation linkage

A reviewer can link evidence to a checklist item through a `ChecklistEvidenceLink`,
which references a document, an optional page, and optionally an evidence citation
or evidence candidate. When a draft finding is created from a checklist item with
a document reference, a page-level `EvidenceCitation` is created in checklist
context (`citation_context` = `checklist_evidence`) and tied to both the finding
and the checklist item.

## Reviewer notes

Each checklist item carries an optional reviewer note. Notes are validated against
final-decision language so the checklist stays within the review-support
boundary. Adding a note advances the item review status to reviewer note added
when no other status was set.

## Draft finding creation

A reviewer can create a draft finding from a checklist item. The finding is
created with `finding_origin` `checklist_review`, a safe draft
`human_review_status`, a reviewer-selected evidence status, and a link back to the
checklist item. The risk level is reviewer-entered, never a system conclusion.
The checklist item review status becomes draft finding created and records the
new finding id. The draft finding requires reviewer confirmation and never
finalizes an outcome.

## Audit events

Sprint 4 writes `project_checklist_created`, `checklist_item_status_updated`,
`checklist_item_note_added`, `checklist_item_marked_not_applicable_by_reviewer`,
`checklist_evidence_search_performed`, `checklist_evidence_linked`, and
`checklist_draft_finding_created`. Audit metadata records rule pack id, checklist
id, checklist item id, status changes, evidence candidate id, citation id,
finding id, and result counts only. It never records full extracted page text,
raw server file paths, secrets, or API keys.

## Limitations

- The starter rule pack is a review template, not a jurisdiction-adopted
  ordinance and not a compliance standard.
- Checklist status is review-support only and does not determine project
  outcome.
- There is no full jurisdiction rule engine and no legal compliance
  determination.
- Evidence search is deterministic keyword and phrase matching over indexed PDF
  page text only; there is no OCR and there are no embeddings.
- There are no live AI calls.
- There is no real authentication yet.
- Uploaded files remain local unless deployment storage is configured.

## Future jurisdiction-specific ordinance work

Later sprints may add jurisdiction-specific rule packs, rule pack versioning and
import, and richer applicability logic. Any such work must keep rule packs as
review-support templates, keep checklist status reviewer-controlled, and keep the
professional boundary: the system organizes review; a licensed Professional
Engineer remains responsible for engineering decisions.
