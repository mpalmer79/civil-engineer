"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

// Closed-scope, rule-based project guide. All answers are static, pre-written
// copy. There are no external API calls and no generated text; typed input
// only selects one of the static answers below via keyword matching.

type QuickLink = { href: string; label: string };

type Topic = {
  id: string;
  chip: string;
  question?: string;
  keywords: string[];
  paragraphs: string[];
  links?: QuickLink[];
};

const DEVELOPER_LINKS: QuickLink[] = [
  { href: "http://linkedin.com/in/mpalmer1234", label: "LinkedIn" },
  { href: "https://www.github.com/mpalmer79", label: "GitHub" },
  { href: "https://www.github.com/mpalmer79/civil-engineer", label: "Project Repository" },
];

const TOPICS: Topic[] = [
  {
    id: "developer",
    chip: "Developer & Source Code",
    question: "I would like to know more about the developer of this project.",
    keywords: ["developer", "michael", "palmer", "linkedin", "github", "source", "repo", "repository", "author", "built this"],
    paragraphs: [
      "This project was developed by Michael Palmer as part of a software engineering portfolio focused on civil engineering review workflows, evidence-first systems, and human-in-the-loop AI support.",
      "Michael is a Computer Science student with professional experience across automotive technology, implementation, workflow design, and applied AI solutions. This project demonstrates his ability to model a real-world review process, build a polished Next.js interface, structure synthetic demo data, and communicate technical boundaries clearly.",
    ],
    links: DEVELOPER_LINKS,
  },
  {
    id: "brookside",
    chip: "Brookside Meadows Demo",
    question: "How does the Brookside Meadows demo work?",
    keywords: ["brookside", "meadows", "hartwell", "subdivision", "demo", "synthetic", "47", "sample project", "fixture"],
    paragraphs: [
      "Brookside Meadows is a synthetic 47-lot residential subdivision used to demonstrate the app's workflow. It gives reviewers a realistic project context for document intake, stormwater evidence review, applicant response tracking, and review packet preparation.",
    ],
    links: [
      { href: "/guided-demo", label: "Start Guided Demo" },
      { href: "/projects", label: "View Projects" },
    ],
  },
  {
    id: "workflow",
    chip: "Review Workflow",
    keywords: ["workflow", "queue", "response", "handoff", "review packet", "process", "resubmittal", "intake"],
    paragraphs: [
      "The workflow begins with project intake, moves through reviewer queue management, document and evidence review, applicant response tracking, and ends with a reviewer-controlled handoff package.",
    ],
    links: [
      { href: "/dashboard/queue", label: "Open Review Queue" },
      { href: "/response-package", label: "Response Package" },
      { href: "/review-packet", label: "Review Packet" },
    ],
  },
  {
    id: "evidence",
    chip: "Evidence & Documents",
    keywords: ["evidence", "documents", "pdf", "dxf", "plan", "findings", "citations", "audit", "traceability"],
    paragraphs: [
      "The project emphasizes evidence-first review. Findings should connect back to supporting documents, plan references, or review artifacts so the reviewer can understand why an item was flagged.",
    ],
    links: [
      { href: "/documents", label: "Documents" },
      { href: "/findings", label: "Findings" },
      { href: "/audit", label: "Audit Trail" },
    ],
  },
  {
    id: "overview",
    chip: "Project Overview",
    question: "What does Civil Engineer AI help reviewers do?",
    keywords: ["overview", "project", "what is this", "purpose", "help reviewers", "about", "portfolio", "stormwater"],
    paragraphs: [
      "Civil Engineer AI is a portfolio project that demonstrates a stormwater review support workflow. It helps organize project documents, reviewer findings, applicant responses, and handoff packages while keeping final review decisions under human control.",
    ],
    links: [
      { href: "/guided-demo", label: "Start Guided Demo" },
      { href: "/dashboard/queue", label: "Open Review Queue" },
      { href: "/projects", label: "View Projects" },
    ],
  },
];

// Chips render in reading order; matching uses the array order above so the
// developer and demo topics win ties over the broader overview keywords.
const CHIP_ORDER = ["overview", "brookside", "workflow", "evidence", "developer"];

const SUGGESTED_QUESTION_IDS = ["overview", "brookside", "developer"];

// Questions about real engineering decisions get the scoped response below
// instead of a topic answer or the generic fallback.
const SAFETY_STEMS = [
  "approv",
  "complian",
  "detention",
  "basin",
  "legal",
  "permit",
  "real project",
  "replace",
  "stamp",
  "certif",
  "construction advice",
  "build this",
];

const SAFETY_RESPONSE =
  "This guide cannot provide engineering, permitting, legal, or code-compliance advice. Civil Engineer AI is a portfolio demonstration of review support workflows. Final engineering decisions remain under qualified human review.";

const FALLBACK_RESPONSE =
  "Thanks for your question. I can help with information about this Civil Engineer AI project, including the Brookside Meadows demo, review workflow, evidence tracking, response packages, technical implementation, and developer information. I do not have enough project-specific information to answer that question accurately.";

const INTRO =
  "Welcome. I can help you explore this Civil Engineer AI project, including the Brookside Meadows demo, review workflow, evidence tracking, response packages, source code, and developer background.";

const BOUNDARY_LINE =
  "AI provides review support. You make the decisions. Every review is human.";

type Answer =
  | { kind: "topic"; topic: Topic }
  | { kind: "safety" }
  | { kind: "fallback" };

function matchAnswer(raw: string): Answer {
  const text = raw.toLowerCase();

  if (SAFETY_STEMS.some((stem) => text.includes(stem))) {
    return { kind: "safety" };
  }

  for (const topic of TOPICS) {
    if (topic.keywords.some((keyword) => text.includes(keyword))) {
      return { kind: "topic", topic };
    }
  }

  return { kind: "fallback" };
}

export default function CivilEngineerAIGuide() {
  const [open, setOpen] = useState(false);
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [question, setQuestion] = useState("");
  const launcherRef = useRef<HTMLButtonElement | null>(null);
  const panelRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) return;

    panelRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
        launcherRef.current?.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open]);

  const close = () => {
    setOpen(false);
    launcherRef.current?.focus();
  };

  const showTopic = (id: string) => {
    const topic = TOPICS.find((t) => t.id === id);
    if (topic) setAnswer({ kind: "topic", topic });
  };

  const submitQuestion = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;
    setAnswer(matchAnswer(trimmed));
    setQuestion("");
  };

  const chips = CHIP_ORDER.map((id) => TOPICS.find((t) => t.id === id)).filter(
    (t): t is Topic => Boolean(t),
  );

  const suggested = SUGGESTED_QUESTION_IDS.map((id) =>
    TOPICS.find((t) => t.id === id),
  ).filter((t): t is Topic => Boolean(t?.question));

  return (
    <>
      <button
        ref={launcherRef}
        type="button"
        aria-expanded={open}
        aria-controls="ceai-guide-panel"
        onClick={() => setOpen((v) => !v)}
        className="fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-full bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg transition hover:bg-blue-700"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-4 w-4"
          aria-hidden="true"
        >
          <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
        </svg>
        Civil Engineer AI Guide
      </button>

      {open && (
        <section
          id="ceai-guide-panel"
          ref={panelRef}
          role="dialog"
          aria-modal="false"
          aria-labelledby="ceai-guide-title"
          tabIndex={-1}
          className="fixed bottom-20 left-4 right-4 z-50 flex max-h-[min(34rem,calc(100vh-7rem))] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl sm:left-auto sm:w-96"
        >
          <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-4 py-3">
            <h2 id="ceai-guide-title" className="text-sm font-semibold text-slate-900">
              Civil Engineer AI Guide
            </h2>

            <button
              type="button"
              onClick={close}
              aria-label="Close guide"
              className="grid h-7 w-7 place-items-center rounded-md text-slate-500 transition hover:bg-slate-200 hover:text-slate-700"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                className="h-4 w-4"
                aria-hidden="true"
              >
                <path d="M6 6l12 12M18 6L6 18" />
              </svg>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-3">
            <p className="text-xs leading-relaxed text-slate-600">{INTRO}</p>

            <p className="mt-2 text-[11px] text-slate-400">{BOUNDARY_LINE}</p>

            <div className="mt-3 flex flex-wrap gap-1.5" aria-label="Guide topics">
              {chips.map((topic) => (
                <button
                  key={topic.id}
                  type="button"
                  onClick={() => showTopic(topic.id)}
                  className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-600 transition hover:border-blue-300 hover:text-blue-700"
                >
                  {topic.chip}
                </button>
              ))}
            </div>

            <div className="mt-3 space-y-1.5">
              {suggested.map((topic) => (
                <button
                  key={topic.id}
                  type="button"
                  onClick={() => showTopic(topic.id)}
                  className="block w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-left text-xs text-slate-700 transition hover:border-blue-300 hover:bg-blue-50"
                >
                  {topic.question}
                </button>
              ))}
            </div>

            <div aria-live="polite">
              {answer && (
                <div className="mt-3 rounded-lg border border-blue-100 bg-blue-50/60 px-3 py-2.5">
                  {answer.kind === "topic" ? (
                    <>
                      {answer.topic.paragraphs.map((p) => (
                        <p key={p.slice(0, 24)} className="mb-2 text-xs leading-relaxed text-slate-700 last:mb-0">
                          {p}
                        </p>
                      ))}

                      {answer.topic.links && (
                        <ul className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
                          {answer.topic.links.map((link) => (
                            <li key={link.href}>
                              {link.href.startsWith("/") ? (
                                <Link
                                  href={link.href}
                                  className="text-xs font-medium text-blue-700 hover:underline"
                                >
                                  {link.label}
                                </Link>
                              ) : (
                                <a
                                  href={link.href}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-xs font-medium text-blue-700 hover:underline"
                                >
                                  {link.label}
                                </a>
                              )}
                            </li>
                          ))}
                        </ul>
                      )}
                    </>
                  ) : (
                    <p className="text-xs leading-relaxed text-slate-700">
                      {answer.kind === "safety" ? SAFETY_RESPONSE : FALLBACK_RESPONSE}
                    </p>
                  )}

                  <button
                    type="button"
                    onClick={() => setAnswer(null)}
                    className="mt-2 text-[11px] font-medium text-slate-500 hover:text-slate-700 hover:underline"
                  >
                    Clear answer
                  </button>
                </div>
              )}
            </div>
          </div>

          <form
            onSubmit={submitQuestion}
            className="flex items-center gap-2 border-t border-slate-100 px-3 py-2.5"
          >
            <label htmlFor="ceai-guide-input" className="sr-only">
              Ask me about this project
            </label>

            <input
              id="ceai-guide-input"
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask me about this project."
              className="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs text-slate-700 placeholder:text-slate-400"
            />

            <button
              type="submit"
              className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-blue-700"
            >
              Ask
            </button>
          </form>
        </section>
      )}
    </>
  );
}
