"""Optional live OpenAI provider.

This provider is only used when a live provider is fully configured (see
get_provider in provider.py). It is intentionally minimal and defensive: it
lazily imports the openai package, requests JSON output, and returns the parsed
dict. Any failure returns None so the service records a validation failure
rather than crashing. The openai package is not a required dependency; install
it only if you intend to use live calls.

Setup (optional):
    pip install openai
    export AI_PROVIDER=openai
    export AI_ENABLE_LIVE_CALLS=true
    export OPENAI_API_KEY=...   # never commit this
    export AI_MODEL=gpt-4o-mini
"""

from __future__ import annotations

import json


class OpenAIProvider:
    name = "openai"

    def __init__(self, *, model_name: str, api_key: str) -> None:
        self.model_name = model_name
        self._api_key = api_key

    def generate_finding(
        self,
        *,
        project: dict,
        checklist_item: dict,
        evidence: list[dict],
        prompt: str,
    ) -> dict | None:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self._api_key)
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a constrained stormwater review-support "
                            "assistant. Return only valid JSON. You do not "
                            "approve plans or certify compliance."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            content = response.choices[0].message.content
            if not content:
                return None
            return json.loads(content)
        except Exception:
            # Network, auth, parse, or missing-package failures fall through to a
            # validation failure recorded by the service.
            return None
