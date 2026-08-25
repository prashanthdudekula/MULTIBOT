# composer.py
# Async LLM composition pipeline using Gemini REST API.
# Handles routing by trigger kind, re-prompting on validation failures,
# and fallback JSON extraction.

import os
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

from dotenv import load_dotenv

from prompts import (
    build_universal_trigger_prompt,
    build_followup_prompt,
)
from validators import should_re_prompt, extract_json_from_response
from decision_engine import evaluate_signals

load_dotenv()
logger = logging.getLogger(__name__)

# ============================================================================
# Client setup — Direct REST API (no SDK dependency)
# ============================================================================

_api_key = os.environ.get("GEMINI_API_KEY")
if not _api_key:
    logger.warning("GEMINI_API_KEY not set — LLM calls will fail.")

import asyncio

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
TEMPERATURE = float(os.environ.get("COMPOSER_TEMPERATURE", "0.1"))
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

api_semaphore = asyncio.Semaphore(2)

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

        # Evaluate deterministic signals
        decision = evaluate_signals(
            merchant_context=merchant_context,
            trigger_context=trigger_context,
            category_context=category_context
        )

        # Route to the correct prompt builder
        prompt = _build_prompt(
            trigger_kind=trigger_kind,
            category_context=category_context,
            merchant_context=merchant_context,
            trigger_context=trigger_context,
            decision=decision,
            customer_context=customer_context,
            strict=use_strict,
        )

        if not prompt:
            logger.warning(f"Empty prompt for trigger_kind={trigger_kind}, skipping.")
            return None

        # Call Gemini
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
    if raw_text == "__RATE_LIMIT__":
        return "⚠️ Rate limit hit. Please wait 30 seconds before sending another message."
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
    decision: Any,
    customer_context: Optional[dict],
    strict: bool,
) -> str:
    """Route to the universal prompt builder."""
    return build_universal_trigger_prompt(
        category_context=category_context,
        merchant_context=merchant_context,
        trigger_context=trigger_context,
        decision=decision,
        customer_context=customer_context,
        strict=strict,
    )


async def _call_llm(prompt: str) -> Optional[str]:
    """Call Gemini via direct REST API and return the raw text response."""
    import asyncio
    from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=10))
    def _do_call():
        url = f"{GEMINI_API_URL}/{MODEL}:generateContent?key={_api_key}"
        body_dict = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": TEMPERATURE,
                "maxOutputTokens": 600
            }
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(body_dict).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            resp = urllib.request.urlopen(req, timeout=45)
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                logger.warning(f"Rate limited, retrying...")
                raise e
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except:
                pass
            logger.error(f"Gemini HTTP {e.code}: {error_body[:200]}")
            raise e
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "quota" in err_str:
                raise e
            logger.error(f"Unexpected LLM error: {e}")
            return None

    try:
        async with api_semaphore:
            result = await asyncio.to_thread(_do_call)
        return result
    except RetryError:
        logger.error("Rate limit exceeded after all retries.")
        return "__RATE_LIMIT__"
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
