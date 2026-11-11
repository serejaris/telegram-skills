#!/usr/bin/env python3
import argparse
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

S = 2
W = H = 512 * S
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
PINK = (255, 39, 188, 255)
YELLOW = (255, 222, 0, 255)
DARK = (15, 22, 30, 255)
BOLD = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
IMPACT = "/System/Library/Fonts/Supplemental/Impact.ttf"
RAINBOW = [(0, (255, 0, 60)), (0.2, (255, 140, 0)), (0.4, (255, 230, 0)), (0.6, (0, 200, 80)), (0.8, (0, 120, 255)), (1, (160, 0, 255))]
CHROME = [(0, (255, 235, 250)), (0.45, (255, 60, 200)), (0.55, (200, 0, 140)), (1, (255, 140, 230))]
STYLES = ("wordart-chrome", "wordart-rainbow", "pink", "impact", "tags")


def fit(font, text, width, start=300):
    size = start
    while size > 10:
        f = ImageFont.truetype(font, size)
        b = f.getbbox(text)
        if b[2] - b[0] <= width:
            return f
        size -= 2
    return ImageFont.truetype(font, size)


def line(text, font, fill, stroke, stroke_fill=BLACK, pad=60):
    b = font.getbbox(text)
    im = Image.new("RGBA", (b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((pad - b[0], pad - b[1]), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def gradient(size, stops, vertical):
    w, h = size
    n = h if vertical else w
    strip = Image.new("RGBA", (1, n) if vertical else (n, 1))
    px = strip.load()
    for i in range(n):
        t = i / max(1, n - 1)
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0 or 1)
                px[(0, i) if vertical else (i, 0)] = tuple(int(c0[m] + (c1[m] - c0[m]) * k) for m in range(3)) + (255,)
                break
    return strip.resize(size)


def warp(mask, amp, mode, persp):
    w, h = mask.size
    out = Image.new("L", (w, h + 2 * amp + int(h * persp)), 0)
    for x in range(w):
        t = x / (w - 1)
        shift = amp * (math.sin(math.pi * t) if mode == "arch" else math.sin(2 * math.pi * t))
        scale = 1 + persp * (t - 0.5) * 2
        col = mask.crop((x, 0, x + 1, h)).resize((1, max(1, int(h * scale))))
        out.paste(col, (x, int(out.height / 2 - col.height / 2 - shift)))
    return out.crop(out.getbbox())


def wordart(text, font, width, stops, vertical, mode, amp, persp, extrude, depth, edge):
    f = fit(font, text, width)
    b = f.getbbox(text)
    m = Image.new("L", (b[2] - b[0] + 40, b[3] - b[1] + 40), 0)
    ImageDraw.Draw(m).text((20 - b[0], 20 - b[1]), text, font=f, fill=255)
    m = warp(m, amp, mode, persp)
    pad = depth + 40
    canvas = Image.new("RGBA", (m.width + 2 * pad, m.height + 2 * pad), (0, 0, 0, 0))
    full = Image.new("L", canvas.size, 0)
    for i in range(depth, -1, -1):
        full.paste(255, (pad + i, pad + i), m)
    canvas.paste(BLACK, (0, 0), full.filter(ImageFilter.MaxFilter(2 * edge + 1)))
    for i in range(depth, 0, -1):
        k = 0.55 + 0.45 * (1 - i / depth)
        canvas.paste(tuple(int(c * k) for c in extrude) + (255,), (pad + i, pad + i), m)
    canvas.paste(gradient(m.size, stops, vertical), (pad, pad), m)
    shine = Image.new("L", m.size, 0)
    ImageDraw.Draw(shine).rectangle((0, 0, m.width, int(m.height * 0.42)), fill=70)
    canvas.paste(WHITE, (pad, pad), ImageChops.multiply(shine, m))
    return canvas


def tag(text, font, width, fill, rot):
    f = fit(font, text, width)
    b = f.getbbox(text)
    px, py = int(f.size * 0.28), int(f.size * 0.16)
    im = Image.new("RGBA", (b[2] - b[0] + 2 * px, b[3] - b[1] + 2 * py), fill)
    ImageDraw.Draw(im).text((px - b[0], py - b[1]), text, font=f, fill=BLACK)
    framed = Image.new("RGBA", (im.width + 16 * S, im.height + 16 * S), BLACK)
    framed.alpha_composite(im, (8 * S, 8 * S))
    return framed.rotate(rot, resample=Image.BICUBIC, expand=True)


def figure(cut, outline, width_k, top_k):
    src = Image.open(cut).convert("RGBA")
    src = src.crop(src.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox())
    fw = int(W * width_k)
    fh = int(src.height * fw / src.width)
    y = int(H * top_k)
    fig = src.resize((fw, fh), Image.LANCZOS).crop((0, 0, fw, min(fh, H - y)))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(fig, ((W - fw) // 2, y))
    hard = layer.getchannel("A").point(lambda v: 255 if v > 90 else 0)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if outline:
        ring = hard.filter(ImageFilter.MaxFilter(2 * outline * S + 1)).filter(ImageFilter.GaussianBlur(S))
        out.paste(WHITE, (0, 0), ring)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), hard.filter(ImageFilter.GaussianBlur(0.7 * S))))
    out.alpha_composite(layer)
    return out


def stack(top_img, main_img, gap, rot):
    blk = Image.new("RGBA", (max(top_img.width, main_img.width), top_img.height + main_img.height - gap), (0, 0, 0, 0))
    blk.alpha_composite(top_img, ((blk.width - top_img.width) // 2, 0))
    blk.alpha_composite(main_img, ((blk.width - main_img.width) // 2, top_img.height - gap))
    if rot:
        blk = blk.rotate(rot, resample=Image.BICUBIC, expand=True)
    k = min(1, W * 0.98 / blk.width)
    return blk.resize((int(blk.width * k), int(blk.height * k)), Image.LANCZOS)


def caption(style, top, word, bold, impact):
    top, word = top.upper(), word.upper()
    if style == "impact":
        f1 = fit(impact, top, int(W * 0.92))
        f2 = fit(impact, word, int(W * 0.80))
        return stack(line(top, f1, WHITE, int(f1.size * 0.09)), line(word, f2, WHITE, int(f2.size * 0.09)), 100, 0)
    if style == "tags":
        return stack(tag(top, bold, int(W * 0.60), WHITE, 5), tag(word, bold, int(W * 0.80), YELLOW, -4), 40, 0)
    fa = fit(bold, top, int(W * 0.62))
    head = line(top, fa, WHITE, int(fa.size * 0.16))
    if style == "pink":
        fb = fit(bold, word, int(W * 0.92))
        main = line(word, fb, PINK, int(fb.size * 0.14))
    elif style == "wordart-rainbow":
        main = wordart(word, bold, int(W * 0.90), RAINBOW, False, "arch", 34 * S, 0, (40, 40, 120), 14 * S, 4 * S)
    else:
        main = wordart(word, bold, int(W * 0.86), CHROME, True, "wave", 22 * S, 0.22, (120, 0, 90), 16 * S, 4 * S)
    return stack(head, main, 40 if style.startswith("wordart") else 70, 8)


def fit512(layer):
    out = layer.resize((512, 512), Image.LANCZOS)
    out = out.crop(out.getchannel("A").getbbox())
    k = 512 / max(out.size)
    out = out.resize((round(out.width * k), round(out.height * k)), Image.LANCZOS)
    final = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    final.alpha_composite(out, ((512 - out.width) // 2, (512 - out.height) // 2))
    return final


def on_dark(images, gap=20):
    sheet = Image.new("RGBA", (len(images) * (512 + gap) + gap, 512 + 2 * gap), DARK)
    for i, im in enumerate(images):
        sheet.alpha_composite(im, (gap + i * (512 + gap), gap))
    return sheet.convert("RGB")


def make(a):
    layer = figure(a.cut, a.outline, a.fig_width, a.fig_top)
    cap = caption(a.style, a.top, a.word, a.font, a.impact_font)
    layer.alpha_composite(cap, ((W - cap.width) // 2, -20))
    final = fit512(layer)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    final.save(out / f"{a.name}.webp", lossless=True)
    final.save(out / f"{a.name}.png")
    on_dark([final]).save(out / f"{a.name}-dark.png")
    print(out / f"{a.name}.webp")


def sheet(a):
    on_dark([Image.open(p).convert("RGBA") for p in a.files]).save(a.out)
    print(a.out)


def main():
    p = argparse.ArgumentParser(description="Static Telegram sticker: cutout figure + caption on top")
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--cut", required=True, help="RGBA cutout of the figure")
    m.add_argument("--top", required=True, help="small first line")
    m.add_argument("--word", required=True, help="main word")
    m.add_argument("--style", choices=STYLES, default="wordart-chrome")
    m.add_argument("--outline", type=int, default=0, help="white outline around the figure, px at 512; 0 = none")
    m.add_argument("--fig-width", type=float, default=0.80)
    m.add_argument("--fig-top", type=float, default=0.36)
    m.add_argument("--font", default=BOLD, help="heavy font with Cyrillic")
    m.add_argument("--impact-font", default=IMPACT)
    m.add_argument("--out", required=True)
    m.add_argument("--name", required=True)
    m.set_defaults(fn=make)
    s = sub.add_parser("sheet", help="previews side by side on a dark chat background")
    s.add_argument("files", nargs="+")
    s.add_argument("--out", required=True)
    s.set_defaults(fn=sheet)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
