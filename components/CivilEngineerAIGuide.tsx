"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

// Civil Engineer AI Guide: a deterministic local project guide. This component
// handles presentation, interaction, and accessibility only. Retrieval,
// ranking, safety classification, page awareness, and answer composition live
// in lib/guide, which is lazy-loaded when the panel first opens so the
// knowledge catalog stays out of the initial page bundle. Questions never
// leave the browser: no inference API, no model download, no telemetry.

import type { GuideAnswer, GuideContext, QuickLink } from "@/lib/guide/types";

type GuideEngine = {
  answerQuestion: (question: string, context: GuideContext) => GuideAnswer;
  KNOWLEDGE: { id: string; title: string }[];
  sourceUrl: (path: string) => string;
};

const INTRO =
  "Welcome. I am a deterministic local guide for this project. I can explain the Brookside Meadows demo, the reviewer workflow, the architecture, security, testing, what is real versus seeded, and where things live in the repository. Your questions stay in this browser.";

const BOUNDARY_LINE =
  "AI provides review support. You make the decisions. Every review is human.";

const SUGGESTED_QUESTIONS = [
  "What is Civil Engineer AI?",
  "What is Brookside Meadows?",
  "How does authentication work?",
  "What is real and what is seeded?",
];

type Message =
  | { role: "user"; text: string }
  | { role: "guide"; answer: GuideAnswer };

function AnswerLinks({ links }: { links: QuickLink[] }) {
  if (links.length === 0) return null;
  return (
    <ul className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
      {links.map((link) => (
        <li key={link.href}>
          {link.href.startsWith("/") ? (
            <Link href={link.href} className="text-xs font-medium text-blue-700 hover:underline">
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
  );
}

function AnswerSources({
  sources,
  sourceUrl,
}: {
  sources: string[];
  sourceUrl: (path: string) => string;
}) {
  if (sources.length === 0) return null;
  return (
    <div className="mt-2 border-t border-blue-100 pt-1.5">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
        Sources
      </span>
      <ul className="mt-0.5 space-y-0.5">
        {sources.map((path) => (
          <li key={path}>
            <a
              href={sourceUrl(path)}
              target="_blank"
              rel="noreferrer"
              className="break-all font-mono text-[10px] text-blue-700 hover:underline"
            >
              {path}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function CivilEngineerAIGuide() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [engine, setEngine] = useState<GuideEngine | null>(null);
  const launcherRef = useRef<HTMLButtonElement | null>(null);
  const panelRef = useRef<HTMLElement | null>(null);
  const bodyRef = useRef<HTMLDivElement | null>(null);
  const historyRef = useRef<{ question: string; answeredEntryIds: string[] }[]>([]);
  const pathname = usePathname();

  // Lazy-load the retrieval engine the first time the panel opens.
  useEffect(() => {
    if (!open || engine) return;
    let active = true;
    Promise.all([import("@/lib/guide"), import("@/lib/guide/sourceLinks")]).then(
      ([guide, links]) => {
        if (!active) return;
        setEngine({
          answerQuestion: guide.answerQuestion,
          KNOWLEDGE: guide.KNOWLEDGE,
          sourceUrl: links.sourceUrl,
        });
      },
    );
    return () => {
      active = false;
    };
  }, [open, engine]);

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

  // Keep the newest exchange in view.
  useEffect(() => {
    const body = bodyRef.current;
    if (body) body.scrollTop = body.scrollHeight;
  }, [messages, open]);

  const close = () => {
    setOpen(false);
    launcherRef.current?.focus();
  };

  const ask = useCallback(
    (text: string) => {
      if (!engine) return;
      const answer = engine.answerQuestion(text, {
        route: pathname ?? "/",
        history: historyRef.current,
      });
      const answeredEntryIds =
        answer.kind === "grounded" ? [answer.entry.id] : [];
      historyRef.current = [
        ...historyRef.current.slice(-4),
        { question: text, answeredEntryIds },
      ];
      setMessages((prev) => [
        ...prev,
        { role: "user", text },
        { role: "guide", answer },
      ]);
    },
    [engine, pathname],
  );

  const submitQuestion = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;
    ask(trimmed);
    setQuestion("");
  };

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

          <div ref={bodyRef} className="flex-1 overflow-y-auto px-4 py-3">
            <p className="text-xs leading-relaxed text-slate-600">{INTRO}</p>
            <p className="mt-2 text-[11px] text-slate-400">{BOUNDARY_LINE}</p>

            <div className="mt-3 space-y-1.5">
              {SUGGESTED_QUESTIONS.map((suggested) => (
                <button
                  key={suggested}
                  type="button"
                  disabled={!engine}
                  onClick={() => ask(suggested)}
                  className="block w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-left text-xs text-slate-700 transition hover:border-blue-300 hover:bg-blue-50 disabled:opacity-60"
                >
                  {suggested}
                </button>
              ))}
            </div>

            <div aria-live="polite" className="space-y-2">
              {messages.map((message, index) =>
                message.role === "user" ? (
                  <p
                    key={index}
                    className="ml-8 mt-3 rounded-lg rounded-br-sm bg-slate-100 px-3 py-2 text-xs leading-relaxed text-slate-700"
                  >
                    {message.text}
                  </p>
                ) : (
                  <div
                    key={index}
                    className="mr-4 rounded-lg rounded-bl-sm border border-blue-100 bg-blue-50/60 px-3 py-2.5"
                  >
                    {message.answer.kind === "safety" ? (
                      <p className="text-xs leading-relaxed text-slate-700">
                        {message.answer.message}
                      </p>
                    ) : message.answer.kind === "low_confidence" ? (
                      <>
                        <p className="text-xs leading-relaxed text-slate-700">
                          {message.answer.message}
                        </p>
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {message.answer.suggestions.map((sugg) => (
                            <button
                              key={sugg.id}
                              type="button"
                              onClick={() => ask(sugg.title)}
                              className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-600 transition hover:border-blue-300 hover:text-blue-700"
                            >
                              {sugg.title}
                            </button>
                          ))}
                        </div>
                      </>
                    ) : message.answer.kind === "page_context" ? (
                      <>
                        {message.answer.blocks.map((block) => (
                          <p key={block.slice(0, 24)} className="mb-2 text-xs leading-relaxed text-slate-700 last:mb-0">
                            {block}
                          </p>
                        ))}
                        <AnswerLinks links={message.answer.links} />
                        {engine ? (
                          <AnswerSources
                            sources={message.answer.sources}
                            sourceUrl={engine.sourceUrl}
                          />
                        ) : null}
                      </>
                    ) : (
                      <>
                        {message.answer.confidence === "medium" ? (
                          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-amber-600">
                            Closest matching topic
                          </p>
                        ) : null}
                        {message.answer.blocks.map((block) => (
                          <p key={block.slice(0, 24)} className="mb-2 text-xs leading-relaxed text-slate-700 last:mb-0">
                            {block}
                          </p>
                        ))}
                        <AnswerLinks links={message.answer.links} />
                        {engine ? (
                          <AnswerSources
                            sources={message.answer.sources}
                            sourceUrl={engine.sourceUrl}
                          />
                        ) : null}
                        {message.answer.related.length > 0 ? (
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {message.answer.related.map((rel) => (
                              <button
                                key={rel.id}
                                type="button"
                                onClick={() => ask(rel.title)}
                                className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-600 transition hover:border-blue-300 hover:text-blue-700"
                              >
                                {rel.title}
                              </button>
                            ))}
                          </div>
                        ) : null}
                      </>
                    )}
                  </div>
                ),
              )}

              {messages.length > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    setMessages([]);
                    historyRef.current = [];
                  }}
                  className="mt-1 text-[11px] font-medium text-slate-500 hover:text-slate-700 hover:underline"
                >
                  Clear conversation
                </button>
              )}
            </div>
          </div>

          <form
            onSubmit={submitQuestion}
            className="flex items-center gap-2 border-t border-slate-100 px-3 py-2.5"
          >
            <label htmlFor="ceai-guide-input" className="sr-only">
              Ask about this project
            </label>
            <input
              id="ceai-guide-input"
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask about this project."
              className="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs text-slate-700 placeholder:text-slate-400"
            />
            <button
              type="submit"
              disabled={!engine}
              className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-blue-700 disabled:opacity-60"
            >
              Ask
            </button>
          </form>
        </section>
      )}
    </>
  );
}
