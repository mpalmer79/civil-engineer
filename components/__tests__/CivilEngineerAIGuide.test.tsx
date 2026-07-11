import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";

let mockPathname = "/";
vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
}));

import CivilEngineerAIGuide from "@/components/CivilEngineerAIGuide";

async function openGuide() {
  render(<CivilEngineerAIGuide />);
  fireEvent.click(screen.getByRole("button", { name: /civil engineer ai guide/i }));
  // The engine lazy-loads; the Ask button enables once it is ready.
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Ask" })).toBeEnabled(),
  );
}

async function ask(text: string) {
  fireEvent.change(screen.getByLabelText(/ask about this project/i), {
    target: { value: text },
  });
  fireEvent.click(screen.getByRole("button", { name: "Ask" }));
}

beforeEach(() => {
  mockPathname = "/";
});

afterEach(() => cleanup());

describe("guide launcher and focus behavior", () => {
  it("opens the panel, focuses it, and returns focus to the launcher on Escape", async () => {
    await openGuide();
    const panel = document.getElementById("ceai-guide-panel");
    expect(panel).not.toBeNull();
    expect(document.activeElement).toBe(panel);

    fireEvent.keyDown(document, { key: "Escape" });
    expect(document.getElementById("ceai-guide-panel")).toBeNull();
    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: /civil engineer ai guide/i }),
    );
  });

  it("announces answers through a polite live region", async () => {
    await openGuide();
    const panel = document.getElementById("ceai-guide-panel");
    expect(panel?.querySelector('[aria-live="polite"]')).not.toBeNull();
  });
});

describe("grounded answering", () => {
  it("answers a direct question with sources and related topics", async () => {
    await openGuide();
    await ask("How does authentication work?");
    await waitFor(() =>
      expect(screen.getByText(/browser never holds the token/i)).toBeInTheDocument(),
    );
    // Repository source references render as stable links.
    const source = screen.getByRole("link", { name: /adr\/0003-secure-session-architecture/i });
    expect(source.getAttribute("href")).toContain("github.com/mpalmer79/civil-engineer");
  });

  it("handles a typo-bearing question", async () => {
    await openGuide();
    await ask("whats is civl engineer ai");
    await waitFor(() =>
      expect(screen.getByText(/reviewer-controlled, evidence-first/i)).toBeInTheDocument(),
    );
  });

  it("resolves a short follow-up against the previous answer", async () => {
    await openGuide();
    await ask("what is csrf protection here");
    await waitFor(() =>
      expect(screen.getByText(/two independent checks/i)).toBeInTheDocument(),
    );
    await ask("what tests cover it");
    await waitFor(() =>
      expect(
        screen.getAllByRole("link", { name: /session\.test\.ts/i }).length,
      ).toBeGreaterThanOrEqual(1),
    );
  });

  it("answers page-context questions from the current route", async () => {
    mockPathname = "/documents";
    await openGuide();
    await ask("what am I looking at?");
    await waitFor(() =>
      expect(screen.getByText(/seeded brookside meadows submission package/i)).toBeInTheDocument(),
    );
  });
});

describe("safety classification", () => {
  it("refuses an engineering-decision question", async () => {
    await openGuide();
    await ask("Is this basin correctly sized?");
    await waitFor(() =>
      expect(
        screen.getByText(/cannot provide engineering, permitting, legal/i),
      ).toBeInTheDocument(),
    );
  });

  it("answers a repository question that merely names a basin", async () => {
    await openGuide();
    await ask("Where is detention basin information represented?");
    await waitFor(() =>
      expect(screen.getByText(/pond a on the grading plan/i)).toBeInTheDocument(),
    );
  });
});

describe("low-confidence behavior", () => {
  it("declines to guess on unknown questions and offers likely topics", async () => {
    await openGuide();
    await ask("what is the weather in boston");
    await waitFor(() =>
      expect(
        screen.getByText(/could not locate enough public project information/i),
      ).toBeInTheDocument(),
    );
  });
});

describe("privacy and honesty guarantees", () => {
  it("makes no network requests when answering", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    await openGuide();
    await ask("How does authentication work?");
    await waitFor(() =>
      expect(screen.getByText(/browser never holds the token/i)).toBeInTheDocument(),
    );
    expect(fetchSpy).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it("states its local, private nature in the intro", async () => {
    await openGuide();
    expect(screen.getByText(/your questions stay in this browser/i)).toBeInTheDocument();
  });

  it("no longer claims a seeded fallback for backend failures", () => {
    const knowledge = readFileSync("lib/guide/knowledge.ts", "utf8");
    expect(knowledge).not.toContain("falls back to seeded");
    const component = readFileSync("components/CivilEngineerAIGuide.tsx", "utf8");
    expect(component).not.toContain("falls back to seeded");
  });

  it("uses HTTPS for the LinkedIn link", () => {
    const knowledge = readFileSync("lib/guide/knowledge.ts", "utf8");
    expect(knowledge).not.toContain("http://linkedin");
    expect(knowledge).toContain("https://linkedin.com/in/mpalmer1234");
  });

  it("does not use em dashes in guide source or knowledge", () => {
    for (const path of [
      "components/CivilEngineerAIGuide.tsx",
      "lib/guide/knowledge.ts",
      "lib/guide/safety.ts",
      "lib/guide/answerComposer.ts",
    ]) {
      expect(readFileSync(path, "utf8")).not.toContain("\u2014");
    }
  });
});
