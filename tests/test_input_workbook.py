"""Tests for src/input_workbook.py."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class InputWorkbookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import openpyxl  # noqa: F401
            cls.has_openpyxl = True
        except ImportError:
            cls.has_openpyxl = False

    def setUp(self) -> None:
        if not self.has_openpyxl:
            self.skipTest("openpyxl not installed")

    def test_generate_creates_workbook(self) -> None:
        from src.input_workbook import InputWorkbook
        wb = InputWorkbook()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test_input.xlsx"
            wb.generate(path)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 1000)

    def test_read_returns_dict_and_missing(self) -> None:
        from src.input_workbook import InputWorkbook
        wb = InputWorkbook()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test_input.xlsx"
            wb.generate(path)
            data, missing = wb.read(path)
            self.assertIsInstance(data, dict)
            self.assertIsInstance(missing, list)
            # All cells should be missing (empty workbook)
            self.assertGreater(len(missing), 0)

    def test_read_filled_workbook(self) -> None:
        from src.input_workbook import InputWorkbook
        import openpyxl
        wb = InputWorkbook()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test_filled.xlsx"
            wb.generate(path)
            # Fill in some values
            wb2 = openpyxl.load_workbook(path)
            ws = wb2["Project & Client"]
            ws.cell(2, 3, "Test Report Title")
            ws.cell(3, 3, "Test Owner")
            wb2.save(path)
            data, missing = wb.read(path)
            self.assertEqual(data.get("project", {}).get("report_title"), "Test Report Title")
            self.assertEqual(data.get("client", {}).get("owner_name"), "Test Owner")
            # Should have fewer missing
            self.assertLess(len(missing), 100)

    def test_cli_runnable(self) -> None:
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(ROOT / "src" / "input_workbook.py"),
                 "generate", "--output", str(Path(tmp) / "cli_test.xlsx")],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("[OK]", result.stdout)


if __name__ == "__main__":
    unittest.main()
