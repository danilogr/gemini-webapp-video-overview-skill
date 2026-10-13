# Pitfalls, and the fix for each

Every one of these happened in a real build.

## Sync

**The pointer drifts off the words.** The visuals were timed first. Fix: never
hand-time; every action is `L<id>.start±s` and retime.py writes the real
times from the audio.

**Every action is ~2 s late.** The webm starts when the page opens, but the
clock starts after the page loads and setup runs. Fix (built in): record.cjs
writes the clock's start to `rec/offset.txt`; build.sh cuts everything
before it with `-ss`.

**An action starts late and the next one piles up.** Actions too close
together. The recorder prints `! N action(s) started more than 0.25 s late`.
Space them ≥ 1.2 s, or add `"pause"` to the next line.

## Things a headless recording never shows

**Native `<select>` popups.** Drawn by the OS, not the page: a click opens
nothing visible. Use the `select` action (pointer + ripple + value set), and
narrate the choice ("choose Weekly from the menu").

**File dialogs.** Same. Use `upload`, which hands the file over directly.

**Tooltips (`title` attributes).** Never rendered headless. If the script says
"the button tells you what it will undo", show that text somewhere visible —
a status line, a label — or say it instead of showing it.

**The OS cursor.** There is none; cursor.js draws one. It lives in the top
layer (a popover) so a modal `<dialog>` cannot cover it — in an ordinary
`z-index` layer the pointer went *behind* the confirm dialog.

**The pointer vanished after a page load.** Every load makes a new document
and a new pointer at (-100, -100); after a login it was gone, then flew in
from the top-left corner. Fix (built in): cursor.js keeps its position in
sessionStorage, and record.cjs puts it back after every load.

## Loading

**Every page load times out, though curl is fast.** Chromium's HTTP/2 stalled
on one network. Fix: `"launch_args": ["--disable-http2"]`.

**`load` never comes, or comes late.** A third-party script (a tracker, an A/B
tool, a chat widget) holds it up. Fix: `"block"` its URLs, or
`"wait_until": "domcontentloaded"` with a `ready` selector.

**The next action runs before the new page has rendered.** `ready` covers only
the first page and `goto`. After a click that loads a page, add a `waitFor`
for something on the new page at the same moment, and give the next line a
`"pause"` if the load is slow.

## Input

**Typing appends.** The field already held a value ("Untitled" + "Groceries" =
"UntitledGroceries"). Fix (built in): `type` selects all first; pass
`{"clear": false}` to append on purpose.

**Typing looks instant.** `fill()` sets the value at once and does not read as
typing. `type` presses each key with a 55 ms delay.

**A typed value is not saved.** Many apps commit on `change`/blur. `type`
presses Tab after typing; use `{"commit": "Enter"}` for forms that submit on
Enter.

## Layout and data

**Something is cut off at the recording size.** The app's default layout at
1280×800 hid the third item of a row, or truncated a total in a header.
Look at the frames; adjust the layout in `setup` (resize a pane, collapse a
sidebar, set a zoom) or change `size`.

**The script claims something the data cannot show.** "The overdue invoice turns
red…" over demo data with no overdue invoice. Fix the demo data, or the words.

**Toasts from setup are still on screen at second 0.** `setup_settle_ms`
(2000) waits for them; raise it if the app's toasts last longer.

**The app counts the recording as a user.** Analytics and usage tracking
should ignore automation (`navigator.webdriver`, a HeadlessChrome user agent);
check before recording against production, and `"block"` third-party
trackers you cannot change.

**Real data in a video.** Use demo data and invented names. A published video
cannot be taken back.

## Audio

**OpenAI WAVs report ~4 GB of frames.** The response is streamed, so the RIFF
header carries a placeholder size; Python's `wave` believes it and retime.py
computes a day-long video. Fix (built in): tts_openai.py rewrites each file
through ffmpeg.

**The voice is half as loud as it should be.** `amix` normalises by the
number of inputs. Fix (built in): `normalize=0` — the lines never overlap.

**Two voices in one video.** Some lines re-voiced after the engine or voice
changed. Fix (built in): each WAV records its `_voice`; any change re-voices
every line.

**The video plays, but with no voice, on one device.** The file has sound
(inspect.py measures it) but a player drops it. TTS voices are 24 kHz mono,
and not every player, phone or in-app viewer plays that reliably. Fix (built
in): mux.py writes 48 kHz stereo AAC, the format every player expects. If a
viewer is still silent, check it did not start muted — many do.

**Gemini 429 / 500.** Rate limits and occasional empty responses on the
preview models. Fix (built in): backoff and retry.

**A typing frame shows a half-filled field.** inspect.py waits for the whole
text (≈1 s + 55 ms per character); if a frame is still partial, the next
action came too soon after the `type`.

## Encoding

**The video will not start until fully downloaded.** The `moov` atom is at the
end. Fix (built in): `-movflags +faststart`.

**Files too large.** CRF 23 with `-preset slow` gives ~1–2 MB per 30 s at
1280×800 for typical UI (mostly static). Raise CRF to 26–28 for smaller files;
the UI text stays legible up to ~28.
