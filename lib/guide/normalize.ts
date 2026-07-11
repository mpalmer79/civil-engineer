// Deterministic text normalization for guide retrieval: tokenization, light
// stemming, synonym expansion, and bounded typo tolerance. All local, no
// network, no model.

const SYNONYMS: Record<string, string> = {
  auth: "authentication",
  authn: "authentication",
  login: "signin",
  "log": "signin", // "log in" tokenizes to ["log", "in"]
  signon: "signin",
  db: "database",
  postgres: "postgresql",
  repo: "repository",
  docs: "documentation",
  doc: "document",
  ui: "frontend",
  js: "javascript",
  ts: "typescript",
  nextjs: "next",
  api: "api",
  ai: "ai",
  llm: "ai",
  gpt: "ai",
  csrf: "csrf",
  bff: "proxy",
  e2e: "endtoend",
  spec: "test",
  stormwater: "stormwater",
  subdivision: "subdivision",
  dev: "developer",
};

const STOPWORDS = new Set([
  "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
  "do", "does", "did", "to", "of", "in", "on", "for", "with", "at", "by",
  "and", "or", "not", "no", "it", "its", "this", "that", "these", "those",
  "i", "me", "my", "we", "our", "you", "your", "they", "their",
  "can", "could", "would", "should", "will", "shall", "may", "might",
  "about", "into", "from", "as", "if", "so", "than", "then", "there",
  "here", "have", "has", "had", "am", "any", "some", "tell", "please",
]);

// Light suffix stripping. Deliberately conservative: it must never merge
// unrelated words (the substring-collision defect this replaces).
export function stem(token: string): string {
  let t = token;
  if (t.length > 5 && t.endsWith("ing")) t = t.slice(0, -3);
  else if (t.length > 4 && t.endsWith("ies")) t = `${t.slice(0, -3)}y`;
  else if (t.length > 4 && t.endsWith("ed")) t = t.slice(0, -2);
  else if (t.length > 3 && t.endsWith("s") && !t.endsWith("ss")) t = t.slice(0, -1);
  return t;
}

export function tokenize(raw: string): string[] {
  return raw
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
}

// Full pipeline: tokenize, drop stopwords, apply synonyms, stem.
export function normalizeQuery(raw: string): string[] {
  return tokenize(raw)
    .filter((t) => !STOPWORDS.has(t))
    .map((t) => SYNONYMS[t] ?? t)
    .map(stem);
}

// Normalized single-string form used for phrase matching.
export function normalizePhrase(raw: string): string {
  return normalizeQuery(raw).join(" ");
}

// Bounded edit distance for typo tolerance. Returns true when a and b are
// within one insertion, deletion, or substitution. Only used for tokens of
// length five or more, so short words cannot blur into each other.
export function withinOneEdit(a: string, b: string): boolean {
  if (a === b) return true;
  const la = a.length;
  const lb = b.length;
  if (Math.abs(la - lb) > 1) return false;
  let i = 0;
  let j = 0;
  let edits = 0;
  while (i < la && j < lb) {
    if (a[i] === b[j]) {
      i += 1;
      j += 1;
      continue;
    }
    edits += 1;
    if (edits > 1) return false;
    if (la > lb) i += 1;
    else if (lb > la) j += 1;
    else {
      i += 1;
      j += 1;
    }
  }
  return edits + (la - i) + (lb - j) <= 1;
}
