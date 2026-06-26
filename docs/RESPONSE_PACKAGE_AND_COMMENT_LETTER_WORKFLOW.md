# Response Package and Comment Letter Workflow

The response package and comment letter workflow is the reviewer-controlled output
layer added in Production Foundations Sprint 8. It lets a reviewer assemble
selected review-support records into a controlled communication artifact and a
deterministic comment letter draft.

A response package is a reviewer communication artifact. Issuing a package records
that a reviewer issued a communication. It does not approve a project, certify
compliance, verify CAD, validate design, declare safety, resolve an issue, or
close an issue.

## Response package concept

A response package collects reviewer-selected records for a single project and
tracks them from draft, through reviewer handoff, to issuance, with a preserved
revision history. The package is named, typed, numbered, and versioned. It can
reference a response matrix and a resubmittal round.

## Selected source records

Package items are created from reviewer-selected records. Each item stores the
source type and source id, a reviewer comment, an optional category, optional
requested evidence, an optional applicant response summary, an optional reviewer
follow-up note, and an optional citation reference. Adding a record never modifies
the source record.

Supported source types:

- `finding`: a reviewer finding.
- `checklist_item`: a project checklist review item.
- `response_matrix_item`: a response matrix item.
- `citation`: a reviewer-selected evidence citation (recorded as a page or section
  reference, never full extracted page text).
- `document_reference`: a document reference.
- `resubmittal_summary`: a resubmittal round summary.
- `manual_reviewer_note`: a reviewer-entered note.

## Matrix item inclusion

A reviewer can add response matrix items to a package from the response matrix
detail page or a single matrix item from the matrix item detail page. Each matrix
item carries its reviewer comment, applicant response summary, and reviewer
follow-up status into the package item.

## Citation inclusion

A reviewer can add evidence citations to a package. The package item records a
short citation reference (page label and section) for the comment letter. It never
includes full extracted page text, raw storage paths, or storage keys.

## Applicant response summary

When a package item is created from a response matrix item, the recorded applicant
response is carried into the package item as an applicant response summary for the
reviewer to include or edit. It is reviewer communication content, not proof.

## Resubmittal summary

When a package references a resubmittal round, the comment letter draft includes a
short resubmittal summary noting that carried-forward items remain under reviewer
review across rounds.

## Comment letter sections

A generated comment letter draft has these sections: title, subject line,
introduction, project summary, review scope, review-support comments (built from
the included package items), an optional resubmittal summary, and a closing. A
fixed review-support boundary statement is rendered with every draft and preview
and is never an editable section.

## Reviewer edits

Every comment letter section is reviewer-editable. Each reviewer-entered field is
checked against the prohibited-language guard, so a reviewer cannot save
final-decision wording (for example, approved, certified, or compliant as a final
outcome).

## Package preview

The package preview returns safe, structured data: package metadata, the boundary
statement, and the included items with their reviewer comments, requested
evidence, applicant response summaries, and citation references. The preview never
includes raw paths, storage keys, signed URLs, tokens, or secrets.

## Issuance record

Issuing a package sets its status to issued by reviewer and records who issued it
and when. Issuance is a communication record only. It does not approve a project,
certify compliance, validate design, resolve an issue, or close an issue.

## Revision history

Starting a revision increments the revision number, sets the package status to
revision started, records a revision row capturing the prior status, and marks
prior issued comment letter drafts as superseded. The prior issued record is
preserved, not overwritten.

## Limitations

- Comment letter drafts are deterministic templates only. There are no live AI
  calls.
- This is not a final approval workflow, a legal compliance determination, or an
  engineering validation.
- There is no applicant-facing portal. Applicant response summaries are
  reviewer-entered content.

See [API_RESPONSE_PACKAGES.md](API_RESPONSE_PACKAGES.md) for the endpoints and
[COMMENT_LETTER_TEMPLATE_BOUNDARY.md](COMMENT_LETTER_TEMPLATE_BOUNDARY.md) for the
template boundary.
