from __future__ import annotations

from pathlib import Path
import tempfile
import yaml
from openpyxl import load_workbook

from src.input_workbook import InputWorkbook, registry_sheet_defs

ROOT = Path(__file__).resolve().parents[1]


def test_every_excel_registry_entry_has_a_workbook_row():
    registry = yaml.safe_load((ROOT / "config/placeholder_registry.yaml").read_text())
    keys = {item["key"] for item in registry["items"] if item.get("source") == "excel"}
    workbook_keys = {field["key"] for fields in registry_sheet_defs().values() for field in fields}
    assert keys <= workbook_keys


def test_workbook_has_required_topic_sheets_and_visual_controls():
    required = {
        "Project & Client", "Consultancy and Designer", "Site & Soil", "Codes",
        "Wall & Finish Loads", "Live Loads", "Foundation", "Staircase",
        "Irregularity Declarations", "Figures", "Sign-off",
    }
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "Project_Input.xlsx"
        InputWorkbook().generate(path)
        wb = load_workbook(path)
        assert required <= set(wb.sheetnames)
        assert any(ws.max_column >= 6 for ws in wb.worksheets)
        assert any(ws.data_validations.dataValidation for ws in wb.worksheets)
        ws = wb["Project & Client"]
        assert ws["C2"].fill.fgColor.rgb in {"00FFFFCC", "FFFFCC"}
        assert ws["D2"].fill.fgColor.rgb in {"00E0E0E0", "E0E0E0"}
        assert "hypothetical" in str(ws["E2"].value).lower()


def test_read_reports_precise_invalid_cell():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "Project_Input.xlsx"
        InputWorkbook().generate(path)
        wb = load_workbook(path)
        ws = wb["Project & Client"]
        ws["C5"] = "Not an occupancy"
        wb.save(path)
        _, missing = InputWorkbook().read(path)
        assert any(item["sheet"] == "Project & Client" and item["row"] == "5" and item["key"] == "building.occupancy_class" and "invalid" in item.get("reason", "") for item in missing)
