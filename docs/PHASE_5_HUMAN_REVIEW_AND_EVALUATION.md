# Phase 5: Human Review Queue and Evaluation Scoring

**Product:** Civil Engineer AI: Stormwater Review Assistant
**Fixture:** Brookside Meadows

Phase 4 added the controlled AI Review Assistant: an evidence-first workflow that
generates validated draft review-support findings. Phase 5 adds the next layer of
the review lifecycle: persisted human review actions and heuristic evaluation
scoring against the expected Brookside Meadows findings.

Phase 5 makes the product feel like a complete AI-assisted review workflow rather
than a draft generator. The full loop is now:

1. Evidence is retrieved.
2. AI draft findings are generated.
3. Draft findings are validated and safety checked.
4. Draft findings require human review.
5. A reviewer accepts, edits, rejects, escalates, marks unclear, or requests more
   information.
6. The system records the review action and applies a status transition.
7. Evaluation scoring compares draft findings against the expected planted
   issues.
8. Metrics expose recall, precision, citation validity, prohibited wording, and
   reviewer outcomes.
9. Audit events preserve the decision history.

## What Phase 5 adds

- A persisted `human_review_actions` table and review action history.
- A real Human Review Queue page at `/human-review`.
- Review action endpoints and review status transitions.
- Audit events for every human review action.
- A persisted `ai_evaluation_results` table and an `ai_evaluation_matches` table.
- An evaluation scoring service that compares draft findings against the seeded
  expected findings.
- Evaluation scoring endpoints and an updated Evaluation page that shows recall,
  precision, citation validity, prohibited wording, and validation and safety
  failure counts, with an explainable match table.
- Failed draft findings surfaced separately from valid drafts on both the AI
  Review page and the Human Review Queue.

## Why human review is required

Civil Engineer AI is a review-support and evidence-organization system. It does
not approve plans, certify compliance, stamp drawings, replace a Professional
Engineer, or make final safety determinations. An AI draft finding is a starting
point for a human reviewer, never a conclusion. Phase 5 enforces this by routing
every draft finding to a reviewer and recording the reviewer decision, so the
human stays in control of the outcome and the decision history is auditable.

## Human review action model

A human review action is stored in `human_review_actions` with these fields:

- `review_action_id`, `draft_finding_id`, `project_id`, `review_run_id`
- `reviewer_name`, `action`, `reviewer_note`
- `edited_title`, `edited_summary`, `edited_recommended_action`
- `previous_status`, `new_status`, `created_at`

### Allowed review actions

| Action | Resulting status |
| --- | --- |
| `accepted` | `accepted_by_reviewer` |
| `edited` | `edited_by_reviewer` |
| `rejected` | `rejected_by_reviewer` |
| `escalated` | `escalated` |
| `marked_unclear` | `marked_unclear` |
| `requested_more_information` | `requested_more_information` |

### Status transitions

A draft finding starts at `requires_human_review` (valid drafts) or
`validation_failed` (drafts that did not pass validation). A review action moves
the draft to the resulting status listed above. The rules are:

- Only valid draft findings (validation passed) can be accepted or edited.
- Failed draft findings can be rejected, escalated, marked unclear, or have more
  information requested, but never accepted or edited.
- Every action requires a reviewer name and a reviewer note.
- Edited text is checked for prohibited final-decision wording before it is
  saved. If prohibited wording is found, the edit is rejected and a safety
  failure is audited.
- An accepted or edited finding stays a review-support finding under human
  control. No action produces final engineering approval language.

### Why no action is called approve

The word "approve" implies a final engineering decision. Civil Engineer AI never
makes that decision. The strongest action a reviewer can take is `accepted`,
which means the reviewer accepts the draft as a review-support finding worth
acting on, not that the design is approved, certified, compliant, or safe. The
backend status vocabulary, the API, and the UI deliberately avoid the words
approved, certified, compliant, and safe as statuses or conclusions.

## How evaluation scoring works

Evaluation scoring compares an AI review run's draft findings against the seeded
expected findings for the project (the ten Brookside Meadows planted issues). It
is transparent and heuristic. It is a quality signal for human reviewers, not a
certification of the AI or the package, and it does not pretend to be
mathematically perfect.

The result is stored in `ai_evaluation_results` and the individual matches are
stored in `ai_evaluation_matches`.

### How draft findings are matched to expected findings

For each valid draft finding, the service looks for the best matching expected
finding that has not already been matched, in this priority order:

1. `related_checklist_match`: the draft's checklist item id is listed in the
   expected finding's related checklist items (confidence 0.95).
2. `exact_category_match`: the category of the draft's checklist item equals the
   expected finding's category (confidence 0.7).
3. `title_similarity_match`: the keyword overlap between the draft title and the
   expected title (Jaccard over non-stopword tokens) is at or above a small
   threshold (confidence equals the overlap).

Matching is one-to-one: each expected finding is matched by at most one draft,
and each draft matches at most one expected finding. Expected findings with no
match are recorded as `unmatched_expected`. Valid draft findings with no match
are recorded as `extra_draft`. Failed drafts are counted separately and never
match.

### How recall and precision are calculated

- Recall = matched findings divided by total expected findings.
- Precision = matched findings divided by total valid draft findings.

Both are reported as fractions between 0 and 1.

### How citation validity is checked

For each valid draft finding, the service confirms that it cites at least one
source chunk id and that every cited chunk id exists in the project's retrieved
evidence (the seeded document chunks). The citation validity rate is the fraction
of valid drafts that pass this check.

### How validation failures and safety failures are counted

- `validation_failure_count`: draft findings whose validation status is
  `validation_failed`.
- `safety_failure_count`: draft findings whose safety check status is
  `safety_check_failed`.
- `prohibited_word_count`: the total count of prohibited final-decision words
  found across the title, summary, and recommended action of all draft findings.

### Overall score

The overall score is a transparent weighted blend of the core signals:

```
overall_score = 0.4 * recall
              + 0.3 * precision
              + 0.2 * citation_validity_rate
              + 0.1 * (1 if prohibited_word_count == 0 else 0)
```

It is a heuristic summary for quick comparison, not a precise grade.

## Audit events

Every human review action and evaluation scoring run writes audit events with
non-sensitive metadata (project id, review run id, draft finding id, review
action id, evaluation result id, previous and new status, reviewer name,
validation and safety status, match counts, and a score summary). Secrets and API
keys are never logged.

Human review events:

- `human_review_action_started`
- `human_review_action_recorded`
- `draft_finding_status_updated`
- `edited_finding_safety_check_passed`
- `edited_finding_safety_check_failed`

Evaluation scoring events:

- `evaluation_scoring_started`
- `evaluation_match_created`
- `evaluation_scoring_completed`
- `evaluation_scoring_failed`

## Endpoints

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

No endpoint is named approve.

## What remains out of scope

Phase 5 does not add authentication, deployment work, CAD parsing, real document
upload, embeddings, vector search, or final engineering decision logic. Live AI
calls remain disabled by default, and the mock provider is the default, so the
project runs and tests pass without any API key. Only OpenAI has a real live
provider implementation; the Anthropic placeholder was removed from the
live-ready provider logic so the repo does not imply a provider works when it
does not.

## What Phase 6 should build next

Phase 6 begins the expansion modules described in the roadmap. Good next steps
that build on the Phase 5 foundation:

- Reviewer dashboards and reviewer-disagreement tracking across runs.
- Trend tracking of recall, precision, and citation validity across review runs.
- Prompt regression testing tied to the evaluation scoring service.
- Additional review domains (grading, utilities, roadway) that reuse the same
  checklist, retrieval, review, and evaluation backbone.
