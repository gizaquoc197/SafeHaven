"""OutputFilter implementation — sanitize LLM responses."""

from __future__ import annotations

import re

from safehaven.models import RiskLevel

_EMPATHETIC_PREFIX = (
    "It sounds like you're going through a tough time, "
    "and your feelings are completely valid.\n\n"
)

# Patterns that should be stripped from any LLM output
_DANGEROUS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b\d+\s*(?:mg|milligrams?)\b", re.IGNORECASE),
    re.compile(r"(?:how to|method|way to)\s+(?:harm|hurt|kill|end)", re.IGNORECASE),
    re.compile(r"(?:step[- ]by[- ]step|instructions?).*(?:suicide|self[- ]harm)", re.IGNORECASE),
]


class SafeOutputFilter:
    """Sanitize LLM output based on current risk level."""

    def validate(self, response: str, risk: RiskLevel) -> str:
        """Sanitize LLM output based on current risk level.

        - Strip lines matching dangerous patterns.
        - At MEDIUM risk, prepend empathetic framing.
        - At LOW risk, return as-is.
        """
        # Strip dangerous lines
        lines = response.splitlines(keepends=True)
        safe_lines: list[str] = []
        for line in lines:
            if any(pat.search(line) for pat in _DANGEROUS_PATTERNS):
                continue
            safe_lines.append(line)
        cleaned = "".join(safe_lines).strip()

        if risk == RiskLevel.MEDIUM:
            return _EMPATHETIC_PREFIX + cleaned

        return cleaned
