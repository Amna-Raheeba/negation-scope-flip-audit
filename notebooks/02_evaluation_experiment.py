"""Evaluation experiment: flip rates per trap family, all extractors.

Runs the full headline evaluation (seeded corpus generation + audit)
and prints the aggregate table. This is the same computation that
produces results/; CI runs it as a smoke check.

Run: python notebooks/02_evaluation_experiment.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from negation_scope.evaluate import headline_markdown, run_evaluation


def main():
    evaluation = run_evaluation()
    print(headline_markdown(evaluation))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
