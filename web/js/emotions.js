// ── Emotion system ─────────────────────────────────────────────────────────
import { EMOTION_TRIGGERS, EMOTION_DEFS } from './config.js';
import { getEmotions, saveEmotions, defaultEmotions } from './state.js';

export function triggerEmotion(eventName, intensity = 1.0) {
  const emotions = getEmotions();
  const deltas = EMOTION_TRIGGERS[eventName] || {};
  for (const [key, delta] of Object.entries(deltas)) {
    if (key in emotions) {
      emotions[key] = clamp(emotions[key] + delta * intensity);
    }
  }
  saveEmotions(emotions);
  return emotions;
}

export function decayEmotions() {
  const emotions = getEmotions();
  for (const key of Object.keys(defaultEmotions)) {
    const current  = emotions[key] ?? defaultEmotions[key];
    const baseline = defaultEmotions[key];
    emotions[key] = clamp(current + (baseline - current) * 0.08);
  }
  saveEmotions(emotions);
  return emotions;
}

export function addNoise(scale = 0.025) {
  const emotions = getEmotions();
  for (const key of Object.keys(emotions)) {
    emotions[key] = clamp(emotions[key] + (Math.random() - 0.5) * 2 * scale);
  }
  saveEmotions(emotions);
  return emotions;
}

export function dominant(emotions) {
  return Object.entries(emotions).sort((a,b) => b[1] - a[1])[0][0];
}

export function topThree(emotions) {
  return Object.entries(emotions).sort((a,b) => b[1] - a[1]).slice(0,3).map(e=>e[0]);
}

export function moodSummary(emotions) {
  const top = topThree(emotions);
  const secondary = emotions[top[1]] > 0.25 ? top[1] : null;
  return secondary ? `${top[0]} with hints of ${secondary}` : top[0];
}

export function positivity(emotions) {
  const pos = (emotions.happy + emotions.excited + emotions.peaceful + emotions.content + emotions.energized) / 5;
  const neg = (emotions.sad + emotions.anxious + emotions.tired + emotions.bored + emotions.irritated) / 5;
  return clamp((pos - neg + 1) / 2);
}

export function toPromptText(emotions) {
  const top = topThree(emotions);
  const scores = top.map(e => `${e} (${Math.round(emotions[e] * 100)}%)`).join(', ');
  const mood = moodSummary(emotions);
  const pos = positivity(emotions);
  const lines = [`Mood: ${mood}`, `Top emotions: ${scores}`, `Positivity: ${Math.round(pos * 100)}%`];
  if (emotions.tired > 0.6)    lines.push('Writing style: tired, low energy, shorter messages');
  if (emotions.excited > 0.6)  lines.push('Writing style: enthusiastic, energetic, maybe caps for emphasis');
  if (emotions.happy > 0.65)   lines.push('Writing style: upbeat, feel free to use emojis naturally');
  if (emotions.peaceful > 0.65)lines.push('Writing style: calm, thoughtful, a little poetic');
  if (emotions.irritated > 0.4)lines.push('Writing style: a bit short or grumpy, still warm but low patience');
  if (emotions.anxious > 0.5)  lines.push('Writing style: slightly overthinking, a little scattered');
  if (emotions.sad > 0.5)      lines.push('Writing style: quieter, introspective, lower energy');
  return lines.join('\n');
}

export function dominantEmoji(emotions) {
  const d = dominant(emotions);
  return EMOTION_DEFS[d]?.emoji ?? '🌸';
}

function clamp(v) { return Math.max(0, Math.min(1, Math.round(v * 1000) / 1000)); }
