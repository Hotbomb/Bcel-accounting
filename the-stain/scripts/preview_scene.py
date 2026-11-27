# Preview a stretch of the film (graded, matted, with the final mix and burned subtitles) while rendering continues.
# Usage: python3 scripts/preview_scene.py <first_shot> <last_shot> <out.mp4> [th|en]
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finish as F
first, last, out = sys.argv[1:4]; lang = sys.argv[4] if len(sys.argv) > 4 else "en"
ids = [s["id"] for s in F.TL]; sel = F.TL[ids.index(first):ids.index(last) + 1]
parts = []
for s in sel:
    sid = s["id"]; p = f"{F.TMP}/{sid}.mp4"; parts.append(p)
    if sid == "0-0": F.black(p, s["dur"]); continue
    if sid == "0C": F.black(p, s["dur"], [("THE STAIN", F.FONT_LAT, 72, "(h/2)-70"), ("รอยเปื้อน", F.FONT_TH, 46, "(h/2)+20")], fade=0.6); continue
    vf = F.shot_filter(s)
    if sid == "8C": vf = "drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:enable='lt(n,3)'," + vf
    F.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"clips/{sid}.mp4", "-vf", vf, "-t", f"{s['dur']:.4f}", "-r", str(F.FPS),
           "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p", p])
lst = f"{F.TMP}/plist.txt"; open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
F.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", f"{F.TMP}/ppic.mp4"])
t0 = sel[0]["start"]; dur = sum(s["dur"] for s in sel)
F.subtitles()
srt = f"{F.TMP}/psub.srt"  # shift subtitles to the preview's start
F.run(["ffmpeg", "-y", "-loglevel", "error", "-itsoffset", f"-{t0}", "-i", f"output/the_stain_{lang}.srt", srt])
style = "FontName=Noto Sans Thai,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=1.4,Shadow=0,MarginV=24"
F.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{F.TMP}/ppic.mp4", "-ss", str(t0), "-t", str(dur), "-i", "audio/mix/full_mix.wav",
       "-map", "0:v", "-map", "1:a", "-vf", f"subtitles={srt}:force_style='{style}',fade=t=out:st={dur-1.5}:d=1.5", "-af", f"afade=t=out:st={dur-1.5}:d=1.5",
       "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out])
print(out, round(os.path.getsize(out) / 1e6, 1), "MB")
