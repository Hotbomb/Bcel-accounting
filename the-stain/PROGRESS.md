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
- [ ] 4C (72 unique frames)
- [ ] 4D (72 unique frames)
- [ ] 4E (192 unique frames)
- [ ] 4F (144 unique frames)
- [ ] 5A (96 unique frames)
- [ ] 5B (72 unique frames)
- [ ] 5C (36 unique frames)
- [ ] 5D (72 unique frames)
- [ ] 6A (96 unique frames)
- [ ] 6B (192 unique frames)
- [ ] 6C (216 unique frames)
- [ ] 6D (216 unique frames)
- [ ] 6E (168 unique frames)
- [ ] 7A (120 unique frames)
- [ ] 7B (72 unique frames)
- [ ] 7C (96 unique frames)
- [ ] 8A (60 unique frames)
- [ ] 8B (60 unique frames)
- [ ] 8C (72 unique frames)
- [ ] 8D (168 unique frames)
- [ ] 9A (96 unique frames)
- [ ] 9B (96 unique frames)
- [ ] 9C (72 unique frames)
- [ ] 9D (192 unique frames)
- [ ] 9E (120 unique frames)
- [ ] 10A (168 unique frames)
- [ ] 10B (96 unique frames)
- [ ] 10C (144 unique frames)
- [ ] 10D (120 unique frames)
- [ ] 10E (144 unique frames)
- [ ] 10F (96 unique frames)
