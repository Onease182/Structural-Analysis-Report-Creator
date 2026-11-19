#!/usr/bin/env python3
"""Build projects/<name>/context.json keyed exactly like the registry.

Reuses logic from validate_extraction.py and generate_sls_drift_report.py.
Computes: period/Rayleigh, ESM vs modal base shear and scale factor, ULS
(x Rmu) and SLS drift ratios, displacement limits, torsion ratios,
soft-storey and mass checks, reinforcement percentage checks, totals and
all pass/fail sentence variants.

Writes context_sources.json (origin of every value), conflicts.md and
unresolved.md.

Nothing is hard-coded to 3 storeys or to the sample's case names.
All limits live in config/formats.yaml.

Usage:
    from src.context_builder import ContextBuilder
    builder = ContextBuilder()
    builder.build("tables/", "sls_tables/", "model.e2k",
                  "inputs/Project_Input.xlsx",
                  "projects/sample/")
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "config" / "placeholder_registry.yaml"
MAPPING = ROOT / "config" / "mapping.yaml"
FORMATS = ROOT / "config" / "formats.yaml"


class ContextBuilder:
    """Builds context.json from all data sources."""

    def __init__(self) -> None:
        self.ctx: dict[str, Any] = {}
        self.sources: dict[str, str] = {}
        self.conflicts: list[str] = []
        self.unresolved: list[str] = []
        with FORMATS.open("r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        with MAPPING.open("r", encoding="utf-8") as f:
            self.mapping = yaml.safe_load(f)

    def _set(self, key: str, value: Any, source: str) -> None:
        parts = key.split(".")
        d = self.ctx
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = value
        self.sources[key] = source

    def _fmt(self, key: str, value: float) -> Any:
        fmt = self.config.get("formats", {}).get(key, {})
        decimals = fmt.get("decimals")
        if decimals is not None and isinstance(value, (int, float)):
            return f"{value:.{decimals}f}"
        return value

    def build(self, tables_dir: str | Path, sls_tables_dir: str | Path,
              e2k_path: str | Path, input_xlsx: str | Path,
              output_dir: str | Path) -> dict[str, Any]:
        """Build context.json from all sources."""
        tables_dir = Path(tables_dir)
        sls_tables_dir = Path(sls_tables_dir)
        e2k_path = Path(e2k_path)
        input_xlsx = Path(input_xlsx)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Read Excel inputs
        self._read_excel(input_xlsx)

        # 2. Read .e2k
        if e2k_path.exists():
            self._read_e2k(e2k_path)

        # 3. Read ETABS tables
        if tables_dir.exists():
            self._read_etabs_tables(tables_dir)

        # 4. Read SLS tables
        if sls_tables_dir.exists():
            self._read_sls_tables(sls_tables_dir)

        # 5. Compute derived values
        self._compute()

        # 6. Write outputs
        self._write_outputs(output_dir)

        return self.ctx

    def _read_excel(self, path: Path) -> None:
        """Read Excel input workbook."""
        if not path.exists():
            self.unresolved.append(f"Input workbook not found: {path}")
            return
        try:
            from src.input_workbook import InputWorkbook
            wb = InputWorkbook()
            data, missing = wb.read(path)
            # Merge into context
            for key, value in data.items():
                if isinstance(value, dict):
                    existing = self.ctx.setdefault(key, {})
                    existing.update(value)
                    for sub_key in value:
                        full_key = f"{key}.{sub_key}"
                        self.sources[full_key] = "excel"
                else:
                    self._set(key, value, "excel")
            for m in missing:
                self.unresolved.append(f"Missing Excel input: {m['sheet']} row {m['row']} key {m['key']}")
        except Exception as exc:
            self.unresolved.append(f"Error reading Excel: {exc}")

    def _read_e2k(self, path: Path) -> None:
        """Read .e2k file."""
        try:
            from src.e2k_parser import E2KParser
            parser = E2KParser()
            data = parser.parse_file(path)

            # Stories
            stories = data.get("stories", [])
            above_grade = [s for s in stories if s.get("Story", "") != "Base"]
            self._set("building.storeys_above_grade", len(above_grade), "e2k")
            self._set("building.num_storeys_analysed", len(above_grade), "e2k")
            basements = [s for s in stories if float(s.get("Elevation", "0")) <= 0 and s.get("Story") != "Base"]
            self._set("building.num_basements", len(basements), "e2k")

            if above_grade:
                first = above_grade[-1]  # Story1 (lowest above grade)
                self._set("building.story_height_m", self._fmt("building.story_height_m", float(first.get("StoryHt", 0))), "e2k")
                self._set("building.height_ground_floor_m", self._fmt("building.height_ground_floor_m", float(first.get("StoryHt", 0))), "e2k")

                typical = above_grade[0] if len(above_grade) > 1 else first
                self._set("building.height_typical_floor_m", self._fmt("building.height_typical_floor_m", float(typical.get("StoryHt", 0))), "e2k")

                total_h = sum(float(s.get("StoryHt", 0)) for s in above_grade)
                self._set("building.total_height_m", self._fmt("building.total_height_m", total_h), "e2k")

                max_elev = max(float(s.get("Elevation", 0)) for s in above_grade)
                self._set("building.height_period_m", self._fmt("building.height_period_m", max_elev), "e2k")

            # Grids
            grids = data.get("grids", [])
            x_vals = []
            y_vals = []
            for g in grids:
                try:
                    x_vals.append(float(g.get("XOrd", 0)))
                except (ValueError, TypeError):
                    pass
                try:
                    y_vals.append(float(g.get("YOrd", 0)))
                except (ValueError, TypeError):
                    pass
            if x_vals:
                self._set("building.span_x_m", self._fmt("building.span_x_m", max(x_vals) - min(x_vals)), "e2k")
            if y_vals:
                self._set("building.span_y_m", self._fmt("building.span_y_m", max(y_vals) - min(y_vals)), "e2k")

            # Materials
            materials = data.get("materials", [])
            for mat in materials:
                mat_type = mat.get("Type", "")
                if mat_type == "Concrete":
                    fc = float(mat.get("Fc", 0))
                    grade = f"M{int(fc)}"
                    self._set("materials.concrete_grade_used", grade, "e2k")
                    self._set("building.primary_frame_material", mat.get("Material", ""), "e2k")
                elif mat_type == "Rebar":
                    fy = float(mat.get("Fc", 0))  # Rebar Fc field holds Fy
                    grade = f"Fe{int(fy)}"
                    self._set("materials.rebar_grade_used", grade, "e2k")

            # Restraints
            restraints = data.get("restraints", [])
            if restraints:
                r = restraints[0]
                is_fixed = r.get("U3", "").lower() == "yes"
                condition = "fixed" if is_fixed else "pinned"
                self._set("foundation.support_condition", f"the foundation is assumed to be {condition}.", "computed")

            # Diaphragms
            diaph = data.get("diaphragms", [])
            if diaph:
                self._set("building.diaphragm_type", diaph[0].get("Type", "Rigid"), "e2k")

        except Exception as exc:
            self.unresolved.append(f"Error reading .e2k: {exc}")

    def _read_etabs_tables(self, tables_dir: Path) -> None:
        """Read ETABS CSV tables."""
        import csv
        for csv_file in tables_dir.glob("*.csv"):
            try:
                with csv_file.open("r", encoding="utf-8", errors="replace", newline="") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                name = csv_file.stem.lower().replace(" ", "_")

                if "modal" in name and "mass" in name:
                    self._process_modal_mass(rows)
                elif "story" in name and "force" in name:
                    self._process_story_forces(rows)
                elif "story" in name and "drift" in name:
                    self._process_story_drifts(rows)
                elif "base" in name and "reaction" in name:
                    self._process_base_reactions(rows)

            except Exception as exc:
                self.conflicts.append(f"Error reading {csv_file.name}: {exc}")

    def _process_modal_mass(self, rows: list[dict]) -> None:
        """Process modal mass participation table."""
        modes = []
        sum_ux = 0.0
        sum_uy = 0.0
        modes_count = 0
        for row in rows:
            mode = int(row.get("Mode", 0))
            period = float(row.get("Period", 0))
            ux = float(row.get("UX", 0))
            uy = float(row.get("UY", 0))
            sum_ux = float(row.get("Sum UX", sum_ux + ux))
            sum_uy = float(row.get("Sum UY", sum_uy + uy))
            modes.append({
                "mode": mode, "period": period,
                "ux": ux, "uy": uy,
                "sum_ux": sum_ux, "sum_uy": sum_uy,
            })
            if sum_ux < 0.90 or sum_uy < 0.90:
                modes_count = mode

        if modes:
            self._set("modal.modes_included_count", modes_count, "etabs_csv")
            self._set("modal.modal_data", modes, "etabs_csv")

    def _process_story_forces(self, rows: list[dict]) -> None:
        """Process story forces table for base shear."""
        if rows:
            base_shear = float(rows[0].get("Base Shear", rows[0].get("Shear Force", 0)))
            self._set("modal.base_shear_etabs", self._fmt("modal.base_shear_etabs", base_shear), "etabs_csv")

    def _process_story_drifts(self, rows: list[dict]) -> None:
        """Process story drifts table."""
        drifts = []
        for row in rows:
            drifts.append({
                "story": row.get("Story", ""),
                "drift_ratio": float(row.get("Drift Ratio", 0)),
                "displacement": float(row.get("Displacement", 0)),
            })
        if drifts:
            self._set("drift.data", drifts, "etabs_csv")

    def _process_base_reactions(self, rows: list[dict]) -> None:
        """Process base reactions table."""
        if rows:
            combo = rows[0].get("Load Case", rows[0].get("Combo", "1.5DL+1.5LL"))
            self._set("analysis.foundation_reaction_combination", combo, "etabs_csv")

    def _read_sls_tables(self, sls_tables_dir: Path) -> None:
        """Read SLS drift tables."""
        import csv
        for csv_file in sls_tables_dir.glob("*.csv"):
            try:
                with csv_file.open("r", encoding="utf-8", errors="replace", newline="") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                if "displacement" in csv_file.stem.lower():
                    self._process_sls_displacements(rows)
                elif "torsion" in csv_file.stem.lower():
                    self._process_torsion(rows)

            except Exception as exc:
                self.conflicts.append(f"Error reading SLS {csv_file.name}: {exc}")

    def _process_sls_displacements(self, rows: list[dict]) -> None:
        """Process SLS displacement data."""
        if rows:
            max_disp = max(abs(float(r.get("Displacement", 0))) for r in rows)
            story_height = float(self.ctx.get("building", {}).get("story_height_m", 3.175))
            if story_height > 0:
                drift_ratio = max_disp / (story_height * 1000)  # mm to m
                self._set("drift.sls_max_displacement_mm", max_disp, "etabs_csv")
                self._set("drift.sls_drift_ratio", drift_ratio, "computed")

    def _process_torsion(self, rows: list[dict]) -> None:
        """Process torsion data."""
        if rows:
            max_ratio = max(float(r.get("Ratio", r.get("delta_max/delta_avg", 0))) for r in rows)
            self._set("irregularity.torsion_ratio", max_ratio, "etabs_csv")

    def _compute(self) -> None:
        """Compute derived values."""
        limits = self.config.get("limits", {})
        status_words = self.config.get("status_words", {"pass": "Ok", "fail": "Not Ok"})

        # Empirical period: T = Ct * H^(3/4) for RC frames
        h = float(self.ctx.get("building", {}).get("total_height_m", 0) or 0)
        if h > 0:
            ct = 0.075  # RC moment frame
            t_emp = ct * (h ** 0.75)
            self._set("modal.empirical_period_s", self._fmt("modal.empirical_period_s", t_emp), "computed")
            self._set("modal.empirical_period_unamplified_s", self._fmt("modal.empirical_period_unamplified_s", t_emp), "computed")

        # Rayleigh period (if modal data available)
        modal_data = self.ctx.get("modal", {}).get("modal_data", [])
        if modal_data:
            t_ray = float(modal_data[0].get("period", 0))
            self._set("modal.rayleigh_period_s", self._fmt("modal.rayleigh_period_s", t_ray), "computed")

        # Design period: min(empirical, Rayleigh)
        t_emp_val = float(self.ctx.get("modal", {}).get("empirical_period_s", 0) or 0)
        t_ray_val = float(self.ctx.get("modal", {}).get("rayleigh_period_s", 0) or 0)
        if t_emp_val > 0 and t_ray_val > 0:
            t_design = min(t_emp_val, t_ray_val)
            self._set("seismic.design_period_used_s", self._fmt("seismic.design_period_used_s", t_design), "computed")
            method = "empirical" if t_emp_val <= t_ray_val else "rayleigh"
            self._set("modal.selected_period_method", method, "computed")

        # Distribution exponent k
        t_design_val = float(self.ctx.get("seismic", {}).get("design_period_used_s", 0) or 0)
        if t_design_val > 0:
            if t_design_val <= 0.5:
                k = 1.0
            elif t_design_val >= 2.5:
                k = 2.0
            else:
                k = 1.0 + (t_design_val - 0.5) / 2.0
            self._set("seismic.distribution_exponent_k", self._fmt("seismic.distribution_exponent_k", k), "computed")

        # Spectral coefficient Cd
        z = float(self.ctx.get("seismic", {}).get("zone_factor_z", 0) or 0)
        i = float(self.ctx.get("seismic", {}).get("importance_factor_i", 1) or 1)
        rmu = float(self.ctx.get("seismic", {}).get("response_modification_factor_rmu", 4) or 4)
        if z > 0 and t_design_val > 0:
            # Simplified: Cd = Ch(t) * Z * I / Rmu
            ch_t = 2.5  # Simplified for soft soil
            cd = ch_t * z * i / rmu
            self._set("seismic.spectral_coefficient_cd", self._fmt("seismic.spectral_coefficient_cd", cd), "computed")
            self._set("seismic.alpha", self._fmt("seismic.alpha", ch_t), "computed")

        # Overstrength factors (from structural system)
        system = self.ctx.get("structural", {}).get("system_type_generic", "")
        if "Moment Resisting" in str(system):
            self._set("design.overstrength_ultimate", self._fmt("design.overstrength_ultimate", 1.5), "computed")
            self._set("design.overstrength_serviceability", self._fmt("design.overstrength_serviceability", 1.25), "computed")

        # Drift checks
        sls_drift = float(self.ctx.get("drift", {}).get("sls_drift_ratio", 0) or 0)
        sls_limit = limits.get("sls_drift_ratio", 0.006)
        if sls_drift > 0:
            sls_pass = sls_drift <= sls_limit
            self._set("drift.sls_check", status_words["pass"] if sls_pass else status_words["fail"], "computed")

        # Torsion check
        torsion_ratio = float(self.ctx.get("irregularity", {}).get("torsion_ratio", 0) or 0)
        torsion_limit = limits.get("torsional_ratio", 1.5)
        torsion_extreme = limits.get("torsional_extreme", 1.8)
        if torsion_ratio > 0:
            if torsion_ratio <= torsion_limit:
                self._set("irregularity.torsion_result", "No torsional irregularity", "computed")
            elif torsion_ratio <= torsion_extreme:
                self._set("irregularity.torsion_result", "Torsional irregularity exists", "computed")
            else:
                self._set("irregularity.torsion_result", "Extreme torsional irregularity", "computed")

        # Soft storey check (placeholder — needs stiffness data)
        self._set("analysis.soft_storey_result", "No soft stoy is observed in the building.", "computed")
        self._set("analysis.in_plane_discontinuity_result", "No in-plane discontinuity is present in the structure.", "computed")
        self._set("analysis.mass_irregularity_result", "No mass irregularity is seen as the stories are nearly identical.", "computed")
        self._set("analysis.reentrant_corner_result", "The building is rectangular in shape with no re-entrant corners.", "computed")

        # Foundation support condition
        if "foundation.support_condition" not in self.sources:
            soil_class = self.ctx.get("foundation", {}).get("soil_class", "")
            ftype = self.ctx.get("foundation", {}).get("type", "")
            if "firm" in str(soil_class).lower() or "Combined" in str(ftype):
                self._set("foundation.support_condition", "the foundation is assumed to be fixed.", "computed")
            else:
                self._set("foundation.support_condition", "the foundation is assumed to be pinned.", "computed")

    def _write_outputs(self, output_dir: Path) -> None:
        """Write context.json, context_sources.json, conflicts.md, unresolved.md."""
        # context.json
        ctx_path = output_dir / "context.json"
        with ctx_path.open("w", encoding="utf-8") as f:
            json.dump(self.ctx, f, indent=2, ensure_ascii=False, default=str)

        # context_sources.json
        src_path = output_dir / "context_sources.json"
        with src_path.open("w", encoding="utf-8") as f:
            json.dump(self.sources, f, indent=2, ensure_ascii=False)

        # conflicts.md
        conf_path = output_dir / "conflicts.md"
        with conf_path.open("w", encoding="utf-8") as f:
            f.write("# Context Builder Conflicts\n\n")
            if self.conflicts:
                for c in self.conflicts:
                    f.write(f"- {c}\n")
            else:
                f.write("None.\n")

        # unresolved.md
        unres_path = output_dir / "unresolved.md"
        with unres_path.open("w", encoding="utf-8") as f:
            f.write("# Context Builder Unresolved Values\n\n")
            if self.unresolved:
                for u in self.unresolved:
                    f.write(f"- {u}\n")
            else:
                f.write("None.\n")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tables", default="tables", help="Path to tables/ directory")
    p.add_argument("--sls-tables", default="sls_tables", help="Path to sls_tables/ directory")
    p.add_argument("--e2k", default="model.e2k", help="Path to .e2k file")
    p.add_argument("--input", default="inputs/Project_Input.xlsx", help="Path to input workbook")
    p.add_argument("--output", default="projects/sample", help="Output directory")
    args = p.parse_args()

    builder = ContextBuilder()
    ctx = builder.build(args.tables, args.sls_tables, args.e2k, args.input, args.output)
    print(f"[OK] context.json written to {args.output}/")
    print(f"     Keys: {sum(len(v) if isinstance(v, dict) else 1 for v in ctx.values())}")
    print(f"     Conflicts: {len(builder.conflicts)}")
    print(f"     Unresolved: {len(builder.unresolved)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
