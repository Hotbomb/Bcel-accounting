# English dub: every line as audio/vo_en/<shot>_<char>_<n>.wav, acted per line (speed / pitch / loudness + phrasing).
# Lines are fitted to the Thai timing (sped up a little if needed) so the dub sits on the same picture.
import asyncio, json, os, subprocess
import edge_tts
os.environ.setdefault("SSL_CERT_FILE", "/root/.ccr/ca-bundle.crt")
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "audio", "vo_en"); os.makedirs(OUT, exist_ok=True)
TMP = "/tmp/vo_en_tmp"; os.makedirs(TMP, exist_ok=True)

CAST = {  # voice, base pitch (Hz), base rate (%)
    "martin": ("en-US-ChristopherNeural", -2, -2),
    "dao":    ("en-US-AvaMultilingualNeural", 0, -2),
    "andy":   ("en-US-BrianMultilingualNeural", -5, -4),
    "do":     ("en-US-GuyNeural", +3, +4),
}
# acting presets: (rate %, pitch Hz, volume %)
N, TENSE, COLD, CALM = (0, 0, 0), (-4, -2, 0), (-10, -4, -5), (-8, -3, -5)
JOLLY, SMUG, ANGRY, SHOUT = (6, 6, 10), (2, 4, 5), (8, 4, 20), (12, 8, 35)
SCARED, PLEAD, SAD, EERIE, WHISPER = (6, 5, -5), (-4, 4, -5), (-12, -5, -10), (-12, -3, -10), (-10, -2, -25)
ACT = {
    "0A|0": CALM, "0B|0": (0, 2, 0), "0B|1": COLD,
    "1A|0": (4, 6, 5), "1C|0": TENSE, "1C|1": N, "1C|2": JOLLY,
    "1D|0": (4, 3, 0), "1D|1": (10, 0, 0),
    "1E|0": (-6, 2, 0), "1E|1": JOLLY, "1E|2": (5, 5, 20),
    "1F|0": (2, 0, 0), "1F|1": (4, 0, -5),
    "1H|0": TENSE, "1H|1": N, "1H|2": JOLLY,
    "1I|0": (-10, 4, 0), "1I|1": (-12, 2, -5), "1I|2": (-10, -4, -10),
    "1J|0": (2, 3, 5), "1J|1": SHOUT, "1J|2": (-5, 0, 0),
    "1K|0": COLD, "1K|1": COLD,
    "2B|0": SHOUT, "2C|0": TENSE, "2C|1": (6, 3, 10),
    "3A|0": SMUG, "3B|0": (-4, -3, 15), "3B|1": (-10, -2, 0),
    "3E|0": EERIE, "3E|1": (4, 2, 5), "3E|2": EERIE, "3F|0": (6, 0, 10),
    "4A|0": (4, 4, 20), "4C|0": (8, 6, 15), "4C|1": (14, 10, 40), "4D|0": (-6, -3, -15),
    "4E|0": WHISPER, "4E|1": EERIE, "4E|2": (-14, -4, -15),
    "4F|0": ANGRY, "4F|1": (4, 3, 10), "4F|2": TENSE,
    "5A|0": WHISPER, "5B|0": (5, 4, 0), "5D|0": (4, 3, 10),
    "6A|0": (-6, -4, 5), "6B|0": SHOUT, "6B|1": COLD, "6B|2": (-8, 2, -15), "6B|3": COLD,
    "6C|0": (6, 5, 20), "6C|1": TENSE, "6C|2": (-4, 2, 5),
    "6D|0": TENSE, "6D|1": ANGRY, "6D|2": ANGRY, "6D|3": ANGRY,
    "6E|0": SCARED, "6E|1": PLEAD, "6E|2": (-10, -4, -5),
    "7A|0": (-4, 0, -10), "7A|1": COLD, "8A|0": (-8, -4, 0), "8B|0": SHOUT,
    "8D|0": (-14, -2, -15), "8D|1": (-6, -3, 0),
    "9B|0": (-10, 4, -15), "9C|0": WHISPER,
    "9D|0": SHOUT, "9D|1": (-2, 0, -5), "9D|2": (6, 6, 20), "9D|3": (6, 6, 20), "9D|4": (2, 6, 25),
    "10A|0": (-10, -3, -10), "10C|0": SAD, "10C|1": SAD,
}
# phrasing tweaks (punctuation drives the voice's rhythm and emphasis)
TEXT = {"2B|0": "Ow!! Who hit me?!", "4C|1": "WHO. HAS. A GUN?!", "9B|0": "I... I... haven't died yet.",
        "1I|0": "Happy birthday... happy birthday!", "1J|1": "One! Two! Three!", "1E|2": "Cheers!!",
        "9D|0": "Stay back!! All of you!", "8B|0": "What if you MISS?!", "6B|0": "Hey! Give that back!"}

def sgn(x, unit): return f"{'+' if x >= 0 else ''}{x}{unit}"

async def tts(char, text, act, out_wav):
    v, p0, r0 = CAST[char]; r, p, vol = act
    mp3 = os.path.join(TMP, os.path.basename(out_wav) + ".mp3")
    for attempt in range(8):
        try:
            c = edge_tts.Communicate(text, v, rate=sgn(r0 + r, "%"), pitch=sgn(p0 + p, "Hz"), volume=sgn(vol, "%"), proxy=PROXY)
            await c.save(mp3)
            if os.path.getsize(mp3) > 0:
                subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-af",
                    "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse",
                    "-ar", "48000", "-ac", "1", out_wav])
                return
        except Exception:
            pass
        await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"TTS failed: {out_wav}")

def dur(p): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

def fit(path, room):
    """Speed a line up (max 1.35x) if it runs past the room it has before the next line / end of shot."""
    d = dur(path)
    if d <= room: return d, 1.0
    k = min(1.35, d / room); tmp = path + ".fit.wav"
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-af", f"atempo={k:.3f}", tmp]); os.replace(tmp, path)
    return dur(path), k

async def job(sem, s, i, l, room):
    async with sem:
        key = f"{s['id']}|{i}"; act = ACT.get(key, N); text = TEXT.get(key, l["en"])
        out = os.path.join(OUT, f"{s['id']}_{l['char']}_{i}.wav")
        if not os.path.exists(out):
            if l["char"] == "all":
                parts = []
                for ch in CAST:
                    pw = os.path.join(TMP, f"{s['id']}_all_{i}_{ch}.wav")
                    if not os.path.exists(pw): await tts(ch, text, act, pw)
                    parts.append(pw)
                fc = "".join(f"[{k}]adelay={d}[a{k}];" for k, d in enumerate((0, 70, 140, 40))) + "".join(f"[a{k}]" for k in range(4)) + "amix=inputs=4:normalize=0,volume=0.6"
                subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error"] + sum([["-i", p] for p in parts], []) + ["-filter_complex", fc, "-ar", "48000", "-ac", "1", out])
            else:
                await tts(l["char"], text, act, out)
        d, k = fit(out, room)
        print(f"{key:7} {l['char']:6} {d:4.1f}s room {room:4.1f}s x{k:.2f}  {text}", flush=True)

async def main():
    tl = json.load(open(os.path.join(ROOT, "timeline.json")))
    sem = asyncio.Semaphore(3); jobs = []
    for s in tl:
        for i, l in enumerate(s["lines"]):
            nxt = s["lines"][i + 1]["start"] if i + 1 < len(s["lines"]) else s["dur"] + 0.6
            jobs.append(job(sem, s, i, l, max(l["end"] - l["start"] + 0.25, nxt - l["start"] - 0.1)))
    await asyncio.gather(*jobs)

if __name__ == "__main__":
    asyncio.run(main())
