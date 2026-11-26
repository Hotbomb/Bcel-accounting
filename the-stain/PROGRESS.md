# THE STAIN — Progress

## Where things live
- Repo: `hotbomb/bcel-accounting` (borrowed; unrelated to the banking app). All film files are in the `the-stain/` folder.
- Branch: `ccr-35112457-trui8i` (this cloud setup only allows pushing to this branch, so it replaces the brief's `film` branch). The banking app deploys from a different branch, so film work does not touch the live site.
- Cloud environment: `the-stain` (personal; allows `speech.platform.bing.com` for the Thai voices). Start new film sessions in this environment.

## Tool setup (each new session = fresh machine)
- Blender: `download.blender.org` is blocked, so Blender is installed from PyPI as the `bpy` module: `python3 -m venv /opt/bpyenv && /opt/bpyenv/bin/pip install bpy==5.2.5` (Blender **5.2.5 LTS**, not 4.2). Run scripts with `/opt/bpyenv/bin/python script.py` instead of `blender -b -P`.
- EEVEE/Workbench need `apt-get install -y libegl1 libgl1 libegl-mesa0 libgl1-mesa-dri`.
- Voices: `pip install --break-system-packages edge-tts`; edge-tts must be given the proxy explicitly (`scripts/tts.sh` does this) and the service is flaky, so the script retries.

## Phase 0 results (2026-11-26)
- Machine: 4 CPUs, 15 GB RAM, plenty of disk, no GPU. ffmpeg 7 present.
- Test render, simple room + clay figure, 1280×720:
  - Workbench: 1.2 s/frame (animatic only)
  - EEVEE: 16 s/frame (25 s first frame, shader compile)
  - Cycles CPU 16 samples + denoise: 9.3 s/frame
  - Cycles CPU 32 samples + denoise: 18.3 s/frame
- Thai voices: edge-tts works. Only 2 Thai voices exist: Niwat (male) and Premwadee (female). Martin, Andy and Do all use Niwat with pitch/rate offsets.
- Hum: `scripts/make_hum.sh` works (tested on a test tone). **Waiting for the song.**
- Estimate: ~8 min ≈ 5,800 unique frames. The full set (haze, more objects, depth of field) will be slower than the test: expect ~20–35 s/frame in Cycles 16 → roughly **32–56 hours** of rendering.

## Decisions
- (waiting for Phase 0 answers)

## Next
- Phase 0 questions sent to the user. Then Phase 1.
