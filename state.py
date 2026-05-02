# state.py
# Centralized in-memory state: context store, suppression tracker, conversation manager
# Replace with Redis/SQLite for production-grade persistence.

from datetime import datetime, timedelta, timezone

UTC = timezone.utc
from typing import Optional, List, Dict, Any

SUPPRESSION_TTL_DAYS = 7  # How long to suppress a key after it's been used


class ContextStore:
    """
    In-memory store for all context scopes:
      - 'category'  : category-level config + digest
      - 'merchant'  : per-merchant identity, performance, offers
      - 'customer'  : per-customer identity + history
      - 'trigger'   : event payloads that drive outbound messages
    """

    def __init__(self):
        # (scope, context_id) -> {'version': int, 'payload': dict, 'stored_at': str}
        self.contexts: Dict[tuple, dict] = {}

        # conversation_id -> list of turn dicts
        self.conversations: Dict[str, List[dict]] = {}

        # suppression_key -> datetime when it was used
        self.suppression_log: Dict[str, datetime] = {}

        self.start_time = datetime.now(UTC)

    # ------------------------------------------------------------------
    # Context management
    # ------------------------------------------------------------------

    def store_context(self, scope: str, context_id: str, version: int, payload: dict):
        """
        Idempotent upsert keyed by (scope, context_id).
        Raises ValueError if the incoming version is <= the stored version.
        """
        key = (scope, context_id)
        current = self.contexts.get(key)

        if current and current["version"] >= version:
            raise ValueError(
                f"Stale version: stored={current['version']}, incoming={version}"
            )

        self.contexts[key] = {
            "version": version,
            "payload": payload,
            "stored_at": datetime.now(UTC).isoformat(),
        }

    def get_context(self, scope: str, context_id: str) -> Optional[dict]:
        """Return the payload for the latest stored version, or None."""
        key = (scope, context_id)
        entry = self.contexts.get(key)
        return entry["payload"] if entry else None

    def get_all_contexts_by_scope(self, scope: str) -> List[dict]:
        """Return all payloads for a given scope."""
        return [
            entry["payload"]
            for (s, _), entry in self.contexts.items()
            if s == scope
        ]

    # ------------------------------------------------------------------
    # Conversation management
    # ------------------------------------------------------------------

    def create_conversation(self, conversation_id: str):
        """Initialize an empty conversation thread (idempotent)."""
        self.conversations.setdefault(conversation_id, [])

    def add_turn(self, conversation_id: str, role: str, message: str):
        """Append a turn to the conversation history."""
        self.conversations.setdefault(conversation_id, []).append(
            {
                "role": role,
                "message": message,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

    def get_conversation(self, conversation_id: str) -> List[dict]:
        """Return full conversation history for a given ID."""
        return self.conversations.get(conversation_id, [])

    def get_last_bot_message(self, conversation_id: str) -> Optional[str]:
        """Return the last message sent by Vera (to detect repetition)."""
        history = self.conversations.get(conversation_id, [])
        for turn in reversed(history):
            if turn["role"] == "vera":
                return turn["message"]
        return None

    # ------------------------------------------------------------------
    # Suppression
    # ------------------------------------------------------------------

    def mark_suppressed(self, suppression_key: str):
        """Record that a suppression key has been used."""
        if suppression_key:
            self.suppression_log[suppression_key] = datetime.now(UTC)

    def is_suppressed(self, suppression_key: Optional[str]) -> bool:
        """
        Return True if the suppression key was used within SUPPRESSION_TTL_DAYS.
        Falsy keys are never suppressed.
        """
        if not suppression_key:
            return False
        used_at = self.suppression_log.get(suppression_key)
        if not used_at:
            return False
        return (datetime.now(UTC) - used_at) < timedelta(days=SUPPRESSION_TTL_DAYS)

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def uptime_seconds(self) -> int:
        return int((datetime.now(UTC) - self.start_time).total_seconds())

    def stats(self) -> dict:
        """Count stored contexts by scope."""
        counts: Dict[str, int] = {}
        for (scope, _) in self.contexts:
            counts[scope] = counts.get(scope, 0) + 1
        return counts


# Singleton instance — import this everywhere
store = ContextStore()
