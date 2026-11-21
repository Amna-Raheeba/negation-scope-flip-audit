import json
import os

from negation_scope.evaluate import check_drift, run_evaluation, write_results
from negation_scope.extractors import EXTRACTOR_NAMES
from negation_scope.generate import FAMILIES

SMALL = {"base_seed": 5, "notes_per_family": 10}


def test_run_evaluation_shape():
    evaluation = run_evaluation(SMALL)
    assert evaluation["n_notes"] == 10 * len(FAMILIES)
    assert evaluation["n_mentions"] > evaluation["n_notes"]
    assert len(evaluation["rows"]) == len(FAMILIES) * len(EXTRACTOR_NAMES)


def test_aggregates_have_headline_keys():
    agg = run_evaluation(SMALL)["aggregates"]
    for key in (
        "keyword_flip_rate", "window_flip_rate", "scope_flip_rate",
        "keyword_trap_flip_rate", "window_trap_flip_rate",
        "scope_trap_flip_rate", "window_worst_family",
        "window_worst_family_flip_rate", "scope_worst_family",
        "window_scope_trap_gap", "window_scope_worst_gap",
    ):
        assert key in agg


def test_flip_rates_within_unit_interval():
    evaluation = run_evaluation(SMALL)
    for row in evaluation["rows"]:
        assert 0.0 <= row["flip_rate"] <= 1.0
        assert row["flips"] <= row["mentions"]


def test_scope_trap_rate_below_window_trap_rate():
    agg = run_evaluation(SMALL)["aggregates"]
    assert agg["scope_trap_flip_rate"] < agg["window_trap_flip_rate"]
    assert agg["window_scope_trap_gap"] > 0.3


def test_keyword_flips_every_plain_negative():
    evaluation = run_evaluation(SMALL)
    row = [
        r for r in evaluation["rows"]
        if r["family"] == "plain_negative" and r["extractor"] == "keyword"
    ][0]
    assert row["flip_rate"] == 1.0


def test_write_results_creates_four_files(tmp_path):
    evaluation = run_evaluation(SMALL)
    write_results(evaluation, str(tmp_path))
    for name in ("evaluation.json", "evaluation.csv",
                 "evaluation_summary.md", "HEADLINE.md"):
        assert os.path.exists(os.path.join(str(tmp_path), name))
    with open(os.path.join(str(tmp_path), "evaluation.json")) as handle:
        stored = json.load(handle)
    assert stored["aggregates"] == evaluation["aggregates"]


def test_check_drift_passes_on_identical():
    evaluation = run_evaluation(SMALL)
    ok, problems = check_drift(evaluation, evaluation)
    assert ok
    assert problems == []


def test_check_drift_catches_tampering():
    evaluation = run_evaluation(SMALL)
    tampered = json.loads(json.dumps(evaluation))
    tampered["aggregates"]["window_trap_flip_rate"] += 0.5
    ok, problems = check_drift(evaluation, tampered)
    assert not ok
    assert any(key == "window_trap_flip_rate" for key, *_ in problems)
