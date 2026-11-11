#!/usr/bin/env python3
import argparse

from PIL import Image
from rembg import new_session, remove


def main():
    p = argparse.ArgumentParser(description="Cut a person out of a video frame")
    p.add_argument("frame")
    p.add_argument("out", help="lossless .webp or .png with alpha")
    p.add_argument("--box", help="x0,y0,x1,y1 crop before cutting")
    p.add_argument("--model", default="birefnet-portrait")
    a = p.parse_args()
    im = Image.open(a.frame).convert("RGB")
    if a.box:
        im = im.crop(tuple(int(v) for v in a.box.split(",")))
    res = remove(im, session=new_session(a.model))
    res = res.crop(res.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox())
    res.save(a.out, lossless=True) if a.out.endswith(".webp") else res.save(a.out)
    bg = Image.new("RGBA", res.size, (40, 160, 90, 255))
    bg.alpha_composite(res)
    preview = a.out.rsplit(".", 1)[0] + "-green.jpg"
    bg.convert("RGB").save(preview)
    print(a.out, preview)


if __name__ == "__main__":
    main()
