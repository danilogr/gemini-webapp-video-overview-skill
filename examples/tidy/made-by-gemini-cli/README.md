# Made by Gemini CLI

This video was made by **Gemini CLI 0.63.0** (model `gemini-3.8-flash`) with
only this skill installed in the project's `.agents/skills/` — no other help.
The request, as a person would type it:

> Make me a short narrated how-to video, about 20 to 30 seconds, of the task
> app running at http://127.0.0.1:8766/index.html. Show how to add a task
> with a High priority, then mark it done. Start from an empty list (the app
> empties its list when the URL ends with ?reset). Put the finished mp4, its
> captions and a poster image in ./out/. A Gemini API key is already in the
> environment as GEMINI_API_KEY. When you finish, tell me what you made and
> how you checked it.

It took 8 minutes and 61 tool calls. It read the skill and its references,
wrote `narration.json` (here), voiced it with Gemini, built the video, ran
`inspect.py` and opened all seven frames before publishing. The result:
24 s, 1280×800, 48 kHz stereo narration at −17.6 dB, every action on the
element its line names.
