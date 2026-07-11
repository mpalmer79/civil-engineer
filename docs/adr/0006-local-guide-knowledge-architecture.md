# ADR 0006: Local guide knowledge and retrieval architecture

Status: Accepted

## Context

The Civil Engineer AI Guide was a single client component holding seven
static topics, substring keyword matching, and a noun-based safety filter. It
blocked legitimate repository questions containing words like basin or
permit, carried a stale claim that the frontend falls back to seeded data,
and could not answer page-context or follow-up questions. It also could not
be evaluated: there was no corpus, no freshness check, and no separation
between knowledge and presentation.

## Decision

1. Knowledge lives outside the component in `lib/guide`: a curated,
   allowlisted catalog of public project information plus generated
   repository facts (dependency versions, route list, ADR titles, commit
   identifier) produced by a deterministic build script. No secrets, tenant
   data, or raw source files are indexed.
2. Retrieval is deterministic and local: token-aware BM25-style ranking with
   field weights, synonym expansion, light stemming, bounded typo tolerance,
   phrase boosts, route-context boosts, and conversation boosts. No browser
   model, no model download, no remote inference, no telemetry; questions
   never leave the browser.
3. Safety classifies intent, not nouns: engineering-decision requests are
   refused; repository questions that name technical safety nouns are
   answered. The critical decision set must classify at 100 percent in CI.
4. Answers are composed, not generated: one entry's direct answer, detail,
   limitation, links, repository sources, and related topics. Every factual
   technical answer cites sources, linked to the generating commit.
5. Freshness is enforced: CI fails when referenced paths or routes stop
   existing, generated facts go stale, or a retired claim reappears.
6. Accuracy is enforced: a 100+ question evaluation corpus gates retrieval at
   95 percent top-topic accuracy and safety at 100 percent on critical cases.

## Consequences

- The guide is honest by construction: it can only say what the catalog
  supports, and CI catches drift between the catalog and the repository.
- Intelligence comes from structure (fields, synonyms, context, follow-up
  intents), not from a model, so behavior is reproducible and testable.
- Extending the guide means adding catalog entries and corpus cases, both of
  which are validated automatically.
