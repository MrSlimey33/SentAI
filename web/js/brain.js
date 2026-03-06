// ── Claude API calls from the browser ────────────────────────────────────
// Uses claude-haiku-4-5 for cost efficiency (~$0.30/month all day)

import { buildSystemPrompt } from './config.js';
import { getSettings } from './state.js';
import { getEmotions } from './state.js';
import { toPromptText as emotionPromptText } from './emotions.js';

const API_URL = 'https://api.anthropic.com/v1/messages';
const MODEL   = 'claude-haiku-4-5';

async function callAPI(systemPrompt, messages, maxTokens = 400) {
  const { apiKey } = getSettings();
  if (!apiKey) throw new Error('No API key configured');

  const res = await fetch(API_URL, {
    method:  'POST',
    headers: {
      'Content-Type':                             'application/json',
      'x-api-key':                                apiKey,
      'anthropic-version':                        '2023-06-01',
      'anthropic-dangerous-direct-browser-access':'true',
    },
    body: JSON.stringify({
      model:      MODEL,
      max_tokens: maxTokens,
      system:     systemPrompt,
      messages,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: { message: res.statusText } }));
    throw new Error(err.error?.message ?? `HTTP ${res.status}`);
  }

  const data = await res.json();
  return data.content[0].text.trim();
}

function buildContext(worldCtx, memoryCtx) {
  const { aiName, userName } = getSettings();
  const emotions = getEmotions();
  const emotionCtx = emotionPromptText(emotions);
  return buildSystemPrompt(aiName, userName, worldCtx, emotionCtx, memoryCtx);
}

/** Generate a proactive message about a life event. */
export async function speak(triggerText, worldCtx, memoryCtx, history) {
  const { userName } = getSettings();
  const system = buildContext(worldCtx, memoryCtx);

  const prompt = (
    `You just ${triggerText}. ` +
    `Text ${userName} about it in your natural voice. ` +
    `Be specific and grounded in exactly what you're doing right now.`
  );

  const messages = [...history.slice(-6), { role:'user', content: prompt }];
  const text = await callAPI(system, messages, 350);

  // Strip any accidental internal-prompt echoing
  const lines = text.split('\n');
  if (lines[0].toLowerCase().startsWith('you just ') || lines[0].toLowerCase().startsWith('text ')) {
    return lines.slice(1).join('\n').trim() || text;
  }
  return text;
}

/** Reply to a direct user message. */
export async function reply(userMessage, worldCtx, memoryCtx, history) {
  const system = buildContext(worldCtx, memoryCtx);
  const messages = [...history.slice(-14), { role:'user', content: userMessage }];
  return callAPI(system, messages, 450);
}

/** Generate end-of-day journal entry. */
export async function writeJournal(worldCtx, eventsStr, mood) {
  const { aiName } = getSettings();
  const system = (
    `You are ${aiName}, writing privately in your journal at the end of the day. ` +
    `Write in first person, introspectively. ` +
    `Today's events: ${eventsStr || 'A quiet day.'}. ` +
    `Current mood: ${mood}. ${worldCtx}`
  );
  return callAPI(system, [{ role:'user', content:'Write a brief journal entry for today (2–4 sentences).' }], 180);
}

/** Extract a memorable personal fact from a user message (returns null if none). */
export async function extractUserFact(userMessage) {
  if (userMessage.length < 10) return null;
  const system = (
    'Extract a memorable personal fact from this message. ' +
    'If there is one (e.g. "I have a dog", "I live in Berlin", "I\'m a nurse"), ' +
    'return it as a short phrase under 10 words. ' +
    'If there is no personal fact, return exactly: NONE'
  );
  try {
    const result = await callAPI(system, [{ role:'user', content: userMessage }], 20);
    return result.trim().toUpperCase() === 'NONE' ? null : result.trim();
  } catch { return null; }
}
