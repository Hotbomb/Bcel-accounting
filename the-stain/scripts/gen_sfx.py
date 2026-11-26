# Synthesize all sound effects -> audio/sfx/<name>.wav (48 kHz mono). Laughter/cheers via the character voices.
import numpy as np, soundfile as sf, os, subprocess, asyncio, sys
from scipy.signal import butter, sosfilt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
SR = 48000
rng = np.random.default_rng(11)
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "audio", "sfx"); os.makedirs(OUT, exist_ok=True)

def T(d): return np.arange(int(SR * d)) / SR
def noise(d): return rng.normal(0, 1, int(SR * d))
def filt(x, kind, f, order=2):
    return sosfilt(butter(order, f, kind, fs=SR, output="sos"), x)
def env(t, a, d): return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def norm(x, peak=0.9): return x / (np.abs(x).max() + 1e-9) * peak
def pad(x, d):
    y = np.zeros(int(SR * d)); y[: len(x)] = x[: len(y)]; return y
def place(base, x, at):
    i = int(at * SR); j = min(len(base), i + len(x)); base[i:j] += x[: j - i]; return base
def save(name, x, peak=0.9): sf.write(os.path.join(OUT, name + ".wav"), norm(x, peak).astype(np.float32), SR)

def thud(d=0.5, f=70, dec=0.12):
    t = T(d); return np.sin(2 * np.pi * f * t * (1 - 0.3 * t)) * env(t, 0.002, dec) + 0.3 * filt(noise(d), "low", 400) * env(t, 0.001, 0.03)
def click(d=0.08, f=3000, dec=0.006):
    t = T(d); return filt(noise(d), "band", [f * 0.7, f * 1.3]) * env(t, 0.0003, dec)
def ring(f, d, dec):
    t = T(d); return sum(np.sin(2 * np.pi * f * k * 1.003 ** k * t) / k for k in (1, 2.76, 5.4)) * env(t, 0.001, dec)

S = {}
# cloth
t = T(0.35); S["cloth_snap"] = filt(noise(0.35), "band", [600, 5000]) * env(t, 0.01, 0.05)
t = T(1.6); S["cloth_settle"] = filt(noise(1.6), "band", [300, 3000]) * np.sin(np.pi * t / 1.6) ** 2 * 0.3
# bulb flicker: electrical buzz bursts
t = T(0.8); buzz = np.sign(np.sin(2 * np.pi * 100 * t)) * 0.3 + filt(noise(0.8), "high", 2000) * 0.2
gate = ((t > 0.05) & (t < 0.12)) | ((t > 0.2) & (t < 0.24)) | ((t > 0.33) & (t < 0.55))
S["bulb_flicker"] = filt(buzz * gate, "low", 6000) * 0.5 + click(0.8, 2500) * 0.5
S["song_skip"] = click(0.1, 1800, 0.01) + np.concatenate([click(0.05, 1200), np.zeros(int(SR * 0.05))])
S["glass_clink"] = sum(place(np.zeros(int(SR * 1.5)), ring(f, 1.2, 0.35), a) for f, a in [(2300, 0), (2650, 0.04), (2480, 0.09), (2900, 0.12)])
S["purse_thud"] = thud(0.7, 55, 0.18) + 0.4 * click(0.7, 900, 0.02)
t = T(1.6); S["cork_screw"] = filt(noise(1.6), "band", [1500, 4000]) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * t) ** 8) * 0.3
t = T(0.4); S["cork_pop"] = np.sin(2 * np.pi * 420 * t * np.exp(-t * 8)) * env(t, 0.0005, 0.03) + filt(noise(0.4), "band", [800, 6000]) * env(t, 0.001, 0.05) * 0.6
S["cork_glass"] = click(0.5, 4200, 0.01) + 0.6 * ring(3100, 0.5, 0.06)
t = T(0.8); S["blow_candles"] = filt(noise(0.8), "band", [300, 2500]) * np.sin(np.pi * t / 0.8) ** 1.5
S["glass_knock"] = place(click(0.6, 2500, 0.01) + 0.5 * ring(1900, 0.6, 0.1), thud(0.4, 120, 0.05), 0.12)
t = T(1.0); S["wine_splash"] = filt(noise(1.0), "band", [200, 2500]) * env(t, 0.005, 0.18) + filt(noise(1.0), "high", 3000) * env(t, 0.01, 0.08) * 0.3
S["punch_thud"] = thud(0.5, 85, 0.07) + 0.6 * filt(noise(0.5), "band", [200, 1500]) * env(T(0.5), 0.001, 0.025)
t = T(0.45); S["whoosh"] = filt(noise(0.45), "band", [400, 3000]) * np.sin(np.pi * t / 0.45) ** 3
t = T(0.9); S["chair_scrape"] = filt(noise(0.9) * (1 + np.sin(2 * np.pi * 37 * t)), "band", [250, 1800]) * np.sin(np.pi * t / 0.9) ** 0.5
S["silence"] = np.zeros(SR)
S["lamp_fall"] = place(place(np.zeros(int(SR * 1.6)), thud(0.8, 60, 0.2), 0.25), click(0.6, 3500, 0.03) + 0.4 * ring(1400, 0.6, 0.25), 0.27)
S["lock_click"] = place(click(0.3, 2200, 0.008), click(0.2, 1500, 0.01), 0.09)
t = T(1.4); S["curtain_rings"] = sum(place(np.zeros(int(SR * 1.4)), click(0.15, 3500 + rng.random() * 1500, 0.02) * 0.5, a) for a in np.sort(rng.random(14)) * 1.1) + filt(noise(1.4), "band", [400, 3000]) * np.sin(np.pi * t / 1.4) * 0.25
S["vase_set"] = place(thud(0.4, 200, 0.03) * 0.5, click(0.3, 1800, 0.01) * 0.6, 0.0)
S["box_open"] = place(click(0.3, 1300, 0.01), click(0.2, 2600, 0.006), 0.12)
t = T(0.6); S["purse_rip"] = filt(noise(0.6), "band", [500, 5000]) * env(t, 0.01, 0.15)
t = T(0.9); S["gun_slide"] = thud(0.4, 90, 0.05) * 0.7 + pad(filt(noise(0.9), "band", [300, 2000]) * env(t, 0.02, 0.3) * 0.5, 0.9)[: int(SR * 0.9)] if False else place(filt(noise(0.9), "band", [300, 2000]) * env(t, 0.02, 0.3) * 0.5, thud(0.4, 90, 0.05) * 0.7, 0)
sc = np.zeros(int(SR * 2.5))
for a in np.sort(rng.random(9)) * 2.2: place(sc, thud(0.3, 60 + rng.random() * 60, 0.06) * (0.5 + rng.random() * 0.5), a)
S["scuffle"] = sc + filt(noise(2.5), "band", [200, 2000]) * 0.08
S["vase_fall"] = place(place(np.zeros(int(SR * 1.2)), thud(0.5, 140, 0.05), 0.0), ring(900, 0.8, 0.15) * 0.5 + click(0.8, 2600, 0.02) * 0.4, 0.0)
sk = np.zeros(int(SR * 1.3))
for k, a in enumerate([0, 0.18, 0.33, 0.45, 0.55, 0.62]): place(sk, click(0.2, 1500, 0.02) * (1 - k * 0.12) + thud(0.2, 160, 0.02) * 0.4, a)
S["gun_skitter"] = sk
S["body_drop"] = thud(0.6, 50, 0.15) + filt(noise(0.6), "band", [100, 900]) * env(T(0.6), 0.003, 0.08) * 0.5
S["tackle"] = thud(0.7, 45, 0.2) + filt(noise(0.7), "band", [150, 1200]) * env(T(0.7), 0.003, 0.12) * 0.6
# gunshot: huge transient + low boom + room tail
t = T(2.0); g = filt(noise(2.0), "low", 8000) * env(t, 0.0002, 0.012) * 1.5 + np.sin(2 * np.pi * 55 * t) * env(t, 0.001, 0.15) + filt(noise(2.0), "band", [100, 1500]) * env(t, 0.01, 0.4) * 0.35
S["gunshot"] = g
t = T(4.0); S["ringing"] = (np.sin(2 * np.pi * 6200 * t) * 0.35 + np.sin(2 * np.pi * 6230 * t) * 0.2) * np.minimum(1, t / 0.05) * np.where(t > 3.0, np.exp(-(t - 3.0) * 4), 1)
br = np.zeros(int(SR * 8.0))
for a in np.arange(0, 7.4, 1.25): place(br, filt(noise(1.0), "band", [300, 1600]) * np.sin(np.pi * T(1.0) / 1.0) ** 2 * 0.3, a + rng.random() * 0.2)
S["breath"] = br
S["gun_drop_rug"] = thud(0.4, 110, 0.04) + click(0.4, 1100, 0.015) * 0.3
S["dive"] = place(filt(noise(0.5), "band", [300, 2500]) * np.sin(np.pi * T(0.5) / 0.5) ** 2 * 0.5, thud(0.6, 55, 0.15), 0.35)
fs_ = np.zeros(int(SR * 8.0))
for k in range(12): place(fs_, thud(0.25, 75, 0.04) * 0.8 + click(0.25, 900, 0.01) * 0.25, k * 0.62)
S["footsteps"] = fs_
t = T(2.0); S["door_open"] = place(filt(np.sin(2 * np.pi * (320 + 120 * np.sin(2 * np.pi * 1.3 * t)) * t) + 0.3 * noise(2.0), "band", [200, 1800]) * np.sin(np.pi * t / 2.0) * 0.3, click(0.2, 1200, 0.01), 0)
S["chair_right"] = place(S["chair_scrape"][: int(SR * 0.6)] * 0.6, thud(0.4, 70, 0.08), 0.5)
t = T(3.0); S["pour"] = filt(noise(3.0), "band", [400, 2200]) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t + 3 * np.sin(2 * np.pi * 0.7 * t))) * np.sin(np.pi * t / 3.0) ** 0.6 * 0.5
pb = np.zeros(int(SR * 1.6))
for a in (0, 0.9): place(pb, np.sin(2 * np.pi * 180 * T(0.45)) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 22 * T(0.45)))) * 0.5, a)
S["phone_buzz"] = pb
t = T(1.2); S["song_end_click"] = click(0.1, 1600)
# ambience loops (30 s)
t = T(30.0)
city = filt(np.cumsum(noise(30.0)) * 0.002, "high", 30) * 0.6 + filt(noise(30.0), "band", [150, 900]) * 0.05
for a in rng.random(6) * 26: place(city, filt(noise(4.0), "band", [80, 600]) * np.sin(np.pi * T(4.0) / 4.0) ** 2 * 0.3, a)
S["amb_city"] = city
S["amb_fridge"] = (np.sin(2 * np.pi * 50 * t) * 0.4 + np.sin(2 * np.pi * 100 * t) * 0.25 + np.sin(2 * np.pi * 150 * t) * 0.1) * (0.9 + 0.1 * np.sin(2 * np.pi * 0.13 * t)) + filt(noise(30.0), "low", 200) * 0.1
ck = np.zeros(int(SR * 30.0))
for k in range(30): place(ck, click(0.05, 3300 if k % 2 else 2900, 0.004), k * 1.0)
S["amb_clock"] = ck

for k, v in S.items(): save(k, v)

# ---- voice-based crowd sounds ----
from gen_voices import tts
CROWD = {
    "laughter": [("martin", "ฮ่า ฮ่า ฮ่า ฮ่า"), ("dao", "ฮ่า ฮ่า ฮ่า"), ("andy", "ฮ่า ฮ่า"), ("do", "ฮ่า ฮ่า ฮ่า ฮ่า ฮ่า")],
    "cheer": [("martin", "เย้!"), ("dao", "เย้!"), ("andy", "โอ้โห"), ("do", "เย้ เย้!")],
    "laugh_broken": [("dao", "ฮึ... ฮึ ฮึ..."), ("martin", "ฮ่า... ฮ่า...")],
}
TMP = "/tmp/sfx_tmp"; os.makedirs(TMP, exist_ok=True)
async def crowd():
    for name, parts in CROWD.items():
        files = []
        for ch, txt in parts:
            f = os.path.join(TMP, f"{name}_{ch}.wav")
            if not os.path.exists(f): await tts(ch, txt, f)
            files.append(f)
        delays = [0, 250, 450, 120][: len(files)]
        fc = "".join(f"[{k}]adelay={d}[a{k}];" for k, d in enumerate(delays)) + "".join(f"[a{k}]" for k in range(len(files))) + f"amix=inputs={len(files)}:normalize=0,volume=0.5"
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error"] + sum([["-i", f] for f in files], []) + ["-filter_complex", fc, "-ar", "48000", "-ac", "1", os.path.join(OUT, name + ".wav")])
asyncio.run(crowd())
print("sfx:", len(os.listdir(OUT)))
