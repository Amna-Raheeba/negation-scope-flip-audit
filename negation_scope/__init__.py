"""negation_scope: a negation-scope flip audit for clinical NLP.

Plants clinical findings with known polarity into synthetic notes,
rewrites them with a taxonomy of negation-scope traps, and measures
how often downstream finding extractors flip polarity -- per trap
family, so the audit indicts the extractor, not the note.

Author: Amna Raheeba
"""

from .audit import audit_notes
from .extractors import EXTRACTOR_NAMES, extract, find_mentions
from .generate import FAMILIES, TRAP_FAMILIES, generate_notes
from .models import ABSENT, FINDINGS, PRESENT, Mention, Note

__version__ = "0.1.0"

__all__ = [
    "ABSENT",
    "EXTRACTOR_NAMES",
    "FAMILIES",
    "FINDINGS",
    "Mention",
    "Note",
    "PRESENT",
    "TRAP_FAMILIES",
    "audit_notes",
    "extract",
    "find_mentions",
    "generate_notes",
]
