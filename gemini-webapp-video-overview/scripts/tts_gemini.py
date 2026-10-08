#!/usr/bin/env python3
"""Synthesize each narration line with Gemini TTS -> DIR/audio/line_<id>.wav.

    GEMINI_API_KEY=… python3 tts_gemini.py DIR            # every line
    GEMINI_API_KEY=… python3 tts_gemini.py DIR --stale    # only lines that need it
    GEMINI_API_KEY=… python3 tts_gemini.py DIR 3 5        # just lines 3 and 5

The key goes in the x-goog-api-key header. That works for both kinds of
Gemini API key: the classic `AIza…` and the newer `AQ.…` (tested 2026-10: the
generativelanguage endpoint accepts an AQ. key in the header). GOOGLE_API_KEY
is read if GEMINI_API_KEY is not set.

narration.json settings (all optional):
    "voice": "Charon"                          one of the 30 prebuilt voices
    "model": "gemini-2.5-flash-preview-tts"
    "style": "Read this in a calm, measured…"  prefixed as "<style>: <line>".
              Gemini follows it and does not speak it (checked by transcribing).

Output is 24 kHz mono 16-bit WAV, the same artifact tts_openai.py writes, so
nothing downstream knows which engine ran.

--stale: a line is redone when it has no WAV, when its words changed since it
was spoken, or when the voice changed. A voice change redoes EVERY line —
re-voicing only the edited lines would put two voices in one video.
"""
import base64
import json
import os
import pathlib
import struct
import sys
import time
import urllib.error
import urllib.request

args = sys.argv[1:]
dirs = [a for a in args if pathlib.Path(a).is_dir()]
if not dirs:
    sys.exit("usage: tts_gemini.py DIR [--stale] [line ids…]")
V = pathlib.Path(dirs[0]).resolve()
nar = json.load(open(V / "narration.json"))
STALE = "--stale" in args

MODEL = nar.get("model", "gemini-2.5-flash-preview-tts")
VOICE = nar.get("voice", "Charon")
STYLE = nar.get("style", "").strip()
SIGNATURE = f"gemini|{MODEL}|{VOICE}|{STYLE}"

outdir = V / "audio"
outdir.mkdir(exist_ok=True)


def wav_path(line):
    return outdir / f"line_{line['id']:02d}.wav"


def needs(line):
    return (not wav_path(line).exists()
            or line.get("_spoken", line["text"]) != line["text"]
            or line.get("_voice", SIGNATURE) != SIGNATURE)


only = {int(x) for x in args if x.isdigit()}
lines = [l for l in nar["lines"] if not only or l["id"] in only]
if STALE:
    voice_changed = any(wav_path(l).exists() and l.get("_voice", SIGNATURE) != SIGNATURE
                        for l in nar["lines"])
    if voice_changed and not only:
        print("the voice changed since the audio was made: redoing every line")
        lines = nar["lines"]
    else:
        lines = [l for l in lines if needs(l)]
if not lines:
    print("audio is current:", outdir)
    raise SystemExit(0)

# Asked for only now, so a build with nothing to synthesize needs no key.
KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if not KEY:
    sys.exit("set GEMINI_API_KEY (an AIza… or AQ.… key from https://aistudio.google.com/apikey)")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def wav(pcm, rate=24000):
    return (b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt " +
            struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16) +
            b"data" + struct.pack("<I", len(pcm)) + pcm)


def synth(text):
    prompt = f"{STYLE}: {text}" if STYLE else text
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}},
        },
    }).encode()
    # The preview TTS models rate-limit hard (a few requests a minute on free
    # tiers) and now and then answer 500 with no audio. Back off and retry.
    for attempt in range(6):
        req = urllib.request.Request(URL, data=body, headers={
            "Content-Type": "application/json", "x-goog-api-key": KEY})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            part = d["candidates"][0]["content"]["parts"][0]["inlineData"]
            return base64.b64decode(part["data"])
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300].replace(KEY, "<key>")
            if e.code in (429, 500, 503) and attempt < 5:
                wait = 2 ** attempt * 5
                print(f"  HTTP {e.code}, retrying in {wait}s")
                time.sleep(wait)
                continue
            sys.exit(f"HTTP {e.code}: {msg}")
        except (KeyError, IndexError):
            if attempt < 5:
                time.sleep(3)
                continue
            sys.exit(f"no audio in the response: {json.dumps(d)[:300]}")


for line in lines:
    pcm = synth(line["text"])
    wav_path(line).write_bytes(wav(pcm))
    line["_spoken"] = line["text"]
    line["_voice"] = SIGNATURE
    # Saved after every line, so an interrupted run keeps what it paid for.
    json.dump(nar, open(V / "narration.json", "w"), ensure_ascii=False, indent=2)
    print(f"line {line['id']:>2}: {len(pcm) / 2 / 24000:5.2f}s  \"{line['text'][:52]}…\"")
print("voice:", VOICE, "model:", MODEL, "->", outdir)
