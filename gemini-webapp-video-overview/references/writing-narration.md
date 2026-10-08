# Writing the narration

The script is most of the quality of these videos. A viewer is watching the
pointer and listening at the same time; the words have to tell them where to
look *just before* the pointer gets there.

## Lines

- **One idea per line, 6–20 words.** A line is one beat of the video: one
  action, or one thing to notice. Long lines leave the screen still while the
  voice keeps going.
- **Say the noun early.** "Click a project's name. Only its tasks stay…" — the
  thing to look at comes first, so the action can start 0.3–0.8 s into the
  line and the pointer arrives as the word is heard.
- **Describe what is on screen, not what the product aspires to.** Every claim
  must be visible in that moment. If the demo data cannot show it, change the
  data or cut the claim.
- **Name controls by what is printed on them**, in the same case: "Export
  CSV", not "the download button". People look for the words they hear.
- **Plain, calm, never salesy.** No "simply", "just", "powerful",
  "seamlessly". The tone of a colleague showing a colleague.
- **Numbers as they should be spoken**, if the engine stumbles: "twelve
  hundred and fifty dollars" reads better than "$1,250.00".
- **End on the result**, not on a click: the last line says what you now have.

## Shape of a video

| Video | Lines | Length | Shape |
|---|---|---|---|
| Feature how-to | 4–7 | 20–40 s | what it is for → do it → what you see → one variation → how to undo or leave |
| What's new | 5–7 | 25–40 s | "New: …" → each feature in one or two lines → where to find it |
| Walkthrough | 8–12 | 60–90 s | the job from start to finish, one line per step, the result at the end |

Set the state a short video needs in `setup` rather than narrating it. A
feature video that spends ten seconds creating data loses the viewer.

## Timing actions to lines

- Click or type **0.3–0.8 s after the line starts**. Ring something **while
  it is being named** or just after.
- Keep **≥ 1.2 s between actions**. Typing takes ~0.8 s plus 55 ms per
  character; a click ~0.8 s including the glide.
- When the voice must wait for the app (a page load, a dialog), give the next
  line a `"pause"` instead of squeezing.
- After building, `inspect.py` prints the line being spoken at each action —
  read it next to the frames.

## Revising

Change a word → rebuild with the default mode: only that line is re-voiced,
everything re-times. Change only actions → `--no-tts`. Change the voice or
style → every line is re-voiced automatically.
