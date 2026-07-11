// Deterministic answer composition. An answer combines at most one entry's
// direct answer, its supporting detail, one limitation, links, repository
// sources, and related questions. Nothing is synthesized beyond the curated
// catalog and the generated repository facts, and every technical answer
// carries its sources.

import { KNOWLEDGE_BY_ID } from "./knowledge";
import { isPageContextQuestion, routeInfoFor } from "./routeContext";
import { classifySafety } from "./safety";
import { search } from "./search";
import type { GuideAnswer, GuideContext, KnowledgeEntry } from "./types";

const LOW_CONFIDENCE_MESSAGE =
  "I could not locate enough public project information to answer that reliably. I only know this repository's documented, public material. These topics might be close:";

// Follow-up intents that reshape the answer over the previous entry.
type FollowUpIntent = "implementation" | "tests" | "real_or_seeded" | "detail" | "limitations";

const FOLLOW_UP_PATTERNS: { intent: FollowUpIntent; pattern: RegExp }[] = [
  { intent: "implementation", pattern: /\bwhere is (it|that|this) (implemented|defined|built)\b/ },
  { intent: "implementation", pattern: /\bwhich files?\b/ },
  { intent: "tests", pattern: /\bwhat tests? (cover|enforce|check|guard)s? (it|that|this)?\b/ },
  { intent: "real_or_seeded", pattern: /\bis (that|it|this) real or seeded\b/ },
  { intent: "real_or_seeded", pattern: /\bis (that|it|this) (real|seeded|mocked|fake)\b/ },
  { intent: "detail", pattern: /\bhow does (that|it|this) work\b/ },
  { intent: "detail", pattern: /\btell me more\b/ },
  { intent: "detail", pattern: /\bwhat happens after (that|this)\b/ },
  { intent: "limitations", pattern: /\bwhat are (its|the) limitations\b/ },
  { intent: "limitations", pattern: /\bwhy was (that|this) (design )?chosen\b/ },
];

function detectFollowUp(question: string): FollowUpIntent | null {
  const text = question.toLowerCase().replace(/[^a-z0-9 ]+/g, " ").replace(/\s+/g, " ");
  for (const { intent, pattern } of FOLLOW_UP_PATTERNS) {
    if (pattern.test(text)) return intent;
  }
  return null;
}

function relatedOf(entry: KnowledgeEntry): { id: string; title: string }[] {
  return (entry.related ?? [])
    .map((id) => KNOWLEDGE_BY_ID.get(id))
    .filter((e): e is KnowledgeEntry => Boolean(e))
    .slice(0, 3)
    .map((e) => ({ id: e.id, title: e.title }));
}

function groundedAnswer(
  entry: KnowledgeEntry,
  confidence: "high" | "medium",
  blocks: string[],
): GuideAnswer {
  return {
    kind: "grounded",
    confidence,
    entry,
    blocks,
    links: entry.links ?? [],
    sources: entry.sources ?? [],
    related: relatedOf(entry),
  };
}

function followUpAnswer(entry: KnowledgeEntry, intent: FollowUpIntent): GuideAnswer {
  const blocks: string[] = [];
  if (intent === "implementation") {
    const paths = entry.implementation ?? entry.sources ?? [];
    blocks.push(
      paths.length > 0
        ? `${entry.title}: the relevant repository paths are listed below.`
        : `${entry.title}: I do not have specific implementation paths cataloged for this topic.`,
    );
    return {
      kind: "grounded",
      confidence: "high",
      entry,
      blocks,
      links: entry.links ?? [],
      sources: paths,
      related: relatedOf(entry),
    };
  }
  if (intent === "tests") {
    const tests = entry.tests ?? [];
    blocks.push(
      tests.length > 0
        ? `${entry.title}: the covering test locations are listed below.`
        : `${entry.title}: I do not have specific test paths cataloged for this topic, but the CI gates in .github/workflows/ci.yml run the full suites.`,
    );
    return {
      kind: "grounded",
      confidence: "high",
      entry,
      blocks,
      links: entry.links ?? [],
      sources: tests.length > 0 ? tests : entry.sources ?? [],
      related: relatedOf(entry),
    };
  }
  if (intent === "real_or_seeded") {
    blocks.push(
      entry.realOrSeeded ??
        "This capability is a real implemented code path; only the Brookside Meadows content itself is seeded and labeled.",
    );
    return groundedAnswer(entry, "high", blocks);
  }
  if (intent === "limitations") {
    blocks.push(
      entry.limitation ??
        "The general boundary applies: review support only, no engineering decisions, live AI off by default.",
    );
    return groundedAnswer(entry, "high", blocks);
  }
  // detail
  blocks.push(entry.shortAnswer, ...(entry.detail ?? []));
  if (entry.limitation) blocks.push(entry.limitation);
  return groundedAnswer(entry, "high", blocks);
}

export function answerQuestion(question: string, context: GuideContext): GuideAnswer {
  const safety = classifySafety(question);
  if (!safety.allowed) {
    return { kind: "safety", message: safety.message };
  }

  // Page-context questions answer from the route map.
  if (isPageContextQuestion(question)) {
    const info = routeInfoFor(context.route);
    if (info) {
      const blocks = [
        `${info.title}: ${info.description}`,
        info.stage ? `Workflow stage: ${info.stage}.` : "",
        info.dataSource === "public_demo"
          ? "This is a public demo surface rendering seeded Brookside Meadows data, labeled with a data-source notice."
          : info.dataSource === "authenticated"
            ? "This is an authenticated surface; its records come from the backend and failures render explicit states."
            : "This is a public informational page.",
        info.nextSteps ? `Next: ${info.nextSteps}` : "",
      ].filter(Boolean);
      return {
        kind: "page_context",
        blocks,
        links: info.links ?? [],
        sources: info.sources ?? [],
      };
    }
  }

  // Short follow-ups reshape the previous answer.
  const followUp = detectFollowUp(question);
  const lastIds = context.history.at(-1)?.answeredEntryIds ?? [];
  if (followUp && lastIds.length > 0) {
    const previous = KNOWLEDGE_BY_ID.get(lastIds[0]);
    if (previous) return followUpAnswer(previous, followUp);
  }

  const { ranked, confidence } = search(question, context);

  if (confidence === "low" || ranked.length === 0) {
    const suggestions = (ranked.length > 0
      ? ranked.slice(0, 3).map((r) => r.entry)
      : [KNOWLEDGE_BY_ID.get("product-purpose"), KNOWLEDGE_BY_ID.get("brookside-meadows"), KNOWLEDGE_BY_ID.get("real-vs-seeded")]
    )
      .filter((e): e is KnowledgeEntry => Boolean(e))
      .map((e) => ({ id: e.id, title: e.title }));
    return { kind: "low_confidence", message: LOW_CONFIDENCE_MESSAGE, suggestions };
  }

  const top = ranked[0].entry;
  if (confidence === "high") {
    const blocks = [top.shortAnswer, ...(top.detail ?? [])];
    if (top.limitation) blocks.push(top.limitation);
    return groundedAnswer(top, "high", blocks);
  }

  // Medium confidence: answer cautiously, name the matched topic, offer choices.
  const blocks = [`Closest match: ${top.title}.`, top.shortAnswer];
  if (top.limitation) blocks.push(top.limitation);
  return groundedAnswer(top, "medium", blocks);
}
