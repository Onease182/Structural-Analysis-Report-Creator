from pathlib import Path
import unittest

from src.e2k_parser import E2KParser

ROOT = Path(__file__).resolve().parents[1]
ULS = ROOT / "tables" / "Chatra Bahadur Ramel_ULS.e2k"
SLS = ROOT / "sls_tables" / "Chatra Bahadur Ramel_SLS.e2k"


class RealE2KTests(unittest.TestCase):
    def parse(self, path):
        return E2KParser().parse_file(path)

    def test_real_uls_geometry_materials_and_sections(self):
        data = self.parse(ULS)
        stories = {r["Story"]: r for r in data["stories"]}
        self.assertEqual([stories[f"Story{i}"]["StoryHt"] for i in (1, 2, 3)], ["3175"] * 3)
        self.assertEqual(stories["Base"]["Elevation"], "0")

        materials = {r["Material"]: r for r in data["materials"]}
        self.assertEqual(materials["M20"]["Fc"], "20")
        self.assertEqual(materials["HYSD500"]["Fy"], "500")

        frames = {r["Section"]: r for r in data["frame_sections"]}
        self.assertEqual((frames["Column 355 x 355"]["t2"], frames["Column 355 x 355"]["t3"]), ("355", "355"))
        self.assertEqual((frames["Beam 250 x 430"]["t2"], frames["Beam 250 x 430"]["t3"]), ("250", "430"))
        slab = next(r for r in data["slab_properties"] if r["Section"] == "Slab 125")
        self.assertEqual(slab["Thickness"], "125")

    def test_real_uls_parser_sections_and_seismic_data(self):
        data = self.parse(ULS)
        self.assertTrue(data["concrete_sections"])
        self.assertTrue(data["controls"])
        self.assertTrue(data["concrete_design_preferences"])
        self.assertTrue(data["frame_object_loads"])
        self.assertTrue(data["shell_object_loads"])
        self.assertEqual(data["point_object_loads"], [])
        self.assertTrue(data["restraints"])
        self.assertEqual(data["restraints"][0]["Story"], "Base")
        self.assertTrue(data["property_modifiers"])

        modifiers = {r["Section"]: r for r in data["frame_modifiers"]}
        self.assertEqual(modifiers["Beam 250 x 430"]["I2MOD"], "0.35")
        self.assertEqual(modifiers["Column 355 x 355"]["I2MOD"], "0.7")
        seismic = next(r for r in data["load_patterns"] if r.get("LoadPat") == "EQX-ULS" and "SHEARCOEFF" in r)
        self.assertEqual(seismic["SHEARCOEFF"], "0.1458")
        self.assertEqual(seismic["ECC"], "0.05")
        self.assertEqual(seismic["TOPSTORY"], "Story3")
        self.assertEqual(seismic["BOTTOMSTORY"], "Base")
        self.assertEqual(len(data["load_combinations"]), 12)

    def test_real_sls_modifiers_and_same_geometry(self):
        data = self.parse(SLS)
        modifiers = {r["Section"]: r for r in data["frame_modifiers"]}
        self.assertEqual(modifiers["Beam 250 x 430"]["I2MOD"], "0.7")
        self.assertEqual(modifiers["Column 355 x 355"]["I2MOD"], "0.9")
        self.assertEqual(next(r for r in data["slab_properties"] if r["Section"] == "Slab 125")["Thickness"], "125")


if __name__ == "__main__":
    unittest.main()
