# Vera — AI Merchant Growth Assistant

A deterministic, context-aware AI decision engine built for the **magicpin Vera AI Challenge**.

Vera helps merchants decide **what action to take next**, then generates a concise, specific, and actionable message grounded entirely in the merchant's current context.

The system combines deterministic signal selection with **Gemini 3.5 Flash-Lite** for controlled natural-language generation.

---

## 1. What Vera Does

Vera receives structured context about:

* Merchant identity
* Business category
* Performance metrics
* Active offers
* Conversation history
* Current triggers
* Optional customer context

It then determines the **single strongest action opportunity** and produces:

```text
message
CTA
send_as
suppression_key
rationale
```

The goal is not to generate generic marketing copy.

The goal is to make the **best decision for the merchant at that moment**.

---

## 2. Core Decision Flow

```text
Category
    +
Merchant Context
    +
Trigger
    +
Optional Customer Context
            |
            v
     Signal Extraction
            |
            v
     Signal Prioritization
            |
            v
     Deterministic Decision
            |
            v
    Gemini 3.5 Flash-Lite
            |
            v
     Message Generation
            |
            v
       Validation
            |
            v
       Vera Response
```

The deterministic layer decides **what Vera should do**.

The LLM is used to express that decision naturally while remaining grounded in the supplied context.

---

## 3. Design Principles

### Context First

Every decision is based on the context actually received by Vera.

The system does not assume facts that were not provided.

### One Strong Signal

Vera does not repeat every available merchant metric.

It identifies the signal that matters most for the current trigger.

### Specificity

Messages use real information such as:

* Views
* CTR
* Bookings
* Search volume
* Active offers
* Offer prices
* Dates
* Local demand

when those values are available.

### No Fabricated Claims

Vera never invents:

* Offers
* Discounts
* Customer counts
* Search volume
* Prices
* Dates
* Performance metrics
* Availability

### One Clear CTA

Each outbound message has one low-friction next action.

### Category-Aware Communication

The decision and message style adapt to the merchant's category:

* Dentist
* Salon
* Restaurant
* Gym
* Pharmacy

---

## 4. Example

### Input

```json
{
  "category": "gym",
  "merchant": {
    "name": "FlexZone Gym",
    "performance": {
      "views": 150,
      "ctr": 0.9,
      "bookings": 3
    },
    "offers": []
  },
  "trigger": {
    "type": "dip",
    "signal": "declining_views"
  }
}
```

### Decision

```text
Primary signal:
Declining views

Supporting state:
No active offers

Recommended action:
Create or promote a relevant offer
```

### Generated response

```text
FlexZone's views are down to 150 and you have no active offer right now. Want me to promote a simple membership offer to bring more local interest?
```

The exact output depends on the context received at runtime.

---

# 5. Challenge Scoring Alignment

Vera is designed around the five challenge scoring dimensions.

| Dimension             | Strategy                                                     |
| --------------------- | ------------------------------------------------------------ |
| Decision Quality      | Rank signals and select the strongest actionable opportunity |
| Specificity           | Ground responses in real merchant metrics and offers         |
| Category Fit          | Apply category-specific language and actions                 |
| Merchant Fit          | Use merchant identity, performance and offer state           |
| Engagement Compulsion | One concrete reason + one low-friction CTA                   |

Each dimension is scored from **0–10**, for a maximum of **50 points**.

---

# 6. API

The bot exposes the required challenge endpoints.

### Health

```http
GET /v1/healthz
```

Used to verify that the bot is reachable.

### Metadata

```http
GET /v1/metadata
```

Returns bot capabilities and metadata.

### Context

```http
POST /v1/context
```

Receives and stores merchant/category/customer context.

Context updates are handled by version so that newer context can replace older state atomically.

### Tick

```http
POST /v1/tick
```

Processes new triggers and context changes and decides whether Vera should take an action.

### Reply

```http
POST /v1/reply
```

Handles merchant/customer replies and maintains conversation-aware behavior.

---

# 7. Project Structure

```text
MULTIBOT/
│
├── main.py
├── compose.py
├── decision_engine.py
├── signal_selector.py
├── context_store.py
├── llm.py
├── validators.py
├── models.py
│
├── dataset/
│   ├── categories/
│   ├── merchants_seed.json
│   ├── customers_seed.json
│   ├── triggers_seed.json
│   └── generate_dataset.py
│
├── examples/
│   ├── api-call-examples.md
│   └── case-studies.md
│
├── judge_simulator.py
├── requirements.txt
├── .env.example
└── README.md
```

---

# 8. Technology Stack

### Backend

* Python
* FastAPI
* Pydantic

### AI

* Gemini 3.5 Flash-Lite
* Google Gemini API

### Deployment

* Google Cloud Run

### Testing

* Official magicpin judge simulator
* Canonical test pairs
* API endpoint tests

---

# 9. Gemini Integration

The application uses the Gemini API for controlled reasoning and message generation.

Model:

```text
gemini-3.5-flash-lite
```

The API key is supplied through an environment variable.

```bash
GEMINI_API_KEY=your_api_key
```

The key must **never** be committed to source control.

---

# 10. Local Setup

Clone the repository:

```bash
git clone <YOUR_REPOSITORY_URL>
cd MULTIBOT
```

Create a virtual environment:

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set the Gemini API key.

### Windows PowerShell

```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
```

### Linux/macOS

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

Start the server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

# 11. Local Health Check

Open:

```text
http://localhost:8000/v1/healthz
```

Expected response:

```json
{
  "status": "ok"
}
```

Then verify metadata:

```text
http://localhost:8000/v1/metadata
```

---

# 12. Dataset

The challenge dataset contains:

* 5 business categories
* 50 merchants
* 200 customers
* 100 triggers
* 30 canonical test pairs

Generate the expanded dataset with:

```bash
python3 dataset/generate_dataset.py --seed-dir dataset --out expanded
```

The dataset generation is deterministic.

---

# 13. Judge Simulator

The official local judge simulator can be used to validate the bot before submission.

Configure:

```text
LLM_PROVIDER
LLM_API_KEY
BOT_URL
```

Then run:

```bash
python judge_simulator.py
```

The simulator validates:

```text
/v1/healthz
/v1/metadata
/v1/context
/v1/tick
/v1/reply
```

It also evaluates the bot against the canonical test pairs.

---

# 14. Determinism

For identical:

* input context
* trigger
* customer state
* model configuration
* simulator configuration

the system aims to produce deterministic decisions.

The deterministic decision layer reduces unnecessary variation and ensures that the LLM operates within a controlled decision boundary.

---

# 15. Grounding and Safety

Vera follows strict grounding rules.

The model may only use facts supplied by the challenge context.

Before returning a response, the system validates:

* Required output fields
* CTA presence
* Single CTA constraint
* Merchant facts
* Offer references
* Numeric values
* Unsupported claims
* Message length
* Suppression behavior

If generated content violates the constraints, the system falls back to a deterministic response rather than returning an ungrounded message.

---

# 16. Deployment

The bot is designed to run as a public HTTP service.

Recommended deployment:

**Google Cloud Run**

Example:

```bash
gcloud run deploy vera-bot \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated
```

The deployed service exposes:

```text
https://YOUR-CLOUD-RUN-URL/v1/healthz
https://YOUR-CLOUD-RUN-URL/v1/metadata
https://YOUR-CLOUD-RUN-URL/v1/context
https://YOUR-CLOUD-RUN-URL/v1/tick
https://YOUR-CLOUD-RUN-URL/v1/reply
```

The final Cloud Run base URL is submitted to the challenge judge.

---

# 17. Environment Variables

```text
GEMINI_API_KEY
```

Optional application configuration can be added through environment variables without committing secrets to the repository.

A `.env` file should never be committed.

Recommended `.gitignore` entries:

```text
.env
.venv/
__pycache__/
*.pyc
```

---

# 18. Performance Goals

The implementation is designed around the challenge constraints:

```text
Maximum response timeout: 30 seconds
Judge rate:               10 requests/second
Context limit:            500 KB
Actions per tick:         20
```

The system minimizes unnecessary LLM calls by performing deterministic signal selection before generation.

---

# 19. Why This Architecture

A pure LLM chatbot can produce fluent messages while still making poor business decisions.

Vera instead separates:

```text
Decision
   ↓
Action
   ↓
Message
```

This allows the system to optimize for the actual evaluation criteria rather than writing quality alone.

The deterministic layer provides:

* Predictability
* Grounding
* Signal prioritization
* Constraint enforcement
* Lower latency

Gemini provides:

* Natural language generation
* Contextual phrasing
* Category-aware communication
* Flexible response handling

Together they produce a merchant assistant that is both **decision-oriented and conversational**.

---

# 20. Submission

Before submission:

```text
[ ] All required endpoints return successfully
[ ] Context updates are handled correctly
[ ] Tick processing is stateful
[ ] Reply handling works
[ ] No API keys are committed
[ ] Gemini API is reachable
[ ] Judge simulator passes
[ ] Public Cloud Run URL is reachable
[ ] Bot remains live after submission
```

Submit the public Cloud Run base URL:

```text
https://YOUR-SERVICE-URL
```

The judge will call:

```text
GET  /v1/healthz
GET  /v1/metadata
POST /v1/context
POST /v1/tick
POST /v1/reply
```

---

## Built for the Vera Challenge

Vera is designed around one principle:

> **Choose the right action from the real merchant context, then make that action easy to say yes to.**

The system optimizes for **signal quality, specificity, category fit, merchant fit, and engagement** rather than generic AI-generated marketing copy.
