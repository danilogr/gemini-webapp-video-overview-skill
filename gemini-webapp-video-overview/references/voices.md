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

## Consistency

Every WAV records the engine, model, voice and style that made it
(`_voice` in narration.json). If any of those change, the next build re-voices
every line of that video — a video with two voices sounds broken. Across a
set of videos, keep the same voice and style in every narration.json.
