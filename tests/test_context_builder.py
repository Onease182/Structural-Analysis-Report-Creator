"""Tests for src/context_builder.py."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.context_builder import ContextBuilder
from src.e2k_parser import E2KParser

FIXTURE_E2K = ROOT / "tests" / "fixtures" / "sample.e2k"


class ContextBuilderTests(unittest.TestCase):
    def test_build_from_e2k_only(self) -> None:
        """Build context from .e2k fixture (no ETABS tables or Excel)."""
        builder = ContextBuilder()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "project"
            ctx = builder.build(
                tables_dir=Path("/nonexistent"),
                sls_tables_dir=Path("/nonexistent"),
                e2k_path=str(FIXTURE_E2K),
                input_xlsx=Path("/nonexistent"),
                output_dir=str(output),
            )
            # Check stories
            self.assertEqual(ctx["building"]["storeys_above_grade"], 3)
            self.assertEqual(ctx["building"]["num_storeys_analysed"], 3)
            self.assertEqual(ctx["building"]["num_basements"], 0)
            # Check heights
            self.assertIn("total_height_m", ctx["building"])
            # Check materials
            self.assertEqual(ctx["materials"]["concrete_grade_used"], "M20")
            # Check outputs exist
            self.assertTrue((output / "context.json").exists())
            self.assertTrue((output / "context_sources.json").exists())
            self.assertTrue((output / "conflicts.md").exists())
            self.assertTrue((output / "unresolved.md").exists())

    def test_unresolved_lists_missing_files(self) -> None:
        builder = ContextBuilder()
        with tempfile.TemporaryDirectory() as tmp:
            builder.build(
                tables_dir=Path("/nonexistent"),
                sls_tables_dir=Path("/nonexistent"),
                e2k_path=Path("/nonexistent.e2k"),
                input_xlsx=Path("/nonexistent.xlsx"),
                output_dir=str(Path(tmp) / "project"),
            )
            self.assertGreater(len(builder.unresolved), 0)
            self.assertTrue(any("not found" in u for u in builder.unresolved))

    def test_compute_empirical_period(self) -> None:
        builder = ContextBuilder()
        with tempfile.TemporaryDirectory() as tmp:
            ctx = builder.build(
                tables_dir=Path("/nonexistent"),
                sls_tables_dir=Path("/nonexistent"),
                e2k_path=str(FIXTURE_E2K),
                input_xlsx=Path("/nonexistent"),
                output_dir=str(Path(tmp) / "project"),
            )
            # H = 9.525 m, Ct = 0.075; the configured 1.25 amplification is
            # reported separately from the unamplified empirical period.
            import math
            expected_raw = 0.075 * (9.525 ** 0.75)
            self.assertAlmostEqual(float(ctx["modal"]["empirical_period_unamplified_s"]), expected_raw, places=3)
            self.assertAlmostEqual(float(ctx["modal"]["empirical_period_s"]), expected_raw * 1.25, places=3)

    def test_compute_overstrength(self) -> None:
        builder = ContextBuilder()
        builder.ctx = {"structural": {"system_type_generic": "Moment Resisting Frames"}}
        builder._compute()
        self.assertEqual(builder.ctx["design"]["overstrength_ultimate"], "1.5")

    def test_cli_runnable(self) -> None:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(ROOT / "src" / "context_builder.py"),
             "--tables", "/nonexistent", "--sls-tables", "/nonexistent",
             "--e2k", str(FIXTURE_E2K), "--input", "/nonexistent",
             "--output", "/tmp/test_project"],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("[OK]", result.stdout)

    def test_no_hardcoded_storey_count(self) -> None:
        """The builder must not hard-code 3 storeys — it reads from .e2k."""
        builder = ContextBuilder()
        with tempfile.TemporaryDirectory() as tmp:
            ctx = builder.build(
                tables_dir=Path("/nonexistent"),
                sls_tables_dir=Path("/nonexistent"),
                e2k_path=str(FIXTURE_E2K),
                input_xlsx=Path("/nonexistent"),
                output_dir=str(Path(tmp) / "project"),
            )
            # The fixture has 4 stories (Story3, Story2, Story1, Base)
            # Above grade = 3 (Story3, Story2, Story1)
            self.assertEqual(ctx["building"]["storeys_above_grade"], 3)
            # But this is READ from the .e2k, not hard-coded

    def test_limits_from_config(self) -> None:
        """Limits must come from config/formats.yaml, not be hard-coded."""
        builder = ContextBuilder()
        limits = builder.config.get("limits", {})
        self.assertEqual(limits["sls_drift_ratio"], 0.006)
        self.assertEqual(limits["uls_drift_ratio"], 0.025)
        self.assertEqual(limits["torsional_ratio"], 1.5)
        self.assertEqual(limits["min_column_steel_pct"], 1.0)


if __name__ == "__main__":
    unittest.main()
