// ── Daily scheduler — fires life events based on real wall-clock time ─────
import {
  BREAKFAST_OPTIONS, LUNCH_OPTIONS, DINNER_OPTIONS,
  AFTERNOON_ACTIVITIES, EVENING_ACTIVITIES, CAT_BEHAVIORS,
  pick, pickPair,
} from './config.js';

/**
 * A LifeEvent is what gets returned when a scheduled moment arrives.
 * @typedef {{ name:string, triggerText:string, emotionTrigger:string,
 *             room:string, activity:string, shouldMessage:boolean, meal?:string }} LifeEvent
 */

/** Returns a LifeEvent if the current time matches an un-fired slot, else null. */
export function checkSchedule(hasFiredFn) {
  const now  = new Date();
  const h    = now.getHours();
  const m    = now.getMinutes();

  // ── Wake up ──────────────────────────────────────────────────────────────
  if (h === 7 && m < 30 && !hasFiredFn('wake_up')) {
    const groggy = Math.random() < 0.3;
    return {
      name: 'wake_up',
      triggerText: groggy
        ? 'just woke up groggy — hit snooze twice. not a morning person today'
        : pick([
            'just woke up and Pixel immediately sat on your face',
            'just woke up — the light through the curtains is really pretty this morning',
            'woke up to your alarm and actually feel okay today',
          ]),
      emotionTrigger: groggy ? 'woke_up_groggy' : 'woke_up_well',
      room: 'bedroom',
      activity: 'waking up',
      shouldMessage: true,
    };
  }

  // ── Morning coffee ────────────────────────────────────────────────────────
  if (h === 7 && m >= 30 && !hasFiredFn('morning_coffee')) {
    return {
      name: 'morning_coffee',
      triggerText: pick([
        'made your first espresso of the day and it came out PERFECT — nice crema',
        'made morning espresso. Pixel sat on the counter watching like a tiny judge',
        'made espresso and took it out to the balcony. the air is so fresh',
        'made coffee and sat in the windowsill just existing for a moment',
      ]),
      emotionTrigger: 'good_coffee',
      room: 'kitchen',
      activity: 'making espresso',
      shouldMessage: true,
    };
  }

  // ── Breakfast ──────────────────────────────────────────────────────────────
  if (h === 8 && m < 45 && !hasFiredFn('breakfast')) {
    const [meal, note] = pickPair(BREAKFAST_OPTIONS);
    return {
      name: 'breakfast',
      triggerText: `just finished making ${meal} for breakfast (${note})`,
      emotionTrigger: 'cooked_good_meal',
      room: 'kitchen',
      activity: 'eating breakfast',
      shouldMessage: true,
      meal,
    };
  }

  // ── Mid-morning (sometimes) ───────────────────────────────────────────────
  if (h === 10 && m < 30 && !hasFiredFn('mid_morning') && Math.random() < 0.5) {
    const [activity, note] = pick([
      ['settled into work — designing a new onboarding flow', 'deep focus'],
      ['been in a really good design session', 'everything is clicking'],
      ['sketching ideas for a side project', 'it\'s getting interesting'],
      ['reorganizing your Figma components', 'chaotic but necessary'],
    ]);
    return {
      name: 'mid_morning',
      triggerText: `${activity} (${note})`,
      emotionTrigger: Math.random() < 0.5 ? 'creative_breakthrough' : 'productive_work',
      room: 'living_room',
      activity: 'working',
      shouldMessage: true,
    };
  }
  // Register as fired even when skipped so it doesn't re-trigger
  if (h === 10 && m >= 30 && !hasFiredFn('mid_morning')) return { name:'mid_morning', _skip:true };

  // ── Lunch ──────────────────────────────────────────────────────────────────
  if (h === 12 && m < 30 && !hasFiredFn('lunch')) {
    const [meal, note] = pickPair(LUNCH_OPTIONS);
    const cat = pick(CAT_BEHAVIORS);
    return {
      name: 'lunch',
      triggerText: `made ${meal} for lunch (${note}). Pixel ${cat}`,
      emotionTrigger: 'cooked_good_meal',
      room: 'kitchen',
      activity: 'eating lunch',
      shouldMessage: true,
      meal,
    };
  }

  // ── Afternoon ────────────────────────────────────────────────────────────
  if (h === 14 && m < 30 && !hasFiredFn('afternoon')) {
    const [activity, note] = pickPair(AFTERNOON_ACTIVITIES);
    return {
      name: 'afternoon',
      triggerText: `been ${activity} this afternoon (${note})`,
      emotionTrigger: pick(['productive_work','nice_walk','good_book','good_music','pixel_cuddles']),
      room: pick(['living_room','bedroom','balcony']),
      activity,
      shouldMessage: true,
    };
  }

  // ── Spontaneous late-afternoon thought ───────────────────────────────────
  if (h === 16 && m < 30 && !hasFiredFn('late_afternoon') && Math.random() < 0.6) {
    return {
      name: 'late_afternoon',
      triggerText: pick([
        'noticed something funny just now',
        'found a song you\'ve been looking for for months',
        'your design finally came together and you\'re weirdly emotional about it',
        `Pixel just ${pick(CAT_BEHAVIORS)}`,
        'the light in the apartment right now is so golden and perfect',
        'randomly remembered something from a while ago and now you\'re nostalgic',
      ]),
      emotionTrigger: pick(['good_music','pixel_cuddles','nostalgic','peaceful']),
      room: 'living_room',
      activity: 'relaxing',
      shouldMessage: true,
    };
  }
  if (h === 16 && m >= 30 && !hasFiredFn('late_afternoon')) return { name:'late_afternoon', _skip:true };

  // ── Dinner prep ──────────────────────────────────────────────────────────
  if (h === 18 && m < 30 && !hasFiredFn('dinner_prep')) {
    const [meal, note] = pickPair(DINNER_OPTIONS);
    const cat = pick(CAT_BEHAVIORS);
    return {
      name: 'dinner_prep',
      triggerText: `in the middle of making ${meal} for dinner (${note}). Pixel ${cat}`,
      emotionTrigger: 'cooked_good_meal',
      room: 'kitchen',
      activity: 'cooking dinner',
      shouldMessage: true,
      meal,
    };
  }

  // ── Evening ──────────────────────────────────────────────────────────────
  if (h === 20 && m < 30 && !hasFiredFn('evening')) {
    const [activity, note] = pickPair(EVENING_ACTIVITIES);
    return {
      name: 'evening',
      triggerText: `settled in for the evening — ${activity} (${note})`,
      emotionTrigger: 'good_evening',
      room: pick(['living_room','bedroom']),
      activity,
      shouldMessage: true,
    };
  }

  // ── Bedtime ──────────────────────────────────────────────────────────────
  if (h === 22 && m < 30 && !hasFiredFn('bedtime')) {
    return {
      name: 'bedtime',
      triggerText: pick([
        'getting ready for bed. Pixel is already asleep — showing you up',
        'brushing teeth and winding down. today was a lot in a good way',
        'doing skincare and listening to something quiet. almost ready for bed',
        'about to try to read before sleep but will probably be asleep in 3 pages',
      ]),
      emotionTrigger: 'peaceful',
      room: 'bedroom',
      activity: 'getting ready for sleep',
      shouldMessage: true,
    };
  }

  return null;
}

export function isSleeping() {
  const h = new Date().getHours();
  return h < 7 || h >= 23;
}

export function friendlyTime() {
  return new Date().toLocaleTimeString('en-US', { hour:'numeric', minute:'2-digit' });
}

export function SCHEDULE_SUMMARY() {
  return [
    '~7:00 AM  — waking up',
    '~7:30 AM  — morning coffee ritual',
    '~8:00 AM  — after breakfast',
    '~10:00 AM — mid-morning (sometimes)',
    '~12:00 PM — lunchtime',
    '~2:00 PM  — afternoon adventures',
    '~4:00 PM  — spontaneous thought (random)',
    '~6:00 PM  — dinner in progress',
    '~8:00 PM  — evening settle-in',
    '~10:00 PM — bedtime',
    '+ anytime  — replies to your messages',
  ];
}
