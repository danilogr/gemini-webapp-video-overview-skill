# Putting the videos on a site

`build_all.sh` writes, per video, `<slug>.mp4` (H.264/AAC, faststart),
`<slug>.vtt` (captions) and `<slug>.jpg` (poster), and one `videos.json`:

```json
[{"slug": "todo-basics", "title": "Add a task and mark it done", "seconds": 26}]
```

## The player

```html
<video controls preload="metadata" poster="videos/todo-basics.jpg" playsinline>
  <source src="videos/todo-basics.mp4" type="video/mp4">
  <track kind="captions" src="videos/todo-basics.vtt" srclang="en" label="English" default>
</video>
```

- **Captions on by default.** Many people watch help videos muted.
- `playsinline` keeps iOS from forcing full screen.
- A list built from `videos.json` (title + `m:ss`) lets new videos appear
  without code changes.
- Pause the video when its dialog or panel closes.

## Safari needs byte ranges

Safari opens an mp4 with `Range: bytes=0-1` and plays nothing unless the
server answers **206 Partial Content** with `Content-Range`. Chrome copes
with a plain 200, so this is easy to miss in testing. Check:

```bash
curl -s -o /dev/null -D - -H 'Range: bytes=0-1' https://your.site/videos/x.mp4 | head -5
# want: HTTP/2 206 and content-range: bytes 0-1/<size>
```

Most web servers and CDNs do this. Some edge asset layers do not (for
example, a static-assets layer that always returns the whole file). Then
serve the videos through a small handler that reads the file and slices the
requested range — single range, `bytes=a-b`, `bytes=a-`, `bytes=-n`; 416 when
out of range; `Accept-Ranges: bytes` on every answer. Keep the files small,
since such a handler usually reads the whole file to slice it.

## Content-Security-Policy

Media and captions fall under `media-src`, which falls back to
`default-src`. Serving the files from the same origin needs no policy change.
Do not add a third-party host to the policy for videos.

## Caching

The file names carry no version, so do not mark them `immutable`; a day
(`max-age=86400`) is a reasonable default. Rebuilding replaces the files in
place.

## A "what's new" video

A pattern that works: on load, if the person has used the app before (any
saved settings or data exist) and a stored "seen" marker is not the current
release id, open a dialog that plays the what's-new video muted with
captions, with "Close" and "More videos". Set the marker when it opens, so it
shows once. Set it silently on a first visit, so new users are not told what
is "new". Skip it for automated or deep-linked sessions. Bump the id to show
the next one.

## Measuring

If the site counts feature use, count: a help video started, the what's-new
video watched to the end, closed early, and "More videos". These are usually
watched before any other activity, so make sure the counts do not depend on
a session that only starts with the app's main action.
