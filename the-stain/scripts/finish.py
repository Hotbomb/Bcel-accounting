# Phase 6: finishing. Mattes, grade, grain, titles, credits, subtitles, final mix -> output/
# Usage: python3 scripts/finish.py [--partial]   (--partial: use black placeholders for shots not rendered yet)
import json, os, subprocess, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(ROOT)
TL = json.load(open("timeline.json"))
PARTIAL = "--partial" in sys.argv
W, H, FPS = 1280, 720, 24
TMP = "renders/finish"; os.makedirs(TMP, exist_ok=True); os.makedirs("output", exist_ok=True)
FONT_TH = "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf"
FONT_LAT = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/tlwg/Waree.ttf"
def run(cmd): subprocess.check_call(cmd, shell=isinstance(cmd, str))

def bar(m):  # letterbox (top/bottom) or pillarbox (sides) size for a ratio
    if m >= W / H: return ("lb", round((H - W / m) / 2))
    return ("pb", round((W - H * m) / 2))

GRADE = {  # per act: warm -> neutral/desaturating -> cold green
    1: "colorbalance=rs=0.03:gs=0.0:bs=-0.04:rm=0.04:bm=-0.03,eq=saturation=1.05",
    2: "colorbalance=rs=0.0:bs=0.0,eq=saturation=0.82",
    3: "colorbalance=rs=-0.03:gs=0.02:bs=0.02:rm=-0.03:gm=0.02,eq=saturation=0.72",
    4: "colorbalance=rs=-0.05:gs=0.03:bs=0.03:rm=-0.04:gm=0.03:bm=0.02,eq=saturation=0.65:contrast=1.04",
}
POST = "vignette=angle=0.55,noise=alls=5:allf=t+u"

def shot_filter(s):
    act = s["act"]; m = s["matte"]; f = [GRADE[act], POST]
    if isinstance(m, str):  # "2.39>1.85": mattes slide in as the curtains close (0.6s..2.2s)
        a, b = [float(x) for x in m.split(">")]; ha, hb = bar(a)[1], bar(b)[1]
        steps = [(0.0, 0.6, ha)] + [(0.6 + 1.6 * k / 20, 0.6 + 1.6 * (k + 1) / 20, round(ha + (hb - ha) * (k + 0.5) / 20)) for k in range(20)] + [(2.2, 9999, hb)]
        for t0, t1, h in steps:
            if h > 0:
                en = f"enable='between(t,{t0:.3f},{t1:.3f})'"
                f += [f"drawbox=x=0:y=0:w=iw:h={h}:color=black:t=fill:{en}", f"drawbox=x=0:y=ih-{h}:w=iw:h={h}:color=black:t=fill:{en}"]
    else:
        kind, n = bar(m)
        if n > 0:
            if kind == "lb": f += [f"drawbox=x=0:y=0:w=iw:h={n}:color=black:t=fill", f"drawbox=x=0:y=ih-{n}:w=iw:h={n}:color=black:t=fill"]
            else: f += [f"drawbox=x=0:y=0:w={n}:h=ih:color=black:t=fill", f"drawbox=x=iw-{n}:y=0:w={n}:h=ih:color=black:t=fill"]
    return ",".join(f)

def esc(t): return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’")

def black(out, dur, text_lines=(), fade=0.0):
    vf = []
    for (txt, font, size, y) in text_lines:
        vf.append(f"drawtext=fontfile={font}:text='{esc(txt)}':fontcolor=white@0.92:fontsize={size}:x=(w-text_w)/2:y={y}")
    if fade:
        vf.append(f"fade=t=in:st=0:d={fade},fade=t=out:st={max(0, dur - fade)}:d={fade}")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=black:s={W}x{H}:r={FPS}:d={dur}"] +
        (["-vf", ",".join(vf)] if vf else []) + ["-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", out])

def credits(out, dur):
    roll = ["THE STAIN", "รอยเปื้อน", "", "MARTIN  ·  มาร์ติน", "DAO  ·  ดาว", "ANDY  ·  แอนดี้", "DO  ·  โด้", "",
            "Written, directed and designed by the filmmaker", "Made in code with Blender, ffmpeg and Python", "Thai voices: Microsoft Edge neural TTS",
            "Original music composed in code", "", "After Sartre's Huis Clos", "", "ขอให้คืนนี้ไม่มีวันจบ"]
    txtfile = os.path.abspath(f"{TMP}/credits.txt"); open(txtfile, "w").write("\n".join(roll))
    title_end = 8.0
    vf = (f"drawtext=fontfile={FONT_LAT}:text='THE STAIN':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=(h/2)-60:enable='lt(t,{title_end})',"
          f"drawtext=fontfile={FONT_TH}:text='รอยเปื้อน':fontcolor=white@0.85:fontsize=44:x=(w-text_w)/2:y=(h/2)+20:enable='lt(t,{title_end})',"
          f"drawtext=fontfile={FONT_REG}:textfile={txtfile}:fontcolor=white@0.9:fontsize=30:line_spacing=18:x=(w-text_w)/2:"
          f"y=h-(t-{title_end})*{(H + 1100) / (dur - title_end - 6):.3f}:enable='gte(t,{title_end})',"
          f"fade=t=in:st=0:d=2,fade=t=out:st={dur - 3}:d=3")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=black:s={W}x{H}:r={FPS}:d={dur}", "-vf", vf,
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", out])

def srt_time(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def subtitles():
    for lang in ("th", "en"):
        out, k = [], 1
        for s in TL:
            for l in s["lines"]:
                a = s["start"] + l["start"]; b = s["start"] + l["end"] + 0.35
                out.append(f"{k}\n{srt_time(a)} --> {srt_time(b)}\n{l[lang]}\n"); k += 1
        open(f"output/the_stain_{lang}.srt", "w").write("\n".join(out))

def main():
    parts = []
    for s in TL:
        sid = s["id"]; out = f"{TMP}/{sid}.mp4"; parts.append(out)
        if sid == "0-0": black(out, s["dur"]); continue
        if sid == "0C":
            black(out, s["dur"], [("THE STAIN", FONT_LAT, 72, "(h/2)-70"), ("รอยเปื้อน", FONT_TH, 46, "(h/2)+20")], fade=0.6); continue
        if sid == "CREDITS": credits(out, s["dur"]); continue
        clip = f"clips/{sid}.mp4"
        if not os.path.exists(clip):
            if not PARTIAL: sys.exit(f"missing {clip}")
            black(out, s["dur"], [(f"[{sid} not rendered yet]", FONT_LAT, 28, "(h/2)")]); continue
        vf = shot_filter(s)
        if sid == "8C": vf = "drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:enable='lt(n,3)'," + vf
        if sid == "10F": vf += f",fade=t=out:st={s['dur'] - 2.5}:d=2.5"
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", clip, "-vf", vf, "-t", f"{s['dur']:.4f}", "-r", str(FPS),
             "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p", out])
    lst = f"{TMP}/list.txt"; open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", f"{TMP}/picture.mp4"])
    subtitles()
    mix = "audio/mix/full_mix.wav"
    final = "output/the_stain_final.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{TMP}/picture.mp4", "-i", mix, "-map", "0:v", "-map", "1:a",
         "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", final])
    style = "FontName=Noto Sans Thai,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=1.4,Shadow=0,MarginV=24"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", final, "-vf", f"subtitles=output/the_stain_th.srt:force_style='{style}'",
         "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", "output/the_stain_th_burned.mp4"])
    outs = [final, "output/the_stain_th_burned.mp4"]
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", final, "-vf", f"subtitles=output/the_stain_en.srt:force_style='{style}'",
         "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", "output/the_stain_en_burned.mp4"])
    outs.append("output/the_stain_en_burned.mp4")
    if os.path.exists("audio/mix/full_mix_en.wav"):  # English dub: same picture, English voices
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", final, "-i", "audio/mix/full_mix_en.wav", "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", "output/the_stain_english_dub.mp4"])
        outs.append("output/the_stain_english_dub.mp4")
    for f in outs:
        print(f, round(os.path.getsize(f) / 1e6, 1), "MB")

if __name__ == "__main__":
    main()
