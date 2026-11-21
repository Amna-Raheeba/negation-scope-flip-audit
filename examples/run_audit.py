"""Audit the demo notes (one per family) and print the report.

Run: python examples/run_audit.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from negation_scope.audit import audit_notes
from negation_scope.generate import notes_from_dict
from negation_scope.report import audit_report_markdown, flip_examples_markdown


def main():
    path = os.path.join(os.path.dirname(__file__), "demo_notes.json")
    with open(path) as handle:
        notes = notes_from_dict(json.load(handle))
    audit = audit_notes(notes)
    print(audit_report_markdown(audit, title="Demo-notes audit"))
    print(flip_examples_markdown(audit, extractor="window"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
