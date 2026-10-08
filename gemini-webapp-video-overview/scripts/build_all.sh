#!/usr/bin/env bash
# Build a set of videos into one folder, with captions, posters and a list.
#
#   build_all.sh ROOT PUB                 # every video under ROOT
#   build_all.sh ROOT PUB slug1 slug2     # just these
#   build_all.sh --no-tts ROOT PUB        # reuse all audio; no key needed
#   build_all.sh --tts ROOT PUB slug      # re-voice every line of slug
#
# ROOT has one folder per video, named by its slug, each with narration.json.
# The order of the list is ROOT/ORDER (one slug per line) if it exists, else
# alphabetical. For each video PUB gets <slug>.mp4, <slug>.vtt and <slug>.jpg;
# then PUB/videos.json lists them all: [{slug, title, seconds}].
#
# By default only lines with no audio, new words or a new voice are
# synthesized, so a rebuild that changes no words needs no key. Every video
# is recorded from the app as it is now, so a rebuild also checks the app
# still does what the videos show.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

TTS=--stale
case "${1:-}" in --no-tts|--tts|--stale) TTS="$1"; shift ;; esac
[[ $# -ge 2 ]] || { echo "usage: build_all.sh [--tts|--no-tts] ROOT PUB [slug…]" >&2; exit 2; }
ROOT="$(cd "$1" && pwd)"; mkdir -p "$2"; PUB="$(cd "$2" && pwd)"; shift 2

# A while-read loop, not mapfile: macOS still ships bash 3.2.
ALL=()
if [[ -f "$ROOT/ORDER" ]]; then
  while IFS= read -r s; do [[ -n "$s" && "$s" != \#* ]] && ALL+=("$s"); done < "$ROOT/ORDER"
else
  for d in "$ROOT"/*/; do d="${d%/}"; [[ -f "$d/narration.json" ]] && ALL+=("${d##*/}"); done
fi
SLUGS=("$@"); [[ $# -eq 0 ]] && SLUGS=(${ALL[@]+"${ALL[@]}"})
[[ ${#SLUGS[@]} -gt 0 ]] || { echo "no videos found in $ROOT" >&2; exit 1; }

for slug in "${SLUGS[@]}"; do
  [[ -f "$ROOT/$slug/narration.json" ]] || { echo "no video called $slug in $ROOT" >&2; exit 1; }
  echo; echo "######## $slug"
  OUT="$PUB/$slug.mp4" "$HERE/build.sh" "$TTS" "$ROOT/$slug"
  python3 "$HERE/publish.py" "$slug" "$ROOT/$slug" "$PUB"
done

python3 "$HERE/publish.py" --list "$ROOT" "$PUB" ${ALL[@]+"${ALL[@]}"}
du -ch "$PUB"/*.mp4 | tail -1
