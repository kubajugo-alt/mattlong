# M0 — Pipeline tests (25 Nov 2026)

| Pipeline | Result | Notes |
|---|---|---|
| ElevenLabs voice → file | **Works** | `creative_generate_speech` returns signed MP3 URLs (44.1 kHz mono, 128 kbps) that download directly. Cost: ~83 credits per take for a 13-word line on `eleven_v4`; the default is 2 takes per call. Test voice for Matt: "Obsidian" (gritty American, middle-aged). Account usage can't be read until the connector is reconnected with more permissions. |
| Public-domain jazz → file | **Works** | Internet Archive's George Blood 78rpm collection downloads directly (MP3 and FLAC). Test track: King Oliver's Jazz Band, "Tears" (recorded 1923; US recordings from 1925 or earlier are public domain as of 2026). Item: `78_tears_king-olivers-jazz-band-king-oliver-louis-armstrong-honore-dutray-johnny-dodd_gbia0190842a`. Check the original recording year of every track, not the reissue date. |
| Canva image → file | **Blocked** | `generate-image` works (Matt reference, media `MAHb4YmgAN8`, 1664×2496), but the connector only hands back a 133×200 thumbnail. The signed thumbnail URL can't be resized. The full-size route is wrapping the image in a design and exporting it, but `create-design` then failed with "Credit quota cooldown is active". |
| Matt consistency (3 poses) | Not started | Waits on the Canva decision. |
| Cut-out arm test | Not started | Waits on a full-size image. |
