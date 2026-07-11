// Types for the Civil Engineer AI Guide: a deterministic local project guide
// grounded in an allowlisted knowledge catalog. It never calls an outside
// inference API, never loads a model, and never sends the visitor's questions
// anywhere. Answers are extractive and template-based.

export type QuickLink = { href: string; label: string };

export type SafetyClass = "public";

export type KnowledgeEntry = {
  // Stable identifier, referenced by the evaluation corpus and follow-ups.
  id: string;
  title: string;
  topic: string;
  // One-paragraph direct answer.
  shortAnswer: string;
  // Optional deeper explanation blocks, shown for direct questions.
  detail?: string[];
  // Optional single limitation statement appended to grounded answers.
  limitation?: string;
  // Query surface: exact phrases score highest, then aliases, then keywords.
  keyPhrases: string[];
  aliases?: string[];
  entities?: string[];
  // Route links offered with the answer.
  links?: QuickLink[];
  // Repository paths that ground the answer. Validated by
  // scripts/check-guide-knowledge.mjs; a missing path fails CI.
  sources?: string[];
  // Structured follow-up material.
  implementation?: string[];
  tests?: string[];
  realOrSeeded?: string;
  // Route prefixes where this entry is contextually boosted.
  contextTags?: string[];
  related?: string[];
  priority?: number;
  safety: SafetyClass;
};

export type GuideConfidence = "high" | "medium" | "low";

export type GuideAnswer =
  | {
      kind: "grounded";
      confidence: GuideConfidence;
      entry: KnowledgeEntry;
      // Extra text blocks composed for this specific question (for example a
      // follow-up view over the same entry, or page context).
      blocks: string[];
      links: QuickLink[];
      sources: string[];
      related: { id: string; title: string }[];
    }
  | {
      kind: "page_context";
      blocks: string[];
      links: QuickLink[];
      sources: string[];
    }
  | {
      kind: "safety";
      message: string;
    }
  | {
      kind: "low_confidence";
      message: string;
      suggestions: { id: string; title: string }[];
    };

export type ConversationTurn = {
  question: string;
  answeredEntryIds: string[];
};

export type GuideContext = {
  // Current pathname, used for page-context boosts and questions.
  route: string;
  // Prior turns, newest last, used for follow-up resolution.
  history: ConversationTurn[];
};
