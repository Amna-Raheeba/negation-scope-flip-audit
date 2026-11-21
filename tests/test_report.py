from negation_scope.audit import audit_notes
from negation_scope.cli import demo_notes
from negation_scope.generate import FAMILIES
from negation_scope.report import audit_report_markdown, flip_examples_markdown


def test_audit_report_lists_all_families():
    report = audit_report_markdown(audit_notes(demo_notes()))
    for family in FAMILIES:
        assert family in report


def test_audit_report_shows_overall_rates():
    report = audit_report_markdown(audit_notes(demo_notes()))
    assert "Overall flip rates" in report
    assert "window" in report
    assert "scope" in report


def test_audit_report_custom_title():
    report = audit_report_markdown(audit_notes(demo_notes()), title="My audit")
    assert report.startswith("# My audit")


def test_flip_examples_for_window_on_demo():
    audit = audit_notes(demo_notes())
    text = flip_examples_markdown(audit, extractor="window")
    assert "Example flips (window)" in text


def test_flip_examples_empty_case():
    audit = audit_notes(demo_notes())
    text = flip_examples_markdown(audit, extractor="scope", limit=0)
    assert "Example flips (scope)" in text
