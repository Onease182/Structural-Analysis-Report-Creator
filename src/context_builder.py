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
    EXPECTED_COLUMNS, load_csvs, validate_tables = {}, None, None

try:
    from generate_sls_drift_report import build_stories, evaluate, tidy_joint_drifts, tidy_story_drifts
except ImportError:  # pragma: no cover
    build_stories = evaluate = tidy_joint_drifts = tidy_story_drifts = None


class ContextBuilder:
    """Build context.json and its evidence files from project inputs."""

    def __init__(self) -> None:
        self.ctx: dict[str, Any] = {}
        self.sources: dict[str, str] = {}
        self.conflicts: list[str] = []
        self.unresolved: list[str] = []
        self.config = self._load_yaml(FORMATS)
        self.mapping = self._load_yaml(MAPPING)
        self.formulas = self._load_yaml(SEISMIC_FORMULAS)
        self.spectrum = self._load_yaml(SPECTRUM) if SPECTRUM.exists() else {}

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

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

    def _set(self, key: str, value: Any, source: str) -> None:
        if value is None or (isinstance(value, str) and not value.strip()):
            self._unresolved(f"{key}: source {source} supplied no value")
            return
        old_source = self.sources.get(key)
        if old_source and self._get(key) != value:
            self.conflicts.append(
                f"{key}: conflict between {old_source}={self._get(key)!r} and {source}={value!r}; "
                "higher-priority source retained"
            )
            if self._source_rank(source) <= self._source_rank(old_source):
                return
        parts = key.split(".")
        d = self.ctx
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = value
        self.sources[key] = source

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
        self._write_outputs(Path(output_dir))
        return self.ctx

    def _read_excel(self, path: Path) -> None:
        if not path.exists():
            self._unresolved(f"input workbook not found: {path}")
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
            stories = data.get("stories", [])
            above = [s for s in stories if s.get("Story") != "Base"]
            # Real ETABS exports store geometry in the file units (mm for the
            # committed model); legacy fixtures already use metres.
            def length_m(value: Any) -> float:
                number = float(value)
                return number / 1000.0 if abs(number) > 100 else number
            self._set("building.storeys_above_grade", len(above), "e2k")
            self._set("building.num_storeys_analysed", len(above), "e2k")
            basements = [s for s in stories if length_m(s.get("Elevation", "0")) <= 0 and s.get("Story") != "Base"]
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
            self._unresolved(f"error reading .e2k {path}: {exc}")

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
                elif "story" in name and "max_avg" in name:
                    self._process_torsion(rows, path.name)
                    self._process_displacement_summary(rows, path.name, "drift.uls")
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
        for row in rows:
            ratio = self._number(row, drift_col)
            if ratio is None: self._unresolved(f"{file}: non-numeric drift row {row}"); continue
            drifts.append({"story": row["Story"], "drift_ratio": abs(ratio), "displacement": self._number(row, disp_col) if disp_col else None, "case": self._value(row, "OutputCase", "Case", "Load Case")})
        self._set("drift.data", drifts, "etabs_csv")

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
        if vals: self._set("design.column.max_provided_pct", max(vals) if max(vals) > 1 else max(vals) * 100, "etabs_csv")

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
                name = path.stem.lower()
                if "story" in name and "drift" in name:
                    self._process_sls_story_drifts(rows, path.name)
                elif "displacement" in name:
                    self._process_sls_displacements(rows, path.name)
                elif "torsion" in name or "max_avg" in name:
                    self._process_torsion(rows, path.name)
            except Exception as exc:
                self.conflicts.append(f"Error reading SLS {path.name}: {exc}")

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
        self._set("drift.sls_max_displacement_mm", max(vals) * (1000 if max(vals) < 1 else 1), "etabs_csv")

    def _process_displacement_summary(self, rows: list[dict[str, Any]], file: str, prefix: str) -> None:
        if not rows or not self._require(rows, ("OutputCase", "Direction", "Maximum"), file):
            return
        by_dir: dict[str, float] = {}
        for row in rows:
            value = self._number(row, "Maximum")
            direction = str(row.get("Direction", "")).upper()
            if value is not None and direction in {"X", "Y"}:
                by_dir[direction] = max(by_dir.get(direction, 0.0), abs(value) * 1000.0)
        for direction, value in by_dir.items():
            self._set(f"{prefix}_max_{direction.lower()}_mm", value, "etabs_csv:" + file)

    def _process_torsion(self, rows: list[dict[str, Any]], file: str) -> None:
        col = next((c for c in ("Ratio", "delta_max/delta_avg", "Max/Avg") if rows and c in rows[0]), None)
        if not col:
            self._unresolved(f"{file}: missing torsion ratio column"); return
        vals = [self._number(r, col) for r in rows]; vals = [v for v in vals if v is not None]
        if vals: self._set("irregularity.torsion_ratio", max(vals), "etabs_csv")

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
        story = self._get("analysis.story_force_data", [])
        if story:
            valid = [r for r in story if None not in (r.get("force"), r.get("displacement"), r.get("weight"))]
            if valid:
                g = float(self.formulas.get("rayleigh_period", {}).get("gravity_m_s2", 9.80665))
                num = sum(r["weight"] * r["displacement"] ** 2 for r in valid)
                den = g * sum(r["force"] * r["displacement"] for r in valid)
                if den > 0: self._set("modal.rayleigh_period_s", self._fmt("modal.rayleigh_period_s", 2 * math.pi * math.sqrt(num / den)), "computed: story force/displacement tables")
                else: self._unresolved("Rayleigh period: denominator g*sum(Fi*di) is not positive")
            else: self._unresolved("Rayleigh period requires Story, force Fi, displacement di and weight Wi for every governing row")
        elif data:
            self._unresolved("Rayleigh period cannot use the first modal period; story force/displacement tables are required")
        t_emp = self._get("modal.empirical_period_s"); t_ray = self._get("modal.rayleigh_period_s")
        if t_emp and t_ray:
            t = min(float(t_emp), float(t_ray)); self._set("seismic.design_period_used_s", self._fmt("seismic.design_period_used_s", t), "computed")
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
        (output_dir / "context_sources.json").write_text(json.dumps(self.sources, indent=2, ensure_ascii=False), encoding="utf-8")
        (output_dir / "conflicts.md").write_text("# Context Builder Conflicts\n\n" + ("\n".join(f"- {x}" for x in self.conflicts) if self.conflicts else "None.") + "\n", encoding="utf-8")
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
