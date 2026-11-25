#!/usr/bin/env python3
"""Generate auditable evidence from the committed ETABS exports and tables."""
from __future__ import annotations

import csv
import json
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


def mismatch(lines, section, key, source, expected, actual):
    if not same(expected, actual):
        lines.append(f"- `{section}` `{key}`: e2k={expected!r}; CSV={actual!r} ({source})")


def reconciliation(uls):
    mismatches = []
    stories = {r.get("Story"): r for r in uls.get("stories", [])}
    for r in rows(ROOT / "tables" / "12_Story_Definitions.csv"):
        story = r.get("Story")
        if story not in stories:
            mismatches.append(f"- `stories` `{story}`: e2k row missing; CSV height={r.get('Height')!r}")
            continue
        e2k_mm = num(stories[story].get("StoryHt"))
        csv_m = num(r.get("Height"))
        if e2k_mm is None or csv_m is None or abs(e2k_mm / 1000 - csv_m) > 1e-9:
            mismatches.append(f"- `stories` `{story}` height: e2k={stories[story].get('StoryHt')!r} mm; CSV={r.get('Height')!r} m")
    csv_sections = {r.get("Name"): r for r in rows(ROOT / "tables" / "22b_Frame_Sect_Rect.csv")}
    e2k_sections = {r.get("Section"): r for r in uls.get("frame_sections", [])}
    for name, r in csv_sections.items():
        e = e2k_sections.get(name)
        if not e:
            mismatches.append(f"- `frame_sections` `{name}`: e2k definition missing; CSV row present")
            continue
        for field, ekey, ckey in (("t2", "t2", "t2"), ("t3", "t3", "t3"), ("Material", "Material", "Material")):
            mismatch(mismatches, "frame_sections", f"{name}.{field}", "22b_Frame_Sect_Rect.csv", e.get(ekey), r.get(ckey))
    csv_materials = {r.get("Material"): r for r in rows(ROOT / "tables" / "21_Materials.csv")}
    for name, e in {r.get("Material"): r for r in uls.get("materials", [])}.items():
        c = csv_materials.get(name)
        if not c:
            mismatches.append(f"- `materials` `{name}`: e2k material present; CSV row missing")
            continue
        strength = e.get("Fc") or e.get("Fy")
        expected_grade = (f"M{int(float(strength))}" if e.get("Fc") else
                          ("HYSD" + str(int(float(strength))) if name.upper().startswith("HYSD") else strength))
        mismatch(mismatches, "materials", f"{name}.grade", "21_Materials.csv", expected_grade, c.get("Grade"))
    e_mass = uls.get("mass_source", [])
    c_mass = rows(ROOT / "tables" / "28_Mass_Source.csv")
    if len(e_mass) != len(c_mass):
        mismatches.append(f"- `mass_source` row count: e2k={len(e_mass)}; CSV={len(c_mass)}")
    for i, (e, c) in enumerate(zip(e_mass, c_mass)):
        for field in ("Name", "SourceSelf", "SourceAdded", "SourceLoads", "LoadPattern", "Multiplier"):
            mismatch(mismatches, "mass_source", f"row[{i}].{field}", "28_Mass_Source.csv", e.get(field) or e.get(field.upper()), c.get(field))
    return mismatches


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


def md_list(title, intro, values):
    body = "\n".join(values) if values else "- None; computed comparison found no differences."
    return f"# {title}\n\n{intro}\n\n{body}\n"


def main() -> int:
    out = ROOT / "docs"; out.mkdir(exist_ok=True)
    up, sp = E2KParser(), E2KParser()
    uls, sls = up.parse_file(ULS), sp.parse_file(SLS)
    rec = reconciliation(uls)
    (out / "e2k_csv_reconciliation.md").write_text(md_list("E2K/CSV Reconciliation", "Computed from real ULS e2k and ETABS CSV rows. Every checked story, frame section, material, and mass-source field is compared; ULS is authoritative.", rec), encoding="utf-8")
    diffs = model_differences(uls, sls)
    (out / "model_consistency.md").write_text(md_list("ULS/SLS Model Comparison", "Computed from parsed real ULS and SLS e2k records. Every difference is listed by parsed section; SLS remains restricted to serviceability use.", diffs), encoding="utf-8")
    workbook = ROOT / "tables" / "etabs_tables.xlsx"
    if workbook.exists():
        temp = ROOT / ".evidence_context"
        if temp.exists():
            shutil.rmtree(temp)
        ContextBuilder().build(ROOT / "tables", ROOT / "sls_tables", ULS, workbook, temp)
        for name in ("context_sources.json", "unresolved.md", "conflicts.md"):
            shutil.copy2(temp / name, out / name)
        shutil.rmtree(temp)
    else:
        (out / "context_sources.json").write_text(json.dumps({"source_priority": ["etabs_csv", "e2k", "excel", "computed"], "values": {}}, indent=2) + "\n", encoding="utf-8")
        (out / "unresolved.md").write_text("# Context Builder Unresolved Values\n\n- UNRESOLVED: input workbook not found\n", encoding="utf-8")
        (out / "conflicts.md").write_text("# Context Builder Conflicts\n\n- UNRESOLVED: context builder was not run because input workbook was missing\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
