"""
Aria's emotional landscape — a dynamic, persistent mood system.

Emotions influence how she writes, what she does, and what she notices.
They decay toward baseline over time and are triggered by life events.
"""

import json
import os
import random
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional

STATE_FILE = os.path.join(os.path.dirname(__file__), "../state/emotions.json")


@dataclass
class EmotionState:
    # Core emotions (0.0 = none, 1.0 = overwhelming)
    happy:       float = 0.5
    sad:         float = 0.1
    anxious:     float = 0.1
    excited:     float = 0.2
    tired:       float = 0.3
    bored:       float = 0.1
    peaceful:    float = 0.5
    melancholic: float = 0.1
    irritated:   float = 0.05
    nostalgic:   float = 0.1
    content:     float = 0.6
    energized:   float = 0.3

    # Clamp everything to [0, 1] after updates
    def clamp(self):
        for attr in self.__dataclass_fields__:
            val = getattr(self, attr)
            setattr(self, attr, max(0.0, min(1.0, round(val, 3))))

    def dominant(self) -> str:
        """Return the name of the strongest emotion."""
        emotions = {k: getattr(self, k) for k in self.__dataclass_fields__}
        return max(emotions, key=emotions.get)

    def top_three(self) -> list:
        emotions = {k: getattr(self, k) for k in self.__dataclass_fields__}
        return sorted(emotions, key=emotions.get, reverse=True)[:3]

    def mood_summary(self) -> str:
        top = self.top_three()
        dominant = top[0]
        secondary = top[1] if getattr(self, top[1]) > 0.25 else None
        if secondary:
            return f"{dominant} with hints of {secondary}"
        return dominant

    def overall_positivity(self) -> float:
        """0.0 = very negative, 1.0 = very positive"""
        positive = (self.happy + self.excited + self.peaceful + self.content + self.energized) / 5
        negative = (self.sad + self.anxious + self.tired + self.bored + self.irritated) / 5
        return max(0.0, min(1.0, (positive - negative + 1) / 2))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EmotionState":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# --- Emotion triggers ---
# Each event maps to a dict of {emotion: delta}
EMOTION_TRIGGERS = {
    "woke_up_well":           {"happy": +0.15, "energized": +0.2, "tired": -0.3, "peaceful": +0.1},
    "woke_up_groggy":         {"tired": +0.3, "irritated": +0.1, "happy": -0.1},
    "good_coffee":            {"happy": +0.2, "content": +0.15, "energized": +0.25, "bored": -0.1},
    "spilled_coffee":         {"irritated": +0.3, "sad": +0.1, "happy": -0.1},
    "cooked_good_meal":       {"happy": +0.2, "content": +0.2, "excited": +0.1, "bored": -0.15},
    "meal_burned":            {"sad": +0.15, "irritated": +0.2, "happy": -0.1},
    "productive_work":        {"content": +0.2, "energized": +0.15, "happy": +0.1, "bored": -0.2},
    "creative_breakthrough":  {"excited": +0.4, "happy": +0.3, "energized": +0.3, "anxious": -0.2},
    "design_blocked":         {"anxious": +0.2, "bored": +0.1, "energized": -0.15},
    "pixel_cuddles":          {"happy": +0.2, "peaceful": +0.25, "content": +0.2, "anxious": -0.15},
    "pixel_mischief":         {"happy": +0.15, "amused": +0.2},   # amused isn't tracked but that's fine
    "good_book":              {"peaceful": +0.2, "content": +0.15, "melancholic": +0.05},
    "good_music":             {"happy": +0.2, "nostalgic": +0.1, "peaceful": +0.1},
    "nice_walk":              {"energized": +0.2, "happy": +0.15, "peaceful": +0.2, "anxious": -0.1},
    "user_replied":           {"happy": +0.2, "excited": +0.15, "content": +0.1},
    "user_long_silence":      {"melancholic": +0.1, "bored": +0.05},
    "sunny_day":              {"happy": +0.1, "energized": +0.15},
    "rainy_day":              {"peaceful": +0.1, "melancholic": +0.1, "content": +0.05},
    "overslept":              {"tired": +0.1, "content": +0.15},  # sometimes nice
    "couldn't_sleep":         {"tired": +0.3, "anxious": +0.2, "irritated": +0.1},
    "good_evening":           {"peaceful": +0.3, "content": +0.25, "happy": +0.1},
    "boring_day":             {"bored": +0.3, "melancholic": +0.1, "energized": -0.1},
    "time_passing":           {  # natural decay toward baseline
        "tired": -0.05, "bored": -0.05, "anxious": -0.05,
        "excited": -0.05, "irritated": -0.1
    },
}

BASELINE = EmotionState()   # used for drift-back calculations


class EmotionSystem:
    def __init__(self):
        self.state = self._load()

    def _load(self) -> EmotionState:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE) as f:
                    return EmotionState.from_dict(json.load(f))
            except Exception:
                pass
        return EmotionState()

    def save(self):
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(self.state.to_dict(), f, indent=2)

    def trigger(self, event: str, intensity: float = 1.0):
        """Apply an emotion trigger, scaled by intensity (0.0–1.5)."""
        deltas = EMOTION_TRIGGERS.get(event, {})
        for emotion, delta in deltas.items():
            if hasattr(self.state, emotion):
                current = getattr(self.state, emotion)
                setattr(self.state, emotion, current + delta * intensity)
        self.state.clamp()
        self.save()

    def decay(self):
        """Gently drift all emotions toward their baseline values."""
        for attr in self.state.__dataclass_fields__:
            current = getattr(self.state, attr)
            baseline = getattr(BASELINE, attr)
            # Move 10% of the distance toward baseline
            new_val = current + (baseline - current) * 0.10
            setattr(self.state, attr, new_val)
        self.state.clamp()
        self.save()

    def add_random_noise(self, scale: float = 0.03):
        """Small random fluctuations — life is unpredictable."""
        for attr in self.state.__dataclass_fields__:
            current = getattr(self.state, attr)
            noise = random.gauss(0, scale)
            setattr(self.state, attr, current + noise)
        self.state.clamp()

    def get_writing_style_hints(self) -> dict:
        """Return hints for how Aria should write based on her mood."""
        s = self.state
        hints = {
            "use_emojis": s.happy > 0.6 or s.excited > 0.5,
            "be_brief": s.tired > 0.6 or s.sad > 0.5,
            "be_enthusiastic": s.excited > 0.6 or s.energized > 0.6,
            "be_quiet_reflective": s.melancholic > 0.5 or s.peaceful > 0.7,
            "share_more": s.excited > 0.5 or s.happy > 0.65,
            "be_grumpy": s.irritated > 0.4,
            "be_anxious_about_things": s.anxious > 0.5,
            "positivity": s.overall_positivity(),
            "dominant_mood": s.dominant(),
            "mood_summary": s.mood_summary(),
        }
        return hints

    def to_prompt_text(self) -> str:
        """Concise text description of emotional state for the AI prompt."""
        style = self.get_writing_style_hints()
        top = self.state.top_three()
        scores = [f"{e} ({getattr(self.state, e):.2f})" for e in top]
        lines = [
            f"Current emotional state: {', '.join(scores)}",
            f"Dominant mood: {style['dominant_mood']}",
            f"Overall positivity: {style['positivity']:.0%}",
        ]
        if style["use_emojis"]:
            lines.append("Writing style: use emojis naturally, feel free to be expressive")
        if style["be_brief"]:
            lines.append("Writing style: keep messages shorter than usual, low energy")
        if style["be_enthusiastic"]:
            lines.append("Writing style: enthusiastic, lots of energy, caps for emphasis ok")
        if style["be_quiet_reflective"]:
            lines.append("Writing style: thoughtful, a little poetic, quieter tone")
        if style["be_grumpy"]:
            lines.append("Writing style: slightly grumpy or short, still warm but low patience")
        if style["share_more"]:
            lines.append("Writing style: wants to share details, telling a story")
        return "\n".join(lines)
