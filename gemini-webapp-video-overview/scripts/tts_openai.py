#!/usr/bin/env python3
"""Synthesize each narration line with OpenAI TTS -> DIR/audio/line_<id>.wav.

The fallback to tts_gemini.py, used when only an OpenAI key is available.
Same arguments, same output (24 kHz mono 16-bit WAV), same --stale rules:

    OPENAI_API_KEY=sk-… python3 tts_openai.py DIR [--stale] [line ids…]

narration.json settings (all optional):
    "voice_openai": "onyx"           alloy, ash, ballad, coral, echo, fable,
                                     nova, onyx, sage, shimmer, verse
    "model_openai": "gpt-4o-mini-tts"
    "instructions": "Calm, measured…"  delivery direction; gpt-4o models only.
              Falls back to "style" so one sentence steers both engines.
"""
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave

args = sys.argv[1:]
dirs = [a for a in args if pathlib.Path(a).is_dir()]
if not dirs:
    sys.exit("usage: tts_openai.py DIR [--stale] [line ids…]")
V = pathlib.Path(dirs[0]).resolve()
nar = json.load(open(V / "narration.json"))
STALE = "--stale" in args

MODEL = nar.get("model_openai", "gpt-4o-mini-tts")
VOICE = nar.get("voice_openai", "onyx")
INSTRUCTIONS = (nar.get("instructions") or nar.get("style") or
                "Calm, clear and unhurried. You are showing someone how to use a tool.")
SIGNATURE = f"openai|{MODEL}|{VOICE}|{INSTRUCTIONS}"

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

KEY = os.environ.get("OPENAI_API_KEY")
if not KEY:
    sys.exit("set OPENAI_API_KEY")


def synth(text):
    payload = {"model": MODEL, "voice": VOICE, "input": text, "response_format": "wav"}
    if MODEL.startswith("gpt-"):          # tts-1 and tts-1-hd reject instructions
        payload["instructions"] = INSTRUCTIONS
    for attempt in range(6):
        req = urllib.request.Request(
            "https://api.openai.com/v1/audio/speech", data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and attempt < 5:
                time.sleep(2 ** attempt * 3)
                continue
            sys.exit(f"HTTP {e.code}: {e.read().decode()[:300]}")


for line in lines:
    raw = outdir / f".raw_{line['id']:02d}.wav"
    raw.write_bytes(synth(line["text"]))
    # The response is streamed, so its RIFF header carries a placeholder data
    # size (0xFFFFFFFF). Python's wave module believes it and reports ~4 GB of
    # frames, and retime.py then computes a day-long narration. ffmpeg rewrites
    # the header with the real size.
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
                    "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(wav_path(line))],
                   check=True)
    raw.unlink()
    line["_spoken"] = line["text"]
    line["_voice"] = SIGNATURE
    json.dump(nar, open(V / "narration.json", "w"), ensure_ascii=False, indent=2)
    with wave.open(str(wav_path(line)), "rb") as w:
        secs = w.getnframes() / w.getframerate()
    print(f"line {line['id']:>2}: {secs:5.2f}s  \"{line['text'][:52]}…\"")
print("voice:", VOICE, "model:", MODEL, "->", outdir)
