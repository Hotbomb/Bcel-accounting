# THE STAIN — Progress

## Status (2026-11-26)
The user asked me to decide everything and make the full film. Phases 0–4 are done (QA contact sheets replace the animatic review). **Phase 5 (final render) is running.**

## Where things live
- Repo `hotbomb/bcel-accounting` (borrowed), folder `the-stain/`, branch `ccr-35112457-trui8i` (stands in for the brief's `film` branch).
- Cloud environment `the-stain` (allows speech.platform.bing.com).

## Decisions (made by Claude, as asked)
- Engine: Cycles CPU, 10 samples + OpenImageDenoise, 1280×720, on twos, render cropped to the letterbox area.
- Characters: Option B (code-built clay puppets). Voices: edge-tts (Niwat ×3 with pitch/rate offsets, Premwadee).
- Full length (~8.4 min + 3 min credits). Blender 5.2.5 from PyPI (download.blender.org is blocked).
- No song was uploaded, so an original song was composed in code (`scripts/compose_song.py`, `assets/song.wav`). The hum (hum_1..6) is made from it. If the user uploads `song.mp3`, re-run make_hums.sh + mix_audio.py and re-finish.
- Volumetric haze replaced by a soft camera-only beam mesh + compositor-style grade (CPU budget).
- 0-0 (black), 0C (title) and CREDITS are made in ffmpeg, not Blender.

## Tool setup for a fresh machine
apt-get install -y ffmpeg libegl1 libgl1 libegl-mesa0 libgl1-mesa-dri fonts-noto-core fonts-noto-color-emoji fonts-thai-tlwg
python3 -m venv /opt/bpyenv && /opt/bpyenv/bin/pip install bpy==5.2.5 soundfile scipy
pip install --break-system-packages edge-tts pydub numpy scipy soundfile pillow
Then: python3 scripts/make_textures.py; scripts/make_hums.sh; python3 scripts/mix_audio.py (song.wav: python3 scripts/compose_song.py)

## How to continue rendering
scripts/render_queue.sh 6600   # resumable; encodes + commits each finished shot

## Render queue
- [x] 0A (rendered 2026-11-26)
- [x] 0B (rendered 2026-11-26)
- [x] 1A (rendered 2026-11-26)
- [x] 1B (rendered 2026-11-26)
- [x] 1C (rendered 2026-11-26)
- [x] 1D (rendered 2026-11-26)
- [x] 1E (rendered 2026-11-26)
- [x] 1F (rendered 2026-11-26)
- [x] 1G (rendered 2026-11-26)
- [x] 1H (rendered 2026-11-26)
- [x] 1I (rendered 2026-11-26)
- [x] 1J (rendered 2026-11-26)
- [x] 1K (rendered 2026-11-26)
- [x] 2A (rendered 2026-11-26)
- [x] 2B (rendered 2026-11-26)
- [x] 2C (rendered 2026-11-26)
- [x] 2D (rendered 2026-11-26)
- [x] 3A (rendered 2026-11-26)
- [x] 3B (rendered 2026-11-27)
- [x] 3C (rendered 2026-11-27)
- [x] 3D (rendered 2026-11-27)
- [x] 3E (rendered 2026-11-27)
- [x] 3F (rendered 2026-11-27)
- [x] 4A (rendered 2026-11-27)
- [x] 4B (rendered 2026-11-27)
- [x] 4C (rendered 2026-11-27)
- [x] 4D (rendered 2026-11-27)
- [x] 4E (rendered 2026-11-27)
- [x] 4F (rendered 2026-11-27)
- [x] 5A (rendered 2026-11-27)
- [x] 5B (rendered 2026-11-27)
- [x] 5C (rendered 2026-11-27)
- [x] 5D (rendered 2026-11-27)
- [x] 6A (rendered 2026-11-27)
- [x] 6B (rendered 2026-11-27)
- [x] 6C (rendered 2026-11-27)
- [x] 6D (rendered 2026-11-27)
- [x] 6E (rendered 2026-11-27)
- [x] 7A (rendered 2026-11-27)
- [x] 7B (rendered 2026-11-27)
- [x] 7C (rendered 2026-11-27)
- [x] 8A (rendered 2026-11-27)
- [x] 8B (rendered 2026-11-27)
- [x] 8C (rendered 2026-11-27)
- [x] 8D (rendered 2026-11-27)
- [x] 9A (rendered 2026-11-27)
- [x] 9B (rendered 2026-11-27)
- [x] 9C (rendered 2026-11-27)
- [x] 9D (rendered 2026-11-27)
- [x] 9E (rendered 2026-11-27)
- [x] 10A (rendered 2026-11-27)
- [x] 10B (rendered 2026-11-27)
- [x] 10C (rendered 2026-11-27)
- [x] 10D (rendered 2026-11-27)
- [x] 10E (rendered 2026-11-27)
- [x] 10F (rendered 2026-11-27)

## Owner decision (Nov 27)
- Keep Thai voices for the film. After the Thai film is finished, make an English dub version (new English TTS voices laid over the existing picture, no re-render).

## Owner requests for after the Thai render (Nov 27), in this order
1. Send the owner the full Thai mp4 first (finish.py), as a file in chat.
2. Fix confusing actions, then re-render only those shots:
   - 1K: show Andy's glass tipping, falling and the wine landing on the old stain (clear slow-mo insert).
   - 3C: show Do's elbow actually hitting Martin's nose (contact frame, then cut).
   - 2B: make the "invisible punch" read clearly (sharper head snap, blood appears on cue).
   - Watch the whole film for other unclear moments and fix them too.
3. English dub: expressive English neural voices, tuned per line for emotion (rate/pitch/volume), laid over the picture.
- Notify the owner every time a scene finishes rendering, with % left (render_queue.sh now exits 4 on "SCENE n COMPLETE").

## Thai film finished (Nov 27)
- output/the_stain_th_burned.mp4 (Thai subs), output/the_stain_en_burned.mp4 (English subs), output/the_stain_final.mp4 (clean master, CRF 22 to stay under 100 MB). Sent to owner.
- Next: shot fixes (1K, 3C, 2B + full watch-through), then English dub.

## Final delivery (2026-11-27)
- All clarity fixes re-rendered: 1K (glass spill), 2B & 3C (elbow to nose), 7A (gun shown), 7B (gun lands on rug), 8A, 8B, 4C, 5A, 9C.
- English dub done: output/the_stain_english_dub.mp4. Thai with subs: output/the_stain_th_burned.mp4. Also the_stain_final.mp4 (no subs) and the_stain_en_burned.mp4 (Thai voices, English subs).
