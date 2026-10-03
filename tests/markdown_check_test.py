"""Exercise link checks without depending on the repository's current links."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("markdown_check", ROOT / "scripts/check_markdown.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class MarkdownTest(unittest.TestCase):
    def test_heading_ids_and_duplicates(self):
        self.assertEqual(CHECK.anchors("# An `API`\n# An `API`\n## A-B\n"), {"an-api", "an-api-1", "a-b"})

    def test_fences_are_not_links(self):
        self.assertEqual(CHECK.prose("```md\n[example](absent.md)\n```\n~~~\n# Example\n~~~\n"), "")

    def test_missing_target_and_anchor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "target.md").write_text("# Present\n")
            doc = root / "source.md"
            doc.write_text("[ok](target.md#present)\n[bad](target.md#absent)\n[missing](gone.md)\n")
            self.assertEqual(CHECK.check(doc), ["missing heading: target.md#absent", "missing path: gone.md"])

    def test_encoded_path_and_external_url(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "some file.md").write_text("# Present\n")
            doc = root / "source.md"
            doc.write_text('[ok](some%20file.md#present)\n[external](https://example.org/)\n')
            self.assertEqual(CHECK.check(doc), [])

    def test_inventory_uses_current_worktree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", directory], check=True)
            removed = root / "removed.md"
            removed.write_text("# Former doc\n")
            subprocess.run(["git", "add", "removed.md"], cwd=root, check=True)
            removed.unlink()
            new = root / "new.md"
            new.write_text("# New doc\n")
            self.assertEqual(CHECK.files(root), [new])


if __name__ == "__main__":
    unittest.main()
