# composer.py
# Async LLM composition pipeline using Anthropic Claude.
# Handles routing by trigger kind, re-prompting on validation failures,
# and fallback JSON extraction.

import os
import json
import logging
from typing import Optional, Dict, Any

import groq
from dotenv import load_dotenv

from prompts import (
    build_universal_trigger_prompt,
    build_followup_prompt,
)
from validators import should_re_prompt, extract_json_from_response

load_dotenv()
logger = logging.getLogger(__name__)

# ============================================================================
# Client setup
# ============================================================================

_api_key = os.environ.get("GROQ_API_KEY")
if not _api_key:
    logger.warning("GROQ_API_KEY not set — LLM calls will fail.")

client = groq.AsyncGroq(api_key=_api_key)

MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_TOKENS = int(os.environ.get("COMPOSER_MAX_TOKENS", "600"))
TEMPERATURE = float(os.environ.get("COMPOSER_TEMPERATURE", "0.7"))

# ============================================================================
# Main composition entry point
# ============================================================================


async def compose_message(
    category_context: Dict[str, Any],
    merchant_context: Dict[str, Any],
    trigger_context: Dict[str, Any],
    customer_context: Optional[Dict[str, Any]] = None,
    strict: bool = False,
    previous_body: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """
    Compose a message from the four context objects.

    Returns dict with keys: body, cta, rationale
    Returns None if composition fails after all retries.
    """
    trigger_kind = trigger_context.get("kind", "generic")
    category_slug = category_context.get("slug", "generic")

    for attempt in range(3):  # up to 3 attempts (initial + 2 retries)
        use_strict = strict or (attempt > 0)  # escalate to strict on retries

        # Route to the correct prompt builder
        prompt = _build_prompt(
            trigger_kind=trigger_kind,
            category_context=category_context,
            merchant_context=merchant_context,
            trigger_context=trigger_context,
            customer_context=customer_context,
            strict=use_strict,
        )

        if not prompt:
            logger.warning(f"Empty prompt for trigger_kind={trigger_kind}, skipping.")
            return None

        # Call Claude
        raw_text = await _call_llm(prompt)
        if not raw_text:
            logger.error(f"LLM returned empty response on attempt {attempt + 1}")
            continue

        # Parse response
        result = _parse_response(raw_text)
        if not result:
            logger.warning(f"Could not parse JSON from LLM response (attempt {attempt + 1})")
            if attempt < 2:
                continue
            break

        body = result.get("body", "")
        cta = result.get("cta", "open_ended")

        # Validate and decide whether to re-prompt
        do_reprompt, error = should_re_prompt(
            body=body,
            cta=cta,
            category_slug=category_slug,
            attempt_num=attempt,
            previous_body=previous_body,
        )

        if do_reprompt:
            logger.info(f"Validation failed (attempt {attempt + 1}): {error} — re-prompting")
            continue

        # All good
        logger.info(f"Composed message on attempt {attempt + 1}: cta={cta}, len={len(body)}")
        return result

    logger.error("All composition attempts failed; returning None")
    return None


async def compose_followup(
    merchant_context: Dict[str, Any],
    category_context: Optional[Dict[str, Any]],
    conversation_history: list,
    intent: str,
) -> str:
    """
    Compose a follow-up reply in an ongoing conversation.
    Falls back to a safe canned message on failure.
    """
    if not category_context:
        category_context = {}

    prompt = build_followup_prompt(
        merchant_context=merchant_context,
        category_context=category_context,
        conversation_history=conversation_history,
        intent=intent,
    )

    raw_text = await _call_llm(prompt)
    if not raw_text:
        return _safe_fallback(intent)

    result = _parse_response(raw_text)
    if result and result.get("body"):
        return result["body"]

    # If JSON parse failed, try to use the raw text directly (trimmed)
    if raw_text and len(raw_text.strip()) <= 1000:
        return raw_text.strip()[:280]

    return _safe_fallback(intent)


# ============================================================================
# Internals
# ============================================================================


def _build_prompt(
    trigger_kind: str,
    category_context: dict,
    merchant_context: dict,
    trigger_context: dict,
    customer_context: Optional[dict],
    strict: bool,
) -> str:
    """Route to the universal prompt builder."""
    return build_universal_trigger_prompt(
        category_context=category_context,
        merchant_context=merchant_context,
        trigger_context=trigger_context,
        customer_context=customer_context,
        strict=strict,
    )


async def _call_llm(prompt: str) -> Optional[str]:
    """Call OpenAI and return the raw text response."""
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Unexpected LLM error: {e}")
    return None


def _parse_response(text: str) -> Optional[Dict[str, str]]:
    """
    Parse LLM text into a dict. Tries strict JSON first, then regex extraction.
    """
    # 1. Direct JSON parse
    try:
        data = json.loads(text.strip())
        if isinstance(data, dict) and "body" in data:
            if "thinking" in data:
                logger.info(f"Vera Thinking: {data['thinking']}")
            return data
    except json.JSONDecodeError:
        pass

    # 2. Extract JSON block from surrounding text
    json_str = extract_json_from_response(text)
    if json_str:
        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and "body" in data:
                if "thinking" in data:
                    logger.info(f"Vera Thinking: {data['thinking']}")
                return data
        except json.JSONDecodeError:
            pass

    # 3. Last resort: treat entire text as body
    stripped = text.strip()
    if stripped:
        return {
            "thinking": "Failed to parse JSON, fell back to raw text.",
            "body": stripped[:280],
            "cta": "open_ended",
            "rationale": "Extracted from non-JSON LLM response",
        }

    return None


def _safe_fallback(intent: str) -> str:
    """Return a safe canned follow-up when composition fails."""
    fallbacks = {
        "accepted": "Great! I'll get that ready for you. Give me a moment.",
        "engaging": "Happy to help! What would work best for you?",
        "ask_for_time": "No worries — I'll check back when you're ready.",
    }
    return fallbacks.get(intent, "Thanks for your reply! How can I help further?")
