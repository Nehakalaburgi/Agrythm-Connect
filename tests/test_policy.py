from connect.policy import check_reply, extract_tokens, mentioned_inputs

CORPUS = ("Spray neem oil at 3 ml per litre of water in the evening.\n"
          "नीम तेल 3 मिली प्रति लीटर पानी में मिलाकर छिड़काव करें।")


def allowed(reply: str) -> bool:
    return check_reply(reply, CORPUS).allowed


def test_approved_dose_and_molecule_are_allowed():
    assert allowed("As advised: neem oil, 3 ml per litre of water.")
    assert allowed("सलाह के अनुसार: नीम तेल, 3 मिली प्रति लीटर पानी।")
    assert allowed("3 millilitres of neem oil")  # unit synonyms normalise


def test_unapproved_molecule_is_blocked():
    for text in ["Use chlorpyrifos this week.", "imidacloprid works well", "क्लोरपायरीफॉस डाल दें"]:
        assert not allowed(text), text


def test_unapproved_or_changed_dose_is_blocked():
    assert not allowed("Spray 5 ml per litre")
    assert not allowed("neem oil 13 ml per litre")  # 13 must not match 3
    assert not allowed("neem oil 3 ml per litre, or 10 g of powder")
    assert not allowed("5 मिली प्रति लीटर")
    assert not allowed("use 2.5 kg per acre")


def test_compatibility_claims_are_blocked():
    assert not allowed("You can tank mix it with your fungicide.")
    assert not allowed("yeh dawa dusri dawa ke saath mila sakte hain, it is compatible")


def test_harvest_interval_claims_are_blocked():
    assert not allowed("Wait 7 days before harvest.")
    assert not allowed("The PHI is short.")
    assert not allowed("तोड़ने से पहले इंतज़ार करें")


def test_plain_safe_text_is_allowed():
    assert allowed("Remove the affected lower leaves and keep the field dry.")
    assert allowed("Thank you. Your response has been recorded. 2.5 acres noted.")


def test_dose_in_corpus_is_allowed_but_not_other_numbers_of_same_unit():
    assert extract_tokens("3 ml") <= extract_tokens(CORPUS)
    assert not extract_tokens("30 ml") <= extract_tokens(CORPUS)


def test_mentioned_inputs_extracts_farmer_named_chemicals():
    assert mentioned_inputs("can I use Imidacloprid instead?") == ["imidacloprid"]
    assert mentioned_inputs("kitna daalna hai") == []
