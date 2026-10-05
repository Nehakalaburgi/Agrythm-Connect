"""DEMO seed data. All farmers are fictional and all advisory text is a PLACEHOLDER.

This is not agronomic guidance. Real advisories come from SME-approved Trust AI records.
Advisory 4 is deliberately NOT approved, to test Gates 1 and 2.
"""
from __future__ import annotations

import json
import sqlite3

FARMERS = [
    # id, name, village, language
    (1, "Ramesh Yadav", "Sehore (demo)", "hi"),
    (2, "Sunita Devi", "Barabanki (demo)", "hi"),
    (3, "Mohan Patel", "Hoshangabad (demo)", "hi"),
    (4, "Anil Kumar", "Sehore (demo)", "hi"),
    (5, "Lakshmi Narayan", "Kolar (demo)", "en"),
]

# (id, farmer_id, farm name, acres, crop, stage)
CYCLES = [
    (1, 1, "North plot", 2.5, "tomato", "flowering"),
    (2, 2, "River plot", 1.0, "chilli", "vegetative"),
    (3, 3, "Main field", 3.0, "onion", "bulb formation"),
    (4, 4, "East plot", 1.5, "tomato", "fruiting"),
    (5, 5, "Hill plot", 2.0, "tomato", "vegetative"),
]

OBSERVATIONS = {
    1: "Early signs of leaf spotting on lower leaves.",
    2: "Soil surface drying quickly between irrigations.",
    3: "Bulbs sizing up evenly.",
    4: "Fruit set is good.",
    5: "Plants are leaning; no support yet.",
}


def _f(en: str, hi: str) -> dict:
    return {"en": en, "hi": hi}


ADVISORIES = [
    dict(
        id=1, cycle=1, approved=1, followup_days=3,
        en=("Remove the affected lower leaves and keep the field dry; avoid overhead watering "
            "this week. Spray neem oil at 3 ml per litre of water in the evening."),
        hi=("प्रभावित निचली पत्तियाँ हटा दें और खेत को सूखा रखें; इस हफ्ते ऊपर से पानी न दें। "
            "शाम को नीम तेल 3 मिली प्रति लीटर पानी में मिलाकर छिड़काव करें।"),
        facts={
            "dose": _f("As advised: neem oil, 3 ml per litre of water.",
                       "सलाह के अनुसार: नीम तेल, 3 मिली प्रति लीटर पानी।"),
            "timing": _f("Spray in the evening, this week.", "इसी हफ्ते शाम को छिड़काव करें।"),
            "why": _f("Removing affected leaves and keeping the field dry helps limit the spread.",
                      "प्रभावित पत्तियाँ हटाने और खेत सूखा रखने से फैलाव कम होता है।"),
        },
    ),
    dict(
        id=2, cycle=2, approved=1, followup_days=5,
        en="Irrigate lightly in the early morning on alternate days for the next two weeks.",
        hi="अगले दो हफ्ते हर दूसरे दिन सुबह जल्दी हल्की सिंचाई करें।",
        facts={
            "timing": _f("Early morning, every second day, for two weeks.",
                         "सुबह जल्दी, हर दूसरे दिन, दो हफ्ते तक।"),
            "why": _f("Light, regular watering keeps soil moisture even at this stage.",
                      "इस अवस्था में हल्की और नियमित सिंचाई से मिट्टी की नमी बराबर रहती है।"),
        },
    ),
    dict(
        id=3, cycle=3, approved=1, followup_days=4,
        en="Stop irrigation one week before harvest so the bulbs cure well.",
        hi="कटाई से एक हफ्ते पहले सिंचाई बंद कर दें ताकि प्याज़ अच्छी तरह सूखे।",
        facts={
            "phi": _f("Stop irrigation one week before harvest.",
                      "कटाई से एक हफ्ते पहले सिंचाई बंद करें।"),
            "why": _f("Dry bulbs cure better and store longer.",
                      "सूखे प्याज़ बेहतर पकते हैं और ज्यादा समय तक टिकते हैं।"),
        },
    ),
    dict(  # NOT approved: must never trigger a conversation
        id=4, cycle=4, approved=0, followup_days=3,
        en="Draft advisory awaiting SME approval.",
        hi="मसौदा सलाह, विशेषज्ञ की मंजूरी बाकी है।",
        facts={},
    ),
    dict(
        id=5, cycle=5, approved=1, followup_days=3,
        en=("Tie the plants to stakes this week and remove side shoots below the first "
            "flower cluster."),
        hi="इसी हफ्ते पौधों को डंडों से बाँधें और पहले फूल गुच्छे के नीचे की साइड शाखाएँ हटा दें।",
        facts={
            "timing": _f("Do it this week.", "यह काम इसी हफ्ते करें।"),
            "why": _f("Staking keeps fruit off the soil and improves airflow.",
                      "डंडे से फल मिट्टी से दूर रहते हैं और हवा का आना-जाना बढ़ता है।"),
        },
    ),
]


def seed_demo(conn: sqlite3.Connection) -> None:
    with conn:
        for fid, name, village, lang in FARMERS:
            conn.execute("INSERT INTO farmers(id,name,village,language,phone) VALUES(?,?,?,?,?)",
                         (fid, name, village, lang, f"+91-00000-0000{fid}"))
        for cid, fid, farm, acres, crop, stage in CYCLES:
            conn.execute("INSERT INTO farms(id,farmer_id,name,acres) VALUES(?,?,?,?)",
                         (cid, fid, farm, acres))
            conn.execute("INSERT INTO crop_cycles(id,farm_id,crop,stage,sowing_date) VALUES(?,?,?,?,?)",
                         (cid, cid, crop, stage, "2026-08-01"))
            conn.execute("INSERT INTO observations(id,crop_cycle_id,observed_by,notes,observed_at)"
                         " VALUES(?,?,?,?,?)",
                         (cid, cid, "Demo Agronomist", OBSERVATIONS[cid], "2026-09-28T10:00:00"))
        for a in ADVISORIES:
            conn.execute(
                "INSERT INTO advisories(id,crop_cycle_id,observation_id,text_en,text_hi,approved_facts,"
                "approved,approved_by,followup_days) VALUES(?,?,?,?,?,?,?,?,?)",
                (a["id"], a["cycle"], a["cycle"], a["en"], a["hi"],
                 json.dumps(a["facts"], ensure_ascii=False), a["approved"],
                 "Demo SME" if a["approved"] else None, a["followup_days"]))
