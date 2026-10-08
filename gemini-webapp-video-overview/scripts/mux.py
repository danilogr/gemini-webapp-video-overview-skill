#!/usr/bin/env python3
"""Lay each line's audio onto the silent recording at its start time.

    python3 mux.py DIR [OUT.mp4]       # OUT defaults to DIR/video.mp4

Each WAV is delayed to its line's "start" with adelay and the clips are mixed
with normalize=0: retime.py never lets two lines overlap, so full level is the
right level, and amix's default normalisation would quietly halve it. The mix
is padded or trimmed to the video's length. ABR sets the AAC bit rate
(default 96k; the voice is 24 kHz mono, so more buys nothing).
"""
import json
import os
import pathlib
import subprocess
import sys

args = sys.argv[1:]
if not args:
    sys.exit("usage: mux.py DIR [OUT.mp4]")
V = pathlib.Path(args[0]).resolve()
out = pathlib.Path(args[1]) if len(args) > 1 else V / "video.mp4"
nar = json.load(open(V / "narration.json"))
lines = nar["lines"]
silent = V / "silent.mp4"

vdur = float(subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "default=nokey=1:noprint_wrappers=1", str(silent)],
    capture_output=True, text=True, check=True).stdout.strip())

inputs, parts, labels = [], [], []
for i, l in enumerate(lines, start=1):            # input 0 is the video
    inputs += ["-i", str(V / "audio" / f"line_{l['id']:02d}.wav")]
    parts.append(f"[{i}]adelay={int(round(l['start'] * 1000))}:all=1[a{i}]")
    labels.append(f"[a{i}]")
filt = (";".join(parts) + ";" + "".join(labels) +
        f"amix=inputs={len(lines)}:normalize=0:dropout_transition=0[mx];"
        f"[mx]apad,atrim=0:{vdur:.3f}[a]")

r = subprocess.run(
    ["ffmpeg", "-y", "-i", str(silent), *inputs, "-filter_complex", filt,
     "-map", "0:v", "-map", "[a]", "-c:v", "copy",
     "-c:a", "aac", "-b:a", os.environ.get("ABR", "96k"),
     "-movflags", "+faststart", str(out)],
    capture_output=True, text=True)
if r.returncode:
    print(r.stderr[-1500:])
    raise SystemExit(1)
print("wrote", out)
