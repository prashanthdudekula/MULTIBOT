# bot.py
# FastAPI application — the 5 required endpoints for the MagicPin AI Challenge.
# Run: python -m uvicorn bot:app --host 0.0.0.0 --port 8080

import logging
import os
from datetime import datetime, timezone
from typing import Any, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from state import store
from seed_data import load_seed_data, MERCHANTS, TRIGGERS
from composer import compose_message, compose_followup

UTC = timezone.utc

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vera — magicpin Merchant AI Bot",
    description="MagicPin AI Challenge entry: LLM-powered merchant engagement bot.",
    version="1.0.0",
)

# Load seed data on startup
_seed_result = load_seed_data(store)
logger.info(f"Seed data loaded: {_seed_result}")

# ============================================================================
# Pydantic models
# ============================================================================


class ContextPushRequest(BaseModel):
    scope: str
    context_id: str
    version: int
    payload: dict
    delivered_at: str


class TickRequest(BaseModel):
    now: str
    available_triggers: List[str] = []


class ReplyRequest(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    from_role: str  # "merchant" or "customer"
    message: str
    received_at: str
    turn_number: int


class MessageAction(BaseModel):
    conversation_id: str
    merchant_id: Optional[str]
    customer_id: Optional[str]
    send_as: str  # "vera" or "merchant_on_behalf"
    trigger_id: Optional[str]
    template_name: str
    template_params: List[str]
    body: str
    cta: str
    suppression_key: Optional[str]
    rationale: str


class TickResponse(BaseModel):
    actions: List[MessageAction] = []


class ReplyAction(BaseModel):
    action: str  # "send" | "wait" | "end"
    body: Optional[str] = None
    wait_seconds: Optional[int] = None
    cta: Optional[str] = None
    rationale: str


# ============================================================================
# 1. GET /v1/healthz
# ============================================================================


@app.get("/v1/healthz")
async def healthz():
    """Liveness probe — returns uptime and context load counts."""
    return {
        "status": "ok",
        "uptime_seconds": store.uptime_seconds(),
        "contexts_loaded": store.stats(),
    }


# ============================================================================
# 2. GET /v1/metadata
# ============================================================================


@app.get("/v1/metadata")
async def metadata():
    """Bot identity — update team info here or via .env."""
    return {
        "team_name": "MULTIBOTS",
        "team_members": ["Developer"],
        "model": "llama-3.3-70b-versatile",
        "approach": "Context-aware LLM composition with strict 50-point rubric prompt optimization. Uses Groq Llama-3.3 with structured JSON output enforcement and an internal thinking step.",
        "contact_email": "team@multibots.dev",
        "version": "1.0.0",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# 2b. GET /v1/merchants — list all seeded merchants for frontend selector
# ============================================================================


@app.get("/v1/merchants")
async def list_merchants():
    """Return all merchant contexts for the frontend selector."""
    merchants = store.get_all_contexts_by_scope("merchant")
    result = []
    for m in merchants:
        mid = m.get("merchant_id", "unknown")
        identity = m.get("identity", {})
        merchant_triggers = [
            t["payload"] for t in TRIGGERS
            if t["payload"].get("merchant_id") == mid
        ]
        result.append({
            "merchant_id": mid,
            "name": identity.get("name", mid),
            "owner": identity.get("owner_first_name", ""),
            "category": m.get("category_slug", ""),
            "language": identity.get("language_pref", "en"),
            "performance": m.get("performance", {}),
            "offers": [o.get("title") for o in m.get("offers", []) if o.get("status") == "active"],
            "signals": m.get("signals", []),
            "triggers": [{"id": t.get("kind", ""), "kind": t.get("kind", "")} for t in merchant_triggers],
        })
    return {"merchants": result}


# ============================================================================
# 3. POST /v1/context
# ============================================================================


@app.post("/v1/context")
async def push_context(body: ContextPushRequest):
    """
    Receive and store a context payload. Idempotent by (scope, context_id, version).
    Returns 200 with accepted=False on stale version (not a 4xx).
    """
    try:
        store.store_context(body.scope, body.context_id, body.version, body.payload)
        logger.info(f"Stored context: scope={body.scope} id={body.context_id} v={body.version}")
        return {
            "accepted": True,
            "ack_id": f"ack_{body.context_id}_v{body.version}",
            "stored_at": datetime.now(UTC).isoformat(),
        }
    except ValueError as e:
        key = (body.scope, body.context_id)
        current_version = store.contexts.get(key, {}).get("version", 0)
        logger.warning(f"Stale context rejected: {e}")
        return {
            "accepted": False,
            "reason": "stale_version",
            "current_version": current_version,
        }


# ============================================================================
# 4. POST /v1/tick
# ============================================================================


@app.post("/v1/tick", response_model=TickResponse)
async def tick(body: TickRequest):
    """
    Periodic wake-up. For each merchant × trigger combination that is not
    suppressed, compose a MessageAction via the LLM pipeline.
    Returns at most ONE action per merchant per tick to avoid spam.
    """

    actions: List[MessageAction] = []
    merchants = store.get_all_contexts_by_scope("merchant")

    logger.info(
        f"Tick at {body.now}: {len(merchants)} merchants, "
        f"{len(body.available_triggers)} triggers"
    )

    for merchant_ctx in merchants:
        merchant_id = merchant_ctx.get("merchant_id", "unknown")
        category_slug = (
            merchant_ctx.get("category_slug")
            or merchant_ctx.get("identity", {}).get("category")
            or ""
        )

        category_ctx = store.get_context("category", category_slug)
        if not category_ctx:
            logger.debug(f"No category context for slug={category_slug}, skipping merchant {merchant_id}")
            continue

        # ONE action per merchant per tick
        for trigger_id in body.available_triggers:
            trigger_ctx = store.get_context("trigger", trigger_id)
            if not trigger_ctx:
                continue

            # Ensure trigger belongs to this merchant (when merchant_id is set)
            trigger_merchant = trigger_ctx.get("merchant_id")
            if trigger_merchant and trigger_merchant != merchant_id:
                continue

            # Suppression check
            suppression_key = trigger_ctx.get("suppression_key")
            if store.is_suppressed(suppression_key):
                logger.debug(f"Suppressed: key={suppression_key}")
                continue

            customer_id = trigger_ctx.get("customer_id")
            customer_ctx = store.get_context("customer", customer_id) if customer_id else None

            # Conversation already running for this pair?
            conv_id = f"conv_{merchant_id}_{trigger_id}"
            if customer_id:
                conv_id = f"conv_{customer_id}_{trigger_id}"

            existing = store.get_conversation(conv_id)
            if existing:
                logger.debug(f"Conversation {conv_id} already active, skipping")
                continue

            try:
                result = await compose_message(
                    category_context=category_ctx,
                    merchant_context=merchant_ctx,
                    trigger_context=trigger_ctx,
                    customer_context=customer_ctx,
                )

                if not result or not result.get("body"):
                    logger.warning(f"Empty composition for {merchant_id}/{trigger_id}")
                    continue

                send_as = "merchant_on_behalf" if trigger_ctx.get("scope") == "customer" else "vera"

                action = MessageAction(
                    conversation_id=conv_id,
                    merchant_id=merchant_id,
                    customer_id=customer_id,
                    send_as=send_as,
                    trigger_id=trigger_id,
                    template_name=f"vera_{trigger_ctx.get('kind', 'generic')}_v1",
                    template_params=[
                        merchant_ctx.get("identity", {}).get("name", merchant_id),
                        trigger_ctx.get("kind", "engagement"),
                    ],
                    body=result["body"],
                    cta=result.get("cta", "open_ended"),
                    suppression_key=suppression_key,
                    rationale=result.get("rationale", "Composed from 4 contexts"),
                )

                actions.append(action)
                store.create_conversation(conv_id)
                store.add_turn(conv_id, "vera", result["body"])

                # Mark suppressed so we don't re-send within TTL
                store.mark_suppressed(suppression_key)

                logger.info(f"Action queued: {conv_id} cta={action.cta}")

                # One action per merchant per tick — move to next merchant
                break

            except Exception as e:
                logger.error(f"Composition error for {merchant_id}/{trigger_id}: {e}", exc_info=True)
                continue

    logger.info(f"Tick complete: {len(actions)} actions")
    return TickResponse(actions=actions)


# ============================================================================
# 5. POST /v1/reply
# ============================================================================


@app.post("/v1/reply", response_model=ReplyAction)
async def reply(body: ReplyRequest):
    """
    Handle an inbound merchant or customer reply.
    Detects intent and composes the appropriate next action.
    """

    # Record incoming turn
    store.add_turn(body.conversation_id, body.from_role, body.message)
    history = store.get_conversation(body.conversation_id)

    logger.info(
        f"Reply received: conv={body.conversation_id} from={body.from_role} "
        f"turn={body.turn_number}"
    )

    # Detect intent
    intent = _detect_intent(body.message, history)
    logger.info(f"Detected intent: {intent}")

    # ---- Auto-reply (canned OOO / same repeated message) ----
    if intent == "auto_reply":
        return ReplyAction(
            action="end",
            rationale="Detected auto-reply / repeated canned response; gracefully exiting",
        )

    # ---- Rejected ----
    if intent == "rejected":
        return ReplyAction(
            action="end",
            rationale="Merchant declined; gracefully exiting conversation",
        )

    # ---- Wants time ----
    if intent == "ask_for_time":
        return ReplyAction(
            action="wait",
            wait_seconds=3600,
            rationale="Merchant asked for more time; backing off 1 hour",
        )

    # ---- Accepted or still engaging ----
    merchant_ctx = store.get_context("merchant", body.merchant_id) if body.merchant_id else {}
    category_slug = ""
    category_ctx = None

    if merchant_ctx:
        category_slug = (
            merchant_ctx.get("category_slug")
            or merchant_ctx.get("identity", {}).get("category")
            or ""
        )
        category_ctx = store.get_context("category", category_slug)

    try:
        reply_body = await compose_followup(
            merchant_context=merchant_ctx or {},
            category_context=category_ctx or {},
            conversation_history=history,
            intent=intent,
        )
    except Exception as e:
        logger.error(f"Follow-up composition error: {e}", exc_info=True)
        reply_body = "Thanks for your reply! Let me get back to you shortly."

    # Record Vera's response
    store.add_turn(body.conversation_id, "vera", reply_body)

    return ReplyAction(
        action="send",
        body=reply_body,
        cta="open_ended" if intent == "engaging" else "yes_no_choice",
        rationale=f"Intent={intent}; composed follow-up via LLM",
    )


# ============================================================================
# Intent detection
# ============================================================================


def _detect_intent(message: str, history: List[dict]) -> str:
    """
    Classify the intent of an inbound message.
    Returns one of: 'accepted', 'rejected', 'ask_for_time', 'auto_reply', 'engaging'
    """
    lower = message.lower().strip()

    # Auto-reply: same message repeated 3+ times in last 3 turns
    if len(history) >= 3:
        recent = [t["message"] for t in history[-3:]]
        if len(set(recent)) == 1:
            return "auto_reply"

    # Auto-reply keywords
    auto_reply_phrases = [
        "out of office", "i am away", "i'm away", "will respond when i return",
        "auto reply", "automatic reply",
    ]
    if any(p in lower for p in auto_reply_phrases):
        return "auto_reply"

    # Acceptance
    accept_phrases = [
        "yes", "ok", "okay", "sure", "go ahead", "let's do it", "send it",
        "do it", "go for it", "sounds good", "agreed", "confirm", "proceed",
        "haan", "bilkul", "theek hai", "karo", "chalega", "ho jaye",
    ]
    if any(lower == p or lower.startswith(p + " ") or lower.startswith(p + ",") for p in accept_phrases):
        return "accepted"
    if any(p in lower for p in ["yes please", "yes, go", "yes go", "yes do"]):
        return "accepted"

    # Rejection
    reject_phrases = [
        "no", "stop", "not interested", "no thanks", "no thank you",
        "don't want", "do not want", "please stop", "unsubscribe",
        "nahi", "nahi chahiye", "interested nahi", "kaam nahi",
    ]
    if any(p in lower for p in reject_phrases):
        return "rejected"

    # Wants time
    time_phrases = [
        "later", "tomorrow", "next week", "in a bit", "some time",
        "let me think", "i'll think", "will get back", "get back to you",
        "baad mein", "kal", "week baad", "sochta hoon",
    ]
    if any(p in lower for p in time_phrases):
        return "ask_for_time"

    return "engaging"


# ============================================================================
# Entry point
# ============================================================================


if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
