"""Generate the stored case data.

Writes:
- data/notes.json: the full evaluation corpus, using the same seed
  scheme as negation_scope.evaluate, so the stored notes are exactly
  the ones the headline evaluation audits.
- examples/demo_notes.json: one note per family (the CLI demo set).

Run: python scripts/build_cases.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from negation_scope.cli import demo_notes
from negation_scope.evaluate import DEFAULT_CONFIG
from negation_scope.generate import generate_notes, notes_to_dict


def main():
    root = os.path.join(os.path.dirname(__file__), "..")
    cfg = DEFAULT_CONFIG
    notes = generate_notes(
        seed=cfg["base_seed"], notes_per_family=cfg["notes_per_family"]
    )
    data_path = os.path.join(root, "data", "notes.json")
    with open(data_path, "w") as handle:
        json.dump(notes_to_dict(notes), handle, separators=(",", ":"))
    print(
        "Wrote %s (%d notes, %d mentions)"
        % (data_path, len(notes), sum(len(n.mentions) for n in notes))
    )

    demo_path = os.path.join(root, "examples", "demo_notes.json")
    demo = demo_notes()
    with open(demo_path, "w") as handle:
        json.dump(notes_to_dict(demo), handle, indent=2)
    print("Wrote %s (%d notes)" % (demo_path, len(demo)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
