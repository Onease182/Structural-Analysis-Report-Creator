#!/usr/bin/env python3
"""Generate auditable evidence from the committed ETABS exports and tables."""
from __future__ import annotations

import csv
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.e2k_parser import E2KParser
from src.context_builder import ContextBuilder

ULS = ROOT / "tables" / "Chatra Bahadur Ramel_ULS.e2k"
SLS = ROOT / "sls_tables" / "Chatra Bahadur Ramel_SLS.e2k"


def rows(path: Path):
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def same(a, b, tol=1e-9):
    na, nb = num(a), num(b)
    return abs(na - nb) <= tol if na is not None and nb is not None else str(a).strip() == str(b).strip()


def mismatch(result, section, key, source, expected, actual):
    result["checked"] += 1
    if same(expected, actual):
        result["matches"] += 1
    else:
        result["mismatches"].append(f"- `{section}` `{key}`: e2k={expected!r}; CSV={actual!r} ({source})")


def reconciliation(uls, tables_dir=ROOT / "tables"):
    result = {"checked": 0, "matches": 0, "mismatches": [], "not_comparable": []}
    stories = {r.get("Story"): r for r in uls.get("stories", [])}
    for r in rows(tables_dir / "12_Story_Definitions.csv"):
        story = r.get("Story")
        if story not in stories:
            result["mismatches"].append(f"- `stories` `{story}`: e2k row missing; CSV height={r.get('Height')!r}")
            continue
        mismatch(result, "stories", f"{story}.height_m", "12_Story_Definitions.csv (e2k mm / 1000)", num(stories[story].get("StoryHt")) / 1000, num(r.get("Height")))
    csv_sections = {r.get("Name"): r for r in rows(tables_dir / "22b_Frame_Sect_Rect.csv")}
    e2k_sections = {r.get("Section"): r for r in uls.get("frame_sections", [])}
    for name, r in csv_sections.items():
        e = e2k_sections.get(name)
        if not e:
            result["mismatches"].append(f"- `frame_sections` `{name}`: e2k definition missing; CSV row present")
            continue
        for field, ekey, ckey in (("t2_m", "t2", "t2"), ("t3_m", "t3", "t3")):
            mismatch(result, "frame_sections", f"{name}.{field}", "22b_Frame_Sect_Rect.csv (e2k mm / 1000)", num(e.get(ekey)) / 1000, num(r.get(ckey)))
        mismatch(result, "frame_sections", f"{name}.material", "22b_Frame_Sect_Rect.csv", e.get("Material"), r.get("Material"))
    csv_materials = {r.get("Material"): r for r in rows(tables_dir / "21_Materials.csv")}
    for name, e in {r.get("Material"): r for r in uls.get("materials", [])}.items():
        c = csv_materials.get(name)
        if not c:
            result["mismatches"].append(f"- `materials` `{name}`: e2k material present; CSV row missing")
            continue
        typ = str(e.get("Type", "")).lower()
        if "concrete" in typ:
            result["checked"] += 1
            csv_fc = num(re.search(r"(\d+(?:\.\d+)?)", name).group(1)) if re.search(r"(\d+(?:\.\d+)?)", name) else None
            if same(e.get("Fc"), csv_fc) and name == c.get("Material"):
                result["matches"] += 1
            else:
                result["mismatches"].append(f"- `materials` `{name}`: concrete name/Fc e2k=({name!r}, {e.get('Fc')!r}); CSV=({c.get('Material')!r}, {csv_fc!r})")
        elif "steel" in typ:
            mismatch(result, "materials", f"{name}.grade", "21_Materials.csv", e.get("GRADE") or e.get("Grade"), c.get("Grade"))
            fy_col = next((x for x in ("Fy", "FY", "Yield") if x in c), None)
            if fy_col:
                mismatch(result, "materials", f"{name}.Fy", "21_Materials.csv", e.get("Fy"), c.get(fy_col))
            else:
                result["not_comparable"].append(f"steel `{name}` Fy: 21_Materials.csv has no Fy/Yield column")
    # Per-frame section and material references: raw e2k LINEASSIGN is keyed by
    # label/story; CSV 17 is keyed the same way and its section points to 22b.
    e2k_assign = {}
    for line in uls.get("raw_sections", {}).get("LINEASSIGNS", []):
        t = re.findall(r'"(?:[^"\\]|\\.)*"|\S+', line)
        if len(t) >= 6 and t[0].upper() == "LINEASSIGN":
            fields = dict(zip(t[3::2], t[4::2]))
            e2k_assign[(t[2].strip('"'), t[1].strip('"'))] = fields.get("SECTION", "").strip('"')
    for r in rows(tables_dir / "17_Frame_Assignments.csv"):
        key = (r.get("Story", ""), r.get("Label", "")); section = e2k_assign.get(key)
        if section is None:
            result["mismatches"].append(f"- `frame_assignments` `{key[0]}/{key[1]}`: e2k assignment missing")
            continue
        mismatch(result, "frame_assignments", f"{key[0]}/{key[1]}.section", "17_Frame_Assignments.csv", section, r.get("AnalysisSect"))
        e_section = e2k_sections.get(section, {})
        csv_section = csv_sections.get(r.get("AnalysisSect"), {})
        mismatch(result, "frame_assignments", f"{key[0]}/{key[1]}.material", "22b_Frame_Sect_Rect.csv", e_section.get("Material"), csv_section.get("Material"))
    # Mass source is positional in e2k MASSSOURCELOAD; compare only by pattern
    # and multiplier, never against unrelated CSV option-column names.
    e_mass = {}
    for line in uls.get("raw_sections", {}).get("MASSSOURCE", []):
        t = re.findall(r'"(?:[^"\\]|\\.)*"|\S+', line)
        if t and t[0].upper() == "MASSSOURCELOAD" and len(t) >= 4:
            e_mass[t[2].strip('"')] = num(t[3].strip('"'))
    c_mass = {r.get("LoadPattern", ""): num(r.get("Multiplier", "")) for r in rows(tables_dir / "28_Mass_Source.csv")}
    for pattern in sorted(set(e_mass) | set(c_mass)):
        mismatch(result, "mass_source", f"{pattern}.multiplier", "28_Mass_Source.csv (LoadPattern/Multiplier)", e_mass.get(pattern, "missing"), c_mass.get(pattern, "missing"))
    return result


def model_differences(uls, sls):
    sections = ["stories", "materials", "frame_sections", "slab_properties", "frame_modifiers", "load_patterns", "load_combinations", "controls", "concrete_sections", "point_assignments"]
    diffs = []
    for section in sections:
        a, b = uls.get(section, []), sls.get(section, [])
        def identity(r, i):
            return next((r.get(k) for k in ("Section", "Material", "Story", "Combo", "LoadPat", "Point", "_command") if r.get(k)), str(i))
        am = {identity(r, i): r for i, r in enumerate(a)}
        bm = {identity(r, i): r for i, r in enumerate(b)}
        for key in sorted(set(am) | set(bm)):
            if key not in am or key not in bm:
                diffs.append(f"- `{section}` `{key}`: ULS={'present' if key in am else 'missing'}; SLS={'present' if key in bm else 'missing'}")
                continue
            for field in sorted(set(am[key]) | set(bm[key])):
                if field == "_command":
                    continue
                if not same(am[key].get(field), bm[key].get(field)):
                    diffs.append(f"- `{section}` `{key}.{field}`: ULS={am[key].get(field)!r}; SLS={bm[key].get(field)!r}")
    for section in ("frame_object_loads", "shell_object_loads", "point_object_loads"):
        if uls.get(section) != sls.get(section):
            diffs.append(f"- `{section}`: ULS rows={len(uls.get(section, []))}; SLS rows={len(sls.get(section, []))}; records compared by full parsed row")
    return diffs


def seismic_comparison(uls, sls):
    def by_direction(data):
        out = {}
        for row in data.get("load_patterns", []):
            name = str(row.get("LoadPat", ""))
            if name.startswith("EQX") or name.startswith("EQY"):
                direction = name[2]
                if "SHEARCOEFF" in row:
                    out[direction] = row
        return out
    ur, sr = by_direction(uls), by_direction(sls)
    lines = []
    for direction in ("X", "Y"):
        u, s = ur.get(direction, {}), sr.get(direction, {})
        lines.append(f"- `EQ{direction}` user coefficient: ULS SHEARCOEFF={u.get('SHEARCOEFF', 'UNRESOLVED')}; SLS SHEARCOEFF={s.get('SHEARCOEFF', 'UNRESOLVED')}; ULS HEIGHTEXPONENT={u.get('HEIGHTEXPONENT', 'UNRESOLVED')}; SLS HEIGHTEXPONENT={s.get('HEIGHTEXPONENT', 'UNRESOLVED')}; ULS ECC={u.get('ECC', 'UNRESOLVED')}; SLS ECC={s.get('ECC', 'UNRESOLVED')}")
    # The configured C(T) is the constant branch for soil C.  The project
    # sample/config supplies Z, I and the serviceability Omega_s=1.25.
    import yaml
    spectrum = yaml.safe_load((ROOT / "config" / "nbc105_spectrum.yaml").read_text())
    sample = yaml.safe_load((ROOT / "config" / "sample_context.yaml").read_text())
    c_t = float(spectrum["soil_classes"]["C"]["constant_shape_factor"])
    seismic = sample.get("seismic", {})
    z = float(seismic["zone_factor_z"])
    importance = float(seismic["importance_factor_i"])
    omega_s = float(sample["design"]["overstrength_serviceability"])
    calculated = 0.20 * c_t * z * importance / omega_s
    lines.append(f"- Computed SLS coefficient: 0.20 * Ch={c_t:g} * Z={z:g} * I={importance:g} / Omega_s={omega_s:g} = {calculated:.5f}; ETABS SLS target=0.14000; difference={calculated - 0.14:+.5f}")
    return lines


def md_list(title, intro, values):
    body = "\n".join(values) if values else "- None; computed comparison found no differences."
    return f"# {title}\n\n{intro}\n\n{body}\n"


def main() -> int:
    out = ROOT / "docs"; out.mkdir(exist_ok=True)
    up, sp = E2KParser(), E2KParser()
    uls, sls = up.parse_file(ULS), sp.parse_file(SLS)
    rec = reconciliation(uls)
    rec_intro = ("Computed from real ULS e2k and ETABS CSV rows using keyed, like-for-like comparisons. "
                 f"Checked items: {rec['checked']}; matches: {rec['matches']}; real mismatches: {len(rec['mismatches'])}. "
                 "Dimensions are normalized to metres (e2k millimetres / 1000); mass source is compared by LoadPattern and Multiplier.")
    notes = [f"- Not comparable (not counted as mismatch): {x}" for x in rec["not_comparable"]]
    (out / "e2k_csv_reconciliation.md").write_text(md_list("E2K/CSV Reconciliation", rec_intro, rec["mismatches"] + notes), encoding="utf-8")
    diffs = model_differences(uls, sls)
    diffs.extend(seismic_comparison(uls, sls))
    (out / "model_consistency.md").write_text(md_list("ULS/SLS Model Comparison", "Computed from parsed real ULS and SLS e2k records. Every difference is listed by parsed section, including direction-keyed auto-seismic parameters; SLS remains restricted to serviceability use.", diffs), encoding="utf-8")
    workbook = ROOT / "inputs" / "Project_Input.xlsx"
    if workbook.exists():
        temp = ROOT / ".evidence_context"
        if temp.exists():
            shutil.rmtree(temp)
        ContextBuilder().build(ROOT / "tables", ROOT / "sls_tables", ULS, workbook, temp)
        for name in ("context_sources.json", "unresolved.md", "conflicts.md"):
            shutil.copy2(temp / name, out / name)
        shutil.rmtree(temp)
    else:
        temp = ROOT / ".evidence_context"
        if temp.exists():
            shutil.rmtree(temp)
        ContextBuilder().build(ROOT / "tables", ROOT / "sls_tables", ULS, workbook, temp)
        for name in ("context_sources.json", "unresolved.md", "conflicts.md"):
            shutil.copy2(temp / name, out / name)
        shutil.rmtree(temp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
