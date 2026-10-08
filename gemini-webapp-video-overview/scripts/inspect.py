#!/usr/bin/env python3
"""Check a take without watching it: one frame per action, the sound level,
and what the app showed.

    python3 inspect.py DIR [VIDEO.mp4]     # VIDEO defaults to DIR/video.mp4

Writes DIR/frames/NN_<seconds>_<action>.png — one frame a beat after every
pointer action and ring, which is when its effect should be on screen — and
prints, for each, the narration line being spoken at that instant. Then the
mean and peak volume, and rec/final-state.json.

Logs cannot tell you a ring landed on the wrong element, or that the pointer
clicked while the page was still loading. The frames can. Open them and look:
is the pointer on the thing the line names, at the moment it names it?
"""
import json
import pathlib
import re
import subprocess
import sys

if len(sys.argv) < 2:
    sys.exit(__doc__)
V = pathlib.Path(sys.argv[1]).resolve()
# The video: an explicit path, else where build.sh last wrote it (build_all
# puts it beside the other published files), else DIR/video.mp4.
recorded = V / "rec" / "output.txt"
mp4 = (pathlib.Path(sys.argv[2]) if len(sys.argv) > 2
       else pathlib.Path(recorded.read_text().strip()) if recorded.exists()
       else V / "video.mp4")
if not mp4.exists():
    sys.exit(f"no video at {mp4}: build it first, or pass its path")
nar = json.load(open(V / "narration.json"))


def resolve(at):
    if isinstance(at, (int, float)) or re.fullmatch(r"-?\d+(\.\d+)?", str(at)):
        return float(at)
    m = re.fullmatch(r"L(\d+)\.(start|end)([+-][\d.]+)?", at)
    line = next(l for l in nar["lines"] if l["id"] == int(m[1]))
    return line[m[2]] + float(m[3] or 0)


def speaking(t):
    for l in nar["lines"]:
        if l["start"] - 0.2 <= t <= l["end"] + 0.2:
            return f"L{l['id']}: {l['text'][:60]}"
    return "(silence)"


SHOWN = {"click", "dblclick", "select", "type", "ring", "cursor", "hover",
         "download", "upload", "scroll", "press"}
frames = V / "frames"
frames.mkdir(exist_ok=True)
for old in frames.glob("*.png"):
    old.unlink()

# The effect of a click shows a beat later; a ring is drawn at once; typing
# needs time for the characters to appear.
DELAY = {"type": 1.4, "ring": 0.5, "press": 0.5}
steps = sorted(((resolve(a["at"]), a["do"]) for a in nar.get("actions", [])), key=lambda s: s[0])
n = 0
for t, do in steps:
    if do[0] not in SHOWN:
        continue
    n += 1
    at = t + DELAY.get(do[0], 0.9)
    if do[0] == "type" and len(do) > 2:     # glide + click + the characters
        at = t + 1.0 + len(str(do[2])) * nar.get("type_delay_ms", 55) / 1000 + 0.3
    name = f"{n:02d}_{at:05.1f}s_{do[0]}.png"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{at:.2f}", "-i", str(mp4),
                    "-frames:v", "1", "-vf", "scale=960:-1", str(frames / name)], check=True)
    target = " ".join(str(x) for x in do[1:2])
    print(f"{name:<28} {do[0]:<8} {target[:40]:<40} | {speaking(t)}")

vol = subprocess.run(["ffmpeg", "-i", str(mp4), "-af", "volumedetect", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
mean = re.search(r"mean_volume: (-?[\d.]+)", vol)
peak = re.search(r"max_volume: (-?[\d.]+)", vol)
print(f"\nvolume: mean {mean[1] if mean else '?'} dB, peak {peak[1] if peak else '?'} dB"
      "   (speech normally sits around -16 to -26 dB mean; below -35 is a silent take)")

state = V / "rec" / "final-state.json"
if state.exists():
    print("\nstate:", state.read_text())
print(f"\n{n} frames in {frames}/ — open them.")
