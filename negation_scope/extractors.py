"""Three finding extractors that differ only in negation handling.

All three share the same mention finder (exact surface-form matching
over the token stream), so the audit isolates one variable: how
polarity is decided for a mention that was found.

- ``keyword``: no negation handling at all -- every mention is present.
  This is the baseline a pipeline gets when negation is ignored.
- ``window``: a simplified NegEx-style extractor. A mention is negated
  when an active negation trigger appears within a fixed token window
  before it (or a short window after it), with no sentence terminator
  in between. Pseudo-negation phrases ("no change", "not only") make a
  trigger inert, as in NegEx. Documented simplification: scope ends
  only at sentence punctuation, never at conjunctions or clause
  boundaries -- which is exactly where the trap families bite.
- ``scope``: a dependency-lite scope extractor. The note is segmented
  into clause regions (sentence punctuation, contrastive conjunctions,
  and subordinate / relative clause boundaries are barriers); a trigger
  scopes over its whole region, on either side of the mention;
  coordinated lists therefore stay in scope at any distance, and scope
  never leaks across a clause boundary. Two active triggers covering a
  mention cancel (double negation). Mentions inside a family-history
  or resolved-history frame are attributed away from the patient.

Both negation-aware extractors share one trigger lexicon and one
pseudo-negation list, so the comparison is about scope computation,
not about who has the bigger dictionary.
"""

from .models import ABSENT, FINDINGS, PRESENT, Prediction, tokenize

# Negation triggers as token sequences, longest first for matching.
TRIGGERS = (
    ("negative", "for"),
    ("free", "of"),
    ("clear", "of"),
    ("rules", "out"),
    ("rule", "out"),
    ("ruled", "out"),
    ("cannot",),
    ("denies",),
    ("denied",),
    ("deny",),
    ("without",),
    ("absent",),
    ("never",),
    ("none",),
    ("not",),
    ("no",),
    ("excludes",),
    ("excluded",),
)

# Phrases whose apparent trigger negates nothing (NegEx pseudo-negation).
PSEUDO_NEGATIONS = (
    ("no", "significant", "change"),
    ("no", "change"),
    ("no", "increase"),
    ("not", "only"),
    ("not", "cause"),
)

PRE_WINDOW = 4
POST_WINDOW = 3
_SENTENCE_END = (".", ";")
_CONTRASTIVES = ("but", "however", "yet", "nevertheless", "instead")
_SUBORDINATORS = (
    "although", "though", "while", "when", "because", "since", "if",
    "unless",
)
_RELATIVE_PRONOUNS = ("who", "which")
_KINSHIP = ("mother", "father", "sister", "brother")


def find_mentions(tokens):
    """Find every finding surface form in the token stream."""
    found = []
    for name in sorted(FINDINGS):
        surface = FINDINGS[name]
        width = len(surface)
        for start in range(0, len(tokens) - width + 1):
            if list(tokens[start:start + width]) == surface:
                found.append((name, start, start + width))
    found.sort(key=lambda item: (item[1], item[2], item[0]))
    return found


def _match_phrases(tokens, phrases):
    """Return (start, end) spans of every phrase occurrence."""
    spans = []
    for phrase in phrases:
        width = len(phrase)
        for start in range(0, len(tokens) - width + 1):
            if tuple(tokens[start:start + width]) == phrase:
                spans.append((start, start + width))
    return spans


def find_triggers(tokens):
    """Return active trigger spans; pseudo-negation triggers are inert."""
    pseudo_starts = set(
        start for start, _end in _match_phrases(tokens, PSEUDO_NEGATIONS)
    )
    triggers = []
    for start, end in _match_phrases(tokens, TRIGGERS):
        if start in pseudo_starts:
            continue
        triggers.append((start, end))
    triggers.sort()
    return triggers


def extract_keyword(tokens):
    """Baseline: every found mention is present."""
    return [
        Prediction(name, start, end, PRESENT)
        for name, start, end in find_mentions(tokens)
    ]


def _window_negated(triggers, mention_start, mention_end, tokens):
    for trig_start, trig_end in triggers:
        if trig_end <= mention_start:
            distance = mention_start - trig_end
            between = tokens[trig_end:mention_start]
            if distance <= PRE_WINDOW and not any(
                tok in _SENTENCE_END for tok in between
            ):
                return True
        elif trig_start >= mention_end:
            distance = trig_start - mention_end
            between = tokens[mention_end:trig_start]
            if distance <= POST_WINDOW and not any(
                tok in _SENTENCE_END for tok in between
            ):
                return True
    return False


def extract_window(tokens):
    """NegEx-style fixed-window extractor."""
    triggers = find_triggers(tokens)
    predictions = []
    for name, start, end in find_mentions(tokens):
        negated = _window_negated(triggers, start, end, tokens)
        predictions.append(
            Prediction(name, start, end, ABSENT if negated else PRESENT)
        )
    return predictions


def _barrier_gaps(tokens):
    """Gap indices a negation scope cannot cross.

    A gap ``g`` sits between token ``g - 1`` and token ``g``. Barriers:
    after sentence punctuation; before a contrastive conjunction; the
    comma closing a sentence-initial subordinate clause; and the commas
    bounding a relative clause.
    """
    gaps = set()
    count = len(tokens)
    for index, tok in enumerate(tokens):
        if tok in _SENTENCE_END:
            gaps.add(index + 1)
        if tok in _CONTRASTIVES:
            gaps.add(index)
    # Sentence-initial subordinate clause: first comma closes it.
    sentence_start = 0
    for index in range(count + 1):
        if index == count or tokens[index] in _SENTENCE_END:
            if (sentence_start < count
                    and tokens[sentence_start] in _SUBORDINATORS):
                for pos in range(sentence_start, index):
                    if tokens[pos] == ",":
                        gaps.add(pos + 1)
                        break
            sentence_start = index + 1
    # Relative clauses: comma + who/which ... next comma.
    for index in range(count - 1):
        if tokens[index] == "," and tokens[index + 1] in _RELATIVE_PRONOUNS:
            gaps.add(index)
            for pos in range(index + 2, count):
                if tokens[pos] == ",":
                    gaps.add(pos + 1)
                    break
                if tokens[pos] in _SENTENCE_END:
                    break
    return gaps


def _regions(tokens):
    """Split token indices into clause regions at barrier gaps."""
    gaps = _barrier_gaps(tokens)
    regions = []
    current = []
    for index in range(len(tokens)):
        if index in gaps and current:
            regions.append(current)
            current = []
        current.append(index)
    if current:
        regions.append(current)
    return regions


def _region_of(regions, position):
    for region in regions:
        if region[0] <= position <= region[-1]:
            return region
    return [position]


def _is_attributed(tokens, region, mention_start):
    """True when the mention is framed as someone else's / resolved."""
    region_tokens = [tokens[i] for i in region]
    before = [tokens[i] for i in region if i < mention_start]
    if "family" in region_tokens:
        return True
    if any(tok in _KINSHIP for tok in before):
        return True
    for pos in range(len(before) - 1):
        if before[pos] == "history" and before[pos + 1] == "of":
            return True
    if "previously" in before:
        return True
    after = [tokens[i] for i in region if i >= mention_start]
    if "resolved" in after:
        return True
    return False


def extract_scope(tokens):
    """Dependency-lite clause-scope extractor."""
    triggers = find_triggers(tokens)
    regions = _regions(tokens)
    predictions = []
    for name, start, end in find_mentions(tokens):
        region = _region_of(regions, start)
        covering = [
            span for span in triggers
            if region[0] <= span[0] and span[1] - 1 <= region[-1]
        ]
        if covering:
            polarity = ABSENT if len(covering) % 2 == 1 else PRESENT
        elif _is_attributed(tokens, region, start):
            polarity = ABSENT
        else:
            polarity = PRESENT
        predictions.append(Prediction(name, start, end, polarity))
    return predictions


EXTRACTORS = {
    "keyword": extract_keyword,
    "window": extract_window,
    "scope": extract_scope,
}

EXTRACTOR_NAMES = ("keyword", "window", "scope")


def extract(extractor_name, text):
    """Run one extractor over raw note text."""
    if extractor_name not in EXTRACTORS:
        raise ValueError("unknown extractor: %s" % extractor_name)
    return EXTRACTORS[extractor_name](tokenize(text))
