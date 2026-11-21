import pytest

from negation_scope.generate import (
    FAMILIES,
    TRAP_FAMILIES,
    generate_family_notes,
    generate_notes,
    notes_from_dict,
    notes_to_dict,
)
from negation_scope.models import ABSENT, FINDINGS, PRESENT, tokenize


def test_corpus_size_scales_with_notes_per_family():
    notes = generate_notes(seed=1, notes_per_family=5)
    assert len(notes) == 5 * len(FAMILIES)


def test_all_families_present():
    notes = generate_notes(seed=1, notes_per_family=2)
    assert set(note.family for note in notes) == set(FAMILIES)
    assert len(TRAP_FAMILIES) == 8


def test_generation_is_deterministic():
    first = generate_notes(seed=42, notes_per_family=3)
    second = generate_notes(seed=42, notes_per_family=3)
    assert notes_to_dict(first) == notes_to_dict(second)


def test_different_seeds_differ():
    first = generate_notes(seed=1, notes_per_family=3)
    second = generate_notes(seed=2, notes_per_family=3)
    assert notes_to_dict(first) != notes_to_dict(second)


def test_spans_align_with_tokens_and_text():
    notes = generate_notes(seed=3, notes_per_family=4)
    for note in notes:
        assert tokenize(note.text) == note.tokens
        for mention in note.mentions:
            surface = note.tokens[mention.start:mention.end]
            assert surface == FINDINGS[mention.finding]


def test_every_note_has_a_mention():
    notes = generate_notes(seed=3, notes_per_family=4)
    assert all(note.mentions for note in notes)


def test_note_ids_are_unique():
    notes = generate_notes(seed=3, notes_per_family=4)
    ids = [note.note_id for note in notes]
    assert len(set(ids)) == len(ids)


def _polarities(family, seed=11):
    notes = generate_family_notes(family, 30, seed)
    return [mention.polarity for note in notes for mention in note.mentions]


def test_plain_positive_all_present():
    assert set(_polarities("plain_positive")) == {PRESENT}


def test_plain_negative_all_absent():
    assert set(_polarities("plain_negative")) == {ABSENT}


def test_coordination_all_absent_three_per_note():
    notes = generate_family_notes("coordination_beyond_window", 10, 5)
    assert all(len(note.mentions) == 3 for note in notes)
    assert set(_polarities("coordination_beyond_window")) == {ABSENT}


def test_pseudo_negation_all_present():
    assert set(_polarities("pseudo_negation")) == {PRESENT}


def test_historical_family_all_absent():
    assert set(_polarities("historical_family")) == {ABSENT}


def test_double_negation_all_present():
    assert set(_polarities("double_negation")) == {PRESENT}


def test_subordinate_clause_pairs_absent_then_present():
    notes = generate_family_notes("subordinate_clause", 10, 5)
    for note in notes:
        assert [m.polarity for m in note.mentions] == [ABSENT, PRESENT]


def test_contrastive_pairs_absent_then_present():
    notes = generate_family_notes("contrastive_scope_break", 10, 5)
    for note in notes:
        assert [m.polarity for m in note.mentions] == [ABSENT, PRESENT]


def test_postposed_and_long_distance_all_absent():
    assert set(_polarities("postposed_negation")) == {ABSENT}
    assert set(_polarities("long_distance_scope")) == {ABSENT}


def test_unknown_family_raises():
    with pytest.raises(ValueError):
        generate_family_notes("no_such_family", 1, 1)


def test_serialization_roundtrip():
    notes = generate_notes(seed=9, notes_per_family=2)
    assert notes_from_dict(notes_to_dict(notes)) == notes
