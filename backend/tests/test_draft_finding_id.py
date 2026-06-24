"""Unit tests for explicit draft finding id composition (gap 5)."""

from __future__ import annotations

from app.services.ai_review_service import _make_draft_finding_id


def test_draft_finding_id_format() -> None:
    # The historical format is draft_<run token>_<checklist item id>, where the
    # run token is the run id without its "airun_" prefix.
    assert (
        _make_draft_finding_id("airun_abc12345", "chk_infiltration_testing")
        == "draft_abc12345_chk_infiltration_testing"
    )


def test_draft_finding_id_matches_prior_slice_behavior() -> None:
    # Pin equivalence with the prior hardcoded slice (review_run_id[6:]) for the
    # current "airun_" prefix, so no stored reference or test breaks.
    run_id = "airun_deadbeef"
    checklist_item_id = "chk_downstream_capacity"
    assert _make_draft_finding_id(run_id, checklist_item_id) == (
        f"draft_{run_id[6:]}_{checklist_item_id}"
    )


def test_draft_finding_id_does_not_depend_on_slice_offset() -> None:
    # If the run id prefix scheme changed length, the helper strips the named
    # prefix rather than a fixed offset. A run id without the known prefix is
    # used verbatim as the token.
    assert (
        _make_draft_finding_id("run-2024_x", "chk_oem_owner")
        == "draft_run-2024_x_chk_oem_owner"
    )
