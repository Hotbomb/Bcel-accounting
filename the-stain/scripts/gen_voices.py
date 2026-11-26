# Generate every dialogue line as audio/vo/<shot>_<char>_<n>.wav (48 kHz mono). Skips existing files.
import asyncio, json, os, subprocess, sys
import edge_tts
os.environ.setdefault("SSL_CERT_FILE", "/root/.ccr/ca-bundle.crt")
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
VOICES = {
    "martin": ("th-TH-NiwatNeural", "-6Hz", "-5%"),
    "dao":    ("th-TH-PremwadeeNeural", "-1Hz", "-5%"),
    "andy":   ("th-TH-NiwatNeural", "-14Hz", "-12%"),
    "do":     ("th-TH-NiwatNeural", "+10Hz", "+8%"),
}
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VO = os.path.join(ROOT, "audio", "vo"); os.makedirs(VO, exist_ok=True)
TMP = "/tmp/vo_tmp"; os.makedirs(TMP, exist_ok=True)

async def tts(char, text, out_wav):
    v, p, r = VOICES[char]
    mp3 = os.path.join(TMP, os.path.basename(out_wav) + ".mp3")
    for attempt in range(8):
        try:
            c = edge_tts.Communicate(text, v, pitch=p, rate=r, proxy=PROXY)
            await c.save(mp3)
            if os.path.getsize(mp3) > 0:
                subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3,
                    "-af", "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse",
                    "-ar", "48000", "-ac", "1", out_wav])
                return
        except Exception as e:
            pass
        await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"TTS failed: {out_wav}")

async def job(sem, shot, i, line):
    async with sem:
        base = os.path.join(VO, f"{shot}_{line['char']}_{i}.wav")
        if os.path.exists(base): return
        if line["char"] == "all":
            parts = []
            for ch in ("martin", "dao", "andy", "do"):
                pw = os.path.join(TMP, f"{shot}_all_{i}_{ch}.wav")
                if not os.path.exists(pw): await tts(ch, line["th"], pw)
                parts.append(pw)
            # mix with small human offsets
            delays = [0, 70, 140, 40]
            fc = "".join(f"[{k}]adelay={d}[a{k}];" for k, d in enumerate(delays)) + \
                 "".join(f"[a{k}]" for k in range(4)) + "amix=inputs=4:normalize=0,volume=0.6"
            cmd = ["ffmpeg", "-y", "-loglevel", "error"] + sum([["-i", p] for p in parts], []) + \
                  ["-filter_complex", fc, "-ar", "48000", "-ac", "1", base]
            subprocess.check_call(cmd)
        else:
            await tts(line["char"], line["th"], base)
        print("ok", os.path.basename(base), flush=True)

async def main():
    shots = json.load(open(os.path.join(ROOT, "shots.json")))
    sem = asyncio.Semaphore(3)
    await asyncio.gather(*[job(sem, s["id"], i, l) for s in shots for i, l in enumerate(s["lines"])])

if __name__ == "__main__":
    asyncio.run(main())
