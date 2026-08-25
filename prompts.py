# prompts.py
# Prompt template builders for dynamic trigger kinds.
# All prompts enforce JSON-only output and include engagement lever guidance.

from typing import Dict, Any, Optional, List
import json

# ============================================================================
# Shared constants
# ============================================================================


ANTI_PATTERNS = """
ANTI-PATTERNS (strictly avoid — each violation costs points):
  ✗ Generic offers: "30% off", "flat 99", "special discount" — only mention offers that exist in merchant context
  ✗ Multiple CTAs: you must end the message with EXACTLY ONE simple yes/no question. Do NOT include multiple asks.
  ✗ Buried CTA: CTA must be the VERY LAST sentence
  ✗ Long preamble: never start with "I hope this finds you" or "I'm reaching out"
  ✗ Re-introduction: don't say "Hi, I'm Vera" unless turn_number == 1
  ✗ Hallucinated data: NEVER invent claims, numbers, or features. Only cite facts from the provided context.
  ✗ Repetition: don't echo the previous message verbatim
  ✗ Marketing buzzwords in clinical categories: no "amazing", "incredible", "game-changer" for dentists/pharmacies
  ✗ Vague statements: no "many customers", "significant growth", "great results" — use exact numbers
"""

JSON_FORMAT = """
OUTPUT FORMAT (strict JSON, nothing else):
{
  "thinking": "<1-2 sentences: which SINGLE signal did you pick and WHY it connects to this merchant's situation right now>",
  "body": "<WhatsApp message text, ≤280 chars. MUST include exact numbers from PRIMARY SIGNAL. MUST match the Category Voice tone. MUST end with exactly ONE yes/no question from OBJECTIVE.>",
  "cta": "<open_ended | yes_no_choice | booking_slots | greeting>",
  "rationale": "<1 sentence explaining the psychological lever used: loss_aversion / curiosity_gap / social_proof / urgency / peer_comparison>"
}
Do NOT wrap in markdown. Do NOT add any text outside the JSON object.
"""

# ============================================================================
# Category Voice Guides (injected into prompts for Category Fit)
# ============================================================================

CATEGORY_VOICE_GUIDES = {
    "dentists": """CATEGORY VOICE — DENTISTS (peer_clinical):
  - Write as a PEER professional, NOT a salesperson. Use "Dr." prefix.
  - Tone: clinical, respectful, collegial. Like one dentist texting another.
  - OK to use: fluoride varnish, scaling, caries, OPG, RCT, implant, aligner
  - NEVER use: "guaranteed", "100% safe", "miracle", "best in city", marketing hype
  - Style examples: "Worth a look — JIDA Oct 2026 p.14", "This likely affects your high-risk adult cohort"
  - Register: respectful_collegial — share data, cite sources, be concise""",
  
    "salons": """CATEGORY VOICE — SALONS (warm_practical):
  - Write as an approachable expert friend, warm but business-savvy.
  - Tone: friendly, practical, encouraging. Like a senior stylist giving a tip.
  - OK to use: balayage, keratin, smoothening, hair spa, olaplex, booking
  - NEVER use: "guaranteed glow", "permanent results", "instant transformation", "miracle"
  - Style examples: "Bridal season is starting — bookings usually 2x normal", "Your Saturday 5-7pm slot has been strongest this month"
  - Register: approachable_expert — practical business tips with warmth""",
  
    "restaurants": """CATEGORY VOICE — RESTAURANTS (warm_busy_practical):
  - Write as a fellow restaurant operator who gets the hustle.
  - Tone: warm, busy, practical. Operator-to-operator. Brief, no fluff.
  - OK to use: footfall, covers, AOV, table turnover, thali, biryani, reservations
  - NEVER use: "best food in city", "guaranteed packed house", "miracle marketing"
  - Style examples: "Quick one — IPL match nights have been 1.5x your weekday avg", "biryani delivery searches in your area up 28%"
  - Register: fellow_operator — respect their time, get to the point""",
  
    "gyms": """CATEGORY VOICE — GYMS (energetic_disciplined):
  - Write as a coach/mentor, energetic but data-driven.
  - Tone: motivational, disciplined, direct. Like a head coach giving a pep talk with numbers.
  - OK to use: footfall, membership churn, PT sessions, HIIT, functional, split, retention
  - NEVER use: "guaranteed weight loss", "shred in 7 days", "miracle transformation"
  - Style examples: "Your weekday 7-9pm slot has been at 90%+ capacity all month", "April drop-off is normal; bookings recover by 2nd week May"
  - Register: coach_to_member — direct, encouraging, data-backed""",
  
    "pharmacies": """CATEGORY VOICE — PHARMACIES (trustworthy_precise):
  - Write as a trusted neighbourhood pharmacist advisor.
  - Tone: trustworthy, precise, no-nonsense. Facts and figures, not hype.
  - OK to use: OTC, schedule H, generic, branded, molecule, MRP, expiry, batch
  - NEVER use: "miracle cure", "guaranteed result", "100% safe", "best price" without data
  - Style examples: "Your repeat-prescription customer count is up 18% this month", "Generic alternative for metformin just got approved — 30% lower MRP"
  - Register: neighbourhood_pharmacist — factual, concise, health-first"""
}

# ============================================================================
# Universal Prompt Builder
# ============================================================================

def build_universal_trigger_prompt(
    category_context: Dict[str, Any],
    merchant_context: Dict[str, Any],
    trigger_context: Dict[str, Any],
    decision: Any,
    customer_context: Optional[Dict[str, Any]] = None,
    strict: bool = False,
) -> str:
    """Compose a message for ANY trigger kind, optionally customer-facing."""

    # 1. Category extraction
    slug = category_context.get("slug", "unknown")
    voice = category_context.get("voice", {})
    tone = voice.get("tone", "professional")
    register = voice.get("register", "professional")
    taboos: List[str] = voice.get("vocab_taboo", [])
    tone_examples = voice.get("tone_examples", [])
    
    # Get category-specific voice guide
    voice_guide = CATEGORY_VOICE_GUIDES.get(slug, f"Tone: {tone}. Register: {register}.")
    
    # 2. Merchant extraction
    merchant_id = merchant_ctx_field(merchant_context, "merchant_id", "unknown")
    merchant_name = merchant_ctx_field(merchant_context, ["identity", "name"], "there")
    merchant_lang = merchant_ctx_field(merchant_context, ["identity", "language_pref"], "en")
    owner_name = merchant_ctx_field(merchant_context, ["identity", "owner_first_name"], "Partner")
    locality = merchant_ctx_field(merchant_context, ["identity", "locality"], "your area")
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
You are composing a message FROM {merchant_name} TO customer {customer_name}.
Write directly to the customer on behalf of the merchant. DO NOT write to the merchant.
CUSTOMER NAME: {customer_name}
CUSTOMER LANG: {customer_lang}
CUSTOMER DATA: {json.dumps(customer_context.get('relationship', {}))}
"""
    else:
        role_block = f"""
You are Vera, magicpin's merchant AI assistant, composing a WhatsApp message TO merchant owner {owner_name}.
Write directly to the merchant to help them grow their business.
MERCHANT OWNER: {owner_name}
MERCHANT LANG: {merchant_lang}
"""

    # Build urgency block
    urgency_block = ""
    if hasattr(decision, 'urgency_hook') and decision.urgency_hook:
        urgency_block = f"""
URGENCY HOOK (weave this into your message to create engagement compulsion):
  {decision.urgency_hook}
"""

    prompt = f"""{role_block}

MERCHANT CONTEXT:
  name: {merchant_name}
  owner: {owner_name}
  locality: {locality}
  category: {slug}
  active_offers: {', '.join(active_offers) if active_offers else 'none'}
  performance: views={perf.get('views', '?')}, calls={perf.get('calls', '?')}, ctr={perf.get('ctr', '?')}

{voice_guide}

DETERMINISTIC DECISION (You MUST follow this exactly — do NOT deviate):
  PRIMARY SIGNAL: {decision.primary_signal}
  SUPPORTING FACT: {decision.supporting_fact}
  OBJECTIVE: {decision.recommended_action}
{urgency_block}
SCORING RULES (each dimension is scored 0-10, aim for 10/10 on all):

1. DECISION QUALITY (10/10): Your message must clearly connect the PRIMARY SIGNAL to WHY it matters for THIS merchant RIGHT NOW. Show cause-and-effect reasoning, not just stating facts.

2. SPECIFICITY (10/10): You MUST use the exact numbers from PRIMARY SIGNAL and SUPPORTING FACT. Every claim must be verifiable. No rounding, no generalizing. If views are 120, say "120".

3. CATEGORY FIT (10/10): Follow the Category Voice guide EXACTLY. Match the tone, register, and allowed vocabulary. NEVER use taboo words.

4. MERCHANT FIT (10/10): Use their exact name ({merchant_name}), owner name ({owner_name}), and locality ({locality}). Reference their actual active offers if relevant.

5. ENGAGEMENT COMPULSION (10/10): End with EXACTLY ONE low-friction yes/no question from the OBJECTIVE. Weave in urgency/loss-aversion from the URGENCY HOOK.

{ANTI_PATTERNS}

TASK:
  - Follow the OBJECTIVE in DETERMINISTIC DECISION exactly.
  - Base your message ONLY on PRIMARY SIGNAL and SUPPORTING FACT. Do NOT invent other facts.
  - Match the Category Voice tone ({tone}) and register ({register}).
  - Keep body ≤280 characters.
  - Use Hinglish if language preference includes 'hi'.
  - CTA must be in the LAST sentence and must be a simple yes/no question.

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
    voice = category_context.get("voice", {}) if category_context else {}
    tone = voice.get("tone", "professional")

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
  - Match the category tone ({tone})
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
