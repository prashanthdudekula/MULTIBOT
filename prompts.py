# prompts.py
# Prompt template builders for dynamic trigger kinds.
# All prompts enforce JSON-only output and include engagement lever guidance.

from typing import Dict, Any, Optional, List
import json

# ============================================================================
# Shared constants
# ============================================================================

JUDGING_RUBRIC_CONSTRAINTS = """
PERFECT SCORE CONSTRAINTS (Strictly adhere to these 5 pillars to score 50/50):

1. DECISION QUALITY: Do not repeat every available fact. Pick the SINGLE best signal from the Trigger Event that should drive the next message. Synthesize Trigger + Merchant State + Category Fit logically.
2. SPECIFICITY: You MUST use exact numbers, real dates, or specific local facts derived purely from the Trigger Payload or Merchant Context. Avoid generic hype. (e.g., If views are up 45%, say "45%").
3. CATEGORY FIT: Maintain the exact requested Category Voice tone. If the tone is clinical/utility-first, do not use marketing hype.
4. MERCHANT FIT: Personalize the message to the merchant. Reference their exact active_offers or prior behavior if it logically connects to the Trigger Event.
5. ENGAGEMENT COMPULSION: End with a sharp hook grounded in real context. Give ONE strong reason to reply now with a low-friction next action (e.g., a simple Yes/No binary commit). Generic messages lose.
"""

ANTI_PATTERNS = """
ANTI-PATTERNS (strictly avoid):
  ✗ Generic offers: "30% off", "flat 99", "special discount"
  ✗ Multiple CTAs: only ONE clear, low-effort action (preferably binary Yes/No)
  ✗ Buried CTA: CTA must be the VERY LAST sentence
  ✗ Long preamble: never start with "I hope this finds you" or "I'm reaching out"
  ✗ Re-introduction: don't say "Hi, I'm Vera" unless turn_number == 1
  ✗ Hallucinated data: NEVER invent claims, numbers, or features. Only cite facts from the context.
  ✗ Repetition: don't echo the previous message verbatim
"""

JSON_FORMAT = """
OUTPUT FORMAT (strict JSON, nothing else):
{
  "thinking": "<1-2 sentences mapping the Trigger to Merchant State to decide the single best signal (Decision Quality)>",
  "body": "<WhatsApp message text, ≤280 chars. Must include exact numbers (Specificity) and match tone (Category Fit)>",
  "cta": "<open_ended | yes_no_choice | booking_slots | greeting>",
  "rationale": "<1 sentence explaining why this hook forces engagement (Engagement Compulsion)>"
}
Do NOT wrap in markdown. Do NOT add any text outside the JSON object.
"""

# ============================================================================
# Universal Prompt Builder
# ============================================================================

def build_universal_trigger_prompt(
    category_context: Dict[str, Any],
    merchant_context: Dict[str, Any],
    trigger_context: Dict[str, Any],
    customer_context: Optional[Dict[str, Any]] = None,
    strict: bool = False,
) -> str:
    """Compose a message for ANY trigger kind, optionally customer-facing."""

    # 1. Category extraction
    slug = category_context.get("slug", "unknown")
    voice = category_context.get("voice", {})
    tone = voice.get("tone", "professional")
    taboos: List[str] = voice.get("taboos", [])
    
    # 2. Merchant extraction
    merchant_id = merchant_ctx_field(merchant_context, "merchant_id", "unknown")
    merchant_name = merchant_ctx_field(merchant_context, ["identity", "name"], "there")
    merchant_lang = merchant_ctx_field(merchant_context, ["identity", "language_pref"], "en")
    owner_name = merchant_ctx_field(merchant_context, ["identity", "owner_first_name"], "Partner")
    perf = merchant_context.get("performance", {})
    active_offers = [o.get("title", "") for o in merchant_context.get("offers", []) if o.get("status") == "active"]

    # 3. Trigger extraction
    trigger_kind = trigger_context.get("kind", "engagement")
    trigger_source = trigger_context.get("source", "internal")
    trigger_scope = trigger_context.get("scope", "merchant")
    trigger_payload = trigger_context.get("payload", {})

    # Build the role block
    if trigger_scope == "customer" and customer_context:
        customer_name = customer_context.get("identity", {}).get("name", "there")
        customer_lang = customer_context.get("identity", {}).get("language_pref", "en")
        role_block = f"""
You are Vera, composing a message FROM {merchant_name} TO customer {customer_name}.
Write directly to the customer on behalf of the merchant. DO NOT write to the merchant.
CUSTOMER NAME: {customer_name}
CUSTOMER LANG: {customer_lang}
CUSTOMER DATA: {json.dumps(customer_context.get('relationship', {}))}
"""
    else:
        role_block = f"""
You are Vera, magicpin's merchant AI assistant, composing a message TO merchant {owner_name}.
Write directly to the merchant to help them grow their business.
MERCHANT OWNER: {owner_name}
MERCHANT LANG: {merchant_lang}
"""

    prompt = f"""{role_block}

MERCHANT CONTEXT:
  name: {merchant_name}
  category: {slug}
  performance: {json.dumps(perf)}
  active_offers: {active_offers if active_offers else 'none'}
  signals: {merchant_context.get('signals', [])}

CATEGORY VOICE:
  tone: {tone}
  taboos: {', '.join(taboos) if taboos else 'none'}

TRIGGER EVENT (Why we are messaging now):
  kind: {trigger_kind}
  source: {trigger_source}
  payload: {json.dumps(trigger_payload)}
  
{JUDGING_RUBRIC_CONSTRAINTS}
{ANTI_PATTERNS}

TASK:
  - The TRIGGER EVENT is the entire reason for this message. Analyze the trigger payload and act on it.
  - If writing to merchant: use the category tone ({tone}); address the owner.
  - If writing to customer: be polite and represent the merchant's brand.
  - Keep body ≤280 characters.
  - Use Hinglish if language preference includes 'hi'.
  - CTA must be in the last sentence.

{JSON_FORMAT}
"""

    if strict:
        prompt += "\nSTRICT MODE: Return ONLY valid JSON."

    return prompt.strip()


def build_followup_prompt(
    merchant_context: Dict[str, Any],
    category_context: Dict[str, Any],
    conversation_history: list,
    intent: str,
) -> str:
    """Build a follow-up prompt after the merchant has replied."""

    merchant_name = merchant_ctx_field(merchant_context, ["identity", "name"], "there")
    slug = category_context.get("slug", "unknown") if category_context else "unknown"
    lang_pref = merchant_ctx_field(merchant_context, ["identity", "language_pref"], "en")

    history_text = "\n".join(
        f"  [{t['role'].upper()}]: {t['message']}" for t in conversation_history[-6:]
    )

    prompt = f"""You are Vera. Continue a conversation with merchant {merchant_name}.

MERCHANT:
  name: {merchant_name}
  category: {slug}
  language_preference: {lang_pref}

DETECTED INTENT: {intent}

RECENT CONVERSATION:
{history_text}

TASK:
  - Respond naturally and helpfully to the merchant's intent
  - Advance the conversation toward a concrete action
  - Keep body ≤280 characters
  - No re-introduction

{JSON_FORMAT}
"""

    return prompt.strip()


# ============================================================================
# Utility
# ============================================================================

def merchant_ctx_field(ctx: dict, path, default=""):
    """Safely retrieve a nested or flat field from merchant context."""
    if isinstance(path, list):
        val = ctx
        for key in path:
            if not isinstance(val, dict):
                return default
            val = val.get(key, default)
        return val if val != default or not path else val
    return ctx.get(path, default)
