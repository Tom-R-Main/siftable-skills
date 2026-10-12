#!/usr/bin/env python3
"""Test resource resolution and static validation on source and installed trees."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import install_skills
import validate_repo


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.skills = self.root / 'skills'
        self.skills.mkdir()

    def skill(self, name, body='', fields=''):
        path = self.skills / name
        path.mkdir(exist_ok=True)
        (path / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Use this portable testing workflow for validation of resources.\n{fields}---\n{body}\n')
        return path

    def test_nested_markdown_is_document_relative(self):
        path = self.skill('alpha', '[details](references/deep.md)')
        (path / 'references').mkdir()
        (path / 'references' / 'deep.md').write_text('[root](../SKILL.md)\n')
        self.assertEqual(validate_repo.validate_skill(path), [])

    def test_missing_sibling_and_nested_resource_detected(self):
        path = self.skill('alpha', '[missing](../beta/references/guide.md)')
        self.skill('beta')
        errors = validate_repo.validate_skill(path)
        self.assertTrue(any('unresolved resource ../beta/references/guide.md' in e for e in errors), errors)

    def test_external_links_and_project_import_examples_are_not_dependencies(self):
        path = self.skill('alpha', '[docs](https://example.com/scripts/example.py)\nimport X from "../../components/X";')
        self.assertEqual(validate_repo.validate_skill(path), [])
        self.assertEqual(validate_repo.skill_dependencies(path, self.skills), set())

    def test_fenced_project_tests_and_regex_examples_are_not_resources(self):
        path = self.skill('alpha', '''Project tests/approvals/rollback are safeguards.
```bash
rg '^(go|module)[[:space:](]' -g 'go.mod' .
terraform test -test-directory=tests/unit/
```
```hcl
# tests/unit/main.tftest.hcl
run "example" {}
```
''')
        self.assertEqual(validate_repo.validate_skill(path), [])

    def test_fenced_bundled_script_reference_is_still_checked(self):
        path = self.skill('alpha', '```bash\npython3 scripts/missing.py\n```')
        self.assertTrue(any('unresolved resource scripts/missing.py' in error
                            for error in validate_repo.validate_skill(path)))

    def test_escape_and_missing_code_resource_fail(self):
        path = self.skill('alpha', '[escape](../../outside.md)\nRead `scripts/missing.py`.')
        errors = validate_repo.validate_skill(path)
        self.assertTrue(any('escapes skills tree' in e for e in errors), errors)
        self.assertTrue(any('unresolved resource scripts/missing.py' in e for e in errors), errors)

    def test_metadata_license_and_multiline_description(self):
        path = self.skill('alpha', fields='license: MIT\ncompatibility: Python 3\nmetadata:\n  version: "1.0"\n')
        self.assertEqual(validate_repo.validate_skill(path), [])

    def test_agent_yaml_icons_resolve_from_skill_root(self):
        path = self.skill('alpha')
        (path / 'agents').mkdir()
        (path / 'assets').mkdir()
        (path / 'assets' / 'small.svg').write_text('<svg/>')
        (path / 'agents' / 'openai.yaml').write_text('interface:\n  icon_small: "./assets/small.svg"\n  icon_large: "./assets/missing.png"\n')
        errors = validate_repo.validate_skill(path)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn('unresolved resource ./assets/missing.png', errors[0])
        (path / 'assets' / 'missing.png').write_bytes(b'fixture')
        self.assertEqual(validate_repo.validate_skill(path), [])
        text = (path / 'SKILL.md').read_text().replace('description: Use this portable testing workflow for validation of resources.', 'description: >-\n  Use this portable testing workflow\n  for validation of resources.')
        (path / 'SKILL.md').write_text(text)
        self.assertEqual(validate_repo.validate_skill(path), [])

    def test_new_script_never_executed_by_validation(self):
        path = self.skill('alpha', 'Read `scripts/integration.py`.')
        (path / 'scripts').mkdir()
        (path / 'scripts' / 'integration.py').write_text('raise RuntimeError("must never execute")\n')
        with patch.object(validate_repo.subprocess, 'run', side_effect=AssertionError('unexpected execution')):
            self.assertEqual(validate_repo.validate_skill(path, run_help=True), [])

    def test_invalid_plain_scalar_and_duplicate_fields_are_rejected(self):
        path = self.skill('alpha', fields='license: MIT\nlicense: MIT\n')
        self.assertTrue(any('duplicate top-level' in error for error in validate_repo.validate_skill(path)))
        path = self.skill('beta')
        (path / 'SKILL.md').write_text((path / 'SKILL.md').read_text().replace(
            'Use this portable testing workflow for validation of resources.',
            'Use this workflow for validation. Read-only: it never changes resources.'))
        self.assertTrue(any('quote a scalar' in error for error in validate_repo.validate_skill(path)))

    def test_installed_tree_keeps_complete_closure_without_repository_files(self):
        self.skill('alpha', '[beta](../beta/SKILL.md)')
        self.skill('beta')
        dest = self.root / 'installed'
        install_skills.install(self.skills, dest, ['alpha'], apply=True)
        self.assertEqual(validate_repo.validate_skill(dest / 'alpha'), [])
        self.assertEqual(validate_repo.validate_skill(dest / 'beta'), [])
        self.assertEqual(validate_repo.skill_dependencies(dest / 'alpha', dest), {'beta'})
        self.assertFalse((self.root / 'scripts').exists())


if __name__ == '__main__':
    unittest.main()
