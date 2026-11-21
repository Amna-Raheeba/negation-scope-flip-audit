# Demo-notes audit

10 notes, 14 planted mentions. A flip is an extracted polarity that differs from the planted ground truth.

| Family | Mentions | Keyword | Window (NegEx-style) | Scope |
|---|---|---|---|---|
| plain_positive | 1 | 0.000 | 0.000 | 0.000 |
| plain_negative | 1 | 1.000 | 0.000 | 0.000 |
| coordination_beyond_window | 3 | 1.000 | 0.333 | 0.000 |
| pseudo_negation | 1 | 0.000 | 1.000 | 1.000 |
| historical_family | 1 | 1.000 | 1.000 | 0.000 |
| double_negation | 1 | 0.000 | 1.000 | 0.000 |
| subordinate_clause | 2 | 0.500 | 0.500 | 0.000 |
| postposed_negation | 1 | 1.000 | 0.000 | 0.000 |
| contrastive_scope_break | 2 | 0.500 | 0.500 | 0.000 |
| long_distance_scope | 1 | 1.000 | 1.000 | 0.000 |

Overall flip rates:

- keyword: 0.643 (9 flips of 14 mentions)
- window: 0.500 (7 flips of 14 mentions)
- scope: 0.071 (1 flips of 14 mentions)

Example flips (window):

- [coordination_beyond_window] dyspnea: gold=absent predicted=present -- "The patient denies dizziness, fatigue, and dyspnea."
- [pseudo_negation] pleural effusion: gold=present predicted=absent -- "No improvement in the pleural effusion despite treatment."
- [historical_family] vomiting: gold=absent predicted=present -- "The patient's father had vomiting. vitals are stable."
- [double_negation] hemoptysis: gold=present predicted=absent -- "It is not true that the patient is free of hemoptysis. the nurse was notified."
- [subordinate_clause] tachycardia: gold=present predicted=absent -- "The patient, who denies hemoptysis, reports tachycardia."

