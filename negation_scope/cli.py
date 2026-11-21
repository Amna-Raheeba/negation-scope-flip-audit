"""Command line interface.

Usage:
    python -m negation_scope demo
    python -m negation_scope audit --notes examples/demo_notes.json
    python -m negation_scope evaluate --outdir results
"""

import argparse
import json

from .audit import audit_notes
from .evaluate import run_evaluation, write_results
from .generate import generate_notes, notes_from_dict
from .report import audit_report_markdown, flip_examples_markdown

DEMO_SEED = 7


def demo_notes():
    """One note per family, for the built-in demo."""
    return generate_notes(seed=DEMO_SEED, notes_per_family=1)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="negation_scope",
        description=(
            "Audit clinical finding extractors with planted "
            "negation-scope traps: measure the polarity-flip rate per "
            "construction family."
        ),
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("demo", help="Audit one note per family and report")

    audit_parser = sub.add_parser(
        "audit", help="Audit a JSON file of planted notes"
    )
    audit_parser.add_argument("--notes", required=True,
                              help="Notes JSON path (see data/notes.json)")

    eval_parser = sub.add_parser(
        "evaluate", help="Run the headline evaluation and write results"
    )
    eval_parser.add_argument("--outdir", default="results")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "demo":
        audit = audit_notes(demo_notes())
        print(audit_report_markdown(audit, title="Demo audit"))
        print(flip_examples_markdown(audit, extractor="window"))
        return 0
    if args.command == "audit":
        with open(args.notes) as handle:
            notes = notes_from_dict(json.load(handle))
        audit = audit_notes(notes)
        print(audit_report_markdown(audit))
        return 0
    if args.command == "evaluate":
        evaluation = run_evaluation()
        write_results(evaluation, args.outdir)
        agg = evaluation["aggregates"]
        print(
            "Wrote results to %s: window trap flip rate %.3f, scope "
            "%.3f, keyword %.3f."
            % (
                args.outdir,
                agg["window_trap_flip_rate"],
                agg["scope_trap_flip_rate"],
                agg["keyword_trap_flip_rate"],
            )
        )
        return 0
    parser.print_help()
    return 2
