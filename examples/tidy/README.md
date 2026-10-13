# Example: Tidy

A small invented task app, made to show the skill on a full set of steps,
and the three narrated videos the skill built of it.

![The Help page of Tidy playing one of its videos, with captions](docs/help-page.png)

| Video | Length | Shows the skill doing |
|---|---|---|
| [Add a task and set its priority](site/videos/add-tasks.mp4) | 0:33 | `type`, `select` on a native menu, `click`, rings on a badge and a counter |
| [Finish a task, and filter the list](site/videos/finish-and-filter.mp4) | 0:22 | `setup` (three tasks made before the clock, then cut), checkboxes, filters, `snap` |
| [Delete a task, and keep notes on one](site/videos/delete-and-details.mp4) | 0:25 | the pointer above a modal `<dialog>`, a click that loads another page with `waitFor`, the pointer keeping its place across page loads, typing into a textarea |

All three use the Gemini voice "Charon" with a style direction, and the
app's teal as the pointer accent. Each has captions (`.vtt`) and a poster
(`.jpg`), and `site/videos/videos.json` lists them. The site's Help page
(`site/help.html`) builds its list from that file and plays each video with
captions on — the pattern in `references/serving.md`.

## Made by another agent

[`made-by-gemini-cli/`](made-by-gemini-cli/) holds a fourth video of Tidy,
made by Gemini CLI with only this skill — its narration, captions, poster and
the request it was given.

## Layout

```
site/           the app: index.html (tasks), task.html (a task's page), help.html (videos)
  videos/       what build_all.sh published: <slug>.mp4/.vtt/.jpg and videos.json
videos/         the sources: ORDER and one folder per video with its narration.json
docs/           the screenshot above
```

## Rebuild

```bash
S=../../gemini-webapp-video-overview/scripts
python3 -m http.server 8765 --directory site &        # the app, at http://127.0.0.1:8765
GEMINI_API_KEY=… $S/build_all.sh videos site/videos   # voice, time, record, publish all three
python3 $S/inspect.py videos/delete-and-details       # frames to check
```

Every video starts from `index.html?reset`, which empties the list, so each
take starts from the same state. The voice files are not committed, so a
rebuild re-voices the lines (about a minute with a Gemini key).
