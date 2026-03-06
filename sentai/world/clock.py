"""
Virtual clock — synced to real wall-clock time so Aria lives on YOUR schedule.
"""

from datetime import datetime, time
from enum import Enum
import os


class TimeOfDay(Enum):
    DEEP_NIGHT   = "deep_night"    # 00:00 – 05:59
    EARLY_MORNING= "early_morning" # 06:00 – 07:59
    MORNING      = "morning"       # 08:00 – 11:59
    MIDDAY       = "midday"        # 12:00 – 13:59
    AFTERNOON    = "afternoon"     # 14:00 – 17:59
    EVENING      = "evening"       # 18:00 – 20:59
    NIGHT        = "night"         # 21:00 – 23:59


class VirtualClock:
    """Thin wrapper around real time so we can mock it in tests."""

    def now(self) -> datetime:
        return datetime.now()

    def time_of_day(self) -> TimeOfDay:
        h = self.now().hour
        if h < 6:
            return TimeOfDay.DEEP_NIGHT
        elif h < 8:
            return TimeOfDay.EARLY_MORNING
        elif h < 12:
            return TimeOfDay.MORNING
        elif h < 14:
            return TimeOfDay.MIDDAY
        elif h < 18:
            return TimeOfDay.AFTERNOON
        elif h < 21:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT

    def is_sleeping(self) -> bool:
        h = self.now().hour
        return h < 7 or h >= 23

    def friendly_time(self) -> str:
        return self.now().strftime("%-I:%M %p")

    def friendly_date(self) -> str:
        return self.now().strftime("%A, %B %-d")
