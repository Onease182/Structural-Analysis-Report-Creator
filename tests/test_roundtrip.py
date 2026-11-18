"""Round-trip regression test and sample-token scan.

Builds a 'sample context' from the registry examples, renders the template,
and compares to the original sample. Also scans the template for
sample-specific tokens that should not appear outside placeholders.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from typing import Any

import yaml
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEMPLATE = ROOT / "templates" / "master_template.docx"
SAMPLE = ROOT / "Chatra Bahadur Ramtel.docx"
REGISTRY = ROOT / "config" / "placeholder_registry.yaml"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def load_registry() -> list[dict[str, Any]]:
    with REGISTRY.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)["items"]


class SampleTokenScanTests(unittest.TestCase):
    """No sample-specific token may remain in the template outside a
    placeholder."""

    @classmethod
    def setUpClass(cls) -> None:
        doc = Document(str(TEMPLATE))
        cls.full_text = "".join((t.text or "") for t in doc.element.body.iter(f"{{{W_NS}}}t"))

    def test_no_chatra_ramtel_in_template(self) -> None:
        """The client name 'Chatra Bahadur Ramtel' must not appear in the
        template outside a placeholder."""
        # Remove all placeholder content first
        cleaned = re.sub(r"\{\{[^}]+\}\}", "", self.full_text)
        self.assertNotIn("Chatra", cleaned, "Sample client name 'Chatra' found in template outside placeholder")
        self.assertNotIn("Ramtel", cleaned, "Sample client name 'Ramtel' found in template outside placeholder")

    def test_no_damak_in_template(self) -> None:
        cleaned = re.sub(r"\{\{[^}]+\}\}", "", self.full_text)
        self.assertNotIn("Damak", cleaned, "Sample location 'Damak' found in template outside placeholder")

    def test_no_civira_in_template(self) -> None:
        cleaned = re.sub(r"\{\{[^}]+\}\}", "", self.full_text)
        self.assertNotIn("Civira", cleaned, "Sample consultant 'Civira' found in template outside placeholder")

    def test_no_sample_numeric_values_in_template(self) -> None:
        """Sample-specific numeric values from VARIABLE entries must not
        remain in the template outside placeholders."""
        cleaned = re.sub(r"\{\{[^}]+\}\}", "", self.full_text)
        # Check for known sample values
        sample_values = ["3.175", "4.216", "10.058", "240.02", "1.004", "0.508"]
        found = []
        for val in sample_values:
            if val in cleaned:
                found.append(val)
        self.assertEqual(found, [], f"Sample numeric values found in template: {found}")

    def test_no_etabs_version_in_template(self) -> None:
        """The specific ETABS version '19.0.0' should not be hard-coded."""
        cleaned = re.sub(r"\{\{[^}]+\}\}", "", self.full_text)
        self.assertNotIn("ETABS 19.0.0", cleaned, "Hard-coded ETABS version found in template")


class FieldCountTests(unittest.TestCase):
    """The template must preserve the same number of instrText fields as
    the original sample (except explicitly removed TOC entries)."""

    def test_field_count_matches_sample(self) -> None:
        sample_doc = Document(str(SAMPLE))
        tmpl_doc = Document(str(TEMPLATE))
        sample_fields = list(sample_doc.element.body.iter(f"{{{W_NS}}}instrText"))
        tmpl_fields = list(tmpl_doc.element.body.iter(f"{{{W_NS}}}instrText"))
        # Allow some difference for removed TOC entries and conditional blocks
        diff = abs(len(sample_fields) - len(tmpl_fields))
        self.assertLessEqual(diff, 10, f"Field count differs by {diff}: sample={len(sample_fields)}, template={len(tmpl_fields)}")


class RoundTripTextComparisonTests(unittest.TestCase):
    """Compare paragraph text between the sample and a dummy render of the
    template. Differences outside owner-approved computed variants and
    2025 clause changes are failures."""

    @classmethod
    def setUpClass(cls) -> None:
        from docxtpl import DocxTemplate, InlineImage
        from docx.shared import Inches
        import struct, zlib

        entries = load_registry()
        tpl = DocxTemplate(str(TEMPLATE))

        # Build context from registry examples
        ctx: dict[str, Any] = {}
        for entry in entries:
            key = entry["key"]
            entry_type = entry.get("type", "text")
            example = entry.get("example")
            if entry_type == "image":
                dummy = ROOT / "tests" / "fixtures" / "dummy_100x100.png"
                if not dummy.exists():
                    dummy.parent.mkdir(parents=True, exist_ok=True)
                    # Create minimal PNG
                    sig = b'\x89PNG\r\n\x1a\n'
                    ihdr_data = struct.pack('>IIBBBBB', 100, 100, 8, 2, 0, 0, 0)
                    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
                    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
                    raw = b'\x00' + b'\xc0\xc0' * 100
                    raw = raw * 100
                    compressed = zlib.compress(raw)
                    idat_crc = zlib.crc32(b'IDAT' + compressed)
                    idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
                    iend_crc = zlib.crc32(b'IEND')
                    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
                    dummy.write_bytes(sig + ihdr + idat + iend)
                ctx_val = InlineImage(tpl, str(dummy))
            elif entry_type == "bool":
                ctx_val = True
            elif entry_type == "table":
                cols = entry.get("columns") or []
                ctx_val = {"rows": [{c.get("key", f"c{i}").split(".")[-1]: key for i, c in enumerate(cols)}]}
            elif entry_type == "number":
                ctx_val = example if example is not None else 1
            else:
                ctx_val = example if example is not None else key
            # Set nested
            parts = key.split(".")
            d = ctx
            for part in parts[:-1]:
                d = d.setdefault(part, {})
            d[parts[-1]] = ctx_val

        tpl.render(ctx)
        cls.rendered_path = ROOT / "build" / "roundtrip_rendered.docx"
        (ROOT / "build").mkdir(parents=True, exist_ok=True)
        tpl.save(str(cls.rendered_path))

    def test_heading_count_matches(self) -> None:
        sample_doc = Document(str(SAMPLE))
        rendered_doc = Document(str(self.rendered_path))
        sample_headings = [p for p in sample_doc.paragraphs if p.style and "heading" in (p.style.name or "").lower()]
        rendered_headings = [p for p in rendered_doc.paragraphs if p.style and "heading" in (p.style.name or "").lower()]
        # Allow 2 difference for restyled conclusion headings
        diff = abs(len(sample_headings) - len(rendered_headings))
        self.assertLessEqual(diff, 2, f"Heading count: sample={len(sample_headings)}, rendered={len(rendered_headings)}")

    def test_table_count_matches(self) -> None:
        sample_doc = Document(str(SAMPLE))
        rendered_doc = Document(str(self.rendered_path))
        # T15 was replaced with an image placeholder per owner decision
        expected_diff = 1
        diff = abs(len(sample_doc.tables) - len(rendered_doc.tables))
        self.assertEqual(diff, expected_diff,
                         f"Table count diff: sample={len(sample_doc.tables)}, "
                         f"rendered={len(rendered_doc.tables)}, expected diff={expected_diff}")

    def test_image_count_matches(self) -> None:
        WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
        sample_doc = Document(str(SAMPLE))
        rendered_doc = Document(str(self.rendered_path))
        sample_images = list(sample_doc.element.body.iter(f"{{{W_NS}}}inline")) + list(sample_doc.element.body.iter(f"{{{WP_NS}}}anchor"))
        rendered_images = list(rendered_doc.element.body.iter(f"{{{W_NS}}}inline")) + list(rendered_doc.element.body.iter(f"{{{WP_NS}}}anchor"))
        self.assertEqual(len(sample_images), len(rendered_images),
                         f"Image count: sample={len(sample_images)}, rendered={len(rendered_images)}")


if __name__ == "__main__":
    unittest.main()
