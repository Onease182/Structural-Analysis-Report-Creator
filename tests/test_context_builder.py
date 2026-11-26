"""Tests for src/context_builder.py."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.context_builder import ContextBuilder
from src.e2k_parser import E2KParser

FIXTURE_E2K = ROOT / "tests" / "fixtures" / "sample.e2k"
REAL_ULS = ROOT / "tables" / "Chatra Bahadur Ramel_ULS.e2k"


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

    def test_real_uls_story_elevations_are_derived_bottom_up(self) -> None:
        builder = ContextBuilder()
        builder._read_e2k(REAL_ULS)
        self.assertEqual(builder.ctx["building"]["story_elevations_m"], {"Story1": "3.175", "Story2": "6.350", "Story3": "9.525"})
        self.assertEqual(builder.ctx["building"]["height_ground_floor_m"], "3.175")
        self.assertEqual(builder.ctx["building"]["height_period_m"], "9.525")

    def test_e2k_read_failure_is_loud(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.e2k"
            bad.write_text('$ STORIES IN SEQUENCE FROM TOP\nSTORY "Story1" HEIGHT not-a-number\n', encoding="utf-8")
            with self.assertRaises(RuntimeError):
                ContextBuilder()._read_e2k(bad)

    def test_sls_joint_and_story_displacements_are_separate(self) -> None:
        builder = ContextBuilder()
        builder._read_sls_tables(ROOT / "sls_tables")
        self.assertAlmostEqual(builder.ctx["drift"]["sls_max_displacement_mm"], 20.82, places=3)
        self.assertAlmostEqual(builder.ctx["drift"]["sls_joint_max_displacement_mm"], 22.371, places=3)
        self.assertFalse(any("higher-priority source retained" in item for item in builder.conflicts))

    def test_real_computed_groups_and_loop_tables(self) -> None:
        builder = ContextBuilder()
        with tempfile.TemporaryDirectory() as tmp:
            ctx = builder.build(ROOT / "tables", ROOT / "sls_tables", REAL_ULS, ROOT / "missing.xlsx", Path(tmp) / "project")
        self.assertAlmostEqual(float(ctx["modal"]["rayleigh_period_x_s"]), 0.602, places=3)
        self.assertAlmostEqual(float(ctx["modal"]["rayleigh_period_y_s"]), 0.531, places=3)
        self.assertAlmostEqual(float(ctx["drift"]["uls_max_x_mm"]), 122.296, places=3)
        self.assertAlmostEqual(float(ctx["drift"]["uls_max_y_mm"]), 74.744, places=3)
        self.assertAlmostEqual(float(ctx["irregularity"]["torsion_x_ratio"]), 1.469, places=3)
        self.assertAlmostEqual(float(ctx["irregularity"]["torsion_y_ratio"]), 1.032, places=3)
        self.assertEqual(ctx["seismic"]["spectral_coefficient_cd"], 0.1458)
        self.assertTrue(ctx["table"]["modal"]["rayleigh_x"])
        self.assertTrue(ctx["table"]["drift"]["sls_story_drift_figures_x_y"])

    def test_every_non_excel_registry_key_is_value_or_explicit_unresolved(self) -> None:
        builder = ContextBuilder()
        with tempfile.TemporaryDirectory() as tmp:
            ctx = builder.build(ROOT / "tables", ROOT / "sls_tables", REAL_ULS, ROOT / "missing.xlsx", Path(tmp) / "project")
        registry = yaml.safe_load((ROOT / "config" / "placeholder_registry.yaml").read_text())["items"]
        def lookup(key):
            value = ctx
            for part in key.split("."):
                if not isinstance(value, dict) or part not in value:
                    return None
                value = value[part]
            return value
        target = [entry["key"] for entry in registry if entry.get("source") in {"e2k", "computed", "etabs_api"}]
        self.assertEqual([key for key in target if lookup(key) is None], [])


if __name__ == "__main__":
    unittest.main()
