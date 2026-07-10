# Civil Engineer AI: SaaS Transition Roadmap

From portfolio piece to a product that can start sales conversations.

---

## Implementation reality note

For the canonical, code-checked statement of what is implemented today (real DXF
parsing with ezdxf, PDF text-layer indexing with pypdf, and what is not: DWG,
GIS, OCR, computer vision, vector search, live AI by default), see the
"Implementation reality" section of `docs/SAAS_POSITIONING.md`. Where this
roadmap describes the DXF-parse-to-findings flow as real, that is accurate. The
sales framing in this document (for example "pass review the first time") is
aspirational positioning language, not a product guarantee; public copy stays
review-support only and makes no approval, certification, or pass-review promise.

---

## The core diagnosis

The codebase is strong. The positioning is not. Right now the homepage sells caution, not capability, and that is the entire reason the "wow" is missing.

Count what dominates the current landing page: "review-support" (everywhere), "does not approve / certify / verify / validate," two separate safety boundary banners, "live AI calls disabled by default," and a literal "Hero visual placeholder." Every confident claim is immediately walked back. That defensive framing is exactly right for a portfolio piece making a professional-boundary argument. It is the opposite of what a SaaS landing page does. A buyer skimming this learns six times what the product will not do before they understand the one painful thing it does for them.

"Wow" for this buyer is not a WebGL hero. It is "this caught what my junior reviewer would have missed, in thirty seconds." The single most impressive thing the product does, parse a real DXF and surface findings with page-level evidence traceability, is currently buried as the seventh link in a list labeled "CAD Intake (DXF)."

The fix is sequenced below. Positioning first, because building polish on top of the wrong message just makes the wrong message shinier.

---

## Buyer decision: lead with AEC firms, not municipalities

Sell to civil/AEC firms doing internal QA first. Treat municipal review departments as phase-two expansion.

Why AEC firms are the better first customer:

1. They feel the pain commercially. Every missed item in a review round costs them a resubmittal cycle, which is real schedule slip and real money. That is a P&L argument, not a workflow-improvement argument.
2. They can actually buy. Credit card or short procurement, no public RFP, no annual budget cycle, no year-plus sales motion.
3. The value proposition is sharper. A firm runs your tool on its own submission before sending it, catches the findings a municipal reviewer would catch, and passes review the first time. "Pass review the first time" is a cleaner sell than asking an under-resourced municipal office to change how it works.

Why municipalities wait:

Gov procurement is slow, price-sensitive, and risk-averse toward a solo founder with a pre-revenue product. You would burn 18 months to land one logo. But once you have AEC logos, the gov intro becomes the warmest possible pitch: "the firms submitting to your office already run this before they send it to you."

Your own background reinforces the AEC-first call. Twenty-five years inside regulated retail compliance means you already know how to sell "avoid the costly rejection" to an operations buyer. That is the same muscle.

One naming note for later: the product is currently honest that it does metadata extraction, not geometry validation or compliance certification. Keep that honesty. The AEC pitch does not require overclaiming. "Catch the issues that get submissions kicked back" is true today and is enough.

---

## Phase 0: Reframe the message (days, not weeks)

No new features. Rewrite what the product says about itself. This is the highest-leverage work and it is almost free.

- Replace the headline. Kill "A document-first, evidence-first, reviewer-controlled stormwater review-support platform." Four hedged adjectives is not a value proposition. Replace with an outcome aimed at AEC firms, for example: "Catch the stormwater review issues that get your submissions kicked back, before you submit." (Wording is yours; the shape is outcome plus buyer plus pain.)
- Lead the hero with the product working, not a placeholder. The DXF-parse-to-findings flow is the hero. Show it.
- Demote the boundary language. Keep it (it is a genuine credibility asset and legally smart), but move it below the fold into a "How we keep a human responsible" section. It should reassure after interest, not suppress interest before it forms.
- Collapse the two safety banners into one.
- Cut the feature-list homepage. Eight workflow cards plus six foundation cards plus six metric cards is a documentation index, not a sales page. Pick the three capabilities that matter to an AEC buyer (DXF intake and findings, evidence traceability, resubmittal comparison) and let everything else live one click deeper.

Deliverable for this phase: a rewritten `app/page.tsx` and a one-page positioning statement. This is a single focused working session.

---

## Phase 1: Build the one demo that sells (1 to 2 weeks)

A prospect should be able to experience the wow without a sales call, because the conversion goal is "credible enough to start conversations," and a self-running demo is what makes someone reply to your outreach.

- Make the DXF-upload-to-findings path the front door. From the homepage, one click to a live demo that runs on the Brookside Meadows fixture, no login. Visitor watches a real file get parsed and findings appear with page-level citations.
- Add a single "wow" moment: a before/after or a counter ("17 review-support findings surfaced in 12 seconds"). Honest, specific, fixture-backed. This is where your ShipDay instinct for cinematic framing pays off, applied with restraint.
- Instrument it. Even basic analytics on "started demo / completed demo / clicked contact" tells you whether the message works before you spend on outreach.

Deliverable: a public, no-auth guided demo reachable in one click from the hero, plus event tracking.

---

## Phase 2: Multi-tenant foundations (3 to 5 weeks)

Only now does it become software someone can pay for. The codebase already has organizations and role-based access, which is most of the hard part. Verify and harden rather than rebuild.

- Confirm true tenant isolation. Every query scoped by org, no cross-tenant leakage. This is the thing that ends a B2B deal if it fails, so test it explicitly.
- Move off SQLite to Postgres for production (the docs already anticipate this).
- Real authentication and account lifecycle: sign up, invite teammates, password reset.
- A minimal billing integration (Stripe). Even a single paid tier is enough to take money.
- Turn on the live AI calls behind a real key and a usage guard, since "live AI calls disabled by default" cannot ship as the production posture of an AI product.

Deliverable: a deployed, multi-tenant instance where a new firm can sign up, invite a colleague, run a review, and be billed.

---

## Phase 3: First customers and proof (ongoing, starts during Phase 2)

Do not wait for the product to be finished to start selling. Start now with the demo from Phase 1.

- Line up three to five design-partner firms. Free or near-free in exchange for real usage and a quote. Your CADNET interview and any NH AEC contacts are the warm start.
- Run their real DXF files. The product parses real files today; that is your unfair advantage over a slide deck.
- Convert one design partner into one paying logo and one written case study. That single case study is what makes the next ten conversations easy, and it is what makes the eventual municipal pitch land.

Deliverable: one paying customer and one case study. That is the threshold where this stops being a portfolio piece and becomes a company, however small.

---

## What to deliberately NOT do

- Do not build geometry validation or compliance certification. It is a different, far harder, far more liable product. The metadata-extraction scope is defensible and shippable. Stay in it.
- Do not chase municipalities yet. Note inbound interest, do not pursue it.
- Do not add a WebGL hero or a 3D scene. Wrong wow for this buyer. The wow is the parse, not the chrome.
- Do not expand the feature surface. You have more features than message already. Sharpen, do not add.

---

## Sequenced summary

| Phase | Focus | Output | Rough effort |
|---|---|---|---|
| 0 | Reframe the message | Rewritten homepage + positioning statement | Days |
| 1 | Build the one demo that sells | Public no-auth guided demo + analytics | 1 to 2 weeks |
| 2 | Multi-tenant foundations | Postgres, auth, billing, tenant isolation, live AI | 3 to 5 weeks |
| 3 | First customers and proof | One paying logo + one case study | Ongoing, start in P2 |

The dependency that matters: Phase 0 is free and unlocks everything else. Do it this week. Everything downstream gets easier once the product stops apologizing for itself on the first screen.
