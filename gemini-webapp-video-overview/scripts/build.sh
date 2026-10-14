#!/usr/bin/env bash
# Build one narrated video, end to end: voice → timing → recording → mp4.
#
#   build.sh DIR                # synthesize only lines that need it (--stale)
#   build.sh --tts DIR          # synthesize every line again
#   build.sh --no-tts DIR       # reuse the audio as it is; no key needed
#
# DIR holds narration.json. It gets audio/, rec/, silent.mp4, transcript.vtt
# and the video: DIR/video.mp4, or $OUT.
#
# The order is the point. Audio is the master clock: the lines are spoken
# first, measured, and their true times written into narration.json — THEN the
# app is recorded against those times. Record first and the pointer drifts off
# the words by the third line, and every fix moves everything after it.
#
# Voice engine: $TTS_ENGINE (gemini|openai|voicebox), else narration.json
# "engine", else gemini when GEMINI_API_KEY/GOOGLE_API_KEY is set, else openai
# when OPENAI_API_KEY is set, else voicebox (offline: NeMo-Speech, voicebox's
# engine) when nemo-speech is installed or its server answers, else gemini.
#
# Environment: OUT (mp4 path), CRF (quality, default 23), ABR (audio bit
# rate, default 128k), NODE_PATH (a node_modules holding playwright).
# Needs: python3, node, ffmpeg/ffprobe, Playwright with Chromium.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

TTS=--stale
case "${1:-}" in
  --no-tts) TTS=none; shift ;;
  --tts)    TTS=all; shift ;;
  --stale)  shift ;;
esac
[[ $# -ge 1 ]] || { echo "usage: build.sh [--tts|--no-tts] DIR" >&2; exit 2; }
DIR="$(cd "$1" && pwd)"
OUT="${OUT:-$DIR/video.mp4}"
CRF="${CRF:-23}"
export ABR="${ABR:-128k}"

for tool in python3 node ffmpeg ffprobe; do
  command -v "$tool" >/dev/null || { echo "missing: $tool" >&2; exit 1; }
done

# Playwright: use what node can already import; else look for a copy in the
# npx cache; else say how to install it.
if ! node -e 'require("playwright")' 2>/dev/null; then
  if [[ -z "${NODE_PATH:-}" ]]; then
    for d in "$DIR/node_modules" "$PWD/node_modules" "$HOME"/.npm/_npx/*/node_modules; do
      [[ -d "$d/playwright" ]] && { export NODE_PATH="$d"; break; }
    done
  fi
  node -e 'require("playwright")' 2>/dev/null || {
    echo "playwright is not importable from node. Install it once with:" >&2
    echo "  npm i -g playwright && npx playwright install chromium   (then NODE_PATH=\$(npm root -g))" >&2
    exit 1
  }
fi
# Say which copy runs: its Chromium revision must be installed
# (`npx playwright@<this version> install chromium`).
node -e 'const p=require.resolve("playwright/package.json");console.log("playwright", require(p).version, "from", p.replace(/\/package.json$/,""))'

engine="${TTS_ENGINE:-$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('engine',''))" "$DIR/narration.json")}"
if [[ -z "$engine" ]]; then
  if [[ -n "${GEMINI_API_KEY:-}${GOOGLE_API_KEY:-}" ]]; then engine=gemini
  elif [[ -n "${OPENAI_API_KEY:-}" ]]; then engine=openai
  # No key at all: use the offline voice if NeMo-Speech is installed.
  elif command -v nemo-speech >/dev/null || [[ -x "$HOME/.local/bin/nemo-speech" ]] \
       || curl -s -m 2 -o /dev/null "${NEMO_HTTP_URL:-http://127.0.0.1:8082}/v1/models"; then engine=voicebox
  else engine=gemini; fi
fi
[[ "$engine" == local ]] && engine=voicebox          # the earlier name of the offline engine
[[ -f "$HERE/tts_$engine.py" ]] || { echo "unknown voice engine: $engine (gemini, openai or voicebox)" >&2; exit 2; }

if [[ "$TTS" != none ]]; then
  echo "== 1/5  voice ($engine)"
  args=("$DIR"); [[ "$TTS" == --stale ]] && args+=(--stale)
  python3 "$HERE/tts_$engine.py" "${args[@]}"
fi

echo; echo "== 2/5  timing the script to the audio"
python3 "$HERE/retime.py" "$DIR"

echo; echo "== 3/5  recording the app"
node "$HERE/record.cjs" "$DIR"

read -r W H < <(python3 -c "import json,sys;print(*json.load(open(sys.argv[1])).get('size',[1280,800]))" "$DIR/narration.json")
echo; echo "== 4/5  encoding, from the instant the clock started"
ffmpeg -y -loglevel error -ss "$(cat "$DIR/rec/offset.txt")" -i "$(ls "$DIR"/rec/*.webm | head -1)" \
  -vf "fps=30,scale=${W}:${H}" -c:v libx264 -preset slow -pix_fmt yuv420p -crf "$CRF" \
  -movflags +faststart "$DIR/silent.mp4"

echo; echo "== 5/5  laying the voice on the timeline"
python3 "$HERE/mux.py" "$DIR" "$OUT"

echo "$OUT" > "$DIR/rec/output.txt"      # inspect.py finds the video here
secs="$(ffprobe -v error -show_entries format=duration -of default=nokey=1:noprint_wrappers=1 "$OUT")"
echo; echo "done: $OUT  (${secs%.*} s, $(du -h "$OUT" | cut -f1))"
echo "next: python3 $HERE/inspect.py $DIR   — then LOOK at the frames"
