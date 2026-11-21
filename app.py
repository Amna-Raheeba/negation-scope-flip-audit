"""Streamlit dashboard for negation-scope-flip-audit.

Three tabs:
1. Trap explorer -- sample notes from one construction family, with
   the planted polarity next to each extractor's call.
2. Flip rates -- per-family flip rates from the stored headline
   evaluation (results/evaluation.json).
3. Evaluation -- the stored headline aggregates and caveats.

Run: streamlit run app.py
"""

import json
import os

import streamlit as st

from negation_scope.audit import audit_notes
from negation_scope.extractors import EXTRACTOR_NAMES, extract
from negation_scope.generate import FAMILIES, generate_family_notes

st.set_page_config(page_title="Negation Scope Flip Audit", layout="wide")

RESULTS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "results", "evaluation.json"
)


def _load_evaluation():
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH) as handle:
            return json.load(handle)
    return None


def tab_explorer():
    st.header("Explore a trap family")
    st.write(
        "Each note below was generated with planted polarity. Compare "
        "the gold call with what each extractor extracts from the text "
        "alone."
    )
    family = st.selectbox("Construction family", FAMILIES, index=2)
    notes = generate_family_notes(family, 3, seed=99)
    for note in notes:
        st.markdown("**%s**" % note.text)
        rows = []
        for mention in note.mentions:
            row = {
                "finding": mention.finding,
                "gold": mention.polarity,
            }
            for name in EXTRACTOR_NAMES:
                preds = extract(name, note.text)
                match = [
                    pred.polarity for pred in preds
                    if (pred.start, pred.end, pred.finding)
                    == (mention.start, mention.end, mention.finding)
                ]
                row[name] = match[0] if match else "?"
            rows.append(row)
        st.dataframe(rows, hide_index=True)


def tab_flip_rates():
    st.header("Flip rate per family")
    evaluation = _load_evaluation()
    if evaluation is None:
        st.write(
            "No stored results yet. Run "
            "`python -m negation_scope evaluate` first."
        )
        return
    by_key = {
        (row["family"], row["extractor"]): row["flip_rate"]
        for row in evaluation["rows"]
    }
    chart_data = {
        name: [by_key[(family, name)] for family in FAMILIES]
        for name in EXTRACTOR_NAMES
    }
    st.bar_chart(chart_data)
    rows = []
    for family in FAMILIES:
        row = {"family": family}
        for name in EXTRACTOR_NAMES:
            row[name] = round(by_key[(family, name)], 3)
        rows.append(row)
    st.dataframe(rows, hide_index=True)


def tab_evaluation():
    st.header("Headline evaluation")
    evaluation = _load_evaluation()
    if evaluation is None:
        st.write(
            "No stored results yet. Run "
            "`python -m negation_scope evaluate` first."
        )
        return
    agg = evaluation["aggregates"]
    st.write(
        "%d notes, %d planted mentions, %d notes per family, seed %d."
        % (
            evaluation["n_notes"],
            evaluation["n_mentions"],
            evaluation["config"]["notes_per_family"],
            evaluation["config"]["base_seed"],
        )
    )
    rows = [
        {"metric": "keyword flip rate (all)", "value": agg["keyword_flip_rate"]},
        {"metric": "window flip rate (all)", "value": agg["window_flip_rate"]},
        {"metric": "scope flip rate (all)", "value": agg["scope_flip_rate"]},
        {"metric": "keyword flip rate (traps)", "value": agg["keyword_trap_flip_rate"]},
        {"metric": "window flip rate (traps)", "value": agg["window_trap_flip_rate"]},
        {"metric": "scope flip rate (traps)", "value": agg["scope_trap_flip_rate"]},
        {"metric": "window worst family", "value": agg["window_worst_family"]},
        {"metric": "window worst-family flip rate", "value": agg["window_worst_family_flip_rate"]},
        {"metric": "scope worst family", "value": agg["scope_worst_family"]},
        {"metric": "scope worst-family flip rate", "value": agg["scope_worst_family_flip_rate"]},
    ]
    st.dataframe(rows, hide_index=True)
    st.write(
        "Caveat: all notes are synthetic and seeded, with polarity "
        "planted by construction. The audit measures extractor "
        "behaviour on these constructions, not error rates on real "
        "clinical text."
    )
    demo = audit_notes(generate_family_notes("double_negation", 5, seed=3))
    st.write(
        "Live mini-audit (5 double-negation notes): window flips "
        "%.2f, scope flips %.2f."
        % (
            demo["totals"]["window"]["flip_rate"],
            demo["totals"]["scope"]["flip_rate"],
        )
    )


tab1, tab2, tab3 = st.tabs(["Trap explorer", "Flip rates", "Evaluation"])
with tab1:
    tab_explorer()
with tab2:
    tab_flip_rates()
with tab3:
    tab_evaluation()
