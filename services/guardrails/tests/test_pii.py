import pytest

from app.pii import PiiEngine
from app.policy import load_policy


@pytest.fixture(scope="module")
def engine():
    return PiiEngine(load_policy())


def test_clean_text_is_allowed_unchanged(engine):
    verdict = engine.evaluate("What's the weather like today?")
    assert verdict.decision == "allow"
    assert verdict.entities_found == []


def test_email_is_redacted(engine):
    verdict = engine.evaluate("Reach me at jane.doe@example.com please.")
    assert verdict.decision == "allow"
    assert "EMAIL_ADDRESS" in verdict.entities_found
    assert "jane.doe@example.com" not in verdict.text
    assert "<EMAIL_ADDRESS>" in verdict.text


def test_iban_is_redacted(engine):
    verdict = engine.evaluate("Please wire it to DE89 3704 0044 0532 0130 00.")
    assert verdict.decision == "allow"
    assert "IBAN_CODE" in verdict.entities_found
    assert "<IBAN_CODE>" in verdict.text


def test_credit_card_is_blocked(engine):
    verdict = engine.evaluate("My card number is 4111 1111 1111 1111.")
    assert verdict.decision == "block"


def test_internal_codename_is_blocked(engine):
    verdict = engine.evaluate("Can you tell me about Project Nighthawk?")
    assert verdict.decision == "block"


def test_person_name_is_redacted(engine):
    verdict = engine.evaluate("My name is John Smith and I need help.")
    assert verdict.decision == "allow"
    assert "PERSON" in verdict.entities_found
    assert "<PERSON>" in verdict.text


def test_v_prefixed_cedula_is_redacted(engine):
    verdict = engine.evaluate("My ID is V-15123456.")
    assert verdict.decision == "allow"
    assert "VE_CEDULA" in verdict.entities_found
    assert "<VE_CEDULA>" in verdict.text


def test_bare_digits_with_cedula_context_are_redacted(engine):
    verdict = engine.evaluate("My cedula is 15123456.")
    assert verdict.decision == "allow"
    assert "VE_CEDULA" in verdict.entities_found
    assert "<VE_CEDULA>" in verdict.text


def test_bare_digits_without_context_are_ignored(engine):
    # Same 8-digit shape, but nothing nearby says it's a cedula — should
    # stay below score_threshold and not be reported at all.
    verdict = engine.evaluate("Please call me at 15123456 this afternoon.")
    assert verdict.decision == "allow"
    assert "VE_CEDULA" not in verdict.entities_found
    assert verdict.text == "Please call me at 15123456 this afternoon."


def test_rif_tax_id_is_redacted(engine):
    verdict = engine.evaluate("My RIF is V-15123456-0.")
    assert verdict.decision == "allow"
    assert "VE_RIF" in verdict.entities_found
    assert "<VE_RIF>" in verdict.text
