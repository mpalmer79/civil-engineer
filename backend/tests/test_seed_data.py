"""Seed data loading tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

PROJECT_ID = "proj_brookside_meadows"


def test_seed_loads_brookside_meadows(client: TestClient) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}")
    assert response.status_code == 200
    project = response.json()
    assert project["project_name"] == "Brookside Meadows Residential Subdivision"
    assert project["acreage"] == 38.5
    assert project["proposed_lots"] == 47
    assert project["disturbed_area"] == 22.0
    assert project["jurisdiction"] == "Town of Hartwell"
    assert len(project["site_conditions"]) == 7
    assert len(project["proposed_improvements"]) == 5
    assert len(project["known_constraints"]) == 5


def test_projects_list_contains_brookside_demo_fixture(
    client: TestClient,
) -> None:
    # Brookside Meadows is the single seeded demo fixture. Real, user-created
    # project records may also exist in the shared test database, so filter to
    # the demo fixture source mode to assert the seeded baseline is intact.
    response = client.get("/api/v1/projects", params={"source_mode": "demo_fixture"})
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 1
    assert projects[0]["project_id"] == PROJECT_ID
    assert projects[0]["source_mode"] == "demo_fixture"

    # The unfiltered list always includes the seeded demo fixture.
    all_projects = client.get("/api/v1/projects").json()
    assert any(p["project_id"] == PROJECT_ID for p in all_projects)


def test_seed_facades_reexport_the_seeds_package() -> None:
    # The legacy seed module paths are thin facades over the app.db.seeds
    # package. They must expose the same objects so both import paths stay
    # interchangeable.
    from app.db import seed, seed_evidence, seed_plansheets, seeds

    assert seed.PROJECT_ID == seeds.PROJECT_ID == PROJECT_ID
    assert seed.seed_database is seeds.seed_database
    assert seed.DOCUMENTS is seeds.DOCUMENTS
    assert seed.CHECKLIST is seeds.CHECKLIST
    assert seed.FINDINGS is seeds.FINDINGS
    assert seed_evidence.seed_evidence is seeds.seed_evidence
    assert seed_evidence.CHUNKS is seeds.CHUNKS
    assert seed_evidence.FINDING_SOURCES is seeds.FINDING_SOURCES
    assert seed_plansheets.seed_plansheets is seeds.seed_plansheets
    assert seed_plansheets.PROJECT_ID == PROJECT_ID
    assert seed_plansheets.PLAN_SHEETS is seeds.PLAN_SHEETS


def test_public_demo_project_id_defaults_to_seeded_fixture(
    client: TestClient,
) -> None:
    # The public demo project id is configurable, and its default must match
    # the seeded reference project so the startup auth seed marks Brookside
    # Meadows as the public demo.
    from app.core.config import get_settings
    from app.db import models
    from app.db.database import SessionLocal

    assert get_settings().PUBLIC_DEMO_PROJECT_ID == PROJECT_ID

    db = SessionLocal()
    try:
        project = db.get(models.Project, PROJECT_ID)
        assert project is not None
        assert project.demo_public is True
        assert project.visibility_mode == "demo_public"
    finally:
        db.close()
