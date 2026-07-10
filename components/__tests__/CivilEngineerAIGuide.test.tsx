import { readFileSync } from "node:fs";
import { join } from "node:path";

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import CivilEngineerAIGuide from "@/components/CivilEngineerAIGuide";

afterEach(() => cleanup());

const DEVELOPER_QUESTION =
  "I would like to know more about the developer of this project.";

function openGuide() {
  render(<CivilEngineerAIGuide />);
  fireEvent.click(
    screen.getByRole("button", { name: /civil engineer ai guide/i }),
  );
}

function ask(text: string) {
  fireEvent.change(screen.getByLabelText(/ask me about this project/i), {
    target: { value: text },
  });
  fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));
}

describe("CivilEngineerAIGuide launcher and panel", () => {
  it("renders a launcher labeled Civil Engineer AI Guide", () => {
    render(<CivilEngineerAIGuide />);
    const launcher = screen.getByRole("button", {
      name: /civil engineer ai guide/i,
    });
    expect(launcher).toBeInTheDocument();
    expect(launcher).toHaveAttribute("aria-expanded", "false");
  });

  it("opens an accessible dialog panel with a visible title and intro", () => {
    openGuide();
    const panel = screen.getByRole("dialog", {
      name: /civil engineer ai guide/i,
    });
    expect(panel).toBeInTheDocument();
    expect(
      screen.getByText(/welcome\. i can help you explore this civil engineer ai project/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/ai provides review support\. you make the decisions\. every review is human\./i),
    ).toBeInTheDocument();
  });

  it("closes from the close button and returns to a collapsed launcher", () => {
    openGuide();
    fireEvent.click(screen.getByRole("button", { name: /close guide/i }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(
      screen.getByRole("button", { name: /civil engineer ai guide/i }),
    ).toHaveAttribute("aria-expanded", "false");
  });

  it("closes on Escape", () => {
    openGuide();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});

describe("CivilEngineerAIGuide categories and suggested questions", () => {
  it("renders the category chips", () => {
    openGuide();
    for (const chip of [
      "Project Overview",
      "For Civil Engineers",
      "Brookside Meadows Demo",
      "Review Workflow",
      "Evidence & Documents",
      "Technical Implementation",
      "Developer & Source Code",
    ]) {
      expect(screen.getByRole("button", { name: chip })).toBeInTheDocument();
    }
  });

  it("renders the three suggested questions, including the exact developer question", () => {
    openGuide();
    expect(
      screen.getByRole("button", {
        name: "What does Civil Engineer AI help reviewers do?",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "How does the Brookside Meadows demo work?",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: DEVELOPER_QUESTION }),
    ).toBeInTheDocument();
  });

  it("shows the developer answer with profile and repository links", () => {
    openGuide();
    fireEvent.click(screen.getByRole("button", { name: DEVELOPER_QUESTION }));
    expect(
      screen.getByText(/developed by michael palmer/i),
    ).toBeInTheDocument();

    const links = {
      LinkedIn: "http://linkedin.com/in/mpalmer1234",
      GitHub: "https://www.github.com/mpalmer79",
      "Project Repository": "https://www.github.com/mpalmer79/civil-engineer",
    };
    for (const [label, href] of Object.entries(links)) {
      expect(screen.getByRole("link", { name: label })).toHaveAttribute(
        "href",
        href,
      );
    }
  });

  it("links topic answers only to routes that exist", () => {
    openGuide();
    fireEvent.click(
      screen.getByRole("button", {
        name: "What does Civil Engineer AI help reviewers do?",
      }),
    );
    for (const [label, route] of [
      ["Start Guided Demo", "app/guided-demo"],
      ["Open Review Queue", "app/dashboard/queue"],
      ["View Projects", "app/projects"],
    ] as const) {
      expect(screen.getByRole("link", { name: label })).toBeInTheDocument();
      expect(
        readFileSync(join(process.cwd(), route, "page.tsx"), "utf8").length,
      ).toBeGreaterThan(0);
    }
  });
});

describe("CivilEngineerAIGuide typed input", () => {
  it("answers a known keyword question with the matching static answer", () => {
    openGuide();
    ask("Where can I find the GitHub repository?");
    expect(screen.getByText(/developed by michael palmer/i)).toBeInTheDocument();
  });

  it("echoes the asked question in the conversation thread", () => {
    openGuide();
    ask("Where can I find the GitHub repository?");
    expect(
      screen.getByText("Where can I find the GitHub repository?"),
    ).toBeInTheDocument();
  });

  it("accumulates multiple exchanges instead of replacing the answer", () => {
    openGuide();
    ask("How does the Brookside Meadows demo work?");
    ask("What is the review workflow process?");
    expect(
      screen.getByText(/synthetic 47-lot residential subdivision/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/begins with project intake/i),
    ).toBeInTheDocument();
  });

  it("clears the conversation with the clear button", () => {
    openGuide();
    ask("How does the Brookside Meadows demo work?");
    fireEvent.click(screen.getByRole("button", { name: /clear conversation/i }));
    expect(
      screen.queryByText(/synthetic 47-lot residential subdivision/i),
    ).toBeNull();
    expect(
      screen.queryByRole("button", { name: /clear conversation/i }),
    ).toBeNull();
  });

  it("falls back for unrelated questions", () => {
    openGuide();
    ask("What is the best pizza in town?");
    expect(
      screen.getByText(/i do not have enough project-specific information/i),
    ).toBeInTheDocument();
  });

  it("answers the real-world value question with the overview, not the fallback", () => {
    openGuide();
    ask("How does this help solve real world challenges?");
    expect(
      screen.getByText(/plan review is evidence work/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/i do not have enough project-specific information/i),
    ).toBeNull();
  });

  it("answers the civil engineer value question with the reviewer answer, not the fallback", () => {
    openGuide();
    ask("How can this help me as a civil engineer?");
    expect(
      screen.getByText(/the value is organization and traceability/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/i do not have enough project-specific information/i),
    ).toBeNull();
  });

  it("answers technical stack questions with the implementation answer", () => {
    openGuide();
    ask("What is the technical stack behind this?");
    expect(
      screen.getByText(/next\.js app router with typescript/i),
    ).toBeInTheDocument();
  });

  it("keeps the user's question visible alongside the answer after sending", () => {
    openGuide();
    ask("How can this help me as a civil engineer?");
    expect(
      screen.getByText("How can this help me as a civil engineer?"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/the value is organization and traceability/i),
    ).toBeInTheDocument();
  });

  it("keeps the scoped safety response for real-use questions despite value keywords", () => {
    openGuide();
    ask("Can I use this for my real world project?");
    expect(
      screen.getByText(/cannot provide engineering, permitting, legal, or code-compliance advice/i),
    ).toBeInTheDocument();
  });

  it("uses the scoped safety response for engineering decision questions", () => {
    openGuide();
    ask("Can the AI approve this plan?");
    expect(
      screen.getByText(/cannot provide engineering, permitting, legal, or code-compliance advice/i),
    ).toBeInTheDocument();
  });

  it("uses the scoped safety response for sizing and code questions", () => {
    openGuide();
    ask("What is the correct detention basin size?");
    expect(
      screen.getByText(/final engineering decisions remain under qualified human review/i),
    ).toBeInTheDocument();
  });
});

describe("CivilEngineerAIGuide scope and language hygiene", () => {
  const source = () =>
    readFileSync(
      join(process.cwd(), "components/CivilEngineerAIGuide.tsx"),
      "utf8",
    );

  it("makes no external API calls and references no LLM providers", () => {
    const text = source().toLowerCase();
    expect(text).not.toContain("fetch(");
    expect(text).not.toContain("axios");
    expect(text).not.toContain("openai");
    expect(text).not.toContain("anthropic");
    expect(text).not.toContain("api key");
  });

  it("never says ask me anything or unsafe capability claims", () => {
    const text = source().toLowerCase();
    expect(text).not.toContain("ask me anything");
    expect(text).not.toContain("i can answer any question");
    expect(text).not.toContain("autonomous review");
    expect(text).not.toContain("automated approval");
    expect(text).not.toContain("replaces civil engineers");
  });

  it("contains no em dashes in guide copy", () => {
    expect(source()).not.toContain("\u2014");
  });
});
