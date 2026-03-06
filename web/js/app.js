// ── Main application — wires everything together ──────────────────────────
import { checkSchedule, isSleeping, friendlyTime } from './scheduler.js';
import { triggerEmotion, decayEmotions, addNoise, dominant, moodSummary, positivity, dominantEmoji as getDominantEmoji } from './emotions.js';
import { speak, reply, writeJournal, extractUserFact } from './brain.js';
import { EMOTION_DEFS, ROOMS, pick } from './config.js';
import {
  getSettings, saveSettings,
  getWorld, saveWorld,
  getEmotions, saveEmotions,
  getMemory, saveMemory,
  getMessages, addMessage,
  getFiredToday, markFired, hasFired,
  getConversationHistory,
  resetAll,
} from './state.js';

// ── DOM references ─────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const setupOverlay   = $('setup-overlay');
const appDiv         = $('app');
const headerStatus   = $('header-status-text');
const headerTime     = $('header-time');
const statusDot      = $('status-dot');
const chatName       = $('chat-name');
const chatAvatar     = $('chat-avatar');
const chatSubtitle   = $('chat-subtitle');
const messagesDiv    = $('messages');
const todayLabel     = $('today-label');
const userInput      = $('user-input');
const sendBtn        = $('send-btn');
const typingInd      = $('typing-indicator');
const sleepingNotice = $('sleeping-notice');
const sleepingName   = $('sleeping-name');
const logList        = $('log-list');
const stateActivity  = $('state-activity');
const stateMood      = $('state-mood');
const stateCoffee    = $('state-coffee');
const stateMeals     = $('state-meals');
const energyBar      = $('energy-bar');
const happinessBar   = $('happiness-bar');
const emotionBarsDiv = $('emotion-bars');
const dominantEmojiEl = $('dominant-emoji');
const dominantLabel  = $('dominant-label');
const journalDiv     = $('journal-entries');
const pixelBadge     = $('pixel-badge');
const settingsBtn    = $('settings-btn');
const settingsModal  = $('settings-modal');
const settingsClose  = $('settings-close');
const settingsKey    = $('settings-key');
const settingsUsername = $('settings-username');
const settingsAiname = $('settings-ainame');
const settingsSave   = $('settings-save');
const resetBtn       = $('reset-btn');

// ── Boot ────────────────────────────────────────────────────────────────────
// Setup form is handled by the plain <script> in index.html (no module needed).
// Here we only need to start the app when a key already exists.
function boot() {
  const settings = getSettings();
  if (settings.apiKey) {
    startApp(settings);
  }
  // No key → setup overlay is visible by default from HTML; plain script handles it.
}

// ── App start ──────────────────────────────────────────────────────────────
function startApp(settings) {
  appDiv.hidden       = false;
  setupOverlay.hidden = true;
  // Apply names
  chatName.textContent   = settings.aiName;
  chatAvatar.textContent = settings.aiName.charAt(0).toUpperCase();
  sleepingName.textContent = settings.aiName;
  todayLabel.textContent = new Date().toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'});

  // Load & render existing messages
  renderAllMessages();
  renderEmotions();
  renderWorld();
  renderJournal();

  // Bind UI
  bindChat();
  bindSettings();

  // Start loops
  tickClock();
  setInterval(tickClock, 30_000);       // update clock every 30s
  setInterval(tickScheduler, 60_000);   // check scheduler every 60s
  setInterval(() => { decayEmotions(); renderEmotions(); }, 300_000); // decay every 5 min

  // Immediate scheduler check (catches up if opened mid-day)
  setTimeout(tickScheduler, 2000);
}

// ── Clock tick ──────────────────────────────────────────────────────────────
function tickClock() {
  const now  = new Date();
  headerTime.textContent = now.toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'});
  const sleeping = isSleeping();

  if (sleeping) {
    statusDot.className   = 'status-dot sleeping';
    headerStatus.textContent = `${getSettings().aiName} is sleeping`;
    chatSubtitle.textContent = '💤 sleeping';
    sleepingNotice.hidden = false;
    sendBtn.disabled      = false; // allow leaving messages
  } else {
    statusDot.className   = 'status-dot';
    const mood = moodSummary(getEmotions());
    headerStatus.textContent = `feeling ${mood}`;
    chatSubtitle.textContent = 'online';
    sleepingNotice.hidden = true;
  }
}

// ── Scheduler tick ──────────────────────────────────────────────────────────
async function tickScheduler() {
  if (isSleeping()) {
    // End-of-day journal at ~23:00
    const h = new Date().getHours();
    if (h >= 23 && !hasFired('journal')) {
      markFired('journal');
      await doEndOfDay();
    }
    return;
  }

  const event = checkSchedule(hasFired);
  if (!event) return;

  markFired(event.name);
  if (event._skip) return;
  if (!event.shouldMessage) return;

  // Update world
  updateWorld(event.room, event.activity, event.meal);

  // Update emotions
  triggerEmotion(event.emotionTrigger);
  addNoise();
  renderEmotions();

  // Log event
  logEvent(`${event.activity} in ${event.room.replace('_',' ')}`);

  // Generate & send message
  showTyping();
  try {
    const text = await speak(
      event.triggerText,
      buildWorldContext(),
      buildMemoryContext(),
      getConversationHistory(6),
    );
    hideTyping();
    const emotions = getEmotions();
    const hint     = moodSummary(emotions);
    addMessage('aria', text, hint);
    appendMessage({ role:'aria', text, emotionHint: hint,
      time: new Date().toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'}) });
    scrollToBottom();
  } catch(err) {
    hideTyping();
    console.error('speak error:', err);
    appendSystemMsg(`(${getSettings().aiName} is having a moment — ${err.message})`);
  }
}

// ── User sends a message ───────────────────────────────────────────────────
async function handleUserSend() {
  const text = userInput.value.trim();
  if (!text) return;

  userInput.value = '';
  autoResize();
  sendBtn.disabled = true;

  // Show user message
  addMessage('user', text);
  appendMessage({ role:'user', text,
    time: new Date().toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'}) });
  scrollToBottom();

  if (isSleeping()) {
    appendSystemMsg(`💤 ${getSettings().aiName} is sleeping. She'll see this in the morning.`);
    sendBtn.disabled = false;
    return;
  }

  // Update emotions
  triggerEmotion('user_replied');
  renderEmotions();

  // Try to extract user fact (non-blocking)
  extractUserFact(text).then(fact => {
    if (fact) {
      const mem = getMemory();
      if (!mem.userFacts.includes(fact)) {
        mem.userFacts.push(fact);
        if (mem.userFacts.length > 20) mem.userFacts.splice(0, mem.userFacts.length-20);
        saveMemory(mem);
      }
    }
  });

  // Generate reply
  showTyping();
  try {
    const replyText = await reply(
      text,
      buildWorldContext(),
      buildMemoryContext(),
      getConversationHistory(14),
    );
    hideTyping();
    const hint = moodSummary(getEmotions());
    addMessage('aria', replyText, hint);
    appendMessage({ role:'aria', text: replyText, emotionHint: hint,
      time: new Date().toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'}) });
    scrollToBottom();
  } catch(err) {
    hideTyping();
    console.error('reply error:', err);
    appendSystemMsg(`(something went wrong: ${err.message})`);
  }

  sendBtn.disabled = false;
}

// ── End of day journal ──────────────────────────────────────────────────────
async function doEndOfDay() {
  const world  = getWorld();
  const events = world.todaysEvents.map(e => e.text).join('; ') || 'A quiet day.';
  const mood   = moodSummary(getEmotions());
  try {
    const summary = await writeJournal(buildWorldContext(), events, mood);
    const mem = getMemory();
    mem.journal.push({
      date: new Date().toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'}),
      summary,
      mood,
      highlight: world.todaysEvents.at(-1)?.text ?? 'just existing',
    });
    if (mem.journal.length > 14) mem.journal.splice(0, mem.journal.length-14);
    mem.dayCount++;
    saveMemory(mem);

    // Reset today
    world.todaysEvents = [];
    world.mealsToday   = [];
    world.coffeesToday = 0;
    world.dayCount     = (world.dayCount ?? 0) + 1;
    saveWorld(world);

    decayEmotions();
    decayEmotions();
    renderJournal();
    renderEmotions();
  } catch(err) {
    console.error('journal error:', err);
  }
}

// ── World helpers ───────────────────────────────────────────────────────────
function updateWorld(room, activity, meal) {
  const w = getWorld();
  w.currentRoom     = room;
  w.currentActivity = activity;
  if (meal) w.mealsToday.push(meal);
  if (activity === 'making espresso' || activity === 'making coffee') w.coffeesToday++;
  saveWorld(w);
  renderWorld();
}

function logEvent(text) {
  const w = getWorld();
  w.todaysEvents.push({ time: friendlyTime(), text });
  if (w.todaysEvents.length > 20) w.todaysEvents.splice(0, w.todaysEvents.length-20);
  saveWorld(w);
  renderLog();
}

function buildWorldContext() {
  const w   = getWorld();
  const now = new Date();
  const tod = getTimeOfDay(now.getHours());
  const meals = w.mealsToday.length ? w.mealsToday.join(', ') : "hasn't eaten yet";
  return (
    `It is ${now.toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'})} ` +
    `(${tod}). ` +
    `Aria is in her ${w.currentRoom.replace('_',' ')}, currently ${w.currentActivity}. ` +
    `She's had ${w.coffeesToday} coffee(s) today. ` +
    `Meals today: ${meals}. Pixel the cat is nearby.`
  );
}

function buildMemoryContext() {
  const mem = getMemory();
  const lines = [];
  if (mem.journal.length) {
    const last = mem.journal.at(-1);
    lines.push(`Yesterday (${last.date}): ${last.summary} You felt ${last.mood}.`);
  }
  if (mem.userFacts.length) {
    lines.push(`Things you know about ${getSettings().userName}: ${mem.userFacts.slice(-5).join('; ')}`);
  }
  if (mem.dayCount > 0) lines.push(`You've been keeping this journal for ${mem.dayCount} day(s).`);
  return lines.join('\n') || 'This is your first day. Everything is new.';
}

function getTimeOfDay(h) {
  if (h < 6)  return 'deep night';
  if (h < 8)  return 'early morning';
  if (h < 12) return 'morning';
  if (h < 14) return 'midday';
  if (h < 18) return 'afternoon';
  if (h < 21) return 'evening';
  return 'night';
}

// ── Rendering ───────────────────────────────────────────────────────────────
function renderAllMessages() {
  messagesDiv.querySelectorAll('.msg, .sys-msg').forEach(el => el.remove());
  getMessages().forEach(appendMessage);
  scrollToBottom();
}

function appendMessage(msg) {
  const el = document.createElement('div');
  el.className = `msg ${msg.role}`;

  if (msg.role === 'aria' && msg.emotionHint) {
    const badge = document.createElement('div');
    badge.className = 'msg-emotion';
    badge.textContent = msg.emotionHint;
    el.appendChild(badge);
  }

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.textContent = msg.text;
  el.appendChild(bubble);

  const time = document.createElement('div');
  time.className = 'msg-time';
  time.textContent = msg.time;
  el.appendChild(time);

  messagesDiv.appendChild(el);
}

function appendSystemMsg(text) {
  const el = document.createElement('div');
  el.className = 'sys-msg';
  el.style.cssText = 'text-align:center;font-size:.75rem;color:var(--text-faint);padding:.3rem 0;';
  el.textContent = text;
  messagesDiv.appendChild(el);
  scrollToBottom();
}

function renderEmotions() {
  const emotions = getEmotions();
  const dom = dominant(emotions);
  const emoji = EMOTION_DEFS[dom]?.emoji ?? '🌸';
  dominantEmojiEl.textContent = emoji;
  dominantLabel.textContent = dom;

  // Bars
  emotionBarsDiv.innerHTML = '';
  const sorted = Object.entries(emotions).sort((a,b) => b[1]-a[1]);
  for (const [key, val] of sorted) {
    const pct  = Math.round(val * 100);
    const def  = EMOTION_DEFS[key];
    const row  = document.createElement('div');
    row.className = 'emotion-row';
    row.innerHTML = `
      <div class="emotion-name">${key}</div>
      <div class="emotion-bar-wrap">
        <div class="emotion-bar ${key}" style="width:${pct}%"></div>
      </div>
      <div class="emotion-pct">${pct}%</div>
    `;
    emotionBarsDiv.appendChild(row);
  }

  // Mini bars
  const pos = positivity(emotions);
  happinessBar.style.width = `${Math.round(pos*100)}%`;
  energyBar.style.width    = `${Math.round(emotions.energized*100)}%`;

  // Mood text
  stateMood.textContent = moodSummary(emotions);
}

function renderWorld() {
  const w = getWorld();

  // Highlight active room
  document.querySelectorAll('.room').forEach(el => {
    el.classList.remove('active');
    el.querySelector('.room-activity').textContent = '';
    el.querySelector('.room-presence').hidden = true;
  });

  const activeEl = document.getElementById(`room-${w.currentRoom}`);
  if (activeEl) {
    activeEl.classList.add('active');
    activeEl.querySelector('.room-activity').textContent = w.currentActivity;
    activeEl.querySelector('.room-presence').hidden = false;
  }

  // State card
  stateActivity.textContent = w.currentActivity || '—';
  stateCoffee.textContent   = `☕ ${w.coffeesToday}`;
  stateMeals.textContent    = w.mealsToday.length
    ? w.mealsToday.slice(-2).join(', ')
    : '—';

  // Move Pixel randomly to a room
  movePixel(w.catLocation || 'bedroom');
  renderLog();
}

function movePixel(roomKey) {
  const el = document.getElementById(`room-${roomKey}`);
  if (!el) return;
  const rect = el.getBoundingClientRect();
  const fp   = document.getElementById('floor-plan').getBoundingClientRect();
  pixelBadge.style.left = `${rect.left - fp.left + 4}px`;
  pixelBadge.style.top  = `${rect.top  - fp.top  + 4}px`;
}

function renderLog() {
  const w = getWorld();
  logList.innerHTML = '';
  if (!w.todaysEvents.length) {
    logList.innerHTML = '<li class="log-empty">Nothing yet today…</li>';
    return;
  }
  w.todaysEvents.slice(-8).reverse().forEach(ev => {
    const li = document.createElement('li');
    li.innerHTML = `<span class="log-time">${ev.time}</span>${ev.text}`;
    logList.appendChild(li);
  });
}

function renderJournal() {
  const mem = getMemory();
  journalDiv.innerHTML = '';
  if (!mem.journal.length) {
    journalDiv.innerHTML = '<p class="journal-empty">No entries yet. She writes at bedtime.</p>';
    return;
  }
  mem.journal.slice().reverse().forEach(entry => {
    const el = document.createElement('div');
    el.className = 'journal-entry fade-in';
    el.innerHTML = `
      <div class="journal-date">${entry.date}</div>
      <div class="journal-text">${entry.summary}</div>
      <div class="journal-mood">felt: ${entry.mood}</div>
    `;
    journalDiv.appendChild(el);
  });
}

// ── Typing indicator ───────────────────────────────────────────────────────
function showTyping() {
  typingInd.hidden = false;
  sendBtn.disabled = true;
}
function hideTyping() {
  typingInd.hidden = true;
  sendBtn.disabled = false;
}

function scrollToBottom() {
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// ── Settings ────────────────────────────────────────────────────────────────
function bindSettings() {
  settingsBtn.addEventListener('click', () => {
    const s = getSettings();
    settingsKey.value      = s.apiKey;
    settingsUsername.value = s.userName;
    settingsAiname.value   = s.aiName;
    settingsModal.hidden   = false;
  });
  settingsClose.addEventListener('click', () => { settingsModal.hidden = true; });
  settingsModal.addEventListener('click', e => { if (e.target === settingsModal) settingsModal.hidden = true; });
  settingsSave.addEventListener('click', () => {
    const key  = settingsKey.value.trim();
    const user = settingsUsername.value.trim() || 'Friend';
    const ai   = settingsAiname.value.trim()   || 'Aria';
    if (!key) { settingsKey.focus(); return; }
    saveSettings({ apiKey: key, userName: user, aiName: ai });
    chatName.textContent   = ai;
    chatAvatar.textContent = ai.charAt(0).toUpperCase();
    sleepingName.textContent = ai;
    settingsModal.hidden   = true;
  });
  resetBtn.addEventListener('click', () => {
    if (confirm('Reset all of Aria\'s memories, emotions, and logs? This cannot be undone.')) {
      const key  = settingsKey.value.trim();
      const user = settingsUsername.value.trim() || 'Friend';
      const ai   = settingsAiname.value.trim()   || 'Aria';
      resetAll();
      saveSettings({ apiKey: key, userName: user, aiName: ai });
      settingsModal.hidden = true;
      renderAllMessages();
      renderEmotions();
      renderWorld();
      renderJournal();
    }
  });
}

// ── Chat input ──────────────────────────────────────────────────────────────
function bindChat() {
  sendBtn.addEventListener('click', handleUserSend);
  userInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleUserSend();
    }
  });
  userInput.addEventListener('input', autoResize);
}

function autoResize() {
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
}

// ── Random cat movement every 5 minutes ────────────────────────────────────
setInterval(() => {
  const rooms  = Object.keys(ROOMS);
  const newLoc = pick(rooms);
  const w      = getWorld();
  w.catLocation = newLoc;
  saveWorld(w);
  movePixel(newLoc);
}, 5 * 60 * 1000);

// ── Kick it off ────────────────────────────────────────────────────────────
try {
  boot();
} catch (err) {
  document.body.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:center;
                height:100vh;background:#0b0b14;color:#e2e8f0;
                font-family:system-ui;flex-direction:column;gap:1rem;padding:2rem;text-align:center;">
      <div style="font-size:2rem;">⚠</div>
      <div style="font-size:1.1rem;font-weight:600;">Something went wrong loading SentAI</div>
      <div style="color:#94a3b8;font-size:.85rem;max-width:400px;">${err.message}</div>
      <div style="color:#475569;font-size:.75rem;">Open the browser console (F12) for details.</div>
    </div>`;
  console.error('SentAI boot error:', err);
}
