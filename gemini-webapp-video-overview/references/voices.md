# Voices

## Gemini (default)

Set `"voice"` in narration.json. The model is `gemini-2.5-flash-preview-tts`
unless `"model"` says otherwise (`gemini-2.5-pro-preview-tts` is slower and
somewhat richer). Output is 24 kHz mono PCM.

| Voice | Character | Voice | Character |
|---|---|---|---|
| Zephyr | bright | Puck | upbeat |
| **Charon** | informative — good default for how-tos | Kore | firm |
| Fenrir | excitable | Leda | youthful |
| Orus | firm | Aoede | breezy |
| Callirrhoe | easy-going | Autonoe | bright |
| Enceladus | breathy | Iapetus | clear |
| Umbriel | easy-going | Algieba | smooth |
| Despina | smooth | Erinome | clear |
| Algenib | gravelly | **Rasalgethi** | informative |
| Laomedeia | upbeat | **Achernar** | soft |
| Alnilam | firm | Schedar | even |
| Gacrux | mature | Pulcherrima | forward |
| Achird | friendly | Zubenelgenubi | casual |
| **Vindemiatrix** | gentle | Sadachbia | lively |
| Sadaltager | knowledgeable | **Sulafat** | warm |

Calm narration: Charon, Rasalgethi, Sadaltager, Iapetus (clear, informative);
Vindemiatrix, Sulafat, Achernar (gentle, warm, soft).

**Style.** `"style"` is sent as `"<style>: <line>"`. Gemini follows it and
does not read it aloud (checked by transcribing the output); it mostly changes
pace and warmth. Example: `"Read this in a calm, measured, professional voice,
unhurried and never salesy"` — expect lines ~20–30 % slower than plain.

**Keys.** `GEMINI_API_KEY` (or `GOOGLE_API_KEY`), sent in the
`x-goog-api-key` header. Both classic `AIza…` keys and the newer `AQ.…` keys
are accepted on the generativelanguage endpoint this way. Create one at
https://aistudio.google.com/apikey.

**Limits.** The preview TTS models rate-limit hard on free tiers and
occasionally return 500 with no audio. `tts_gemini.py` backs off and retries
(5 s, 10 s, 20 s, …). A 30-line set takes a few minutes; `--stale` avoids
re-voicing unchanged lines.

## OpenAI (fallback)

`"voice_openai"` (default `onyx`): alloy, ash, ballad, coral, echo, fable,
nova, onyx, sage, shimmer, verse. `"model_openai"` defaults to
`gpt-4o-mini-tts`, which takes `"instructions"` (falls back to `"style"`);
`tts-1`/`tts-1-hd` ignore direction.

## Offline: voicebox's engine (NeMo-Speech.cpp + MagpieTTS)

`tts_voicebox.py` voices every line on this machine, with no key and no
network, using the speech engine of the
[voicebox](https://github.com/danilogr/voicebox) plugin: NVIDIA
NeMo-Speech.cpp running MagpieTTS. It talks only to the local speech server —
voicebox's, if it is running, or one it starts with voicebox's arguments and
stops at the end.

**Setup.** With voicebox: `/voicebox:setup` once. Without it, about 800 MB
(binary 14 MB, MagpieTTS and its codec 640 MB, grammars 137 MB unpacked):

```bash
curl -fsSL https://github.com/NVIDIA/NeMo-Speech.cpp/raw/main/scripts/install.sh \
  | sh -s -- --binary-only --no-modify-path        # ~/.local/bin/nemo-speech
~/.local/bin/nemo-speech pull magpie
# the grammars that make it read numbers, prices and dates as words:
V=$(~/.local/bin/nemo-speech --version | awk '{print $2}'); D=~/Library/Caches/speak-core
mkdir -p $D && curl -fsSL https://github.com/NVIDIA/NeMo-Speech.cpp/releases/download/v$V/tn_configs.tar.bz2 \
  | tar -xjf - -C $D && echo $V > $D/tn_configs/.nemo-speech-version
```

**Settings** are read the way voicebox reads them, so one setup serves both:

| Setting | Default | |
|---|---|---|
| `"engine"` / `TTS_ENGINE` | auto | `voicebox` forces it (`local` still works). Auto picks it when no API key is set and `nemo-speech` is installed or its server answers. |
| `"voice_voicebox"` / `VOICEBOX_VOICE` | `John` | John, Sofia, Aria, Jason, Leo |
| `"model_voicebox"` / `NEMO_TTS_MODEL` | `magpie` | |
| `"voicebox_url"` / `NEMO_HTTP_URL` | `http://127.0.0.1:8082` | the speech server |
| `NEMO_BIN` | `nemo-speech` | the binary, if not on `PATH` (`~/.local/bin` is also tried) |
| `NEMO_TN_DIR` | `~/Library/Caches/speak-core/tn_configs` | the number grammars |
| `NEMO_TTS_SEED` | `1234` here (voicebox: unset) | the voice timbre seed — see below |
| `NEMO_API_KEY` | unset | sent to the server as a bearer token |

**The seed matters.** MagpieTTS draws each voice's timbre at random when its
server starts. Measured: the same line on two fresh starts with
`--tts.seed 1234` came out byte-identical; without a seed, two starts gave
two different takes. So a server this script starts always gets a seed, the
seed is part of each line's voice signature, and changing it re-voices every
line. A server that was already running (voicebox's) keeps its own seed: set
`NEMO_TTS_SEED` to the same value for both, as voicebox's README advises, or a
re-voiced line may not match the rest.

Notes, measured on an Apple M4 Pro (Metal):
- **Pace.** A line of one or two sentences takes 1–3 s to voice. MagpieTTS
  also speaks faster than Gemini with a style: the same script ran ~25 % shorter.
- **One sentence per request.** MagpieTTS repeats or garbles words when a
  request holds several sentences, so each line is sent a sentence at a time
  and joined with a 250 ms pause — as voicebox does.
- **No style direction.** `"style"` is ignored; pick the voice instead.
- **Loudness.** It comes out ~7 dB quieter than the cloud voices; each line is
  normalized to about −18 LUFS so a set of videos sounds even.
- **Check the words.** A word is still occasionally repeated. Listen to the
  take, or transcribe it, before publishing.

## Consistency

Every WAV records the engine, model, voice and style that made it
(`_voice` in narration.json). If any of those change, the next build re-voices
every line of that video — a video with two voices sounds broken. Across a
set of videos, keep the same voice and style in every narration.json.
