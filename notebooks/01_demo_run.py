"""Demo: audit one note per construction family with all extractors.

The demo set has one seeded note from each of the 10 families (8 scope
traps + 2 controls). The window extractor's flips cluster exactly in
the trap families; the table makes the failure pattern visible.

Run: python notebooks/01_demo_run.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from negation_scope.audit import audit_notes
from negation_scope.cli import demo_notes
from negation_scope.report import audit_report_markdown, flip_examples_markdown


def main():
    notes = demo_notes()
    for note in notes:
        print("[%s] %s" % (note.family, note.text))
    print("")
    audit = audit_notes(notes)
    print(audit_report_markdown(audit, title="Demo audit"))
    print(flip_examples_markdown(audit, extractor="window"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
