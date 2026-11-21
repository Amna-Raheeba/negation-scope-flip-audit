from negation_scope.audit import audit_notes
from negation_scope.generate import generate_notes
from negation_scope.models import ABSENT, PRESENT, Mention, Note


def _note(note_id, family, text, tokens, mentions):
    return Note(note_id=note_id, family=family, text=text,
                tokens=tokens, mentions=mentions)


def test_keyword_flips_plain_negation():
    note = _note(
        "n1", "plain_negative", "No fever.", ["no", "fever", "."],
        [Mention("fever", 1, 2, ABSENT, "plain_negative")],
    )
    audit = audit_notes([note])
    assert audit["totals"]["keyword"]["flips"] == 1
    assert audit["totals"]["window"]["flips"] == 0
    assert audit["totals"]["scope"]["flips"] == 0


def test_window_flips_double_negation_scope_does_not():
    note = _note(
        "n2", "double_negation", "We cannot rule out pneumonia.",
        ["we", "cannot", "rule", "out", "pneumonia", "."],
        [Mention("pneumonia", 4, 5, PRESENT, "double_negation")],
    )
    audit = audit_notes([note])
    assert audit["totals"]["window"]["flips"] == 1
    assert audit["totals"]["scope"]["flips"] == 0
    assert audit["totals"]["keyword"]["flips"] == 0


def test_per_family_rates_are_computed():
    notes = generate_notes(seed=2, notes_per_family=3)
    audit = audit_notes(notes)
    plain_neg = audit["per_family"]["plain_negative"]
    assert plain_neg["keyword"]["flip_rate"] == 1.0
    assert plain_neg["window"]["flip_rate"] == 0.0
    assert plain_neg["scope"]["flip_rate"] == 0.0


def test_totals_match_mention_count():
    notes = generate_notes(seed=2, notes_per_family=3)
    audit = audit_notes(notes)
    expected = sum(len(note.mentions) for note in notes)
    assert audit["n_mentions"] == expected
    for name in ("keyword", "window", "scope"):
        assert audit["totals"][name]["mentions"] == expected


def test_details_record_flips_with_text():
    notes = generate_notes(seed=2, notes_per_family=3)
    audit = audit_notes(notes)
    assert audit["details"]
    detail = audit["details"][0]
    assert detail["gold"] != detail["predicted"]
    assert detail["text"]
    assert detail["extractor"] in ("keyword", "window", "scope")


def test_scope_beats_window_on_trap_families():
    notes = generate_notes(seed=2, notes_per_family=10)
    audit = audit_notes(notes)
    assert (audit["totals"]["scope"]["flip_rate"]
            < audit["totals"]["window"]["flip_rate"])
