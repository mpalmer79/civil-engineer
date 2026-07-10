# Phase 4: AI Review Assistant

> Historical record. This document describes a completed build phase and is
> not current implementation guidance. See docs/README.md for the current
> documentation index.

**Product:** Civil Engineer AI: Stormwater Review Assistant
**Phase:** 4, AI Review Assistant

Phase 3 added the document evidence and retrieval foundation. Phase 4 adds the
first controlled AI review workflow. It uses retrieved source evidence,
structured prompts, JSON output validation, prohibited-word safety checks, audit
events, and mandatory human review.

Civil Engineer AI is a review-support and evidence-organization system. The AI
Review Assistant produces draft review-support findings, not final engineering
conclusions. It does not approve plans, certify compliance, stamp drawings,
replace a licensed Professional Engineer, or make final safety determinations.

## What Phase 4 adds

- A backend AI review service that runs a constrained, evidence-first workflow.
- A provider abstraction with a deterministic mock provider (default) and an
  optional, disabled-by-default live provider.
- Environment-based AI configuration.
- Structured prompts built from retrieved evidence only.
- A strict Pydantic output schema for AI draft findings.
- Validation and safety checks before any output is saved.
- Audit events for every step of an AI review run.
- New tables: `ai_review_runs` and `ai_draft_findings`.
- API endpoints to run and read AI reviews and draft findings.
- An AI Review page in the frontend.
- Tests proving validation, safety checks, audit events, and mock behavior.

It also completes five mini cleanup items from the Phase 3 review (README
fallback wording, the retrieval score label, the models docstring, attribution
suppression confirmation, and a stale-name and dash sweep).

## Why the AI assistant is constrained

A review-support system must not behave like a general chatbot. The assistant
never reviews documents from memory. It only reasons over evidence that the
retrieval layer surfaced for a specific checklist item, it must cite the chunk
ids it used, and its output is validated before it is stored. This keeps the
workflow inspectable, keeps the human reviewer in control, and keeps the
professional boundary intact.

## How retrieval feeds prompts

For each checklist item the service:

1. Loads the checklist item.
2. Retrieves source evidence chunks for that item (Phase 3 retrieval).
3. Builds a constrained prompt containing the checklist item and only the
   retrieved evidence.
4. Calls the provider with that prompt.

The prompt (see `backend/app/ai/prompts.py`) frames the model as review-support
only, forbids outside knowledge and final decisions, lists the prohibited
words, and requires the model to cite chunk ids and to mark uncertainty.

## How JSON schema validation works

The provider returns a raw JSON object. Before anything is saved, the service
validates it against `AIDraftFindingOutput` (see `backend/app/ai/schemas.py`):

- `finding_type` must be one of the allowed, non-approval types.
- `risk_level` must be low, medium, or high.
- `confidence` must be between 0 and 1.
- `requires_human_review` must be true.
- `safety_boundary_acknowledged` must be true.
- `source_chunk_ids` must be present.

## How prohibited-word safety checks work

After schema validation, `backend/app/ai/validators.py` runs safety checks:

- No prohibited final-decision wording (approved, certified, fully compliant,
  safe, engineer-confirmed, passes review, meets all requirements) in the title,
  summary, recommended action, or finding type.
- `source_chunk_ids` must be non-empty and must all reference chunks that were
  actually retrieved for that checklist item.
- The title, summary, and recommended action must be non-empty.

If validation or safety checks fail, the output is not presented as a valid
draft finding. The failure and its details are stored on the draft record and
written to the audit log. Failures are never hidden.

## Why every draft finding requires human review

Draft findings are saved with status `requires_human_review`. The schema
requires `requires_human_review` to be true, and the UI labels every draft as
requiring human reviewer action. The AI does not make final engineering
decisions; a human reviewer evaluates each draft against the cited evidence.

## How the mock provider works

The default provider is a deterministic mock (`backend/app/ai/mock_provider.py`).
It returns fixed, schema-valid draft findings for the checklist items tied to
the Brookside Meadows planted issues, and it cites the chunk ids from the
retrieved evidence so source citations are always valid. It makes no external
calls and generates no random content, so the demo and tests are stable. A mock
run produces ten draft findings:

1. Design storm assumption may conflict with the town standard
2. Infiltration testing evidence not found
3. Groundwater separation for infiltration not addressed
4. Downstream culvert capacity discussion not found
5. Maintenance responsibility may be unclear
6. Erosion control sequencing may not be tied to phasing
7. Inspection corrective action not found
8. Open RFI on pipe material may be unresolved
9. Basin naming may be inconsistent across documents
10. Referenced revised grading sheet not found in the package

## Optional live provider configuration

A live provider is only used when it is fully configured. `get_provider` returns
the mock provider unless the provider is openai or anthropic, live calls are
enabled, and an API key is present. To enable a live OpenAI provider (optional):

```env
AI_PROVIDER=openai
AI_ENABLE_LIVE_CALLS=true
OPENAI_API_KEY=...        # never commit this
AI_MODEL=gpt-4o-mini
```

and install the optional package: `pip install openai`. The repo does not
require a paid API key to run, never commits keys, never exposes keys to the
frontend, and never logs secrets. If the live provider is unavailable or fails,
the service falls back to the mock provider. The Anthropic provider is left as a
documented connection point for a later step.

## Audit events written

Each AI review run writes audit events, with non-sensitive metadata (provider,
model name, prompt version, retrieved chunk ids, validation and safety status).
Secrets and API keys are never stored.

- `ai_review_run_started`
- `checklist_item_loaded`
- `evidence_retrieved`
- `prompt_built`
- `provider_called`
- `draft_finding_generated`
- `draft_finding_validation_passed`
- `draft_finding_validation_failed`
- `safety_check_passed`
- `safety_check_failed`
- `ai_review_run_completed`

## API endpoints

- `POST /api/v1/projects/{project_id}/ai-review-runs`
- `GET /api/v1/projects/{project_id}/ai-review-runs`
- `GET /api/v1/ai-review-runs/{review_run_id}`
- `GET /api/v1/ai-review-runs/{review_run_id}/draft-findings`
- `GET /api/v1/projects/{project_id}/draft-findings`
- `GET /api/v1/draft-findings/{draft_finding_id}`
- `GET /api/v1/projects/{project_id}/ai-provider-mode`

All AI endpoints return safe labels (draft, requires_human_review,
validation_passed, validation_failed, safety_check_passed, safety_check_failed).
None return final-decision labels.

## Evaluation metrics for Phase 4

The AI review workflow tracks the following measurable signals on each run,
which a Phase 5 evaluation harness can score against expected findings:

- Draft finding schema validity (validation_passed rate)
- Source chunk citation validity (cited ids that reference retrieved chunks)
- Prohibited wording count (target zero)
- Human review requirement rate (target 100 percent)
- Validation failure count and safety check failure count
- Expected finding match rate (draft findings vs. the seeded planted issues)
- Unsupported claim count (drafts without valid citations)

## What remains out of scope

- Live AI calls are disabled by default; the demo runs on the mock provider.
- Embeddings, semantic retrieval, and a vector store.
- Authentication, deployment, and CAD or real document upload.
- Final compliance decisions or automated plan approval.
- Persisted human review actions on draft findings (the human review queue
  workflow is a candidate for a later phase).

## What Phase 5 should build next

- A live evaluation harness that runs the AI review against the seeded fixture
  and scores the metrics above, including expected finding match rate.
- A human review queue that records accept, edit, reject, and escalate actions
  on draft findings.
- Optional embedding-based retrieval behind the existing retrieval interface.
- Optional live provider runs measured by the evaluation harness.
