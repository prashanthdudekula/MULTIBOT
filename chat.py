import requests
import json
import time
from datetime import datetime, timezone

BOT_URL = "http://localhost:8080"
MERCHANT_ID = "m_001"
TRIGGER_ID = f"tr_perf_{int(time.time())}"
CONV_ID = f"conv_{MERCHANT_ID}_{TRIGGER_ID}"

print("==================================================")
print("              VERA BOT CHAT INTERFACE             ")
print("==================================================")
print("Waking up Vera and sending an initial trigger...\n")

now_iso = datetime.now(timezone.utc).isoformat()
version = int(time.time())

# 1. Push category context
requests.post(f"{BOT_URL}/v1/context", json={
    "scope": "category",
    "context_id": "dentists",
    "version": version,
    "payload": {"slug": "dentists", "voice": {"tone": "professional"}},
    "delivered_at": now_iso
})

# 2. Push merchant context
requests.post(f"{BOT_URL}/v1/context", json={
    "scope": "merchant",
    "context_id": MERCHANT_ID,
    "version": version,
    "payload": {"category_slug": "dentists", "identity": {"name": "Dr. Smith"}, "language_pref": "en"},
    "delivered_at": now_iso
})

# 3. Push a trigger
requests.post(f"{BOT_URL}/v1/context", json={
    "scope": "trigger",
    "context_id": TRIGGER_ID,
    "version": version,
    "payload": {
        "kind": "perf_spike",
        "merchant_id": MERCHANT_ID,
        "payload": {"delta_pct": 45, "metric": "profile views", "reason": "weekend surge"}
    },
    "delivered_at": now_iso
})

# 4. Trigger a tick to get Vera's first message
response = requests.post(f"{BOT_URL}/v1/tick", json={
    "now": now_iso,
    "available_triggers": [TRIGGER_ID]
})

data = response.json()
print("DEBUG TICK DATA:", json.dumps(data, indent=2))
if data.get("actions") and len(data["actions"]) > 0:
    vera_msg = data["actions"][0]["body"]
    print(f"[Vera]: {vera_msg}\n")
else:
    print("[Vera is quiet...]\n")

# 5. Interactive loop
turn_number = 2
while True:
    try:
        user_input = input("[You]: ")
    except KeyboardInterrupt:
        break
        
    if user_input.lower() in ['quit', 'exit']:
        break

    reply_res = requests.post(f"{BOT_URL}/v1/reply", json={
        "conversation_id": CONV_ID,
        "merchant_id": MERCHANT_ID,
        "message": user_input,
        "turn_number": turn_number,
        "from_role": "merchant",
        "received_at": datetime.now(timezone.utc).isoformat()
    })
    
    turn_number += 1
    reply_data = reply_res.json()
    if reply_data.get("action") == "send":
        print(f"\n[Vera]: {reply_data.get('body')}\n")
    elif reply_data.get("action") == "end":
        print(f"\n[Vera ended the conversation.]\n")
        break
    else:
        print(f"\n[Vera did nothing.]\n")
