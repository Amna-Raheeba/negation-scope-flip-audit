# Headline results

A controlled scope-trap injection audit of clinical finding extraction: 2129 planted mentions in 1500 seeded synthetic notes across 8 negation-scope trap families plus 2 controls, scored by a keyword baseline (no negation handling), a NegEx-style fixed-window extractor, and a dependency-lite clause-scope extractor.

- Ignoring negation entirely (keyword baseline) flips **63.4%** of all mentions and **65.6%** of trap-family mentions.
- The window extractor flips **55.4%** of trap mentions; the scope extractor flips **4.0%** -- a window/scope gap of **51.3** points on trap families.
- Worst family for the window extractor: **historical_family** at **100.0%** flips; the scope extractor scores **0.0%** there.
- The scope extractor is not clean either: its worst family is **pseudo_negation** at **41.3%** flips.

Caveat: all notes are synthetic and seeded, with polarity planted by construction; the audit measures extractor behaviour on these constructions, not performance on real clinical corpora.
