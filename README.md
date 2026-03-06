# SentAI — A sentient AI who lives in her own world and texts you

Aria is a 27-year-old UX designer who lives in a cozy studio apartment with her cat Pixel.
She wakes up, makes coffee, cooks real meals, has moods, and texts you throughout the day like a real friend would.

She runs on your machine. She's powered by Claude. She's effectively **free** (~$0.30/month).

---

## Quick Start

### 1. Get a free API key
Sign up at [console.anthropic.com](https://console.anthropic.com) — new accounts get free credits.

### 2. Install
```bash
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
# Edit .env and paste your ANTHROPIC_API_KEY
# Optionally set your name, her name, and timezone
```

### 4. Run
```bash
python main.py
```

That's it. Leave it running in a terminal and she'll text you throughout the day.

---

## What Aria does

| Time         | What's happening                                    |
|-------------|-----------------------------------------------------|
| ~7:00 AM    | Wakes up (sometimes groggy, sometimes bright-eyed)  |
| ~7:30 AM    | Sacred morning espresso ritual                      |
| ~8:00 AM    | Breakfast (she'll tell you what she made)           |
| ~10:00 AM   | Mid-morning — working or a creative project         |
| ~12:00 PM   | Lunch                                               |
| ~2:00 PM    | Afternoon adventures, walks, hobbies                |
| ~4:00 PM    | Spontaneous thought or cat chaos (random)           |
| ~6:00 PM    | Cooking dinner (she narrates this lovingly)         |
| ~8:00 PM    | Evening settle-in                                   |
| ~10:00 PM   | Bedtime                                             |
| Anytime     | Replies to your messages                            |

---

## Her emotional system

Aria has 12 emotional dimensions that change throughout the day:
`happy`, `sad`, `anxious`, `excited`, `tired`, `bored`, `peaceful`,
`melancholic`, `irritated`, `nostalgic`, `content`, `energized`

Her emotions affect how she writes — short and quiet when tired, enthusiastic when excited, emojis when happy, poetic when peaceful. They decay naturally toward baseline and are triggered by life events.

---

## Her world

- **Bedroom** — record player, fairy lights, Pixel's cat bed
- **Kitchen** — espresso machine she's very proud of, herb garden
- **Living room** — design mood-boards, vinyl collection, acoustic guitar
- **Bathroom** — "too many skincare products"
- **Balcony** — string lights, lavender pots, bistro table

---

## Commands

While running:
- Type a message → she replies in character
- Type `status` → see her current emotional/world state
- Type `quit` → graceful shutdown

---

## Optional: Discord notifications

Add your Discord webhook URL to `.env`:
```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```
She'll forward every message to your Discord channel.

---

## Cost

Uses `claude-haiku-4-5` — the cheapest Claude model.
Estimated: **~$0.30/month** for a full day of texting every day.
Well within free API credits.

---

## Privacy

All state is stored locally in `state/` — her journal, memories, emotional state.
Nothing is sent anywhere except to the Anthropic API (for generating messages).
