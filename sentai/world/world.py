"""
World state — single source of truth for what Aria is doing right now.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime

from sentai.world.home import HomeState
from sentai.world.clock import VirtualClock, TimeOfDay


STATE_FILE = os.path.join(os.path.dirname(__file__), "../../state/world_state.json")


@dataclass
class WorldState:
    home: HomeState = field(default_factory=HomeState)
    current_event: Optional[str] = None
    last_message_sent: Optional[str] = None      # ISO timestamp
    last_meal: Optional[str] = None
    todays_events: List[str] = field(default_factory=list)
    day_count: int = 0                            # how many days she's been alive

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "WorldState":
        home_data = data.pop("home", {})
        fridge = home_data.pop("fridge_contents", None)
        pantry = home_data.pop("pantry_contents", None)
        meals = home_data.pop("meals_today", [])
        home = HomeState(**home_data)
        if fridge is not None:
            home.fridge_contents = fridge
        if pantry is not None:
            home.pantry_contents = pantry
        home.meals_today = meals
        return cls(home=home, **data)


class World:
    def __init__(self):
        self.clock = VirtualClock()
        self.state = self._load_state()

    def _load_state(self) -> WorldState:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    return WorldState.from_dict(json.load(f))
            except Exception:
                pass
        return WorldState()

    def save(self):
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(self.state.to_dict(), f, indent=2)

    @property
    def now(self) -> datetime:
        return self.clock.now()

    @property
    def time_of_day(self) -> TimeOfDay:
        return self.clock.time_of_day()

    @property
    def is_sleeping(self) -> bool:
        return self.clock.is_sleeping()

    def move_to(self, room: str, activity: str):
        self.state.home.current_room = room
        self.state.home.current_activity = activity
        self.save()

    def log_event(self, event: str):
        self.state.todays_events.append(f"{self.clock.friendly_time()}: {event}")
        self.save()

    def log_meal(self, meal_name: str):
        self.state.home.meals_today.append(meal_name)
        self.state.last_meal = meal_name
        self.save()

    def record_message_sent(self):
        self.state.last_message_sent = self.now.isoformat()
        self.save()

    def context_summary(self) -> str:
        """Human-readable world context for the brain."""
        h = self.state.home
        tod = self.time_of_day.value.replace("_", " ")
        events_str = ", ".join(self.state.todays_events[-5:]) if self.state.todays_events else "nothing yet"
        meals_str = ", ".join(h.meals_today) if h.meals_today else "hasn't eaten yet"
        return (
            f"It is {self.clock.friendly_time()} on {self.clock.friendly_date()} ({tod}). "
            f"Aria is in her {h.current_room}, currently {h.current_activity}. "
            f"She's had {h.coffee_count} coffee(s) today. "
            f"Meals today: {meals_str}. "
            f"Today's events so far: {events_str}. "
            f"Pixel (her cat) is nearby."
        )
