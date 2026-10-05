"""Understanding + reply adapter (provider-replaceable). See ADR 0001.

TRL 3 ships a deterministic, free, offline RuleBasedAdapter for English, Hindi (Devanagari)
and Hinglish (Roman Hindi). Free LLM tiers plug in behind the same `LLMAdapter` at TRL 4.
Anything an adapter composes is checked by the policy gate before the farmer hears it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol

from .context import ContextPack


@dataclass
class Understanding:
    intent: str  # confirm | done | delay | reject | new_issue | question | not_understood | unclear
    topic: str | None = None  # for questions: decision | phi | mixing | dose | timing | why | other
    confidence: float = 0.0
    entities: dict = field(default_factory=dict)


class LLMAdapter(Protocol):
    name: str

    def understand(self, utterance: str, ctx: ContextPack) -> Understanding: ...

    def compose(self, kind: str, ctx: ContextPack, **kw) -> str: ...


# --------------------------------------------------------------------------- templates
CROP_HI = {"tomato": "टमाटर", "chilli": "मिर्च", "onion": "प्याज़", "wheat": "गेहूं"}

TEMPLATES: dict[str, dict[str, str]] = {
    "greeting": {
        "hi": ("नमस्ते {name} जी, यह Agrythm की तरफ़ से कॉल है। गुणवत्ता और रिकॉर्ड के लिए यह बातचीत "
               "दर्ज की जा सकती है। हमारे विशेषज्ञ ने आपके {crop} के खेत का दौरा किया था। उनकी "
               "सलाह यह है: {advisory} क्या आप यह समझ गए?"),
        "en": ("Hello {name}, this is a call from Agrythm. This conversation may be recorded for "
               "quality and records. Our expert recently visited your {crop} field. Their advice: "
               "{advisory} Did you understand?"),
    },
    "re_explain": {
        "hi": "कोई बात नहीं, दोबारा सुनिए: {advisory} क्या अब बात साफ़ हुई?",
        "en": "No problem, let me say it again: {advisory} Is that clear now?",
    },
    "ask_clarify": {
        "hi": "माफ़ कीजिए, बात साफ़ नहीं हो पाई। क्या आप यह सलाह अपनाएंगे: हाँ या ना?",
        "en": "Sorry, I did not catch that. Will you follow this advice: yes or no?",
    },
    "answer": {
        "hi": "{fact} क्या आप यह कर पाएंगे?",
        "en": "{fact} Will you be able to do this?",
    },
    # Closing messages are fixed templates; they never pass through an adapter.
    "closing_completed": {
        "hi": "धन्यवाद {name} जी। आपका जवाब दर्ज कर लिया गया है।",
        "en": "Thank you, {name}. Your response has been recorded.",
    },
    "closing_followup": {
        "hi": "ठीक है {name} जी, हम {days} दिन बाद दोबारा संपर्क करेंगे।",
        "en": "Okay {name}, we will get back to you in {days} days.",
    },
    "closing_escalation": {
        "hi": "यह बात हमारे कृषि विशेषज्ञ तक पहुँचा रहे हैं। वे जल्द आपसे संपर्क करेंगे। धन्यवाद।",
        "en": "I am passing this to our agronomy expert. They will contact you soon. Thank you.",
    },
    "closing_unresolved": {
        "hi": "आपसे बात पूरी नहीं हो पाई। हम दोबारा संपर्क करेंगे। धन्यवाद।",
        "en": "We could not finish our conversation. We will contact you again. Thank you.",
    },
}


def render(kind: str, ctx: ContextPack, **kw) -> str:
    crop = CROP_HI.get(ctx.crop, ctx.crop) if ctx.language == "hi" else ctx.crop
    fields = dict(name=ctx.farmer_name, crop=crop, advisory=ctx.advisory_text, **kw)
    if "topic" in kw and "fact" not in kw:
        fields["fact"] = ctx.fact(kw["topic"]) or ""
    return TEMPLATES[kind][ctx.language].format(**fields)


# --------------------------------------------------------------------------- understanding
def _canon(text: str) -> str:
    t = text.lower().replace("'", "").replace("’", "").replace("ँ", "ं")
    t = t.replace("no problem", "ok").replace("not a problem", "ok")
    t = re.sub(r"[^\wऀ-ॿ\s%]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    padded = f" {t} "
    for a, b in ((" नही ", " नहीं "), (" नहि ", " नहीं "), (" करुंगा ", " करूंगा "),
                 (" करुंगी ", " करूंगी "), (" nahin ", " nahi "), (" nai ", " nahi ")):
        padded = padded.replace(a, b)
    return padded.strip()


def _has(c: str, phrases: list[str]) -> str | None:
    padded = f" {c} "
    for p in phrases:
        if f" {p} " in padded:
            return p
    return None


NOT_UNDERSTOOD = [
    "samajh nahi", "samjha nahi", "samjh nahi", "samajh nahi aaya", "samajh nahi paya", "phir se",
    "dobara", "dubara", "repeat", "again", "kya bola", "kya kaha", "didnt understand",
    "did not understand", "dont understand", "do not understand", "not clear", "cant understand",
    "cant follow", "pardon", "slowly", "समझ नहीं", "समझा नहीं", "फिर से", "दोबारा", "दुबारा",
    "क्या बोला", "क्या कहा",
]
NEW_ISSUE = [
    "naya problem", "new problem", "problem", "dikkat", "samasya", "keede", "keeda", "kide",
    "peele", "peeli", "pili", "pila", "yellow", "yellowing", "sookh", "sukh", "sookhne", "wilt",
    "wilting", "murjha", "murjhaa", "daag", "dhabbe", "spots", "bimari", "disease", "pest",
    "pests", "insects", "rog", "कीड़े", "कीड़ा", "पीली", "पीले", "पीला", "सूख", "समस्या", "बीमारी",
    "दाग", "धब्बे", "मुरझा", "रोग", "दिक्कत",
]
TOPIC_KEYWORDS: list[tuple[str, list[str]]] = [
    ("decision", ["double", "dugna", "dugni", "duguna", "zyada", "jyada", "badha", "badhao",
                  "alag dawa", "dusri dawa", "doosri dawa", "kaunsi dawa", "konsi dawa",
                  "which spray", "which pesticide", "which medicine", "what should i spray",
                  "what to spray", "instead", "replace", "badal", "badle", "switch", "daal du",
                  "dal du", "daal dun", "daalun", "dalun", "daal doon", "दुगना", "दुगुना",
                  "ज्यादा", "बढ़ा", "दूसरी दवा", "कौन सी दवा", "कौनसी दवा", "बदल", "डाल दूं"]),
    ("phi", ["harvest", "harvesting", "tod", "todne", "tudai", "tudaai", "waiting period", "phi",
             "कटाई", "तोड़", "तोड़ने", "तुड़ाई"]),
    ("mixing", ["mila", "milake", "milana", "mix", "mixing", "together", "compatible",
                "मिला", "मिलाकर", "मिलाना"]),
    ("dose", ["kitna", "kitni", "dose", "dosage", "quantity", "matra", "ml", "litre", "liter",
              "gram", "how much", "कितना", "कितनी", "मात्रा", "डोज"]),
    ("timing", ["kab", "when", "samay", "kitne din", "kis din", "what time", "कब", "समय",
                "कितने दिन"]),
    ("why", ["kyun", "kyon", "kyu", "why", "kis liye", "kisliye", "क्यों", "क्यूं", "क्यु"]),
]
Q_WORDS = ["kya", "kitna", "kitni", "kitne", "kab", "kaise", "kyun", "kyon", "kyu", "kaun",
           "kaunsi", "konsi", "how", "when", "why", "which", "what", "can", "should", "क्या",
           "कितना", "कितनी", "कितने", "कब", "कैसे", "क्यों", "क्यूं", "कौन"]
REJECT = [
    "nahi karunga", "nahi karungi", "nahi kar sakta", "nahi kar sakti", "nahi kar paunga",
    "nahi kar sakte", "nahi karenge", "nahi karna", "nahi chahiye", "mana", "wont", "cant",
    "cannot", "afford", "paisa nahi", "paise nahi", "नहीं करूंगा", "नहीं करूंगी", "नहीं कर सकता",
    "नहीं कर सकती", "नहीं करना", "नहीं चाहिए", "पैसे नहीं", "पैसा नहीं", "मना",
]
BARE_NO = {"nahi", "no", "na", "nope", "नहीं", "ना"}
DELAY = [
    "kal", "baad mein", "baad me", "later", "tomorrow", "parso", "agle hafte", "next week",
    "thodi der", "abhi nahi", "not now", "time nahi", "vyast", "busy", "कल", "बाद में", "परसों",
    "अगले हफ्ते", "अभी नहीं", "व्यस्त",
]
DONE = [
    "kar diya", "ho gaya", "kar chuka", "kar chuki", "kar liya", "kar di", "already", "done",
    "did it", "completed", "finished", "कर दिया", "हो गया", "कर चुका", "कर चुकी", "कर लिया",
]
CONFIRM = [
    "haan", "han", "ha", "haa", "ji", "ji haan", "theek hai", "thik hai", "theek", "samajh gaya",
    "samajh gayi", "samjha", "samajh aa gaya", "ok", "okay", "yes", "yeah", "sure", "kar dunga",
    "karunga", "karungi", "kar lunga", "kar lungi", "kar denge", "will do", "i will", "alright",
    "bilkul", "हां", "जी", "ठीक है", "ठीक", "समझ गया", "समझ गई", "समझ आ गया", "कर दूंगा",
    "करूंगा", "करूंगी", "कर लूंगा", "बिलकुल",
]


def _delay_days(c: str) -> int:
    if _has(c, ["agle hafte", "next week", "अगले हफ्ते"]):
        return 7
    if _has(c, ["parso", "परसों"]):
        return 2
    if _has(c, ["kal", "tomorrow", "कल"]):
        return 1
    return 2


def _barrier(c: str) -> str:
    if _has(c, ["paisa", "paise", "पैसा", "पैसे", "afford", "cost", "mehnga", "महंगा"]):
        return "cost"
    if _has(c, ["time", "samay", "busy", "vyast", "व्यस्त", "समय"]):
        return "time"
    if _has(c, ["labour", "majdoor", "मजदूर"]):
        return "labour"
    if _has(c, ["available", "uplabdh", "उपलब्ध", "milta", "मिलता"]):
        return "input_unavailable"
    return "unspecified"


def _topic(c: str) -> str | None:
    for topic, words in TOPIC_KEYWORDS:
        if _has(c, words):
            return topic
    return None


class RuleBasedAdapter:
    name = "rule-based"

    def understand(self, utterance: str, ctx: ContextPack) -> Understanding:
        c = _canon(utterance)
        if not c:
            return Understanding("unclear", None, 0.2)
        if _has(c, NOT_UNDERSTOOD):
            return Understanding("not_understood", None, 0.9)
        sym = _has(c, NEW_ISSUE)
        if sym:
            return Understanding("new_issue", None, 0.85, {"symptom": sym})

        topic = _topic(c)
        is_q = bool(_has(c, Q_WORDS)) or ("?" in utterance and topic is not None)
        # Safety bias: anything touching decisions, harvest intervals or mixing is a question.
        if topic in ("decision", "phi", "mixing") or is_q:
            if topic:
                return Understanding("question", topic, 0.85, {"topic": topic})
            return Understanding("question", "other", 0.7, {"topic": "other"})

        if c in BARE_NO:
            return Understanding("reject", None, 0.45, {"barrier": "unspecified"})
        if _has(c, REJECT):
            return Understanding("reject", None, 0.9, {"barrier": _barrier(c)})
        if _has(c, DELAY):
            return Understanding("delay", None, 0.9, {"delay_days": _delay_days(c)})
        if _has(c, DONE):
            return Understanding("done", None, 0.9, {"action_status": "done"})
        if _has(c, CONFIRM):
            return Understanding("confirm", None, 0.88, {"action_status": "acknowledged"})
        return Understanding("unclear", None, 0.2)

    def compose(self, kind: str, ctx: ContextPack, **kw) -> str:
        return render(kind, ctx, **kw)
