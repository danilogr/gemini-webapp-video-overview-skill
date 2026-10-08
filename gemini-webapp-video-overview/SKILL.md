---
name: gemini-webapp-video-overview
description: Make short narrated videos of a real web app being used — product overviews, feature how-tos, "what's new" clips, onboarding walkthroughs — recorded from the live app with Playwright, voiced with Gemini TTS (OpenAI as fallback), with a visible pointer that glides to every click, highlight rings, WebVTT captions, poster frames and a videos.json manifest. Audio is the master clock, so the pointer lands on the words. Use this whenever someone wants a demo video, screencast, tutorial clip, explainer, walkthrough or help video of a website or web app, wants to turn a feature into a short video, wants videos for a help page or changelog, or wants to re-record existing app videos after a UI change — even if they never say "Playwright" or "TTS".
---

# Narrated videos of a web app

This skill turns a short script into an mp4 of the real app being used: a calm
voice explains, a drawn pointer glides to each control a beat before it is
clicked, rings highlight what the voice names, and captions match the audio to
the hundredth of a second. Everything on screen is the real app doing real
work, so if the app breaks, the video breaks — which is the property you want
in a video somebody will show a customer.

Everything lives in `scripts/`. You write one `narration.json` per video; the
scripts do the rest.

## The one idea that makes it work: audio is the master clock

Write the visuals first and the spoken lines always run longer than their
slots: the pointer drifts off the words by the third line, and every fix moves
everything after it. So the dependency is inverted:

1. **Voice** (`tts_gemini.py` / `tts_openai.py`) — each line becomes a WAV.
2. **Time** (`retime.py`) — measures every WAV and writes each line's real
   `start` and `end` into `narration.json`, plus captions.
3. **Record** (`record.cjs`) — runs every action at a time written *relative
   to a line*: `"at": "L4.start+0.6"`. Nothing carries a hand-typed
   timestamp, so changing a word re-times everything.
4. **Encode and mix** (`build.sh`, `mux.py`) — trims the page-load time off the
   front, places each WAV at its start, muxes.

Never edit a `start`, `end` or `total_seconds` by hand. Change the words and
rebuild.

## Requirements

- `python3`, `node`, `ffmpeg`/`ffprobe`, and Playwright with Chromium
  (`npm i -g playwright && npx playwright install chromium`, then
  `NODE_PATH=$(npm root -g)`). `build.sh` also looks in the npx cache.
- A voice key in the environment, never in a file:
  - **Gemini (default):** `GEMINI_API_KEY` — an `AIza…` or an `AQ.…` key from
    Google AI Studio. Both work (the key goes in the `x-goog-api-key` header).
  - **OpenAI (fallback):** `OPENAI_API_KEY`. Used when no Gemini key is set, or
    with `TTS_ENGINE=openai`.
- If the user keeps keys in a `.env`, load only the one variable into the
  command's environment, without its quotes:
  `GEMINI_API_KEY="$(grep -E '^GEMINI_API_KEY=' path/.env | head -1 | cut -d= -f2- | tr -d "\"'")" scripts/build.sh …`.
  Never echo it, never write it into the project, never commit it.
- Playwright: `build.sh` uses whatever `node` can import, else `NODE_PATH`,
  else a copy in the npx cache, and prints which version it chose. That
  version's Chromium must be installed (`npx playwright@<version> install
  chromium`).

## Workflow

### 1. Learn the app before writing a word

Open it (or read its source) and find what each video needs:

- **Stable selectors** for every control you will click or ring: ids,
  `data-*` attributes, `aria-label`s, roles. Avoid positional CSS that breaks
  when a list grows. Check each one exists at the recording size.
- **A ready selector**: something that exists only once the app has rendered
  what the video needs (`"ready"` in narration.json). Starting on a spinner
  wastes the first line.
- **Demo data**: a sample, a demo account, a seeded state. Never record real
  customer data, and never let a recording create real side effects (orders,
  emails, payments) — use a demo or staging environment if the app writes.
- **Does the data show what the script will claim?** If the script says "the
  overdue invoice turns red", the demo data must have an overdue invoice. A video
  that narrates something not on screen is worse than no video.

### 2. Plan the videos

One idea per video, 15–40 seconds, 4–7 lines. A set usually looks like: a
whole-job walkthrough (60–90 s), then one short video per key feature, then a
"what's new" clip per release. Read `references/writing-narration.md` for how
to write lines that time well (short sentences, the noun the viewer should
look at said early, one action per line).

### 3. Write narration.json

One folder per video, named by its slug: `videos/<slug>/narration.json`.
Start from `assets/example/todo-basics/narration.json` — a complete, working
example against a public demo app. The full schema and every action are in
`references/narration-format.md`. The shape:

```json
{
  "slug": "add-a-task",
  "title": "Add a task and mark it done",
  "url": "https://app.example.com/?demo=1",
  "ready": "#task-list",
  "voice": "Charon",
  "style": "Read this in a calm, friendly and unhurried voice",
  "state": {"tasks": "#task-list li", "left": "#count"},
  "setup": [["click", "#dismiss-banner"]],
  "lines": [
    {"id": 1, "text": "Type the task in the box at the top, and press Enter."}
  ],
  "actions": [
    {"at": "L1.start+0.3", "do": ["type", "#new-task", "Buy milk", {"commit": "Enter"}]}
  ]
}
```

Timing rules of thumb, learned the hard way:

- Start an action **0.3–0.8 s after its line starts**, so the pointer arrives
  as the noun is spoken. A glide takes ~0.7 s; a click lands right after it.
- Leave **≥ 1.2 s between actions**; typing needs ~0.8 s plus 55 ms per
  character. The recorder warns when an action starts late.
- Use `ring` for anything the voice names but nobody clicks (a total, a
  status line, a new button). A ring with no pointer reads as "look here".
- Put the state a short video needs (logged in, a list with items, a panel
  open) in `setup`: it runs at full speed before the clock and is cut off.
- After a click that loads another page (a login, a submit, a link), add a
  `waitFor` for something on the new page at the same moment — `ready` only
  covers the first page. The pointer stays where the click left it.
- If page loads hang, see "Loading" in `references/pitfalls.md`
  (`launch_args`, `block`, `wait_until`).
- Add a `snap` at key moments and list what to read in `state`; the values
  land in `rec/final-state.json` so a take can be checked without watching.

### 4. Build

```bash
scripts/build.sh videos/<slug>                 # one video → videos/<slug>/video.mp4
scripts/build_all.sh videos public/videos      # all, plus captions, posters, videos.json
```

The mode flag comes first, before the folders: `build_all.sh --no-tts videos
public/videos`. `--no-tts` reuses the audio as it is (no key needed — use it
when only actions changed). The default only voices lines whose words or voice changed. `--tts`
re-voices everything. A voice or engine change re-voices every line, so one
video never has two voices.

### 5. Check every take — look at the frames

The logs cannot tell you a ring landed on the wrong element or the pointer
clicked while the page was loading. Run:

```bash
python3 scripts/inspect.py videos/<slug>
```

It finds the video wherever the last build wrote it (pass a path as a second
argument to check another file). It writes one frame a beat after every
action into `videos/<slug>/frames/`,
prints which line is being spoken at that instant, the volume, and the
snapshot state. **Open the frames and look.** For each one ask: is the pointer
on the thing the line names, at the moment it names it, and does the screen
show what the words claim? Fix and rebuild (usually `--no-tts`). Speech sits
around −16 to −26 dB mean; much lower means a silent or broken mix.

### 6. Publish and serve

`build_all.sh` writes `<slug>.mp4`, `.vtt`, `.jpg` and `videos.json` into the
output folder, ready to serve as static files. Before shipping them on a site,
read `references/serving.md` — notably, **Safari plays no mp4 unless the server
answers Range requests with 206**, and many static hosts and edge asset layers
do not.

## Known traps

`references/pitfalls.md` lists every failure this pipeline has hit and its fix:
invisible native popups and file dialogs, tooltips that never render headless,
the pointer hidden behind modal dialogs, fields that append instead of
replacing, the page-load offset, OpenAI's streamed WAV header, layout that
differs at the recording size, and more. Read it before the first build on a
new app, and whenever a take looks wrong.

## Files

| Path | What |
|---|---|
| `scripts/build.sh` | One video, end to end |
| `scripts/build_all.sh` | Many videos into one folder, with `videos.json` |
| `scripts/tts_gemini.py`, `scripts/tts_openai.py` | Voice, one WAV per line |
| `scripts/retime.py` | Times the script to the audio; writes captions |
| `scripts/record.cjs` | Drives the app on the clock; records the webm |
| `scripts/cursor.js` | The drawn pointer, click ripple and rings |
| `scripts/mux.py` | Places the voice on the timeline |
| `scripts/publish.py` | Captions, poster and the manifest |
| `scripts/inspect.py` | Frames per action, volume, state — for checking a take |
| `references/narration-format.md` | Every narration.json field and action |
| `references/writing-narration.md` | Writing lines that time and sound right |
| `references/voices.md` | Gemini and OpenAI voices, style direction |
| `references/pitfalls.md` | What goes wrong and the fix |
| `references/serving.md` | Putting the videos on a site: player, captions, Range, "what's new" |
| `assets/example/todo-basics/` | A complete working example |
