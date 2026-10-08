# narration.json

One file per video, in the video's own folder. The scripts write some fields
back into it (marked *written*) — never edit those by hand.

## Top-level fields

| Field | Default | Meaning |
|---|---|---|
| `slug` | folder name | Identifier; the output files are `<slug>.mp4/.vtt/.jpg`. |
| `title` | slug | Shown in `videos.json`. Short, names the outcome ("Add a task and mark it done"). Avoid numbers that go stale ("in 90 seconds"). |
| `url` | — | Page the recording starts on. Relative `goto` URLs resolve against it. |
| `ready` | none | Selector to wait for after every page load. Pick one that exists only when the app has rendered what the video needs. |
| `ready_timeout_ms` | 60000 | How long to wait for `ready` (and the default for `waitFor`). |
| `goto_timeout_ms` | 60000 | How long a page load may take. |
| `wait_until` | `"load"` | When a page counts as loaded: `"load"`, `"domcontentloaded"` or `"networkidle"`. Use `"domcontentloaded"` when a slow third-party script holds up `load`. |
| `launch_args` | none | Chromium flags, e.g. `["--disable-http2"]` when every load times out on a network that stalls HTTP/2. |
| `block` | none | URL globs to refuse, e.g. `["**/*optimizely*", "**/*hotjar*"]`: trackers that would count the recording, chat widgets that pop up mid-take. |
| `settle_ms` | 800 | Extra wait after `ready`, for fonts, images and animations. |
| `size` | `[1280, 800]` | Viewport and video size. 1280×800 reads well embedded at ~1280 px wide; check the layout at that size. |
| `color_scheme` | `"light"` | `"dark"` to record the dark theme. |
| `engine` | auto | `"gemini"` or `"openai"`. Auto: Gemini if a Gemini key is set, else OpenAI. `TTS_ENGINE` overrides. |
| `voice` | `"Charon"` | Gemini voice (see voices.md). |
| `model` | `"gemini-2.5-flash-preview-tts"` | Gemini TTS model. |
| `style` | none | Delivery direction, sent to Gemini as `"<style>: <line>"` (not spoken) and used by OpenAI when `instructions` is absent. |
| `voice_openai`, `model_openai`, `instructions` | `onyx`, `gpt-4o-mini-tts`, style | OpenAI equivalents. |
| `lead`, `gap`, `tail` | 0.5, 0.45, 1.4 | Seconds of silence before the first line, between lines, after the last. |
| `accent`, `outline` | `#2563EB`, `#111827` | Ring/ripple colour and pointer outline. Match the app's brand. |
| `cursor_start` | 20%, 60% of the screen | Where the pointer rests when the clock starts. |
| `glide_ms` | 620 | Pointer travel time per move. |
| `type_delay_ms` | 55 | Per character when typing. |
| `setup_settle_ms` | 2000 | Pause after setup so its toasts fade before the clock. |
| `poster` | middle | Time of the poster frame, written like an `at`: `"L3.start+1.5"`. Choose a frame that shows the feature. |
| `state` | none | `{name: selector}` read at every `snap` and at the end into `rec/final-state.json`. A field gives its value; anything else its text; several matches give a list. |
| `setup` | none | Actions run at full speed before the clock; cut from the video. |
| `lines` | — | The script; see below. |
| `actions` | — | The timeline; see below. |
| `total_seconds` | *written* | Video length, from retime.py. |

## lines

```json
{"id": 3, "text": "Click a date to see every task due that day.", "pause": 0.8}
```

- `id` — integer, unique, used in times (`L3.start`) and file names
  (`audio/line_03.wav`). Keep ids stable when you insert a line; ids do not
  need to be consecutive, but lines play in array order.
- `text` — what is spoken, and the caption.
- `pause` — optional extra seconds of silence before this line, to let a slow
  action (a page load, a dialog) finish before the voice moves on.
- *written*: `start`, `end`, `_dur` (retime.py), `_spoken`, `_voice` (the TTS
  scripts, to know when a line must be re-voiced).

## actions

```json
{"at": "L4.start+0.6", "do": ["click", "#save"]}
```

`at` is `"L<id>.start"` or `"L<id>.end"`, optionally `+`/`-` seconds, or a
plain number of seconds (`3.5` or `"3.5"`). `do` is `[action, …arguments]`. The same vocabulary
works in `setup` (written as bare arrays, run at full speed).

| Action | Arguments | What it does |
|---|---|---|
| `click` | selector | Pointer glides there, ripple, real click. |
| `dblclick` | selector | Same, double click. |
| `cursor` | selector | Pointer glides there; no click. Use to point while talking. |
| `hover` | selector | Glide and a real hover (menus that open on hover). |
| `type` | selector, text, options? | Glide, click, select all, type per character, then Tab. Options: `{"commit": "Enter"}` to press Enter instead, `{"commit": false}` to press nothing, `{"clear": false}` to append. |
| `press` | key | A key press, e.g. `"Escape"`, `"ControlOrMeta+z"`, `"ArrowDown"`. |
| `focus` | selector | Focus without moving the pointer (for keyboard demos). |
| `select` | selector, value | Native `<select>`: pointer goes to it, ripple, value set. The OS popup never appears in a recording; this is the honest substitute. |
| `ring` | selector, ms? | Highlight ring around the element for ms (1600). |
| `scroll` | selector, dy | Wheel-scroll at the element by dy pixels. |
| `scrollTo` | selector, `"top"`/`"bottom"`/px | Smooth-scroll a scrollable element. |
| `reveal` | selector | Scroll its container so it is at the top. |
| `download` | selector, name? | Click and keep the download in `rec/` under name. |
| `upload` | selector, name-or-path | Give a file input a file: a `download` name, or a path relative to the video folder. |
| `goto` | url | Load a page (relative to `url`), then wait for `ready`. |
| `waitFor` | selector, ms? | Wait until it exists. Put it right after a click that loads another page (a login, a submit, a link): `ready` only covers the first page and `goto`. |
| `wait` | ms | Do nothing (mostly for setup). |
| `snap` | label | Read `state` into `rec/final-state.json` under label. |

The drawn pointer keeps its place across page loads: after a login or a link,
it is where the click left it, not gone.

An action that fails (element missing) is logged with `!` and the take
continues; look at the frames to decide whether the take is usable.
