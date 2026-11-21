import json
import os

from negation_scope.evaluate import check_drift, run_evaluation

RESULTS = os.path.join(
    os.path.dirname(__file__), "..", "results", "evaluation.json"
)


def test_stored_results_reproduce():
    with open(RESULTS) as handle:
        stored = json.load(handle)
    fresh = run_evaluation()
    ok, problems = check_drift(stored, fresh)
    assert ok, problems


def test_stored_corpus_matches_evaluation_size():
    data_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "notes.json"
    )
    with open(data_path) as handle:
        corpus = json.load(handle)
    with open(RESULTS) as handle:
        stored = json.load(handle)
    assert len(corpus["notes"]) == stored["n_notes"]
    mentions = sum(len(note["mentions"]) for note in corpus["notes"])
    assert mentions == stored["n_mentions"]
