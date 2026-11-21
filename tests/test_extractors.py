import pytest

from negation_scope.extractors import extract, find_mentions, find_triggers
from negation_scope.models import ABSENT, PRESENT, tokenize


def polarity_of(extractor, text, finding):
    for pred in extract(extractor, text):
        if pred.finding == finding:
            return pred.polarity
    raise AssertionError("finding %s not extracted from %r" % (finding, text))


# --- mention finding -------------------------------------------------------


def test_find_mentions_single_and_multiword():
    tokens = tokenize("No chest pain or fever.")
    found = find_mentions(tokens)
    assert ("chest pain", 1, 3) in found
    assert ("fever", 4, 5) in found


def test_find_mentions_none():
    assert find_mentions(tokenize("The patient is resting.")) == []


def test_find_triggers_skips_pseudo_negations():
    assert find_triggers(tokenize("No change in the cough.")) == []
    assert find_triggers(tokenize("Not only fever.")) == []


def test_find_triggers_finds_real_trigger():
    spans = find_triggers(tokenize("No fever."))
    assert spans == [(0, 1)]


# --- controls ---------------------------------------------------------------


def test_plain_negative_all_extractors():
    text = "The patient denies fever."
    assert polarity_of("keyword", text, "fever") == PRESENT
    assert polarity_of("window", text, "fever") == ABSENT
    assert polarity_of("scope", text, "fever") == ABSENT


def test_plain_positive_all_extractors():
    text = "The patient reports fever."
    for name in ("keyword", "window", "scope"):
        assert polarity_of(name, text, "fever") == PRESENT


def test_no_evidence_of_is_negated():
    text = "There is no evidence of pneumonia."
    assert polarity_of("window", text, "pneumonia") == ABSENT
    assert polarity_of("scope", text, "pneumonia") == ABSENT


# --- coordination beyond window --------------------------------------------


def test_coordination_first_items_negated_by_window():
    text = "No fever, cough, or dyspnea on examination."
    assert polarity_of("window", text, "fever") == ABSENT
    assert polarity_of("window", text, "cough") == ABSENT


def test_coordination_last_item_flips_window_not_scope():
    text = "No fever, cough, or dyspnea on examination."
    assert polarity_of("window", text, "dyspnea") == PRESENT
    assert polarity_of("scope", text, "dyspnea") == ABSENT


def test_coordination_clear_of_last_item():
    text = "The lungs are clear of crackles, wheeze, or pleural effusion."
    assert polarity_of("window", text, "pleural effusion") == PRESENT
    assert polarity_of("scope", text, "pleural effusion") == ABSENT
    assert polarity_of("scope", text, "crackles") == ABSENT


# --- pseudo-negation ---------------------------------------------------------


def test_pseudo_in_lexicon_present_for_all():
    text = "No change in the cough since yesterday."
    for name in ("keyword", "window", "scope"):
        assert polarity_of(name, text, "cough") == PRESENT


def test_pseudo_not_only():
    text = "Not only fever but also cough."
    for name in ("window", "scope"):
        assert polarity_of(name, text, "fever") == PRESENT
        assert polarity_of(name, text, "cough") == PRESENT


def test_pseudo_out_of_lexicon_flips_both_negation_extractors():
    # "No worsening" is not in the shared pseudo-negation list, so both
    # negation-aware extractors honestly misread the persisting cough.
    text = "No worsening of the cough was seen."
    assert polarity_of("keyword", text, "cough") == PRESENT
    assert polarity_of("window", text, "cough") == ABSENT
    assert polarity_of("scope", text, "cough") == ABSENT


# --- historical / family -----------------------------------------------------


def test_family_history_attributed_by_scope_only():
    text = "Family history: mother had diabetes."
    assert polarity_of("keyword", text, "diabetes") == PRESENT
    assert polarity_of("window", text, "diabetes") == PRESENT
    assert polarity_of("scope", text, "diabetes") == ABSENT


def test_kinship_subject_attributed_by_scope():
    text = "The patient's sister has anemia."
    assert polarity_of("window", text, "anemia") == PRESENT
    assert polarity_of("scope", text, "anemia") == ABSENT


def test_resolved_history_attributed_by_scope():
    text = "History of pneumonia in 2019, since resolved."
    assert polarity_of("window", text, "pneumonia") == PRESENT
    assert polarity_of("scope", text, "pneumonia") == ABSENT


# --- double negation ---------------------------------------------------------


def test_cannot_rule_out():
    text = "We cannot rule out pneumonia."
    assert polarity_of("window", text, "pneumonia") == ABSENT
    assert polarity_of("scope", text, "pneumonia") == PRESENT


def test_cannot_be_excluded():
    text = "Pneumonia cannot be excluded."
    assert polarity_of("window", text, "pneumonia") == ABSENT
    assert polarity_of("scope", text, "pneumonia") == PRESENT


def test_do_not_rule_out():
    text = "Do not rule out consolidation yet."
    assert polarity_of("scope", text, "consolidation") == PRESENT


# --- subordinate / relative clauses ------------------------------------------


def test_subordinate_clause_scope_stays_inside():
    text = "Although there is no fever, the cough persists."
    assert polarity_of("window", text, "fever") == ABSENT
    assert polarity_of("scope", text, "fever") == ABSENT
    assert polarity_of("window", text, "cough") == ABSENT
    assert polarity_of("scope", text, "cough") == PRESENT


def test_relative_clause_scope_stays_inside():
    text = "The patient, who denies chest pain, reports dyspnea."
    assert polarity_of("scope", text, "chest pain") == ABSENT
    assert polarity_of("window", text, "dyspnea") == ABSENT
    assert polarity_of("scope", text, "dyspnea") == PRESENT


# --- postposed negation --------------------------------------------------------


def test_postposed_adjacent_caught_by_window():
    text = "Fever was absent on examination."
    assert polarity_of("window", text, "fever") == ABSENT
    assert polarity_of("scope", text, "fever") == ABSENT


def test_postposed_none_reported():
    text = "Fever: none reported."
    assert polarity_of("window", text, "fever") == ABSENT
    assert polarity_of("scope", text, "fever") == ABSENT


def test_postposed_distant_flips_window_not_scope():
    text = "Fever, on careful questioning, was denied."
    assert polarity_of("window", text, "fever") == PRESENT
    assert polarity_of("scope", text, "fever") == ABSENT


# --- contrastive scope break ---------------------------------------------------


def test_contrastive_but_breaks_scope():
    text = "No fever but marked dyspnea."
    assert polarity_of("window", text, "fever") == ABSENT
    assert polarity_of("scope", text, "fever") == ABSENT
    assert polarity_of("window", text, "dyspnea") == ABSENT
    assert polarity_of("scope", text, "dyspnea") == PRESENT


def test_contrastive_however_breaks_scope():
    text = "No fever however, dyspnea is severe."
    assert polarity_of("scope", text, "dyspnea") == PRESENT


# --- long-distance scope --------------------------------------------------------


def test_long_distance_flips_window_not_scope():
    text = "No clinical or radiological evidence of pneumonia."
    assert polarity_of("window", text, "pneumonia") == PRESENT
    assert polarity_of("scope", text, "pneumonia") == ABSENT


def test_long_distance_with_list_commas():
    text = "No evidence on history, examination, or imaging of pneumonia."
    assert polarity_of("window", text, "pneumonia") == PRESENT
    assert polarity_of("scope", text, "pneumonia") == ABSENT


# --- misc -----------------------------------------------------------------------


def test_unknown_extractor_raises():
    with pytest.raises(ValueError):
        extract("no_such_extractor", "No fever.")


def test_sentence_boundary_stops_window():
    text = "No fever. The patient reports cough."
    assert polarity_of("window", text, "cough") == PRESENT
    assert polarity_of("scope", text, "cough") == PRESENT
