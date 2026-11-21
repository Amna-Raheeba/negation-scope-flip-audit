from negation_scope.models import (
    ABSENT,
    FINDINGS,
    PRESENT,
    Mention,
    Note,
    render,
    tokenize,
)


def test_polarity_constants():
    assert PRESENT == "present"
    assert ABSENT == "absent"


def test_lexicon_has_24_findings():
    assert len(FINDINGS) == 24


def test_surface_forms_are_lowercase_tokens():
    for name, surface in FINDINGS.items():
        assert surface == tokenize(name)
        assert all(tok == tok.lower() for tok in surface)


def test_surface_forms_are_unique():
    surfaces = [tuple(surface) for surface in FINDINGS.values()]
    assert len(set(surfaces)) == len(surfaces)


def test_tokenize_lowercases_and_splits_punctuation():
    assert tokenize("No fever, cough.") == ["no", "fever", ",", "cough", "."]


def test_tokenize_keeps_apostrophes_and_numbers():
    assert tokenize("Patient's 2019 visit") == ["patient's", "2019", "visit"]


def test_render_tokenize_roundtrip():
    tokens = ["the", "lungs", "are", "clear", "of", "crackles", ",",
              "wheeze", ".",]
    assert tokenize(render(tokens)) == tokens


def test_render_capitalises_first_letter():
    assert render(["no", "fever", "."]) == "No fever."


def test_mention_dict_roundtrip():
    mention = Mention("chest pain", 3, 5, ABSENT, "plain_negative")
    assert Mention.from_dict(mention.to_dict()) == mention


def test_note_dict_roundtrip():
    note = Note(
        note_id="x-0001",
        family="plain_negative",
        text="No fever.",
        tokens=["no", "fever", "."],
        mentions=[Mention("fever", 1, 2, ABSENT, "plain_negative")],
    )
    assert Note.from_dict(note.to_dict()) == note
