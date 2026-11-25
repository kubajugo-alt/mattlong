# Prologue voice track

Generated from `game/ink/prologue.ink` by `tools/voice_lines.py` (ElevenLabs eleven_v4, cast voices from
`voices/cast.json`, the newsboy on VALF). One mp3 per line, named `<speaker>-<hash of the exact text>`, so an edited
line gets a new file and only that line is re-voiced. `lines.json` maps each file to its speaker and text; spoken
(non-VO) lines have Rhubarb mouth cues (`<id>.json`). Matt's voice-over (`vo-*`) has no cues: his mouth stays shut.

Delivery tags are one or two words (`[quietly]` for the voice-over): longer directions made the model repeat phrases.
`tools/voice_qa.py` transcribes every take and compares it with the script (`qa.json`); the remaining flags are only
the transcript writing numbers as digits ("$50", "4417") and spellings ("Li Wing", "Doyer Street").
