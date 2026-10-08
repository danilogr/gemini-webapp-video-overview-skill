# gemini-webapp-video-overview

A Claude skill that makes short narrated videos of a real web app being used:
product overviews, feature how-tos, "what's new" clips and walkthroughs.

- **Recorded from the live app** with Playwright, with every click a real click.
- **A visible pointer** glides to each control before it is clicked, with a
  click ripple and highlight rings, drawn above modal dialogs too.
- **The audio is the master clock.** Each line is voiced first and measured,
  then every action is scheduled against the real timing (`"L4.start+0.6"`),
  so the pointer lands on the words.
- **Gemini TTS** by default (30 voices, a style direction that is not read
  aloud). **OpenAI TTS** as the fallback.
- **WebVTT captions, poster frames and a `videos.json` manifest**, ready to
  serve on a help page.
- **A checking step**: one frame per action, the spoken line at that moment,
  the volume, and the app's state.

## Install

```bash
git clone git@github.com:danilogr/gemini-webapp-video-overview-skill.git
ln -s "$PWD/gemini-webapp-video-overview-skill/gemini-webapp-video-overview" \
      ~/.claude/skills/gemini-webapp-video-overview
```

Claude Code then uses the skill when you ask for a demo or how-to video of a
web app. You can also run the scripts directly.

## Requirements

- `python3`, `node`, `ffmpeg`
- Playwright with Chromium: `npm i -g playwright && npx playwright install chromium`
- A voice key in the environment: `GEMINI_API_KEY` (an `AIza…` or `AQ.…` key
  from https://aistudio.google.com/apikey), or `OPENAI_API_KEY`

## Try it

```bash
S=gemini-webapp-video-overview
cp -r $S/assets/example/todo-basics /tmp/
GEMINI_API_KEY=… $S/scripts/build.sh /tmp/todo-basics     # → /tmp/todo-basics/video.mp4
python3 $S/scripts/inspect.py /tmp/todo-basics              # frames to check
```

The example records the public TodoMVC demo at
https://demo.playwright.dev/todomvc/ — about 26 seconds, ~500 KB.

## Layout

```
gemini-webapp-video-overview/
  SKILL.md              the workflow Claude follows
  scripts/              build, voice, timing, recording, mixing, publishing, inspection
  references/           narration format, writing, voices, pitfalls, serving
  assets/example/       a complete working example
```

Start with `SKILL.md`, then `references/narration-format.md`.
