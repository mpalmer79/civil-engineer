# Comment Letter Template Boundary

The comment letter draft added in Production Foundations Sprint 8 is generated
from fixed, deterministic templates. This document records the boundary that keeps
the generated letter within review support.

## Deterministic template generation only

A comment letter draft is built by filling fixed template sections from the
package items. The same package always produces the same draft text. The template
includes a title, subject line, introduction, project summary, review scope, a
comment block built from the included package items, an optional resubmittal
summary, and a closing.

## No live AI calls

Generation uses string templates only. There are no live AI calls, no language
model requests, no OCR, and no external services. This is consistent with the
project-wide rule that live AI calls stay disabled by default.

## No legal or engineering conclusions

The generated text never states a legal or engineering conclusion. It does not say
a plan is approved, certified, compliant, noncompliant, safe, unsafe, verified, or
validated, and it does not say an issue is resolved or closed. Each comment is
framed as a review-support item the reviewer asks the applicant to address or
clarify.

## Reviewer-editable output

Every generated section is a reviewer-editable draft. The reviewer is responsible
for the final wording of any communication sent to an applicant. The generated
text is a starting point, not a finished letter.

## Fixed boundary statement

Every comment letter draft and preview renders this fixed boundary statement,
which is never an editable section:

"This draft is prepared for reviewer support. It does not approve plans, certify
compliance, verify design, validate CAD, declare safety, resolve issues, close
issues, or replace the judgment of a licensed Professional Engineer."

Because this statement intentionally describes what the draft does not do, it is a
system constant and is never run through the prohibited-language guard.

## Prohibited language

Reviewer-entered fields are checked against the prohibited-language guard. The
following final-outcome wording is rejected in reviewer-entered content: approved,
certified, compliant as a final outcome, noncompliant as a final outcome, safe,
unsafe, verified, passed review, failed review, validated, resolved, closed, PE
stamped, and final approval.

## Allowed review-support language

Allowed wording includes: response package, response package draft, comment letter
draft, reviewer editable draft, reviewer package, package assembled, package issued
for reviewer handoff, package ready for reviewer handoff, package revision, selected
matrix items, selected citations, applicant response summary, resubmittal summary,
carried forward for review, needs reviewer confirmation, requires human review,
review-support communication, reviewer note, package issuance record, issued by
reviewer, audit attributed, and access controlled.

## Audit and revision handling

Comment letter generation and edits write audit events that record ids, statuses,
and counts only. Audit metadata never includes the full comment letter text, full
applicant response text, full extracted page text, storage keys, raw paths,
tokens, or secrets. When a package revision begins, prior issued or ready drafts
are marked superseded rather than deleted, so the prior draft is preserved.
