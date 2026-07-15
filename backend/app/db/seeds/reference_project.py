"""Brookside Meadows reference-project constants for the seed fixture.

Brookside Meadows is a fictional project used for a portfolio demonstration.
All people, firms, documents, and values are synthetic, and the package
contains intentional gaps and conflicts so the review-support system has
concrete work to surface. The values mirror the Phase 1 TypeScript seed data
under the repository data folder.

Do not change the core fixture facts: 38.5 acres, 47 lots, 22 disturbed acres,
19 documents, 19 checklist items, 10 planted review issues, 8 evaluation cases.
"""

from __future__ import annotations

from datetime import datetime

PROJECT_ID = "proj_brookside_meadows"


def _dt(value: str) -> datetime:
    """Parse an ISO 8601 timestamp, accepting a trailing Z for UTC."""

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


PROJECT = {
    "project_id": PROJECT_ID,
    "project_name": "Brookside Meadows Residential Subdivision",
    "project_type": "Residential subdivision",
    "location_context": (
        "Suburban-to-rural fringe parcel on the edge of an established "
        "neighborhood"
    ),
    "jurisdiction": "Town of Hartwell",
    "review_type": (
        "Subdivision and site plan with post-construction stormwater review"
    ),
    "review_domain": "stormwater",
    "acreage": 38.5,
    "disturbed_area": 22.0,
    "proposed_lots": 47,
    "status": "ready_for_review",
    "summary": (
        "A regional homebuilder has proposed Brookside Meadows: a 47-lot "
        "single-family subdivision on a 38.5-acre former farm parcel at the "
        "edge of an established neighborhood in the Town of Hartwell. The site "
        "falls from a wooded upland in the northwest toward an intermittent "
        "stream and a wetland buffer along the southeast property line, where "
        "runoff currently sheet-flows to an existing culvert under Quarry Road. "
        "The applicant proposes a mix of green infrastructure (bioretention and "
        "an infiltration basin) and conventional gray infrastructure (a wet "
        "detention basin and a piped storm drain network). The Town Engineer "
        "must review the package for completeness and technical adequacy before "
        "the Planning Board acts."
    ),
    "site_conditions": [
        {
            "type": "soils",
            "label": "Mixed soil conditions",
            "description": (
                "Hydrologic soil groups B and C with a band of slower-draining "
                "C/D soils and a possible restrictive layer in the lower "
                "meadow. Infiltration feasibility varies sharply across the "
                "site."
            ),
        },
        {
            "type": "groundwater",
            "label": "Seasonal high groundwater",
            "description": (
                "Soils report notes seasonal high groundwater within about 2.5 "
                "to 3.5 ft of existing grade in the low southeastern portion of "
                "the site, directly relevant to infiltration and bioretention "
                "separation."
            ),
        },
        {
            "type": "wetland_buffer",
            "label": "Wetland buffer",
            "description": (
                "A delineated wetland fringes Brook Run along the southeast "
                "boundary. The town applies a 100-ft buffer near several "
                "proposed grading and outfall features."
            ),
        },
        {
            "type": "stream",
            "label": "Brook Run stream corridor",
            "description": (
                "An intermittent stream crosses the southeast corner and "
                "conveys site runoff toward the Quarry Road culvert. Existing "
                "condition is predominantly sheet flow and shallow concentrated "
                "flow."
            ),
        },
        {
            "type": "slope",
            "label": "Sloping terrain",
            "description": (
                "The site grades from about 412 ft in the northwest to about "
                "358 ft near the southeast corner, roughly 54 ft of fall, with "
                "steeper 8 to 15 percent slopes on the western wood line."
            ),
        },
        {
            "type": "downstream_structure",
            "label": "Quarry Road culvert",
            "description": (
                "Runoff leaves the site through an existing 36-inch reinforced "
                "concrete culvert under Quarry Road. Neighbors downstream have "
                "reported road-edge ponding in large storms."
            ),
        },
        {
            "type": "adjacent_use",
            "label": "Adjacent neighborhood",
            "description": (
                "An established neighborhood (Quarry Road Estates) abuts the "
                "south and east property lines. Abutters are sensitive to "
                "drainage changes, construction traffic, and tree clearing."
            ),
        },
    ],
    "proposed_improvements": [
        {
            "type": "detention_basin",
            "label": "Basin 1",
            "aliases": ["Pond A"],
            "description": (
                "Wet detention basin in the southeast low area providing "
                "peak-flow attenuation before the Quarry Road culvert outfall."
            ),
        },
        {
            "type": "infiltration_basin",
            "label": "Basin 2",
            "aliases": [],
            "description": (
                "Infiltration basin proposed in the meadow to reduce runoff "
                "volume and provide groundwater recharge. Feasibility hinges on "
                "infiltration testing and groundwater separation."
            ),
        },
        {
            "type": "bioretention",
            "label": "Bioretention Cells BR-1 / BR-2",
            "aliases": [],
            "description": (
                "Two roadside bioretention cells along Brookside Drive for "
                "water-quality treatment of road runoff."
            ),
        },
        {
            "type": "storm_drain",
            "label": "Storm Drain Network",
            "aliases": [],
            "description": (
                "Curb inlets, catch basins, and reinforced concrete or HDPE "
                "storm drain pipe conveying road runoff toward the management "
                "facilities."
            ),
        },
        {
            "type": "riprap_apron",
            "label": "Outlet Protection",
            "aliases": [],
            "description": (
                "Riprap aprons at the detention basin outlet and at the culvert "
                "headwall to control scour."
            ),
        },
    ],
    "known_constraints": [
        "Infiltration feasibility versus shallow seasonal high groundwater",
        "Downstream culvert capacity and reported road-edge ponding",
        "Wetland buffer encroachment near proposed outfalls and grading",
        "Phased clearing of about 22 acres on slopes draining to a stream",
        "Long-term maintenance ownership of shared green and gray facilities",
    ],
}
