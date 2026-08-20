import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import calyxserver


class CalyxServerTests(unittest.TestCase):
    def test_valid_port(self):
        self.assertEqual(calyxserver.valid_port("8080"), 8080)

    def test_invalid_ports(self):
        for value in ("0", "65536", "abc", "12.5"):
            with self.subTest(value=value), self.assertRaises(Exception):
                calyxserver.valid_port(value)

    def test_root_and_welcome_page_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "www"
            result = calyxserver.ensure_public_root(root)
            self.assertTrue(result.is_dir())
            self.assertIn("Calyx Web Server", (result / "index.html").read_text())

    def test_existing_index_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "www"
            root.mkdir()
            (root / "index.html").write_text("custom", encoding="utf-8")
            calyxserver.ensure_public_root(root)
            self.assertEqual((root / "index.html").read_text(), "custom")

    @patch("builtins.input", side_effect=["bad", "8080"])
    def test_prompt_retries(self, mocked_input):
        self.assertEqual(calyxserver.prompt_for_port(), 8080)


if __name__ == "__main__":
    unittest.main()
