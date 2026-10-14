#!/usr/bin/env python3
"""Synthesize each narration line OFFLINE, with voicebox's engine -> DIR/audio/line_<id>.wav.

    python3 tts_voicebox.py DIR [--stale] [line ids…]

The voice comes from NVIDIA NeMo-Speech.cpp running MagpieTTS on this machine:
the speech server of the voicebox plugin (https://github.com/danilogr/voicebox)
and its engine, speak-core. No key, no account, and nothing leaves the
machine: every request goes to the local server, and proxy settings are
ignored so a request cannot be routed anywhere else.

The server speaks the OpenAI-compatible /v1/audio/speech. If voicebox's server
is already running, this uses it and leaves it running. If nothing answers,
this starts `nemo-speech serve` with the same arguments voicebox uses and stops
it at the end.

Install: if you use voicebox, `/voicebox:setup` once installs everything this
needs. Without voicebox, ~800 MB (binary, MagpieTTS and its codec, grammars
that read numbers and dates as words) — see references/voices.md, "Offline".

Settings, read like voicebox reads them (so one setup serves both):
    NEMO_HTTP_URL   http://127.0.0.1:8082     the speech server
    NEMO_BIN        nemo-speech               the binary, if not on PATH
    NEMO_TN_DIR     ~/Library/Caches/speak-core/tn_configs   number grammars
    NEMO_API_KEY    unset                     sent as a bearer token if set
    NEMO_TTS_SEED   unset                     the voice timbre seed (see below)
    VOICEBOX_VOICE  John                      the default voice
narration.json (overrides): "voice_voicebox" (or "voice_local"): John, Sofia,
Aria, Jason or Leo; "model_voicebox": "magpie"; "voicebox_url".
MagpieTTS takes no style direction; "style" is not used here.

Timbre. MagpieTTS draws a voice's timbre at random when the server starts,
unless it is given a seed. Without one, a line re-voiced after a restart can
sound like a different person from the lines beside it. So a server started
here always gets a seed (NEMO_TTS_SEED, else 1234), the seed is part of each
line's voice signature, and a different seed re-voices every line. A server
that was already running is used with whatever seed it has: set NEMO_TTS_SEED
to the same value in both, as voicebox's README advises.

MagpieTTS repeats or garbles words when one request holds several sentences,
so each line is sent a sentence at a time (a sentence over 250 characters is
cut at its commas) and the pieces are joined with a 250 ms pause. The result
is resampled to the pipeline's 24 kHz mono 16-bit WAV.

--stale and the voice signature work as in tts_gemini.py: a change of words
redoes the line; a change of engine or voice redoes every line.
"""
import atexit
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave

args = sys.argv[1:]
dirs = [a for a in args if pathlib.Path(a).is_dir()]
if not dirs:
    sys.exit("usage: tts_voicebox.py DIR [--stale] [line ids…]")
V = pathlib.Path(dirs[0]).resolve()
nar = json.load(open(V / "narration.json"))
STALE = "--stale" in args

MODEL = nar.get("model_voicebox") or nar.get("model_local") or os.environ.get("NEMO_TTS_MODEL") or "magpie"
VOICE = (nar.get("voice_voicebox") or nar.get("voice_local") or os.environ.get("VOICEBOX_VOICE")
         or "John")
URL = (nar.get("voicebox_url") or nar.get("local_url") or os.environ.get("NEMO_HTTP_URL")
       or os.environ.get("LOCAL_TTS_URL") or "http://127.0.0.1:8082").rstrip("/")
SEED = os.environ.get("NEMO_TTS_SEED") or "1234"
API_KEY = os.environ.get("NEMO_API_KEY")
SIGNATURE = f"voicebox|{MODEL}|{VOICE}|seed {SEED}"
PIECE_CHARS, PAUSE_MS = 250, 250

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

# Local only: no proxy may carry these requests off the machine.
http = urllib.request.build_opener(urllib.request.ProxyHandler({}))


AUTH = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}


def answering():
    try:
        with http.open(urllib.request.Request(f"{URL}/v1/models", headers=AUTH), timeout=3) as r:
            return r.status == 200
    except (urllib.error.URLError, OSError):
        return False


def find_binary():
    for cand in (os.environ.get("NEMO_BIN"), shutil.which("nemo-speech"),
                 os.path.expanduser("~/.local/bin/nemo-speech")):
        if cand and os.path.exists(cand):
            return cand
    return None


def start_server():
    binary = find_binary()
    if not binary:
        sys.exit("no speech server at " + URL + " and no nemo-speech to start one.\n"
                 "With voicebox: run /voicebox:setup once. Without: references/voices.md, "
                 "\"Offline\".")
    port = re.search(r":(\d+)$", URL)
    # The arguments voicebox's supervisor uses, plus the seed.
    cmd = [binary, "serve", "--tts-model", MODEL, "--port", port[1] if port else "8082",
           "--device", "auto", "--no-ui", "--tts.seed", SEED]
    tn = pathlib.Path(os.environ.get("NEMO_TN_DIR") or
                      os.path.expanduser("~/Library/Caches/speak-core/tn_configs"))
    if (tn / "en" / "verbalize.far").exists():
        cmd += ["--tn-model-dir", str(tn)]   # numbers, prices and dates read as words
    else:
        print("  note: no text-normalization grammars; numbers may be read badly")
    log = open(V / "audio" / ".server.log", "w")
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
    atexit.register(lambda: (proc.terminate(), proc.wait(10)))
    for _ in range(120):
        if answering():
            print(f"started the speech server ({binary}, pid {proc.pid}, seed {SEED})")
            return
        if proc.poll() is not None:
            sys.exit(f"the speech server exited: see {V / 'audio' / '.server.log'}")
        time.sleep(1)
    sys.exit("the speech server did not answer within 120 s")


def sentences(text):
    """Sentence by sentence; a sentence over PIECE_CHARS is cut at its commas."""
    out = []
    for s in re.split(r"(?<=[.!?])\s+", text.strip()):
        while len(s) > PIECE_CHARS:
            cut = s.rfind(",", 0, PIECE_CHARS)
            cut = cut if cut > 0 else s.rfind(" ", 0, PIECE_CHARS)
            out.append(s[:cut].strip(" ,") + ",")
            s = s[cut + 1:].strip()
        if s:
            out.append(s)
    return out


def speak(text):
    body = json.dumps({"model": MODEL, "input": text, "voice": VOICE,
                       "response_format": "wav"}).encode()
    for attempt in range(3):
        req = urllib.request.Request(f"{URL}/v1/audio/speech", data=body,
                                     headers={"Content-Type": "application/json", **AUTH})
        try:
            with http.open(req, timeout=300) as r:
                data = r.read()
            if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
                return data
            err = f"not a WAV: {data[:80]!r}"
        except (urllib.error.URLError, OSError) as e:
            err = str(e)
        time.sleep(2)
    sys.exit(f"the speech server failed on: {text[:60]!r} ({err})")


def joined(parts):
    """One WAV: the parts in order, PAUSE_MS of silence between each two."""
    frames, params = [], None
    for p in parts:
        with wave.open(io.BytesIO(p)) as w:
            params = params or w.getparams()
            frames.append(w.readframes(w.getnframes()))
    gap = b"\0" * (params.framerate * PAUSE_MS // 1000 * params.sampwidth * params.nchannels)
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setparams(params)
        w.writeframes(gap.join(frames))
    return out.getvalue()


if answering():
    print(f"using the speech server already running at {URL} (voicebox's, or another);"
          " its seed is its own — set NEMO_TTS_SEED alike in both")
else:
    start_server()

for line in lines:
    parts = [speak(s) for s in sentences(line["text"])]
    raw = outdir / f".raw_{line['id']:02d}.wav"
    raw.write_bytes(joined(parts))
    # MagpieTTS answers at 22.05 kHz and ~7 dB quieter than the cloud voices;
    # the pipeline's WAVs are 24 kHz mono, and a set of videos should sound
    # equally loud whichever engine voiced it. loudnorm brings each line to
    # about -18 LUFS with peaks under -1.5 dB, where the Gemini lines sit.
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
                    "-af", "loudnorm=I=-18:TP=-1.5:LRA=11",
                    "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(wav_path(line))],
                   check=True)
    raw.unlink()
    line["_spoken"] = line["text"]
    line["_voice"] = SIGNATURE
    json.dump(nar, open(V / "narration.json", "w"), ensure_ascii=False, indent=2)
    with wave.open(str(wav_path(line)), "rb") as w:
        secs = w.getnframes() / w.getframerate()
    print(f"line {line['id']:>2}: {secs:5.2f}s  ({len(parts)} piece{'s' * (len(parts) > 1)})  "
          f"\"{line['text'][:48]}…\"")
print("voice:", VOICE, "model:", MODEL, f"seed {SEED} (offline, voicebox engine) ->", outdir)
