# Negation Scope Flip Audit

A controlled **scope-trap injection audit** for clinical finding
extraction: it plants findings with known polarity into synthetic
notes, rewrites them with a taxonomy of negation-scope traps, and
measures how often downstream extractors **flip the polarity** — per
trap family, so the audit indicts the extractor, not the note.

## 1. What it is

Negation is where clinical NLP quietly breaks. A note that says "no
evidence of pneumonia" must not yield a pneumonia finding; a note that
says "pneumonia cannot be ruled out" must not yield a *negated* one
either. Standard negation tools are evaluated with F1 on annotated
corpora, which averages away exactly the constructions that fail.

This tool takes the other route. A seeded generator builds short
synthetic notes (no real patient data) in which every finding's span
and true polarity are known by construction, then rewrites them with
eight families of scope traps. Three extractors — a keyword baseline
with no negation handling, a NegEx-style fixed-window extractor, and a
dependency-lite clause-scope extractor — read the text alone, and the
audit reports the **polarity-flip rate per trap family** for each.
Everything is offline, deterministic and seeded. Pure Python standard
library; no API keys, no model downloads, no network.

## 2. The novel mechanism

**Planted polarity + a trap taxonomy.** Each note is assembled token
by token from a construction template, so ground truth is exact. The
eight trap families target distinct scope mechanisms:

1. **coordination_beyond_window** — "clear of crackles, wheeze, or
   pleural effusion": the trigger's fixed window expires mid-list.
2. **pseudo_negation** — "no change in the cough", "not only fever
   but also chills": a trigger word that negates nothing.
3. **historical_family** — "family history: mother had diabetes";
   "history of pneumonia in 2019, since resolved": the finding is not
   the patient's current finding at all.
4. **double_negation** — "we cannot rule out pneumonia": two cues
   cancel, and the finding stays in play.
5. **subordinate_clause** — "although there is no fever, the cough
   persists": the negation is scoped inside the subordinate clause.
6. **postposed_negation** — "fever, on careful questioning, was
   denied": the trigger follows the finding, sometimes far behind it.
7. **contrastive_scope_break** — "no fever but marked dyspnea": the
   contrastive conjunction ends the scope.
8. **long_distance_scope** — "no evidence on history, examination, or
   imaging of pneumonia": trigger and finding far apart, one clause.

Two plain controls (affirmed / negated findings) anchor the scale.

**One mention finder, three polarity deciders.** All extractors share
the same surface-form mention finder, so every measured flip is a
negation-handling error, never a span error. The two negation-aware
extractors also share one trigger lexicon and one pseudo-negation
list — the comparison is about *scope computation* (fixed token
window vs clause region), not dictionary size.

## 3. Prior art and the differentiator

- **NegEx** assigns negation with trigger windows over annotated
  corpora and reports detection F1.
- **NegBio** extends scope with dependency patterns, again evaluated
  as a detector on annotated text.
- **NegBERT** and transformer negation detectors learn scope from
  annotations and report F1.

All of these *perform* negation detection and are scored on corpora
where hard constructions are rare and unlabeled by type. None is a
controlled injection harness that plants known polarity, applies a
named taxonomy of scope traps, and reports the **downstream
extraction flip rate per construction family**. That measurement —
which constructions break which scope strategy, and by how much — is
the differentiator. Paper angle: *"Where negation breaks: a
construction-level stress test of clinical finding extraction."*

## 4. Measured headline results

Seeded evaluation: 1,500 notes, 2,129 planted mentions, 150 notes per
family, base seed 20261121. Flip rate = extracted polarity differs
from planted ground truth. Full detail in `results/`.

| Family | Mentions | Keyword | Window | Scope |
|---|---|---|---|---|
| plain_positive | 150 | 0.000 | 0.000 | 0.000 |
| plain_negative | 150 | 1.000 | 0.000 | 0.000 |
| coordination_beyond_window | 450 | 1.000 | 0.333 | 0.000 |
| pseudo_negation | 179 | 0.000 | 0.413 | 0.413 |
| historical_family | 150 | 1.000 | 1.000 | 0.000 |
| double_negation | 150 | 0.000 | 1.000 | 0.000 |
| subordinate_clause | 300 | 0.500 | 0.500 | 0.000 |
| postposed_negation | 150 | 1.000 | 0.293 | 0.000 |
| contrastive_scope_break | 300 | 0.500 | 0.483 | 0.000 |
| long_distance_scope | 150 | 1.000 | 1.000 | 0.000 |

- Ignoring negation entirely (keyword) flips **63.4%** of all
  mentions and **65.6%** of trap-family mentions — it gets every
  genuinely negated finding wrong.
- The window extractor flips **55.4%** of trap mentions. It fails
  *completely* (flip rate 1.000) on three families: historical /
  family framing, double negation, and long-distance scope; it loses
  exactly the last item of every coordinated list (0.333) and half of
  every subordinate-clause and contrastive note (the affirmed
  main-clause finding).
- The scope extractor flips **4.0%** of trap mentions — a
  window/scope gap of **51.3 points** — and is clean on seven of
  eight trap families.
- The honest exception: **pseudo_negation flips both negation-aware
  extractors at 0.413**. Scope structure cannot rescue a trigger the
  shared pseudo-negation lexicon does not know ("no worsening of the
  cough" is read as a negation by both). The audit separates the two
  failure kinds — scope errors, which structure fixes, from lexicon
  gaps, which it does not.

## 5. Quick start

```bash
pip install -r requirements.txt

python -m negation_scope demo                    # one note per family
python -m negation_scope audit --notes examples/demo_notes.json
python -m negation_scope evaluate                # regenerate results/
python examples/run_audit.py                     # audit via the example script
streamlit run app.py                             # dashboard (3 tabs)
```

Notes format: JSON with a `notes` list; each note has `note_id`,
`family`, `text`, `tokens`, and `mentions` (each with `finding`,
`start`, `end`, `polarity`, `family`) — see `data/notes.json`.

## 6. How it works

1. **Generate** — the seeded generator assembles each note from a
   construction template, recording every finding's token span and
   planted polarity.
2. **Extract** — each extractor finds mentions with the shared
   surface-form finder, then decides polarity its own way: keyword
   affirms everything; window looks for an active trigger within 4
   tokens before (or 3 after) the mention; scope segments the note
   into clause regions and lets a trigger scope over its region,
   with two covering triggers cancelling and history / family frames
   attributed away from the patient.
3. **Audit** — predictions are matched to planted mentions by span;
   a polarity mismatch is a flip. Flips are aggregated per family
   per extractor, which is what turns "the extractor is 95% accurate"
   into "the extractor is wrong on *every* double negation".

## 7. Repository layout

```
negation_scope/      the package (models, generate, extractors, audit,
                     evaluate, report, cli)
data/                the full seeded evaluation corpus (1,500 notes)
tests/               pytest suite (85 tests)
notebooks/           01_demo_run.py, 02_evaluation_experiment.py
examples/            demo notes, runner, sample report
scripts/             build_cases.py, reproduce_results.py (drift guard)
results/             evaluation.json/.csv, evaluation_summary.md, HEADLINE.md
app.py               Streamlit dashboard (Trap explorer / Flip rates /
                     Evaluation)
```

## 8. Honest limits

- **Synthetic notes only.** Every number is measured on seeded
  synthetic notes generated from the taxonomy the audit defines. The
  experiment measures how extractors handle these constructions; it
  does not estimate error rates on real clinical text, where traps
  arrive unlabeled and mixed with everything else.
- **The scope extractor knows the grammar.** Its clause rules were
  written against the same construction families the generator
  plants, so its near-zero flip rates show that clause-scope
  computation *can* resolve these constructions — not that it
  resolves unseen real-world syntax. The one family it fails,
  pseudo_negation, fails for a lexicon reason both negation-aware
  extractors share, and the audit reports it rather than hiding it.
- **Polarity is binary and patient-centred.** "Present" means
  asserted as a current finding of the patient; family-history and
  resolved findings are planted as absent. Real extraction also
  needs uncertainty and experiencer as first-class labels — the
  audit's binary frame is a deliberate simplification, stated here.
- **The window extractor is a simplified NegEx.** Fixed window,
  scope terminated only by sentence punctuation. Full NegEx adds
  conjunction termination and a larger pseudo-negation list, which
  would move some of its numbers — the audit measures the widely
  copied simplified design, and says so.
- **Mentions are lexicon matches.** All extractors share one
  surface-form finder over a 24-finding lexicon, so the audit says
  nothing about mention detection (synonyms, abbreviations,
  misspellings) — by design, so polarity is the only variable.

## 9. Reproducing the results

```bash
python scripts/build_cases.py        # regenerate data/ and the demo files
python -m negation_scope evaluate    # regenerate results/
python scripts/reproduce_results.py  # drift guard: PASS/FAIL vs stored results
```

## 10. License

MIT — see `LICENSE`. Author: Amna Raheeba.
