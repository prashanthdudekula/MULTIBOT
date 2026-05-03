# tests/test_composer.py
# Unit tests for the composition pipeline and validators.
# Run: pytest tests/ -v

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# ============================================================================
# Sample fixtures
# ============================================================================

CATEGORY_CTX = {
    "slug": "dentists",
    "voice": {
        "tone": "clinical-professional",
        "taboos": ["guarantee", "cure"],
    },
    "digest": [
        {
            "title": "JIDA Oct 2024: Fluoride varnish reduces caries by 38%",
            "source": "JIDA",
            "summary": "Fluoride varnish applications in school children showed 38% caries reduction.",
            "trial_n": 1200,
            "finding": "38% caries reduction with bi-annual fluoride varnish",
        }
    ],
}

MERCHANT_CTX = {
    "merchant_id": "m_001",
    "category_slug": "dentists",
    "identity": {
        "name": "Dr. Meera",
        "language_pref": "en",
        "category": "dentists",
    },
    "performance": {
        "ctr": 0.018,
        "views_last_30d": 430,
    },
    "offers": [
        {"title": "Scaling + Polish ₹799", "status": "active"},
    ],
}

TRIGGER_RESEARCH = {
    "kind": "research_digest",
    "merchant_id": "m_001",
    "source": "JIDA",
    "suppression_key": "research_m_001_jida_oct",
    "payload": {},
}

TRIGGER_PERF = {
    "kind": "perf_spike",
    "merchant_id": "m_001",
    "suppression_key": "perf_m_001",
    "payload": {
        "delta_pct": 35,
        "metric": "profile views",
        "reason": "magicpin promo boost",
    },
}

MOCK_LLM_RESPONSE = json.dumps({
    "body": "Dr. Meera, JIDA Oct: fluoride varnish cut caries 38% (n=1200). I've drafted a patient-ed WhatsApp for your clinic — reply YES to send?",
    "cta": "yes_no_choice",
    "rationale": "Cited JIDA finding using effort_extern lever; binary CTA in last sentence.",
})


# ============================================================================
# Validator tests
# ============================================================================


def test_validate_empty_body():
    from validators import validate_message
    valid, err = validate_message("", "open_ended", "dentists")
    assert not valid
    assert "Empty" in err


def test_validate_body_too_long():
    from validators import validate_message
    long_body = "A" * 300
    valid, err = validate_message(long_body, "open_ended", "dentists")
    assert not valid
    assert "exceeds" in err.lower() or "long" in err.lower()


def test_validate_long_preamble():
    from validators import validate_message
    body = "I hope this finds you well. Check out this offer."
    valid, err = validate_message(body, "open_ended", "dentists")
    assert not valid
    assert "preamble" in err.lower()


def test_validate_generic_offer():
    from validators import validate_message
    body = "Get 30% off your next visit. Reply YES."
    valid, err = validate_message(body, "yes_no_choice", "dentists")
    assert not valid
    assert "generic offer" in err.lower()


def test_validate_clinical_taboo():
    from validators import validate_message
    body = "Our treatment is guaranteed to cure your pain. Reply YES."
    valid, err = validate_message(body, "yes_no_choice", "dentists")
    assert not valid
    assert "taboo" in err.lower()


def test_validate_verbatim_repeat():
    from validators import validate_message
    body = "Dr. Meera, check this out. Reply YES."
    valid, err = validate_message(body, "yes_no_choice", "dentists", previous_body=body)
    assert not valid
    assert "repetition" in err.lower()


def test_validate_good_message():
    from validators import validate_message
    body = "Dr. Meera, JIDA Oct: fluoride varnish cut caries 38% (n=1200). Want me to draft a patient-ed post? Reply YES."
    valid, err = validate_message(body, "yes_no_choice", "dentists")
    assert valid, f"Expected valid but got: {err}"


# ============================================================================
# Prompt builder tests
# ============================================================================


def test_universal_trigger_prompt_contains_key_fields():
    from prompts import build_universal_trigger_prompt
    prompt = build_universal_trigger_prompt(CATEGORY_CTX, MERCHANT_CTX, TRIGGER_RESEARCH)
    assert "Dr. Meera" in prompt
    assert "dentists" in prompt
    assert "JSON" in prompt


def test_universal_perf_spike_prompt_contains_delta():
    from prompts import build_universal_trigger_prompt
    prompt = build_universal_trigger_prompt(CATEGORY_CTX, MERCHANT_CTX, TRIGGER_PERF)
    assert "35" in prompt
    assert "perf_spike" in prompt


def test_universal_prompt_with_customer():
    from prompts import build_universal_trigger_prompt
    customer_ctx = {
        "identity": {"name": "Rahul", "language_pref": "hi"}
    }
    trigger = {"kind": "recall_due", "scope": "customer"}
    prompt = build_universal_trigger_prompt(CATEGORY_CTX, MERCHANT_CTX, trigger, customer_context=customer_ctx)
    assert "Rahul" in prompt
    assert "hi" in prompt
    assert "TO customer" in prompt


# ============================================================================
# Composer integration tests (mocked LLM)
# ============================================================================


@pytest.mark.asyncio
async def test_compose_message_research_digest():
    """End-to-end composition with mocked Groq response."""
    mock_message = MagicMock()
    mock_message.content = MOCK_LLM_RESPONSE

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("composer.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        from composer import compose_message
        result = await compose_message(
            category_context=CATEGORY_CTX,
            merchant_context=MERCHANT_CTX,
            trigger_context=TRIGGER_RESEARCH,
        )

    assert result is not None
    assert "body" in result
    assert len(result["body"]) > 0
    assert result["cta"] == "yes_no_choice"


@pytest.mark.asyncio
async def test_compose_message_returns_none_on_llm_failure():
    """Composer should return None if LLM keeps failing."""
    with patch("composer.client") as mock_client:
        mock_client.messages.create = AsyncMock(side_effect=Exception("API down"))

        from composer import compose_message
        result = await compose_message(
            category_context=CATEGORY_CTX,
            merchant_context=MERCHANT_CTX,
            trigger_context=TRIGGER_RESEARCH,
        )

    assert result is None


@pytest.mark.asyncio
async def test_compose_followup_accepted():
    """Follow-up composition when merchant accepts."""
    mock_content = MagicMock()
    mock_content.text = json.dumps({
        "body": "Great! Sending the fluoride varnish patient-ed post now.",
        "cta": "open_ended",
        "rationale": "Merchant accepted; advancing."
    })
    mock_response = MagicMock()
    mock_response.content = [mock_content]

    with patch("composer.client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        from composer import compose_followup
        body = await compose_followup(
            merchant_context=MERCHANT_CTX,
            category_context=CATEGORY_CTX,
            conversation_history=[
                {"role": "vera", "message": "JIDA Oct research digest. Reply YES?", "timestamp": "2024-10-01"},
                {"role": "merchant", "message": "Yes, send it", "timestamp": "2024-10-01"},
            ],
            intent="accepted",
        )

    assert isinstance(body, str)
    assert len(body) > 0


# ============================================================================
# State / suppression tests
# ============================================================================


def test_suppression_lifecycle():
    from state import ContextStore
    s = ContextStore()
    assert not s.is_suppressed("key_abc")
    s.mark_suppressed("key_abc")
    assert s.is_suppressed("key_abc")


def test_context_version_conflict():
    from state import ContextStore
    import pytest
    s = ContextStore()
    s.store_context("merchant", "m_001", 2, {"data": "v2"})
    with pytest.raises(ValueError):
        s.store_context("merchant", "m_001", 1, {"data": "v1"})  # stale


def test_conversation_turns():
    from state import ContextStore
    s = ContextStore()
    s.create_conversation("conv_abc")
    s.add_turn("conv_abc", "vera", "Hello!")
    s.add_turn("conv_abc", "merchant", "Hi there")
    turns = s.get_conversation("conv_abc")
    assert len(turns) == 2
    assert turns[0]["role"] == "vera"
    assert s.get_last_bot_message("conv_abc") == "Hello!"
