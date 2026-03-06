"""
Messaging interface — renders the chat in a pretty terminal UI
and optionally forwards messages to Discord via webhook.

The terminal is always active. Discord is opt-in via DISCORD_WEBHOOK_URL in .env.
"""

import os
import sys
import threading
import queue
import time
import requests
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich import box
from rich.columns import Columns
from rich.rule import Rule

AI_NAME   = os.getenv("AI_NAME", "Aria")
USER_NAME = os.getenv("USER_NAME", "Friend")

# Colors
COLOR_AI      = "bright_magenta"
COLOR_USER    = "bright_cyan"
COLOR_SYSTEM  = "dim white"
COLOR_TIME    = "grey50"
COLOR_EMOTION = "yellow"


console = Console()


def _timestamp() -> str:
    return datetime.now().strftime("%-I:%M %p")


def print_ai_message(text: str, emotion_hint: str = ""):
    """Render Aria's message in a styled panel."""
    header = Text(f"  {AI_NAME}  ", style=f"bold {COLOR_AI}")
    if emotion_hint:
        header.append(f"  [{emotion_hint}]", style=COLOR_EMOTION)

    body = Text(text, style="white")

    console.print()
    console.print(Panel(
        body,
        title=header,
        title_align="left",
        border_style=COLOR_AI,
        padding=(0, 1),
    ))
    console.print(Text(f"  {_timestamp()}", style=COLOR_TIME))

    # Forward to Discord if configured
    _send_discord(f"**{AI_NAME}**: {text}")


def print_user_message(text: str):
    """Render user's message."""
    body = Text(f"{USER_NAME}: {text}", style=f"bold {COLOR_USER}")
    console.print(body, justify="right")
    console.print(Text(f"{_timestamp()}  ", style=COLOR_TIME), justify="right")


def print_system(text: str):
    console.print(f"[{COLOR_SYSTEM}]{text}[/{COLOR_SYSTEM}]")


def print_header(schedule_lines: list):
    console.print()
    console.print(Rule(style="bright_magenta"))
    title = Text()
    title.append("  ✦  SentAI  ", style="bold bright_magenta")
    title.append(f"— {AI_NAME}'s World  ✦", style="bright_magenta")
    console.print(title, justify="center")
    console.print(Rule(style="bright_magenta"))
    console.print()
    console.print(f"[{COLOR_SYSTEM}]She'll text you spontaneously throughout the day:[/{COLOR_SYSTEM}]")
    for line in schedule_lines:
        console.print(f"[{COLOR_SYSTEM}]  {line}[/{COLOR_SYSTEM}]")
    console.print()
    console.print(f"[{COLOR_SYSTEM}]Type your message and press Enter to reply.[/{COLOR_SYSTEM}]")
    console.print(f"[{COLOR_SYSTEM}]Type 'quit' to exit, 'status' to see her current state.[/{COLOR_SYSTEM}]")
    console.print()


def print_status(world_ctx: str, emotion_summary: str, memory_hint: str):
    console.print()
    console.print(Panel(
        f"[white]{world_ctx}[/white]\n\n"
        f"[yellow]Emotions: {emotion_summary}[/yellow]\n\n"
        f"[dim]{memory_hint}[/dim]",
        title=f"[bold]{AI_NAME}'s Current State[/bold]",
        border_style="yellow",
        padding=(0, 1),
    ))
    console.print()


def print_sleeping():
    console.print(
        f"[{COLOR_SYSTEM}]  💤  {AI_NAME} is sleeping. She'll text you in the morning.[/{COLOR_SYSTEM}]"
    )


def _send_discord(text: str):
    """Optional: forward messages to a Discord channel via webhook."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return
    try:
        requests.post(
            webhook_url,
            json={"content": text},
            timeout=5,
        )
    except Exception:
        pass  # Discord is optional; don't crash if it fails


class InputHandler:
    """
    Non-blocking input reader that works alongside the scheduler loop.
    Runs input() in a background thread and puts results in a queue.
    """

    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        while True:
            try:
                line = sys.stdin.readline()
                if line:
                    self._queue.put(line.rstrip("\n"))
            except (EOFError, KeyboardInterrupt):
                self._queue.put(None)
                break

    def get_input(self) -> Optional[str]:
        """Return next user input if available, else None."""
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None
