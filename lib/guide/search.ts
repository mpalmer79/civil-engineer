// Deterministic local retrieval over the knowledge catalog. Token-aware
// scoring with field weights, exact phrase boosts, synonym expansion, light
// stemming, bounded typo tolerance, an inverse-document-frequency weight per
// token, and context boosts for the current route and conversation. No
// substring matching: "author" can never match "authorization".

import { KNOWLEDGE } from "./knowledge";
import { normalizePhrase, normalizeQuery, withinOneEdit } from "./normalize";
import type { GuideContext, KnowledgeEntry } from "./types";

type IndexedEntry = {
  entry: KnowledgeEntry;
  // Token -> accumulated field weight within this entry.
  tokenWeights: Map<string, number>;
  // Normalized phrases with their weights.
  phrases: { text: string; weight: number }[];
  totalTokens: number;
};

const FIELD_WEIGHTS = {
  title: 5,
  keyPhrases: 4,
  aliases: 4,
  entities: 4,
  topic: 2,
  shortAnswer: 1.5,
  detail: 0.75,
} as const;

const PHRASE_WEIGHT = 6;

function addTokens(map: Map<string, number>, text: string, weight: number) {
  for (const token of normalizeQuery(text)) {
    map.set(token, (map.get(token) ?? 0) + weight);
  }
}

function buildIndex(): { entries: IndexedEntry[]; docFrequency: Map<string, number> } {
  const entries: IndexedEntry[] = KNOWLEDGE.map((entry) => {
    const tokenWeights = new Map<string, number>();
    addTokens(tokenWeights, entry.title, FIELD_WEIGHTS.title);
    for (const phrase of entry.keyPhrases) addTokens(tokenWeights, phrase, FIELD_WEIGHTS.keyPhrases);
    for (const alias of entry.aliases ?? []) addTokens(tokenWeights, alias, FIELD_WEIGHTS.aliases);
    for (const entity of entry.entities ?? []) addTokens(tokenWeights, entity, FIELD_WEIGHTS.entities);
    addTokens(tokenWeights, entry.topic, FIELD_WEIGHTS.topic);
    addTokens(tokenWeights, entry.shortAnswer, FIELD_WEIGHTS.shortAnswer);
    for (const block of entry.detail ?? []) addTokens(tokenWeights, block, FIELD_WEIGHTS.detail);

    const phrases = [
      ...entry.keyPhrases.map((p) => ({ text: normalizePhrase(p), weight: PHRASE_WEIGHT })),
      ...(entry.entities ?? []).map((p) => ({ text: normalizePhrase(p), weight: PHRASE_WEIGHT * 0.8 })),
      { text: normalizePhrase(entry.title), weight: PHRASE_WEIGHT },
    ].filter((p) => p.text.includes(" "));

    let totalTokens = 0;
    for (const weight of tokenWeights.values()) totalTokens += weight;
    return { entry, tokenWeights, phrases, totalTokens };
  });

  const docFrequency = new Map<string, number>();
  for (const indexed of entries) {
    for (const token of indexed.tokenWeights.keys()) {
      docFrequency.set(token, (docFrequency.get(token) ?? 0) + 1);
    }
  }
  return { entries, docFrequency };
}

const INDEX = buildIndex();
const VOCABULARY = [...INDEX.docFrequency.keys()];

function idf(token: string): number {
  const df = INDEX.docFrequency.get(token) ?? 0;
  const n = INDEX.entries.length;
  return Math.log(1 + (n - df + 0.5) / (df + 0.5));
}

// Resolves a query token against the vocabulary, tolerating one edit for
// tokens of five or more characters. Returns the vocabulary token or null.
function resolveToken(token: string): string | null {
  if (INDEX.docFrequency.has(token)) return token;
  if (token.length < 5) return null;
  let best: string | null = null;
  for (const candidate of VOCABULARY) {
    if (Math.abs(candidate.length - token.length) > 1) continue;
    if (withinOneEdit(token, candidate)) {
      // Prefer the rarest (most specific) candidate on ties.
      if (best === null || idf(candidate) > idf(best)) best = candidate;
    }
  }
  return best;
}

export type ScoredEntry = {
  entry: KnowledgeEntry;
  score: number;
};

export type RetrievalResult = {
  ranked: ScoredEntry[];
  confidence: "high" | "medium" | "low";
};

const K1 = 1.4; // term-frequency saturation

export function search(question: string, context?: GuideContext): RetrievalResult {
  const queryTokens = normalizeQuery(question)
    .map(resolveToken)
    .filter((t): t is string => t !== null);
  const queryPhrase = normalizePhrase(question);

  const previousIds = new Set(
    (context?.history ?? []).flatMap((turn) => turn.answeredEntryIds),
  );

  const scored: ScoredEntry[] = INDEX.entries.map((indexed) => {
    let score = 0;
    for (const token of new Set(queryTokens)) {
      const tf = indexed.tokenWeights.get(token) ?? 0;
      if (tf > 0) {
        score += idf(token) * ((tf * (K1 + 1)) / (tf + K1));
      }
    }
    for (const phrase of indexed.phrases) {
      if (phrase.text && queryPhrase.includes(phrase.text)) {
        score += phrase.weight;
      }
    }
    if (score > 0) {
      // Current-page context boost.
      const route = context?.route ?? "";
      if (route && indexed.entry.contextTags?.some((tag) => route.startsWith(tag))) {
        score *= 1.15;
      }
      // Conversation continuity boost.
      if (previousIds.has(indexed.entry.id)) score *= 1.1;
      if (
        indexed.entry.related?.some((id) => previousIds.has(id))
      ) {
        score *= 1.05;
      }
      score *= 1 + (indexed.entry.priority ?? 0) * 0.05;
    }
    return { entry: indexed.entry, score };
  });

  const ranked = scored
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score);

  let confidence: RetrievalResult["confidence"] = "low";
  if (ranked.length > 0) {
    const top = ranked[0].score;
    const runnerUp = ranked[1]?.score ?? 0;
    const margin = top > 0 ? (top - runnerUp) / top : 0;
    if (top >= 6 && (margin >= 0.2 || runnerUp === 0)) confidence = "high";
    else if (top >= 3) confidence = "medium";
  }

  return { ranked, confidence };
}
