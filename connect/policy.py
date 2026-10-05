"""Safety / policy gate — Gate 3 (safety integrity).

Anything the agent says may mention a molecule, a dose, a compatibility claim or a
harvest-interval ONLY if the same token appears in the approved advisory / approved facts.
Unknown restricted terms are treated as violations (safe-biased).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

RESTRICTED_TERMS = [
    "imidacloprid", "mancozeb", "chlorpyrifos", "copper oxychloride", "carbendazim",
    "azoxystrobin", "cypermethrin", "profenofos", "acephate", "thiamethoxam", "emamectin",
    "lambda cyhalothrin", "glyphosate", "paraquat", "neem oil", "neem",
    "इमिडाक्लोप्रिड", "मैन्कोज़ेब", "मैंकोजेब", "क्लोरपायरीफॉस", "कार्बेन्डाजिम",
    "नीम तेल", "नीम का तेल",
]

_UNIT_GROUPS = {
    "ml": ["ml", "mls", "millilitre", "millilitres", "milliliter", "milliliters", "मिली", "मिलीलीटर"],
    "g": ["gm", "gms", "gram", "grams", "g", "ग्राम"],
    "kg": ["kg", "kgs", "किलो", "किलोग्राम"],
    "l": ["litre", "litres", "liter", "liters", "l", "लीटर"],
    "%": ["%"],
    "ppm": ["ppm"],
}
_UNIT_LOOKUP = {u: canon for canon, units in _UNIT_GROUPS.items() for u in units}
_UNIT_ALT = "|".join(sorted((re.escape(u) for u in _UNIT_LOOKUP), key=len, reverse=True))

DOSE_RE = re.compile(rf"(\d+(?:\.\d+)?)\s*({_UNIT_ALT})(?![a-z])", re.IGNORECASE)
PHI_TERM_RE = re.compile(
    r"(pre-?harvest interval|waiting period|\bphi\b|harvest\s+se\s+pehle|"
    r"कटाई से पहले|तोड़ने से पहले|तुड़ाई से पहले)", re.IGNORECASE)
PHI_DAYS_RE = re.compile(r"(\d+)\s*(?:days?|din|दिन)\s*(?:before|pehle|पहले)", re.IGNORECASE)
COMPAT_RE = re.compile(
    r"(tank[\s-]*mix|mix(?:ed|ing)?\s+(?:it\s+)?with|compatible|mila\s*(?:sakte|kar)|"
    r"मिला सकते|मिलाकर|संगत)", re.IGNORECASE)

_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def normalise(text: str) -> str:
    t = text.lower().replace("ँ", "ं").translate(_DEVANAGARI_DIGITS)
    return re.sub(r"\s+", " ", t).strip()


def extract_tokens(text: str) -> set[str]:
    t = normalise(text)
    tokens: set[str] = set()
    for term in RESTRICTED_TERMS:
        if normalise(term) in t:
            tokens.add(f"term:{normalise(term)}")
    for num, unit in DOSE_RE.findall(t):
        tokens.add(f"dose:{num}{_UNIT_LOOKUP[unit.lower()]}")
    for m in PHI_TERM_RE.findall(t):
        tokens.add(f"phi:{normalise(m)}")
    for m in PHI_DAYS_RE.findall(t):
        tokens.add(f"phi_days:{m}")
    for m in COMPAT_RE.findall(t):
        tokens.add(f"compat:{normalise(m)}")
    return tokens


def mentioned_inputs(text: str) -> list[str]:
    """Chemical/input names a farmer mentioned (for structured extraction)."""
    t = normalise(text)
    return sorted({normalise(term) for term in RESTRICTED_TERMS if normalise(term) in t})


@dataclass
class PolicyResult:
    allowed: bool
    violations: list[str]


def check_reply(reply: str, approved_corpus: str) -> PolicyResult:
    violations = sorted(extract_tokens(reply) - extract_tokens(approved_corpus))
    return PolicyResult(allowed=not violations, violations=violations)
