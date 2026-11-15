"""
validate_extraction.py

Validate the CSV package produced by etabs_extract_tables.py and generate:

    report_data.json
    validation_report.html

Usage from the folder containing the `tables` directory:

    python validate_extraction.py --input tables --output validation

The script is intentionally independent of ETABS. It can therefore be run on
any computer after the extraction package has been copied from the ETABS
computer.

Requirements:
    pip install pandas
"""

from __future__ import annotations

import argparse
import html
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


OPTIONAL_MISSING_TABLES = {"27_Response_Spectrum"}

EXPECTED_COLUMNS: dict[str, list[str]] = {
    "01_Modal_Periods": ["Case", "Mode", "Period"],
    "02_Modal_Mass_Ratios": ["Case", "Mode", "UX", "UY", "SumUX", "SumUY"],
    "03_Base_Reactions": ["OutputCase", "FX", "FY", "FZ", "MX", "MY", "MZ"],
    "04_Story_Drifts": ["Story", "OutputCase", "Direction", "Drift"],
    "05_Story_Forces": ["Story", "OutputCase", "VX", "VY"],
    "07_Column_Design": ["Story", "Label", "RatioRebar"],
    "08_Beam_Design": ["Story", "Label", "AsTop", "AsBot"],
    "07b_Column_PMM_Env": ["Story", "Label", "RatioRebar"],
    "07c_Column_Shear_Env": ["Story", "Label", "VMajor", "VMinor"],
    "08b_Beam_Flexure_Env": ["Story", "Label", "AsTop", "AsBot"],
    "08c_Beam_Shear_Env": ["Story", "Label", "Shear"],
    "09_Centers_Mass_Rigid": ["Story", "XCM", "YCM", "XCR", "YCR"],
    "10_Story_Stiffness": ["Story", "OutputCase", "StiffX", "StiffY"],
    "11_Joint_Reactions": ["Story", "Label", "OutputCase", "FX", "FY", "FZ"],
    "12_Story_Definitions": ["Story", "Height"],
    "13_Grid_Definitions": ["Name", "LineType", "Ordinate"],
    "14_Joint_Coordinates": ["Story", "ObjLabel", "GlobalX", "GlobalY", "GlobalZ"],
    "15_Frame_Connectivity": ["UniqueName", "Story", "UniquePtI", "UniquePtJ"],
    "15b_Column_Connectivity": ["UniqueName", "Story", "UniquePtI", "UniquePtJ"],
    "16_Area_Connectivity": ["Story", "ObjLabel"],
    "16b_Floor_Connectivity": ["UniqueName", "Story", "Area"],
    "17_Frame_Assignments": ["Story", "Label", "SectProp"],
    "18_Area_Assignments": ["Story", "Label", "SectProp"],
    "19_Diaphragm_Assignments": ["Story", "Label", "Diaphragm"],
    "20_Joint_Restraints": ["Story", "Label", "UX", "UY", "UZ"],
    "21_Materials": ["Material", "Type", "Grade"],
    "22_Frame_Sections": ["Name", "Material", "Shape", "Area"],
    "23_Area_Sections": ["Name", "Type", "Material", "TotalThick"],
    "24_Load_Patterns": ["Name", "Type", "SelfWtMult"],
    "25_Load_Cases": ["Name", "LoadType"],
    "26_Load_Combinations": ["Name", "Type", "LoadName", "SF"],
    "28_Mass_Source": ["Name", "IncLateral", "SourceSelf"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("tables"),
        help="Folder containing extracted CSV files and extraction_manifest.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation"),
        help="Folder in which report_data.json and validation_report.html are written.",
    )
    return parser.parse_args()


def json_value(value: Any) -> Any:
    """Convert pandas/numpy values to JSON-safe Python values."""
    if value is None:
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def clean_records(df: pd.DataFrame, limit: int | None = None) -> list[dict[str, Any]]:
    if limit is not None:
        df = df.head(limit)
    return [
        {str(column): json_value(value) for column, value in row.items()}
        for row in df.to_dict(orient="records")
    ]


def load_manifest(input_dir: Path) -> dict[str, Any]:
    path = input_dir / "extraction_manifest.json"
    if not path.exists():
        return {
            "status": "missing",
            "warning": "extraction_manifest.json was not found; CSV files were still inspected.",
        }
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"status": "invalid", "error": str(exc)}


def load_csvs(input_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    frames: dict[str, pd.DataFrame] = {}
    errors: dict[str, str] = {}
    for path in sorted(input_dir.glob("*.csv")):
        name = path.stem
        try:
            frames[name] = pd.read_csv(path)
        except Exception as exc:  # keep validating the remaining package
            errors[name] = str(exc)
    return frames, errors


def status_for(severity: str, message: str, **extra: Any) -> dict[str, Any]:
    item = {"severity": severity, "message": message}
    item.update(extra)
    return item


def numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[column], errors="coerce").dropna()


def max_numeric(df: pd.DataFrame, column: str, absolute: bool = False) -> float | None:
    values = numeric_series(df, column)
    if values.empty:
        return None
    if absolute:
        values = values.abs()
    return json_value(values.max())


def governing_row(df: pd.DataFrame, column: str, absolute: bool = False) -> dict[str, Any] | None:
    values = numeric_series(df, column)
    if values.empty:
        return None
    index = values.abs().idxmax() if absolute else values.idxmax()
    row = df.loc[index]
    return {str(key): json_value(value) for key, value in row.items()}


def validate_tables(
    frames: dict[str, pd.DataFrame],
    manifest: dict[str, Any],
    read_errors: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    table_summary: dict[str, Any] = {}
    manifest_tables = manifest.get("tables", {}) if isinstance(manifest, dict) else {}

    for name, error in read_errors.items():
        checks.append(status_for("FAIL", f"Could not read {name}.csv: {error}", table=name))
        table_summary[name] = {"status": "read_error", "error": error}

    requested_names = list(manifest_tables) if manifest_tables else sorted(EXPECTED_COLUMNS)
    for name in requested_names:
        entry = manifest_tables.get(name, {})
        expected = EXPECTED_COLUMNS.get(name, [])
        if entry.get("status") == "missing" or name not in frames:
            severity = "WARN" if name in OPTIONAL_MISSING_TABLES else "FAIL"
            message = "Optional table is unavailable." if severity == "WARN" else "Required table is missing."
            checks.append(status_for(severity, f"{name}: {message}", table=name))
            table_summary[name] = {
                "status": "missing",
                "rows": 0,
                "expected_columns": expected,
                "actual_columns": [],
            }
            continue

        df = frames[name]
        missing_columns = [column for column in expected if column not in df.columns]
        if df.empty:
            severity = "WARN" if name in OPTIONAL_MISSING_TABLES else "FAIL"
            checks.append(status_for(severity, f"{name}.csv is empty.", table=name))
        elif missing_columns:
            checks.append(
                status_for(
                    "FAIL",
                    f"{name} is missing expected columns: {', '.join(missing_columns)}.",
                    table=name,
                    missing_columns=missing_columns,
                )
            )
        else:
            checks.append(status_for("PASS", f"{name}: {len(df)} rows and required columns present.", table=name))

        table_summary[name] = {
            "status": "ok" if not missing_columns and not df.empty else "invalid",
            "rows": int(len(df)),
            "expected_columns": expected,
            "actual_columns": list(df.columns),
            "missing_columns": missing_columns,
        }

    return checks, table_summary


def analysis_summary(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    periods = frames.get("01_Modal_Periods")
    masses = frames.get("02_Modal_Mass_Ratios")
    if periods is not None and {"Period", "Mode"}.issubset(periods.columns):
        p = periods.copy()
        p["Period"] = pd.to_numeric(p["Period"], errors="coerce")
        p = p.dropna(subset=["Period"]).sort_values("Mode")
        result["modal"] = {
            "number_of_modes": int(len(p)),
            "fundamental_period_s": max_numeric(p.head(1), "Period"),
            "periods": clean_records(p),
        }
    if masses is not None:
        mass = {"rows": int(len(masses))}
        for direction in ("X", "Y", "Z", "RZ"):
            cumulative = f"SumU{direction}" if direction in {"X", "Y", "Z"} else "SumRZ"
            if cumulative in masses.columns:
                values = numeric_series(masses, cumulative)
                hit = values[values >= 0.90]
                mass[f"{cumulative}_final"] = json_value(values.iloc[-1]) if not values.empty else None
                mass[f"{cumulative}_90_percent_mode"] = json_value(masses.loc[hit.index[0], "Mode"]) if not hit.empty else None
        result["modal_mass_participation"] = mass

    drifts = frames.get("04_Story_Drifts")
    if drifts is not None and "Drift" in drifts.columns:
        d = drifts.copy()
        d["Drift"] = pd.to_numeric(d["Drift"], errors="coerce")
        d = d.dropna(subset=["Drift"])
        result["storey_drifts"] = {
            "maximum_absolute_drift": max_numeric(d, "Drift", absolute=True),
            "governing_row": governing_row(d, "Drift", absolute=True),
            "by_direction": clean_records(
                d.groupby("Direction", dropna=False)["Drift"].agg(lambda s: s.abs().max()).reset_index()
            ) if "Direction" in d.columns else [],
        }

    story_forces = frames.get("05_Story_Forces")
    if story_forces is not None:
        result["storey_forces"] = {
            "maximum_VX": max_numeric(story_forces, "VX", absolute=True),
            "maximum_VY": max_numeric(story_forces, "VY", absolute=True),
            "governing_VX_row": governing_row(story_forces, "VX", absolute=True),
            "governing_VY_row": governing_row(story_forces, "VY", absolute=True),
        }

    reactions = frames.get("03_Base_Reactions")
    if reactions is not None:
        result["base_reactions"] = {
            "maximum_abs_FX": max_numeric(reactions, "FX", absolute=True),
            "maximum_abs_FY": max_numeric(reactions, "FY", absolute=True),
            "maximum_abs_FZ": max_numeric(reactions, "FZ", absolute=True),
            "governing_FZ_row": governing_row(reactions, "FZ", absolute=True),
        }

    centers = frames.get("09_Centers_Mass_Rigid")
    if centers is not None:
        result["centers_of_mass_and_rigidity"] = clean_records(centers)

    stiffness = frames.get("10_Story_Stiffness")
    if stiffness is not None:
        result["story_stiffness"] = clean_records(stiffness)

    return result


def design_summary(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    column = frames.get("07_Column_Design")
    if column is not None:
        ratios = numeric_series(column, "RatioRebar")
        result["columns"] = {
            "members_or_rows": int(len(column)),
            "maximum_RatioRebar": max_numeric(column, "RatioRebar"),
            "governing_row": governing_row(column, "RatioRebar"),
            "rows_over_1_0": int((ratios > 1.0).sum()),
            "rows_over_0_9": int((ratios > 0.9).sum()),
        }

    beam = frames.get("08_Beam_Design")
    if beam is not None:
        top = numeric_series(beam, "AsTop")
        bottom = numeric_series(beam, "AsBot")
        result["beams"] = {
            "members_or_rows": int(len(beam)),
            "maximum_AsTop": max_numeric(beam, "AsTop"),
            "maximum_AsBot": max_numeric(beam, "AsBot"),
            "governing_AsTop_row": governing_row(beam, "AsTop"),
            "governing_AsBot_row": governing_row(beam, "AsBot"),
            "rows_with_missing_rebar": int((beam[["AsTop", "AsBot"]].isna().any(axis=1)).sum())
            if {"AsTop", "AsBot"}.issubset(beam.columns) else None,
        }

    column_shear = frames.get("07c_Column_Shear_Env")
    if column_shear is not None:
        result["column_shear"] = {
            "maximum_VMajor": max_numeric(column_shear, "VMajor", absolute=True),
            "maximum_VMinor": max_numeric(column_shear, "VMinor", absolute=True),
            "governing_VMajor_row": governing_row(column_shear, "VMajor", absolute=True),
            "governing_VMinor_row": governing_row(column_shear, "VMinor", absolute=True),
        }

    beam_shear = frames.get("08c_Beam_Shear_Env")
    if beam_shear is not None:
        result["beam_shear"] = {
            "maximum_Shear": max_numeric(beam_shear, "Shear", absolute=True),
            "governing_row": governing_row(beam_shear, "Shear", absolute=True),
        }
    return result


def geometry_summary(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, label in (
        ("12_Story_Definitions", "stories"),
        ("13_Grid_Definitions", "grid_lines"),
        ("14_Joint_Coordinates", "joints"),
        ("15_Frame_Connectivity", "beams"),
        ("15b_Column_Connectivity", "columns"),
        ("16_Area_Connectivity", "areas"),
        ("16b_Floor_Connectivity", "floors"),
        ("17_Frame_Assignments", "frame_assignments"),
        ("18_Area_Assignments", "area_assignments"),
        ("19_Diaphragm_Assignments", "diaphragm_assignments"),
        ("20_Joint_Restraints", "restraints"),
    ):
        if name in frames:
            result[label] = {"rows": int(len(frames[name]))}
    stories = frames.get("12_Story_Definitions")
    if stories is not None:
        result["story_table"] = clean_records(stories)
    return result


def input_summary(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, label in (
        ("21_Materials", "materials"),
        ("22_Frame_Sections", "frame_sections"),
        ("23_Area_Sections", "area_sections"),
        ("24_Load_Patterns", "load_patterns"),
        ("25_Load_Cases", "load_cases"),
        ("26_Load_Combinations", "load_combinations"),
        ("28_Mass_Source", "mass_sources"),
    ):
        if name in frames:
            result[label] = {
                "rows": int(len(frames[name])),
                "records": clean_records(frames[name]),
            }
    return result


def overall_status(checks: list[dict[str, Any]]) -> str:
    severities = {check["severity"] for check in checks}
    if "FAIL" in severities:
        return "FAIL"
    if "WARN" in severities:
        return "PASS WITH WARNINGS"
    return "PASS"


def html_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "<p><em>No records available.</em></p>"
    head = "".join(f"<th>{html.escape(str(column))}</th>" for column in columns)
    body_parts = []
    for row in rows:
        cells = "".join(f"<td>{html.escape(str(row.get(column, "")))}</td>" for column in columns)
        body_parts.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_parts)}</tbody></table>"


def validation_html(report: dict[str, Any]) -> str:
    status = report["validation"]["overall_status"]
    status_class = status.lower().replace(" ", "-")
    checks = report["validation"]["checks"]
    check_rows = [
        {
            "status": check["severity"],
            "table": check.get("table", ""),
            "message": check["message"],
        }
        for check in checks
    ]
    table_rows = []
    for name, item in report["validation"]["tables"].items():
        table_rows.append(
            {
                "table": name,
                "status": item.get("status", ""),
                "rows": item.get("rows", 0),
                "missing_columns": ", ".join(item.get("missing_columns", [])),
            }
        )

    analysis = report.get("analysis", {})
    modal = analysis.get("modal", {})
    mass = analysis.get("modal_mass_participation", {})
    design = report.get("design", {})
    columns = design.get("columns", {})
    beams = design.get("beams", {})

    summary_rows = [
        {"metric": "Overall validation", "value": status},
        {"metric": "Fundamental period T1 (s)", "value": modal.get("fundamental_period_s")},
        {"metric": "Modal mass SumUX final", "value": mass.get("SumUX_final")},
        {"metric": "Modal mass SumUY final", "value": mass.get("SumUY_final")},
        {"metric": "Maximum absolute storey drift", "value": analysis.get("storey_drifts", {}).get("maximum_absolute_drift")},
        {"metric": "Maximum column RatioRebar", "value": columns.get("maximum_RatioRebar")},
        {"metric": "Rows with column RatioRebar > 1.0", "value": columns.get("rows_over_1_0")},
        {"metric": "Maximum beam AsTop", "value": beams.get("maximum_AsTop")},
        {"metric": "Maximum beam AsBot", "value": beams.get("maximum_AsBot")},
    ]

    project = report.get("extraction", {})
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ETABS Extraction Validation Report</title>
<style>
body {{ font-family: Arial, sans-serif; color: #20252b; margin: 0; background: #f4f6f8; }}
main {{ max-width: 1180px; margin: 0 auto; padding: 34px; background: white; min-height: 100vh; }}
h1 {{ margin-bottom: 4px; }} h2 {{ margin-top: 32px; border-bottom: 2px solid #d9e1e8; padding-bottom: 6px; }}
.meta {{ color: #596773; margin-bottom: 24px; }}
.badge {{ display: inline-block; padding: 7px 12px; border-radius: 4px; font-weight: bold; }}
.pass {{ background: #d9f2df; color: #17652b; }}
.pass-with-warnings, .warn {{ background: #fff0c2; color: #7c5700; }}
.fail {{ background: #ffd9d9; color: #8f1d1d; }}
table {{ width: 100%; border-collapse: collapse; margin: 12px 0 20px; font-size: 13px; }}
th {{ background: #203747; color: white; text-align: left; }}
th, td {{ border: 1px solid #d5dde3; padding: 7px 8px; vertical-align: top; }}
tr:nth-child(even) {{ background: #f7f9fa; }}
.note {{ background: #eef5fa; border-left: 4px solid #397da6; padding: 10px 14px; }}
.small {{ font-size: 12px; color: #596773; }}
</style>
</head>
<body><main>
<h1>ETABS Extraction Validation Report</h1>
<div class="meta">Generated {html.escape(report["generated_at"])}<br>
Model: {html.escape(str(project.get("model_filename", "Unknown")))}<br>
Extraction timestamp: {html.escape(str(project.get("extraction_timestamp", "Unknown")))}</div>
<p><span class="badge {status_class}">{html.escape(status)}</span></p>
<div class="note">This report validates extracted ETABS tables and summarizes available data. It is not a substitute for independent structural-engineering review or code-compliance approval.</div>
<h2>Summary</h2>
{html_table(summary_rows, ["metric", "value"])}
<h2>Validation checks</h2>
{html_table(check_rows, ["status", "table", "message"])}
<h2>Table inventory</h2>
{html_table(table_rows, ["table", "status", "rows", "missing_columns"])}
<h2>Model and input inventory</h2>
<p class="small">The detailed records are available in report_data.json.</p>
{html_table([
    {"category": key, "rows": value.get("rows", "" ) if isinstance(value, dict) else ""}
    for key, value in report.get("geometry", {}).items()
    if isinstance(value, dict) and "rows" in value
], ["category", "rows"])}
{html_table([
    {"category": key, "rows": value.get("rows", "" ) if isinstance(value, dict) else ""}
    for key, value in report.get("inputs", {}).items()
    if isinstance(value, dict) and "rows" in value
], ["category", "rows"])}
<h2>Analysis and design summaries</h2>
<pre>{html.escape(json.dumps({"analysis": report.get("analysis", {}), "design": report.get("design", {})}, indent=2, ensure_ascii=False))}</pre>
<p class="small">Generated by validate_extraction.py.</p>
</main></body></html>"""


def main() -> int:
    args = parse_args()
    input_dir = args.input.resolve()
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        print(f"Input folder does not exist: {input_dir}", file=sys.stderr)
        return 2

    manifest = load_manifest(input_dir)
    frames, read_errors = load_csvs(input_dir)
    checks, table_summary = validate_tables(frames, manifest, read_errors)

    report: dict[str, Any] = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "extraction": {
            "model_filename": manifest.get("model_filename"),
            "extraction_timestamp": manifest.get("extraction_timestamp"),
            "present_units_enum": manifest.get("present_units_enum"),
            "analysis_ran": manifest.get("analysis_ran"),
            "concrete_design_ran": manifest.get("concrete_design_ran"),
            "available_table_count": manifest.get("available_table_count"),
            "configuration": manifest.get("configuration", {}),
        },
        "validation": {
            "overall_status": overall_status(checks),
            "checks": checks,
            "tables": table_summary,
            "read_errors": read_errors,
        },
        "geometry": geometry_summary(frames),
        "inputs": input_summary(frames),
        "analysis": analysis_summary(frames),
        "design": design_summary(frames),
    }

    json_path = output_dir / "report_data.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    html_path = output_dir / "validation_report.html"
    html_path.write_text(validation_html(report), encoding="utf-8")

    print(f"Loaded {len(frames)} CSV files from {input_dir}")
    print(f"Validation status: {report['validation']['overall_status']}")
    print(f"Saved: {json_path}")
    print(f"Saved: {html_path}")
    return 0 if report["validation"]["overall_status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
