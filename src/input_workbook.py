#!/usr/bin/env python3
"""Generate and read the Excel input workbook for project-specific data.

Generates inputs/Project_Input.xlsx from registry entries with source=excel.
Each sheet covers one topic with yellow input cells, grey example column,
and dropdowns/number validation. Values already known from ETABS/.e2k are
pre-filled and marked 'From ETABS - confirm'.

read() returns a nested dict plus a precise list of missing/invalid cells.

Also implements the T6 load-assessment table: a code-built table from
the wall/floor-finish inputs that reuses the sample's formatting.

Usage:
    from src.input_workbook import InputWorkbook
    wb = InputWorkbook()
    wb.generate("inputs/Project_Input.xlsx")
    data, missing = wb.read("inputs/Project_Input.xlsx")
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    import openpyxl
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
except ImportError:
    openpyxl = None  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "config" / "placeholder_registry.yaml"

# Sheet definitions: sheet name, list of (key, label, example, source, validation)
SHEET_DEFS: dict[str, list[dict[str, Any]]] = {
    "Project & Client": [
        {"key": "project.report_title", "label": "Report Title", "example": "Structural report of Residence Building"},
        {"key": "client.owner_name", "label": "Building Owner Name", "example": "Mr. Chatra Bahadur Ramtel"},
        {"key": "building.location", "label": "Location", "example": "Damak"},
        {"key": "building.occupancy_class", "label": "Occupancy Class", "example": "Residential", "validation": "Residential,Commercial,Industrial,Institutional"},
        {"key": "client.designer_name", "label": "Structural Designer Name", "example": "Mr. Sachin KC"},
        {"key": "client.designer_nec_reg", "label": "NEC Registration No.", "example": "131xx"},
        {"key": "client.designer_contact", "label": "Designer Contact No.", "example": "9841xxxxxxx"},
        {"key": "client.consultant_name", "label": "Consulting Firm", "example": "CivoraX Infra"},
        {"key": "consultancy.name", "label": "Consultancy Name", "example": "Swarup Engineering Consultancy"},
        {"key": "consultancy.address", "label": "Consultancy Address", "example": "Dharan-16, Sunsari"},
        {"key": "designer.name", "label": "Designer Name", "example": "Er. Anij Bhandari"},
        {"key": "designer.nec_no", "label": "Designer NEC No.", "example": "13925"},
        {"key": "designer.nec_category", "label": "Designer NEC Category", "example": "Civil “A” Category"},
        {"key": "client.municipality_reg", "label": "Municipality Reg. No.", "example": "Xxxx"},
        {"key": "client.application_date", "label": "Application Date", "example": "2026/xx/xx"},
    ],
    "Site & Soil": [
        {"key": "building.num_basements", "label": "Number of Basements", "example": 0, "validation_type": "whole"},
        {"key": "foundation.soil_bearing", "label": "Soil Bearing Capacity (kN/m2)", "example": "120"},
        {"key": "seismic.soil_class", "label": "Soil Class (NBC)", "example": "C", "validation": "A,B,C,D,E"},
        {"key": "seismic.site_soil_category", "label": "Site Soil Category", "example": "Very Soft Soil"},
        {"key": "seismic.zone_factor_z", "label": "Seismic Zone Factor Z", "example": 0.35},
        {"key": "seismic.structural_type", "label": "Structural Type", "example": "Ordinary Structures"},
    ],
    "Codes": [
        {"key": "codes.edition", "label": "Code Edition", "example": "NBC 105:2025"},
    ],
    "Wall & Finish Loads": [
        {"key": "loads.wall_unit_weight", "label": "Wall Unit Weight (kN/m3)", "example": 19.625},
        {"key": "loads.wall_thickness_mm", "label": "Wall Thickness (mm)", "example": 230},
        {"key": "loads.wall_height_m", "label": "Wall Height per Floor (m)", "example": 3.175},
        {"key": "loads.floor_finish_thickness_mm", "label": "Floor Finish Thickness (mm)", "example": 20},
        {"key": "loads.floor_finish_unit_weight", "label": "Floor Finish Unit Weight (kN/m3)", "example": 24.0},
        {"key": "loads.plaster_thickness_mm", "label": "Plaster Thickness (mm)", "example": 12},
        {"key": "loads.plaster_unit_weight", "label": "Plaster Unit Weight (kN/m3)", "example": 20.4},
        {"key": "loads.slab_thickness_mm", "label": "Slab Thickness (mm)", "example": 125},
        {"key": "loads.slab_unit_weight", "label": "Slab Concrete Unit Weight (kN/m3)", "example": 24.0},
        {"key": "loads.slab_dead_load", "label": "Slab Dead Load (kN/m2, computed)", "example": 3.175},
        {"key": "loads.live_load_residential", "label": "Live Load Residential (kN/m2)", "example": 2.0},
        {"key": "loads.live_load_corridor", "label": "Live Load Corridor (kN/m2)", "example": 3.0},
        {"key": "loads.roof_live_load", "label": "Roof Live Load (kN/m2)", "example": 1.5},
    ],
    "Foundation": [
        {"key": "foundation.type", "label": "Foundation Type", "example": "Combined Footing", "validation": "Isolated,Combined,Mat,Pile"},
        {"key": "structural.system_type_generic", "label": "Structural System (generic)", "example": "Moment Resisting Frames"},
        {"key": "structural.system_type_period_category", "label": "Structural System (period category)", "example": "Moment Resisting Concrete Frame"},
        {"key": "structural.system_type_table_5_2", "label": "Structural System (Table 5-2)", "example": "Reinforced Concrete Moment Resisting Frame"},
        {"key": "slab.type", "label": "Slab Type", "example": "Conventional", "validation": "Conventional,Flat,Waffle"},
    ],
    "Staircase": [
        {"key": "building.has_staircase", "label": "Has Staircase?", "example": True, "validation": "True,False"},
    ],
    "Figures": [
        {"key": "figure.design.slab_sheet", "label": "Slab Design Sheet Image", "example": "(user-supplied file path)"},
    ],
    "Sign-off": [
        {"key": "signoff.date", "label": "Date", "example": "2026/xx/xx"},
        {"key": "signoff.engineer_signature", "label": "Engineer Signature", "example": ""},
    ],
}

SAMPLE_VALUES: dict[str, Any] = {
    "project.report_title": "Structural report of Residence Building of Chatra Bahadur Ramtel",
    "client.owner_name": "Mr. Chatra Bahadur Ramtel", "building.location": "Damak",
    "building.occupancy_class": "Residential", "client.designer_name": "Mr. Anij Bhandari",
    "client.designer_nec_reg": "13925", "client.designer_contact": "9862123845",
    "client.consultant_name": "Swarup Engineering Consultancy", "consultancy.name": "Swarup Engineering Consultancy",
    "consultancy.address": "Dharan-16, Sunsari", "designer.name": "Er. Anij Bhandari",
    "designer.nec_no": "13925", "designer.nec_category": "Civil “A” Category",
    "client.municipality_reg": "123", "client.application_date": "2026/11/24",
    "building.num_basements": 0, "foundation.soil_bearing": "Soil Bearing Capacity is taken as 120 kN/m2",
    "building.story_height_m": 3.175, "building.total_height_m": 9.525,
    "seismic.soil_class": "C", "seismic.site_soil_category": "Firm soil", "seismic.zone_factor_z": 0.35,
    "seismic.structural_type": "Ordinary Structures", "codes.edition": "NBC 105:2025",
    "loads.wall_unit_weight": 19.625, "loads.wall_thickness_mm": 230, "loads.wall_height_m": 3.175,
    "loads.floor_finish_thickness_mm": 20, "loads.floor_finish_unit_weight": 24.0,
    "loads.plaster_thickness_mm": 12, "loads.plaster_unit_weight": 20.4,
    "loads.slab_thickness_mm": 125, "loads.slab_unit_weight": 24.0, "loads.slab_dead_load": 3.0,
    "loads.live_load_residential": 2.0, "loads.live_load_corridor": 3.0, "loads.roof_live_load": 1.5,
    "foundation.type": "Combined Footing", "structural.system_type_generic": "Moment Resisting Frames",
    "structural.system_type_period_category": "Moment Resisting Concrete Frame",
    "structural.system_type_table_5_2": "Reinforced Concrete Moment Resisting Frame",
    "slab.type": "Conventional", "building.has_staircase": True, "signoff.date": "2026/11/24",
}

SHEET_TOPICS = {
    "project": "Project & Client", "client": "Project & Client", "consultancy": "Consultancy and Designer",
    "designer": "Consultancy and Designer", "building": "Project & Client", "seismic": "Site & Soil",
    "codes": "Codes", "loads": "Wall & Finish Loads", "foundation": "Foundation",
    "structural": "Foundation", "slab": "Foundation", "figure": "Figures", "signoff": "Sign-off",
}

def registry_sheet_defs() -> dict[str, list[dict[str, Any]]]:
    """Return the curated fields plus every registry entry whose source is Excel."""
    result = {name: [dict(field) for field in fields] for name, fields in SHEET_DEFS.items()}
    # Keep the legacy combined sheets for reader compatibility, while exposing
    # the topic sheets required by the project brief.
    result.setdefault("Consultancy and Designer", [])
    result.setdefault("Live Loads", [])
    result.setdefault("Irregularity Declarations", [])
    for field in result["Project & Client"]:
        if field["key"].startswith(("consultancy.", "designer.")) or field["key"] in {"client.designer_name", "client.designer_nec_reg", "client.designer_contact"}:
            result["Consultancy and Designer"].append(dict(field))
    for field in result["Wall & Finish Loads"]:
        if field["key"].startswith("loads.live_") or field["key"] == "loads.roof_live_load":
            result["Live Loads"].append(dict(field))
    for field in result.get("Codes", []):
        if any(token in field["key"] for token in ("irregularity", "torsional", "soft_storey", "mass_", "reentrant", "diaphragm", "out_of_plane")):
            result["Irregularity Declarations"].append(dict(field))
    seen = {field["key"] for fields in result.values() for field in fields}
    entries = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")).get("items", [])
    for entry in entries:
        key = str(entry.get("key", ""))
        if entry.get("source") != "excel" or not key or key in seen:
            continue
        topic = SHEET_TOPICS.get(key.split(".", 1)[0], "Project & Client")
        result.setdefault(topic, []).append({"key": key, "label": str(entry.get("description") or key),
            "example": entry.get("example", ""), "registry_type": entry.get("type"),
            "required": bool(entry.get("required", False)), "condition": entry.get("condition")})
        seen.add(key)
    return result


class InputWorkbook:
    """Generate and read the Excel input workbook."""

    YELLOW = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
    GREY = PatternFill(start_color="E0E0E0", end_color="E0E0E0", fill_type="solid")
    HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    HEADER_FONT = Font(color="FFFFFF", bold=True)
    THIN_BORDER = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    def generate(self, output_path: str | Path) -> None:
        """Generate the Excel workbook."""
        if openpyxl is None:
            raise RuntimeError("openpyxl is required: pip install openpyxl")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        for sheet_name, fields in registry_sheet_defs().items():
            ws = wb.create_sheet(title=sheet_name[:31])  # Excel max 31 chars
            # Header row
            ws.cell(1, 1, "Key").fill = self.HEADER_FILL
            ws.cell(1, 1).font = self.HEADER_FONT
            ws.cell(1, 2, "Label").fill = self.HEADER_FILL
            ws.cell(1, 2).font = self.HEADER_FONT
            ws.cell(1, 3, "Value").fill = self.HEADER_FILL
            ws.cell(1, 3).font = self.HEADER_FONT
            ws.cell(1, 4, "Example").fill = self.HEADER_FILL
            ws.cell(1, 4).font = self.HEADER_FONT
            ws.cell(1, 5, "Source / review status").fill = self.HEADER_FILL
            ws.cell(1, 5).font = self.HEADER_FONT
            ws.cell(1, 6, "Hypothetical sample").fill = self.HEADER_FILL
            ws.cell(1, 6).font = self.HEADER_FONT
            for c in range(1, 7):
                ws.cell(1, c).border = self.THIN_BORDER

            for ri, field in enumerate(fields, start=2):
                ws.cell(ri, 1, field["key"]).border = self.THIN_BORDER
                ws.cell(ri, 2, field["label"]).border = self.THIN_BORDER
                # Value cell (yellow, empty — user fills this)
                val_cell = ws.cell(ri, 3)
                if field["key"] in SAMPLE_VALUES:
                    val_cell.value = SAMPLE_VALUES[field["key"]]
                val_cell.fill = self.YELLOW
                val_cell.border = self.THIN_BORDER
                # Example cell (grey)
                ex_cell = ws.cell(ri, 4, str(field.get("example", "")))
                ex_cell.fill = self.GREY
                ex_cell.font = Font(italic=True, color="808080")
                ex_cell.border = self.THIN_BORDER
                source = "Sample report — hypothetical; confirm"
                if field["key"] in {"building.num_basements", "seismic.soil_class", "seismic.zone_factor_z", "building.story_height_m", "building.total_height_m", "loads.slab_dead_load"}:
                    source = "From ETABS - confirm"
                ws.cell(ri, 5, source).border = self.THIN_BORDER
                ws.cell(ri, 6, "Yes").fill = self.GREY
                ws.cell(ri, 6).font = Font(italic=True, color="808080")
                ws.cell(ri, 6).border = self.THIN_BORDER
                # Validation
                if "validation" in field:
                    dv = DataValidation(type="list", formula1=f'"{field["validation"]}"', allow_blank=True)
                    ws.add_data_validation(dv)
                    dv.add(val_cell)
                elif field.get("validation_type") == "whole" or field.get("registry_type") in {"number", "integer"}:
                    dtype = "whole" if field.get("validation_type") == "whole" or field.get("registry_type") == "integer" else "decimal"
                    dv = DataValidation(type=dtype, operator="greaterThanOrEqual", formula1=0, allow_blank=True)
                    ws.add_data_validation(dv)
                    dv.add(val_cell)
                elif field.get("registry_type") == "bool":
                    dv = DataValidation(type="list", formula1='"True,False"', allow_blank=True)
                    ws.add_data_validation(dv)
                    dv.add(val_cell)

            # Column widths
            ws.column_dimensions["A"].width = 35
            ws.column_dimensions["B"].width = 35
            ws.column_dimensions["C"].width = 20
            ws.column_dimensions["D"].width = 30
            ws.column_dimensions["E"].width = 28
            ws.column_dimensions["F"].width = 18

        wb.save(str(output_path))

    def build_t6_load_assessment(self, ctx: dict[str, Any]) -> list[list[str]]:
        """Build the T6 load assessment table from wall/floor-finish inputs.

        Returns a list of rows (each a list of cell strings) that can be
        inserted into the template as a code-built table, reusing the
        sample's formatting structure.
        """
        loads = ctx.get("loads", {})
        building = ctx.get("building", {})

        wall_uw = loads.get("wall_unit_weight", 19.625)
        wall_t = loads.get("wall_thickness_mm", 230)
        wall_h = loads.get("wall_height_m", building.get("story_height_m", 3.175))
        plaster_t = loads.get("plaster_thickness_mm", 12)
        plaster_uw = loads.get("plaster_unit_weight", 20.4)
        ff_t = loads.get("floor_finish_thickness_mm", 20)
        ff_uw = loads.get("floor_finish_unit_weight", 24.0)
        slab_t = loads.get("slab_thickness_mm", 125)
        slab_uw = loads.get("slab_unit_weight", 24.0)
        slab_dl = loads.get("slab_dead_load", round(slab_t / 1000 * slab_uw, 3))
        ll_res = loads.get("live_load_residential", 2.0)
        ll_corr = loads.get("live_load_corridor", 3.0)
        ll_roof = loads.get("roof_live_load", 1.5)

        # Compute wall load per meter
        wall_load = round(wall_h * (wall_uw + 2 * plaster_t / 1000 * plaster_uw), 2)
        ff_load = round(ff_t / 1000 * ff_uw, 2)

        rows = [
            ["Wall Load", "", "", "", "", "", ""],
            ["", f"Cement Plaster {plaster_uw} KN/M3", "", "", "", "", ""],
            ["", f"Brick {wall_uw} KN/M3", "", "", "", "", ""],
            ["", f"AVG {round((wall_uw + plaster_uw) / 2, 3)} KN/M3", "", "", "", "", ""],
            ["", f"Floor Height {wall_h}m", "", "", f"Beam Depth 0.380m", "", "", ""],
            ["", f"For {wall_t} mm wall", f"{wall_load} KN/M", "", "", "", ""],
            ["", f"For {wall_t - 80} mm Wall", f"{round(wall_load * (wall_t - 80) / wall_t, 1)} KN/M", "", "", "", ""],
            ["", "", "", "", "", "", ""],
            ["FLOOR FINISH", "", "", "", "", "", ""],
            ["", f"Cement Mortar Bed {plaster_uw} KN/M3", f"{ff_t / 1000}", f"{ff_load} KN/M2", "", "", ""],
            ["", f"Floor Tile {ff_uw} KN/M3", f"{ff_t / 1000}", f"{round(ff_t / 1000 * ff_uw, 3)}", "", "", ""],
            ["", "", "", "", "", "", ""],
            ["ROOF LIVE", "", "", "", f"{ll_roof}", "", "", ""],
            ["", "", "", "", "", "", ""],
            ["Slab Dead Load", f"{slab_dl} KN/m2", "", "", "", "", ""],
            ["Floor Finish", f"{ff_load} KN/M2", "", "", "", "", ""],
            ["", "", "", "", "", "", ""],
            ["LIVE LOADS", "", "", "", "", "", ""],
            ["", "Dwelling houses", f"{ll_res} kN/m2", "", "", "", ""],
            ["", "Corridors", f"{ll_corr} kN/m2", "", "", "", ""],
            ["", "Roof", f"{ll_roof} kN/m2", "", "", "", ""],
        ]
        return rows

    def read(self, input_path: str | Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
        """Read the workbook and return a nested dict plus missing/invalid cells."""
        if openpyxl is None:
            raise RuntimeError("openpyxl is required")
        wb = openpyxl.load_workbook(str(input_path), data_only=True)
        ctx: dict[str, Any] = {}
        missing: list[dict[str, str]] = []

        def _set_nested(key: str, value: Any) -> None:
            parts = key.split(".")
            d = ctx
            for p in parts[:-1]:
                d = d.setdefault(p, {})
            d[parts[-1]] = value

        for sheet_name, fields in registry_sheet_defs().items():
            # Find the sheet (may be truncated to 31 chars)
            ws = None
            for sn in wb.sheetnames:
                if sn.startswith(sheet_name[:20]):
                    ws = wb[sn]
                    break
            if ws is None:
                for field in fields:
                    missing.append({"sheet": sheet_name, "row": "?", "key": field["key"]})
                continue

            for ri in range(2, ws.max_row + 1):
                key = ws.cell(ri, 1).value
                label = ws.cell(ri, 2).value
                value = ws.cell(ri, 3).value
                if not key:
                    continue
                field = next((f for f in fields if f["key"] == str(key)), {})
                if value is None or str(value).strip() == "":
                    missing.append({
                        "sheet": sheet_name, "row": str(ri),
                        "key": str(key),
                    })
                else:
                    val_str = str(value).strip()
                    validation = field.get("validation")
                    if validation and val_str not in {v.strip() for v in validation.split(",")}:
                        missing.append({"sheet": sheet_name, "row": str(ri), "key": str(key),
                                        "reason": f"invalid value {val_str!r}; allowed {validation}"})
                        continue
                    rtype = field.get("registry_type")
                    if rtype in {"number", "integer"}:
                        try:
                            numeric = float(val_str)
                            if rtype == "integer" and numeric != int(numeric):
                                raise ValueError
                        except ValueError:
                            missing.append({"sheet": sheet_name, "row": str(ri), "key": str(key),
                                            "reason": f"invalid {rtype} value {val_str!r}"})
                            continue
                    if rtype == "bool" and val_str.lower() not in {"true", "false"}:
                        missing.append({"sheet": sheet_name, "row": str(ri), "key": str(key),
                                        "reason": f"invalid bool value {val_str!r}"})
                        continue
                    # Type conversion
                    if val_str.lower() == "true":
                        _set_nested(str(key), True)
                    elif val_str.lower() == "false":
                        _set_nested(str(key), False)
                    else:
                        try:
                            num = float(val_str)
                            _set_nested(str(key), int(num) if num == int(num) else num)
                        except ValueError:
                            _set_nested(str(key), val_str)

        return ctx, missing


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command")
    gen = sub.add_parser("generate", help="Generate the input workbook")
    gen.add_argument("--output", default="inputs/Project_Input.xlsx")
    rd = sub.add_parser("read", help="Read the workbook")
    rd.add_argument("--input", default="inputs/Project_Input.xlsx")
    args = p.parse_args()

    wb = InputWorkbook()
    if args.command == "generate":
        wb.generate(args.output)
        print(f"[OK] Generated: {args.output}")
    elif args.command == "read":
        data, missing = wb.read(args.input)
        print(f"[OK] Read: {args.input}")
        print(f"     Keys: {sum(len(v) if isinstance(v, dict) else 1 for v in data.values())}")
        print(f"     Missing: {len(missing)}")
        for m in missing[:5]:
            print(f"       {m}")
    else:
        p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
