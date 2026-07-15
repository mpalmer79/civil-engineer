"""CAD intake exception type and parser and limitation constants.

Single source of truth for the parser identity (name and version) and the
review-support limitation notes shared across the CAD intake submodules. These
notes state plainly that DXF metadata extraction is for review support only and
does not verify CAD, validate design, certify compliance, or replace a licensed
Professional Engineer.
"""

from __future__ import annotations

import ezdxf

PARSER_NAME = "ezdxf"
PARSER_VERSION = ezdxf.__version__

LIMITATIONS_NOTE = (
    "DXF metadata extraction for review support only. It does not verify CAD, "
    "validate geometry or design, certify compliance, stamp drawings, or "
    "replace a licensed Professional Engineer."
)

CONTEXT_NOTE = (
    "This is extracted DXF review-support metadata, not a verification or "
    "validation of the CAD file or the design."
)


class CadIntakeError(Exception):
    """Raised when a CAD intake operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
