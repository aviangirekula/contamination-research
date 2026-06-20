"""Regex PII detectors for the leakage analysis (Enron-in-Pile subset only).

ETHICS: this module is used *only* on the Enron Emails subset of The Pile -- a
public corpus already in Pythia's training data -- and only for aggregate
counts/rates. It must never be used to target real individuals, and callers must
never print matched PII strings. The detectors return *spans*, not enriched
identities, so downstream code can count types without surfacing the values.

Public API:
  find_pii(text)  -> list of (pii_type, (start, end)) spans
  pii_types(text) -> set of pii_type strings present
"""
from __future__ import annotations

import re
from typing import List, Set, Tuple

# Email: conservative but covers "a@b.com" style addresses.
_EMAIL = re.compile(
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"
)

# US phone: optional country code, common separators / parens.
#   555-123-4567, (555) 123-4567, 555.123.4567, +1 555 123 4567
_PHONE = re.compile(
    r"(?<!\d)(?:\+?1[\s.\-]?)?(?:\(\d{3}\)|\d{3})[\s.\-]\d{3}[\s.\-]\d{4}(?!\d)"
)

# SSN-like: 123-45-6789 (optional; reported separately).
_SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")

#: ordered so SSN is checked before phone (disjoint patterns, but explicit).
_DETECTORS = [
    ("email", _EMAIL),
    ("ssn", _SSN),
    ("phone", _PHONE),
]


def find_pii(text: str) -> List[Tuple[str, Tuple[int, int]]]:
    """Return a list of ``(pii_type, (start, end))`` spans found in ``text``.

    Spans are character offsets into ``text``. Overlapping matches from different
    detectors are all reported; callers that want unique types should use
    :func:`pii_types`.
    """
    out: List[Tuple[str, Tuple[int, int]]] = []
    for pii_type, pattern in _DETECTORS:
        for m in pattern.finditer(text):
            out.append((pii_type, (m.start(), m.end())))
    out.sort(key=lambda x: (x[1][0], x[1][1]))
    return out


def pii_types(text: str) -> Set[str]:
    """Return the set of PII types present in ``text`` (no values, no spans)."""
    return {t for t, _ in find_pii(text)}
