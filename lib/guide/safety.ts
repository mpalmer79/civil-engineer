// Intent-based safety classification for the guide. The previous
// implementation refused any question containing broad nouns such as basin,
// permit, or compliance, which blocked legitimate repository questions. This
// classifier distinguishes what is being ASKED, not which nouns appear.
//
// Allowed: where a feature is implemented, what the demo represents, how the
// product limits its claims, what a route displays, what tests enforce the
// safety wording.
//
// Refused: requests for an engineering decision, code-compliance judgment,
// permitting outcome, safety determination, construction advice, or approval.

export type SafetyDecision =
  | { allowed: true }
  | { allowed: false; message: string };

export const SAFETY_RESPONSE =
  "This guide cannot provide engineering, permitting, legal, or code-compliance advice. Civil Engineer AI is a review-support demonstration; final engineering decisions remain with a licensed Professional Engineer. I can explain how this project represents such topics: for example where detention basin data lives in the demo fixture, or which tests enforce the professional wording boundary.";

// Phrases that signal the asker wants a real engineering or permitting
// decision. Matched against the lowercased question with word boundaries.
const DECISION_PATTERNS: RegExp[] = [
  // Judgment about adequacy, sizing, safety, or compliance of a design.
  /\bis (this|the|my|our) (basin|pond|design|plan|project|system|pipe|culvert|site)[a-z ]* (correct|right|adequate|sufficient|safe|compliant|acceptable|ok|okay|good enough|properly sized|sized correctly)\b/,
  /\b(correctly|properly|adequately) (sized|designed|engineered)\b/,
  /\bdoes (this|the|my|our) (plan|design|project|basin|site)[a-z ]* (comply|meet|satisfy)\b/,
  /\b(comply|compliant) with (the )?(code|regulation|ordinance|standard)\b/,
  /\bcan (this|the|my|our) (project|plan|site|design)[a-z ]* (get|receive|obtain|be granted) a permit\b/,
  /\bwill (this|the|my|our) [a-z ]*(pass|clear) (review|inspection|permitting)\b/,
  /\bis (this|the|it|my|our) [a-z ]*(design |project |plan )?safe\b/,
  /\bshould (construction|building|work|grading) (proceed|start|begin|continue)\b/,
  /\bcan (i|we|you) (build|construct|start construction|break ground)\b/,
  /\b(approve|approval of|stamp|certify|sign off on) (this|the|my|our) (plan|design|project|drawing|submission)\b/,
  /\bcan (the )?(ai|system|app|tool|guide) (approve|certify|stamp|sign off)\b/,
  /\bsize (a|the|my|our) (basin|pond|pipe|culvert)\b/,
  /\bhow (big|large|deep) should (a|the|my|our) (basin|pond|pipe|culvert) be\b/,
  /\bconstruction advice\b/,
  /\buse (this|the app|the tool|it) (for|on) (a |my |our )?real (project|submission|review)\b/,
  /\blegal advice\b/,
  /\b(is|am) (this|it|i) (legal|allowed|permitted) to\b/,
];

// Signals that the question is about the repository, the demo, or the
// product's own boundaries rather than a real decision. When one of these
// applies, the question is answerable even though it names basins, permits,
// or compliance.
const REPOSITORY_PATTERNS: RegExp[] = [
  /\bwhere (is|are|does|do|can i find)\b/,
  /\bwhich (file|files|module|modules|component|components|route|routes|test|tests|doc|docs|document|documents)\b/,
  /\bhow (does|do|is|are) (the|this) (app|application|repo|repository|project|system|demo|product|codebase|backend|frontend|guide)\b/,
  /\b(is|does) (there|the repo|the repository|the project|the codebase)\b/,
  /\brepresented\b/,
  /\bimplemented\b/,
  /\bdefined\b/,
  /\bmodeled\b/,
  /\bdiscuss(es|ed)?\b/,
  /\bwording\b/,
  /\bboundar(y|ies)\b/,
  /\bprohibited\b/,
  /\bforbidden\b/,
  /\btests? (enforce|cover|guard|check)\b/,
  /\bdemo (data|fixture|project)\b/,
  /\bseeded\b/,
  /\bsynthetic\b/,
];

export function classifySafety(question: string): SafetyDecision {
  const text = question.toLowerCase().replace(/[^a-z0-9 ]+/g, " ").replace(/\s+/g, " ").trim();

  const decisionHit = DECISION_PATTERNS.some((p) => p.test(text));
  if (!decisionHit) return { allowed: true };

  // A decision-shaped phrase inside a clearly repository-scoped question is
  // allowed: "where is construction advice prohibited?" names the prohibition
  // itself, not a request for advice.
  const repositoryHit = REPOSITORY_PATTERNS.some((p) => p.test(text));
  if (repositoryHit) return { allowed: true };

  return { allowed: false, message: SAFETY_RESPONSE };
}
