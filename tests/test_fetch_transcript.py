import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest


spec = importlib.util.spec_from_file_location(
    "fetch_transcript", Path(__file__).resolve().parents[1] / "scripts" / "fetch_transcript.py"
)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class TranscriptTests(unittest.TestCase):
    def test_supported_links_preserve_video_identity(self):
        identifier = "wvt5JNUXXLM"
        for url in [
            identifier,
            f"https://www.youtube.com/watch?v={identifier}&t=42s&list=example",
            f"youtube.com/watch?v={identifier}",
            f"https://youtu.be/{identifier}?si=example",
            f"https://m.youtube.com/shorts/{identifier}",
            f"https://youtube.com/live/{identifier}",
            f"https://www.youtube.com/embed/{identifier}",
        ]:
            with self.subTest(url=url):
                self.assertEqual(helper.video_id(url), identifier)

    def test_invalid_or_misleading_links_are_rejected(self):
        for url in [
            "youtube.com/w/kdjgfwirhe", "https://youtube.com/playlist?list=example",
            "https://youtube.com.evil.example/watch?v=wvt5JNUXXLM",
            "https://youtube.com@evil.example/watch?v=wvt5JNUXXLM",
            "https://evil.example/wvt5JNUXXLM", "https://youtube.com/watch?v=short",
            "ftp://youtube.com/watch?v=wvt5JNUXXLM",
            "https://youtube.com/watch?v=wvt5JNUXXLM&v=abcdefghijk",
        ]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                helper.video_id(url)

    def test_payload_preserves_captions_and_real_timestamps(self):
        class Captions(list):
            video_id = "wvt5JNUXXLM"
            language = "English"
            language_code = "en"
            is_generated = True

        captions = Captions([
            SimpleNamespace(start=272.75, duration=3.5, text="About 2×, for this workload only."),
            SimpleNamespace(start=3661.1, duration=2, text="Actually, the final result differs."),
        ])
        result = helper.transcript_payload(captions, metadata_error="HTTPError")
        self.assertEqual(len(result["segments"]), 2)
        self.assertEqual(result["segments"][0]["timestamp"], "4:32")
        self.assertTrue(result["segments"][0]["url"].endswith("&t=272s"))
        self.assertEqual(result["segments"][1]["timestamp"], "1:01:01")
        self.assertEqual(result["segments"][1]["text"], captions[1].text)
        self.assertEqual(result["last_caption_end_seconds"], 3663.1)
        self.assertTrue(result["is_generated"])
        self.assertIsNone(result["metadata"])
        with self.assertRaises(ValueError):
            helper.transcript_payload(Captions())


if __name__ == "__main__":
    unittest.main()
