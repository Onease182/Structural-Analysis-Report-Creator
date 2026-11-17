"""Tests for the master template generation (Phase 2)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEMPLATE = ROOT / "templates" / "master_template.docx"
REPLACEMENT_LOG = ROOT / "docs" / "template_replacement_log.md"
REGISTRY = ROOT / "config" / "placeholder_registry.yaml"
MAKE_TEMPLATE = ROOT / "tools" / "make_template.py"
VERIFY_TEMPLATE = ROOT / "tools" / "verify_template.py"


class TemplateExistenceTests(unittest.TestCase):
    """The template and replacement log must exist after make_template.py runs."""

    def test_template_docx_exists(self) -> None:
        self.assertTrue(TEMPLATE.exists(), f"Template not found: {TEMPLATE}")
        self.assertGreater(TEMPLATE.stat().st_size, 1000,
                           "Template file is suspiciously small")

    def test_replacement_log_exists(self) -> None:
        self.assertTrue(REPLACEMENT_LOG.exists(),
                        f"Replacement log not found: {REPLACEMENT_LOG}")
        content = REPLACEMENT_LOG.read_text(encoding="utf-8")
        self.assertIn("# Template Replacement Log", content)
        self.assertIn("Total replacements:", content)

    def test_make_template_script_exists(self) -> None:
        self.assertTrue(MAKE_TEMPLATE.exists())
        self.assertTrue(VERIFY_TEMPLATE.exists())


class StrictModeTests(unittest.TestCase):
    """Strict mode: the generator must fail if any codes.clauses.* entry
    has a null or empty target_clause_2025."""

    def test_no_clause_has_null_target_in_registry(self) -> None:
        with REGISTRY.open("r", encoding="utf-8") as f:
            entries = yaml.safe_load(f)["items"]
        bad = [e["key"] for e in entries
               if e["key"].startswith("codes.clauses.")
               and not e.get("target_clause_2025")]
        self.assertEqual(bad, [], f"Clauses with null target: {bad}")

    def test_strict_mode_validator_catches_null_targets(self) -> None:
        """The validate_registry_strict function must raise on null targets."""
        from tools import make_template
        bad_entries = [
            {"key": "codes.clauses.test", "target_clause_2025": None},
        ]
        with self.assertRaises(ValueError) as ctx:
            make_template.validate_registry_strict(bad_entries)
        self.assertIn("test", str(ctx.exception))

    def test_strict_mode_validator_catches_empty_targets(self) -> None:
        from tools import make_template
        bad_entries = [
            {"key": "codes.clauses.test", "target_clause_2025": ""},
        ]
        with self.assertRaises(ValueError):
            make_template.validate_registry_strict(bad_entries)

    def test_strict_mode_accepts_valid_targets(self) -> None:
        from tools import make_template
        good_entries = [
            {"key": "codes.clauses.test", "target_clause_2025": "5.4.1.2"},
        ]
        # Should not raise
        make_template.validate_registry_strict(good_entries)


class TemplatePlaceholderTests(unittest.TestCase):
    """The template must contain docxtpl placeholders and no unmatched text."""

    @classmethod
    def setUpClass(cls) -> None:
        from docx import Document
        W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        doc = Document(str(TEMPLATE))
        body = doc.element.body
        cls.full_text = "".join((t.text or "") for t in body.iter(f"{{{W_NS}}}t"))

    def test_template_contains_text_placeholders(self) -> None:
        import re
        text_placeholders = re.findall(r"\{\{\s*\w+", self.full_text)
        self.assertGreater(len(text_placeholders), 10,
                           "Template should have many {{ }} text placeholders")

    def test_template_contains_staircase_conditional(self) -> None:
        self.assertIn("{%p if building.has_staircase %}", self.full_text)
        self.assertIn("{%p endif %}", self.full_text)

    def test_template_contains_table_row_templates(self) -> None:
        self.assertIn("{%tr for r in rows %}", self.full_text)
        self.assertIn("{%tr endfor %}", self.full_text)

    def test_template_contains_clause_placeholders(self) -> None:
        self.assertIn("{{ codes.clauses.", self.full_text)
        self.assertIn("{{ codes.edition }}", self.full_text)

    def test_template_contains_figure_placeholders(self) -> None:
        self.assertIn("{{ figure.", self.full_text)


if __name__ == "__main__":
    unittest.main()
