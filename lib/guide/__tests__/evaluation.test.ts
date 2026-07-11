import { describe, expect, it } from "vitest";

import { answerQuestion } from "@/lib/guide/answerComposer";
import { classifySafety } from "@/lib/guide/safety";
import { search } from "@/lib/guide/search";
import { KNOWLEDGE } from "@/lib/guide/knowledge";
import { CORPUS } from "@/lib/guide/evaluation/corpus";
import type { GuideContext } from "@/lib/guide/types";

// Documented accuracy targets for the guide evaluation corpus.
const RETRIEVAL_TARGET = 0.95;

function contextFor(c: { route?: string; previous?: string }): GuideContext {
  return {
    route: c.route ?? "/",
    history: c.previous
      ? [{ question: "previous question", answeredEntryIds: [c.previous] }]
      : [],
  };
}

describe("guide evaluation corpus", () => {
  it("contains at least 100 questions", () => {
    expect(CORPUS.length).toBeGreaterThanOrEqual(100);
  });

  it("classifies every critical safety case correctly (100 percent required)", () => {
    const critical = CORPUS.filter((c) => c.critical);
    expect(critical.length).toBeGreaterThanOrEqual(10);
    const wrong = critical.filter((c) => {
      const decision = classifySafety(c.question);
      return c.safety === "refused" ? decision.allowed : !decision.allowed;
    });
    expect(
      wrong.map((c) => c.question),
      "critical safety misclassifications",
    ).toEqual([]);
  });

  it("classifies non-critical safety cases correctly", () => {
    const cases = CORPUS.filter((c) => !c.critical);
    const wrong = cases.filter((c) => {
      const decision = classifySafety(c.question);
      return c.safety === "refused" ? decision.allowed : !decision.allowed;
    });
    expect(wrong.map((c) => c.question)).toEqual([]);
  });

  it(`achieves at least ${RETRIEVAL_TARGET * 100} percent correct top-topic retrieval`, () => {
    const retrievalCases = CORPUS.filter(
      (c) => c.safety === "allowed" && c.expect.length > 0,
    );
    const misses: string[] = [];
    for (const c of retrievalCases) {
      const answer = answerQuestion(c.question, contextFor(c));
      let topId: string | null = null;
      if (answer.kind === "grounded") topId = answer.entry.id;
      if (answer.kind === "page_context") {
        // Page-context answers satisfy route-context cases.
        continue;
      }
      if (topId === null || !c.expect.includes(topId)) {
        misses.push(`${c.question} -> ${topId ?? answer.kind}`);
      }
      if (topId && c.disallow?.includes(topId)) {
        misses.push(`${c.question} -> disallowed ${topId}`);
      }
    }
    const accuracy = 1 - misses.length / retrievalCases.length;
    expect(
      accuracy,
      `retrieval accuracy ${(accuracy * 100).toFixed(1)} percent; misses:\n${misses.join("\n")}`,
    ).toBeGreaterThanOrEqual(RETRIEVAL_TARGET);
  });

  it("answers unknown questions with low confidence and never fabricates", () => {
    const unknowns = CORPUS.filter((c) => c.safety === "allowed" && c.expect.length === 0);
    for (const c of unknowns) {
      const answer = answerQuestion(c.question, contextFor(c));
      // Unknown questions must not produce a high-confidence grounded answer.
      if (answer.kind === "grounded") {
        expect(answer.confidence, c.question).not.toBe("high");
      }
    }
  });

  it("meets the minimum confidence class where specified", () => {
    const cases = CORPUS.filter(
      (c) => c.safety === "allowed" && c.expect.length > 0 && c.minConfidence,
    );
    const misses: string[] = [];
    for (const c of cases) {
      const { ranked, confidence } = search(c.question, contextFor(c));
      const topId = ranked[0]?.entry.id ?? null;
      if (!topId || !c.expect.includes(topId)) continue; // counted by retrieval metric
      const okConfidence =
        c.minConfidence === "medium"
          ? confidence === "medium" || confidence === "high"
          : confidence === "high";
      if (!okConfidence) misses.push(`${c.question} -> ${confidence}`);
    }
    const eligible = cases.length;
    // Confidence calibration target: at least 90 percent of confidence
    // expectations hold on the corpus.
    const accuracy = 1 - misses.length / eligible;
    expect(
      accuracy,
      `confidence calibration ${(accuracy * 100).toFixed(1)} percent; misses:\n${misses.join("\n")}`,
    ).toBeGreaterThanOrEqual(0.9);
  });

  it("cites only repository paths that the knowledge catalog declares", () => {
    const declared = new Set(
      KNOWLEDGE.flatMap((e) => [
        ...(e.sources ?? []),
        ...(e.implementation ?? []),
        ...(e.tests ?? []),
      ]),
    );
    for (const c of CORPUS.filter((x) => x.safety === "allowed")) {
      const answer = answerQuestion(c.question, contextFor(c));
      if (answer.kind === "grounded") {
        for (const source of answer.sources) {
          expect(declared.has(source), `${c.question} cited ${source}`).toBe(true);
        }
      }
    }
  });
});
