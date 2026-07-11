// Public entry point for the Civil Engineer AI Guide's retrieval engine.
// Imported lazily by the guide panel so the knowledge catalog stays out of
// the initial page bundle.

export { answerQuestion } from "./answerComposer";
export { classifySafety, SAFETY_RESPONSE } from "./safety";
export { search } from "./search";
export { KNOWLEDGE, KNOWLEDGE_BY_ID } from "./knowledge";
export { routeInfoFor, isPageContextQuestion } from "./routeContext";
export type {
  ConversationTurn,
  GuideAnswer,
  GuideContext,
  KnowledgeEntry,
  QuickLink,
} from "./types";
