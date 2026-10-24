"""Builds the spoken message. Pure function: weather + farmer in, text out. No provider calls.

The voice always says it is an AI. Hindi wording is a DRAFT and needs native-speaker review (see docs/DECISIONS.md).
"""
from __future__ import annotations

from .contracts import FarmerContext, Language, WeatherReport

WORDS_PER_SECOND = 2.4  # rough speaking pace; replaced by real measured length once TTS is connected

_EN = (
    "Hello {name}. This is an automated voice assistant from Agrythm. I am an AI, not a person. "
    "Here is today's weather for {place}. It will be {summary}. "
    "The temperature will be between {tmin} and {tmax} degrees Celsius. "
    "The chance of rain is {rain} percent. "
    "Please plan your farm work for today with this in mind. "
    "I will call every morning like this with the weather. "
    "If you do not want these calls, please tell your Agrythm contact person. "
    "Thank you for listening. Have a good day."
)

_HI = (
    "नमस्ते {name}। मैं एग्रिदम की ओर से बोल रही एआई आवाज़ हूँ, कोई इंसान नहीं हूँ। "
    "यह {place} का आज का मौसम है। आज मौसम {summary} रहेगा। "
    "तापमान {tmin} से {tmax} डिग्री सेल्सियस के बीच रहेगा। "
    "बारिश की संभावना {rain} प्रतिशत है। "
    "कृपया आज के खेत के काम इसी हिसाब से तय करें। "
    "मैं हर सुबह इसी तरह मौसम की जानकारी देने के लिए फ़ोन करूँगी। "
    "अगर आप ये कॉल नहीं चाहते, तो कृपया अपने एग्रिदम संपर्क व्यक्ति को बता दें। "
    "सुनने के लिए धन्यवाद। आपका दिन शुभ हो।"
)


def build_message(farmer: FarmerContext, weather: WeatherReport) -> str:
    template = _HI if farmer.language is Language.HI else _EN
    return template.format(
        name=farmer.display_name, place=weather.place_name, summary=weather.summary,
        tmin=weather.temp_min_c, tmax=weather.temp_max_c, rain=weather.rain_chance_pct,
    )


def estimate_seconds(text: str) -> float:
    return len(text.split()) / WORDS_PER_SECOND
