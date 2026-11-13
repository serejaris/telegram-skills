import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_sticker as cs


def png(w, h, color=6):
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, color, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(b"")) + chunk(b"IEND", b"")


def riff(chunk_type, payload):
    body = b"WEBP" + chunk_type + struct.pack("<I", len(payload)) + payload
    return b"RIFF" + struct.pack("<I", len(body)) + body


def vp8x(w, h, alpha=True):
    return riff(b"VP8X", bytes([0x10 if alpha else 0, 0, 0, 0]) + (w - 1).to_bytes(3, "little") + (h - 1).to_bytes(3, "little"))


def vp8l(w, h, alpha=True):
    bits = (w - 1) | ((h - 1) << 14) | (int(alpha) << 28)
    return riff(b"VP8L", b"\x2f" + bits.to_bytes(4, "little") + b"\x00" * 8)


def vp8(w, h):
    return riff(b"VP8 ", b"\x00" * 3 + b"\x9d\x01\x2a" + struct.pack("<HH", w, h) + b"\x00" * 8)


class Files(unittest.TestCase):
    def run_on(self, data):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(data)
        try:
            return cs.check_file(f.name)
        finally:
            Path(f.name).unlink()

    def test_valid_png(self):
        r = self.run_on(png(512, 400))
        self.assertEqual((r["width"], r["height"], r["errors"], r["warnings"]), (512, 400, [], []))

    def test_png_without_alpha_warns(self):
        r = self.run_on(png(512, 512, color=2))
        self.assertEqual(r["errors"], [])
        self.assertTrue(r["warnings"])

    def test_wrong_size(self):
        self.assertTrue(self.run_on(png(500, 500))["errors"])
        self.assertTrue(self.run_on(png(513, 300))["errors"])

    def test_webp_variants(self):
        self.assertEqual(self.run_on(vp8x(512, 512))["errors"], [])
        r = self.run_on(vp8l(300, 512))
        self.assertEqual((r["width"], r["height"], r["alpha"], r["errors"]), (300, 512, True, []))
        r = self.run_on(vp8(512, 512))
        self.assertEqual((r["alpha"], r["errors"]), (False, []))
        self.assertTrue(r["warnings"])

    def test_too_big(self):
        self.assertTrue(self.run_on(png(512, 512) + b"\x00" * (512 * 1024))["errors"])

    def test_malformed(self):
        for data in (b"", b"GIF89a" + b"\x00" * 40, b"\x89PNG\r\n\x1a\n", b"RIFF\x00\x00\x00\x00WEBPXXXX" + b"\x00" * 20, vp8l(512, 512)[:20]):
            self.assertTrue(self.run_on(data)["errors"], data[:16])

    def test_missing_file(self):
        self.assertTrue(cs.check_file("/nonexistent/sticker.webp")["errors"])


class Names(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(cs.check_name("vibecoding")["errors"], [])
        self.assertEqual(cs.check_name("memes_by_MyBot", "@mybot")["errors"], [])

    def test_bad(self):
        for name in ("", "1abc", "a__b", "кириллица", "a" * 65, "with-dash"):
            self.assertTrue(cs.check_name(name)["errors"], name)
        self.assertTrue(cs.check_name("memes", "mybot")["errors"])

    def test_cli_exit(self):
        self.assertEqual(cs.main(["name", "ok_name"]), 0)
        self.assertEqual(cs.main(["name", "bad__name"]), 1)


if __name__ == "__main__":
    unittest.main()
