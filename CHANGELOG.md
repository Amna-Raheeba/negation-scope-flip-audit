# Changelog

## 0.1.0 — 2026-11-21

- Initial release.
- Seeded generator of synthetic clinical notes with planted finding
  polarity: 8 negation-scope trap families (coordination beyond
  window, pseudo-negation, historical/family framing, double
  negation, subordinate clause, postposed negation, contrastive scope
  break, long-distance scope) plus plain positive/negative controls.
- Three extractors over one shared mention finder: a keyword baseline
  with no negation handling, a simplified NegEx-style fixed-window
  extractor, and a dependency-lite clause-scope extractor with
  double-negation cancellation and history/family attribution.
- Span-matched audit that reports the polarity-flip rate per trap
  family per extractor, with per-mention flip details.
- Headline evaluation: 1,500 notes / 2,129 planted mentions; keyword
  flips 65.6% of trap mentions, window 55.4%, scope 4.0%; both
  negation-aware extractors flip 41.3% of pseudo-negations (a shared
  lexicon gap, reported as such).
- Streamlit dashboard (3 tabs), CLI, notebooks, and a reproducibility
  script with a headline-drift guard.
