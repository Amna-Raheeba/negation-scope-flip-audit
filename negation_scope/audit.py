"""The audit: run extractors over planted notes and count flips.

A *flip* is a mention whose extracted polarity differs from the planted
ground truth. Because every extractor shares the same mention finder,
a flip is always a polarity error, never a span error -- the audit
measures negation handling, not named-entity recognition.
"""

from .extractors import EXTRACTOR_NAMES, EXTRACTORS
from .generate import FAMILIES
from .models import tokenize


def audit_notes(notes, extractor_names=EXTRACTOR_NAMES):
    """Audit notes with each extractor.

    Returns a dict with per-extractor, per-family flip counts and a
    per-mention detail list for the first extractor errors found.
    """
    per_family = {}
    for family in FAMILIES:
        per_family[family] = {
            name: {"mentions": 0, "flips": 0} for name in extractor_names
        }
    totals = {
        name: {"mentions": 0, "flips": 0} for name in extractor_names
    }
    details = []
    for note in notes:
        tokens = tokenize(note.text)
        gold = {(m.start, m.end, m.finding): m for m in note.mentions}
        for name in extractor_names:
            predictions = EXTRACTORS[name](tokens)
            predicted = {pred.key(): pred for pred in predictions}
            for key, mention in gold.items():
                pred = predicted.get(key)
                polarity = pred.polarity if pred is not None else None
                flipped = polarity != mention.polarity
                cell = per_family[mention.family][name]
                cell["mentions"] += 1
                totals[name]["mentions"] += 1
                if flipped:
                    cell["flips"] += 1
                    totals[name]["flips"] += 1
                    details.append({
                        "note_id": note.note_id,
                        "family": mention.family,
                        "extractor": name,
                        "finding": mention.finding,
                        "gold": mention.polarity,
                        "predicted": polarity,
                        "text": note.text,
                    })
    for family in FAMILIES:
        for name in extractor_names:
            cell = per_family[family][name]
            cell["flip_rate"] = (
                cell["flips"] / cell["mentions"] if cell["mentions"] else 0.0
            )
    for name in extractor_names:
        cell = totals[name]
        cell["flip_rate"] = (
            cell["flips"] / cell["mentions"] if cell["mentions"] else 0.0
        )
    return {
        "per_family": per_family,
        "totals": totals,
        "details": details,
        "n_notes": len(notes),
        "n_mentions": sum(len(note.mentions) for note in notes),
    }
