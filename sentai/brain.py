"""
Aria's brain — Claude API integration.

All of Aria's spoken words come from here.
Uses claude-haiku-4-5 for cost efficiency (~$0.30/month for a full day of chatting).
"""

import os
import anthropic
from typing import Optional, List

from sentai.persona import get_system_prompt
from sentai.emotions import EmotionSystem
from sentai.memory import Memory
from sentai.world.world import World


class Brain:
    def __init__(self, world: World, emotions: EmotionSystem, memory: Memory):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.world = world
        self.emotions = emotions
        self.memory = memory
        # Model: haiku is the cheapest — keeps this effectively free
        self.model = "claude-haiku-4-5"

    def _build_system_prompt(self, extra_context: str = "") -> str:
        world_ctx = self.world.context_summary()
        if extra_context:
            world_ctx += f"\n\nAdditional context: {extra_context}"
        memory_ctx = self.memory.memory_context_for_prompt()
        if memory_ctx:
            world_ctx += f"\n\nMemory / history:\n{memory_ctx}"
        emotion_ctx = self.emotions.to_prompt_text()
        return get_system_prompt(world_ctx, emotion_ctx)

    def speak(self, trigger: str, extra_context: str = "") -> str:
        """
        Generate a proactive message from Aria about a life event.
        `trigger` is a short description of what just happened.
        """
        system = self._build_system_prompt(extra_context)

        # Use a short recent history so she sounds continuous
        history = self.memory.recent_conversation_for_prompt(n=6)

        # The "user" message here is an internal prompt — it won't be shown
        # We frame it as Aria thinking about what to text
        prompt_msg = (
            f"You just {trigger}. "
            f"Text {os.getenv('USER_NAME', 'your friend')} about it in your natural voice. "
            f"Be specific and grounded in the details of what you're actually doing."
        )

        messages = history + [{"role": "user", "content": prompt_msg}]

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=400,
                system=system,
                messages=messages,
            )
            text = response.content[0].text.strip()
            # Remove any accidental internal-prompt echoing
            if text.lower().startswith("you just ") or text.lower().startswith("text "):
                text = text.split("\n", 1)[-1].strip()
            return text
        except anthropic.APIError as e:
            return f"(Aria is having a moment — {e})"

    def reply(self, user_message: str) -> str:
        """
        Reply to a message from the user.
        This is a real back-and-forth conversation turn.
        """
        system = self._build_system_prompt()
        history = self.memory.recent_conversation_for_prompt(n=14)
        messages = history + [{"role": "user", "content": user_message}]

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=system,
                messages=messages,
            )
            return response.content[0].text.strip()
        except anthropic.APIError as e:
            return f"(sorry, can't think straight right now — {e})"

    def generate_journal_summary(self) -> dict:
        """At end of day, reflect on the day and write a journal entry."""
        world_ctx = self.world.context_summary()
        events = self.world.state.todays_events
        events_str = "\n".join(events) if events else "A quiet day."
        mood = self.emotions.state.mood_summary()

        system = f"""You are {os.getenv('AI_NAME', 'Aria')}, writing privately in your journal at the end of the day.
Write in first person, introspectively, as yourself.
Today's events: {events_str}
Current mood: {mood}
{world_ctx}"""

        messages = [{"role": "user", "content": "Write a brief journal entry for today (2–4 sentences)."}]
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                system=system,
                messages=messages,
            )
            summary = response.content[0].text.strip()
        except Exception:
            summary = f"A day lived. {events_str[:100]}"

        highlights = self.world.state.todays_events
        highlight = highlights[-1] if highlights else "just existing"
        return {
            "summary": summary,
            "mood": mood,
            "highlight": highlight,
        }

    def extract_user_fact(self, user_message: str) -> Optional[str]:
        """Try to extract a memorable fact about the user from their message."""
        if len(user_message) < 10:
            return None

        system = (
            "You extract memorable personal facts from messages. "
            "If the message contains a specific personal fact about the sender "
            "(e.g., 'I have a dog named Rex', 'I live in Seattle', 'I'm a nurse', "
            "'I hate mornings'), extract it as a SHORT phrase (under 10 words). "
            "If there's no memorable personal fact, respond with NONE."
        )
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=30,
                system=system,
                messages=[{"role": "user", "content": user_message}],
            )
            result = response.content[0].text.strip()
            if result.upper() == "NONE" or not result:
                return None
            return result
        except Exception:
            return None
