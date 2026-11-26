# Original song for THE STAIN, synthesized in code (no samples, no downloads).
# D minor, 66 bpm. Piano melody + string pad + bass + reverb.  -> assets/song.wav (48 kHz stereo)
import numpy as np, soundfile as sf, os
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
BPM = 66.0
BEAT = 60.0 / BPM
rng = np.random.default_rng(7)
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}
def hz(name):
    n, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((NOTE[n] + 12 * (o + 1) - 69) / 12)

def piano(f, dur, vel=0.6):
    n = int(SR * (dur + 2.5)); t = np.arange(n) / SR
    out = np.zeros(n)
    for h in range(1, 9):
        fh = f * h * np.sqrt(1 + 0.0004 * h * h)
        amp = vel / (h ** 1.4)
        decay = 1.2 + 0.6 * h
        out += amp * np.sin(2 * np.pi * fh * t + rng.random() * 6) * np.exp(-t * decay / (1 + f / 900))
    att = np.minimum(1, t / 0.004)
    rel = np.where(t > dur, np.exp(-(t - dur) * 6), 1.0)
    return out * att * rel * 0.35

def pad(freqs, dur, vol=0.12):
    n = int(SR * (dur + 1.5)); t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):
            ff = f * 2 ** (det / 12)
            ph = rng.random()
            saw = 2 * ((ff * t + ph) % 1) - 1
            out += saw
    sos = butter(2, 1400, "low", fs=SR, output="sos")
    out = sosfilt(sos, out) / (len(freqs) * 3)
    env = np.minimum(1, t / 0.9) * np.where(t > dur, np.exp(-(t - dur) * 2.5), 1.0)
    return out * env * vol

def bass(f, dur):
    n = int(SR * (dur + 1)); t = np.arange(n) / SR
    out = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    env = np.minimum(1, t / 0.02) * np.exp(-t * 0.5) * np.where(t > dur, np.exp(-(t - dur) * 8), 1.0)
    return out * env * 0.16

CH = {  # chord tones
    "Dm": ["D3", "F3", "A3"], "Bb": ["A#2", "D3", "F3"], "F": ["F3", "A3", "C4"], "C": ["C3", "E3", "G3"],
    "Gm": ["G2", "A#2", "D3"], "A": ["A2", "C#3", "E3"], "Am": ["A2", "C3", "E3"],
}
ROOT = {"Dm": "D2", "Bb": "A#1", "F": "F2", "C": "C2", "Gm": "G1", "A": "A1", "Am": "A1"}

# Melody: (note or None, beats). The motif "A4 D5 C5 A4 . G4 F4 E4 F4" is the hook the hum quotes.
HOOK = [("A4", 1), ("D5", 1), ("C5", 1), ("A4", 3), ("G4", 1), ("F4", 1), ("E4", 1), ("F4", 3)]
HOOK2 = [("A4", 1), ("D5", 1), ("C5", 1), ("A4", 2), ("F4", 1), ("G4", 1), ("A4", 1), ("E4", 4), (None, 2)]
VERSE = [("D4", 1), ("F4", 1), ("A4", 2), ("G4", 1), ("F4", 1), ("E4", 2),
         ("C4", 1), ("E4", 1), ("G4", 2), ("F4", 1), ("E4", 1), ("D4", 2),
         ("D4", 1), ("F4", 1), ("A4", 2), ("A#4", 1), ("A4", 1), ("G4", 2),
         ("F4", 1), ("E4", 1), ("C#4", 2), ("D4", 4)]
BRIDGE = [("F5", 2), ("E5", 1), ("D5", 1), ("C5", 3), ("A4", 1),
          ("A#4", 2), ("A4", 1), ("G4", 1), ("F4", 3), ("D4", 1),
          ("G4", 2), ("A4", 1), ("A#4", 1), ("C5", 2), ("D5", 2),
          ("E5", 3), ("C#5", 1), ("D5", 4)]

def seq_len(s): return sum(b for _, b in s)
# sections: (name, melody, chords per 4 beats, piano arpeggio on?)
SECTIONS = [
    ("intro", [(None, 16)], ["Dm", "Bb", "F", "C"], True),
    ("hookA", HOOK + HOOK2, ["Dm", "Bb", "F", "C", "Dm", "Bb", "Gm", "A"], True),
    ("verse", VERSE, ["Dm", "C", "Bb", "A", "Dm", "Gm", "A", "Dm"], True),
    ("hookB", HOOK + HOOK2, ["Dm", "Bb", "F", "C", "Dm", "Bb", "Gm", "A"], True),
    ("bridge", BRIDGE, ["Bb", "F", "Gm", "Dm", "Gm", "Am", "A", "Dm"], True),
    ("hookC", HOOK + HOOK2, ["Dm", "Bb", "F", "C", "Dm", "Bb", "Gm", "A"], True),
    ("outro", HOOK[:5] + [(None, 2), ("D4", 8)], ["Dm", "Bb", "Dm", "Dm"], False),
]
total_beats = sum(max(seq_len(m), 4 * len(c)) for _, m, c, _ in SECTIONS)
N = int(SR * (total_beats * BEAT + 8))
L = np.zeros(N); R = np.zeros(N)
def put(sig, at, pan=0.0, gain=1.0):
    i = int(at * SR); j = min(N, i + len(sig)); s = sig[: j - i] * gain
    L[i:j] += s * np.sqrt(0.5 * (1 - pan)); R[i:j] += s * np.sqrt(0.5 * (1 + pan))

markers = {}
beat = 0.0
for name, mel, chords, arp in SECTIONS:
    markers[name] = beat * BEAT
    sec_beats = max(seq_len(mel), 4 * len(chords))
    loud = {"intro": 0.7, "hookA": 0.85, "verse": 0.8, "hookB": 1.0, "bridge": 1.05, "hookC": 1.1, "outro": 0.7}[name]
    for k, ch in enumerate(chords):
        t0 = (beat + 4 * k) * BEAT
        put(pad([hz(x) for x in CH[ch]] + [hz(CH[ch][0][:-1] + str(int(CH[ch][0][-1]) + 1))], 4 * BEAT, 0.10 * loud), t0, 0.0)
        put(bass(hz(ROOT[ch]), 4 * BEAT), t0, 0.0, loud)
        if arp:
            tones = CH[ch] + [CH[ch][1][:-1] + str(int(CH[ch][1][-1]) + 1)]
            for q in range(8):
                nt = tones[[0, 2, 1, 3, 2, 1, 3, 2][q]]
                put(piano(hz(nt), BEAT * 0.5, 0.28 * loud), t0 + q * BEAT * 0.5, -0.3 + 0.1 * (q % 3))
    t = beat * BEAT
    for nt, b in mel:
        if nt:
            put(piano(hz(nt), b * BEAT * 0.95, 0.75 * loud), t + rng.normal(0, 0.006), 0.15)
            put(pad([hz(nt)], b * BEAT, 0.05 * loud), t, 0.2)  # string doubling: makes the melody sustain (good for the hum)
        t += b * BEAT
    beat += sec_beats

# reverb
ir_n = int(SR * 3.2); tir = np.arange(ir_n) / SR
ir = rng.normal(0, 1, (2, ir_n)) * np.exp(-tir * 2.2)
ir[:, : int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
wetL = fftconvolve(L, ir[0])[:N]; wetR = fftconvolve(R, ir[1])[:N]
mix = np.stack([L + 0.12 * wetL / np.abs(ir[0]).sum() * 60, R + 0.12 * wetR / np.abs(ir[1]).sum() * 60], 1)
mix /= np.abs(mix).max() * 1.12
end = int(SR * (total_beats * BEAT + 6)); mix = mix[:end]
fade = int(SR * 4); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets"); os.makedirs(here, exist_ok=True)
sf.write(os.path.join(here, "song.wav"), mix.astype(np.float32), SR, subtype="PCM_24")
import json; json.dump({k: round(v, 3) for k, v in markers.items()}, open(os.path.join(here, "song_markers.json"), "w"), indent=1)
print("song", round(len(mix) / SR, 1), "s", markers)
