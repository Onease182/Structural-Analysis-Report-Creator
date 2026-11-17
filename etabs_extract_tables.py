"""
etabs_extract_tables.py
Pull the tables needed for the NBC 105:2025 report from the ETABS model that is
currently open, and save them to one Excel workbook (plus a CSV per table).

Run:   python etabs_extract_tables.py
Needs: pip install comtypes pandas openpyxl

EDIT THE CONFIG BLOCK BELOW to match your load case / combination names.

ULS drift / displacement / torsion package (used by generate_sls_drift_report.py)
--------------------------------------------------------------------------------
Run this script FIRST with the ULS-stiffness model open (beams 0.35, columns 0.70, Table 3-1).
Besides the report tables it writes, for the ULS_CHECK_CASES only (unscaled, metres):
    04_Story_Drifts.csv                   ETABS Story Drifts
    31_Joint_Drifts.csv                   ETABS Joint Drifts (every joint, every step)
    32_Joint_Displacements.csv            ETABS Joint Displacements
    33_Story_Max_Avg_Displacements.csv    ETABS Story Max Over Avg Displacements (torsion)
    14_Joint_Coordinates.csv              joint X/Y/Z (API point names)
Then open the SLS model and run etabs_extract_sls_drifts.py, then
    python generate_sls_drift_report.py --tables sls_tables --uls-tables tables
"""

import os
import sys
import json
from datetime import datetime
import comtypes.client
import pandas as pd

# ----------------------------------------------------------------------------
# CONFIG - edit these
# ----------------------------------------------------------------------------
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tables")   # "tables" folder next to this script
UNITS_ENUM = 6                                  # 6 = kN-m-C (restored afterwards)

SEISMIC_CASES = ["EQX-ULS", "EQY-ULS", "RSX-ULS", "RSY-ULS"]
# ESM cases that feed the ULS drift / displacement / torsion tables of the SLS-ULS report.
# Only these are written to 31 / 32 / 33 (keeps the per-joint tables small).
ULS_CHECK_CASES = ["EQX-ULS", "EQY-ULS"]
BASE_REACTION_CASES = SEISMIC_CASES + ["Dead", "Live", "DL + LL"]
# "Story Max Over Avg Displacements" (table 33) IS extracted now: the torsional irregularity
# check of the SLS-ULS report needs it.
REACTION_COMBO_KEYWORDS = [
    "DL + LL",
    "DL+LL",
    "ENV-ULS",
    "1.2DL+1.5LL",
    "0.9DL+EQX",
    "0.9DL+EQY",
    "1.2DL+0.3LL+EQX",
    "1.2DL+0.3LL+EQY",
]

RUN_ANALYSIS_IF_NEEDED = True        # run analysis if the model is not locked
RUN_DESIGN_IF_NEEDED = True          # run concrete design if design tables are empty
EXPORT_E2K = True                    # also write the model as an .e2k text file into OUT_DIR
# eFileTypeIO values to try, in order, until a valid .e2k comes out. The enum differs
# between ETABS releases, so every result is checked by reading the file header.
E2K_FILETYPE_CANDIDATES = [3, 2, 1]
USE_API_GEOMETRY_FALLBACK = True     # read joints/frames/areas through the ETABS API if the
                                     # connectivity tables are missing or unreadable

# Table keys as ETABS names them (version dependent). Edit if a table is reported missing.
TABLES = {
    "01_Modal_Periods":      ["Modal Periods and Frequencies"],
    "02_Modal_Mass_Ratios":  ["Modal Participating Mass Ratios"],
    "03_Base_Reactions":     ["Base Reactions"],
    "04_Story_Drifts":       ["Story Drifts"],
    "05_Story_Forces":       ["Story Forces"],
    "07_Column_Design":      ["Concrete Column Summary", "Concrete Column PMM Envelope"],
    "08_Beam_Design":        ["Concrete Beam Summary", "Concrete Beam Flexure Envelope"],
    # extra design tables: these carry the required reinforcement areas
    "07b_Column_PMM_Env":    ["Concrete Column PMM Envelope"],
    "07c_Column_Shear_Env":  ["Concrete Column Shear Envelope"],
    "08b_Beam_Flexure_Env":  ["Concrete Beam Flexure Envelope"],
    "08c_Beam_Shear_Env":    ["Concrete Beam Shear Envelope"],
    "09_Centers_Mass_Rigid": ["Centers of Mass and Rigidity"],
    "10_Story_Stiffness":    ["Story Stiffness"],
    "11_Joint_Reactions":    ["Joint Reactions"],

    # Model geometry and assignments.  ETABS table names vary by release;
    # find_key() tries the exact names first and then a starts-with match.
    "12_Story_Definitions":  ["Story Definitions", "Story Data"],
    "13_Grid_Definitions":   [
        "Grid Definitions - Grid Lines", "Grid Definitions - General"
    ],
    "14_Joint_Coordinates":  ["Objects and Elements - Joints"],
    "15_Frame_Connectivity": ["Beam Object Connectivity"],
    "15b_Column_Connectivity": ["Column Object Connectivity"],
    "15c_Brace_Connectivity": ["Brace Object Connectivity"],
    "16_Area_Connectivity":  ["Objects and Elements - Areas"],
    "16b_Floor_Connectivity": ["Floor Object Connectivity"],
    "16c_Wall_Connectivity": ["Wall Object Connectivity"],
    "17_Frame_Assignments":  [
        "Frame Assignments - Summary", "Frame Assignments - Section",
        "Frame Assignments"
    ],
    "18_Area_Assignments":   [
        "Area Assignments - Section", "Area Assignments"
    ],
    "19_Diaphragm_Assignments": [
        "Joint Assignments - Diaphragms", "Diaphragm Definitions"
    ],
    "20_Joint_Restraints":   [
        "Joint Assignments - Restraints", "Joint Restraint Assignments"
    ],

    # Materials and section properties/assignments.
    "21_Materials":          [
        "Material Properties 01 - General",
        "Material Properties - General",
        "Material Properties"
    ],
    "22_Frame_Sections":     [
        "Frame Section Property Definitions - Summary",
        "Frame Section Properties 01 - General",
        "Frame Section Properties - General",
        "Frame Section Assignments"
    ],
    # rectangular / circular dimensions, used to extrude members in the 3D figure
    "22b_Frame_Sect_Rect":   [
        "Frame Section Property Definitions - Concrete Rectangular"
    ],
    "22c_Frame_Sect_Circ":   [
        "Frame Section Property Definitions - Concrete Circular"
    ],
    "23_Area_Sections":      [
        "Area Section Property Definitions - Summary",
        "Area Section Properties 01 - General",
        "Area Section Properties - General",
        "Area Section Assignments"
    ],

    # Load definitions needed for the report's loading and combinations chapter.
    "24_Load_Patterns":      [
        "Load Pattern Definitions", "Load Patterns"
    ],
    "25_Load_Cases":         [
        "Load Case Definitions", "Load Cases"
    ],
    "26_Load_Combinations":  [
        "Load Combination Definitions", "Load Combinations"
    ],
    "27_Response_Spectrum":  [
        "Response Spectrum Functions",
        "Load Case Definitions - Response Spectrum",
        "Response Spectrum"
    ],
    "28_Mass_Source":        ["Mass Source Definitions", "Mass Source"],

    # ULS drift / displacement / torsion package (see docstring); fetched for ULS_CHECK_CASES only
    "31_Joint_Drifts":       ["Joint Drifts"],
    "32_Joint_Displacements": ["Joint Displacements"],
    "33_Story_Max_Avg_Displacements": [
        "Story Max Over Avg Displacements", "Story Max/Avg Displacements"
    ],
}
# tables fetched with the display selection narrowed to ULS_CHECK_CASES (huge otherwise)
NARROW_SELECTION_TABLES = {"31_Joint_Drifts", "32_Joint_Displacements", "33_Story_Max_Avg_Displacements"}

# which tables get filtered by case name, and how
CASE_FILTER = {
    "03_Base_Reactions": ("exact", BASE_REACTION_CASES),
    "04_Story_Drifts":   ("exact", SEISMIC_CASES),
    "05_Story_Forces":   ("exact", SEISMIC_CASES),
    "11_Joint_Reactions": ("contains", REACTION_COMBO_KEYWORDS),
    "31_Joint_Drifts":   ("exact", ULS_CHECK_CASES),
    "32_Joint_Displacements": ("exact", ULS_CHECK_CASES),
    "33_Story_Max_Avg_Displacements": ("exact", ULS_CHECK_CASES),
}
CASE_COLUMNS = ["OutputCase", "Case", "LoadCase", "Output Case", "Load Case"]


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def connect():
    try:
        etabs = comtypes.client.GetActiveObject("CSI.ETABS.API.ETABSObject")
    except Exception as e:
        sys.exit(f"Could not attach to ETABS. Open the model first. ({e})")
    return etabs.SapModel


def available_tables(db):
    """Return {table_name: table_key} for every table ETABS can show."""
    r = db.GetAvailableTables()
    # (NumberTables, TableKey[], TableName[], ImportType[], ret)
    keys, names = list(r[1]), list(r[2])
    return dict(zip(names, keys))


def save_available_table_diagnostic(name_to_key):
    """Save every table exposed by this ETABS installation for troubleshooting."""
    rows = [
        {"table_name": name, "table_key": key}
        for name, key in sorted(name_to_key.items(), key=lambda item: item[0].lower())
    ]
    pd.DataFrame(rows).to_csv(
        os.path.join(OUT_DIR, "available_tables.csv"), index=False
    )
    with open(os.path.join(OUT_DIR, "available_tables.txt"), "w", encoding="utf-8") as f:
        for row in rows:
            f.write(f"{row['table_name']}\t{row['table_key']}\n")


def select_all_outputs(model):
    db = model.DatabaseTables
    pats = model.LoadPatterns.GetNameList()[1]
    cases = model.LoadCases.GetNameList()[1]
    combos = model.RespCombo.GetNameList()[1]
    db.SetLoadPatternsSelectedForDisplay(list(pats))
    db.SetLoadCasesSelectedForDisplay(list(cases))
    db.SetLoadCombinationsSelectedForDisplay(list(combos))


def select_only_cases(model, wanted):
    """Show only the named load cases (no patterns, no combinations) in the database tables.
    Names are matched case-insensitively against the model; returns the exact names used."""
    db = model.DatabaseTables
    names = list(model.LoadCases.GetNameList()[1] or [])
    lower = {n.lower(): n for n in names}
    use = [lower[w.lower()] for w in wanted if w.lower() in lower]
    db.SetLoadCasesSelectedForDisplay(use)
    for setter in (db.SetLoadPatternsSelectedForDisplay, db.SetLoadCombinationsSelectedForDisplay):
        try:
            setter([])
        except Exception:
            pass          # some builds reject an empty list; unwanted rows are filtered out later
    return use


def fetch(db, table_key):
    """Return a DataFrame for one table, or None if ETABS has no data for it."""
    r = db.GetTableForDisplayArray(table_key, [""], "All", 0, [], 0, [])
    # comtypes returns every ByRef argument, so the tuple ends with
    # (..., TableVersion, FieldsKeysIncluded[], NumberRecords, TableData[], ret).
    # Counting from the end keeps this correct whether or not FieldKeyList is echoed.
    ret = r[-1]
    _version, fields, nrec, data = r[-5], list(r[-4]), r[-3], list(r[-2])
    if ret != 0 or nrec == 0 or not fields:
        return None
    n = len(fields)
    rows = [data[i * n:(i + 1) * n] for i in range(nrec)]
    df = pd.DataFrame(rows, columns=fields)
    for c in df.columns:                      # numbers where possible, text otherwise
        try:
            df[c] = pd.to_numeric(df[c])
        except (ValueError, TypeError):
            pass
    return df


def filter_cases(df, mode, wanted):
    col = next((c for c in CASE_COLUMNS if c in df.columns), None)
    if col is None:
        return df, None
    s = df[col].astype(str).str.lower()
    w = [x.lower() for x in wanted]
    if mode == "exact":
        mask = s.isin(w)
    else:
        mask = s.apply(lambda v: any(x in v for x in w))
    return df[mask].reset_index(drop=True), sorted(df[col].astype(str).unique())


def find_key(name_to_key, candidates):
    """Match a wanted table name against what this ETABS version offers."""
    lower = {n.lower(): k for n, k in name_to_key.items()}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()], c
    for c in candidates:                      # fall back to 'starts with' (design tables
        for n, k in name_to_key.items():      # carry the design code in the name)
            if n.lower().startswith(c.lower()):
                return k, n
    return None, None



def export_e2k(model, model_filename):
    """Export the open model to <OUT_DIR>/<model>.e2k and verify it is really an .e2k.

    Returns a manifest dict. The file is checked for the e2k section markers because a
    wrong FileType enum can silently write a different format under the .e2k name.
    """
    stem = os.path.splitext(os.path.basename(str(model_filename or "model")))[0] or "model"
    path = os.path.join(OUT_DIR, f"{stem}.e2k")
    attempts = []
    for ftype in E2K_FILETYPE_CANDIDATES:
        if os.path.exists(path):
            os.remove(path)
        try:
            ret = model.File.ExportFile(path, ftype)
            ret = ret[-1] if isinstance(ret, (tuple, list)) else ret
        except Exception as exc:
            attempts.append({"file_type": ftype, "result": f"exception: {exc}"})
            continue
        ok = False
        if ret == 0 and os.path.exists(path) and os.path.getsize(path) > 0:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    head = f.read(20000).upper()
                ok = "$ PROGRAM INFORMATION" in head or "$ CONTROLS" in head or "$ STORIES" in head
            except OSError:
                ok = False
        attempts.append({"file_type": ftype, "return_code": ret, "valid_e2k": ok})
        if ok:
            print(f"[E2K]     {path} ({os.path.getsize(path) / 1024:.0f} KB, FileType={ftype})")
            return {"status": "ok", "path": os.path.basename(path), "file_type_used": ftype,
                    "size_bytes": os.path.getsize(path), "attempts": attempts}
        if os.path.exists(path):
            os.remove(path)               # do not leave a wrong-format file behind
    print("[E2K]     export failed - use File > Export > ETABS .e2k Text File manually. "
          f"Attempts: {attempts}")
    return {"status": "failed", "attempts": attempts}

# ----------------------------------------------------------------------------
# Geometry package for the 3D figure (generate_etabs_figures.py)
#   14_Joint_Coordinates.csv  Joint, GlobalX, GlobalY, GlobalZ (+ Story/Label)
#   29_Frame_Members.csv      Frame, Type, JointI, JointJ, Story, Section, Width, Depth
#   30_Slab_Panels.csv        Area, Type, Story, Joint1 .. JointN
# ----------------------------------------------------------------------------
import re


def _norm(c):
    return re.sub(r"[^a-z0-9]", "", str(c).lower())


def _sid(v):
    """Stable string id: 12.0 -> '12', ' A1 ' -> 'A1', NaN -> ''."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _col(df, *names):
    """First column whose normalised name equals one of `names`."""
    m = {_norm(c): c for c in df.columns}
    for n in names:
        if _norm(n) in m:
            return m[_norm(n)]
    return None


def _end_col(df, *suffixes):
    """First column whose normalised name ends with a suffix; 'unique...' preferred."""
    cands = [c for c in df.columns if any(_norm(c).endswith(x) for x in suffixes)]
    cands.sort(key=lambda c: not _norm(c).startswith("unique"))
    return cands[0] if cands else None


def normalise_joints(df):
    if df is None:
        return None
    x, y, z = _col(df, "GlobalX", "X"), _col(df, "GlobalY", "Y"), _col(df, "GlobalZ", "Z")
    idc = _col(df, "UniqueName", "Joint", "Name", "Label")
    if None in (x, y, z, idc):
        return None
    out = pd.DataFrame({
        "Joint": df[idc].map(_sid),
        "GlobalX": pd.to_numeric(df[x], errors="coerce"),
        "GlobalY": pd.to_numeric(df[y], errors="coerce"),
        "GlobalZ": pd.to_numeric(df[z], errors="coerce"),
    })
    for extra in ("Story", "Label"):
        c = _col(df, extra)
        if c is not None:
            out[extra] = df[c].values
    return out.dropna(subset=["GlobalX", "GlobalY", "GlobalZ"]).drop_duplicates("Joint").reset_index(drop=True)


def frames_from_tables(results):
    rows = []
    for key, kind in (("15_Frame_Connectivity", "beam"), ("15b_Column_Connectivity", "column"),
                      ("15c_Brace_Connectivity", "brace")):
        df = results.get(key)
        if df is None:
            continue
        idc = _col(df, "UniqueName", "Name", "Frame", "Beam", "Column", "Brace", "Label")
        ci = _end_col(df, "pti", "jointi", "pointi")
        cj = _end_col(df, "ptj", "jointj", "pointj")
        if None in (idc, ci, cj):
            print(f"[WARN] {key}: cannot find frame id / I / J columns in {list(df.columns)}")
            continue
        stc = _col(df, "Story")
        for _, r in df.iterrows():
            rows.append({"Frame": _sid(r[idc]), "Type": kind, "JointI": _sid(r[ci]),
                         "JointJ": _sid(r[cj]), "Story": r[stc] if stc else ""})
    return pd.DataFrame(rows, columns=["Frame", "Type", "JointI", "JointJ", "Story"]) if rows else None


def areas_from_tables(results):
    rows = []
    for key, kind in (("16b_Floor_Connectivity", "floor"), ("16c_Wall_Connectivity", "wall")):
        df = results.get(key)
        if df is None:
            continue
        idc = _col(df, "UniqueName", "Name", "Floor", "Wall", "Label")
        pts = [c for c in df.columns if re.fullmatch(r"(unique)?(pt|point|joint)\d+", _norm(c))]
        pts.sort(key=lambda c: int(re.search(r"\d+", _norm(c)).group()))
        if idc is None or len(pts) < 3:
            print(f"[WARN] {key}: cannot find area id / point columns in {list(df.columns)}")
            continue
        stc = _col(df, "Story")
        for _, r in df.iterrows():
            p = [_sid(r[c]) for c in pts if _sid(r[c]) not in ("", "0")]
            if len(p) >= 3:
                rows.append({"Area": _sid(r[idc]), "Type": kind, "Story": r[stc] if stc else "",
                             **{f"Joint{i + 1}": v for i, v in enumerate(p)}})
    return pd.DataFrame(rows) if rows else None


def add_section_sizes(frames, results):
    """Add Section / Width / Depth to the frame table where the tables allow it."""
    frames["Section"], frames["Width"], frames["Depth"] = "", float("nan"), float("nan")
    asg = results.get("17_Frame_Assignments")
    if asg is None:
        return frames
    idc = _col(asg, "UniqueName", "Name", "Frame")
    sc = _col(asg, "AnalSect", "AnalysisSection", "Section", "DesignSect", "DesignSection")
    if idc is None or sc is None:
        return frames
    sec_of = {_sid(a): _sid(b) for a, b in zip(asg[idc], asg[sc])}
    dims = {}
    rect = results.get("22b_Frame_Sect_Rect")
    if rect is not None:
        n, t3, t2 = _col(rect, "Name"), _col(rect, "t3", "Depth"), _col(rect, "t2", "Width")
        if None not in (n, t3, t2):
            for a, d, w in zip(rect[n], rect[t3], rect[t2]):
                dims[_sid(a)] = (w, d)
    circ = results.get("22c_Frame_Sect_Circ")
    if circ is not None:
        n, dc = _col(circ, "Name"), _col(circ, "Diameter", "t3", "D")
        if None not in (n, dc):
            for a, d in zip(circ[n], circ[dc]):
                dims[_sid(a)] = (d, d)
    frames["Section"] = frames["Frame"].map(sec_of).fillna("")
    for i, sec in frames["Section"].items():
        if sec in dims:
            frames.loc[i, "Width"], frames.loc[i, "Depth"] = dims[sec]
    return frames


# --- ETABS API fallbacks (used only when the tables above are unavailable) ---
def api_joints(model):
    po = model.PointObj
    names = list(po.GetNameList()[1] or [])
    rows = []
    for n in names:
        r = po.GetCoordCartesian(n, 0.0, 0.0, 0.0)
        if r[-1] == 0:
            rows.append({"Joint": _sid(n), "GlobalX": r[0], "GlobalY": r[1], "GlobalZ": r[2]})
    return pd.DataFrame(rows) if rows else None


def api_frames(model, joints):
    fo = model.FrameObj
    names = list(fo.GetNameList()[1] or [])
    xyz = joints.set_index("Joint")[["GlobalX", "GlobalY", "GlobalZ"]]
    rows = []
    for n in names:
        p = fo.GetPoints(n, "", "")
        if p[-1] != 0:
            continue
        a, b = _sid(p[0]), _sid(p[1])
        if a not in xyz.index or b not in xyz.index:
            continue
        sec = fo.GetSection(n, "", "")
        pa, pb = xyz.loc[a], xyz.loc[b]
        horiz = ((pa.GlobalX - pb.GlobalX) ** 2 + (pa.GlobalY - pb.GlobalY) ** 2) ** .5
        kind = "column" if abs(pa.GlobalZ - pb.GlobalZ) > horiz else "beam"
        w = d = float("nan")
        try:
            rect = model.PropFrame.GetRectangle(sec[0], "", "", 0.0, 0.0, 0, "", "")
            if rect[-1] == 0:
                d, w = rect[2], rect[3]          # T3 = depth, T2 = width
        except Exception:
            pass
        rows.append({"Frame": _sid(n), "Type": kind, "JointI": a, "JointJ": b, "Story": "",
                     "Section": sec[0] if sec[-1] == 0 else "", "Width": w, "Depth": d})
    return pd.DataFrame(rows) if rows else None


def api_areas(model, joints):
    ao = model.AreaObj
    names = list(ao.GetNameList()[1] or [])
    known = set(joints["Joint"])
    z = joints.set_index("Joint")["GlobalZ"]
    rows = []
    for n in names:
        r = ao.GetPoints(n, 0, [])
        if r[-1] != 0:
            continue
        p = [_sid(x) for x in r[1]]
        if len(p) < 3 or not set(p) <= known:
            continue
        kind = "floor" if max(z[k] for k in p) - min(z[k] for k in p) < 1e-6 else "wall"
        rows.append({"Area": _sid(n), "Type": kind, "Story": "",
                     **{f"Joint{i + 1}": v for i, v in enumerate(p)}})
    return pd.DataFrame(rows) if rows else None


def refine_areas_with_api(model, areas):
    """Floor tables can truncate polygons; replace them with the full point list from the API."""
    ao, new = model.AreaObj, {}
    jcols = [c for c in areas.columns if c.startswith("Joint")]
    for i, name in areas["Area"].items():
        try:
            r = ao.GetPoints(name, 0, [])
        except Exception:
            break
        if r[-1] != 0:
            continue
        pts = [_sid(x) for x in r[1]]
        cur = [v for v in (_sid(areas.at[i, c]) for c in jcols) if v]
        if len(pts) >= 3 and pts != cur:
            new[i] = pts
    if not new:
        return areas, 0
    for k in range(1, max(len(p) for p in new.values()) + 1):   # add every column first
        if f"Joint{k}" not in areas.columns:
            areas[f"Joint{k}"] = ""
    jcols = [c for c in areas.columns if c.startswith("Joint")]
    for i, pts in new.items():
        for c in jcols:
            areas.at[i, c] = ""
        for k, p in enumerate(pts, start=1):
            areas.at[i, f"Joint{k}"] = p
    return areas, len(new)


def build_column_locations(model, results, manifest):
    """34_Column_Locations.csv: ETABS column label -> plan position (X, Y in m).

    generate_sls_drift_report.py matches these to the grid lines in 13_Grid_Definitions to name
    columns by grid ID (B5, A3, ...)."""
    frames, joints = results.get("29_Frame_Members"), results.get("14_Joint_Coordinates")
    if frames is None or joints is None or "Joint" not in joints.columns:
        print("[COLUMNS] no frame/joint geometry - 34_Column_Locations.csv not written")
        manifest["column_locations"] = {"status": "skipped"}
        return
    xyz = joints.set_index("Joint")
    rows = []
    for _, r in frames[frames["Type"] == "column"].iterrows():
        a = r["JointI"]
        if a not in xyz.index:
            continue
        label, story = "", ""
        try:
            res = model.FrameObj.GetLabelFromName(r["Frame"], "", "")
            if res[-1] == 0:
                label, story = res[0], res[1]
        except Exception:
            pass
        rows.append({"Label": label, "Story": story, "UniqueName": r["Frame"],
                     "X": float(xyz.at[a, "GlobalX"]), "Y": float(xyz.at[a, "GlobalY"])})
    if not rows:
        print("[COLUMNS] no columns found")
        manifest["column_locations"] = {"status": "empty"}
        return
    df = pd.DataFrame(rows)
    results["34_Column_Locations"] = df
    df.to_csv(os.path.join(OUT_DIR, "34_Column_Locations.csv"), index=False)
    unlabeled = int((df["Label"] == "").sum())
    print(f"[COLUMNS] {len(df)} columns located" + (f" ({unlabeled} without an ETABS label)" if unlabeled else ""))
    if "13_Grid_Definitions" not in results:
        print("[COLUMNS] WARNING 13_Grid_Definitions missing - columns cannot be named by grid ID")
    manifest["column_locations"] = {"status": "ok", "columns": int(len(df)), "unlabeled": unlabeled}


def build_geometry_package(model, results, manifest):
    """Write 14 / 29 / 30 so generate_etabs_figures.py can draw the extruded 3D view."""
    src = {}
    # The API point names are the ones the connectivity tables refer to, so they are
    # the source of truth.  The raw joint table can list extra rows with other ids.
    raw_joints = results.get("14_Joint_Coordinates")
    joints, src["joints"] = None, "api"
    if USE_API_GEOMETRY_FALLBACK:
        try:
            joints = api_joints(model)
        except Exception as exc:
            print(f"[GEOMETRY] API joint read failed: {exc}")
    if joints is None:
        joints = normalise_joints(raw_joints); src["joints"] = "table"
        if joints is None and raw_joints is not None:
            print(f"[GEOMETRY] joint table has no usable id/X/Y/Z columns: {list(raw_joints.columns)}")
    if joints is None:
        print("[GEOMETRY] no joint coordinates - 3D figure will not be possible")
        manifest["geometry_package"] = {"status": "failed", "reason": "no joints"}
        return
    results["14_Joint_Coordinates"] = joints

    frames = frames_from_tables(results)
    src["frames"] = "table"
    if frames is not None:
        frames = add_section_sizes(frames, results)
    elif USE_API_GEOMETRY_FALLBACK:
        frames = api_frames(model, joints); src["frames"] = "api"
    areas = areas_from_tables(results)
    src["areas"] = "table"
    if areas is not None and USE_API_GEOMETRY_FALLBACK:
        areas, n_fix = refine_areas_with_api(model, areas)
        if n_fix:
            src["areas"] = f"table (+{n_fix} polygons completed from API)"
    if areas is None and USE_API_GEOMETRY_FALLBACK:
        areas = api_areas(model, joints); src["areas"] = "api"

    # keep only members whose joints exist; classify beams/columns by geometry if needed
    known = set(joints["Joint"])
    if frames is not None:
        frames = frames[frames["JointI"].isin(known) & frames["JointJ"].isin(known)].reset_index(drop=True)
        xyz = joints.set_index("Joint")
        dz = (xyz.loc[frames["JointI"], "GlobalZ"].values - xyz.loc[frames["JointJ"], "GlobalZ"].values)
        dh = ((xyz.loc[frames["JointI"], "GlobalX"].values - xyz.loc[frames["JointJ"], "GlobalX"].values) ** 2 +
              (xyz.loc[frames["JointI"], "GlobalY"].values - xyz.loc[frames["JointJ"], "GlobalY"].values) ** 2) ** .5
        geo_kind = pd.Series(["column" if abs(a) > b else "beam" for a, b in zip(dz, dh)])
        frames["Type"] = frames["Type"].where(frames["Type"] == "brace", geo_kind)
        results["29_Frame_Members"] = frames
        frames.to_csv(os.path.join(OUT_DIR, "29_Frame_Members.csv"), index=False)
    if areas is not None:
        jc = [c for c in areas.columns if c.startswith("Joint")]
        areas = areas[areas[jc].apply(lambda r: all(v in known for v in r.dropna() if v != ""), axis=1)]
        results["30_Slab_Panels"] = areas.reset_index(drop=True)
        areas.to_csv(os.path.join(OUT_DIR, "30_Slab_Panels.csv"), index=False)
    joints.to_csv(os.path.join(OUT_DIR, "14_Joint_Coordinates.csv"), index=False)

    manifest["geometry_package"] = {
        "status": "ok", "sources": src,
        "joints": int(len(joints)),
        "frames": 0 if frames is None else int(len(frames)),
        "areas": 0 if areas is None else int(len(areas)),
        "sized_frames": 0 if frames is None else int(frames["Width"].notna().sum()),
    }
    print(f"[GEOMETRY] joints={len(joints)}  frames={0 if frames is None else len(frames)}  "
          f"areas={0 if areas is None else len(areas)}  source={src}")
    if frames is None:
        print("[GEOMETRY] WARNING no frame data - figures script will infer members from joints")


# ----------------------------------------------------------------------------
# Quick checks printed to the console
# ----------------------------------------------------------------------------
def modal_checks(periods, mass):
    print("\n--- MODAL CHECKS ---")
    if periods is not None and "Period" in periods.columns:
        p = periods.copy()
        print(f"Modes found: {len(p)}   T1 = {p['Period'].iloc[0]:.4f} s")
    if mass is not None:
        m = mass.copy()
        for i, row in m.iterrows():
            ux, uy, rz = row.get("UX", 0), row.get("UY", 0), row.get("RZ", 0)
            dom = max([("UX", ux), ("UY", uy), ("RZ", rz)], key=lambda t: t[1])[0]
            m.loc[i, "Dominant"] = {"UX": "Translation X", "UY": "Translation Y",
                                    "RZ": "Torsion"}[dom]
        cols = [c for c in ["Mode", "Period", "UX", "UY", "RZ", "SumUX", "SumUY",
                            "SumRZ", "Dominant"] if c in m.columns]
        print(m[cols].to_string(index=False))
        for s in ("SumUX", "SumUY"):
            if s in m.columns:
                hit = m[m[s] >= 0.90]
                msg = f"mode {int(hit['Mode'].iloc[0])}" if len(hit) else "NOT reached"
                print(f"90% check {s}: {msg}  (final = {m[s].iloc[-1]:.3f})")


def torsion_check(df):
    print("\n--- TORSION CHECK (max/avg and max/min) ---")
    if df is None or df.empty:
        print("no data")
        return
    cols = [c for c in df.columns]
    ratio_col = next((c for c in cols if c.lower() == "ratio"), None)
    if ratio_col:
        # ETABS 'Ratio' is Max/Avg.  Max/Min = Max / (2*Avg - Max)  =>  r/(2-r)
        r = pd.to_numeric(df[ratio_col], errors="coerce")
        df["Max/Min (derived)"] = r / (2 - r)
        worst = df.loc[df["Max/Min (derived)"].idxmax()]
        print(f"worst Max/Avg = {r.max():.3f}  ->  Max/Min = "
              f"{worst['Max/Min (derived)']:.3f}  "
              f"(limit 1.5 irregular, 2.5 not permitted)")
        print("note: Max/Min derived assuming Min = 2*Avg - Max (two-point avg).")


def uls_summary(results):
    """Console look at the ULS package (values are unscaled ETABS results; the report applies Rmu)."""
    print("\n--- ULS PACKAGE (unscaled) ---")
    sm = results.get("33_Story_Max_Avg_Displacements")
    cc = next((c for c in CASE_COLUMNS if sm is not None and c in sm.columns), None)
    if sm is not None and cc and "Maximum" in sm.columns:
        for case, g in sm.groupby(cc):
            mx = pd.to_numeric(g["Maximum"], errors="coerce").abs().max() * 1000
            print(f"{case}: max story displacement {mx:.4f} mm")
        torsion_check(sm.copy())
    else:
        print("33_Story_Max_Avg_Displacements not extracted: the report will compute torsion from table 32.")
    for key in ("31_Joint_Drifts", "32_Joint_Displacements"):
        print(f"{key}: {'ok, ' + str(len(results[key])) + ' rows' if key in results else 'NOT extracted'}")


# ----------------------------------------------------------------------------
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for stale in ("14_Joint_Coordinates.csv", "29_Frame_Members.csv", "30_Slab_Panels.csv", "34_Column_Locations.csv",
                  "31_Joint_Drifts.csv", "32_Joint_Displacements.csv", "33_Story_Max_Avg_Displacements.csv"):
        p = os.path.join(OUT_DIR, stale)          # never mix files from different runs
        if os.path.exists(p):
            os.remove(p)
    model = connect()
    model_filename = model.GetModelFilename()
    print("Model:", model_filename)
    model_cases = {c.lower() for c in (model.LoadCases.GetNameList()[1] or [])}
    missing_uls = [c for c in ULS_CHECK_CASES if c.lower() not in model_cases]
    if missing_uls:
        print(f"[WARN] ULS check case(s) not in this model: {missing_uls}. Tables 31-33 will be empty. "
              "Open the ULS model or edit ULS_CHECK_CASES.")

    analysis_ran = False
    if not model.GetModelIsLocked() and RUN_ANALYSIS_IF_NEEDED:
        print("Model not analysed - running analysis...")
        model.Analyze.RunAnalysis()
        analysis_ran = True

    original_units = model.GetPresentUnits()
    model.SetPresentUnits(UNITS_ENUM)
    results = {}
    geometry_manifest = {}
    e2k_manifest = {"status": "disabled"}
    design_ran = False
    table_manifest = {}
    available_table_count = 0
    try:
        if EXPORT_E2K:
            try:
                e2k_manifest = export_e2k(model, model_filename)
            except Exception as exc:
                print(f"[E2K]     failed: {exc}")
                e2k_manifest = {"status": "failed", "reason": str(exc)}
        db = model.DatabaseTables
        select_all_outputs(model)
        name_to_key = available_tables(db)
        available_table_count = len(name_to_key)
        save_available_table_diagnostic(name_to_key)

        design_ran = False
        for sheet, candidates in TABLES.items():
            key, used = find_key(name_to_key, candidates)

            # A design table may not be exposed until concrete design has been
            # run.  Run it once, refresh the table catalogue, and search again.
            if key is None and sheet.startswith(("07", "08")) \
                    and RUN_DESIGN_IF_NEEDED and not design_ran:
                print("Design tables unavailable - running concrete design...")
                model.DesignConcrete.StartDesign()
                design_ran = True
                select_all_outputs(model)
                name_to_key = available_tables(db)
                available_table_count = len(name_to_key)
                save_available_table_diagnostic(name_to_key)
                key, used = find_key(name_to_key, candidates)

            if key is None:
                print(f"[MISSING] {sheet}: none of {candidates} offered by this ETABS version")
                table_manifest[sheet] = {
                    "status": "missing",
                    "candidates": candidates,
                }
                continue
            if sheet in NARROW_SELECTION_TABLES:
                select_only_cases(model, ULS_CHECK_CASES)
                try:
                    df = fetch(db, key)
                finally:
                    select_all_outputs(model)
            else:
                df = fetch(db, key)

            if df is None and sheet.startswith(("07", "08")) \
                    and RUN_DESIGN_IF_NEEDED and not design_ran:
                print("Design tables empty - running concrete design...")
                model.DesignConcrete.StartDesign()
                design_ran = True
                select_all_outputs(model)
                df = fetch(db, key)

            if df is None:
                print(f"[EMPTY]   {sheet} ({used})")
                table_manifest[sheet] = {
                    "status": "empty",
                    "candidates": candidates,
                    "etabs_table_name": used,
                    "table_key": key,
                }
                continue

            filter_info = None
            if sheet in CASE_FILTER:
                mode, wanted = CASE_FILTER[sheet]
                df, available = filter_cases(df, mode, wanted)
                filter_info = {
                    "mode": mode,
                    "requested": wanted,
                    "available_in_table": available,
                }
                if df.empty:
                    print(f"[NO MATCH] {sheet}: none of {wanted} found. "
                          f"Case names in model: {available}")
                    table_manifest[sheet] = {
                        "status": "no_case_match",
                        "candidates": candidates,
                        "etabs_table_name": used,
                        "table_key": key,
                        "filter": filter_info,
                    }
                    continue

            results[sheet] = df
            suffix = "_raw" if sheet == "14_Joint_Coordinates" else ""
            df.to_csv(os.path.join(OUT_DIR, f"{sheet}{suffix}.csv"), index=False)
            print(f"[OK]      {sheet} ({used}): {len(df)} rows")
            table_manifest[sheet] = {
                "status": "ok",
                "candidates": candidates,
                "etabs_table_name": used,
                "table_key": key,
                "rows": int(len(df)),
                "columns": list(df.columns),
                "filter": filter_info,
            }

        # slab sections: keep every "Area Section Property Definitions - ..." table (rib/waffle data)
        for tname, tkey in sorted(name_to_key.items()):
            if tname.lower().startswith("area section property definitions") and tname not in \
                    {v.get("etabs_table_name") for v in table_manifest.values()}:
                df = fetch(db, tkey)
                if df is not None:
                    safe = "23x_" + re.sub(r"[^A-Za-z0-9]+", "_", tname)[:60].strip("_")
                    results[safe] = df
                    df.to_csv(os.path.join(OUT_DIR, f"{safe}.csv"), index=False)
                    print(f"[OK]      {safe} ({tname}): {len(df)} rows")

        # normalise geometry for the 3D figure (needs the model open, so inside try)
        geometry_manifest = {}
        try:
            build_geometry_package(model, results, geometry_manifest)
            build_column_locations(model, results, geometry_manifest)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            print(f"[GEOMETRY] failed: {exc}")
            geometry_manifest = {"status": "failed", "reason": str(exc)}
    finally:
        model.SetPresentUnits(original_units)

    if results:
        xlsx = os.path.join(OUT_DIR, "etabs_tables.xlsx")
        with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
            for sheet, df in results.items():
                df.to_excel(xw, sheet_name=sheet[:31], index=False)
        print("\nSaved:", xlsx)

    modal_checks(results.get("01_Modal_Periods"), results.get("02_Modal_Mass_Ratios"))
    uls_summary(results)

    manifest = {
        "extraction_timestamp": datetime.now().astimezone().isoformat(),
        "model_filename": model_filename,
        "present_units_enum": UNITS_ENUM,
        "analysis_ran": analysis_ran,
        "concrete_design_ran": design_ran,
        "available_table_count": available_table_count,
        "diagnostic_files": ["available_tables.csv", "available_tables.txt"],
        "configuration": {
            "seismic_cases": SEISMIC_CASES,
            "base_reaction_cases": BASE_REACTION_CASES,
            "reaction_combo_keywords": REACTION_COMBO_KEYWORDS,
            "uls_check_cases": ULS_CHECK_CASES,
            "uls_tables": ["04_Story_Drifts", "31_Joint_Drifts", "32_Joint_Displacements",
                           "33_Story_Max_Avg_Displacements", "14_Joint_Coordinates"],
        },
        "e2k_export": e2k_manifest,
        "geometry_package": geometry_manifest.get("geometry_package", geometry_manifest),
        "column_locations": geometry_manifest.get("column_locations"),
        "tables": table_manifest,
    }
    manifest_path = os.path.join(OUT_DIR, "extraction_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print("Saved:", manifest_path)


if __name__ == "__main__":
    main()