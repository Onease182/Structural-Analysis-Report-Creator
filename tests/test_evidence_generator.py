from pathlib import Path
import csv
import shutil
import tempfile
import unittest

from src.e2k_parser import E2KParser
from tools.generate_evidence import reconciliation

ROOT = Path(__file__).resolve().parents[1]
ULS = ROOT / "tables" / "Chatra Bahadur Ramel_ULS.e2k"
CHECKED_CSVS = (
    "12_Story_Definitions.csv",
    "17_Frame_Assignments.csv",
    "21_Materials.csv",
    "22b_Frame_Sect_Rect.csv",
    "28_Mass_Source.csv",
)


class EvidenceGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.data = E2KParser().parse_file(ULS)

    def make_tables(self):
        temp = tempfile.TemporaryDirectory()
        directory = Path(temp.name)
        for name in CHECKED_CSVS:
            shutil.copy2(ROOT / "tables" / name, directory / name)
        return temp, directory

    def test_real_reconciliation_has_no_false_unit_or_mass_mismatches(self):
        temp, directory = self.make_tables()
        try:
            result = reconciliation(self.data, directory)
            self.assertGreater(result["checked"], 0)
            self.assertEqual(result["mismatches"], [])
            self.assertEqual(result["checked"], result["matches"])
        finally:
            temp.cleanup()

    def test_wrong_section_unit_is_detected(self):
        temp, directory = self.make_tables()
        try:
            path = directory / "22b_Frame_Sect_Rect.csv"
            rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
            rows[0]["t2"] = "250"  # millimetres incorrectly substituted for CSV metres
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader(); writer.writerows(rows)
            result = reconciliation(self.data, directory)
            self.assertTrue(any("Beam 250 x 430.t2_m" in item for item in result["mismatches"]))
        finally:
            temp.cleanup()

    def test_wrong_mass_multiplier_is_detected(self):
        temp, directory = self.make_tables()
        try:
            path = directory / "28_Mass_Source.csv"
            rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
            for row in rows:
                if row["LoadPattern"] == "Live":
                    row["Multiplier"] = "0.31"
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader(); writer.writerows(rows)
            result = reconciliation(self.data, directory)
            self.assertTrue(any("Live.multiplier" in item for item in result["mismatches"]))
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
