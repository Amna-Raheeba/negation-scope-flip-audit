"""Headline evaluation: polarity-flip rates per trap family.

The corpus is generated with the canonical seed (see
:mod:`negation_scope.generate`): every family contributes the same
number of notes, and every planted mention is scored by all three
extractors. The headline numbers are the flip rate per trap family for
the NegEx-style window extractor vs the dependency-lite scope
extractor, the window/scope gap on the worst family, and the keyword
baseline's overall flip rate (what ignoring negation costs).

Everything is deterministic: same seed, same numbers.
"""

import csv
import json
import os

from .audit import audit_notes
from .extractors import EXTRACTOR_NAMES
from .generate import FAMILIES, TRAP_FAMILIES, generate_notes

DEFAULT_CONFIG = {
    "base_seed": 20261121,
    "notes_per_family": 150,
}

_CSV_FIELDS = ("family", "extractor", "mentions", "flips", "flip_rate")


def run_evaluation(config=None):
    """Generate the corpus and audit it with all three extractors."""
    cfg = dict(DEFAULT_CONFIG)
    if config:
        cfg.update(config)
    notes = generate_notes(
        seed=cfg["base_seed"], notes_per_family=cfg["notes_per_family"]
    )
    audit = audit_notes(notes)
    rows = []
    for family in FAMILIES:
        for name in EXTRACTOR_NAMES:
            cell = audit["per_family"][family][name]
            rows.append({
                "family": family,
                "extractor": name,
                "mentions": cell["mentions"],
                "flips": cell["flips"],
                "flip_rate": round(cell["flip_rate"], 6),
            })
    aggregates = _aggregates(audit)
    return {
        "config": cfg,
        "n_notes": audit["n_notes"],
        "n_mentions": audit["n_mentions"],
        "rows": rows,
        "aggregates": aggregates,
    }


def _aggregates(audit):
    per_family = audit["per_family"]
    totals = audit["totals"]
    agg = {}
    for name in EXTRACTOR_NAMES:
        agg["%s_flip_rate" % name] = round(totals[name]["flip_rate"], 6)
        trap_mentions = sum(
            per_family[family][name]["mentions"] for family in TRAP_FAMILIES
        )
        trap_flips = sum(
            per_family[family][name]["flips"] for family in TRAP_FAMILIES
        )
        agg["%s_trap_flip_rate" % name] = round(
            trap_flips / trap_mentions if trap_mentions else 0.0, 6
        )
        worst_family = max(
            TRAP_FAMILIES,
            key=lambda family: per_family[family][name]["flip_rate"],
        )
        agg["%s_worst_family" % name] = worst_family
        agg["%s_worst_family_flip_rate" % name] = round(
            per_family[worst_family][name]["flip_rate"], 6
        )
        for family in FAMILIES:
            agg["%s_flip_rate__%s" % (name, family)] = round(
                per_family[family][name]["flip_rate"], 6
            )
    agg["window_scope_trap_gap"] = round(
        agg["window_trap_flip_rate"] - agg["scope_trap_flip_rate"], 6
    )
    agg["window_scope_worst_gap"] = round(
        agg["window_worst_family_flip_rate"]
        - agg["scope_flip_rate__%s" % agg["window_worst_family"]],
        6,
    )
    return agg


def write_results(evaluation, outdir):
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "evaluation.json"), "w") as handle:
        json.dump(evaluation, handle, indent=2)
    with open(os.path.join(outdir, "evaluation.csv"), "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for row in evaluation["rows"]:
            writer.writerow({key: row[key] for key in _CSV_FIELDS})
    with open(os.path.join(outdir, "evaluation_summary.md"), "w") as handle:
        handle.write(summary_markdown(evaluation))
    with open(os.path.join(outdir, "HEADLINE.md"), "w") as handle:
        handle.write(headline_markdown(evaluation))


def _family_table(evaluation):
    lines = []
    lines.append(
        "| Family | Mentions | Keyword | Window (NegEx-style) | Scope |"
    )
    lines.append("|---|---|---|---|---|")
    by_key = {
        (row["family"], row["extractor"]): row for row in evaluation["rows"]
    }
    for family in FAMILIES:
        mentions = by_key[(family, "keyword")]["mentions"]
        cells = []
        for name in EXTRACTOR_NAMES:
            cells.append("%.3f" % by_key[(family, name)]["flip_rate"])
        lines.append(
            "| %s | %d | %s | %s | %s |"
            % (family, mentions, cells[0], cells[1], cells[2])
        )
    return lines


def summary_markdown(evaluation):
    agg = evaluation["aggregates"]
    cfg = evaluation["config"]
    lines = []
    lines.append("# Evaluation summary")
    lines.append("")
    lines.append(
        "Seeded evaluation: %d synthetic notes, %d planted finding "
        "mentions across %d construction families (8 negation-scope "
        "trap families + 2 plain controls), %d notes per family, base "
        "seed %d. A flip is an extracted polarity that differs from "
        "the planted ground truth. All extractors share one mention "
        "finder, so every flip is a negation-handling error."
        % (
            evaluation["n_notes"],
            evaluation["n_mentions"],
            len(FAMILIES),
            cfg["notes_per_family"],
            cfg["base_seed"],
        )
    )
    lines.append("")
    lines.append("## Flip rate per family")
    lines.append("")
    lines.extend(_family_table(evaluation))
    lines.append("")
    lines.append("## Aggregates")
    lines.append("")
    lines.append(
        "- Overall flip rate: keyword %.3f, window %.3f, scope %.3f."
        % (agg["keyword_flip_rate"], agg["window_flip_rate"],
           agg["scope_flip_rate"])
    )
    lines.append(
        "- Trap families only: keyword %.3f, window %.3f, scope %.3f."
        % (agg["keyword_trap_flip_rate"], agg["window_trap_flip_rate"],
           agg["scope_trap_flip_rate"])
    )
    lines.append(
        "- Worst trap family for the window extractor: %s at %.3f; the "
        "scope extractor scores %.3f on the same family (gap %.3f)."
        % (
            agg["window_worst_family"],
            agg["window_worst_family_flip_rate"],
            agg["scope_flip_rate__%s" % agg["window_worst_family"]],
            agg["window_scope_worst_gap"],
        )
    )
    lines.append(
        "- Worst trap family for the scope extractor: %s at %.3f."
        % (agg["scope_worst_family"], agg["scope_worst_family_flip_rate"])
    )
    lines.append("")
    lines.append(
        "Caveat: all notes are synthetic and seeded, generated from the "
        "construction taxonomy the audit defines; the experiment "
        "measures how extractors handle these constructions, not error "
        "rates on real clinical text."
    )
    lines.append("")
    return "\n".join(lines)


def headline_markdown(evaluation):
    agg = evaluation["aggregates"]
    lines = []
    lines.append("# Headline results")
    lines.append("")
    lines.append(
        "A controlled scope-trap injection audit of clinical finding "
        "extraction: %d planted mentions in %d seeded synthetic notes "
        "across 8 negation-scope trap families plus 2 controls, scored "
        "by a keyword baseline (no negation handling), a NegEx-style "
        "fixed-window extractor, and a dependency-lite clause-scope "
        "extractor."
        % (evaluation["n_mentions"], evaluation["n_notes"])
    )
    lines.append("")
    lines.append(
        "- Ignoring negation entirely (keyword baseline) flips **%.1f%%** "
        "of all mentions and **%.1f%%** of trap-family mentions."
        % (agg["keyword_flip_rate"] * 100, agg["keyword_trap_flip_rate"] * 100)
    )
    lines.append(
        "- The window extractor flips **%.1f%%** of trap mentions; the "
        "scope extractor flips **%.1f%%** -- a window/scope gap of "
        "**%.1f** points on trap families."
        % (
            agg["window_trap_flip_rate"] * 100,
            agg["scope_trap_flip_rate"] * 100,
            agg["window_scope_trap_gap"] * 100,
        )
    )
    lines.append(
        "- Worst family for the window extractor: **%s** at **%.1f%%** "
        "flips; the scope extractor scores **%.1f%%** there."
        % (
            agg["window_worst_family"],
            agg["window_worst_family_flip_rate"] * 100,
            agg["scope_flip_rate__%s" % agg["window_worst_family"]] * 100,
        )
    )
    lines.append(
        "- The scope extractor is not clean either: its worst family is "
        "**%s** at **%.1f%%** flips."
        % (agg["scope_worst_family"], agg["scope_worst_family_flip_rate"] * 100)
    )
    lines.append("")
    lines.append(
        "Caveat: all notes are synthetic and seeded, with polarity "
        "planted by construction; the audit measures extractor "
        "behaviour on these constructions, not performance on real "
        "clinical corpora."
    )
    lines.append("")
    return "\n".join(lines)


_DRIFT_KEYS = (
    "keyword_flip_rate",
    "window_flip_rate",
    "scope_flip_rate",
    "keyword_trap_flip_rate",
    "window_trap_flip_rate",
    "scope_trap_flip_rate",
    "window_worst_family_flip_rate",
    "scope_worst_family_flip_rate",
    "window_scope_trap_gap",
    "window_scope_worst_gap",
)


def check_drift(stored, fresh, tol=1e-6):
    """Compare stored vs fresh aggregate drift keys.

    Returns (ok, problems) where problems lists
    (key, stored_value, fresh_value, diff) for out-of-tolerance keys.
    """
    problems = []
    stored_agg = stored["aggregates"]
    fresh_agg = fresh["aggregates"]
    for key in _DRIFT_KEYS:
        stored_value = stored_agg[key]
        fresh_value = fresh_agg[key]
        diff = abs(stored_value - fresh_value)
        if diff > tol:
            problems.append((key, stored_value, fresh_value, diff))
    for key in ("window_worst_family", "scope_worst_family"):
        if stored_agg[key] != fresh_agg[key]:
            problems.append((key, stored_agg[key], fresh_agg[key], None))
    return (not problems, problems)
