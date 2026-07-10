# Civil Engineer AI Guide

The Civil Engineer AI Guide is a closed-scope, rule-based project guide mounted on every page from a floating launcher in the lower right corner. It exists so a recruiter or technical reviewer can get oriented without leaving the page they are on. It is not a general-purpose AI assistant, and it never generates open-ended text.

## Purpose

- Explain what the project is and what it demonstrates.
- Point visitors at the right routes: guided demo, reviewer queue, documents, findings, response package, review packet, and audit trail.
- Answer questions about the developer with the developer profile links.
- Keep every response inside the project's professional boundary.

## How it works

The guide is a single React component, `components/CivilEngineerAIGuide.tsx`, with local state only. Every answer is static, pre-written copy stored in the component. The typed input matches the question text against a fixed keyword list and selects one of those static answers. There are no calls to OpenAI, Anthropic, or any outside LLM or API, no API keys, and no environment variables. Nothing the visitor types leaves the browser.

## Supported categories

- Project Overview
- For Civil Engineers
- Brookside Meadows Demo
- Review Workflow
- Evidence & Documents
- Technical Implementation
- Developer & Source Code

## Conversation behavior

The panel keeps a conversation thread. Each question the visitor sends stays visible as a message, the matching answer appears beneath it, exchanges accumulate instead of replacing each other, and the thread scrolls to the newest answer automatically. A clear conversation control resets the thread. Typed questions are scored against every topic's keyword list, with multi-word phrases weighted higher, and the best-scoring topic answers; the safety scope check always runs first.

## Suggested questions

1. What does Civil Engineer AI help reviewers do?
2. How does the Brookside Meadows demo work?
3. I would like to know more about the developer of this project.

## Scope limitations and fallback behavior

The guide only answers from its pre-written project content. Questions it cannot match return a fallback that names what the guide can help with and states that it does not have enough project-specific information to answer.

Questions that ask for real engineering decisions receive a stronger scoped response instead: the guide cannot provide engineering, permitting, legal, or code-compliance advice, and final engineering decisions remain under qualified human review. This covers questions like whether a subdivision can move forward, detention basin sizing, code questions, use on a real project, or whether the AI replaces a civil engineer.

## Developer links included

- LinkedIn: http://linkedin.com/in/mpalmer1234
- GitHub: https://www.github.com/mpalmer79
- Project Repository: https://www.github.com/mpalmer79/civil-engineer

## Tests

`components/__tests__/CivilEngineerAIGuide.test.tsx` covers the launcher, panel accessibility, category chips, the exact suggested questions, the developer answer and links, route links resolving to real route directories, keyword matching, the fallback, the safety-scoped response, and source hygiene (no external API calls, no banned capability claims, no em dashes).
