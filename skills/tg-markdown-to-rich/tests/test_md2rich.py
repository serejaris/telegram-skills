import importlib.util
import pathlib
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


if __name__ == "__main__":
    unittest.main()
