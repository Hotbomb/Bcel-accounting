# Procedural textures and phone screens -> assets/tex/*.png  (system python: numpy, scipy, PIL)
import numpy as np, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import gaussian_filter
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "assets", "tex"); os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(5)
TH = "/usr/share/fonts/truetype/tlwg/Waree.ttf"
THB = "/usr/share/fonts/truetype/tlwg/Waree-Bold.ttf"
EMO = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
def save(a, name):
    Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).save(os.path.join(OUT, name))

# ---- night city with bokeh (seen through the window, out of focus) ----
W, H = 2048, 1024
img = np.zeros((H, W, 3))
sky = np.linspace(0.02, 0.07, H)[:, None]
img += sky[..., None] * np.array([0.5, 0.6, 1.0])
x = 0
while x < W:  # building silhouettes with lit windows
    bw = rng.integers(60, 200); bh = rng.integers(250, 800)
    img[H - bh:, x:x + bw] = np.array([0.012, 0.014, 0.022])
    for wy in range(H - bh + 20, H - 10, 26):
        for wx in range(x + 8, x + bw - 8, 18):
            if rng.random() < 0.35:
                c = [np.array([1.0, 0.75, 0.45]), np.array([0.8, 0.9, 1.0]), np.array([1.0, 0.9, 0.7])][rng.integers(3)]
                img[wy:wy + 10, wx:wx + 9] = c * rng.uniform(0.3, 0.9)
    x += bw + rng.integers(0, 30)
img = gaussian_filter(img, (6, 6, 0))
for _ in range(220):  # bokeh discs
    cx, cy, r = rng.integers(0, W), rng.integers(H // 3, H), rng.integers(10, 38)
    yy, xx = np.ogrid[:H, :W]; m = ((xx - cx) ** 2 + (yy - cy) ** 2) < r * r
    c = [np.array([1.0, 0.6, 0.25]), np.array([0.5, 0.7, 1.0]), np.array([1.0, 0.85, 0.6]), np.array([1, 0.3, 0.25])][rng.integers(4)]
    img[m] += c * rng.uniform(0.15, 0.5)
save(np.clip(img, 0, 1), "city.png")

# ---- decals (RGBA): wine stain, new dark stain, blood drops, cork scuff, bullet hole with cracks ----
def blob(n, irregular=0.35, seed=0, soft=3):
    r = np.random.default_rng(seed); yy, xx = np.mgrid[-1:1:n * 1j, -1:1:n * 1j]
    ang = np.arctan2(yy, xx); rad = np.hypot(xx, yy)
    edge = 0.62 + sum(irregular / k * np.sin(k * ang + r.random() * 6) for k in range(2, 9)) * 0.35
    m = (rad < edge).astype(float)
    for _ in range(6):  # splash droplets
        a = r.random() * 6.28; d = r.uniform(0.7, 0.92); s = r.uniform(0.02, 0.06)
        m = np.maximum(m, (np.hypot(xx - d * np.cos(a), yy - d * np.sin(a)) < s).astype(float))
    m = gaussian_filter(m, soft)
    ring = np.clip(1 - np.abs(rad - edge * 0.97) * 12, 0, 1) * m  # darker rim like a dried wine ring
    return m, ring
def rgba(m, ring, col, rimcol):
    a = np.zeros(m.shape + (4,)); a[..., :3] = col; a[..., :3] = a[..., :3] * (1 - ring[..., None]) + np.array(rimcol) * ring[..., None]
    a[..., 3] = np.clip(m * 0.92 + ring * 0.08, 0, 1); return a
m, rg = blob(512, seed=1); save(rgba(m, rg, (0.42, 0.04, 0.08), (0.25, 0.01, 0.04)), "stain_wine.png")
m, rg = blob(512, 0.5, seed=4); save(rgba(m, rg, (0.18, 0.01, 0.02), (0.08, 0.0, 0.01)), "stain_dark.png")
a = np.zeros((256, 256, 4))
for k in range(7):
    c = rng.integers(30, 226, 2); rr = rng.integers(5, 14); yy, xx = np.ogrid[:256, :256]
    mm = gaussian_filter((((xx - c[0]) ** 2 + (yy - c[1]) ** 2) < rr * rr).astype(float), 1.2)
    a[..., 3] = np.maximum(a[..., 3], mm)
a[..., :3] = (0.28, 0.01, 0.02); save(a, "blood_drops.png")
# cork scuff
a = np.zeros((256, 256, 4)); yy, xx = np.mgrid[-1:1:256j, -1:1:256j]
a[..., :3] = 0.9; a[..., 3] = np.clip(gaussian_filter(((np.hypot(xx, yy) < 0.18) * rng.uniform(0.2, 0.7, (256, 256))), 2) * 0.8, 0, 1)
save(a, "cork_scuff.png")
# bullet hole: dark hole + white radial cracks + concentric arcs
im = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0)); d = ImageDraw.Draw(im); C = 512
for k in range(16):
    ang = k / 16 * 6.283 + rng.normal(0, 0.15); L = rng.uniform(250, 500); pts = [(C, C)]
    for s in range(1, 9):
        rr = L * s / 8; a2 = ang + rng.normal(0, 0.05)
        pts.append((C + rr * np.cos(a2), C + rr * np.sin(a2)))
    d.line(pts, fill=(235, 240, 245, 230), width=3)
for rr in (60, 110, 170):
    for k in range(16):
        a0 = k / 16 * 360 + rng.uniform(0, 10); d.arc([C - rr, C - rr, C + rr, C + rr], a0, a0 + rng.uniform(8, 18), fill=(230, 235, 240, 200), width=2)
d.ellipse([C - 70, C - 70, C + 70, C + 70], fill=(220, 225, 230, 160))
d.ellipse([C - 24, C - 24, C + 24, C + 24], fill=(5, 5, 8, 255))
im.filter(ImageFilter.GaussianBlur(0.8)).save(os.path.join(OUT, "bullet_hole.png"))
# curtain hole (frayed)
im = Image.new("RGBA", (256, 256), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.ellipse([100, 100, 156, 156], fill=(40, 30, 25, 255)); d.ellipse([112, 112, 144, 144], fill=(0, 0, 0, 255))
im.filter(ImageFilter.GaussianBlur(1.5)).save(os.path.join(OUT, "curtain_hole.png"))
# body chest hole: dark ring + hole
a = np.zeros((256, 256, 4)); yy, xx = np.mgrid[-1:1:256j, -1:1:256j]; rr = np.hypot(xx, yy)
a[..., :3] = (0.12, 0.0, 0.01); a[..., 3] = np.clip(gaussian_filter((rr < 0.75).astype(float) * (0.6 + 0.4 * rng.random((256, 256))), 6), 0, 1)
a[rr < 0.08] = (0.01, 0.0, 0.0, 1); save(a, "chest_hole.png")
# scratches and cut
a = np.zeros((256, 512, 4)); a[..., :3] = (0.55, 0.08, 0.08)
for k in range(3):
    y0 = 90 + k * 40; xs = np.arange(60, 450)
    for x_ in xs: a[int(y0 + 10 * np.sin(x_ / 90)) - 3: int(y0 + 10 * np.sin(x_ / 90)) + 3, x_, 3] = 0.9
save(a, "scratches.png")
a = np.zeros((128, 512, 4)); a[..., :3] = (0.5, 0.02, 0.03); a[60:68, 40:470, 3] = 1; a[..., 3] = gaussian_filter(a[..., 3], 1.5); save(a, "cut.png")

# ---- fabric / wood / tile / wall ----
def tile_noise(n, s): return gaussian_filter(rng.random((n, n)), s, mode="wrap")
w = tile_noise(1024, 2); g = np.sin(np.linspace(0, 80, 1024)[None, :] + w * 30) * 0.5 + 0.5
wood = np.stack([0.36 + 0.08 * g, 0.2 + 0.05 * g, 0.1 + 0.03 * g], -1); save(wood, "wood.png")
t = np.ones((512, 512, 3)) * np.array([0.62, 0.6, 0.56]); t[::128, :] = 0.3; t[:, ::128] = 0.3; t[1::128, :] = 0.3; t[:, 1::128] = 0.3
t *= (0.92 + 0.08 * tile_noise(512, 3))[..., None]; save(t, "tile.png")
wv = 0.9 + 0.1 * (np.sin(np.arange(512)[:, None] * 1.3) * np.sin(np.arange(512)[None, :] * 1.3) > 0)
save(np.stack([wv] * 3, -1) * tile_noise(512, 1)[..., None] * 0.15 + 0.85, "linen.png")

# ---- phone screens (9:19.5, 540x1170) ----
def font(p, s): return ImageFont.truetype(p, s, layout_engine=ImageFont.Layout.RAQM)
def emoji(ch, size):
    f = ImageFont.truetype(EMO, 109); im = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), ch, font=f, embedded_color=True); return im.resize((int(size * 1.06), size))
def screen(bg=(16, 16, 20)):
    im = Image.new("RGB", (540, 1170), bg); d = ImageDraw.Draw(im)
    d.text((40, 22), "22:47", font=font(THB, 26), fill=(230, 230, 230)); return im, d
def bubble(im, d, y, text, mine, emo=None, blur=False):
    f = font(TH, 30); tw = d.textlength(text, font=f) + (44 if emo else 0)
    x0 = int(540 - 40 - tw - 40) if mine else 40; tw = int(tw)
    box = [x0, y, x0 + tw + 40, y + 70]
    d.rounded_rectangle(box, 26, fill=(0, 132, 255) if mine else (55, 55, 62))
    if blur:
        sub = Image.new("RGB", (int(tw), 50), (0, 132, 255) if mine else (55, 55, 62)); sd = ImageDraw.Draw(sub)
        sd.text((0, 2), text, font=f, fill=(255, 255, 255)); sub = sub.filter(ImageFilter.GaussianBlur(5)); im.paste(sub, (x0 + 20, y + 10))
    else:
        d.text((x0 + 20, y + 12), text, font=f, fill=(255, 255, 255))
    if emo: im.paste(emoji(emo, 36), (int(x0 + tw - 20), y + 16), emoji(emo, 36))
    return y + 90
# 6B: chat with "ดาว ❤️"
im, d = screen(); d.rectangle([0, 70, 540, 170], fill=(30, 30, 36))
d.text((40, 95), "ดาว", font=font(THB, 40), fill=(255, 255, 255)); e = emoji("❤️", 40); im.paste(e, (130, 102), e)
y = 220
for t, mine, em in [("คิดถึงนะ", False, "❤️"), ("เมื่อคืนดีมาก", True, None), ("อย่าบอกมาร์ตินนะ", False, None),
                    ("ไม่บอกหรอก", True, "😘"), ("พรุ่งนี้เจอกันที่เดิม", False, "❤️"), ("รักนะ", True, "❤️"), ("❤️❤️❤️", False, None)]:
    y = bubble(im, d, y, t if t != "❤️❤️❤️" else "xxxx", mine, em if t != "❤️❤️❤️" else None, blur=(t not in ("รักนะ",)))
for k in range(3):
    e = emoji("❤️", 54); im.paste(e, (60 + k * 64, y + 6), e)
im.save(os.path.join(OUT, "phone_chat.png"))
# 6D: threats + one-way booking
im, d = screen(); d.rectangle([0, 70, 540, 170], fill=(30, 30, 36)); d.text((40, 95), "แอนดี้", font=font(THB, 40), fill=(255, 255, 255))
y = 220
for t, mine in [("ศุกร์นี้ 800,000", True), ("ไม่งั้นกูบอกพ่อมึง", True), ("ขอเวลาอีกนิด", False), ("ไม่", True)]:
    y = bubble(im, d, y, t, mine)
d.rounded_rectangle([30, 640, 510, 1080], 24, fill=(245, 245, 248))
d.text((60, 660), "SKYLOTUS AIR", font=font(THB, 34), fill=(20, 60, 140))
d.text((60, 720), "BKK  -  NRT", font=font(THB, 56), fill=(20, 20, 30))
d.text((60, 810), "ONE-WAY · เที่ยวเดียว", font=font(THB, 32), fill=(200, 40, 40))
d.text((60, 870), "ออกเดินทาง 07:00 พรุ่งนี้", font=font(TH, 32), fill=(40, 40, 50))
d.text((60, 930), "ผู้โดยสาร: ANDY", font=font(TH, 30), fill=(60, 60, 70))
d.text((60, 990), "ยืนยันแล้ว", font=font(THB, 32), fill=(20, 140, 60))
im.save(os.path.join(OUT, "phone_threats.png"))
print("textures ->", sorted(os.listdir(OUT)))

# ---- book spine: Huis Clos (easter egg) ----
im = Image.new("RGB", (600, 90), (190, 172, 128)); d = ImageDraw.Draw(im)
d.text((30, 18), "SARTRE  ·  HUIS CLOS", font=font(THB, 40), fill=(60, 20, 15)); im.save(os.path.join(OUT, "huis_clos.png"))

# ---- memorial-style birthday meme (1B) and the RIP comment (10E) ----
def meme_card():
    card = Image.new("RGB", (540, 640), (40, 40, 42)); d = ImageDraw.Draw(card)
    pp = os.path.join(OUT, "do_portrait.png")
    if os.path.exists(pp):
        ph = Image.open(pp).convert("L").resize((300, 300)).convert("RGB")
    else:
        ph = Image.new("RGB", (300, 300), (120, 120, 120)); dd = ImageDraw.Draw(ph); dd.ellipse([90, 40, 210, 170], fill=(170, 170, 170)); dd.ellipse([50, 170, 250, 400], fill=(170, 170, 170))
    for cx in (60, 480):  # cartoon clouds
        for k in range(4): d.ellipse([cx - 60 + k * 25, 470 + (k % 2) * 15, cx + 10 + k * 25, 540 + (k % 2) * 15], fill=(200, 200, 205))
    for sx in (-1, 1):  # angel wings
        for k in range(5):
            x0 = 270 + sx * (150 + k * 22); d.ellipse([min(x0, x0 + sx * 90), 150 + k * 18, max(x0, x0 + sx * 90), 210 + k * 18], fill=(225, 225, 228))
    mask = Image.new("L", (300, 300), 0); ImageDraw.Draw(mask).ellipse([0, 0, 300, 300], fill=255)
    card.paste(ph, (120, 90), mask)
    d.ellipse([195, 30, 345, 70], outline=(235, 220, 150), width=8)  # halo
    d.text((130, 410), "HBD ตำนาน", font=font(THB, 52), fill=(240, 240, 240)); e = emoji("🕊️", 48); card.paste(e, (410, 418), e)
    d.text((185, 480), "1998 – 2026", font=font(TH, 36), fill=(210, 210, 210))
    return card
def post_screen(comments):
    im, d = screen((250, 250, 252)); d.text((40, 22), "22:47", font=font(THB, 26), fill=(20, 20, 20))
    d.ellipse([30, 80, 90, 140], fill=(120, 120, 130)); d.text((105, 85), "เต้ย", font=font(THB, 30), fill=(20, 20, 20))
    d.text((105, 120), "เมื่อ 3 ชั่วโมงที่แล้ว", font=font(TH, 22), fill=(120, 120, 120))
    im.paste(meme_card().resize((540, 640)), (0, 160)); y = 820
    for who, txt, em in comments:
        d.rounded_rectangle([30, y, 510, y + 92], 22, fill=(235, 235, 240)); d.text((50, y + 8), who, font=font(THB, 24), fill=(30, 30, 30))
        d.text((50, y + 44), txt, font=font(TH, 28), fill=(30, 30, 30))
        if em: e = emoji(em, 32); im.paste(e, (int(50 + d.textlength(txt, font=font(TH, 28)) + 8), y + 48), e)
        y += 108
    return im
post_screen([("แอนดี้", "555555 ตายตาหลับ", None), ("ดาว", "สุขสันต์วันเกิดนะ", "🎂")]).save(os.path.join(OUT, "phone_meme.png"))
post_screen([("ดาว", "สุขสันต์วันเกิดนะ", "🎂"), ("เต้ย", "RIP ตำนาน", "😂")]).save(os.path.join(OUT, "phone_rip.png"))
print("extra textures ok")

# ---- the future tablecloth over the body: same wine stain, soaked darker, one round hole over the chest ----
W2, H2 = 1024, 1024
cl = np.ones((H2, W2, 3)) * np.array([0.93, 0.92, 0.89]) * (0.95 + 0.05 * gaussian_filter(rng.random((H2, W2)), 1))[..., None]
yy, xx = np.mgrid[0:H2, 0:W2]
m, rg = blob(420, seed=1)  # the same wine-stain shape as the table
cy, cx = 430, 470
sub = cl[cy - 210:cy + 210, cx - 210:cx + 210]
sub[:] = sub * (1 - m[..., None] * 0.9) + np.array([0.3, 0.02, 0.05]) * m[..., None] * 0.9
dark = gaussian_filter(((xx - 500) ** 2 / 1.0 + (yy - 470) ** 2 / 1.3 < 150 ** 2).astype(float) * (0.7 + 0.3 * rng.random((H2, W2))), 18)
cl = cl * (1 - dark[..., None] * 0.85) + np.array([0.09, 0.0, 0.01]) * dark[..., None] * 0.85
hole = np.hypot(xx - 500, yy - 470) < 9; cl[hole] = 0.01
save(np.clip(cl, 0, 1), "body_cloth.png")
print("body cloth ok")
