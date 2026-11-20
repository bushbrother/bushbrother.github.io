"""Render the PicPak cartoon weather + news card (400x300, 4-colour palette).

Usage: python3 make_card.py card.json out_basename
Writes out_basename.png (exact 400x300, only #000/#fff/#ff0/#f00) and out_basename_x3.png.

card.json example:
{
  "place": "Walton-on-Thames",
  "date": "Fri 20 Nov",
  "now": 8, "hi": 9, "lo": 1,
  "condition": "partly_cloudy",      # sunny | partly_cloudy | cloudy | rain
  "summary": "Partly cloudy · 15% rain",
  "headlines": ["...", "...", "..."]  # 3 short headlines, ~60 chars max each
}
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFont

S = 4
W, H = 400, 300
BLACK, WHITE, YELLOW, RED = (0, 0, 0), (255, 255, 255), (255, 255, 0), (255, 0, 0)
PAL = [BLACK, WHITE, YELLOW, RED]


def find_font(names):
    for root in ["/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.fonts")]:
        for dp, _, fs in os.walk(root):
            for n in names:
                if n in fs:
                    return os.path.join(dp, n)
    return None


ARCHIVO = find_font(["ArchivoBlack-Regular.ttf"]) or find_font(["DejaVuSans-Bold.ttf"])
COMIC_B = find_font(["ComicRelief-Bold.ttf"]) or find_font(["DejaVuSans-Bold.ttf"])

data = json.load(open(sys.argv[1]))
out = sys.argv[2]


def f(path, px):
    return ImageFont.truetype(path, int(px * S))


img = Image.new("RGB", (W * S, H * S), YELLOW)
d = ImageDraw.Draw(img)


def R(*v):
    return [int(x * S) for x in v]


def panel(x0, y0, x1, y1, fill=WHITE, r=10, sh=4, ow=3):
    d.rounded_rectangle(R(x0 + sh, y0 + sh, x1 + sh, y1 + sh), radius=r * S, fill=BLACK)
    d.rounded_rectangle(R(x0, y0, x1, y1), radius=r * S, fill=fill, outline=BLACK, width=ow * S)


def text(xy, s, font, fill, anchor="la"):
    d.text(R(*xy), s, font=font, fill=fill, anchor=anchor)


def outlined_text(xy, s, font, fill, stroke=2, anchor="la"):
    d.text(R(*xy), s, font=font, fill=fill, anchor=anchor, stroke_width=stroke * S, stroke_fill=BLACK)


def wrap(s, font, maxw):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw * S:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_font(path, s, start, maxw):
    px = start
    while px > 9 and d.textlength(s, font=f(path, px)) > maxw * S:
        px -= 0.5
    return f(path, px)


def sun(cx, cy, sr):
    for i in range(10):
        a = math.radians(i * 36 + 10)
        x0, y0 = cx + math.cos(a) * (sr + 5), cy + math.sin(a) * (sr + 5)
        x1, y1 = cx + math.cos(a) * (sr + 15), cy + math.sin(a) * (sr + 15)
        d.line(R(x0, y0, x1, y1), fill=BLACK, width=7 * S)
        d.line(R(x0, y0, x1, y1), fill=RED, width=3 * S)
    d.ellipse(R(cx - sr, cy - sr, cx + sr, cy + sr), fill=YELLOW, outline=BLACK, width=3 * S)
    d.ellipse(R(cx - 10, cy - 8, cx - 5, cy - 1), fill=BLACK)
    d.ellipse(R(cx + 3, cy - 8, cx + 8, cy - 1), fill=BLACK)
    d.arc(R(cx - 11, cy - 6, cx + 9, cy + 12), start=20, end=160, fill=BLACK, width=3 * S)
    d.ellipse(R(cx - 17, cy + 1, cx - 10, cy + 7), fill=RED)
    d.ellipse(R(cx + 7, cy + 1, cx + 14, cy + 7), fill=RED)


def cloud(dx, dy, face=False):
    blobs = [(92, 130, 17), (112, 122, 21), (131, 132, 14), (77, 138, 11)]
    blobs = [(x + dx, y + dy, r) for x, y, r in blobs]
    for (x, y, r) in blobs:
        d.ellipse(R(x - r - 3, y - r - 3, x + r + 3, y + r + 3), fill=BLACK)
    d.rounded_rectangle(R(66 + dx, 130 + dy, 146 + dx, 154 + dy), radius=12 * S, fill=BLACK)
    for (x, y, r) in blobs:
        d.ellipse(R(x - r, y - r, x + r, y + r), fill=WHITE)
    d.rounded_rectangle(R(69 + dx, 133 + dy, 143 + dx, 151 + dy), radius=10 * S, fill=WHITE)
    if face:
        cx, cy = 108 + dx, 138 + dy
        d.ellipse(R(cx - 10, cy - 6, cx - 5, cy + 1), fill=BLACK)
        d.ellipse(R(cx + 5, cy - 6, cx + 10, cy + 1), fill=BLACK)
        d.arc(R(cx - 7, cy + 4, cx + 7, cy + 12), start=200, end=340, fill=BLACK, width=2 * S)


# ---- banner ----
d.rectangle(R(0, 0, W, 46), fill=RED)
d.line(R(0, 46, W, 46), fill=BLACK, width=3 * S)
for x in range(0, W + 20, 20):
    d.ellipse(R(x - 7, 40, x + 7, 52), fill=RED, outline=BLACK, width=2 * S)
d.rectangle(R(0, 30, W, 45), fill=RED)
date_font = f(ARCHIVO, 15)
date_w = d.textlength(data["date"], font=date_font) / S
outlined_text((17, 25), data["place"], fit_font(ARCHIVO, data["place"], 21, 383 - 17 - date_w - 14),
              WHITE, stroke=2, anchor="lm")
outlined_text((383, 25), data["date"], date_font, YELLOW, stroke=2, anchor="rm")

# ---- weather panel ----
panel(16, 62, 156, 288)
cond = data.get("condition", "partly_cloudy")
if cond == "sunny":
    sun(86, 112, 26)
elif cond == "cloudy":
    cloud(-28, -38)
    cloud(-6, -10, face=True)
elif cond == "rain":
    cloud(-14, -26, face=True)
    for i, x in enumerate(range(58, 136, 15)):
        y = 140 + (i % 2) * 8
        d.polygon(R(x, y, x - 5, y + 10, x + 5, y + 10), fill=BLACK)
        d.ellipse(R(x - 6, y + 5, x + 6, y + 17), fill=BLACK)
        d.polygon(R(x, y + 2, x - 3.5, y + 10, x + 3.5, y + 10), fill=RED)
        d.ellipse(R(x - 4.5, y + 6.5, x + 4.5, y + 15.5), fill=RED)
else:  # partly_cloudy
    sun(64, 104, 22)
    cloud(0, 0)

outlined_text((86, 196), f"{round(data['now'])}°", f(ARCHIVO, 46), RED, stroke=3, anchor="mm")
text((86, 226), "now", f(COMIC_B, 13), BLACK, anchor="mm")
hi_s, lo_s = f"High {round(data['hi'])}°", f"Low {round(data['lo'])}°"
d.rounded_rectangle(R(22, 238, 85, 258), radius=9 * S, fill=YELLOW, outline=BLACK, width=2 * S)
text((53.5, 248), hi_s, fit_font(COMIC_B, hi_s, 13, 56), BLACK, anchor="mm")
d.rounded_rectangle(R(89, 238, 152, 258), radius=9 * S, fill=BLACK)
text((120.5, 248), lo_s, fit_font(COMIC_B, lo_s, 13, 56), WHITE, anchor="mm")
text((86, 273), data["summary"], fit_font(COMIC_B, data["summary"], 10.5, 128), BLACK, anchor="mm")

# ---- news panel ----
panel(168, 62, 384, 288)
d.rounded_rectangle(R(180, 54, 320, 80), radius=12 * S, fill=BLACK)
d.rounded_rectangle(R(178, 50, 318, 78), radius=12 * S, fill=RED, outline=BLACK, width=3 * S)
outlined_text((248, 64), "Today's news", f(ARCHIVO, 14), WHITE, stroke=2, anchor="mm")

heads = data["headlines"][:3]


def layout(px):
    bf = f(COMIC_B, px)
    lh = px * 1.26
    blocks = [wrap(h, bf, 180) for h in heads]
    total = 92 + sum(len(b) * lh + 12 for b in blocks) - 12
    return bf, lh, blocks, total


px = 13.5
bf, lh, blocks, total = layout(px)
while total > 282 and px > 10:
    px -= 0.5
    bf, lh, blocks, total = layout(px)
if total > 282:
    sys.exit(f"Headlines too long to fit (needs {total:.0f}px, max 282). Shorten them.")

y = 92
for i, lines in enumerate(blocks):
    bx, by = 186, y + 7
    d.ellipse(R(bx - 8, by - 8, bx + 8, by + 8), fill=YELLOW if i % 2 == 0 else RED, outline=BLACK, width=2 * S)
    text((bx, by), str(i + 1), f(ARCHIVO, 10), BLACK if i % 2 == 0 else WHITE, anchor="mm")
    for j, ln in enumerate(lines):
        text((199, y + j * lh), ln, bf, BLACK)
    y += len(lines) * lh + 12
    if i < len(blocks) - 1:
        for x in range(186, 372, 8):
            d.line(R(x, y - 7, x + 4, y - 7), fill=BLACK, width=int(1.5 * S))

# ---- downscale and snap to palette ----
small = img.resize((W, H), Image.LANCZOS)
pal_img = Image.new("P", (1, 1))
flat = [v for c in PAL for v in c]
pal_img.putpalette(flat + [0] * (768 - len(flat)))
snapped = small.quantize(palette=pal_img, dither=Image.Dither.NONE).convert("RGB")
snapped.save(out + ".png")
snapped.resize((W * 3, H * 3), Image.NEAREST).save(out + "_x3.png")
print(f"OK {out}.png  (news font {px}px, bottom {total:.0f}px)")
