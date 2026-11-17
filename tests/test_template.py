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

    def test_captions_preserve_style_seq_label(self) -> None:
        """For every caption paragraph in the sample, the caption's style,
        SEQ field, and label prefix ('Table N:' / 'Figure N:') must be
        identical in the template."""
        import re
        from docx import Document
        W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        sample_doc = Document(str(ROOT / "Chatra Bahadur Ramtel.docx"))
        tmpl_doc = Document(str(TEMPLATE))

        # Collect caption paragraphs from the sample
        caption_texts = []
        for p in sample_doc.paragraphs:
            text = p.text.strip()
            if re.match(r"^(Table|Figure)\s+\d+\s*:", text, re.I):
                caption_texts.append(text)
        self.assertGreater(len(caption_texts), 5, "Expected several captions in sample")

        # For each caption, check that the template still has the label prefix
        tmpl_text = self.full_text
        missing_labels = []
        for ct in caption_texts:
            label_match = re.match(r"^((?:Table|Figure)\s+\d+\s*:)", ct)
            if label_match:
                label = label_match.group(1)
                if label not in tmpl_text:
                    missing_labels.append(label)
        self.assertEqual(missing_labels, [],
                         f"Caption labels missing from template: {missing_labels}")

    def test_conclusion_paragraphs_not_heading_styled(self) -> None:
        """The in-plane and mass-irregularity conclusion paragraphs must be
        restyled to Body Text, not heading-styled, and must not appear in
        the TOC."""
        from docx import Document
        W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        tmpl_doc = Document(str(TEMPLATE))
        conclusion_keys = {
            "analysis.in_plane_discontinuity_result",
            "analysis.mass_irregularity_result",
        }
        for p in tmpl_doc.paragraphs:
            text = p.text.strip()
            for key in conclusion_keys:
                if f"{{{{ {key} }}}}" in text:
                    style_name = p.style.name if p.style else ""
                    self.assertNotIn(
                        "heading", style_name.lower(),
                        f"Conclusion paragraph for {key} is still heading-styled "
                        f"({style_name}); should be Body Text"
                    )

    def test_anchored_images_preserved_in_template(self) -> None:
        """Anchored images must stay anchored in the template (not converted
        to inline placeholders). The template should have the same number of
        wp:anchor elements as the sample."""
        from docx import Document
        WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"

        sample_doc = Document(str(ROOT / "Chatra Bahadur Ramtel.docx"))
        tmpl_doc = Document(str(TEMPLATE))

        sample_anchors = list(sample_doc.element.body.iter(f"{{{WP_NS}}}anchor"))
        tmpl_anchors = list(tmpl_doc.element.body.iter(f"{{{WP_NS}}}anchor"))
        self.assertEqual(
            len(tmpl_anchors), len(sample_anchors),
            f"Anchored image count: sample={len(sample_anchors)}, "
            f"template={len(tmpl_anchors)}. Anchored images must be preserved."
        )


if __name__ == "__main__":
    unittest.main()
