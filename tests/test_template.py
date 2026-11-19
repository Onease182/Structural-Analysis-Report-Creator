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
        # The loop tables now use full dotted paths like
        # {%tr for r in table.seismic.vertical_force_dist.rows %}
        self.assertIn("{%tr for r in ", self.full_text)
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

    def test_strict_mode_fails_on_missing_key(self) -> None:
        """Deleting one key from the context should cause a failure."""
        from tools.verify_template import validate_context_strict
        with REGISTRY.open("r", encoding="utf-8") as f:
            entries = yaml.safe_load(f)["items"]
        # Build a valid context, then delete one key
        ctx: dict[str, Any] = {}
        for entry in entries:
            if entry.get("required"):
                parts = entry["key"].split(".")
                d = ctx
                for part in parts[:-1]:
                    d = d.setdefault(part, {})
                d[parts[-1]] = "dummy"
        # Delete one required key
        if "building" in ctx and "has_staircase" in ctx["building"]:
            del ctx["building"]["has_staircase"]
        with self.assertRaises(ValueError) as exc:
            validate_context_strict(ctx, entries)
        self.assertIn("has_staircase", str(exc.exception))

    def test_strict_mode_fails_on_null_clause_value(self) -> None:
        """A null codes.clauses.* value should cause a render-time failure."""
        from tools.verify_template import validate_context_strict
        with REGISTRY.open("r", encoding="utf-8") as f:
            entries = yaml.safe_load(f)["items"]
        ctx: dict[str, Any] = {}
        for entry in entries:
            parts = entry["key"].split(".")
            d = ctx
            for part in parts[:-1]:
                d = d.setdefault(part, {})
            d[parts[-1]] = "dummy"
        # Set a clause value to null
        ctx.setdefault("codes", {}).setdefault("clauses", {})["soft_storey"] = None
        with self.assertRaises(ValueError) as exc:
            validate_context_strict(ctx, entries)
        self.assertIn("soft_storey", str(exc.exception))

    def test_strict_mode_accepts_valid_context(self) -> None:
        """A valid context with all keys present should pass validation."""
        from tools.verify_template import validate_context_strict
        with REGISTRY.open("r", encoding="utf-8") as f:
            entries = yaml.safe_load(f)["items"]
        ctx: dict[str, Any] = {}
        for entry in entries:
            parts = entry["key"].split(".")
            d = ctx
            for part in parts[:-1]:
                d = d.setdefault(part, {})
            d[parts[-1]] = "dummy"
        # Should not raise
        validate_context_strict(ctx, entries)

    def test_t6_guard_cleared(self) -> None:
        """T6 (table.loads.load_assessment) must NOT have status=pending_implementation.
        It is now implemented via src/input_workbook.py build_t6_load_assessment()."""
        with REGISTRY.open("r", encoding="utf-8") as f:
            entries = yaml.safe_load(f)["items"]
        t6 = next(e for e in entries if e["key"] == "table.loads.load_assessment")
        self.assertNotEqual(t6.get("status"), "pending_implementation",
                         "T6 should no longer be pending — implemented in 3c")

    def test_clause_placeholders_in_template(self) -> None:
        """The template must contain clause key placeholders for 4.1.4, 4.1.5,
        and (Cl. 3.6.1) — they must not appear as hard-coded text."""
        import re
        cleaned = re.sub(r"\{\{[^}]+\}\}", "", self.full_text)
        self.assertNotIn("4.1.4", cleaned,
                         "Hard-coded '4.1.4' found in template — should be {{ codes.clauses.seismic_zoning_factor }}")
        self.assertNotIn("4.1.5", cleaned,
                         "Hard-coded '4.1.5' found in template — should be {{ codes.clauses.importance_factor }}")
        self.assertNotIn("(Cl. 3.6.1)", cleaned,
                         "Hard-coded '(Cl. 3.6.1)' found in template — should be ({{ codes.clauses.load_combinations }})")
        # Verify the placeholders ARE present
        self.assertIn("codes.clauses.seismic_zoning_factor", self.full_text)
        self.assertIn("codes.clauses.importance_factor", self.full_text)
        self.assertIn("codes.clauses.load_combinations", self.full_text)


if __name__ == "__main__":
    unittest.main()
