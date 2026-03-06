// ── Centralized state with localStorage persistence ───────────────────────

const KEYS = {
  settings:  'sentai_settings',
  world:     'sentai_world',
  emotions:  'sentai_emotions',
  memory:    'sentai_memory',
  messages:  'sentai_messages',
  firedToday:'sentai_fired',
};

function load(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch { return fallback; }
}
function save(key, val) {
  try { localStorage.setItem(key, JSON.stringify(val)); } catch {}
}

// ── Settings ──────────────────────────────────────────────────────────────
export const defaultSettings = {
  apiKey:   '',
  userName: 'Friend',
  aiName:   'Aria',
};

export function getSettings()          { return load(KEYS.settings, { ...defaultSettings }); }
export function saveSettings(s)        { save(KEYS.settings, s); }

// ── World state ───────────────────────────────────────────────────────────
export const defaultWorld = {
  currentRoom:     'bedroom',
  currentActivity: 'sleeping',
  catLocation:     'bedroom',
  coffeesToday:    0,
  mealsToday:      [],
  todaysEvents:    [],   // {time, text}
  dayCount:        0,
};

export function getWorld()      { return load(KEYS.world, { ...defaultWorld }); }
export function saveWorld(w)    { save(KEYS.world, w); }

// ── Emotion state ─────────────────────────────────────────────────────────
export const defaultEmotions = {
  happy:       0.5,
  peaceful:    0.5,
  content:     0.6,
  excited:     0.2,
  energized:   0.3,
  tired:       0.3,
  sad:         0.1,
  anxious:     0.1,
  bored:       0.1,
  melancholic: 0.1,
  irritated:   0.05,
  nostalgic:   0.1,
};

export function getEmotions()     { return load(KEYS.emotions, { ...defaultEmotions }); }
export function saveEmotions(e)   { save(KEYS.emotions, e); }

// ── Memory ────────────────────────────────────────────────────────────────
export const defaultMemory = {
  journal:     [],   // [{date, summary, mood, highlight}]
  userFacts:   [],   // short strings
  dayCount:    0,
  firstDay:    new Date().toLocaleDateString('en-US', {month:'long', day:'numeric', year:'numeric'}),
};

export function getMemory()     { return load(KEYS.memory, { ...defaultMemory }); }
export function saveMemory(m)   { save(KEYS.memory, m); }

// ── Chat messages ─────────────────────────────────────────────────────────
export function getMessages()      { return load(KEYS.messages, []); }
export function saveMessages(arr)  { save(KEYS.messages, arr); }

export function addMessage(role, text, emotionHint = '') {
  const msgs = getMessages();
  msgs.push({
    role,              // 'aria' | 'user'
    text,
    emotionHint,
    time: new Date().toLocaleTimeString('en-US', { hour:'numeric', minute:'2-digit' }),
    ts:   Date.now(),
  });
  // keep last 200 messages
  if (msgs.length > 200) msgs.splice(0, msgs.length - 200);
  saveMessages(msgs);
  return msgs;
}

// ── Fired-today tracker ────────────────────────────────────────────────────
export function getFiredToday() {
  const today = new Date().toDateString();
  const stored = load(KEYS.firedToday, { day: '', fired: [] });
  if (stored.day !== today) return { day: today, fired: [] };
  return stored;
}
export function markFired(name) {
  const ft = getFiredToday();
  if (!ft.fired.includes(name)) ft.fired.push(name);
  save(KEYS.firedToday, ft);
}
export function hasFired(name) {
  return getFiredToday().fired.includes(name);
}

// ── Helpers ────────────────────────────────────────────────────────────────
export function resetAll() {
  Object.values(KEYS).forEach(k => localStorage.removeItem(k));
}

export function getConversationHistory(n = 12) {
  const msgs = getMessages().slice(-n);
  return msgs.map(m => ({
    role:    m.role === 'aria' ? 'assistant' : 'user',
    content: m.text,
  }));
}
