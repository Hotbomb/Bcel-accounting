# Full soundtrack from timeline.json -> audio/mix/full_mix.wav (+ stems). Also usable as the radio-play cut.
import json, os, sys, numpy as np, soundfile as sf, subprocess
EN = "--en" in sys.argv  # English dub: same mix, English voices from audio/vo_en/
from scipy.signal import butter, sosfilt, fftconvolve
SR = 48000
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
tl = json.load(open(os.path.join(ROOT, "timeline.json")))
total = tl[-1]["start"] + tl[-1]["dur"]
N = int(total * SR) + SR
dlg, fx, amb, hum, mus = (np.zeros(N) for _ in range(5))
rng = np.random.default_rng(3)

def load(p):
    x, sr = sf.read(p, always_2d=True); x = x.mean(1)
    if sr != SR:
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-ar", str(SR), "-ac", "1", "/tmp/_rs.wav"])
        x, _ = sf.read("/tmp/_rs.wav")
    return x
def db(x): return 10 ** (x / 20)
def filt(x, kind, f): return sosfilt(butter(2, f, kind, fs=SR, output="sos"), x)
def put(bus, x, at, g=1.0):
    i = int(at * SR)
    if i >= N: return
    j = min(N, i + len(x)); bus[i:j] += x[: j - i] * g
def rms_norm(x, target_db):
    r = np.sqrt(np.mean(x[np.abs(x) > 1e-3] ** 2)) + 1e-9
    return x * db(target_db) / r
room_ir = rng.normal(0, 1, int(SR * 0.6)) * np.exp(-np.arange(int(SR * 0.6)) / SR * 9)
room_ir /= np.abs(room_ir).sum() / 8

by_id = {s["id"]: s for s in tl}
def T(sid, t=0.0): return by_id[sid]["start"] + t

# ---------- dialogue ----------
for s in tl:
    for l in s["lines"]:
        f = l["file"].replace("audio/vo/", "audio/vo_en/") if EN else l["file"]
        x = rms_norm(load(os.path.join(ROOT, f)), -20)
        if "os" in l["flags"]:
            x = filt(x, "low", 3500) * 0.6
        wet = fftconvolve(x, room_ir)[: len(x) + SR // 2]
        x = np.concatenate([x, np.zeros(SR // 2)]) + 0.12 * wet
        g = 1.0
        if s["scene"] >= 7: g = 1.15  # near silence around them: voices closer
        put(dlg, x, s["start"] + l["start"], g)

# ---------- sfx ----------
GAIN = {"laughter": -6, "cheer": -6, "gunshot": 2, "ringing": -10, "song_clean": 0, "breath": -12, "footsteps": -10,
        "amb": 0, "clock_tick": -20, "cloth_settle": -10, "cork_screw": -12, "pour": -10, "bulb_flicker": -14,
        "scuffle": -6, "whoosh": -12, "glass_clink": -8, "curtain_rings": -6, "laugh_broken": -4, "phone_buzz": -12}
song = load(os.path.join(ROOT, "assets", "song.wav"))
markers = json.load(open(os.path.join(ROOT, "assets", "song_markers.json")))
for s in tl:
    for e in s["sfx"]:
        n, at = e["name"], s["start"] + e["at"]
        if n in ("black", "silence", "room_act1", "city_cut", "clock_tick"): continue
        if n == "song_clean":  # from the party speaker: small-speaker EQ, cut by the skip
            seg = song[int(markers["hookA"] * SR): int((markers["hookA"] + 3.45) * SR)]
            seg = filt(filt(seg, "high", 250), "low", 6000) * 0.5
            seg[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
            put(fx, seg, at); continue
        if n == "bday_tune":  # public-domain birthday melody on a music box
            notes = [("G4", .75), ("G4", .25), ("A4", 1), ("G4", 1), ("C5", 1), ("B4", 2), ("G4", .75), ("G4", .25), ("A4", 1), ("G4", 1), ("D5", 1), ("C5", 2)]
            NT = {"G4": 392.0, "A4": 440.0, "B4": 493.9, "C5": 523.3, "D5": 587.3}
            t0 = at
            for nm, b in notes:
                d = b * 0.42; tt = np.arange(int(SR * (d + 1))) / SR
                put(fx, (np.sin(2 * np.pi * NT[nm] * 2 * tt) + 0.3 * np.sin(2 * np.pi * NT[nm] * 4 * tt)) * np.exp(-tt * 4) * 0.08, t0)
                t0 += d
            continue
        x = load(os.path.join(ROOT, "audio", "sfx", n + ".wav"))
        put(fx, x * 0.5, at, db(GAIN.get(n, -3)))

# ---------- hum ----------
# (shot where it starts, file, until shot (exclusive, start of), gain dB)
HUMS = [("0-0", 1, "0C", -4), ("2A", 2, "3A", -6), ("4A", 3, "5B", -7), ("5B", 4, "7A", -8),
        ("7A", 4, "9A", -9), ("9A", 5, "10E", -6), ("10E", 6, "CREDITS", -2)]
for start, n, until, g in HUMS:
    h = load(os.path.join(ROOT, "audio", "hum", f"hum_{n}.wav"))
    a, b = T(start), T(until)
    seg = h[: int((b - a) * SR)].copy()
    f = int(min(2.5, (b - a) / 3) * SR)
    if start != "0-0": seg[:f] *= np.linspace(0, 1, f) ** 2
    seg[-f:] *= np.linspace(1, 0, f) ** 2
    put(hum, seg, a, db(g))
# 2A: hum rises out of nowhere then stops
a = T("2A"); i0, i1 = int(a * SR), int((a + by_id["2A"]["dur"]) * SR)
hum[i0:i1] *= np.linspace(0.3, 1.6, i1 - i0)
hum[i1:int(T("3A") * SR)] *= 0.35

# ---------- ambience ----------
def loop(name, a, b, g):
    x = load(os.path.join(ROOT, "audio", "sfx", name + ".wav"))
    n = int((b - a) * SR); y = np.tile(x, n // len(x) + 1)[:n]
    f = min(int(SR * 0.05), n // 2); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    put(amb, y, a, db(g))
city_end = T("4E", next(e["at"] for e in by_id["4E"]["sfx"] if e["name"] == "city_cut"))
loop("amb_city", T("0A"), T("0C"), -26); loop("amb_city", T("1A"), city_end, -22)
loop("amb_fridge", T("0A"), T("CREDITS"), -34)
loop("amb_clock", T("0A"), city_end, -34); loop("amb_clock", city_end, T("7A"), -27); loop("amb_clock", T("7A"), T("CREDITS"), -23)
# black shots and the title: silence except hum
for sid in ("0C",):
    a, b = int(T(sid) * SR), int((T(sid) + by_id[sid]["dur"]) * SR); amb[a:b] = 0
# 3D: total silence
a, b = int(T("3D") * SR), int((T("3D") + by_id["3D"]["dur"]) * SR)
for bus in (amb, hum, fx): bus[a:b] *= 0.0

# ---------- credits: the full song ----------
put(mus, song, T("CREDITS"), 0.9)

# ---------- level balance (reference = dialogue) ----------
def arms(x):
    a = np.abs(x) > 1e-4
    return np.sqrt(np.mean(x[a] ** 2)) + 1e-9 if a.any() else 1e-9
ref = arms(dlg)
for name, bus in (("dlg", dlg), ("fx", fx), ("amb", amb), ("hum", hum), ("mus", mus)):
    print(f"{name}: {20*np.log10(arms(bus)/ref):+.1f} dB vs dialogue")
mus *= ref * db(-1) / arms(mus)
hum *= ref * db(-12) / arms(hum)
amb *= ref * db(-20) / arms(amb)
# ---------- bus + 8C muffle ----------
mix = dlg + fx + amb + hum + mus
g0 = T("8C") + 0.12; g1 = g0 + 3.2
a, b = int(g0 * SR), int(g1 * SR)
ring = load(os.path.join(ROOT, "audio", "sfx", "ringing.wav")) * 0.5 * db(-10)
rest = mix[a:b] - np.pad(ring, (0, max(0, b - a - len(ring))))[: b - a] * 0
muff = filt(filt(rest, "low", 500), "low", 500) * 0.6
xf = np.linspace(0, 1, b - a)
mix[a:b] = muff * (1 - xf) + rest * xf

mix *= 0.3 / ref
mix = np.tanh(mix * 1.0)  # soft limiter: keeps the gunshot from flattening everything
os.makedirs(os.path.join(ROOT, "audio", "mix"), exist_ok=True)
raw = os.path.join(ROOT, "audio", "mix", "full_mix_raw.wav")
sf.write(raw, mix.astype(np.float32), SR)
out = os.path.join(ROOT, "audio", "mix", "full_mix_en.wav" if EN else "full_mix.wav")
subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.0:LRA=14", "-ar", str(SR), "-ac", "2", out])
os.remove(raw)
print("mix", round(total, 1), "s ->", out)
