# Homepage Hotspot Plan

**Product:** Civil Engineer AI: Stormwater Review Assistant
**Asset:** `public/development.png`
**Status:** Phase 1 (static overlay) with a defined path to a fully interactive
development map.

## Purpose

The homepage hero image of Brookside Meadows is a **product feature, not
decoration.** It is the visual entry point to the review fixture and the
foundation of a future interactive development map. This plan defines ten
hotspot zones over the image, what each one means in civil-engineering terms,
how each connects to the seeded checklist items and planted review issues, and
how the interaction grows from a static overlay (Phase 1) to a drill-down map
(later phases).

The hotspot overlay is implemented with HTML/CSS markers positioned over the
image — never with text baked into the image — so it stays accessible,
responsive, and translatable.

## Base Image

- **File:** `public/development.png`
- **Subject:** An illustrative site map of the Brookside Meadows subdivision —
  wooded upland (northwest), former hay meadow (center/south), Brook Run and the
  wetland corridor (southeast), the Quarry Road culvert (downstream edge),
  internal roads and lots, and the stormwater facilities.
- **Aspect ratio:** Rendered in a `16 / 10` frame. The overlay uses
  percentage-based coordinates so it scales with the image at any width.
- **Fallback:** The hero frame has a land-to-water gradient background and a
  caption. If `development.png` is missing or fails to load, the layout and
  hotspot markers still render without breaking.

> **Asset note.** If `public/development.png` is not yet committed, add an
> illustrative subdivision site-map render at that path. The overlay coordinates
> below are visual estimates and should be fine-tuned against the final artwork.

## Interaction Model

Phase 1 uses **Option B: a side panel that updates on selection**, combined with
hover/focus activation, because it is the cleanest accessible pattern and keeps
the image uncluttered:

- Each hotspot is a numbered, circular **button** absolutely positioned over the
  image.
- Hovering, focusing, or clicking a marker updates a side panel (`aria-live`)
  with the hotspot name, category, short description, civil purpose, related
  review issues, and the planned future drill-down.
- Markers are color-coded by category and never cover the whole image.

## Hotspot Coordinate Strategy

- Coordinates are stored in `data/hotspots.ts` as `position.xPercent` /
  `position.yPercent`, measured from the **top-left** of the image.
- Percentages (not pixels) keep markers aligned across screen sizes.
- A code comment flags that final coordinates should be adjusted after viewing
  the deployed page against the real artwork.

## Hotspot Zones

Each zone below lists: visual location · civil purpose · related story element ·
related checklist items · related planted issues · future drill-down · Phase 1
behavior · future behavior.

### 1. Wet Detention Basin

- **Visual location:** Lower-right, southeast low area (~68%, ~72%).
- **Civil purpose:** Peak-flow attenuation and water-quality settling before
  discharge toward the Quarry Road culvert.
- **Story element:** Basin 1 — also labeled "Pond A" on the grading plan.
- **Checklist items:** `chk_bmp_identified`, `chk_outfall_identified`,
  `chk_reference_consistency`.
- **Planted issues:** I-9 (Pond A vs. Basin 1 naming conflict).
- **Future drill-down:** Basin sizing evidence, outfall details, and the naming
  conflict finding.
- **Phase 1 behavior:** Side-panel context with the naming-conflict tag.
- **Future behavior:** Click opens the basin's documents, checklist items, and
  findings.

### 2. Infiltration Basin / Meadow Basin

- **Visual location:** Center meadow (~52%, ~60%).
- **Civil purpose:** Runoff volume reduction and groundwater recharge;
  feasibility depends on infiltration testing and groundwater separation.
- **Story element:** Basin 2 in the lower meadow near shallow groundwater.
- **Checklist items:** `chk_infiltration_testing`, `chk_groundwater_separation`,
  `chk_soil_groundwater_doc`.
- **Planted issues:** I-2 (missing infiltration testing), I-3 (groundwater
  separation not addressed).
- **Future drill-down:** Infiltration testing evidence (missing) and the
  separation discussion.
- **Phase 1 behavior:** Side-panel context with two review-issue tags.
- **Future behavior:** Click links to the two related findings and the soils
  report.

### 3. Wetland Buffer and Stream Corridor

- **Visual location:** Southeast boundary (~80%, ~85%).
- **Civil purpose:** Protected resource area; outfalls and grading near the
  100-ft buffer require Conservation Commission coordination.
- **Story element:** Brook Run and the delineated wetland.
- **Checklist items:** `chk_outfall_identified`, `chk_downstream_capacity`.
- **Planted issues:** None directly (buffer is a known constraint).
- **Future drill-down:** Buffer encroachment review and receiving-water context.
- **Phase 1 behavior:** Side-panel context.
- **Future behavior:** Click surfaces buffer-related review notes and the
  Conservation Commission stakeholder.

### 4. Quarry Road Culvert

- **Visual location:** Downstream edge, far right (~90%, ~78%).
- **Civil purpose:** Existing 36-inch downstream conveyance structure with
  reported road-edge ponding.
- **Story element:** The downstream culvert capacity concern.
- **Checklist items:** `chk_downstream_capacity`.
- **Planted issues:** I-4 (downstream capacity not analyzed).
- **Future drill-down:** Downstream capacity analysis (missing) and ponding
  concern.
- **Phase 1 behavior:** Side-panel context with the I-4 tag.
- **Future behavior:** Click opens the downstream-capacity finding and hydraulic
  calculations.

### 5. Construction Entrance

- **Visual location:** Site entrance off Quarry Road (~84%, ~64%).
- **Civil purpose:** Stabilized construction entrance controlling tracked
  sediment.
- **Story element:** Construction access during phased build.
- **Checklist items:** `chk_erosion_controls`, `chk_escp_phasing`.
- **Planted issues:** None directly.
- **Future drill-down:** Erosion & sediment control plan and sequencing.
- **Phase 1 behavior:** Side-panel context.
- **Future behavior:** Click links to the E&SC plan and phasing plan.

### 6. Erosion Control Perimeter

- **Visual location:** Downhill limits of disturbance (~40%, ~78%).
- **Civil purpose:** Perimeter sediment control during phased clearing on slopes
  draining to Brook Run.
- **Story element:** Silt fence and perimeter controls near the buffer.
- **Checklist items:** `chk_erosion_controls`, `chk_escp_phasing`.
- **Planted issues:** I-6 (E&SC sequencing not tied to phasing).
- **Future drill-down:** The E&SC phasing finding and stabilization timing.
- **Phase 1 behavior:** Side-panel context with the I-6 tag.
- **Future behavior:** Click opens the phasing finding.

### 7. Loop Road Subdivision Lots

- **Visual location:** Upland north/center (~35%, ~38%).
- **Civil purpose:** Primary residential area adding impervious runoff to the
  storm drain network.
- **Story element:** Upland lots on the loop road.
- **Checklist items:** `chk_drainage_areas`, `chk_runoff_calcs`.
- **Planted issues:** None directly.
- **Future drill-down:** Drainage-area mapping and runoff calculations.
- **Phase 1 behavior:** Side-panel context.
- **Future behavior:** Click links to drainage areas and runoff calcs.

### 8. Cul-de-Sac Lower Lots

- **Visual location:** Lower-center near the buffer (~62%, ~50%).
- **Civil purpose:** Lower-elevation lots sensitive to groundwater and buffer
  proximity.
- **Story element:** Meadow Court cul-de-sac lots.
- **Checklist items:** `chk_groundwater_separation`, `chk_drainage_areas`.
- **Planted issues:** I-3 (groundwater separation).
- **Future drill-down:** Groundwater separation context and lower-lot grading.
- **Phase 1 behavior:** Side-panel context with the I-3 tag.
- **Future behavior:** Click links to the separation finding.

### 9. Utility / Pump Station Area

- **Visual location:** Center-north (~58%, ~30%).
- **Civil purpose:** Water main, gravity sewer, and a sanitary pump station;
  storm-drain and buffer crossings are future coordination points.
- **Story element:** Utility extensions serving the low lots.
- **Checklist items:** `chk_rfi_closure`.
- **Planted issues:** I-8 (open pipe-material RFI).
- **Future drill-down:** The open RFI and utility / storm crossing coordination.
- **Phase 1 behavior:** Side-panel context with the I-8 tag.
- **Future behavior:** Click opens the RFI log and the related finding.

### 10. Planted Review Issue Locations

- **Visual location:** Left-center summary marker (~22%, ~60%).
- **Civil purpose:** Demonstration overlay linking map locations to the ten
  expected review-support findings.
- **Story element:** The full set of planted issues across the package.
- **Checklist items:** The high-risk and completeness items spanning the issues.
- **Planted issues:** I-1 through I-10.
- **Future drill-down:** The full findings list with map-linked evidence and
  human review status.
- **Phase 1 behavior:** Side-panel context listing all ten issue tags.
- **Future behavior:** Click opens the findings page filtered to map-linked
  evidence.

## Phase 1 Static Behavior

- Ten numbered markers render over the image from `data/hotspots.ts`.
- Hover, focus, or click updates the side panel; the first hotspot is selected
  by default so the panel is never empty.
- No navigation occurs on click in Phase 1 — the panel is the interaction.
- Markers are color-coded by category and sized to avoid clutter.

## Future Interactive Behavior

- Clicking a marker deep-links to the relevant documents, checklist items, and
  findings.
- Markers reflect live status (e.g., a red ring when an open high-risk finding
  is attached).
- A category filter toggles marker groups (stormwater, wetland, erosion control,
  utility, lots, risk).
- Coordinates become data-driven from real geospatial references in later
  phases.

## Accessibility Requirements

- Each hotspot is a real `<button>` with a descriptive `aria-label`
  ("Hotspot 2: Infiltration basin (Basin 2)") and `aria-pressed` state.
- The side panel uses `aria-live="polite"` so updates are announced.
- Activation works via mouse hover, keyboard focus (Tab), and click/Enter.
- The base image has meaningful, descriptive alt text.
- Color is never the only signal — every marker has a number and the panel
  carries the full text. Risk tags include text labels, not just color.

## Implementation Notes

- Data model: `data/hotspots.ts` (`Hotspot` type with `id`, `name`, `category`,
  `shortDescription`, `civilPurpose`, `relatedChecklistItems`,
  `relatedPlantedIssues`, `futureDrilldown`, and `position`).
- Components: `components/HeroMap.tsx` (client component holding selection
  state) and `components/HotspotMarker.tsx` (presentational button).
- Keep the overlay percentage-based; re-measure coordinates after the final
  `development.png` is in place.
- Do not embed hotspot text in the image; the overlay must remain HTML/CSS.
