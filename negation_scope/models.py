"""Data model and lexicon for the negation-scope flip audit.

A *note* is a short synthetic clinical sentence (all text is generated,
no real patient data). A *mention* is one planted finding inside a note,
with a token span and a ground-truth polarity: whether the finding is
asserted as a current finding of the patient (``present``) or not
(``absent``). Extractors read only the note text; the audit compares
their polarity calls against the planted ground truth.

Author: Amna Raheeba
"""

import re
from dataclasses import dataclass, field

PRESENT = "present"
ABSENT = "absent"
POLARITIES = (PRESENT, ABSENT)

TOKEN_RE = re.compile(r"[A-Za-z0-9']+|[^\sA-Za-z0-9]")


def tokenize(text):
    """Split text into lowercase word / punctuation tokens."""
    return TOKEN_RE.findall(text.lower())


def render(tokens):
    """Render a token list back into readable text.

    Inverse of :func:`tokenize` for the token streams the generator
    builds: punctuation reattaches to the previous word and the first
    letter is capitalised, neither of which changes the token stream.
    """
    text = " ".join(tokens)
    for punct in (",", ".", ";", ":", "!", "?"):
        text = text.replace(" " + punct, punct)
    if text:
        text = text[0].upper() + text[1:]
    return text


# Finding lexicon: canonical name -> surface token sequence.
FINDINGS = {
    "fever": ["fever"],
    "cough": ["cough"],
    "dyspnea": ["dyspnea"],
    "chest pain": ["chest", "pain"],
    "wheeze": ["wheeze"],
    "crackles": ["crackles"],
    "edema": ["edema"],
    "nausea": ["nausea"],
    "headache": ["headache"],
    "rash": ["rash"],
    "fatigue": ["fatigue"],
    "pneumonia": ["pneumonia"],
    "pleural effusion": ["pleural", "effusion"],
    "consolidation": ["consolidation"],
    "tachycardia": ["tachycardia"],
    "hypoxia": ["hypoxia"],
    "hypertension": ["hypertension"],
    "diabetes": ["diabetes"],
    "anemia": ["anemia"],
    "sore throat": ["sore", "throat"],
    "abdominal pain": ["abdominal", "pain"],
    "dizziness": ["dizziness"],
    "vomiting": ["vomiting"],
    "hemoptysis": ["hemoptysis"],
}

FINDING_NAMES = sorted(FINDINGS)


@dataclass
class Mention:
    """One planted finding mention with ground-truth polarity."""

    finding: str
    start: int
    end: int
    polarity: str
    family: str

    def to_dict(self):
        return {
            "finding": self.finding,
            "start": self.start,
            "end": self.end,
            "polarity": self.polarity,
            "family": self.family,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            finding=data["finding"],
            start=data["start"],
            end=data["end"],
            polarity=data["polarity"],
            family=data["family"],
        )


@dataclass
class Note:
    """A synthetic clinical note with planted gold mentions."""

    note_id: str
    family: str
    text: str
    tokens: list = field(default_factory=list)
    mentions: list = field(default_factory=list)

    def to_dict(self):
        return {
            "note_id": self.note_id,
            "family": self.family,
            "text": self.text,
            "tokens": list(self.tokens),
            "mentions": [mention.to_dict() for mention in self.mentions],
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            note_id=data["note_id"],
            family=data["family"],
            text=data["text"],
            tokens=list(data["tokens"]),
            mentions=[Mention.from_dict(item) for item in data["mentions"]],
        )


@dataclass
class Prediction:
    """One extractor polarity call for one mention span."""

    finding: str
    start: int
    end: int
    polarity: str

    def key(self):
        return (self.start, self.end, self.finding)
