"""Seeded generator of synthetic clinical notes with planted polarity.

Each note is built token by token from a construction template, so the
span and ground-truth polarity of every planted finding are known
exactly. Eight families are *scope traps* -- constructions whose
surface form misleads negation handling -- and two are plain controls.

Trap families:

- ``coordination_beyond_window``: a negation trigger heads a coordinated
  list ("clear of X, Y, or Z"); later items sit beyond a fixed window.
- ``pseudo_negation``: a trigger word is present but negates nothing
  ("no change in the cough", "not only fever but also chills").
- ``historical_family``: the finding belongs to a relative or to the
  patient's resolved past, not to the patient now.
- ``double_negation``: two negation cues cancel ("cannot rule out").
- ``subordinate_clause``: negation is scoped inside a subordinate or
  relative clause; the main-clause finding is affirmed.
- ``postposed_negation``: the trigger follows the finding, sometimes at
  a distance ("fever, on careful questioning, was denied").
- ``contrastive_scope_break``: a contrastive conjunction ends the
  negation's scope ("no fever but marked dyspnea").
- ``long_distance_scope``: many tokens separate trigger and finding
  ("no evidence on history, examination, or imaging of pneumonia").

Controls: ``plain_positive`` and ``plain_negative``.

All text is synthetic. No real patient data is used anywhere.
"""

import random

from .models import ABSENT, FINDINGS, PRESENT, Mention, Note, render

CONTROL_FAMILIES = ("plain_positive", "plain_negative")
TRAP_FAMILIES = (
    "coordination_beyond_window",
    "pseudo_negation",
    "historical_family",
    "double_negation",
    "subordinate_clause",
    "postposed_negation",
    "contrastive_scope_break",
    "long_distance_scope",
)
FAMILIES = CONTROL_FAMILIES + TRAP_FAMILIES

_FILLERS = (
    ["the", "patient", "is", "resting", "comfortably", "."],
    ["vitals", "are", "stable", "."],
    ["the", "nurse", "was", "notified", "."],
    ["the", "patient", "remains", "under", "observation", "."],
)


class _Builder:
    """Accumulates tokens and records finding spans as they are added."""

    def __init__(self, family):
        self.family = family
        self.tokens = []
        self.mentions = []

    def add(self, *tokens):
        self.tokens.extend(tokens)
        return self

    def add_finding(self, name, polarity):
        start = len(self.tokens)
        self.tokens.extend(FINDINGS[name])
        self.mentions.append(
            Mention(
                finding=name,
                start=start,
                end=len(self.tokens),
                polarity=polarity,
                family=self.family,
            )
        )
        return self

    def build(self, note_id, rng):
        if rng.random() < 0.3:
            self.tokens.extend(rng.choice(_FILLERS))
        return Note(
            note_id=note_id,
            family=self.family,
            text=render(self.tokens),
            tokens=list(self.tokens),
            mentions=list(self.mentions),
        )


def _pick(rng, count=1):
    names = rng.sample(sorted(FINDINGS), count)
    return names[0] if count == 1 else names


# ---------------------------------------------------------------------------
# Family builders. Each returns a _Builder with one note's tokens/mentions.
# ---------------------------------------------------------------------------


def _plain_positive(rng):
    builder = _Builder("plain_positive")
    finding = _pick(rng)
    variant = rng.randrange(4)
    if variant == 0:
        builder.add("the", "patient", "reports").add_finding(finding, PRESENT)
        builder.add(".")
    elif variant == 1:
        builder.add("examination", "reveals").add_finding(finding, PRESENT)
        builder.add(".")
    elif variant == 2:
        builder.add_finding(finding, PRESENT)
        builder.add("is", "present", "on", "examination", ".")
    else:
        builder.add("the", "patient", "has").add_finding(finding, PRESENT)
        builder.add(".")
    return builder


def _plain_negative(rng):
    builder = _Builder("plain_negative")
    finding = _pick(rng)
    variant = rng.randrange(4)
    if variant == 0:
        builder.add("the", "patient", "denies").add_finding(finding, ABSENT)
        builder.add(".")
    elif variant == 1:
        builder.add("no").add_finding(finding, ABSENT)
        builder.add("was", "noted", ".")
    elif variant == 2:
        builder.add("there", "is", "no", "evidence", "of")
        builder.add_finding(finding, ABSENT)
        builder.add(".")
    else:
        builder.add("the", "patient", "is", "free", "of")
        builder.add_finding(finding, ABSENT)
        builder.add(".")
    return builder


def _coordination_beyond_window(rng):
    builder = _Builder("coordination_beyond_window")
    first, second, third = _pick(rng, 3)
    variant = rng.randrange(3)
    if variant == 0:
        builder.add("the", "lungs", "are", "clear", "of")
    elif variant == 1:
        builder.add("no")
    else:
        builder.add("the", "patient", "denies")
    builder.add_finding(first, ABSENT)
    builder.add(",")
    builder.add_finding(second, ABSENT)
    builder.add(",", "or" if variant != 2 else "and")
    builder.add_finding(third, ABSENT)
    if variant == 1:
        builder.add("on", "examination")
    builder.add(".")
    return builder


def _pseudo_negation(rng):
    builder = _Builder("pseudo_negation")
    variant = rng.randrange(6)
    if variant == 0:
        builder.add("no", "change", "in", "the")
        builder.add_finding(_pick(rng), PRESENT)
        builder.add("since", "yesterday", ".")
    elif variant == 1:
        builder.add("no", "increase", "in", "the")
        builder.add_finding(_pick(rng), PRESENT)
        builder.add("was", "seen", ".")
    elif variant == 2:
        builder.add("no", "worsening", "of", "the")
        builder.add_finding(_pick(rng), PRESENT)
        builder.add("was", "seen", ".")
    elif variant == 3:
        builder.add("no", "improvement", "in", "the")
        builder.add_finding(_pick(rng), PRESENT)
        builder.add("despite", "treatment", ".")
    elif variant == 4:
        builder.add("no", "decrease", "in")
        builder.add_finding(_pick(rng), PRESENT)
        builder.add("was", "observed", ".")
    else:
        first, second = _pick(rng, 2)
        builder.add("not", "only")
        builder.add_finding(first, PRESENT)
        builder.add("but", "also")
        builder.add_finding(second, PRESENT)
        builder.add(".")
    return builder


def _historical_family(rng):
    builder = _Builder("historical_family")
    finding = _pick(rng)
    variant = rng.randrange(6)
    if variant == 0:
        builder.add("family", "history", ":", "mother", "had")
        builder.add_finding(finding, ABSENT)
        builder.add(".")
    elif variant == 1:
        builder.add("family", "history", "of")
        builder.add_finding(finding, ABSENT)
        builder.add("on", "the", "maternal", "side", ".")
    elif variant == 2:
        builder.add("the", "patient's", "father", "had")
        builder.add_finding(finding, ABSENT)
        builder.add(".")
    elif variant == 3:
        builder.add("the", "patient's", "sister", "has")
        builder.add_finding(finding, ABSENT)
        builder.add(".")
    elif variant == 4:
        builder.add("history", "of")
        builder.add_finding(finding, ABSENT)
        builder.add("in", "2019", ",", "since", "resolved", ".")
    else:
        builder.add_finding(finding, ABSENT)
        builder.add("in", "childhood", ",", "long", "resolved", ".")
    return builder


def _double_negation(rng):
    builder = _Builder("double_negation")
    finding = _pick(rng)
    variant = rng.randrange(4)
    if variant == 0:
        builder.add("we", "cannot", "rule", "out")
        builder.add_finding(finding, PRESENT)
        builder.add(".")
    elif variant == 1:
        builder.add_finding(finding, PRESENT)
        builder.add("cannot", "be", "excluded", ".")
    elif variant == 2:
        builder.add("it", "is", "not", "true", "that", "the", "patient",
                    "is", "free", "of")
        builder.add_finding(finding, PRESENT)
        builder.add(".")
    else:
        builder.add("do", "not", "rule", "out")
        builder.add_finding(finding, PRESENT)
        builder.add("yet", ".")
    return builder


def _subordinate_clause(rng):
    builder = _Builder("subordinate_clause")
    first, second = _pick(rng, 2)
    variant = rng.randrange(3)
    if variant == 0:
        builder.add("although", "there", "is", "no")
        builder.add_finding(first, ABSENT)
        builder.add(",", "the")
        builder.add_finding(second, PRESENT)
        builder.add("persists", ".")
    elif variant == 1:
        builder.add("the", "patient", ",", "who", "denies")
        builder.add_finding(first, ABSENT)
        builder.add(",", "reports")
        builder.add_finding(second, PRESENT)
        builder.add(".")
    else:
        builder.add("while", "there", "is", "no")
        builder.add_finding(first, ABSENT)
        builder.add(",")
        builder.add_finding(second, PRESENT)
        builder.add("remains", "severe", ".")
    return builder


def _postposed_negation(rng):
    builder = _Builder("postposed_negation")
    finding = _pick(rng)
    variant = rng.randrange(4)
    if variant == 0:
        builder.add_finding(finding, ABSENT)
        builder.add("was", "absent", "on", "examination", ".")
    elif variant == 1:
        builder.add_finding(finding, ABSENT)
        builder.add(":", "none", "reported", ".")
    elif variant == 2:
        builder.add_finding(finding, ABSENT)
        builder.add(",", "on", "careful", "questioning", ",", "was",
                    "denied", ".")
    else:
        builder.add("the")
        builder.add_finding(finding, ABSENT)
        builder.add("remained", "absent", "throughout", ".")
    return builder


def _contrastive_scope_break(rng):
    builder = _Builder("contrastive_scope_break")
    first, second = _pick(rng, 2)
    variant = rng.randrange(3)
    if variant == 0:
        builder.add("no")
        builder.add_finding(first, ABSENT)
        builder.add("but", "marked")
        builder.add_finding(second, PRESENT)
        builder.add(".")
    elif variant == 1:
        builder.add("the", "patient", "denies")
        builder.add_finding(first, ABSENT)
        builder.add("but", "reports", "severe")
        builder.add_finding(second, PRESENT)
        builder.add(".")
    else:
        builder.add("no")
        builder.add_finding(first, ABSENT)
        builder.add("however", ",")
        builder.add_finding(second, PRESENT)
        builder.add("is", "severe", ".")
    return builder


def _long_distance_scope(rng):
    builder = _Builder("long_distance_scope")
    finding = _pick(rng)
    variant = rng.randrange(3)
    if variant == 0:
        builder.add("no", "clinical", "or", "radiological", "evidence",
                    "of")
        builder.add_finding(finding, ABSENT)
        builder.add(".")
    elif variant == 1:
        builder.add("there", "is", "no", "sign", ",", "on", "examination",
                    "or", "imaging", ",", "of")
        builder.add_finding(finding, ABSENT)
        builder.add(".")
    else:
        builder.add("no", "evidence", "on", "history", ",", "examination",
                    ",", "or", "imaging", "of")
        builder.add_finding(finding, ABSENT)
        builder.add(".")
    return builder


_BUILDERS = {
    "plain_positive": _plain_positive,
    "plain_negative": _plain_negative,
    "coordination_beyond_window": _coordination_beyond_window,
    "pseudo_negation": _pseudo_negation,
    "historical_family": _historical_family,
    "double_negation": _double_negation,
    "subordinate_clause": _subordinate_clause,
    "postposed_negation": _postposed_negation,
    "contrastive_scope_break": _contrastive_scope_break,
    "long_distance_scope": _long_distance_scope,
}


def generate_family_notes(family, count, seed):
    """Generate ``count`` notes of one family, deterministically."""
    if family not in _BUILDERS:
        raise ValueError("unknown family: %s" % family)
    rng = random.Random(seed)
    builder_fn = _BUILDERS[family]
    notes = []
    for index in range(count):
        builder = builder_fn(rng)
        note_id = "%s-%04d" % (family, index)
        notes.append(builder.build(note_id, rng))
    return notes


def generate_notes(seed=20261121, notes_per_family=150):
    """Generate the full corpus: every family, fixed order, seeded."""
    notes = []
    for index, family in enumerate(FAMILIES):
        family_seed = seed + 7919 * index
        notes.extend(generate_family_notes(family, notes_per_family,
                                           family_seed))
    return notes


def notes_to_dict(notes):
    return {"notes": [note.to_dict() for note in notes]}


def notes_from_dict(data):
    return [Note.from_dict(item) for item in data["notes"]]
