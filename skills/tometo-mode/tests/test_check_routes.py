#!/usr/bin/env python3
"""Check route failures, portable installation, and shared-asset comparison."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check-routes.py"
spec = importlib.util.spec_from_file_location("check_routes", SCRIPT)
routes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routes)


class RouteChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def skill(self, root, name, body=""):
        folder = root / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(f"---\nname: {name}\n---\n{body}\n")
        return folder

    def test_resolves_document_relative_links_and_does_not_crawl_siblings(self):
        alpha = self.skill(self.root, "alpha", "[detail](references/a%20b.md#fragment)")
        beta = self.skill(self.root, "beta", "[unselected](missing.md)")
        (alpha / "references").mkdir()
        (alpha / "references" / "a b.md").write_text("[sibling](../../beta/SKILL.md)\n")
        check = routes.Check()
        check.skill(alpha)
        self.assertEqual(check.errors, set())
        self.assertEqual(check.links, 2)
        (beta / "SKILL.md").unlink()
        check = routes.Check()
        check.skill(alpha)
        self.assertTrue(any("missing target" in error for error in check.errors))

    def test_ignores_code_examples_and_external_links(self):
        alpha = self.skill(self.root, "alpha", """```markdown
[example](missing.md)
```
`[inline](absent.md)`
[external](https://example.com/missing)
""")
        check = routes.Check()
        check.skill(alpha)
        self.assertEqual(check.errors, set())
        self.assertEqual(check.links, 0)

    def test_reports_wrong_name_and_cyclic_directory_link(self):
        alpha = self.skill(self.root, "alpha")
        (alpha / "SKILL.md").write_text("---\nname: wrong\n---\n")
        (alpha / "loop").symlink_to(alpha, target_is_directory=True)
        check = routes.Check()
        check.skill(alpha)
        self.assertTrue(any("frontmatter name" in error for error in check.errors))
        self.assertTrue(any("cyclic directory symlink" in error for error in check.errors))

    def test_shared_assets_report_drift(self):
        roots = [self.root / "one", self.root / "two"]
        for index, root in enumerate(roots):
            self.skill(root, "alpha", str(index))
        check = routes.Check()
        check.compare(roots, Path("alpha/SKILL.md"))
        self.assertTrue(any("differs across" in error for error in check.errors))

    def test_default_root_comes_from_installed_script_without_repository_files(self):
        root = self.root / "installed"
        for name in routes.DEFAULT_SKILLS:
            self.skill(root, name)
        folder = root / "tometo-mode" / "scripts"
        folder.mkdir()
        installed = folder / SCRIPT.name
        shutil.copy2(SCRIPT, installed)
        result = subprocess.run([sys.executable, str(installed)], cwd=self.root,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OK: 3 skills", result.stdout)


if __name__ == "__main__":
    unittest.main()
