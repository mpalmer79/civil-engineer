"""Storage and object storage configuration validation items.

Reports only whether each storage setting is configured, never its value.
Credentials are confirmed present or missing; they are never echoed. Raw file
system paths are never exposed. These checks describe configuration readiness
only and never approve a project, certify compliance, or validate design.
"""

from __future__ import annotations

from typing import Any

from app.core.config import Settings

from app.services.environment_validation_service._common import _item


def _storage_items(settings: Settings) -> list[dict[str, Any]]:
    provider = (settings.STORAGE_PROVIDER or "local").strip().lower()
    items = [
        _item(
            category="storage",
            key="STORAGE_PROVIDER",
            status="configured",
            severity="info",
            message=f"Storage provider '{provider}' is selected.",
            required=True,
            configured=True,
            public_hint=provider,
        )
    ]
    # LOCAL_STORAGE_DIR is reported as configured only. The raw path is never
    # exposed in diagnostics, so public_hint stays None.
    items.append(
        _item(
            category="storage",
            key="LOCAL_STORAGE_DIR",
            status="configured" if provider == "local" else "disabled",
            severity=(
                "warning"
                if provider == "local"
                else "info"
            ),
            message=(
                "Local development storage is selected. On a deployment without "
                "a mounted volume, uploaded files are not durable across "
                "redeploys."
                if provider == "local"
                else "Local storage is not the selected provider."
            ),
            required=False,
            configured=True,
            remediation_hint=(
                "For durable deployment storage, set STORAGE_PROVIDER=s3 and the "
                "object storage settings, or mount a persistent volume."
                if provider == "local"
                else None
            ),
        )
    )
    return items


def _object_storage_items(settings: Settings) -> list[dict[str, Any]]:
    provider = (settings.STORAGE_PROVIDER or "local").strip().lower()
    if provider != "s3":
        return [
            _item(
                category="object_storage",
                key="OBJECT_STORAGE",
                status="disabled",
                severity="info",
                message="Object storage is not the selected provider.",
                required=False,
                configured=False,
                public_hint="not_selected",
            )
        ]
    # Provider is s3. Report only whether each setting is configured, never the
    # value. Credentials are confirmed present or missing; they are never echoed.
    bucket_set = bool(settings.OBJECT_STORAGE_BUCKET)
    access_key_set = bool(settings.OBJECT_STORAGE_ACCESS_KEY_ID)
    secret_set = bool(settings.OBJECT_STORAGE_SECRET_ACCESS_KEY)
    missing = not (bucket_set and access_key_set and secret_set)
    items = [
        _item(
            category="object_storage",
            key="OBJECT_STORAGE_BUCKET",
            status="configured" if bucket_set else "missing_required",
            severity="info" if bucket_set else "critical",
            message=(
                "Object storage bucket is configured."
                if bucket_set
                else "Object storage bucket is not configured."
            ),
            required=True,
            configured=bucket_set,
            remediation_hint=(
                None
                if bucket_set
                else "Set OBJECT_STORAGE_BUCKET on the backend service."
            ),
        ),
        _item(
            category="object_storage",
            key="OBJECT_STORAGE_REGION",
            status="configured",
            severity="info",
            message="Object storage region is configured.",
            required=False,
            configured=bool(settings.OBJECT_STORAGE_REGION),
            public_hint=settings.OBJECT_STORAGE_REGION or None,
        ),
        _item(
            category="object_storage",
            key="OBJECT_STORAGE_ENDPOINT_URL",
            status="configured" if settings.OBJECT_STORAGE_ENDPOINT_URL else "missing_optional",
            severity="info",
            message=(
                "A custom object storage endpoint is configured."
                if settings.OBJECT_STORAGE_ENDPOINT_URL
                else "Using the default AWS S3 endpoint (no custom endpoint set)."
            ),
            required=False,
            configured=bool(settings.OBJECT_STORAGE_ENDPOINT_URL),
        ),
        _item(
            category="object_storage",
            key="OBJECT_STORAGE_ACCESS_KEY_ID",
            status="configured" if access_key_set else "missing_required",
            severity="info" if access_key_set else "critical",
            message=(
                "Object storage access key is configured."
                if access_key_set
                else "Object storage access key is not configured."
            ),
            required=True,
            configured=access_key_set,
            remediation_hint=(
                None
                if access_key_set
                else "Set OBJECT_STORAGE_ACCESS_KEY_ID on the backend service only."
            ),
        ),
        _item(
            category="object_storage",
            key="OBJECT_STORAGE_SECRET_ACCESS_KEY",
            status="configured" if secret_set else "missing_required",
            severity="info" if secret_set else "critical",
            message=(
                "Object storage secret access key is configured."
                if secret_set
                else "Object storage secret access key is not configured."
            ),
            required=True,
            configured=secret_set,
            remediation_hint=(
                None
                if secret_set
                else "Set OBJECT_STORAGE_SECRET_ACCESS_KEY on the backend service only."
            ),
        ),
        _item(
            category="object_storage",
            key="OBJECT_STORAGE_SIGNED_URL_EXPIRE_SECONDS",
            status="configured",
            severity="info",
            message="Signed URL expiry is configured.",
            required=False,
            configured=True,
            public_hint=str(settings.OBJECT_STORAGE_SIGNED_URL_EXPIRE_SECONDS),
        ),
    ]
    if missing:
        items.append(
            _item(
                category="object_storage",
                key="OBJECT_STORAGE",
                status="needs_operator_review",
                severity="critical",
                message=(
                    "Object storage is selected but one or more required "
                    "settings are missing."
                ),
                required=True,
                configured=False,
                remediation_hint=(
                    "Set the bucket, access key, and secret access key on the "
                    "backend service only."
                ),
            )
        )
    return items
