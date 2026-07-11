# Civil Engineer AI Guide

The guide is a deterministic local project expert mounted on the site. It
answers questions about this repository: the product, the Brookside Meadows
demo, the architecture, security, testing, what is real versus seeded, and
where things live in the code.

## What it is

- A deterministic local retrieval system over an allowlisted knowledge
  catalog (lib/guide/knowledge.ts) plus generated repository facts
  (lib/guide/generated/repo-facts.json).
- Private to the browser: questions are never sent anywhere, there is no
  telemetry, no logging of question text, no outside inference API, no model
  download, and no embedding service.
- Extractive and template-based: answers are composed from curated entries
  and always identify their repository sources.

## What it is not

- Not a language model and not a general-purpose chatbot.
- It does not read the live repository at runtime; its knowledge is a build
  snapshot recorded with the generating commit.
- It has no access to tenant data and cannot perform engineering analysis or
  give engineering advice.

## Architecture

| Concern | Location |
| --- | --- |
| Presentation, interaction, accessibility | components/CivilEngineerAIGuide.tsx |
| Types | lib/guide/types.ts |
| Normalization (tokens, stemming, synonyms, typo tolerance) | lib/guide/normalize.ts |
| Safety classification | lib/guide/safety.ts |
| Retrieval and ranking | lib/guide/search.ts |
| Answer composition and follow-ups | lib/guide/answerComposer.ts |
| Route awareness | lib/guide/routeContext.ts |
| Curated knowledge catalog | lib/guide/knowledge.ts |
| Generated repository facts | lib/guide/generated/repo-facts.json |
| Source link building (commit-pinned) | lib/guide/sourceLinks.ts |
| Facts generator | scripts/generate-guide-knowledge.mjs |
| Freshness gate | scripts/check-guide-knowledge.mjs |
| Evaluation corpus (100+ questions) | lib/guide/evaluation/corpus.ts |
| Evaluation suite | lib/guide/__tests__/evaluation.test.ts |

The retrieval engine is lazy-loaded when the panel first opens, keeping the
knowledge catalog out of the initial page bundle.

## Search ranking

Token-aware scoring, not substring matching: queries are tokenized, stopwords
dropped, synonyms expanded, and lightly stemmed. Each knowledge entry is
indexed with field weights (title and key phrases highest), an
inverse-document-frequency weight per token with term-frequency saturation,
and exact-phrase boosts. Tokens of five or more characters tolerate one edit
for typos. The current route boosts contextually tagged entries, and the
conversation's previous answers boost related entries. Substring collisions
such as "author" matching "authorization" cannot occur.

## Confidence behavior

- High: strong score with a clear margin; the guide answers directly with
  sources.
- Medium: the guide labels the closest matching topic and answers cautiously.
- Low: the guide states that it could not locate enough public project
  information, offers two or three likely topics, and never fabricates a
  repository path. No numeric confidence percentages are shown.

## Safety classification

Safety runs before answering and classifies intent rather than blocking
nouns. Requests for an engineering decision (adequacy, sizing, code
compliance, permitting outcome, safety determination, approval, construction
advice) are refused with the professional-boundary response. Repository
questions that merely name basins, permits, or compliance (where a feature is
implemented, what tests enforce the wording boundary, what the demo
represents) are answered. The critical decision set in the evaluation corpus
must classify at 100 percent.

## Page awareness and follow-ups

The guide knows the current route: questions such as "what am I looking at"
answer from the route map with the page's purpose, workflow stage, data
source (public demo versus authenticated), and next steps. Short follow-ups
("how does that work", "where is it implemented", "is that real or seeded",
"what tests cover it") resolve against the previous answer. Context lives in
component state only; nothing persists across sessions or devices.

## Freshness gate

npm run check:guide (also in CI) fails when a referenced repository path no
longer exists, a route link no longer resolves, the generated facts are stale
against package.json and the route tree, or a retired claim reappears (for
example the old statement that the frontend falls back to seeded data when
the backend is unreachable, which the application removed). The generated
index records the generating commit; the guide presents its knowledge as a
build snapshot, never a live feed.

## Evaluation

The corpus in lib/guide/evaluation/corpus.ts holds 100+ cases: exact
questions, paraphrases, short and long forms, typos, acronyms, negation,
multi-topic questions, unknown questions, route-context questions, follow-ups,
and adversarial safety wording. CI enforces: at least 95 percent correct
top-topic retrieval, 100 percent correct classification on the critical
engineering-decision set, no unsupported repository-path citations, and
low-confidence behavior on unknown questions.

## Known limitations

- Knowledge is curated: topics outside the catalog get an honest
  low-confidence response rather than an answer.
- Follow-up resolution uses the most recent answer only.
- The knowledge snapshot updates at build time, not continuously.
