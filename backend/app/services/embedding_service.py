"""Deterministic, local embedding service for chunk semantic retrieval.

This service produces a fixed-dimension vector for a piece of text using a local,
deterministic concept-lexicon model. It does not call any external provider, does
not require API keys, and never runs in or reaches frontend code. Embeddings are
review-support signals for ranking candidates, never conclusions.

Why a local concept model: it gives semantic-style recall (a query about a
"stormwater pond" can surface a chunk about a "detention basin" through a shared
concept dimension) while staying fully deterministic and dependency-free, which
fits this repository's constraints. It is not a learned model and is not a
substitute for a real embedding model at production scale; the abstraction below
(provider, model, version, dimension) is designed so a real provider can be added
later behind configuration without changing callers.
"""

from __future__ import annotations

import hashlib
import math
import re

# Embedding model identity. model_version is bumped whenever the vector math or
# the concept lexicon changes, so stored vectors can be detected as stale and
# re-embedded.
EMBEDDING_PROVIDER = "local_concept"
EMBEDDING_MODEL = "concept-lexicon"
EMBEDDING_MODEL_VERSION = "1"

# Concept groups. Each group is one vector dimension. A token that appears in a
# group activates that group's dimension, so texts that share a concept have a
# non-zero cosine similarity even with no shared tokens. Terms are single,
# lowercased tokens (multi-word ideas are represented by their component tokens).
_CONCEPTS: tuple[tuple[str, frozenset[str]], ...] = (
    (
        "impoundment",
        frozenset(
            {"basin", "detention", "retention", "pond", "impoundment", "reservoir"}
        ),
    ),
    (
        "infiltration",
        frozenset(
            {"infiltration", "infiltrate", "percolation", "drawdown", "recharge"}
        ),
    ),
    (
        "erosion",
        frozenset({"erosion", "sediment", "sedimentation", "silt", "swppp"}),
    ),
    (
        "conveyance",
        frozenset(
            {"culvert", "pipe", "swale", "channel", "ditch", "conveyance",
             "outfall", "outlet"}
        ),
    ),
    (
        "grading",
        frozenset(
            {"grading", "grade", "slope", "cut", "fill", "earthwork", "topography"}
        ),
    ),
    (
        "water_quality",
        frozenset(
            {"quality", "pollutant", "treatment", "bmp", "filtration",
             "bioretention"}
        ),
    ),
    (
        "flooding",
        frozenset({"flood", "floodplain", "overflow", "inundation"}),
    ),
    (
        "runoff",
        frozenset(
            {"runoff", "discharge", "flow", "hydrology", "hydraulic",
             "stormwater", "drainage"}
        ),
    ),
    (
        "easement",
        frozenset({"easement", "setback", "buffer"}),
    ),
)

# Generic hashed token dimensions preserve an exact-term signal alongside the
# concept dimensions, so exact keyword overlap still raises similarity.
_HASH_DIMS = 64
_CONCEPT_WEIGHT = 1.0
_TOKEN_WEIGHT = 0.5

EMBEDDING_DIMENSION = len(_CONCEPTS) + _HASH_DIMS


class EmbeddingError(Exception):
    """Raised when text cannot be embedded (for example empty content)."""

    def __init__(self, message: str, *, status_code: int = 422) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def embedding_metadata() -> dict:
    """Return the active embedding identity (no secrets)."""

    return {
        "provider": EMBEDDING_PROVIDER,
        "model_name": EMBEDDING_MODEL,
        "model_version": EMBEDDING_MODEL_VERSION,
        "dimension": EMBEDDING_DIMENSION,
    }


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) >= 3]


def _stable_bucket(token: str) -> int:
    """Deterministic hash bucket for a token (process-independent)."""

    digest = hashlib.md5(token.encode("utf-8")).hexdigest()
    return int(digest, 16) % _HASH_DIMS


def content_hash(text: str) -> str:
    """Stable content hash used to detect when a chunk needs re-embedding."""

    normalized = " ".join((text or "").split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def embed_text(text: str) -> list[float]:
    """Return an L2-normalized embedding vector for text.

    Raises EmbeddingError when the text has no embeddable tokens, so empty or
    whitespace-only content is never embedded.
    """

    tokens = _tokens(text or "")
    if not tokens:
        raise EmbeddingError("Cannot embed empty or non-text content.")

    vector = [0.0] * EMBEDDING_DIMENSION
    for token in tokens:
        for index, (_name, terms) in enumerate(_CONCEPTS):
            if token in terms:
                vector[index] += _CONCEPT_WEIGHT
        bucket = len(_CONCEPTS) + _stable_bucket(token)
        vector[bucket] += _TOKEN_WEIGHT

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        raise EmbeddingError("Embedding produced a zero vector.")
    return [value / norm for value in vector]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity for two equal-length vectors, bounded to [-1, 1]."""

    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm_a * norm_b)))
