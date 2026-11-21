# Evaluation summary

Seeded evaluation: 1500 synthetic notes, 2129 planted finding mentions across 10 construction families (8 negation-scope trap families + 2 plain controls), 150 notes per family, base seed 20261121. A flip is an extracted polarity that differs from the planted ground truth. All extractors share one mention finder, so every flip is a negation-handling error.

## Flip rate per family

| Family | Mentions | Keyword | Window (NegEx-style) | Scope |
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

## Aggregates

- Overall flip rate: keyword 0.634, window 0.476, scope 0.035.
- Trap families only: keyword 0.656, window 0.554, scope 0.040.
- Worst trap family for the window extractor: historical_family at 1.000; the scope extractor scores 0.000 on the same family (gap 1.000).
- Worst trap family for the scope extractor: pseudo_negation at 0.413.

Caveat: all notes are synthetic and seeded, generated from the construction taxonomy the audit defines; the experiment measures how extractors handle these constructions, not error rates on real clinical text.
