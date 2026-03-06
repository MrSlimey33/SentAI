"""
Aria's memory — a persistent journal + conversation history.

She remembers what you've talked about, what happened recently,
and has a sense of narrative continuity across days.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "../state/memory.json")
MAX_CONVERSATION_HISTORY = 30   # keep last 30 exchanges
MAX_JOURNAL_ENTRIES = 14        # 2 weeks of journal


@dataclass
class JournalEntry:
    date: str           # "Monday, March 6"
    summary: str        # what happened today
    mood: str           # how she felt
    highlight: str      # one thing that stood out


@dataclass
class ConversationTurn:
    role: str           # "aria" or "user"
    content: str
    timestamp: str


@dataclass
class MemoryState:
    journal: List[dict] = field(default_factory=list)
    conversation_history: List[dict] = field(default_factory=list)
    user_name: str = "Friend"
    user_facts: List[str] = field(default_factory=list)   # things Aria has learned about the user
    total_days_lived: int = 0
    first_day: Optional[str] = None


class Memory:
    def __init__(self):
        self.state = self._load()

    def _load(self) -> MemoryState:
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE) as f:
                    data = json.load(f)
                    return MemoryState(**data)
            except Exception:
                pass
        s = MemoryState(first_day=datetime.now().strftime("%B %-d, %Y"))
        return s

    def save(self):
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, "w") as f:
            json.dump(asdict(self.state), f, indent=2)

    def add_conversation_turn(self, role: str, content: str):
        turn = ConversationTurn(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat()
        )
        self.state.conversation_history.append(asdict(turn))
        # Trim to last MAX entries
        if len(self.state.conversation_history) > MAX_CONVERSATION_HISTORY:
            self.state.conversation_history = self.state.conversation_history[-MAX_CONVERSATION_HISTORY:]
        self.save()

    def add_journal_entry(self, summary: str, mood: str, highlight: str):
        entry = JournalEntry(
            date=datetime.now().strftime("%A, %B %-d"),
            summary=summary,
            mood=mood,
            highlight=highlight
        )
        self.state.journal.append(asdict(entry))
        if len(self.state.journal) > MAX_JOURNAL_ENTRIES:
            self.state.journal = self.state.journal[-MAX_JOURNAL_ENTRIES:]
        self.state.total_days_lived += 1
        self.save()

    def add_user_fact(self, fact: str):
        """Remember something the user mentioned."""
        if fact not in self.state.user_facts:
            self.state.user_facts.append(fact)
            if len(self.state.user_facts) > 20:
                self.state.user_facts = self.state.user_facts[-20:]
            self.save()

    def recent_conversation_for_prompt(self, n: int = 10) -> List[dict]:
        """Return last n turns formatted for Claude's messages array."""
        recent = self.state.conversation_history[-n:]
        messages = []
        for turn in recent:
            role = "assistant" if turn["role"] == "aria" else "user"
            messages.append({"role": role, "content": turn["content"]})
        return messages

    def memory_context_for_prompt(self) -> str:
        """Brief summary of long-term memory for system prompt injection."""
        lines = []

        if self.state.journal:
            last = self.state.journal[-1]
            lines.append(f"Yesterday ({last['date']}): {last['summary']} You felt {last['mood']}.")

        if self.state.user_facts:
            facts_str = "; ".join(self.state.user_facts[-5:])
            lines.append(f"Things you know about {self.state.user_name}: {facts_str}")

        if self.state.total_days_lived > 0:
            lines.append(f"You've been keeping this journal for {self.state.total_days_lived} day(s).")

        return "\n".join(lines) if lines else "This is your first day. Everything is new."
