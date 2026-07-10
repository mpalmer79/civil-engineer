# Phase 5: Human Review Queue and Evaluation Scoring

> Historical record. This document describes a completed build phase and is
> not current implementation guidance. See docs/README.md for the current
> documentation index.

**Product:** Civil Engineer AI: Stormwater Review Assistant
**Demo fixture:** Brookside Meadows

Phase 4 added the controlled AI Review Assistant: for each checklist item the
backend retrieves source evidence, builds a constrained prompt, validates the
structured output, runs safety checks, and saves a draft review-support finding
that requires human review. Phase 5 adds the next layer of the review lifecycle:
persisted human review actions and evaluation scoring against the expected
Brookside Meadows findings.

This document explains what Phase 5 adds, why human review is required, the
human review action model, how evaluation scoring works, what audit events are
written, and what remains out of scope.

## What Phase 5 adds

- A persisted human review queue for AI draft findings.
- Reviewer actions: accept, edit, reject, escalate, mark unclear, or request
  more information.
- Draft finding status transitions driven by reviewer actions.
- Audit events for every human review action.
- Evaluation scoring that compares AI draft findings against the expected
  findings and stores the result.
- Recall, precision, citation validity rate, human review required rate,
  prohibited word count, validation failure count, and safety failure count.
- Optional per-finding evaluation match records.
- A Human Review page, an updated AI Review page (failed drafts shown
  separately, with an evaluation prompt), and an updated Evaluation dashboard.

## Why human review is required

Civil Engineer AI is a review-support and evidence-organization system. It does
not approve plans, certify compliance, stamp drawings, replace a licensed
Professional Engineer, or make final safety determinations. The AI produces
draft findings only. Those drafts are not conclusions: a human reviewer must
decide what to do with each one. Phase 5 makes that step explicit and
persistent, so the system manages a full review lifecycle rather than just
generating drafts.

## Human review action model

A human review action is stored in the `human_review_actions` table. Each record
captures:

- `review_action_id`, `draft_finding_id`, `project_id`, `review_run_id`
- `reviewer_name`, `action`, `reviewer_note`
- `edited_title`, `edited_summary`, `edited_recommended_action` (used for edits)
- `previous_status`, `new_status`
- `created_at`

### Allowed review actions

- `accepted`
- `edited`
- `rejected`
- `escalated`
- `marked_unclear`
- `requested_more_information`

### Status transitions

Each action maps to a resulting draft finding status:

| Action                       | Resulting status              |
| ---------------------------- | ----------------------------- |
| `accepted`                   | `accepted_by_reviewer`        |
| `edited`                     | `edited_by_reviewer`          |
| `rejected`                   | `rejected_by_reviewer`        |
| `escalated`                  | `escalated`                   |
| `marked_unclear`             | `marked_unclear`              |
| `requested_more_information` | `requested_more_information`  |

A draft finding starts at `requires_human_review` (or `validation_failed` for a
failed draft) and moves to one of these review-support statuses.

### Rules enforced

- Only valid draft findings (validation passed) can be accepted or edited.
- Failed draft findings can be rejected, escalated, or marked unclear, but never
  accepted or edited. They are not usable as review findings until regenerated.
- Every action requires a reviewer note.
- Edited text must still pass the prohibited-word safety check. An edit that
  introduces final-decision wording is rejected and no edit is applied.
- Edited findings remain review-support findings under human control.
- No action creates final engineering approval wording.

### Why no action is called approve

The professional boundary is enforced in the action vocabulary itself. There is
no `approve` action, no `certify` action, and no status such as `approved`,
`certified`, `fully compliant`, or `safe`. Accepting a draft finding means a
reviewer accepts it as a review-support finding worth carrying forward, not that
the project or design is approved.

## How evaluation scoring works

Evaluation scoring compares the draft findings from one AI review run against the
expected Brookside Meadows findings (the ten planted review issues). The result
is stored in `ai_evaluation_results`, with optional per-item rows in
`ai_evaluation_matches`. Scoring is heuristic and explainable, not a
mathematically perfect measure.

### How draft findings are matched to expected findings

For each expected finding, the service tries these strategies in order and stops
at the first match:

1. **Related checklist match** (`related_checklist_match`): the draft finding's
   checklist item is one of the expected finding's related checklist items. This
   is effectively the planted-issue mapping and is the strongest signal.
2. **Category match** (`exact_category_match`): the draft finding's checklist
   category equals the expected finding's category.
3. **Title similarity match** (`title_similarity_match`): the token overlap
   (Jaccard) between the draft and expected titles is at or above a conservative
   threshold.

Each match is one-to-one: a draft finding is used for at most one expected
finding. Expected findings with no match are recorded as `unmatched_expected`.
Valid draft findings that match no expected finding are recorded as
`extra_draft`.

### How recall and precision are calculated

- `recall = matched_findings_count / expected_findings_count`
- `precision = matched_findings_count / draft_findings_count`

where `draft_findings_count` is the number of valid draft findings in the run.
Recall measures how many expected findings were surfaced. Precision measures how
many valid drafts corresponded to an expected finding.

### How citation validity is checked

For each valid draft finding, the service checks that the draft cites at least
one source chunk and that every cited chunk id exists in the project's retrieved
chunks. The `citation_validity_rate` is the fraction of valid drafts that pass
this check. Because Phase 4 validation already enforces citation integrity, this
rate is normally high, and the metric confirms it on the stored data.

### How validation failures and safety failures are counted

- `validation_failure_count`: draft findings in the run with
  `validation_status` of `validation_failed`.
- `safety_failure_count`: draft findings with `safety_check_status` of
  `safety_check_failed`.
- `prohibited_word_count`: draft findings whose title, summary, or recommended
  action contains prohibited final-decision wording (target zero).

Failed drafts are counted separately and are never treated as valid findings.

### Overall score

The overall score is a transparent weighted blend:

```
overall_score = 0.4 * recall
              + 0.3 * precision
              + 0.2 * citation_validity_rate
              + 0.1 * human_review_required_rate
```

It is a heuristic review-support signal, not a certification of the AI output.

## Audit events

Every human review action and every evaluation scoring run writes audit events.

Human review:

- `human_review_action_started`
- `human_review_action_recorded`
- `draft_finding_status_updated`
- `edited_finding_safety_check_passed`
- `edited_finding_safety_check_failed`

Evaluation scoring:

- `evaluation_scoring_started`
- `evaluation_match_created`
- `evaluation_scoring_completed`
- `evaluation_scoring_failed`

Audit metadata includes, where applicable: `project_id`, `review_run_id`,
`draft_finding_id`, `review_action_id`, `evaluation_result_id`,
`previous_status`, `new_status`, `reviewer_name`, validation and safety status,
match counts, and a score summary. Secrets are never logged.

## Backend endpoints

Human review:

- `GET /api/v1/projects/{project_id}/human-review-queue`
- `POST /api/v1/draft-findings/{draft_finding_id}/review-actions`
- `GET /api/v1/draft-findings/{draft_finding_id}/review-actions`
- `GET /api/v1/projects/{project_id}/review-actions`

Evaluation scoring:

- `POST /api/v1/ai-review-runs/{review_run_id}/evaluate`
- `GET /api/v1/ai-review-runs/{review_run_id}/evaluation`
- `GET /api/v1/projects/{project_id}/ai-evaluation-results`
- `GET /api/v1/ai-evaluation-results/{evaluation_result_id}`

No endpoint is called approve, and no endpoint returns a final-decision label.

## What remains out of scope

Phase 5 does not add authentication, deployment work, CAD parsing, real document
upload, embeddings, vector search, or final engineering decision logic. The mock
provider remains the default and live AI calls stay disabled, so the project runs
without any API key.

## What Phase 6 should build next

Phase 6 begins the expansion modules described in the roadmap. The same
retrieval, checklist, findings, human review, audit, and evaluation backbone is
reused to grow from a stormwater assistant into a broader land development review
platform (for example grading, utility coordination, and roadway layout review),
mostly by adding checklist content, document types, and evaluation cases rather
than new infrastructure.
