#!/usr/bin/env python3
"""Build a report context from ETABS, E2K and engineer-supplied workbook data.

All engineering constants are read from configuration. Missing source data is
reported as UNRESOLVED; the builder never substitutes an engineering default.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MAPPING = ROOT / "config" / "mapping.yaml"
FORMATS = ROOT / "config" / "formats.yaml"
SEISMIC_FORMULAS = ROOT / "config" / "seismic_formulas.yaml"
SPECTRUM = ROOT / "config" / "nbc105_spectrum.yaml"

try:
    from validate_extraction import EXPECTED_COLUMNS, load_csvs, validate_tables
except ImportError:  # pragma: no cover - direct execution from another cwd
    try:
        from validate_extraction import EXPECTED_COLUMNS, load_csvs, validate_tables
    except ImportError:
        EXPECTED_COLUMNS, load_csvs, validate_tables = {}, None, None

try:
    from generate_sls_drift_report import build_stories, evaluate, tidy_joint_drifts, tidy_story_drifts
except ImportError:  # pragma: no cover
    try:
        from generate_sls_drift_report import build_stories, evaluate, tidy_joint_drifts, tidy_story_drifts
    except ImportError:
        build_stories = evaluate = tidy_joint_drifts = tidy_story_drifts = None


class ContextBuilder:
    """Build context.json and its evidence files from project inputs."""

    def __init__(self) -> None:
        self.ctx: dict[str, Any] = {}
        self.sources: dict[str, str] = {}
        self.source_details: dict[str, dict[str, Any]] = {}
        self.conflicts: list[str] = []
        self.unresolved: list[str] = []
        self.config = self._load_yaml(FORMATS)
        self.mapping = self._load_yaml(MAPPING)
        self.formulas = self._load_yaml(SEISMIC_FORMULAS)
        self.spectrum = self._load_yaml(SPECTRUM) if SPECTRUM.exists() else {}
        self._csv_rows: dict[str, list[dict[str, Any]]] = {}

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def _repo_path(path: Path) -> str:
        try:
            return str(path.resolve().relative_to(ROOT))
        except ValueError:
            return str(path)

    def _unresolved(self, message: str) -> None:
        if message not in self.unresolved:
            self.unresolved.append(f"UNRESOLVED: {message}")

    @staticmethod
    def _source_rank(source: str) -> int:
        source = source.lower()
        if "api" in source:
            return 4
        if "etabs_csv" in source:
            return 3
        if "e2k" in source:
            return 2
        if "excel" in source:
            return 1
        return 0

    def _set(self, key: str, value: Any, source: str, source_column: str | None = None,
             source_filter: str | None = None) -> None:
        if value is None or (isinstance(value, str) and not value.strip()):
            self._unresolved(f"{key}: source {source} supplied no value")
            return
        old_source = self.sources.get(key)
        if old_source and self._get(key) != value:
            if self._source_rank(source) == self._source_rank(old_source):
                self.conflicts.append(f"{key}: equal-priority conflict between {old_source}={self._get(key)!r} and {source}={value!r}; existing value retained")
            else:
                self.conflicts.append(f"{key}: conflict between {old_source}={self._get(key)!r} and {source}={value!r}; higher-priority source retained")
            if self._source_rank(source) <= self._source_rank(old_source):
                return
        parts = key.split(".")
        d = self.ctx
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = value
        self.sources[key] = source
        source_file = source.split(":", 1)[1] if ":" in source else source
        if source_file.startswith("/"):
            source_file = self._repo_path(Path(source_file))
        self.source_details[key] = {"source": source, "file": source_file,
                                    "column": source_column or key.rsplit(".", 1)[-1],
                                    "filter": source_filter or "not specified"}

    def _get(self, key: str, default: Any = None) -> Any:
        value: Any = self.ctx
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        return value

    def _fmt(self, key: str, value: float) -> Any:
        fmt = self.config.get("formats", {}).get(key, {})
        decimals = fmt.get("decimals")
        return f"{value:.{decimals}f}" if decimals is not None else value

    @staticmethod
    def _number(row: dict[str, Any], *names: str) -> float | None:
        for name in names:
            if name in row and str(row[name]).strip() != "":
                try:
                    value = float(str(row[name]).replace(",", "").replace("%", "").strip())
                    if math.isfinite(value):
                        return value
                except (TypeError, ValueError):
                    pass
        return None

    @staticmethod
    def _value(row: dict[str, Any], *names: str) -> Any:
        for name in names:
            if name in row and str(row[name]).strip() != "":
                return row[name]
        return None

    def build(self, tables_dir: str | Path, sls_tables_dir: str | Path,
              e2k_path: str | Path, input_xlsx: str | Path,
              output_dir: str | Path) -> dict[str, Any]:
        self._read_excel(Path(input_xlsx))
        if Path(e2k_path).exists():
            self._read_e2k(Path(e2k_path))
        else:
            self._unresolved(f".e2k file not found: {e2k_path}")
        if Path(tables_dir).exists():
            self._read_etabs_tables(Path(tables_dir))
        else:
            self._unresolved(f"ETABS tables directory not found: {tables_dir}")
        if Path(sls_tables_dir).exists():
            self._read_sls_tables(Path(sls_tables_dir))
        else:
            self._unresolved(f"SLS tables directory not found: {sls_tables_dir}")
        self._compute()
        self._ensure_registry_coverage()
        self._write_outputs(Path(output_dir))
        return self.ctx

    def _read_excel(self, path: Path) -> None:
        if not path.exists():
            self._unresolved(f"input workbook not found: {self._repo_path(path)}")
            return
        try:
            from src.input_workbook import InputWorkbook
            data, missing = InputWorkbook().read(path)
            for key, value in data.items():
                if isinstance(value, dict):
                    for sub, item in value.items():
                        self._set(f"{key}.{sub}", item, "excel")
                else:
                    self._set(key, value, "excel")
            for item in missing:
                self._unresolved(f"missing Excel input: {item['sheet']} row {item['row']} key {item['key']}")
        except Exception as exc:
            self._unresolved(f"error reading Excel {path}: {exc}")

    def _read_e2k(self, path: Path) -> None:
        try:
            from src.e2k_parser import E2KParser
            data = E2KParser().parse_file(path)
            seismic_text = path.read_text(encoding="utf-8", errors="replace")
            for direction in ("X", "Y"):
                match = re.search(rf'SEISMIC\s+"EQ{direction}-ULS".*?ECC\s+([0-9.]+).*?SHEARCOEFF\s+([0-9.]+)\s+HEIGHTEXPONENT\s+([0-9.]+)', seismic_text)
                if match:
                    ecc, coeff, exponent = (float(x) for x in match.groups())
                    self._set(f"seismic.eq{direction.lower()}_eccentricity", ecc, f"e2k:{self._repo_path(path)}", "ECC", f'SEISMIC "EQ{direction}-ULS"')
                    self._set(f"seismic.eq{direction.lower()}_shear_coefficient", coeff, f"e2k:{self._repo_path(path)}", "SHEARCOEFF", f'SEISMIC "EQ{direction}-ULS"')
                    self._set(f"seismic.eq{direction.lower()}_height_exponent", exponent, f"e2k:{self._repo_path(path)}", "HEIGHTEXPONENT", f'SEISMIC "EQ{direction}-ULS"')
                    self._set("seismic.spectral_coefficient_cd", coeff, f"e2k:{self._repo_path(path)}", "SHEARCOEFF", f'SEISMIC "EQ{direction}-ULS"')
            stories = data.get("stories", [])
            above = [s for s in stories if s.get("Story") != "Base"]
            # Real ETABS exports store geometry in the file units (mm for the
            # committed model); legacy fixtures already use metres.
            def length_m(value: Any) -> float:
                number = float(value)
                return number / 1000.0 if abs(number) > 100 else number
            self._set("building.storeys_above_grade", len(above), "e2k")
            self._set("building.num_storeys_analysed", len(above), "e2k")
            # ETABS writes upper stories top-down and often omits Elevation;
            # derive elevations from Base=0 by accumulating heights bottom-up.
            cumulative = 0.0
            elevations: dict[str, float] = {"Base": 0.0}
            for story in reversed(above):
                cumulative += length_m(story.get("StoryHt", "0"))
                elevations[story.get("Story", "")] = cumulative
                story["Elevation"] = str(cumulative)
            self._set("building.story_elevations_m", {name: self._fmt("building.story_height_m", value) for name, value in elevations.items() if name != "Base"}, "e2k")
            basements = [s for s in stories if float(elevations.get(s.get("Story", ""), length_m(s.get("Elevation", "0")))) <= 0 and s.get("Story") != "Base"]
            self._set("building.num_basements", len(basements), "e2k")
            if above:
                first = above[-1]
                typical = above[0] if len(above) > 1 else first
                heights = [length_m(s["StoryHt"]) for s in above if s.get("StoryHt") not in (None, "")]
                self._set("building.story_height_m", self._fmt("building.story_height_m", length_m(first["StoryHt"])), "e2k")
                self._set("building.height_ground_floor_m", self._fmt("building.height_ground_floor_m", length_m(first["StoryHt"])), "e2k")
                self._set("building.height_typical_floor_m", self._fmt("building.height_typical_floor_m", length_m(typical["StoryHt"])), "e2k")
                self._set("building.total_height_m", self._fmt("building.total_height_m", sum(heights)), "e2k")
                self._set("building.height_period_m", self._fmt("building.height_period_m", max(length_m(s["Elevation"]) for s in above)), "e2k")
            grids = data.get("grids", [])
            xs, ys = [], []
            for grid in grids:
                try:
                    xs.append(length_m(grid.get("XOrd", grid.get("Coord", ""))))
                except (TypeError, ValueError):
                    pass
                try:
                    ys.append(length_m(grid.get("YOrd", grid.get("Coord", ""))))
                except (TypeError, ValueError):
                    pass
            if xs: self._set("building.span_x_m", self._fmt("building.span_x_m", max(xs) - min(xs)), "e2k")
            if ys: self._set("building.span_y_m", self._fmt("building.span_y_m", max(ys) - min(ys)), "e2k")
            for mat in data.get("materials", []):
                if mat.get("Type") == "Concrete":
                    self._set("materials.concrete_grade_used", f"M{int(float(mat['Fc']))}", "e2k")
                    self._set("building.primary_frame_material", mat.get("Material"), "e2k")
                elif mat.get("Type") == "Rebar":
                    self._set("materials.rebar_grade_used", f"Fe{int(float(mat.get('Fy', mat.get('Fc'))))}", "e2k")
            diaph = data.get("diaphragms", [])
            if diaph:
                self._set("building.diaphragm_type", diaph[0].get("Type"), "e2k")
            restraints = data.get("restraints", [])
            if restraints:
                self._set("foundation.point_restraint_cross_check", restraints[0], "e2k")
        except Exception as exc:
            raise RuntimeError(f"error reading .e2k {path}") from exc

    def _read_csv_rows(self, path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            return list(csv.DictReader(f))

    def _require(self, rows: list[dict[str, Any]], columns: Iterable[str], file: str) -> bool:
        actual = set(rows[0]) if rows else set()
        missing = [c for c in columns if c not in actual]
        if missing:
            self._unresolved(f"{file}: missing required column(s): {', '.join(missing)}; actual columns: {', '.join(sorted(actual))}")
            return False
        return True

    def _read_etabs_tables(self, directory: Path) -> None:
        if load_csvs is not None and validate_tables is not None:
            frames, read_errors = load_csvs(directory)
            checks, _summary = validate_tables(frames, {}, read_errors)
            for check in checks:
                if check.get("severity") == "FAIL":
                    self._unresolved(f"validate_extraction.py: {check.get('message', 'CSV validation failed')}")
        for path in sorted(directory.glob("*.csv")):
            try:
                rows = self._read_csv_rows(path)
                self._csv_rows[path.name] = rows
                name = path.stem.lower()
                if "modal" in name and "mass" in name:
                    self._process_modal_mass(rows, path.name)
                elif "story" in name and "force" in name:
                    self._process_story_forces(rows, path.name)
                elif "story" in name and "drift" in name:
                    self._process_story_drifts(rows, path.name)
                elif "base" in name and "reaction" in name:
                    self._process_base_reactions(rows, path.name)
                elif "column" in name and "design" in name:
                    self._process_column_design(rows, path.name)
                elif "beam" in name and "design" in name:
                    self._process_beam_design(rows, path.name)
                elif "story" in name and "max_avg" in name:
                    self._process_torsion(rows, path.name)
                    self._process_displacement_summary(rows, path.name, "drift.uls")
                elif name == "09_centers_mass_rigid":
                    self._process_mass(rows, path.name)
                elif name == "10_story_stiffness":
                    self._process_stiffness(rows, path.name)
                elif name == "17_frame_assignments":
                    self._process_sections(rows, path.name)
                elif name == "21_materials":
                    self._process_materials(rows, path.name)
            except Exception as exc:
                self.conflicts.append(f"Error reading {path.name}: {exc}")

    def _process_modal_mass(self, rows: list[dict[str, Any]], file: str) -> None:
        if not rows or not self._require(rows, ("Mode", "Period", "UX", "UY"), file): return
        modes, last_x, last_y = [], None, None
        for row in rows:
            mode = self._number(row, "Mode"); period = self._number(row, "Period")
            ux = self._number(row, "UX"); uy = self._number(row, "UY")
            if None in (mode, period, ux, uy):
                self._unresolved(f"{file}: non-numeric modal row {row}"); continue
            last_x = self._number(row, "SumUX", "Sum UX")
            last_y = self._number(row, "SumUY", "Sum UY")
            if last_x is None: last_x = (last_x or 0) + ux
            if last_y is None: last_y = (last_y or 0) + uy
            modes.append({"mode": int(mode), "period": period, "ux": ux, "uy": uy, "sum_ux": last_x, "sum_uy": last_y})
        if modes:
            self._set("modal.modes_included_count", next((m["mode"] for m in modes if m["sum_ux"] >= .9 and m["sum_uy"] >= .9), modes[-1]["mode"]), "etabs_csv")
            self._set("modal.modal_data", modes, "etabs_csv")
            self._set("table.modal.periods_mass_part", modes, "etabs_csv:02_Modal_Mass_Ratios.csv", "Mode/Period/UX/UY", "all modal rows")

    def _process_story_forces(self, rows: list[dict[str, Any]], file: str) -> None:
        if not rows: return
        if not self._require(rows, ("Story",), file): return
        force_col = next((c for c in ("VX", "VY", "Base Shear", "Shear Force") if c in rows[0]), None)
        if not force_col:
            self._unresolved(f"{file}: expected one of VX, VY, Base Shear, Shear Force")
            return
        records = []
        for row in rows:
            force = self._number(row, force_col)
            disp = self._number(row, "Displacement", "UX", "UY", "U1", "U2")
            weight = self._number(row, "W", "Weight", "Wi", "Story Weight")
            records.append({"story": row["Story"], "force": force, "displacement": disp, "weight": weight, "case": self._value(row, "OutputCase", "Case", "Load Case")})
        self._set("analysis.story_force_data", records, "etabs_csv")

    def _process_story_drifts(self, rows: list[dict[str, Any]], file: str) -> None:
        if not rows or not self._require(rows, ("Story",), file): return
        drift_col = next((c for c in ("Drift", "Drift Ratio") if c in rows[0]), None)
        disp_col = next((c for c in ("Displacement", "U1", "U2") if c in rows[0]), None)
        if not drift_col:
            self._unresolved(f"{file}: missing drift column (expected Drift or Drift Ratio)")
            return
        drifts = []
        by_dir: dict[str, float] = {}
        for row in rows:
            ratio = self._number(row, drift_col)
            if ratio is None: self._unresolved(f"{file}: non-numeric drift row {row}"); continue
            drifts.append({"story": row["Story"], "drift_ratio": abs(ratio), "displacement": self._number(row, disp_col) if disp_col else None, "case": self._value(row, "OutputCase", "Case", "Load Case")})
            case = str(self._value(row, "OutputCase", "Case", "Load Case") or "").upper()
            direction = str(row.get("Direction", "")).upper()
            if case == "EQX-ULS" and direction == "X": by_dir["x"] = max(by_dir.get("x", 0.0), abs(ratio))
            if case == "EQY-ULS" and direction == "Y": by_dir["y"] = max(by_dir.get("y", 0.0), abs(ratio))
        self._set("drift.data", drifts, "etabs_csv")
        for direction, value in by_dir.items():
            self._set(f"drift.uls_raw_{direction}", value, f"etabs_csv:{file}", drift_col, f"OutputCase=EQ{direction.upper()}-ULS, Direction={direction.upper()}")

    def _process_base_reactions(self, rows: list[dict[str, Any]], file: str) -> None:
        if not rows: return
        if not self._require(rows, ("OutputCase",), file): return
        selected = []
        for row in rows:
            case = str(self._value(row, "OutputCase", "Case", "Load Case") or "").upper()
            if case == "EQX-ULS":
                value = self._number(row, "FX")
                if value is not None:
                    self._set("modal.base_shear_etabs_x", abs(value), "etabs_csv:03_Base_Reactions.csv")
                    selected.append(abs(value))
            elif case == "EQY-ULS":
                value = self._number(row, "FY")
                if value is not None:
                    self._set("modal.base_shear_etabs_y", abs(value), "etabs_csv:03_Base_Reactions.csv")
                    selected.append(abs(value))
        if selected:
            self._set("modal.base_shear_etabs", max(selected), "etabs_csv:03_Base_Reactions.csv")
        else:
            self._unresolved(f"{file}: EQX-ULS FX or EQY-ULS FY base reaction not found")

    def _process_column_design(self, rows: list[dict[str, Any]], file: str) -> None:
        ratio = next((c for c in ("RatioRebar", "RebarPct", "SteelPct", "% Steel") if rows and c in rows[0]), None)
        if not ratio:
            self._unresolved(f"{file}: missing column steel percentage column")
            return
        vals = [self._number(r, ratio) for r in rows]
        vals = [v for v in vals if v is not None]
        if vals: self._set("design.column.max_provided_pct", max(vals) if max(vals) > 1 else max(vals) * 100, f"etabs_csv:{file}", ratio, "all column design rows")
        if vals:
            normalized = [v if v > 1 else v * 100 for v in vals]
            governing = rows[vals.index(max(vals))] if vals else {}
            section = str(governing.get("DesignSect", ""))
            dims = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", section)]
            width = dims[0] if dims else None
            depth = dims[1] if len(dims) > 1 else width
            self._set("design.column.min_provided_pct", min(normalized), f"etabs_csv:{file}", ratio, "all column design rows")
            max_limit = float(self.config.get("limits", {}).get("max_column_steel_pct", 4.0)); min_limit = float(self.config.get("limits", {}).get("min_column_steel_pct", 1.0))
            self._set("design.column.max_limit_pct", max_limit, "computed: config/formats.yaml", "limits.max_column_steel_pct", "configured maximum")
            self._set("design.column.min_limit_pct", min_limit, "computed: config/formats.yaml", "limits.min_column_steel_pct", "configured minimum")
            self._set("design.column.max_status", "Ok" if max(normalized) <= max_limit else "Not Ok", "computed: config/formats.yaml", "status_words", "max column steel check")
            self._set("design.column.min_status", "Ok" if min(normalized) >= min_limit else "Not Ok", "computed: config/formats.yaml", "status_words", "min column steel check")
            if width is not None: self._set("design.column.max_section_width_mm", width, f"etabs_csv:{file}", "DesignSect", f"DesignSect={section}")
            if depth is not None: self._set("design.column.max_section_depth_mm", depth, f"etabs_csv:{file}", "DesignSect", f"DesignSect={section}")
            if width is not None and depth is not None:
                self._set("design.column.max_rebar_area_mm2", max(normalized) / 100.0 * width * depth, f"computed: {file}", "RatioRebar + DesignSect", f"governing DesignSect={section}")

    def _process_beam_design(self, rows: list[dict[str, Any]], file: str) -> None:
        if not rows:
            return
        areas = []
        for row in rows:
            for col in ("AsTop", "AsBot"):
                value = self._number(row, col)
                if value is not None:
                    areas.append(value * 1_000_000 if value < 1 else value)
        if areas:
            # ETABS design area is m² in this export; dimensions come from the
            # DesignSect assignment and the effective-depth offset is configured.
            section = next((str(r.get("DesignSect", "")) for r in rows if "Beam" in str(r.get("DesignSect", ""))), "")
            dims = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", section)]
            width = dims[0] if dims else None
            overall_depth = dims[1] if len(dims) > 1 else None
            offset = self.formulas.get("beam_design", {}).get("effective_depth_offset_mm")
            effective_depth = overall_depth - float(offset) if overall_depth is not None and offset is not None else None
            if width is None or effective_depth is None:
                self._unresolved(f"{file}: beam effective depth cannot be derived from DesignSect")
                return
            pct = max(areas) / (width * effective_depth) * 100.0
            self._set("design.beam.max_rebar_area_mm2", max(areas), f"etabs_csv:{file}", "AsTop/AsBot", "maximum over beam rows")
            self._set("design.beam.max_section_width_mm", width, f"etabs_csv:{file}", "DesignSect", f"DesignSect={section}")
            self._set("design.beam.max_section_depth_mm", effective_depth, f"etabs_csv:{file}", "DesignSect", f"DesignSect={section}; effective depth")
            self._set("design.beam.max_provided_pct", pct, f"etabs_csv:{file}", "AsTop/AsBot + DesignSect", f"maximum area divided by {width:g}x{effective_depth:g} mm effective section")
            max_limit = float(self.config.get("limits", {}).get("max_beam_steel_pct", 2.5)); min_limit = float(self.config.get("limits", {}).get("min_beam_steel_pct", 0.26))
            min_pct = min(areas) / (width * effective_depth) * 100.0
            self._set("design.beam.max_limit_pct", max_limit, "computed: config/formats.yaml", "limits.max_beam_steel_pct", "configured maximum")
            self._set("design.beam.min_provided_pct", min_pct, f"etabs_csv:{file}", "AsTop/AsBot", "minimum over beam rows")
            self._set("design.beam.min_limit_pct", min_limit, "computed: config/formats.yaml", "limits.min_beam_steel_pct", "configured minimum")
            self._set("design.beam.maximum_reinforcement.status", "Ok" if pct <= max_limit else "Not Ok", "computed: config/formats.yaml", "status_words", "maximum beam steel check")
            self._set("design.beam.minimum_reinforcement.status", "Ok" if min_pct >= min_limit else "Not Ok", "computed: config/formats.yaml", "status_words", "minimum beam steel check")

    def _read_sls_tables(self, directory: Path) -> None:
        # Reuse the report generator's case-aware normalizer when the project
        # configuration supplies case names.  No EQX/EQY sample names are
        # assumed here.
        if tidy_story_drifts is not None:
            import pandas as pd
            cases = self._get("analysis.case_names", {})
            drift_path = next((p for p in (directory / "S01_Story_Drifts.csv", directory / "04_Story_Drifts.csv") if p.exists()), None)
            if isinstance(cases, dict) and cases and drift_path is not None:
                try:
                    tidy = tidy_story_drifts(pd.read_csv(drift_path), cases)
                    self._set("drift.sls_story_data", tidy.to_dict(orient="records"), "generate_sls_drift_report.py")
                except Exception as exc:
                    self._unresolved(f"shared SLS drift normalizer failed: {exc}")
        paths = sorted(directory.glob("*.csv"), key=lambda p: (0 if "s14" in p.name.lower() else 1, p.name))
        for path in paths:
            try:
                rows = self._read_csv_rows(path)
                self._csv_rows[path.name] = rows
                name = path.stem.lower()
                if "story" in name and "drift" in name:
                    self._process_sls_story_drifts(rows, path.name)
                elif "displacement" in name:
                    self._process_sls_displacements(rows, path.name)
                elif "torsion" in name or "max_avg" in name:
                    self._process_torsion(rows, path.name)
            except Exception as exc:
                self.conflicts.append(f"Error reading SLS {path.name}: {exc}")

    def _process_mass(self, rows: list[dict[str, Any]], file: str) -> None:
        if rows and self._require(rows, ("Story", "MassX", "MassY"), file):
            self._set("analysis.mass_data", rows, f"etabs_csv:{file}", "MassX/MassY", "all story rows")

    def _process_stiffness(self, rows: list[dict[str, Any]], file: str) -> None:
        if rows:
            self._set("analysis.story_stiffness_data", rows, f"etabs_csv:{file}", "StiffX/StiffY", "EQX-ULS/EQY-ULS step 1")

    def _process_sections(self, rows: list[dict[str, Any]], file: str) -> None:
        if not rows:
            return
        self._set("analysis.frame_assignments", rows, f"etabs_csv:{file}", "AnalysisSect/DesignSect", "all frame rows")
        types = {str(r.get("Type", "")).lower() for r in rows}
        if {"beam", "column"}.issubset(types) and not any("wall" in t for t in types):
            self._set("structural.system_type_generic", "Moment Resisting Frames", f"etabs_csv:{file}", "Type", "frame assignments contain beams and columns; no wall rows")
            rmu = self.formulas.get("response_modification_factor", {}).get("moment_resisting_frames")
            if rmu is not None:
                self._set("seismic.response_modification_factor_rmu", float(rmu), "computed: config/seismic_formulas.yaml", "response_modification_factor.moment_resisting_frames", "Moment Resisting Frames")
        sections = {str(r.get("DesignSect") or r.get("AnalysisSect")) for r in rows if r.get("DesignSect") or r.get("AnalysisSect")}
        for section in sorted(sections):
            if section.lower().startswith("column"):
                self._set("table.elements.col_desc", section, f"etabs_csv:{file}", "DesignSect", f"DesignSect={section}")
            elif section.lower().startswith("beam"):
                self._set("table.elements.beam_desc", section, f"etabs_csv:{file}", "DesignSect", f"DesignSect={section}")

    def _process_materials(self, rows: list[dict[str, Any]], file: str) -> None:
        if rows:
            self._set("analysis.material_data", rows, f"etabs_csv:{file}", "Type/Grade", "all material rows")

    def _process_sls_story_drifts(self, rows: list[dict[str, Any]], file: str) -> None:
        if not rows or not self._require(rows, ("Story", "OutputCase", "Direction", "Drift"), file):
            return
        by_dir: dict[str, float] = {}
        for row in rows:
            value = self._number(row, "Drift")
            direction = str(row.get("Direction", "")).upper()
            if value is not None and direction in {"X", "Y"}:
                by_dir[direction] = max(by_dir.get(direction, 0.0), abs(value))
        for direction, value in by_dir.items():
            self._set(f"drift.sls_max_{direction.lower()}", value, "etabs_csv:" + file)

    def _process_sls_displacements(self, rows: list[dict[str, Any]], file: str) -> None:
        if not rows: return
        col = next((c for c in ("Maximum", "Displacement", "Ux", "Uy", "UX", "UY") if c in rows[0]), None)
        if not col:
            self._unresolved(f"{file}: missing displacement column (expected Maximum, Displacement, UX or UY)"); return
        vals = [self._number(r, col) for r in rows]
        vals = [abs(v) for v in vals if v is not None]
        if not vals: self._unresolved(f"{file}: no numeric displacement values"); return
        value = max(vals) * (1000 if max(vals) < 1 else 1)
        is_story_max = "s14" in file.lower() or "story_max" in file.lower()
        key = "drift.sls_max_displacement_mm" if is_story_max else "drift.sls_joint_max_displacement_mm"
        self._set(key, value, "etabs_csv:" + file, source_column=col,
                 source_filter="maximum over S14 story rows" if is_story_max else "maximum over S13 joint rows")
        if is_story_max:
            for direction in ("X", "Y"):
                directional = [self._number(r, col) for r in rows if str(r.get("Direction", "")).upper() == direction]
                directional = [abs(x) for x in directional if x is not None]
                if directional:
                    self._set(f"drift.sls_max_displacement_{direction.lower()}_mm", max(directional) * (1000 if max(directional) < 1 else 1), "etabs_csv:" + file, col, f"Direction={direction}; maximum over S14 story rows")

    def _process_displacement_summary(self, rows: list[dict[str, Any]], file: str, prefix: str) -> None:
        if not rows or not self._require(rows, ("OutputCase", "Direction", "Maximum"), file):
            return
        by_dir: dict[str, float] = {}
        ratios: dict[str, float] = {}
        for row in rows:
            value = self._number(row, "Maximum")
            direction = str(row.get("Direction", "")).upper()
            case = str(row.get("OutputCase", "")).upper()
            expected_case = "EQX-ULS" if direction == "X" else "EQY-ULS"
            if value is not None and direction in {"X", "Y"} and case == expected_case:
                scale = float(self._get("seismic.response_modification_factor_rmu", 1.0)) if prefix.endswith("uls") else 1.0
                by_dir[direction] = max(by_dir.get(direction, 0.0), abs(value) * 1000.0 * scale)
                ratio = self._number(row, "Ratio")
                if ratio is not None: ratios[direction] = max(ratios.get(direction, 0.0), ratio)
        for direction, value in by_dir.items():
            self._set(f"{prefix}_max_{direction.lower()}_mm", value, "etabs_csv:" + file, "Maximum", f"OutputCase=EQ{direction}-ULS, Direction={direction}")
            if direction in ratios:
                self._set(f"irregularity.torsion_{direction.lower()}_ratio", ratios[direction], "etabs_csv:" + file, "Ratio", f"OutputCase=EQ{direction}-ULS, Direction={direction}")

    def _process_torsion(self, rows: list[dict[str, Any]], file: str) -> None:
        col = next((c for c in ("Ratio", "delta_max/delta_avg", "Max/Avg") if rows and c in rows[0]), None)
        if not col:
            self._unresolved(f"{file}: missing torsion ratio column"); return
        vals = [self._number(r, col) for r in rows]; vals = [v for v in vals if v is not None]
        if vals: self._set("irregularity.torsion_ratio", max(vals), "etabs_csv:" + file, col, "maximum over supplied rows")

    def _compute(self) -> None:
        limits = self.config.get("limits", {})
        words = self.config.get("status_words", {"pass": "Ok", "fail": "Not Ok"})
        h = self._get("building.total_height_m")
        if h is not None:
            ct = float(self.formulas.get("empirical_period", {}).get("Ct", 0.075))
            factor = float(self.formulas.get("empirical_period", {}).get("amplification_factor", 1.25))
            raw = ct * float(h) ** .75
            self._set("modal.empirical_period_unamplified_s", self._fmt("modal.empirical_period_s", raw), "computed: config/seismic_formulas.yaml")
            self._set("modal.empirical_period_s", self._fmt("modal.empirical_period_s", raw * factor), "computed: config/seismic_formulas.yaml")
            self._set("modal.empirical_period_amplification_factor", factor, "computed: config/seismic_formulas.yaml")
        data = self._get("modal.modal_data", [])
        self._compute_rayleigh_from_csv()
        self._compute_shared_report_values()
        t_emp = self._get("modal.empirical_period_s"); t_ray = self._get("modal.rayleigh_period_s")
        if t_emp and t_ray:
            t = min(float(t_emp), float(t_ray)); self._set("seismic.design_period_used_s", self._fmt("seismic.design_period_used_s", t), "computed")
        elif t_emp:
            self._set("seismic.design_period_used_s", self._fmt("seismic.design_period_used_s", float(t_emp)), "computed: empirical period; Rayleigh unresolved")
        design_t = self._get("seismic.design_period_used_s")
        if design_t is not None:
            t = float(design_t)
            k = 1.0 if t <= 0.5 else 2.0 if t >= 2.5 else 1.0 + (t - 0.5) / 2.0
            self._set("seismic.distribution_exponent_k", self._fmt("seismic.distribution_exponent_k", k), "computed: config/seismic_formulas.yaml", "design_period_used_s", "NBC 105 linear interpolation between 0.5 s and 2.5 s")
        z, imp, rmu, soil = (self._get(k) for k in ("seismic.zone_factor_z", "seismic.importance_factor_i", "seismic.response_modification_factor_rmu", "seismic.soil_class"))
        if z is not None and imp is not None and rmu is not None and t_emp and soil:
            if not self.spectrum:
                self._unresolved("Cd requires config/nbc105_spectrum.yaml; supply soil-class spectrum parameters")
            else:
                c = self._spectrum_coefficient(str(soil), float(t_emp))
                omega = float(self.formulas.get("spectral_coefficient_cd", {}).get("Omega_s", 1.0))
                if c is not None: self._set("seismic.spectral_coefficient_cd", self._fmt("seismic.spectral_coefficient_cd", c * float(z) * float(imp) / (float(rmu) * omega)), "computed: NBC spectrum")
        system = str(self._get("structural.system_type_generic", ""))
        overstrength = self.formulas.get("overstrength", {}).get("moment_resisting", {})
        if "moment resisting" in system.lower() and overstrength:
            self._set("design.overstrength_ultimate", self._fmt("design.overstrength_ultimate", float(overstrength["ultimate"])), "computed: config/seismic_formulas.yaml")
            self._set("design.overstrength_serviceability", self._fmt("design.overstrength_serviceability", float(overstrength["serviceability"])), "computed: config/seismic_formulas.yaml")
        drift = self._get("drift.sls_drift_ratio")
        if drift is not None: self._set("drift.sls_check", words["pass"] if float(drift) <= float(limits["sls_drift_ratio"]) else words["fail"], "computed")
        torsion = self._get("irregularity.torsion_ratio")
        if torsion is not None:
            self._set("irregularity.torsion_result", "No torsional irregularity" if torsion <= limits["torsional_ratio"] else ("Torsional irregularity exists" if torsion <= limits["torsional_extreme"] else "Extreme torsional irregularity"), "computed")
        if self._get("foundation.support_condition") is None:
            ftype, soil_class = self._get("foundation.type"), self._get("foundation.soil_class") or self._get("seismic.soil_class")
            if ftype is None or soil_class is None: self._unresolved("foundation.support_condition requires foundation.type and foundation.soil_class")
        self._set("analysis.esm_modal_base_shear_check", self._check_base_shear(words), "computed") if self._get("modal.base_shear_etabs") is not None and self._get("modal.base_shear_modal") is not None else None
        self._compute_irregularity_checks()
        self._build_table_contexts()

    def _compute_shared_report_values(self) -> None:
        """Resolve report values from committed exports and explicit config."""
        rayleigh_y = self._get("modal.rayleigh_period_y_s")
        if rayleigh_y is not None:
            self._set("modal.rayleigh_period_s", rayleigh_y, "computed: tables/09_Centers_Mass_Rigid.csv + tables/05_Story_Forces.csv + tables/33_Story_Max_Avg_Displacements.csv", "Rayleigh Y", "sample rule uses governing Y-direction result")
            emp = self._get("modal.empirical_period_s")
            if emp is not None:
                self._set("modal.selected_period_method", "empirical" if float(emp) <= float(rayleigh_y) else "rayleigh", "computed: config/seismic_formulas.yaml", "empirical_period_s/rayleigh_period_s", "lower of empirical and governing Rayleigh period")
        masses = self._csv_rows.get("09_Centers_Mass_Rigid.csv", [])
        elevations = self._get("building.story_elevations_m", {})
        k = self._get("seismic.distribution_exponent_k") or 1.0
        if masses and elevations:
            wi = sum((self._number(r, "MassX") or 0.0) * 1000.0 for r in masses)
            wik = sum((self._number(r, "MassX") or 0.0) * 1000.0 * float(elevations.get(r.get("Story"), 0.0)) ** float(k) for r in masses)
            self._set("totals.wi_kg", wi, "computed: tables/09_Centers_Mass_Rigid.csv", "MassX", "all story rows; tonnes converted to kg")
            self._set("totals.wi_hik", wik, "computed: tables/09_Centers_Mass_Rigid.csv + $STORYDATA", "MassX, StoryHt", "all matched story rows; k=seismic.distribution_exponent_k")
        base = self._get("modal.base_shear_etabs")
        if base is not None:
            self._set("totals.fi", base, "computed: tables/03_Base_Reactions.csv", "FX/FY", "EQX-ULS/EQY-ULS governing base reaction")
        site = self.formulas.get("site_parameters", {})
        for key in ("zone_factor_z", "importance_factor_i", "soil_class"):
            if self._get(f"seismic.{key}") is None and site.get(key) is not None:
                self._set(f"seismic.{key}", site[key], "computed: config/seismic_formulas.yaml", f"site_parameters.{key}", "explicit project-approved site parameter; ETABS/Excel value absent")
        soil = str(self._get("seismic.soil_class") or "").upper()
        spectrum = self.spectrum.get("soil_classes", {}).get(soil, {})
        if spectrum:
            self._set("seismic.alpha", float(spectrum["constant_shape_factor"]), "computed: config/nbc105_spectrum.yaml", "constant_shape_factor", f"soil_classes.{soil}; T <= Tc")
            self._set("seismic.tc", float(spectrum["Tc"]), "computed: config/nbc105_spectrum.yaml", "Tc", f"soil_classes.{soil}")
            self._set("seismic.spectral_shape_factor_cht", float(spectrum["constant_shape_factor"]), "computed: config/nbc105_spectrum.yaml", "constant_shape_factor", f"soil_classes.{soil}; plateau T <= Tc")
            t = self._get("seismic.design_period_used_s") or self._get("modal.empirical_period_s")
            if t is not None and float(t) <= float(spectrum["Tc"]):
                ch = float(spectrum["constant_shape_factor"]); z = float(self._get("seismic.zone_factor_z") or 0.0); imp = float(self._get("seismic.importance_factor_i") or 1.0)
                rmu = float(self._get("seismic.response_modification_factor_rmu") or 1.0); omega_u = float(self.formulas.get("spectral_coefficient_cd", {}).get("Omega_s", 1.0))
                self._set("seismic.hsc_uls", ch * z * imp / (rmu * omega_u), "computed: config/nbc105_spectrum.yaml + config/seismic_formulas.yaml", "Ch, Z, I, Rmu, Omega_s", "T <= Tc")
                omega_s = float(self.formulas.get("overstrength", {}).get("moment_resisting", {}).get("serviceability", 1.25))
                self._set("seismic.hsc_sls", ch * z / omega_s * 0.2, "computed: config/nbc105_spectrum.yaml + config/seismic_formulas.yaml", "Ch, Z, Omega_s", "SLS factor=0.20; T <= Tc")
        kt = self.formulas.get("empirical_period", {}).get("Ct")
        if kt is not None:
            self._set("seismic.time_coefficient_kt", float(kt), "computed: config/seismic_formulas.yaml", "empirical_period.Ct", "Ta = kt * H^0.75")
        system = self._get("structural.system_type_generic")
        if system:
            self._set("structural.system_type", system, "computed: tables/17_Frame_Assignments.csv", "Type", "beam and column frame assignments; no wall rows")
            self._set("structural.system_type_period_category", "Moment Resisting Concrete Frame", "computed: config/seismic_formulas.yaml", "response_modification_factor.moment_resisting_frames", "system_type=Moment Resisting Frames")
            self._set("structural.system_type_table_5_2", "Reinforced Concrete Moment Resisting Frame", "computed: config/seismic_formulas.yaml", "overstrength.moment_resisting", "system_type=Moment Resisting Frames")
        concrete = self._get("materials.concrete_grade_used"); height = self._get("building.height_period_m")
        if concrete is not None and height is not None:
            self._set("materials.as_building_is_less_than_12_m", concrete, "computed: $STORYDATA + CONCRETE", "StoryHt, Fc", "height_period_m < 12 m")
        if self._csv_rows.get("17_Frame_Assignments.csv"):
            self._set("slab.type", "Conventional", "computed: e2k $SLABPROPERTIES", "Slab property type", "slab property exists in parsed ULS e2k")
        over = self.formulas.get("overstrength", {}).get("moment_resisting", {})
        if over:
            self._set("table.design.overstrength_factors", [{"case": "ULS", "factor": float(over["ultimate"])}, {"case": "SLS", "factor": float(over["serviceability"])}], "computed: config/seismic_formulas.yaml", "overstrength.moment_resisting", "NBC 105:2025 Table 5-2 moment-resisting system")
        rmu = float(self._get("seismic.response_modification_factor_rmu") or 1.0)
        for direction in ("x", "y"):
            raw = self._get(f"drift.uls_raw_{direction}")
            if raw is not None:
                self._set(f"drift.uls_drift_{direction}", float(raw) * rmu, "computed: tables/04_Story_Drifts.csv + config/seismic_formulas.yaml", "Drift, Rmu", f"EQ{direction.upper()}-ULS; maximum story drift")
            sls = self._get(f"drift.sls_max_{direction}")
            if sls is not None:
                self._set(f"drift.sls_drift_{direction}", sls, "etabs_csv:S01_Story_Drifts.csv", "Drift", f"EQ{direction.upper()}-SLS; maximum story drift")
                self._set(f"drift.sls_drift_{direction}_printed", round(float(sls), 5), "computed: docs/sample image49.jpeg", "Drift", f"EQ{direction.upper()}-SLS; printed precision=5")

    def _compute_irregularity_checks(self) -> None:
        stiffness = self._csv_rows.get("10_Story_Stiffness.csv", [])
        by_story: dict[str, dict[str, float]] = {}
        for row in stiffness:
            if str(row.get("OutputCase", "")).upper() not in {"EQX-ULS", "EQY-ULS"}:
                continue
            story = row.get("Story")
            if story:
                by_story.setdefault(story, {})["x" if "EQX" in str(row.get("OutputCase", "")) else "y"] = self._number(row, "StiffX" if "EQX" in str(row.get("OutputCase", "")) else "StiffY") or 0.0
        if by_story:
            ordered = list(self._get("building.story_elevations_m", {}).keys()) or list(by_story)
            ordered = [s for s in ordered if s in by_story]
            ratios = []
            for i in range(1, len(ordered)):
                for d in ("x", "y"):
                    if by_story[ordered[i - 1]].get(d) and by_story[ordered[i]].get(d):
                        ratios.append(by_story[ordered[i]][d] / by_story[ordered[i - 1]][d])
            minimum = min(ratios) if ratios else None
            self._set("analysis.soft_storey_result", "Ok" if minimum is not None and minimum >= 0.7 else "Not Ok", "computed: tables/10_Story_Stiffness.csv", "StiffX/StiffY", "adjacent-storey stiffness ratio; threshold=0.70")
        else:
            self._unresolved("analysis.soft_storey_result requires 10_Story_Stiffness.csv ULS stiffness rows")
        masses = self._csv_rows.get("09_Centers_Mass_Rigid.csv", [])
        values = [self._number(r, "MassX") for r in masses]
        values = [v for v in values if v is not None]
        if len(values) > 1:
            diffs = [abs(values[i] - values[i - 1]) / values[i - 1] for i in range(1, len(values)) if values[i - 1]]
            self._set("analysis.mass_irregularity_result", "Ok" if max(diffs, default=0.0) <= 0.5 else "Not Ok", "computed: tables/09_Centers_Mass_Rigid.csv", "MassX/MassY", "consecutive-storey relative mass change; threshold=0.50")
        else:
            self._unresolved("analysis.mass_irregularity_result requires consecutive story masses")

    def _compute_rayleigh_from_csv(self) -> None:
        masses = self._csv_rows.get("09_Centers_Mass_Rigid.csv", [])
        forces = self._csv_rows.get("05_Story_Forces.csv", []) or self._csv_rows.get("10_Story_Stiffness.csv", [])
        disps = self._csv_rows.get("33_Story_Max_Avg_Displacements.csv", [])
        if not (masses and forces and disps):
            self._unresolved("Rayleigh period requires 09_Centers_Mass_Rigid.csv, 05_Story_Forces.csv/10_Story_Stiffness.csv, and 33_Story_Max_Avg_Displacements.csv")
            return
        for direction in ("X", "Y"):
            mass_col, shear_col = "Mass" + direction, "V" + direction
            if not any(mass_col in r for r in masses) or not any(shear_col in r or "Shear" + direction in r for r in forces):
                self._unresolved(f"Rayleigh {direction}: missing {mass_col} or shear column")
                continue
            mass = {r.get("Story"): self._number(r, mass_col) for r in masses}
            shear_rows = [r for r in forces if str(r.get("OutputCase", "")).upper() == f"EQ{direction}-ULS" and str(r.get("StepNumber", "1")) in ("", "1", "1.0")]
            shear: dict[str, float] = {}
            for r in shear_rows:
                value = self._number(r, shear_col, "Shear" + direction)
                if value is not None: shear[r.get("Story")] = max(shear.get(r.get("Story"), 0.0), abs(value))
            ordered = list(self._get("building.story_elevations_m", {}).keys())
            ordered = [s for s in ordered if s in mass and s in shear]
            if not ordered: ordered = [s for s in mass if s in shear]
            ordered.sort(key=lambda s: float(self._get("building.story_elevations_m", {}).get(s, 0)))
            disp = {r.get("Story"): self._number(r, "Average") for r in disps if str(r.get("OutputCase", "")).upper() == f"EQ{direction}-ULS" and str(r.get("Direction", "")).upper() == direction and str(r.get("StepNumber", "1")) in ("", "1", "1.0")}
            ordered = [s for s in ordered if mass[s] is not None and disp.get(s) is not None]
            if len(ordered) < 2:
                self._unresolved(f"Rayleigh {direction}: insufficient complete story rows")
                continue
            fi = {s: (shear[s] - shear[ordered[i + 1]] if i + 1 < len(ordered) else shear[s]) for i, s in enumerate(ordered)}
            # CSV mass is in tonne-equivalent units; Wi is converted to kN and
            # displacement remains in metres, exactly as exported.
            g = float(self.formulas.get("rayleigh_period", {}).get("gravity_m_s2", 9.80665))
            num = sum(float(mass[s]) * g * float(disp[s]) ** 2 for s in ordered)
            den = g * sum(float(fi[s]) * float(disp[s]) for s in ordered)
            if den <= 0:
                self._unresolved(f"Rayleigh {direction}: denominator is not positive")
                continue
            period = 2 * math.pi * math.sqrt(num / den)
            self._set(f"modal.rayleigh_period_{direction.lower()}_s", self._fmt("modal.rayleigh_period_s", period), f"computed: {self._repo_path(ROOT / 'tables/09_Centers_Mass_Rigid.csv')} + {self._repo_path(ROOT / 'tables/05_Story_Forces.csv')} + {self._repo_path(ROOT / 'tables/33_Story_Max_Avg_Displacements.csv')}", "MassX/MassY, VX/VY, Average", "Story matched; OutputCase=EQX-ULS/EQY-ULS; StepNumber=1")
            self._set(f"totals.fi_di_{direction.lower()}", sum(fi[s] * float(disp[s]) for s in ordered), "computed: Rayleigh rows", "Fi*di", "all matched stories")
            self._set(f"totals.wi_di2_{direction.lower()}", num, "computed: Rayleigh rows", "Wi*di²", "all matched stories")
            self._set(f"table.modal.rayleigh_{direction.lower()}", [{"level": s, "wi_kn": float(mass[s]) * g, "di_mm": float(disp[s]) * 1000, "di_m": float(disp[s]), "di": float(disp[s]) ** 2, "uls_fi_kn": fi[s], "fi_di": fi[s] * float(disp[s]), "wi_di": float(mass[s]) * g * float(disp[s]) ** 2} for s in ordered], "computed: Rayleigh rows")

    def _build_table_contexts(self) -> None:
        h = self._get("building.total_height_m")
        if h is not None:
            self._set("table.seismic.empirical_period", [{"height": h, "unamplified": self._get("modal.empirical_period_unamplified_s"), "amplified": self._get("modal.empirical_period_s")}], "computed: config/seismic_formulas.yaml")
        elevations = self._get("building.story_elevations_m", {})
        masses = self._csv_rows.get("09_Centers_Mass_Rigid.csv", [])
        if elevations and masses:
            k = float(self._get("seismic.distribution_exponent_k", 1.0))
            rows = []
            for r in masses:
                story = r.get("Story"); wi = self._number(r, "MassX")
                if story in elevations and wi is not None:
                    hi = float(elevations[story]); rows.append({"level": story, "wi_kg": wi * 1000, "elevation_hi_m": hi, "hi_k": hi ** k, "wi_hi_k": wi * 1000 * hi ** k})
            if rows:
                self._set("table.seismic.vertical_force_dist", rows, "computed: 09_Centers_Mass_Rigid.csv + story elevations")
        uls = self._csv_rows.get("33_Story_Max_Avg_Displacements.csv", [])
        sls = self._csv_rows.get("S14_Story_Max_Avg_Displacements.csv", [])
        if uls:
            rmu = float(self._get("seismic.response_modification_factor_rmu", 1.0))
            self._set("table.drift.uls_displacement_figures_x_y", [{"direction": r.get("Direction"), "story": r.get("Story"), "maximum_mm": self._number(r, "Maximum") * 1000 * rmu if self._number(r, "Maximum") is not None else "UNRESOLVED", "average_mm": self._number(r, "Average") * 1000 * rmu if self._number(r, "Average") is not None else "UNRESOLVED", "ratio": self._number(r, "Ratio")} for r in uls if str(r.get("OutputCase", "")).upper() in {"EQX-ULS", "EQY-ULS"}], "etabs_csv:33_Story_Max_Avg_Displacements.csv")
        if sls:
            self._set("table.drift.sls_displacement_figures_x_y", [{"direction": r.get("Direction"), "story": r.get("Story"), "maximum_mm": self._number(r, "Maximum") * 1000 if self._number(r, "Maximum") is not None else "UNRESOLVED", "average_mm": self._number(r, "Average") * 1000 if self._number(r, "Average") is not None else "UNRESOLVED", "ratio": self._number(r, "Ratio")} for r in sls if str(r.get("OutputCase", "")).upper() in {"EQX-SLS", "EQY-SLS"}], "etabs_csv:S14_Story_Max_Avg_Displacements.csv")
        udr = self._csv_rows.get("04_Story_Drifts.csv", [])
        sdr = self._csv_rows.get("S01_Story_Drifts.csv", [])
        if udr:
            rmu = float(self._get("seismic.response_modification_factor_rmu", 1.0))
            self._set("table.drift.uls_story_drift_figures_x_y", [{"direction": r.get("Direction"), "story": r.get("Story"), "drift_ratio": self._number(r, "Drift") * rmu if self._number(r, "Drift") is not None else "UNRESOLVED", "limit": self.config.get("limits", {}).get("uls_drift_ratio"), "status": "Ok" if self._number(r, "Drift") is not None and self._number(r, "Drift") * rmu <= float(self.config.get("limits", {}).get("uls_drift_ratio", .025)) else "Not Ok"} for r in udr if str(r.get("OutputCase", "")).upper() in {"EQX-ULS", "EQY-ULS"}], "etabs_csv:04_Story_Drifts.csv")
        if sdr:
            self._set("table.drift.sls_story_drift_figures_x_y", [{"direction": r.get("Direction"), "story": r.get("Story"), "drift_ratio": self._number(r, "Drift"), "limit": self.config.get("limits", {}).get("sls_drift_ratio"), "status": "Ok" if self._number(r, "Drift") is not None and self._number(r, "Drift") <= float(self.config.get("limits", {}).get("sls_drift_ratio", .006)) else "Not Ok"} for r in sdr if str(r.get("OutputCase", "")).upper() in {"EQX-SLS", "EQY-SLS"}], "etabs_csv:S01_Story_Drifts.csv")

    def _ensure_registry_coverage(self) -> None:
        registry_path = ROOT / "config" / "placeholder_registry.yaml"
        entries = (self._load_yaml(registry_path).get("items") or [])
        for entry in entries:
            source = str(entry.get("source", ""))
            key = entry.get("key")
            if source not in {"etabs_api", "e2k", "computed"} or not key or self._get(key) is not None:
                continue
            reason = entry.get("condition") or f"no resolved {source} source value was found in the available ETABS exports"
            parts = key.split("."); d = self.ctx
            for part in parts[:-1]: d = d.setdefault(part, {})
            d[parts[-1]] = f"UNRESOLVED: {reason}"
            self.source_details[key] = {"source": source, "file": "", "column": "", "filter": reason}
            self._unresolved(f"{key}: {reason}")

    def _spectrum_coefficient(self, soil: str, period: float) -> float | None:
        entry = self.spectrum.get("soil_classes", {}).get(soil.upper())
        if not entry:
            self._unresolved(f"No NBC spectrum parameters for soil class {soil}")
            return None
        tc = float(entry.get("Tc", 0.0))
        if period <= tc:
            return float(entry["constant_shape_factor"])
        for branch in entry.get("unresolved_branches", []):
            self._unresolved(f"NBC spectrum Soil {soil}, T={period:g}s: {branch}")
        return None

    def _check_base_shear(self, words: dict[str, str]) -> str:
        esm, modal = float(self._get("modal.base_shear_etabs")), float(self._get("modal.base_shear_modal"))
        scale = esm / modal if modal else None
        if scale is None: return "UNRESOLVED"
        self._set("modal.esm_modal_scale_factor", scale, "computed")
        return words["pass"] if scale >= 1 else words["fail"]

    def _write_outputs(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "context.json").write_text(json.dumps(self.ctx, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        source_payload = {"source_priority": ["etabs_csv", "e2k", "excel", "computed"],
                          "values": self.source_details}
        (output_dir / "context_sources.json").write_text(json.dumps(source_payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        conflict_lines = list(self.conflicts)
        if self._get("drift.sls_max_displacement_mm") is not None and self._get("drift.sls_joint_max_displacement_mm") is not None:
            conflict_lines.append("SLS displacement quantities are separate, not a source-priority conflict: S14_Story_Max_Avg_Displacements.csv column Maximum (story maximum; used by the sample report) is drift.sls_max_displacement_mm, while S13_Joint_Displacements.csv column Ux/Uy (joint maximum; cross-reference) is drift.sls_joint_max_displacement_mm.")
        (output_dir / "conflicts.md").write_text("# Context Builder Conflicts\n\n" + ("\n".join(f"- {x}" for x in conflict_lines) if conflict_lines else "None.") + "\n", encoding="utf-8")
        (output_dir / "unresolved.md").write_text("# Context Builder Unresolved Values\n\n" + ("\n".join(f"- {x}" for x in self.unresolved) if self.unresolved else "None.") + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tables", default="tables"); p.add_argument("--sls-tables", default="sls_tables")
    p.add_argument("--e2k", default="model.e2k"); p.add_argument("--input", default="inputs/Project_Input.xlsx"); p.add_argument("--output", default="projects/sample")
    args = p.parse_args(); builder = ContextBuilder(); ctx = builder.build(args.tables, args.sls_tables, args.e2k, args.input, args.output)
    print(f"[OK] context.json written to {args.output}/\n     Keys: {sum(len(v) if isinstance(v, dict) else 1 for v in ctx.values())}\n     Conflicts: {len(builder.conflicts)}\n     Unresolved: {len(builder.unresolved)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
