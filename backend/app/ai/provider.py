"""AI provider abstraction.

The default provider is the deterministic mock, so the project runs and tests
pass without any paid API key. A live provider is only selected when a provider
is configured, live calls are explicitly enabled, and an API key is present.
"""

from __future__ import annotations

from typing import Protocol

from app.core.config import Settings

# Providers with a real, live implementation in this repository. Anthropic is
# intentionally not listed: there is no live Anthropic provider yet, so the repo
# must not imply that one is live-ready. Add it here only when a real provider
# implementation exists.
LIVE_READY_PROVIDERS: set[str] = {"openai"}


class AIProvider(Protocol):
    name: str
    model_name: str

    def generate_finding(
        self,
        *,
        project: dict,
        checklist_item: dict,
        evidence: list[dict],
        prompt: str,
    ) -> dict | None:
        """Return a raw draft finding dict, or None if no finding is produced."""
        ...


def describe_provider_mode(settings: Settings) -> dict:
    """Return a small, non-sensitive description of the provider mode for the UI.

    Only OpenAI has a real live provider implementation. The mock provider is
    the default and is used whenever a live provider is not fully configured.
    """

    provider = settings.AI_PROVIDER.lower()
    live_ready = (
        provider in LIVE_READY_PROVIDERS
        and settings.AI_ENABLE_LIVE_CALLS
        and bool(_key_for(provider, settings))
    )
    if provider == "mock":
        mode = "mock"
        detail = "Deterministic mock provider. No external calls."
    elif live_ready:
        mode = "live"
        detail = f"Live provider enabled: {provider}."
    else:
        mode = "live_disabled"
        detail = (
            f"Provider '{provider}' selected, but live calls are disabled, no "
            "API key is configured, or no live implementation exists. Using the "
            "mock provider."
        )
    return {
        "provider": provider,
        "mode": mode,
        "model_name": settings.AI_MODEL,
        "live_calls_enabled": settings.AI_ENABLE_LIVE_CALLS,
        "detail": detail,
    }


def _key_for(provider: str, settings: Settings) -> str:
    if provider == "openai":
        return settings.OPENAI_API_KEY
    return ""


def get_provider(settings: Settings) -> AIProvider:
    """Return the configured provider, falling back to the mock provider.

    The mock provider is returned unless a live provider is fully configured
    (provider selected, live calls enabled, and an API key present). This keeps
    the demo and tests working without any paid API key.
    """

    from app.ai.mock_provider import MockProvider

    provider = settings.AI_PROVIDER.lower()
    if (
        provider in LIVE_READY_PROVIDERS
        and settings.AI_ENABLE_LIVE_CALLS
        and _key_for(provider, settings)
    ):
        try:
            from app.ai.openai_provider import OpenAIProvider

            if provider == "openai":
                return OpenAIProvider(
                    model_name=settings.AI_MODEL,
                    api_key=settings.OPENAI_API_KEY,
                )
        except Exception:
            # Any import or setup failure falls back to the mock provider so the
            # service never crashes due to provider configuration.
            return MockProvider(model_name=settings.AI_MODEL)

    return MockProvider(model_name=settings.AI_MODEL)
