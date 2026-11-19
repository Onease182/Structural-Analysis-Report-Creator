"""Tests for src/e2k_parser.py."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.e2k_parser import E2KParser

FIXTURE = ROOT / "tests" / "fixtures" / "sample.e2k"


class E2KParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parser = E2KParser()
        cls.data = cls.parser.parse_file(str(FIXTURE))

    def test_parses_stories(self) -> None:
        stories = self.data.get("stories", [])
        self.assertEqual(len(stories), 4)
        self.assertEqual(stories[0]["Story"], "Story3")
        self.assertEqual(stories[0]["StoryHt"], "3.175")
        self.assertEqual(stories[0]["Elevation"], "9.525")

    def test_parses_grids(self) -> None:
        grids = self.data.get("grids", [])
        self.assertGreater(len(grids), 0)

    def test_parses_points(self) -> None:
        points = self.data.get("points", [])
        self.assertEqual(len(points), 8)
        self.assertEqual(points[0]["Point"], "1")

    def test_parses_frames(self) -> None:
        frames = self.data.get("frames", [])
        self.assertEqual(len(frames), 5)
        col = next(f for f in frames if f["Type"] == "Column")
        self.assertEqual(col["Sec"], "C355x355")

    def test_parses_areas(self) -> None:
        areas = self.data.get("areas", [])
        self.assertEqual(len(areas), 1)

    def test_parses_frame_sections(self) -> None:
        sections = self.data.get("frame_sections", [])
        self.assertEqual(len(sections), 2)
        c355 = next(s for s in sections if s["Section"] == "C355x355")
        self.assertEqual(c355["Material"], "M20")

    def test_parses_materials(self) -> None:
        materials = self.data.get("materials", [])
        self.assertEqual(len(materials), 2)
        m20 = next(m for m in materials if m["Material"] == "M20")
        self.assertEqual(m20["Fc"], "20")

    def test_parses_restraints(self) -> None:
        restraints = self.data.get("restraints", [])
        self.assertEqual(len(restraints), 4)
        r = restraints[0]
        self.assertEqual(r["U1"], "Yes")

    def test_parses_load_patterns(self) -> None:
        lps = self.data.get("load_patterns", [])
        self.assertEqual(len(lps), 7)
        dead = next(lp for lp in lps if lp["LoadPat"] == "DEAD")
        self.assertEqual(dead["Type"], "Dead")

    def test_parses_load_combos(self) -> None:
        combos = self.data.get("load_combos", [])
        self.assertEqual(len(combos), 4)

    def test_parses_mass_source(self) -> None:
        ms = self.data.get("mass_source", [])
        self.assertEqual(len(ms), 2)

    def test_parses_diaphragms(self) -> None:
        diaph = self.data.get("diaphragms", [])
        self.assertEqual(len(diaph), 3)

    def test_unparsed_sections_kept(self) -> None:
        unparsed = self.data.get("unparsed", [])
        # "ETABSNINETYDAYFREELICENSE", "FOREDUCATIONALUSEONLY", "UNPARSED_SECTION"
        self.assertGreaterEqual(len(unparsed), 1)
        self.assertTrue(any("UNPARSED_SECTION" in u for u in unparsed))

    def test_reconcile_no_tables_dir(self) -> None:
        parser = E2KParser()
        parser.parse_file(str(FIXTURE))
        mismatches = parser.reconcile("/nonexistent", None)
        self.assertTrue(any("not found" in m for m in mismatches))

    def test_cli_runnable(self) -> None:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(ROOT / "src" / "e2k_parser.py"),
             "--input", str(FIXTURE), "--tables", "/nonexistent",
             "--output", "/tmp/e2k_test_report.md"],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("[OK]", result.stdout)


if __name__ == "__main__":
    unittest.main()
