import os

from negation_scope.cli import main

ROOT = os.path.join(os.path.dirname(__file__), "..")


def test_demo_command(capsys):
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "Demo audit" in out
    assert "coordination_beyond_window" in out


def test_audit_command_on_demo_notes(capsys):
    path = os.path.join(ROOT, "examples", "demo_notes.json")
    assert main(["audit", "--notes", path]) == 0
    out = capsys.readouterr().out
    assert "Negation-scope audit" in out
    assert "plain_negative" in out


def test_evaluate_command_writes_results(tmp_path, capsys):
    outdir = os.path.join(str(tmp_path), "results")
    assert main(["evaluate", "--outdir", outdir]) == 0
    out = capsys.readouterr().out
    assert "window trap flip rate" in out
    assert os.path.exists(os.path.join(outdir, "evaluation.json"))
    assert os.path.exists(os.path.join(outdir, "HEADLINE.md"))


def test_no_command_prints_help(capsys):
    assert main([]) == 2
    out = capsys.readouterr().out
    assert "negation" in out.lower()


def test_demo_notes_cover_all_families():
    from negation_scope.cli import demo_notes
    from negation_scope.generate import FAMILIES

    families = set(note.family for note in demo_notes())
    assert families == set(FAMILIES)
