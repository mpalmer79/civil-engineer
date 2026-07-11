// Builds stable repository URLs for guide source references. Uses the build
// snapshot's commit identifier when available so links stay accurate even
// after later commits; falls back to the default branch otherwise.

import facts from "./generated/repo-facts.json";

const REPO_BASE = "https://github.com/mpalmer79/civil-engineer/blob";

export function sourceUrl(path: string): string {
  const ref = (facts as { commit: string | null }).commit ?? "main";
  return `${REPO_BASE}/${ref}/${path}`;
}

export function buildSnapshot(): { commit: string | null } {
  return { commit: (facts as { commit: string | null }).commit };
}
