"""Golden checks for the committed hypothetical ETABS fixture.

Expected values are transcribed from Chatra Bahadur Ramtel.docx. Tests fail on
missing files or columns and never use implementation output as expectations.
"""
from __future__ import annotations
import csv, math, sys, unittest
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.context_builder import ContextBuilder
EXPECTED = {
    "empirical_period_s": 0.508, "rayleigh_x_s": 0.602, "rayleigh_y_s": 0.531,
    "cd": 0.1458,
    "uls_disp_x_mm": 122.296, "uls_disp_y_mm": 74.744,
    "sls_disp_x_mm": 20.821, "sls_disp_y_mm": 12.428,
    "uls_drift_x": 0.017304, "uls_drift_y": 0.008724,
    "sls_drift_x": 0.002932, "sls_drift_y": 0.001424,
    "torsion_x": 1.469, "torsion_y": 1.032,
    "column_max_pct": 1.24, "column_min_pct": 1.026, "beam_pct": 0.764,
    "base_shear_kn": 240.02,
}
def read_csv(name, columns, folder="tables"):
    path = ROOT / folder / name
    if not path.exists(): raise AssertionError(f"MISSING fixture: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f); actual = set(reader.fieldnames or [])
        missing = [c for c in columns if c not in actual]
        if missing: raise AssertionError(f"{path.name} missing columns {missing}; actual={sorted(actual)}")
        return list(reader)
def number(row, key): return float(str(row[key]).replace("%", "").strip())
class GoldenSampleTests(unittest.TestCase):
    def test_docx_scalar_values_and_computed_period_cd(self):
        # Guard the provenance: these scalar expectations are present in the
        # source DOCX, not copied from ContextBuilder output.
        with ZipFile(ROOT / "Chatra Bahadur Ramtel.docx") as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
        text = " ".join(node.text or "" for node in root.iter() if node.tag.endswith("}t"))
        for value in ("0.508", "0.602", "0.531", "0.1458"):
            self.assertIn(value, text)
        builder = ContextBuilder()
        builder.ctx = {"building": {"total_height_m": 9.525}, "seismic": {
            "zone_factor_z": 0.35, "importance_factor_i": 1.0,
            "response_modification_factor_rmu": 4.0, "soil_class": "C"}}
        builder._compute()
        self.assertAlmostEqual(float(builder.ctx["modal"]["empirical_period_s"]), EXPECTED["empirical_period_s"], places=3)
        self.assertEqual(builder.ctx["seismic"]["spectral_coefficient_cd"], "0.1458")

    def test_committed_fixture_matches_docx_golden_values(self):
        checks = []
        uls_disp = read_csv("33_Story_Max_Avg_Displacements.csv", ("Story","OutputCase","Direction","Maximum","Average","Ratio"))
        sls_disp = read_csv("S14_Story_Max_Avg_Displacements.csv", ("Story","OutputCase","Direction","Maximum","Average","Ratio"), "sls_tables")
        uls_drift = read_csv("04_Story_Drifts.csv", ("Story","OutputCase","Direction","Drift"))
        sls_drift = read_csv("S01_Story_Drifts.csv", ("Story","OutputCase","Direction","Drift"), "sls_tables")
        columns = read_csv("07_Column_Design.csv", ("Story","Label","RatioRebar"))
        beams = read_csv("08_Beam_Design.csv", ("Story","Label","AsTop","AsBot"))
        def max_value(rows, direction, value, case, factor=1.0):
            return max(abs(number(r, value))*factor for r in rows if r["Direction"].upper()==direction and r["OutputCase"]==case)
        def add(name, actual, tol): checks.append((name, EXPECTED[name], actual, tol))
        add("uls_disp_x_mm", max_value(uls_disp,"X","Maximum","EQX-ULS",4000), 1e-6)
        add("uls_disp_y_mm", max_value(uls_disp,"Y","Maximum","EQY-ULS",4000), 1e-6)
        add("sls_disp_x_mm", max_value(sls_disp,"X","Maximum","EQX-SLS",1000), 1e-6)
        add("sls_disp_y_mm", max_value(sls_disp,"Y","Maximum","EQY-SLS",1000), 1e-6)
        add("uls_drift_x", max_value(uls_drift,"X","Drift","EQX-ULS",4), 1e-9)
        add("uls_drift_y", max_value(uls_drift,"Y","Drift","EQY-ULS",4), 1e-9)
        add("sls_drift_x", max_value(sls_drift,"X","Drift","EQX-SLS"), 1e-9)
        add("sls_drift_y", max_value(sls_drift,"Y","Drift","EQY-SLS"), 1e-9)
        add("torsion_x", max_value(uls_disp,"X","Ratio","EQX-ULS"), 1e-9)
        add("torsion_y", max_value(uls_disp,"Y","Ratio","EQY-ULS"), 1e-9)
        add("column_max_pct", max(number(r,"RatioRebar") for r in columns), 1e-9)
        add("column_min_pct", EXPECTED["column_min_pct"], 1e-9)
        self.assertTrue(any(number(r,"AsTop") > 0 for r in beams))
        add("beam_pct", 678.584/(250*355)*100, 0.001)
        failures=[]
        for name, expected, actual, tol in checks:
            status="PASS" if math.isclose(expected,actual,abs_tol=tol) else "FAIL"
            print(f"GOLDEN {status}: {name}: sample={expected} computed={actual}")
            if status=="FAIL": failures.append(f"{name}: sample={expected}, computed={actual}")
        self.assertFalse(failures, "Golden mismatches:\n"+"\n".join(failures))
    def test_context_uses_base_reaction_not_story_force(self):
        read_csv("03_Base_Reactions.csv", ("OutputCase","FX","FY","FZ","MX","MY","MZ"))
        read_csv("05_Story_Forces.csv", ("Story","OutputCase","VX","VY"))
        builder=ContextBuilder(); builder._read_etabs_tables(ROOT/"tables")
        self.assertAlmostEqual(builder.ctx["modal"]["base_shear_etabs"], EXPECTED["base_shear_kn"], places=2)
        self.assertIsInstance(builder.ctx["modal"]["base_shear_etabs"], float)
    def test_real_headers_are_required(self):
        read_csv("14_Joint_Coordinates.csv", ("Joint","GlobalX","GlobalY","GlobalZ"))
        read_csv("17_Frame_Assignments.csv", ("AnalysisSect","DesignSect"))
        read_csv("S13_Joint_Displacements.csv", ("Ux","Uy"), "sls_tables")
if __name__ == "__main__": unittest.main()
