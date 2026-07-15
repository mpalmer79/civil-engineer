"""Accumulator for sections, items, links, and attachments during generation."""

from __future__ import annotations

from app.db import models

from ._common import SECTION_TITLES, _short


class _Builder:
    """Accumulates sections, items, links, and attachments during generation."""

    def __init__(self, response_package_id: str, project_id: str) -> None:
        self.response_package_id = response_package_id
        self.project_id = project_id
        self.sections: list[models.ResponsePackageSection] = []
        self.items: list[models.ResponsePackageItem] = []
        self.links: list[models.ResponsePackageEvidenceLink] = []
        self.attachments: list[models.ResponsePackageAttachment] = []
        self._order = 0

    def section(
        self,
        section_type: str,
        summary: str,
        *,
        requires_human_review: bool = True,
    ) -> str:
        section_id = f"rsec_{_short()}"
        self.sections.append(
            models.ResponsePackageSection(
                section_id=section_id,
                response_package_id=self.response_package_id,
                title=SECTION_TITLES[section_type],
                section_type=section_type,
                display_order=self._order,
                summary=summary,
                status="draft",
                requires_human_review=requires_human_review,
            )
        )
        self._order += 1
        return section_id

    def item(
        self,
        section_id: str,
        *,
        title: str,
        draft_text: str,
        severity: str,
        source_type: str,
        source_id: str | None,
        assigned_role: str,
        workflow_item_id: str | None = None,
        packet_item_id: str | None = None,
        requires_human_review: bool = True,
        links: list[tuple[str, str, str, str, str | None]] | None = None,
    ) -> None:
        item_id = f"ritem_{_short()}"
        self.items.append(
            models.ResponsePackageItem(
                item_id=item_id,
                response_package_id=self.response_package_id,
                section_id=section_id,
                workflow_item_id=workflow_item_id,
                packet_item_id=packet_item_id,
                title=title,
                draft_text=draft_text,
                reviewer_note=None,
                severity=severity,
                status="draft",
                source_type=source_type,
                source_id=source_id,
                assigned_role=assigned_role,
                requires_human_review=requires_human_review,
                display_order=len(self.items),
            )
        )
        for evidence_type, evidence_id, relationship, label, description in links or []:
            if not evidence_id:
                continue
            self.links.append(
                models.ResponsePackageEvidenceLink(
                    evidence_link_id=f"revl_{_short()}",
                    response_package_id=self.response_package_id,
                    response_item_id=item_id,
                    evidence_type=evidence_type,
                    evidence_id=evidence_id,
                    relationship=relationship,
                    label=label,
                    description=description,
                )
            )

    def attachment(
        self,
        *,
        label: str,
        attachment_type: str,
        source_type: str,
        source_id: str | None,
        description: str | None,
    ) -> None:
        self.attachments.append(
            models.ResponsePackageAttachment(
                attachment_id=f"ratt_{_short()}",
                response_package_id=self.response_package_id,
                label=label,
                attachment_type=attachment_type,
                source_type=source_type,
                source_id=source_id,
                included=True,
                description=description,
                display_order=len(self.attachments),
            )
        )
