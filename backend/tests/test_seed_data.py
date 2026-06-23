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


def test_projects_list_contains_only_brookside(client: TestClient) -> None:
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 1
    assert projects[0]["project_id"] == PROJECT_ID
