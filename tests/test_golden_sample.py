"""Part A golden checks for the anonymised sample fixture and formula contracts."""
from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from src.context_builder import ContextBuilder


class GoldenSampleTests(unittest.TestCase):
    def test_periods_and_cd(self) -> None:
        builder = ContextBuilder()
        builder.ctx = {
            "building": {"total_height_m": 9.525},
            "seismic": {
                "zone_factor_z": 0.35,
                "importance_factor_i": 1.0,
                "response_modification_factor_rmu": 4.0,
                "soil_class": "C",
            },
        }
        builder._compute()
        raw = 0.075 * (9.525 ** 0.75)
        self.assertAlmostEqual(float(builder.ctx["modal"]["empirical_period_unamplified_s"]), raw, places=3)
        self.assertAlmostEqual(float(builder.ctx["modal"]["empirical_period_s"]), raw * 1.25, places=3)
        self.assertEqual(builder.ctx["seismic"]["spectral_coefficient_cd"], "0.1458")

    def test_rayleigh_uses_story_force_displacement_data(self) -> None:
        builder = ContextBuilder()
        builder.ctx = {
            "analysis": {"story_force_data": [
                {"story": "S2", "weight": 100.0, "force": 40.0, "displacement": 0.01},
                {"story": "S1", "weight": 80.0, "force": 30.0, "displacement": 0.02},
            ]}
        }
        builder._compute()
        expected = 2 * math.pi * math.sqrt((100 * .01**2 + 80 * .02**2) /
                                            (9.80665 * (40 * .01 + 30 * .02)))
        self.assertAlmostEqual(float(builder.ctx["modal"]["rayleigh_period_s"]), expected, places=3)

    def test_missing_csv_column_is_unresolved(self) -> None:
        builder = ContextBuilder()
        builder._process_story_drifts([{"Story": "S1", "OutputCase": "EQX"}], "04_Story_Drifts.csv")
        self.assertTrue(any("missing drift column" in item for item in builder.unresolved))

    def test_outputs_record_unresolved_values(self) -> None:
        builder = ContextBuilder()
        with tempfile.TemporaryDirectory() as tmp:
            builder._unresolved("example missing input")
            builder._write_outputs(Path(tmp))
            self.assertIn("UNRESOLVED: example missing input", (Path(tmp) / "unresolved.md").read_text())


if __name__ == "__main__":
    unittest.main()
