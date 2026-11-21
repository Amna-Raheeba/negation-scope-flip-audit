"""Markdown reports for audit runs."""

from .extractors import EXTRACTOR_NAMES
from .generate import FAMILIES


def audit_report_markdown(audit, title="Negation-scope audit"):
    """Render an audit result (from audit_notes) as markdown."""
    lines = []
    lines.append("# %s" % title)
    lines.append("")
    lines.append(
        "%d notes, %d planted mentions. A flip is an extracted "
        "polarity that differs from the planted ground truth."
        % (audit["n_notes"], audit["n_mentions"])
    )
    lines.append("")
    lines.append(
        "| Family | Mentions | Keyword | Window (NegEx-style) | Scope |"
    )
    lines.append("|---|---|---|---|---|")
    for family in FAMILIES:
        cells = audit["per_family"][family]
        mentions = cells[EXTRACTOR_NAMES[0]]["mentions"]
        rates = [
            "%.3f" % cells[name]["flip_rate"] for name in EXTRACTOR_NAMES
        ]
        lines.append(
            "| %s | %d | %s | %s | %s |"
            % (family, mentions, rates[0], rates[1], rates[2])
        )
    lines.append("")
    lines.append("Overall flip rates:")
    lines.append("")
    for name in EXTRACTOR_NAMES:
        cell = audit["totals"][name]
        lines.append(
            "- %s: %.3f (%d flips of %d mentions)"
            % (name, cell["flip_rate"], cell["flips"], cell["mentions"])
        )
    lines.append("")
    return "\n".join(lines)


def flip_examples_markdown(audit, extractor="window", limit=5):
    """Show a few example flips for one extractor."""
    lines = []
    lines.append("Example flips (%s):" % extractor)
    lines.append("")
    shown = 0
    for detail in audit["details"]:
        if detail["extractor"] != extractor:
            continue
        lines.append(
            "- [%s] %s: gold=%s predicted=%s -- \"%s\""
            % (
                detail["family"],
                detail["finding"],
                detail["gold"],
                detail["predicted"],
                detail["text"],
            )
        )
        shown += 1
        if shown >= limit:
            break
    if shown == 0:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)
