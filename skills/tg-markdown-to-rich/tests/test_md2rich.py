import argparse
import importlib.util
import json
import pathlib
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "md2rich.py"
SPEC = importlib.util.spec_from_file_location("md2rich", SCRIPT)
md2rich = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(md2rich)


class MediaBindingTests(unittest.TestCase):
    def test_builds_markdown_without_media(self):
        self.assertEqual(
            md2rich.build_input_rich_message("# Title"),
            {"markdown": "# Title"},
        )

    def test_builds_and_validates_file_id_binding(self):
        markdown = "![](tg://photo?id=cover)"
        media = [
            {
                "id": "cover",
                "media": {"type": "photo", "media": "AgAC_file_id"},
            }
        ]
        md2rich.validate_limits(markdown, media)
        self.assertEqual(
            md2rich.build_input_rich_message(markdown, media)["media"],
            media,
        )

    def test_accepts_animation_through_video_reference(self):
        markdown = "![](tg://video?id=motion)"
        media = [
            {
                "id": "motion",
                "media": {"type": "animation", "media": "attach://motion_file"},
            }
        ]
        md2rich.validate_media_bindings(markdown, media)

    def test_rejects_missing_binding(self):
        with self.assertRaisesRegex(md2rich.LimitError, "has no --media binding"):
            md2rich.validate_media_bindings(
                "![](tg://audio?id=briefing)",
                [],
            )

    def test_rejects_incompatible_binding(self):
        with self.assertRaisesRegex(md2rich.LimitError, "incompatible"):
            md2rich.validate_media_bindings(
                "![](tg://photo?id=cover)",
                [
                    {
                        "id": "cover",
                        "media": {"type": "video", "media": "BAAC_file_id"},
                    }
                ],
            )

    def test_rejects_duplicate_and_invalid_ids(self):
        with self.assertRaisesRegex(md2rich.LimitError, "Duplicate"):
            md2rich.validate_media_bindings(
                "",
                [
                    {"id": "cover", "media": {"type": "photo", "media": "one"}},
                    {"id": "cover", "media": {"type": "photo", "media": "two"}},
                ],
            )
        with self.assertRaisesRegex(
            md2rich.argparse.ArgumentTypeError,
            "1-64",
        ):
            md2rich.parse_media_binding("bad.id=photo=AgAC")

    def test_rejects_invalid_reference_id(self):
        with self.assertRaisesRegex(md2rich.LimitError, "Invalid tg:// media id"):
            md2rich.validate_media_bindings(
                "![](tg://photo?id=bad.id)",
                [],
            )

    def test_parse_media_keeps_equals_in_url(self):
        self.assertEqual(
            md2rich.parse_media_binding(
                "cover=photo=https://cdn.example/image?id=42"
            ),
            {
                "id": "cover",
                "media": {
                    "type": "photo",
                    "media": "https://cdn.example/image?id=42",
                },
            },
        )

    def test_rejects_more_than_fifty_bindings(self):
        media = [
            {
                "id": f"media_{index}",
                "media": {"type": "photo", "media": f"file_{index}"},
            }
            for index in range(51)
        ]
        with self.assertRaisesRegex(md2rich.LimitError, "Too many media bindings"):
            md2rich.validate_media_bindings("", media)

    def test_rejects_binding_the_markup_never_references(self):
        markdown = "![](tg://photo?id=cover)"
        media = [
            {"id": "cover", "media": {"type": "photo", "media": "file_a"}},
            {"id": "leftover", "media": {"type": "photo", "media": "file_b"}},
        ]
        with self.assertRaisesRegex(md2rich.LimitError, "never referenced.*leftover"):
            md2rich.validate_media_bindings(markdown, media)

    def test_keeps_player_metadata_on_the_binding(self):
        markdown = '![](tg://audio?id=answer "The model answered 323")'
        media = [
            {
                "id": "answer",
                "media": {
                    "type": "audio",
                    "media": "attach://answer_file",
                    "duration": 4,
                    "performer": "Voice 2.0",
                    "title": "Answer: 323",
                },
            }
        ]
        md2rich.validate_limits(markdown, media)
        built = md2rich.build_input_rich_message(markdown, media)
        self.assertEqual(built["media"][0]["media"]["performer"], "Voice 2.0")


class AttachmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cover = pathlib.Path(self.tmp.name) / "cover.png"
        self.cover.write_bytes(b"\x89PNG\r\n")

    def _media(self, source="attach://cover_file"):
        return [{"id": "cover", "media": {"type": "photo", "media": source}}]

    def test_resolves_matching_file_part(self):
        resolved = md2rich.resolve_attachments(
            self._media(), [("cover_file", self.cover)]
        )
        self.assertEqual(resolved, {"cover_file": self.cover})

    def test_rejects_attach_without_file_part(self):
        with self.assertRaisesRegex(md2rich.LimitError, "without a file part"):
            md2rich.resolve_attachments(self._media(), [])

    def test_rejects_file_part_without_binding(self):
        with self.assertRaisesRegex(md2rich.LimitError, "not referenced"):
            md2rich.resolve_attachments(
                self._media(source="AgAC_file_id"), [("cover_file", self.cover)]
            )

    def test_multipart_body_carries_json_field_and_file(self):
        body, content_type = md2rich.encode_multipart(
            {"chat_id": "-100", "rich_message": '{"markdown":"# Hi"}'},
            {"cover_file": self.cover},
        )
        boundary = content_type.split("boundary=")[1]
        self.assertIn(f"--{boundary}".encode(), body)
        self.assertIn(b'name="rich_message"', body)
        self.assertIn(b'{"markdown":"# Hi"}', body)
        self.assertIn(b'filename="cover.png"', body)
        self.assertIn(b"Content-Type: image/png", body)
        self.assertTrue(body.endswith(f"--{boundary}--\r\n".encode()))

    def test_media_json_loads_bindings_with_metadata(self):
        path = pathlib.Path(self.tmp.name) / "media.json"
        path.write_text(
            json.dumps(
                [
                    {
                        "id": "answer",
                        "media": {
                            "type": "audio",
                            "media": "attach://answer_file",
                            "duration": 4,
                        },
                    }
                ]
            ),
            encoding="utf-8",
        )
        loaded = md2rich.load_media_json(str(path))
        self.assertEqual(loaded[0]["media"]["duration"], 4)

    def test_media_json_rejects_invalid_binding(self):
        path = pathlib.Path(self.tmp.name) / "bad.json"
        path.write_text(json.dumps([{"id": "x", "media": {"type": "sticker"}}]), encoding="utf-8")
        with self.assertRaises(argparse.ArgumentTypeError):
            md2rich.load_media_json(str(path))


if __name__ == "__main__":
    unittest.main()
