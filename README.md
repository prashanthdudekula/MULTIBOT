# Vera Bot — MagicPin AI Challenge

## Overview

**Vera** is magicpin's merchant AI assistant. This bot receives structured context about merchants, categories, and trigger events, then uses Groq (Llama 3.3) to compose highly personalized WhatsApp-style messages that engage merchants in meaningful conversations.

---

## Architecture

```
Judge → /v1/context (push 4 context types)
      → /v1/tick    (bot decides what to send)
      → /v1/reply   (handle merchant reply)
```

### Files

| File | Purpose |
|------|---------|
| `bot.py` | FastAPI app with all 5 endpoints |
| `composer.py` | Async LLM composition pipeline |
| `validators.py` | Post-generation anti-pattern validation |
| `state.py` | In-memory context store + suppression |
| `prompts.py` | Prompt templates per trigger kind |

---

## Approach

### 1. Context-Aware Routing
Each trigger kind (`research_digest`, `recall_due`, `perf_spike`, generic) gets its own prompt builder. The prompt is assembled from all 4 context objects (category, merchant, trigger, customer) at call time.

### 2. Engagement Levers
Every prompt instructs the LLM to pick **exactly one** of 8 engagement levers:
- Specificity, Loss Aversion, Social Proof, Effort Externalization
- Curiosity, Reciprocity, Ask Merchant, Binary Commitment

### 3. Validation + Re-prompting
After the LLM responds, `validators.py` checks for:
- ✗ Generic offers (regex: `\d+% off`, `flat N`)
- ✗ Multiple CTAs
- ✗ CTA not in last sentence
- ✗ Long preambles
- ✗ Clinical taboos (for `dentists`, `doctors`)
- ✗ Verbatim repetition

If validation fails, the composer re-prompts in `strict` mode (max 2 retries).

### 4. Suppression
Sent `suppression_key` values are tracked in-memory with a 7-day TTL. Duplicate sends are silently skipped.

### 5. Conversation Management
All conversation turns are stored in-memory, keyed by `conversation_id`. This enables context-aware follow-up replies.

---

## Setup

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
copy .env.example .env
# Edit .env and add your GROQ_API_KEY

# 4. Run the bot
python -m uvicorn bot:app --host 0.0.0.0 --port 8080

# 5. Verify
curl http://localhost:8080/v1/healthz
curl http://localhost:8080/v1/metadata

# 6. Run tests
pytest tests/ -v
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | (required) | Your Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Llama model to use |
| `COMPOSER_MAX_TOKENS` | `600` | Max tokens per LLM call |
| `COMPOSER_TEMPERATURE` | `0.7` | LLM temperature |
| `TEAM_NAME` | `MULTIBOTS` | Shown in `/v1/metadata` |
| `TEAM_MEMBERS` | `Developer` | Comma-separated names |
| `CONTACT_EMAIL` | `team@multibots.dev` | Contact email |

---

## Scoring Targets

| Dimension | Max | Strategy |
|---|---|---|
| Category Fit | 20 | Per-trigger voice profiles + taboo enforcement |
| Merchant Fit | 20 | All 4 contexts injected into each prompt |
| Trigger Relevance | 20 | Trigger is the centrepiece; data cited directly |
| Engagement Compulsion | 20 | Exactly 1 lever + binary CTA in last sentence |
| Anti-Pattern Avoidance | 20 | Post-generation validator + re-prompting |

---

## Model

**Llama 3.3 70B Versatile** (Groq) — balances incredible speed, quality, and JSON enforcement. Configurable via `GROQ_MODEL` env var.
