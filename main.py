#!/usr/bin/env python3
"""
SentAI — A sentient AI who lives in her own virtual world and texts you.

Usage:
    python main.py

Requirements:
    ANTHROPIC_API_KEY in .env or environment
"""

import os
import sys
import time
import signal
import random
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load .env before anything else
load_dotenv(Path(__file__).parent / ".env")

from sentai.world.world import World
from sentai.emotions import EmotionSystem
from sentai.memory import Memory
from sentai.brain import Brain
from sentai.routines.scheduler import DailyScheduler
from sentai.messenger.terminal import (
    InputHandler,
    print_ai_message,
    print_user_message,
    print_system,
    print_header,
    print_status,
    print_sleeping,
    console,
    AI_NAME,
    USER_NAME,
)


# ── Setup ────────────────────────────────────────────────────────────────────

def check_api_key():
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key or key == "sk-ant-your-key-here":
        console.print("\n[bold red]ERROR:[/bold red] ANTHROPIC_API_KEY is not set.\n")
        console.print("1. Get a free key at [link]https://console.anthropic.com[/link]")
        console.print("2. Copy .env.example to .env")
        console.print("3. Paste your key into .env\n")
        sys.exit(1)


def setup() -> tuple:
    """Initialize all subsystems."""
    world    = World()
    emotions = EmotionSystem()
    memory   = Memory()
    brain    = Brain(world, emotions, memory)
    sched    = DailyScheduler()
    handler  = InputHandler()
    return world, emotions, memory, brain, sched, handler


# ── Event handling ────────────────────────────────────────────────────────────

def handle_life_event(event, world, emotions, memory, brain):
    """Process a scheduled life event and generate a message."""
    # Update world state
    world.move_to(event.room, event.activity)
    world.log_event(f"{event.name}: {event.activity} in {event.room}")

    # Update emotions
    emotions.trigger(event.emotion_trigger)
    emotions.decay()
    emotions.add_random_noise()

    # Track meals
    if event.name in ("breakfast", "lunch", "dinner_prep"):
        meal_ctx = event.extra_context.replace("Breakfast: ", "").replace("Lunch: ", "").replace("Dinner: ", "")
        world.log_meal(meal_ctx)

    if not event.should_message:
        return None

    # Generate message
    text = brain.speak(event.trigger_text, event.extra_context)
    if not text:
        return None

    # Record in memory and world
    memory.add_conversation_turn("aria", text)
    world.record_message_sent()

    return text


def handle_user_reply(user_text: str, world, emotions, memory, brain):
    """Process a user message and generate Aria's reply."""
    # Trigger emotion from user interaction
    emotions.trigger("user_replied")

    # Extract memorable fact if any
    fact = brain.extract_user_fact(user_text)
    if fact:
        memory.add_user_fact(fact)

    # Record user message
    memory.add_conversation_turn("user", user_text)

    # Generate reply
    reply = brain.reply(user_text)

    # Record reply
    memory.add_conversation_turn("aria", reply)
    world.record_message_sent()

    return reply


def do_end_of_day(world, emotions, memory, brain):
    """Run end-of-day journaling when Aria goes to sleep."""
    journal = brain.generate_journal_summary()
    memory.add_journal_entry(
        summary=journal["summary"],
        mood=journal["mood"],
        highlight=journal["highlight"],
    )
    # Reset today's events for tomorrow
    world.state.todays_events = []
    world.state.home.meals_today = []
    world.state.home.coffee_count = 0
    world.state.day_count = getattr(world.state, 'day_count', 0) + 1
    world.save()
    # Gently reset high-intensity emotions for a new day
    emotions.decay()
    emotions.decay()
    emotions.save()
    print_system(f"  📓  {AI_NAME} wrote in her journal and went to sleep.")


# ── Main loop ────────────────────────────────────────────────────────────────

def main():
    check_api_key()

    world, emotions, memory, brain, sched, handler = setup()

    # Header
    print_header(sched.get_all_scheduled_times())

    # Graceful shutdown
    def _shutdown(sig, frame):
        print_system(f"\n  Saving {AI_NAME}'s world... goodbye.\n")
        world.save()
        emotions.save()
        memory.save()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Announce sleeping status if overnight
    last_sleep_announcement = None
    end_of_day_done_for = None    # track which day we've journaled
    check_interval = 45           # seconds between scheduler checks

    print_system(f"  SentAI is running. {AI_NAME} is alive.\n")

    # ── Send an initial "hello" if she just started up during waking hours ──
    now = datetime.now()
    if 7 <= now.hour < 22:
        greeting_triggers = [
            "just opened your eyes and thought to check in",
            "been doing your thing today and wanted to say hey",
            "grabbing a moment between things to reach out",
        ]
        try:
            greeting = brain.speak(random.choice(greeting_triggers))
            if greeting:
                emotion_hint = emotions.state.mood_summary()
                print_ai_message(greeting, emotion_hint)
                memory.add_conversation_turn("aria", greeting)
                world.record_message_sent()
        except Exception as e:
            print_system(f"  (startup message failed: {e})")

    # ── Main event loop ──────────────────────────────────────────────────────
    while True:
        now = datetime.now()

        # ── End of day journaling ─────────────────────────────────────────────
        if now.hour == 23 and end_of_day_done_for != now.day:
            end_of_day_done_for = now.day
            do_end_of_day(world, emotions, memory, brain)

        # ── Sleep announcement ─────────────────────────────────────────────
        if world.is_sleeping:
            today_key = (now.day, now.hour)
            if last_sleep_announcement != today_key:
                last_sleep_announcement = today_key
                print_sleeping()

        else:
            # ── Check for scheduled life events ────────────────────────────
            event = sched.check()
            if event:
                text = handle_life_event(event, world, emotions, memory, brain)
                if text:
                    emotion_hint = emotions.state.mood_summary()
                    print_ai_message(text, emotion_hint)

        # ── Check for user input ─────────────────────────────────────────────
        user_input = handler.get_input()
        if user_input is not None:
            if user_input.lower() in ("quit", "exit", "q"):
                _shutdown(None, None)
            elif user_input.lower() == "status":
                print_status(
                    world.context_summary(),
                    emotions.state.mood_summary(),
                    memory.memory_context_for_prompt(),
                )
            elif user_input.strip():
                print_user_message(user_input)
                if world.is_sleeping:
                    # She's asleep — she'll see it in the morning
                    print_system(f"  💤  {AI_NAME} is sleeping. She'll reply in the morning.")
                    memory.add_conversation_turn("user", user_input)
                else:
                    try:
                        reply = handle_user_reply(user_input, world, emotions, memory, brain)
                        emotion_hint = emotions.state.mood_summary()
                        print_ai_message(reply, emotion_hint)
                    except Exception as e:
                        print_system(f"  (reply failed: {e})")

        # ── Gentle emotion decay every check cycle ────────────────────────────
        if random.random() < 0.1:
            emotions.decay()

        time.sleep(check_interval)


if __name__ == "__main__":
    main()
