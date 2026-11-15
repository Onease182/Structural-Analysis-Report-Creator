"""
etabs_extract_sls_drifts.py

Extract everything needed for the NBC 105:2025 serviceability (SLS) inter-storey
drift check, the ULS/SLS displacement + drift criteria table and the torsional
irregularity check from the ETABS model that is currently open, and write it to a
dedicated CSV package (default: ./sls_tables).

Check basis (as supplied by the responsible engineer)
-----------------------------------------------------
  * Drifts are read directly from the ETABS load cases EQX-SLS and EQY-SLS after
    the analysis has been run.
  * Limit: 0.006 inter-storey drift ratio (clause 5.5.3).
  * Unmultiplied (elastic) deflections are used (clause 5.5.1.2): this script
    never scales, amplifies or reduces any ETABS result.
  * Worst corner / edge point on each floor governs; the 5 % accidental
    eccentricity variants are part of the SLS cases, so every step of the case
    is extracted and the envelope is taken later by the report generator.
  * The optional kd = 0.94 reduction of clause 6.5 is NOT applied.
  * The ULS cases (default EQX-ULS / EQY-ULS) are extracted the same way, unscaled, for the
    displacement / drift criteria table and the torsional irregularity check (cl. 5.4.2.2).
    If they are not found in the model the SLS extraction still completes (with a warning).

Run (ETABS open with the model, saved to disk):
    python etabs_extract_sls_drifts.py
    python etabs_extract_sls_drifts.py --case-x EQX-SLS --case-y EQY-SLS --out sls_tables
    python etabs_extract_sls_drifts.py --uls-x EQX-ULS --uls-y EQY-ULS     # ULS case names
    python etabs_extract_sls_drifts.py --no-uls                            # SLS only

Requires: pip install comtypes pandas openpyxl

Outputs in the output folder
----------------------------
  S01_Story_Drifts.csv         ETABS "Story Drifts" (SLS + ULS cases, all steps)
  S02_Joint_Drifts.csv         ETABS "Joint Drifts" (SLS + ULS cases, all joints/steps)
  S03_Story_Definitions.csv
  S04_Modal_Periods.csv        S05_Modal_Mass_Ratios.csv
  S06_Base_Reactions.csv       S07_Story_Forces.csv
  S08_Load_Patterns.csv        S09_Load_Cases.csv        S10_Mass_Source.csv
  S11_Centers_Mass_Rigid.csv
  S12_Joint_Coordinates.csv    (UniqueName, GlobalX/Y/Z in metres)
  S13_Joint_Displacements.csv  ETABS "Joint Displacements" (SLS + ULS cases, metres)
  S14_Story_Max_Avg_Displacements.csv   ETABS "Story Max Over Avg Displacements" (SLS + ULS)
  sls_extraction_manifest.json (model, units, case status, row counts, warnings)
  sls_tables.xlsx              (all tables in one workbook)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime

import pandas as pd

try:
    import comtypes.client
except ImportError:  # allows --help / syntax checks on machines without ETABS
    comtypes = None

UNITS_ENUM = 6  # kN-m-C; the user's present units are restored afterwards

TABLES = {
    "S01_Story_Drifts":      ["Story Drifts"],
    "S02_Joint_Drifts":      ["Joint Drifts"],
    "S03_Story_Definitions": ["Story Definitions", "Story Data"],
    "S04_Modal_Periods":     ["Modal Periods and Frequencies"],
    "S05_Modal_Mass_Ratios": ["Modal Participating Mass Ratios"],
    "S06_Base_Reactions":    ["Base Reactions"],
    "S07_Story_Forces":      ["Story Forces"],
    "S08_Load_Patterns":     ["Load Pattern Definitions", "Load Patterns"],
    "S09_Load_Cases":        ["Load Case Definitions", "Load Cases"],
    "S10_Mass_Source":       ["Mass Source Definitions", "Mass Source"],
    "S11_Centers_Mass_Rigid": ["Centers of Mass and Rigidity"],
    "S13_Joint_Displacements": ["Joint Displacements"],
    "S14_Story_Max_Avg_Displacements": ["Story Max Over Avg Displacements", "Story Max/Avg Displacements"],
}
# Tables whose rows must be restricted to the SLS / ULS cases.
CASE_FILTERED = {"S01_Story_Drifts", "S02_Joint_Drifts", "S06_Base_Reactions", "S07_Story_Forces",
                 "S13_Joint_Displacements", "S14_Story_Max_Avg_Displacements"}
CASE_COLUMNS = ["OutputCase", "Case", "LoadCase", "Output Case", "Load Case"]
# The drift tables are the heart of the check; extraction fails loudly without them.
CRITICAL = {"S01_Story_Drifts"}


def parse_args() -> argparse.Namespace:
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--case-x", default="EQX-SLS", help="SLS load case for the X direction")
    p.add_argument("--case-y", default="EQY-SLS", help="SLS load case for the Y direction")
    p.add_argument("--uls-x", default="EQX-ULS", help="ULS load case for the X direction")
    p.add_argument("--uls-y", default="EQY-ULS", help="ULS load case for the Y direction")
    p.add_argument("--no-uls", action="store_true", help="skip the ULS cases (SLS drift check only)")
    p.add_argument("--out", default=os.path.join(here, "sls_tables"), help="output folder")
    p.add_argument("--force-reanalysis", action="store_true",
                   help="re-run the analysis even if ETABS reports the model as already analysed")
    p.add_argument("--no-analysis", action="store_true",
                   help="never run the analysis (fail if the SLS cases have no results)")
    return p.parse_args()


# ----------------------------------------------------------------------------
# ETABS helpers
# ----------------------------------------------------------------------------
def connect():
    if comtypes is None:
        sys.exit("comtypes is not installed: pip install comtypes")
    try:
        etabs = comtypes.client.GetActiveObject("CSI.ETABS.API.ETABSObject")
    except Exception as exc:
        sys.exit(f"Could not attach to ETABS. Open the model first. ({exc})")
    return etabs.SapModel


def resolve_cases(model, wanted: dict[str, str], required: bool = True) -> dict[str, str]:
    """Map direction -> exact ETABS case name (case-insensitive match).
    Aborts if a case is absent and `required`; otherwise warns and returns only the cases found."""
    names = list(model.LoadCases.GetNameList()[1] or [])
    lower = {n.lower(): n for n in names}
    found, missing = {}, []
    for direction, name in wanted.items():
        if name.lower() in lower:
            found[direction] = lower[name.lower()]
        else:
            missing.append(name)
    if missing:
        hints = [n for n in names if "sls" in n.lower() or "uls" in n.lower() or "eq" in n.lower()]
        msg = (f"Load case(s) not found in the model: {missing}\n"
               f"Cases containing 'SLS'/'ULS'/'EQ': {hints or 'none'}\nAll cases: {names}")
        if required:
            sys.exit(msg)
        print("[WARN]", msg)
    return found


def case_status(model, names) -> dict[str, int]:
    """ETABS run status per case: 1 not run, 2 could not start, 3 not finished, 4 finished."""
    try:
        r = model.Analyze.GetCaseStatus(0, [], [])
        return {c: int(s) for c, s in zip(list(r[1]), list(r[2])) if c in names}
    except Exception as exc:
        print(f"[WARN] could not read case status: {exc}")
        return {}


def ensure_analysis(model, run_cases: list[str], force: bool, forbid: bool) -> tuple[bool, dict]:
    status = case_status(model, run_cases)
    done = bool(status) and all(v == 4 for v in status.values())
    need = force or not model.GetModelIsLocked() or (status and not done)
    ran = False
    if need:
        if forbid:
            sys.exit("The requested cases have no finished results and --no-analysis was given.")
        for name in run_cases:                      # make sure the requested cases are flagged to run
            try:
                model.Analyze.SetRunCaseFlag(name, True, False)
            except Exception as exc:
                print(f"[WARN] SetRunCaseFlag({name}) failed: {exc}")
        print("Running analysis ...")
        ret = model.Analyze.RunAnalysis()
        if ret not in (0, None):
            sys.exit(f"RunAnalysis returned {ret}. Check the model for errors/warnings.")
        ran = True
        status = case_status(model, run_cases)
    unfinished = {k: v for k, v in status.items() if v != 4}
    if unfinished:
        print(f"[WARN] cases not reported as finished: {unfinished}")
    return ran, status


def select_outputs(model, run_cases: list[str]) -> None:
    """Restrict table output to the SLS + ULS cases (+ modal) so tables stay small and unambiguous."""
    db = model.DatabaseTables
    all_cases = list(model.LoadCases.GetNameList()[1] or [])
    modal = [c for c in all_cases if "modal" in c.lower()]
    db.SetLoadCasesSelectedForDisplay(sorted(set(run_cases + modal)))
    for setter in (db.SetLoadPatternsSelectedForDisplay, db.SetLoadCombinationsSelectedForDisplay):
        try:
            setter([])
        except Exception:
            pass  # some builds reject an empty list; extra rows are filtered out later anyway


def available_tables(db) -> dict[str, str]:
    r = db.GetAvailableTables()
    return dict(zip(list(r[2]), list(r[1])))      # {table_name: table_key}


def find_key(name_to_key: dict[str, str], candidates: list[str]):
    lower = {n.lower(): k for n, k in name_to_key.items()}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()], c
    for c in candidates:                           # design tables etc. carry suffixes
        for n, k in name_to_key.items():
            if n.lower().startswith(c.lower()):
                return k, n
    return None, None


def fetch(db, table_key: str):
    """DataFrame for one ETABS table, or None when empty. Indexing from the end keeps this
    correct whether or not comtypes echoes the FieldKeyList argument."""
    r = db.GetTableForDisplayArray(table_key, [""], "All", 0, [], 0, [])
    ret = r[-1]
    fields, nrec, data = list(r[-4]), r[-3], list(r[-2])
    if ret != 0 or nrec == 0 or not fields:
        return None
    n = len(fields)
    df = pd.DataFrame([data[i * n:(i + 1) * n] for i in range(nrec)], columns=fields)
    for c in df.columns:
        try:
            df[c] = pd.to_numeric(df[c])
        except (ValueError, TypeError):
            pass
    return df


def filter_cases(df: pd.DataFrame, wanted: list[str]):
    col = next((c for c in CASE_COLUMNS if c in df.columns), None)
    if col is None:
        return df, None, []
    available = sorted(df[col].astype(str).unique())
    mask = df[col].astype(str).str.lower().isin([w.lower() for w in wanted])
    return df[mask].reset_index(drop=True), col, available


def _sid(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def joint_coordinates(model, joint_drifts: pd.DataFrame | None, name_to_key, db):
    """Coordinates for every joint that appears in the Joint Drifts table.

    The API point names are what the Joint Drifts 'UniqueName' column refers to, so the API
    is used first; the 'Objects and Elements - Joints' table is the fallback."""
    if joint_drifts is not None and "UniqueName" in joint_drifts.columns:
        rows = []
        for name in sorted({_sid(v) for v in joint_drifts["UniqueName"]}):
            try:
                r = model.PointObj.GetCoordCartesian(name, 0.0, 0.0, 0.0)
            except Exception:
                continue
            if r[-1] == 0:
                rows.append({"UniqueName": name, "GlobalX": r[0], "GlobalY": r[1], "GlobalZ": r[2]})
        if rows:
            return pd.DataFrame(rows), "api"
    key, _ = find_key(name_to_key, ["Objects and Elements - Joints"])
    df = fetch(db, key) if key else None
    if df is not None:
        norm = {re.sub(r"[^a-z0-9]", "", c.lower()): c for c in df.columns}
        pick = lambda *ns: next((norm[n] for n in ns if n in norm), None)
        u, x, y, z = pick("uniquename", "name", "label"), pick("globalx", "x"), pick("globaly", "y"), pick("globalz", "z")
        if None not in (u, x, y, z):
            out = pd.DataFrame({"UniqueName": df[u].map(_sid), "GlobalX": df[x], "GlobalY": df[y], "GlobalZ": df[z]})
            return out.drop_duplicates("UniqueName"), "table"
    return None, "unavailable"


# ----------------------------------------------------------------------------
def main() -> int:
    cfg = parse_args()
    out_dir = os.path.abspath(cfg.out)
    os.makedirs(out_dir, exist_ok=True)
    for stale in os.listdir(out_dir):              # never mix files from different runs
        if re.match(r"S\d\d_.*\.csv$", stale) or stale in ("sls_tables.xlsx", "sls_extraction_manifest.json"):
            os.remove(os.path.join(out_dir, stale))

    model = connect()
    model_filename = model.GetModelFilename()
    print("Model:", model_filename)
    try:
        etabs_version = str(model.GetVersion()[0])
    except Exception:
        etabs_version = None

    warnings: list[str] = []
    cases = resolve_cases(model, {"X": cfg.case_x, "Y": cfg.case_y})
    sls_cases = list(cases.values())
    print("SLS cases:", cases)
    uls_map: dict[str, str] = {}
    if not cfg.no_uls:
        uls_map = resolve_cases(model, {"X": cfg.uls_x, "Y": cfg.uls_y}, required=False)
        if len(uls_map) < 2:
            warnings.append(f"ULS case(s) not found ({cfg.uls_x}, {cfg.uls_y}); the displacement/drift criteria "
                            "and torsional irregularity tables cannot be fully produced. Use --uls-x / --uls-y.")
        print("ULS cases:", uls_map or "none")
    uls_cases = list(uls_map.values())
    all_cases = sls_cases + uls_cases
    analysis_ran, status = ensure_analysis(model, all_cases, cfg.force_reanalysis, cfg.no_analysis)

    original_units = model.GetPresentUnits()
    model.SetPresentUnits(UNITS_ENUM)
    results: dict[str, pd.DataFrame] = {}
    manifest_tables: dict[str, dict] = {}
    coord_source = "unavailable"
    try:
        db = model.DatabaseTables
        select_outputs(model, all_cases)
        name_to_key = available_tables(db)
        pd.DataFrame({"table_name": list(name_to_key)}).to_csv(
            os.path.join(out_dir, "available_tables.csv"), index=False)

        for sheet, candidates in TABLES.items():
            key, used = find_key(name_to_key, candidates)
            if key is None:
                print(f"[MISSING] {sheet}: none of {candidates} offered by this ETABS version")
                manifest_tables[sheet] = {"status": "missing", "candidates": candidates}
                continue
            df = fetch(db, key)
            if df is None:
                print(f"[EMPTY]   {sheet} ({used})")
                manifest_tables[sheet] = {"status": "empty", "etabs_table_name": used}
                continue
            filt = None
            if sheet in CASE_FILTERED:
                df, col, available = filter_cases(df, all_cases)
                filt = {"column": col, "requested": all_cases, "available_in_table": available}
                if df.empty:
                    print(f"[NO MATCH] {sheet}: {all_cases} not found. Cases in table: {available}")
                    manifest_tables[sheet] = {"status": "no_case_match", "etabs_table_name": used, "filter": filt}
                    continue
            results[sheet] = df
            df.to_csv(os.path.join(out_dir, f"{sheet}.csv"), index=False)
            print(f"[OK]      {sheet} ({used}): {len(df)} rows")
            manifest_tables[sheet] = {"status": "ok", "etabs_table_name": used, "rows": int(len(df)),
                                      "columns": list(df.columns), "filter": filt}

        coords, coord_source = joint_coordinates(model, results.get("S02_Joint_Drifts"), name_to_key, db)
        if coords is not None:
            results["S12_Joint_Coordinates"] = coords
            coords.to_csv(os.path.join(out_dir, "S12_Joint_Coordinates.csv"), index=False)
            print(f"[OK]      S12_Joint_Coordinates ({coord_source}): {len(coords)} joints")
    finally:
        model.SetPresentUnits(original_units)

    # ---- sanity checks the report relies on --------------------------------
    for sheet in CRITICAL:
        if sheet not in results:
            warnings.append(f"{sheet} could not be extracted; the drift check cannot be produced.")
    if "S02_Joint_Drifts" not in results:
        warnings.append("Joint Drifts table unavailable: the worst corner/edge point cannot be identified "
                        "independently; the report will fall back to the ETABS Story Drifts table.")
    if coord_source == "unavailable":
        warnings.append("Joint coordinates unavailable: corner/edge classification will not be possible.")
    if uls_cases and "S14_Story_Max_Avg_Displacements" not in results and "S13_Joint_Displacements" not in results:
        warnings.append("Neither the Story Max Over Avg Displacements nor the Joint Displacements table could be "
                        "extracted: displacements and the torsional ratio cannot be produced.")
    elif uls_cases and "S14_Story_Max_Avg_Displacements" not in results:
        warnings.append("Story Max Over Avg Displacements unavailable: the report will compute the torsional ratio "
                        "from Joint Displacements (average = mean of the two extreme-point displacements).")
    sd = results.get("S01_Story_Drifts")
    if sd is not None and "StepNumber" in sd.columns:
        steps = sd.groupby(next(c for c in CASE_COLUMNS if c in sd.columns))["StepNumber"].nunique()
        for case, n in steps.items():
            if n < 2:
                warnings.append(f"{case}: only {n} step found in Story Drifts; confirm the 5 % eccentricity "
                                "variants are included in the case.")
    for w in warnings:
        print("[WARN]", w)

    if results:
        with pd.ExcelWriter(os.path.join(out_dir, "sls_tables.xlsx"), engine="openpyxl") as xw:
            for sheet, df in results.items():
                df.to_excel(xw, sheet_name=sheet[:31], index=False)

    manifest = {
        "extraction_timestamp": datetime.now().astimezone().isoformat(),
        "model_filename": model_filename,
        "etabs_version": etabs_version,
        "present_units_enum": UNITS_ENUM,
        "analysis_ran": analysis_ran,
        "sls_cases": cases,
        "uls_cases": uls_map,
        "sls_case_status": {k: v for k, v in status.items() if k in sls_cases},   # 4 = finished
        "uls_case_status": {k: v for k, v in status.items() if k in uls_cases},
        "joint_coordinate_source": coord_source,
        "scaling_applied": "none (unmultiplied ETABS results; kd not applied)",
        "warnings": warnings,
        "tables": manifest_tables,
    }
    with open(os.path.join(out_dir, "sls_extraction_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # ---- quick console look at the answer ----------------------------------
    jd = results.get("S02_Joint_Drifts")
    if jd is not None and {"Story", "DriftX", "DriftY"}.issubset(jd.columns):
        print("\n--- Max |drift| per story (all joints, all steps) ---")
        for d, case in cases.items():
            sub = jd[jd[next(c for c in CASE_COLUMNS if c in jd.columns)].astype(str).str.lower() == case.lower()]
            print(case, sub.groupby("Story")[f"Drift{d}"].apply(lambda s: s.abs().max()).round(6).to_dict())
    sm = results.get("S14_Story_Max_Avg_Displacements")
    if sm is not None and {"Maximum", "Story"}.issubset(sm.columns):
        cc = next((c for c in CASE_COLUMNS if c in sm.columns), None)
        if cc:
            print("\n--- Max story displacement per case (mm, all stories/steps) ---")
            for case, g in sm.groupby(cc):
                print(case, round(float(pd.to_numeric(g["Maximum"], errors="coerce").abs().max()) * 1000, 4))
    print(f"\nSaved to: {out_dir}")
    print("Next: python generate_sls_drift_report.py --tables", out_dir)
    return 1 if any("cannot be produced" in w for w in warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
