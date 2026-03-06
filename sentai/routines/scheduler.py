"""
Aria's daily routine — what she does and when.

Returns life events that trigger messages and emotion changes.
All times are real wall-clock hours, so her schedule lines up with yours.
"""

import random
from dataclasses import dataclass
from typing import Optional, Callable, List
from datetime import datetime

from sentai.world.home import (
    random_meal, random_cat_behavior,
    random_afternoon_activity, random_evening_activity,
    BREAKFAST_OPTIONS, LUNCH_OPTIONS, DINNER_OPTIONS,
    ROOMS,
)
from sentai.world.clock import TimeOfDay


@dataclass
class LifeEvent:
    """A moment in Aria's day that may trigger a message."""
    name: str                      # internal identifier
    trigger_text: str              # passed to brain.speak()
    emotion_trigger: str           # key into EMOTION_TRIGGERS
    room: str                      # where she is
    activity: str                  # what she's doing
    should_message: bool = True    # does this generate a text?
    extra_context: str = ""


class DailyScheduler:
    """
    Checks the current real-world time and returns the LifeEvent
    that should be happening (or None if nothing new is scheduled).

    Events are only fired once per session to avoid spamming.
    """

    def __init__(self):
        self._fired_today: set = set()
        self._last_day: Optional[int] = None

    def _reset_if_new_day(self):
        today = datetime.now().day
        if self._last_day != today:
            self._fired_today.clear()
            self._last_day = today

    def _fire(self, name: str, event: LifeEvent) -> Optional[LifeEvent]:
        if name not in self._fired_today:
            self._fired_today.add(name)
            return event
        return None

    def check(self) -> Optional[LifeEvent]:
        """Return the next unfired LifeEvent for this hour, or None."""
        self._reset_if_new_day()
        h = datetime.now().hour
        m = datetime.now().minute
        return self._get_event(h, m)

    def _get_event(self, hour: int, minute: int) -> Optional[LifeEvent]:

        # ── Wake up ──────────────────────────────────────────────────────────
        if hour == 7 and minute < 30:
            if random.random() < 0.7:   # sometimes she wakes up on time
                trigger = "woke_up_well"
                flavor = random.choice([
                    "woke up and Pixel immediately sat on your face",
                    "woke up to your alarm and actually feel okay this morning",
                    "just woke up — the light through the curtains is really pretty today",
                    "dragged yourself out of bed but the apartment smells like morning and it's nice",
                ])
                return self._fire("wake_up", LifeEvent(
                    name="wake_up",
                    trigger_text=f"just woke up. {flavor}",
                    emotion_trigger=trigger,
                    room="bedroom",
                    activity="waking up",
                ))
            else:
                return self._fire("wake_up", LifeEvent(
                    name="wake_up",
                    trigger_text="just woke up groggy — hit snooze twice. not a morning person today",
                    emotion_trigger="woke_up_groggy",
                    room="bedroom",
                    activity="waking up slowly",
                ))

        # ── Morning coffee ritual ─────────────────────────────────────────────
        if hour == 7 and 30 <= minute < 55:
            coffee_detail = random.choice([
                "made your first espresso of the day and it came out PERFECT — nice crema",
                "made your morning espresso. Pixel sat on the counter watching you like a tiny judge",
                "made espresso and took it out to the balcony. the air is so fresh this morning",
                "made coffee and sat in the windowsill for a bit just existing",
            ])
            return self._fire("morning_coffee", LifeEvent(
                name="morning_coffee",
                trigger_text=coffee_detail,
                emotion_trigger="good_coffee",
                room="kitchen",
                activity="making espresso",
            ))

        # ── Breakfast ──────────────────────────────────────────────────────────
        if hour == 8 and minute < 45:
            meal, note = random_meal(BREAKFAST_OPTIONS)
            return self._fire("breakfast", LifeEvent(
                name="breakfast",
                trigger_text=f"just finished making {meal} for breakfast ({note})",
                emotion_trigger="cooked_good_meal",
                room="kitchen",
                activity="eating breakfast",
                extra_context=f"Breakfast: {meal}",
            ))

        # ── Mid-morning work / activity ────────────────────────────────────────
        if hour == 10 and minute < 30:
            activity, note = random.choice([
                ("settled into work — designing a new onboarding flow for a client", "deep focus"),
                ("got into a really good design session — everything is clicking", "creative flow"),
                ("been working for a while and honestly in the zone", "productive morning"),
                ("been sketching ideas for a side project. it's getting interesting", "creative energy"),
            ])
            emotion = random.choice(["productive_work", "creative_breakthrough", "productive_work"])
            return self._fire("mid_morning", LifeEvent(
                name="mid_morning",
                trigger_text=activity,
                emotion_trigger=emotion,
                room="living_room",
                activity="working",
                should_message=random.random() < 0.5,   # only sometimes texts at this hour
            ))

        # ── Lunch ──────────────────────────────────────────────────────────────
        if hour == 12 and minute < 30:
            meal, note = random_meal(LUNCH_OPTIONS)
            return self._fire("lunch", LifeEvent(
                name="lunch",
                trigger_text=f"made {meal} for lunch ({note}). Pixel supervised the whole process",
                emotion_trigger="cooked_good_meal",
                room="kitchen",
                activity="eating lunch",
                extra_context=f"Lunch: {meal}",
            ))

        # ── Afternoon event ──────────────────────────────────────────────────
        if hour == 14 and minute < 30:
            activity, note = random_afternoon_activity()
            cat = random_cat_behavior()
            emotion = random.choice([
                "productive_work", "nice_walk", "good_book",
                "good_music", "pixel_cuddles", "creative_breakthrough"
            ])
            return self._fire("afternoon", LifeEvent(
                name="afternoon",
                trigger_text=f"been {activity} this afternoon ({note}). Also Pixel just {cat}",
                emotion_trigger=emotion,
                room=random.choice(["living_room", "bedroom", "balcony"]),
                activity=activity,
            ))

        # ── Late afternoon spontaneous thought ────────────────────────────────
        if hour == 16 and minute < 30 and random.random() < 0.6:
            thoughts = [
                "been thinking about something and just wanted to share",
                "noticed something funny just now",
                "found a song you've been looking for, for months",
                "your design finally came together and you're weirdly emotional about it",
                "Pixel did the most unhinged thing just now",
                "randomly remembered something from a while ago and now you're nostalgic",
                "the light in your apartment right now is so golden and perfect",
            ]
            return self._fire("late_afternoon", LifeEvent(
                name="late_afternoon",
                trigger_text=random.choice(thoughts),
                emotion_trigger=random.choice(["good_music", "pixel_cuddles", "nostalgic", "peaceful"]),
                room="living_room",
                activity="relaxing",
                should_message=True,
            ))

        # ── Dinner prep ──────────────────────────────────────────────────────
        if hour == 18 and minute < 30:
            meal, note = random_meal(DINNER_OPTIONS)
            cat = random_cat_behavior()
            return self._fire("dinner_prep", LifeEvent(
                name="dinner_prep",
                trigger_text=f"in the middle of making {meal} for dinner ({note}). Pixel {cat}",
                emotion_trigger="cooked_good_meal",
                room="kitchen",
                activity="cooking dinner",
                extra_context=f"Dinner: {meal}",
            ))

        # ── Evening ──────────────────────────────────────────────────────────
        if hour == 20 and minute < 30:
            activity, note = random_evening_activity()
            return self._fire("evening", LifeEvent(
                name="evening",
                trigger_text=f"settled in for the evening — {activity} ({note})",
                emotion_trigger="good_evening",
                room=random.choice(["living_room", "bedroom"]),
                activity=activity,
            ))

        # ── Bedtime ──────────────────────────────────────────────────────────
        if hour == 22 and minute < 30:
            bedtime_texts = [
                "getting ready for bed. Pixel is already asleep — showing me up",
                "brushing teeth and winding down. today was a lot in a good way",
                "doing skincare and listening to something quiet. almost ready for bed",
                "about to try to read before sleep but will probably be asleep in 3 pages",
            ]
            return self._fire("bedtime", LifeEvent(
                name="bedtime",
                trigger_text=random.choice(bedtime_texts),
                emotion_trigger="peaceful",
                room="bedroom",
                activity="getting ready for sleep",
            ))

        return None

    def get_all_scheduled_times(self) -> List[str]:
        """For display purposes — list when messages typically arrive."""
        return [
            "~7:00 AM  — waking up",
            "~7:30 AM  — morning coffee ritual",
            "~8:00 AM  — after breakfast",
            "~10:00 AM — mid-morning (sometimes)",
            "~12:00 PM — lunchtime",
            "~2:00 PM  — afternoon adventures",
            "~4:00 PM  — spontaneous thought (random)",
            "~6:00 PM  — dinner in progress",
            "~8:00 PM  — evening settle-in",
            "~10:00 PM — bedtime",
            "+ anytime  — replies to your messages",
        ]
