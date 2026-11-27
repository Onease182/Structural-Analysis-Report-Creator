"""
generate_sls_drift_report.py

Evaluate the NBC 105:2025 serviceability (SLS) inter-storey drift check from the CSV
package written by etabs_extract_sls_drifts.py and render a one-page JPG result sheet (plus results .csv/.json). It also renders two further
tables from the same package (ULS + SLS cases, taken unscaled from ETABS):
  * Displacement_Drift_Criteria.jpg      max story displacement and max inter-story drift, ULS and SLS
  * Torsional_Irregularity_Check.jpg     delta_max / delta_avg per direction on ULS cases, cl. 5.4.2.2

Check basis (as supplied by the responsible engineer)
  * Drifts come directly from ETABS cases EQX-SLS (X) and EQY-SLS (Y).
  * Limit 0.006 inter-storey drift ratio (clause 5.5.3).
  * Unmultiplied deflections (clause 5.5.1.2): no factor is applied to any ETABS result.
  * The worst corner or edge point on each floor governs; every step of the SLS cases
    (which carry the 5 % accidental-eccentricity variants) is enveloped.
  * Optional kd = 0.94 (clause 6.5, 3 storeys) is NOT applied. It is reported only as an
    informative sensitivity. Use --kd 0.94 to apply it to the compliance result.

  * ULS: cases EQX-ULS / EQY-ULS, ETABS deflections multiplied by Rmu (cl. 5.5.1.1, --uls-scale, default 4),
    optionally read from a second model with ULS stiffness (--uls-tables); drift limit 0.025, displacement limit 0.025 x H; SLS displacement limit
    0.006 x H. H = sum of the story heights. Torsional irregularity if delta_max/delta_avg > 1.5
    (extreme > 1.8). All of these are command-line options (see --help). No ULS factor is applied
    unless --uls-scale is given.

Usage
    pip install pandas matplotlib pillow
    python generate_sls_drift_report.py --tables sls_tables --output report/SLS_Drift_Check.jpg

    Outputs: SLS_Drift_Check.jpg, Displacement_Drift_Criteria.jpg, Torsional_Irregularity_Check.jpg,
    SLS_ULS_Check_Summary.pdf (the three images as a 3-page A4-landscape file; --summary-format tiff|both),
    SLS_Drift_Check.results.csv, SLS_Drift_Check.results.json (the JSON holds the full list of data checks).
    Column_Reinforcement_Details.jpg (+ .csv): provided column bars per floor, selected from the ETABS
    required steel (see "Column reinforcement" below). Not part of the 3-page drift summary.

Column reinforcement (4th image)
  * Source: Concrete Column PMM Envelope / Column Summary (07b_Column_PMM_Env or 07_Column_Design) in the
    ULS tables folder. For every column label and story the governing (maximum) required steel ratio over all
    stations and combinations is taken; required As = ratio x Ag, never below --col-min-steel (1.0 %, NBC 105:2025 cl. 4.2.2b).
  * Provided bars: the SMALLEST combination of the bar ladder (--col-ladder) whose area >= required As.
    Bar area = 3.14 d^2/4 truncated to whole mm2 (so 8-20 = 2512, 4-20+4-16 = 2059, 8-16 = 1607, 4-16+4-12 = 1256).
  * Ties: --tie-legs legs per direction (default 4). The smallest diameter of --tie-dias (8, 10, 12 mm; min 8 mm per
    NBC 105:2025 cl. 4.2.3c) that can be made sufficient for ALL columns within the ductile-detailing limits is used.
    Spacings are restricted to 75 / 100 / 125 / 150 mm (--tie-spacings); the NBC 105:2025 limits are applied first
    and the result is rounded down to an allowed value:
      - end zone (special confining reinforcement, cl. 4.3) spacing <= min(1/4 of the least column dimension, 8 x smallest
        longitudinal bar, 100 mm) per cl. 4.3b; Ash = 0.18 S h (fck/fy)(Ag/Acc - 1) per cl. 4.3c must be covered at
        that spacing (l0 = max(largest lateral dimension, 1/6 clear height, 450 mm) per cl. 4.3a is only printed in the
        console log);
      - mid zone spacing <= 1/2 least lateral dimension per cl. 4.2.3e (and <= 16 x smallest bar, <= 300 mm per IS 13920);
        and, when 07c_Column_Shear_Env has the required Av/s, <= Av provided / Av required per mm;
      - tie diameter >= 8 mm per cl. 4.2.3c (and >= 1/4 of the largest longitudinal bar).
  * Columns with the same size and identical bars on every floor are grouped in one row and numbered
    C1, C2, C3 ... by distinct size + reinforcement pattern. Section size is read from the section
    name ("Column 355 x 355") or from the section table. Above --col-max-steel (4 %, cl. 4.2.2c) the cell is flagged.
    Dimensional checks (cl. 4.2.1: min 300 mm, b/D > 0.45) and bar-count checks (cl. 4.2.2a: min 8 bars, d: min 12 mm)
    are emitted as warnings.
  * Designations are grid IDs (e.g. B5, A3): each column's plan position (34_Column_Locations.csv, written by
    etabs_extract_tables.py) is matched to the nearest grid line in each direction (13_Grid_Definitions); the
    alphabetic line ID comes first, then the numeric one. Columns not within --grid-tol of a grid intersection
    keep their ETABS label. --col-names "C3=D3" overrides any designation.
Beam reinforcement (5th image, Beam_Reinforcement_Details.jpg + .csv)
  * Source: Concrete Beam Flexure Envelope (08b_Beam_Flexure_Env, else 08_Beam_Design) and Concrete Beam Shear
    Envelope (08c_Beam_Shear_Env, stirrup steel VRebar) in the ULS tables folder. Per beam and story the required top
    and bottom steel is enveloped over all combinations, separately for the end zones (--beam-end-frac of the span
    at each end, from the station positions) and mid-span.
  * Bars are split into THROUGH (continuous along the whole beam, shown as '(through)(Th.)') and EXTRA (additional
    at the supports only, shown as '+(extra)(Ex.)'), matching the reference sheet style. The through bars meet the
    mid-span requirement plus the minimum steel 0.24 sqrt(fck)/fy x b x d (d = D - --beam-cover, NBC 105:2025 cl. 4.1.2b)
    and the rule that any section carries >= 25 %% of the larger support steel (cl. 4.1.2e). The through + extra total
    at each support meets the support requirement plus the rule that the bottom steel at the support >= 50 %% of the top
    steel there (cl. 4.1.2d). At least --beam-min-bars (default 3) bars each at top and bottom, each >= 12 mm (cl. 4.1.2a
    requires >= 2x12mm; 3 is a project preference). The through-bar ladder is filtered to combinations with at least
    --beam-min-bars bars. Each part is the smallest combination of --beam-ladder whose area covers its requirement.
    Cells are flagged above --beam-max-steel (2.5 %% of b x d, cl. 4.1.2c).
  * Stirrups: smallest diameter of --beam-tie-dias that works (min 8 mm, NBC 105:2025 cl. 4.1.3d); end zone (2d) spacing <= min(d/4,
    --beam-hoop-mult x smallest bar, 100 mm) per cl. 4.1.3g (default 8 x db); mid-span <= d/2 per cl. 4.1.3f; Av/s must cover the ETABS demand (end / mid) and the minimum 0.4 b / (0.87 fy);
    spacings restricted to --beam-tie-spacings (rounded to the NEAREST allowed value, e.g. 96 mm -> 100 mm, not 75 mm).
    Format '2L-8mm\u03c6 @ 100mm near joints, @ 150mm at mid-span'.
    Cantilever beams (--beam-cantilevers list) use the end-zone spacing throughout (no mid-span relaxation).
    A note 'All cantilever portions: 2L-XXmm\u03c6 @XXmm c/c' is shown at the bottom of the table if the cantilever
    needs a bigger bar or tighter spacing than the regular beams.
  * Beams are grouped PER FLOOR LEVEL: each floor gets its own set of beam types (B1, B2, ... on that floor). Beams
    on the same floor with the same size, through/extra bars and stirrups are one row. The 'Floor' column shows a single
    floor per row. Within each floor, beam types are ordered by LARGEST DEPTH FIRST (D descending, then b descending).
    Beams whose smaller cross-section dimension is below --beam-min-size (default 230 mm) are ignored.
    All panels share one design system (PANEL_W, DPI and the D_* / PILL colour tokens).
"""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_COLUMN_LADDER = "4-16+4-12,8-16,4-20+4-16,8-20,4-25+4-20,8-25"
DEFAULT_BEAM_LADDER = "3-12,2-16+1-12,3-16,2-20+1-16,3-20,2-20+2-16,4-20,5-20,6-20,3-25,4-25,5-25"

NAVY, BLUE, GREY = "17365D", "1F4E79", "404040"
LIGHT_BLUE, LIGHT_GREY, GREEN, YELLOW, RED = "D9EAF7", "F2F4F6", "E2F0D9", "FFF2CC", "FCE4D6"
FONT = "Arial"
STATUS_FILL = {"PASS": GREEN, "COMPLIANT": GREEN, "FAIL": RED, "NON-COMPLIANT": RED, "WARN": YELLOW, "INFO": LIGHT_BLUE}


# ----------------------------------------------------------------------------
# Arguments, small utilities
# ----------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tables", type=Path, default=Path("sls_tables"))
    p.add_argument("--output", type=Path, default=Path("report/SLS_Drift_Check.jpg"))
    p.add_argument("--case-x", default="EQX-SLS")
    p.add_argument("--case-y", default="EQY-SLS")
    p.add_argument("--limit", type=float, default=0.006, help="inter-storey drift ratio limit (cl. 5.5.3)")
    p.add_argument("--kd", type=float, default=1.0, help="kd applied to the compliance result (default 1.0 = not applied)")
    p.add_argument("--kd-info", type=float, default=0.94, help="kd used for the informative sensitivity only")
    p.add_argument("--uls-x", default="EQX-ULS", help="ULS load case, X direction")
    p.add_argument("--uls-y", default="EQY-ULS", help="ULS load case, Y direction")
    p.add_argument("--uls-limit", type=float, default=0.025, help="ULS inter-storey drift ratio limit")
    p.add_argument("--uls-disp-factor", type=float, default=0.025, help="ULS displacement limit = factor x H")
    p.add_argument("--sls-disp-factor", type=float, default=0.006, help="SLS displacement limit = factor x H")
    p.add_argument("--uls-scale", type=float, default=4.0,
                   help="ductility factor Rmu applied to ULS displacements and drifts (NBC 105:2025 cl. 5.5.1.1). "
                        "Default 4.0 = RC / steel moment frame (Table 5-2); set it to your system's Rmu")
    p.add_argument("--uls-tables", type=Path, default=None,
                   help="folder written by etabs_extract_tables.py from the ULS-stiffness model (Table 3-1: beams 0.35, "
                        "columns 0.70). Default: ./tables if it exists, else the --tables folder "
                        "(ULS then uses the same stiffness as SLS)")
    p.add_argument("--height", type=float, default=None, help="total building height H in metres (default: from story data)")
    p.add_argument("--torsion-limit", type=float, default=1.5, help="torsional irregularity if ratio exceeds this")
    p.add_argument("--torsion-extreme", type=float, default=1.8, help="extreme torsional irregularity above this")
    p.add_argument("--criteria-output", type=Path, default=None, help="default: Displacement_Drift_Criteria.jpg beside --output")
    p.add_argument("--torsion-output", type=Path, default=None, help="default: Torsional_Irregularity_Check.jpg beside --output")
    p.add_argument("--summary-output", type=Path, default=None, help="default: SLS_ULS_Check_Summary beside --output (extension set by --summary-format)")
    p.add_argument("--summary-format", choices=["pdf", "tiff", "both"], default="pdf", help="multi-page file holding the three images, one per page")
    p.add_argument("--no-columns", action="store_true", help="skip the column reinforcement details image")
    p.add_argument("--columns-output", type=Path, default=None, help="default: Column_Reinforcement_Details.jpg beside --output")
    p.add_argument("--col-ladder", default=DEFAULT_COLUMN_LADDER,
                   help="allowed bar combinations (n-dia[+n-dia]), comma separated; the smallest one that covers the required As is used")
    p.add_argument("--col-min-steel", type=float, default=1.0, help="minimum column steel, %% of gross area (NBC 105:2025 cl. 4.2.2b: 1.0 %%)")
    p.add_argument("--col-max-steel", type=float, default=4.0, help="maximum column steel, %% of gross area (NBC 105:2025 cl. 4.2.2c: 4.0 %%)")
    p.add_argument("--grid-tol", type=float, default=0.15, help="max distance (m) from a grid line to name a column by grid ID")
    p.add_argument("--no-grid-names", action="store_true", help="use ETABS labels instead of grid IDs")
    p.add_argument("--ties", default=None, help="override the Ties text (default: selected from the demand, see --tie-dias)")
    p.add_argument("--tie-dias", default="8,10,12", help="tie bar diameters tried in order; the first that is sufficient is used")
    p.add_argument("--tie-legs", type=int, default=4, help="tie legs counted in each direction (default 4 = outer square + inner diamond; 2 = single hoop)")
    p.add_argument("--tie-sp-end", type=float, default=100, help="PREFERRED tie spacing near joints (mm); reduced if the ductile limits or Ash require")
    p.add_argument("--tie-spacings", default="75,100,125,150",
                   help="ONLY spacings (mm) allowed for ties; limits are applied first, then the result is rounded down to one of these")
    p.add_argument("--tie-sp-mid", type=float, default=150, help="PREFERRED tie spacing at mid-height (mm); reduced if the limits or shear require")
    p.add_argument("--col-cover", type=float, default=40, help="clear cover to ties (mm)")
    p.add_argument("--fck", type=float, default=20, help="concrete cylinder strength (MPa) for the confinement check")
    p.add_argument("--fy-tie", type=float, default=500, help="tie steel yield strength (MPa)")
    p.add_argument("--no-beams", action="store_true", help="skip the beam reinforcement details image")
    p.add_argument("--no-plans", action="store_true", help="skip the beam and column layout plan images")
    p.add_argument("--beam-plan-output", type=Path, default=None, help="default: Beam_Layout_Plan.jpg beside --output")
    p.add_argument("--column-plan-output", type=Path, default=None, help="default: Column_Layout_Plan.jpg beside --output")
    p.add_argument("--beams-output", type=Path, default=None, help="default: Beam_Reinforcement_Details.jpg beside --output")
    p.add_argument("--beam-ladder", default=DEFAULT_BEAM_LADDER,
                   help="allowed beam bar combinations (n-dia[+n-dia]); the smallest one that covers the required As is used "
                        "(min. 3 bars per face via --beam-min-bars). Bars are split into THROUGH (continuous, meets mid-span req) and EXTRA (at supports only, "
                        "meets support req - through area), shown as '(through)(Th.)+(extra)(Ex.)'")
    p.add_argument("--beam-min-bars", type=int, default=3, help="minimum number of longitudinal bars per face (top and bottom); "
                        "through bars are filtered to combinations with at least this many bars (default 3)")
    p.add_argument("--beam-min-size", type=float, default=230, help="ignore beams whose smaller cross-section dimension is below this "
                        "value (mm); beams smaller than --beam-min-size x --beam-min-size are skipped (default 230)")
    p.add_argument("--beam-max-steel", type=float, default=2.5, help="maximum beam tension steel, %% of b x d (NBC 105:2025 cl. 4.1.2c: 2.5 %%)")
    p.add_argument("--beam-cover", type=float, default=30, help="distance from the extreme fibre to the bar centroid (mm), d = D - this "
                        "(default 30 = 25mm clear cover + half bar diameter; 50 was too conservative and made d/4 < 100)")
    p.add_argument("--fy-long", type=float, default=500, help="longitudinal steel yield strength (MPa), minimum-steel check")
    p.add_argument("--beam-legs", type=int, default=2, help="stirrup legs (default 2 = one closed hoop)")
    p.add_argument("--beam-tie-dias", default="8,10,12", help="stirrup diameters tried in order (min 8 mm per NBC 105:2025 cl. 4.1.3d)")
    p.add_argument("--beam-tie-spacings", default="75,100,125,150", help="ONLY spacings (mm) allowed for stirrups; limits are applied first, then rounded to the NEAREST allowed value")
    p.add_argument("--beam-hoop-mult", type=float, default=8.0, help="end-zone spacing <= this x smallest longitudinal bar (NBC 105:2025 cl. 4.1.3g: 8 x db)")
    p.add_argument("--beam-end-frac", type=float, default=0.25, help="fraction of the span at each end treated as the end zone")
    p.add_argument("--beam-ties", default=None, help="override the stirrup text")
    p.add_argument("--beam-names", default="", help='rename ETABS beam labels, e.g. "B12=B1-A"')
    p.add_argument("--beam-cantilevers", default="", help='comma-separated list of ETABS beam labels that are cantilevers '
                        '(or contain cantilever portions); their stirrup note gets "@XX c/c at all cantilever portion" appended')
    p.add_argument("--col-names", default="", help='rename ETABS labels to grid designations, e.g. "C3=D3,C4=E3"')
    p.add_argument("--hull-tol", type=float, default=0.01, help="tolerance (m) for corner/edge classification")
    p.add_argument("--context", type=Path, default=None, help="optional report_context.json")
    p.add_argument("--project", default=None)
    p.add_argument("--client", default=None)
    p.add_argument("--location", default=None)
    p.add_argument("--designer", default=None)
    p.add_argument("--checker", default=None)
    p.add_argument("--consultancy", default=None)
    p.add_argument("--address", default=None)
    p.add_argument("--revision", default="R0")
    return p.parse_args()


def norm(c: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(c).lower())


def col(df: pd.DataFrame | None, *names: str) -> str | None:
    if df is None:
        return None
    m = {norm(c): c for c in df.columns}
    return next((m[norm(n)] for n in names if norm(n) in m), None)


def sid(v: Any) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def f5(x: Any) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.5f}"


def pct(x: Any) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x * 100:.1f} %"


def num(x: Any, d: int = 3) -> str:
    try:
        v = float(x)
        return "n/a" if not math.isfinite(v) else f"{v:.{d}f}"
    except (TypeError, ValueError):
        return sid(x) or "n/a"


def read_first(folder: Path, *stems: str) -> pd.DataFrame | None:
    """First CSV that exists among the stems (etabs_extract_tables.py name first, then the S-name)."""
    for stem in stems:
        df = read_csv(folder, stem)
        if df is not None:
            return df
    return None


def read_csv(folder: Path, stem: str) -> pd.DataFrame | None:
    path = folder / f"{stem}.csv"
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


# ----------------------------------------------------------------------------
# Geometry: convex hull -> corner / edge / interior classification
# ----------------------------------------------------------------------------
def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower: list = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def dist_to_segment(p, a, b) -> float:
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def classify(p, hull, tol: float) -> str:
    if len(hull) < 3:
        return "Unknown"
    if any(math.hypot(p[0] - v[0], p[1] - v[1]) <= tol for v in hull):
        return "Corner"
    if any(dist_to_segment(p, hull[i], hull[(i + 1) % len(hull)]) <= tol for i in range(len(hull))):
        return "Edge"
    return "Interior"


# ----------------------------------------------------------------------------
# Data preparation
# ----------------------------------------------------------------------------
def step_label(df: pd.DataFrame) -> pd.Series:
    st, sn = col(df, "StepType"), col(df, "StepNumber")
    if st is None and sn is None:
        return pd.Series(["-"] * len(df), index=df.index)
    a = df[st].fillna("").astype(str).str.strip() if st else pd.Series([""] * len(df), index=df.index)
    b = df[sn].map(lambda v: "" if pd.isna(v) else sid(v)) if sn else pd.Series([""] * len(df), index=df.index)
    return (a + " " + b).str.strip().replace("", "-")


def tidy_joint_drifts(jd: pd.DataFrame | None, coords: pd.DataFrame | None, cases: dict[str, str]) -> pd.DataFrame:
    cols = ["Story", "Joint", "Label", "Case", "Dir", "Step", "Drift", "X", "Y", "Z"]
    if jd is None:
        return pd.DataFrame(columns=cols)
    cc, sc, lc, uc = col(jd, "OutputCase", "Case"), col(jd, "Story"), col(jd, "Label"), col(jd, "UniqueName")
    frames = []
    for d, case in cases.items():
        dc = col(jd, f"Drift{d}")
        if None in (cc, sc, dc):
            continue
        sub = jd[jd[cc].astype(str).str.lower() == case.lower()]
        if sub.empty:
            continue
        label = sub[lc].map(sid) if lc else sub[uc].map(sid)
        frames.append(pd.DataFrame({
            "Story": sub[sc].map(sid), "Joint": sub[uc].map(sid) if uc else label, "Label": label,
            "Case": case, "Dir": d, "Step": step_label(sub), "Drift": pd.to_numeric(sub[dc], errors="coerce").abs(),
        }))
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=cols)
    out = out.dropna(subset=["Drift"]) if not out.empty else out
    for c in ("X", "Y", "Z"):
        out[c] = float("nan")
    if coords is not None and not out.empty:
        uid, gx, gy, gz = col(coords, "UniqueName", "Joint"), col(coords, "GlobalX"), col(coords, "GlobalY"), col(coords, "GlobalZ")
        if None not in (uid, gx, gy, gz):
            m = {sid(u): (x, y, z) for u, x, y, z in zip(coords[uid], coords[gx], coords[gy], coords[gz])}
            out["X"] = out["Joint"].map(lambda j: m.get(j, (float("nan"),) * 3)[0])
            out["Y"] = out["Joint"].map(lambda j: m.get(j, (float("nan"),) * 3)[1])
            out["Z"] = out["Joint"].map(lambda j: m.get(j, (float("nan"),) * 3)[2])
    return out[cols] if not out.empty else out


def tidy_story_drifts(sd: pd.DataFrame | None, cases: dict[str, str]) -> pd.DataFrame:
    cols = ["Story", "Case", "Dir", "Step", "Drift", "Label", "X", "Y", "Z"]
    if sd is None:
        return pd.DataFrame(columns=cols)
    cc, sc, dc, drc = col(sd, "OutputCase", "Case"), col(sd, "Story"), col(sd, "Direction"), col(sd, "Drift")
    if None in (cc, sc, drc):
        return pd.DataFrame(columns=cols)
    frames = []
    for d, case in cases.items():
        sub = sd[sd[cc].astype(str).str.lower() == case.lower()]
        if dc:
            sub = sub[sub[dc].astype(str).str.upper().str.startswith(d)]
        if sub.empty:
            continue
        get = lambda n: pd.to_numeric(sub[col(sub, n)], errors="coerce") if col(sub, n) else float("nan")
        frames.append(pd.DataFrame({
            "Story": sub[sc].map(sid), "Case": case, "Dir": d, "Step": step_label(sub),
            "Drift": pd.to_numeric(sub[drc], errors="coerce").abs(),
            "Label": sub[col(sub, "Label")].map(sid) if col(sub, "Label") else "",
            "X": get("X"), "Y": get("Y"), "Z": get("Z"),
        }))
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=cols)
    if not out.empty:
        bad = int(out["Drift"].isna().sum())
        if bad:
            print(f"[WARN] Story Drifts: {bad} of {len(out)} rows have no numeric '{drc}' value and are ignored "
                  f"(raw sample: {sd[drc].head(3).tolist()}). The cross-check column will be blank; "
                  "joint drifts are used for the governing result.")
            out = out.dropna(subset=["Drift"]).reset_index(drop=True)
    return out


def build_stories(defs: pd.DataFrame | None, jd: pd.DataFrame, sd: pd.DataFrame) -> pd.DataFrame:
    """Story, Height (m), Elevation (m of the story level), ordered top -> bottom."""
    names = list(dict.fromkeys(list(jd["Story"]) + list(sd["Story"])))
    heights: dict[str, float] = {}
    if defs is not None:
        n, h = col(defs, "Story", "Name"), col(defs, "Height")
        if n and h:
            heights = {sid(a): float(b) for a, b in zip(defs[n], defs[h]) if pd.notna(b)}
            for s in heights:
                if s not in names:
                    names.append(s)
    elev: dict[str, float] = {}
    z = jd.groupby("Story")["Z"].median().dropna() if not jd.empty else pd.Series(dtype=float)
    if len(z):
        elev = {s: float(z[s]) for s in names if s in z.index}
    if len(elev) == len(names):
        names.sort(key=lambda s: -elev[s])
    elif heights:                                      # defs are listed top -> bottom in ETABS
        order = [s for s in heights if s in names] + [s for s in names if s not in heights]
        names, elev, run = order, {}, 0.0
        for s in reversed(names):
            run += heights.get(s, 0.0)
            elev[s] = run
    rows = []
    for i, s in enumerate(names):
        h = heights.get(s)
        if h is None and s in elev:
            below = elev.get(names[i + 1]) if i + 1 < len(names) else 0.0
            h = elev[s] - (below if below is not None else 0.0)
        rows.append({"Story": s, "Height": h if h is not None else float("nan"), "Elevation": elev.get(s, float("nan"))})
    return pd.DataFrame(rows)


def evaluate(tidy: pd.DataFrame, sdt: pd.DataFrame, stories: pd.DataFrame, cases: dict[str, str],
             limit: float, kd: float, tol: float):
    """Per direction and story: governing drift (worst corner/edge point, all steps enveloped)."""
    if not tidy.empty:
        hulls = {}
        for s in stories["Story"]:
            pts = tidy[tidy["Story"] == s].drop_duplicates("Joint")[["X", "Y"]].dropna()
            hulls[s] = convex_hull([(round(a, 6), round(b, 6)) for a, b in pts.values]) if len(pts) >= 3 else []
        tidy["Loc"] = [classify((x, y), hulls.get(s, []), tol) if pd.notna(x) and pd.notna(y) else "Unknown"
                       for s, x, y in zip(tidy["Story"], tidy["X"], tidy["Y"])]
    else:
        hulls = {}
        tidy["Loc"] = []
    rows = []
    for d, case in cases.items():
        for _, st in stories.iterrows():
            s = st["Story"]
            rec: dict[str, Any] = {"Dir": d, "Case": case, "Story": s, "Height": st["Height"], "Elevation": st["Elevation"]}
            sub = tidy[(tidy["Dir"] == d) & (tidy["Story"] == s)]
            tab = sdt[(sdt["Dir"] == d) & (sdt["Story"] == s)]
            if not sub.empty:
                i = sub["Drift"].idxmax()
                rec.update(all_max=float(sub.loc[i, "Drift"]), all_label=sub.loc[i, "Label"], all_loc=sub.loc[i, "Loc"])
                per = sub[sub["Loc"].isin(["Corner", "Edge"])]
                if not per.empty:
                    j = per["Drift"].idxmax()
                    rec.update(per_max=float(per.loc[j, "Drift"]), label=per.loc[j, "Label"], loc=per.loc[j, "Loc"],
                               x=per.loc[j, "X"], y=per.loc[j, "Y"], step=per.loc[j, "Step"], source="Joint Drifts, corner/edge points")
            if not tab.empty:
                k = tab["Drift"].idxmax()
                rec.update(table_max=float(tab.loc[k, "Drift"]), table_label=tab.loc[k, "Label"])
            if "per_max" in rec:
                rec["gov"] = rec["per_max"]
            elif "all_max" in rec:
                rec.update(gov=rec["all_max"], label=rec["all_label"], loc=rec["all_loc"], step=sub.loc[sub["Drift"].idxmax(), "Step"],
                           x=sub.loc[sub["Drift"].idxmax(), "X"], y=sub.loc[sub["Drift"].idxmax(), "Y"],
                           source="Joint Drifts, all joints (plan classification unavailable)")
            elif "table_max" in rec:
                k = tab["Drift"].idxmax()
                rec.update(gov=rec["table_max"], label=rec["table_label"], loc="Unknown", step=tab.loc[k, "Step"],
                           x=tab.loc[k, "X"], y=tab.loc[k, "Y"], source="ETABS Story Drifts table")
            if "gov" in rec:
                rec["gov_eff"] = rec["gov"] * kd
                rec["ratio"] = rec["gov_eff"] / limit
                rec["status"] = "PASS" if rec["gov_eff"] <= limit else "FAIL"
            rows.append(rec)
    return pd.DataFrame(rows), hulls


# ----------------------------------------------------------------------------
# Validation checks
# ----------------------------------------------------------------------------
def run_checks(res, tidy, sdt, manifest, cases, cfg, ctx, modal_mass) -> list[tuple[str, str]]:
    checks: list[tuple[str, str]] = []
    add = lambda sev, msg: checks.append((sev, msg))
    for d, case in cases.items():
        n_j, n_s = int((tidy["Dir"] == d).sum()) if not tidy.empty else 0, int((sdt["Dir"] == d).sum()) if not sdt.empty else 0
        add("PASS" if (n_j or n_s) else "FAIL", f"{case}: {n_j} joint-drift rows and {n_s} story-drift rows extracted.")
    status = manifest.get("sls_case_status", {})
    if status:
        bad = {k: v for k, v in status.items() if v != 4}
        add("PASS" if not bad else "WARN", "All SLS cases reported by ETABS as finished (analysis complete)."
            if not bad else f"SLS cases not reported as finished: {bad}.")
    else:
        add("WARN", "ETABS case-run status is not recorded in the manifest.")
    for d, case in cases.items():
        steps = tidy[tidy["Dir"] == d]["Step"].nunique() if not tidy.empty else (sdt[sdt["Dir"] == d]["Step"].nunique() if not sdt.empty else 0)
        add("PASS" if steps >= 2 else "WARN",
            f"{case}: {steps} result step(s) enveloped." + ("" if steps >= 2 else " Confirm the 5 % eccentricity variants are in the case."))
    if tidy.empty:
        add("WARN", "Joint Drifts unavailable; the governing point is taken from the ETABS Story Drifts table.")
    elif tidy["X"].isna().all():
        add("WARN", "Joint coordinates unavailable; corner/edge classification not possible (all joints considered).")
    else:
        add("PASS", f"Joint coordinates available for corner/edge classification (tolerance {cfg.hull_tol} m).")
    if not res.empty and {"table_max", "gov"}.issubset(res.columns):
        diffs = res.dropna(subset=["table_max", "gov"])
        if len(diffs):
            worst = (diffs["gov"] - diffs["table_max"]).abs().div(diffs["table_max"].replace(0, float("nan"))).max()
            add("PASS" if worst <= 0.02 else "WARN",
                f"Governing joint drift agrees with the ETABS Story Drifts table (max difference {worst * 100:.1f} %)."
                if worst <= 0.02 else
                f"Governing joint drift differs from the ETABS Story Drifts table by up to {worst * 100:.1f} %; review.")
    if not res.empty and {"all_max", "per_max"}.issubset(res.columns):
        inter = res[(res["all_max"] > res["per_max"] * 1.0001)]
        add("PASS" if inter.empty else "WARN",
            "No interior joint exceeds the corner/edge maximum on any floor." if inter.empty else
            "An interior joint exceeds the corner/edge maximum on: " + ", ".join(f"{r.Story} ({r.Dir})" for r in inter.itertuples()) + ".")
    if res.empty or "gov" not in res.columns or res["gov"].isna().any():
        add("FAIL", "At least one story has no drift result.")
    else:
        add("PASS", f"A governing drift result exists for all {res['Story'].nunique()} stories in both directions.")
    if res["Height"].isna().any():
        add("WARN", "Story height could not be determined for every story (ratios are taken as reported by ETABS).")
    if modal_mass:
        ok = all(v >= 0.90 for v in modal_mass.values())
        add("PASS" if ok else "WARN", "Cumulative modal mass: " + ", ".join(f"{k} {v * 100:.1f} %" for k, v in modal_mass.items())
            + ("." if ok else " (below 90 %)."))
    add("INFO", f"No factor applied to ETABS drifts (clause 5.5.1.2); kd applied to compliance result = {cfg.kd:g}.")
    cm, mm = ctx.get("MODEL_FILENAME"), manifest.get("model_filename")
    if cm and mm and Path(str(cm)).stem.lower() != Path(str(mm)).stem.lower():
        add("WARN", f"The context file refers to model '{cm}' but the extraction is from '{mm}'. Check project details.")
    for w in manifest.get("warnings", []):
        add("WARN", f"Extraction: {w}")
    return checks


# ----------------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------------
def fig_profiles(res: pd.DataFrame, limit: float, kd_info: float, path: Path) -> Path | None:
    dirs = [d for d in ("X", "Y") if not res[res["Dir"] == d].empty]
    if not dirs:
        return None
    fig, axes = plt.subplots(1, len(dirs), figsize=(7.2, 4.2), sharey=True, squeeze=False)
    for ax, d in zip(axes[0], dirs):
        r = res[res["Dir"] == d].dropna(subset=["gov"])
        y = r["Elevation"] if r["Elevation"].notna().all() else range(len(r), 0, -1)
        ax.plot(r["gov_eff"], y, "-o", color=f"#{BLUE}", label="Governing drift")
        ax.axvline(limit, color="#C00000", ls="--", lw=1.2, label=f"Limit {limit:g}")
        ax.plot(r["gov"] * kd_info, y, ":", color="#7F7F7F", lw=1.1, label=f"kd = {kd_info:g} (informative)")
        for xv, yv in zip(r["gov_eff"], y):
            ax.annotate(f"{xv:.5f}", (xv, yv), textcoords="offset points", xytext=(6, 4), fontsize=7)
        ax.set_title(f"{d} direction ({r['Case'].iloc[0]})", fontsize=9)
        ax.set_xlabel("Inter-storey drift ratio", fontsize=8)
        ax.set_xlim(0, max(limit * 1.25, r["gov_eff"].max() * 1.25))
        ax.tick_params(labelsize=7)
        ax.grid(alpha=.3)
        ax.legend(fontsize=6.5, loc="lower right")
    axes[0][0].set_ylabel("Story level elevation (m)" if res["Elevation"].notna().all() else "Story (top = highest)", fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()
    return path


def fig_plan(res: pd.DataFrame, tidy: pd.DataFrame, hulls: dict, path: Path) -> Path | None:
    if tidy.empty or tidy["X"].isna().all():
        return None
    dirs = [d for d in ("X", "Y") if not res[res["Dir"] == d].dropna(subset=["gov"]).empty]
    if not dirs:
        return None
    fig, axes = plt.subplots(1, len(dirs), figsize=(7.2, 3.8), squeeze=False)
    for ax, d in zip(axes[0], dirs):
        r = res[res["Dir"] == d].dropna(subset=["gov"])
        g = r.loc[r["gov"].idxmax()]
        pts = tidy[tidy["Story"] == g["Story"]].drop_duplicates("Joint")
        hull = hulls.get(g["Story"], [])
        ax.scatter(pts["X"], pts["Y"], s=14, color="#7F7F7F", label="Joints")
        if len(hull) >= 3:
            ax.plot([p[0] for p in hull + hull[:1]], [p[1] for p in hull + hull[:1]], color=f"#{BLUE}", lw=1, label="Plan boundary")
        if pd.notna(g.get("x")):
            ax.scatter([g["x"]], [g["y"]], s=70, marker="*", color="#C00000", zorder=5, label=f"Governing joint {g['label']}")
        ax.set_aspect("equal", adjustable="datalim")
        ax.set_title(f"{d}: {g['Story']}", fontsize=9)
        ax.set_xlabel("X (m)", fontsize=8); ax.set_ylabel("Y (m)", fontsize=8)
        ax.tick_params(labelsize=7); ax.grid(alpha=.3); ax.legend(fontsize=6.5)
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()
    return path


# ----------------------------------------------------------------------------
# Shared design system: every panel and the merged sheet use these tokens, so the
# three images match in fonts, colours, spacing and pixel width.
# ----------------------------------------------------------------------------
PANEL_W, PAD, DPI = 11.14, 0.04, 200            # inches, inches, dots/inch -> identical pixel width for all panels
D_BAND, D_BAND_SUB = "#14213D", "#B9C6D8"        # title band (dark navy) and its subtitle
D_SECT, D_HEAD = "#2F5D8C", "#E4EAF2"            # section bar (mid blue), column header (light blue-grey)
D_ZEBRA, D_STRIP = "#F5F8FB", "#EDF2F8"
D_EDGE, D_TEXT, D_MUTED, D_INK = "#C5CFDB", "#1A1A1A", "#5B6675", "#14213D"
PILL = {"ok": ("#DDF1E2", "#1D6B34"), "bad": ("#FADCDA", "#A4262C"),
        "warn": ("#FFF1CC", "#8A5A00"), "info": ("#E1ECF8", "#1F4E79")}
C_X, C_Y, C_LIM = "#2F6DB5", "#E08A2E", "#C62828"
C_OK, C_WARN, C_BAD = "#1D6B34", "#B26A00", "#C62828"


def util_color(u: float) -> str:
    return C_BAD if u > 1 else (C_WARN if u > 0.7 else C_OK)


# ----------------------------------------------------------------------------
# Panel 1: SLS inter-storey drift check (table + bar chart)
# ----------------------------------------------------------------------------
def render_jpg(res: pd.DataFrame, cfg, checks, path: Path) -> bool:
    from matplotlib.patches import Rectangle
    limit = cfg.limit
    names = {"X": cfg.case_x, "Y": cfg.case_y}
    stories = list(dict.fromkeys(res["Story"]))             # top -> bottom
    for d in ("X", "Y"):
        if not res[res["Dir"] == d].empty:
            names[d] = res[res["Dir"] == d]["Case"].iloc[0]

    def get(d, s):
        m = res[(res["Dir"] == d) & (res["Story"] == s)]
        return m.iloc[0] if not m.empty else None

    ok = bool(len(res)) and res["status"].eq("PASS").all()
    n = len(stories)
    kd_txt = "kd not applied" if abs(cfg.kd - 1) < 1e-12 else f"kd = {cfg.kd:g} applied"
    NC = 8
    widths = [1.15, 2.0, 1.15, 0.95, 2.0, 1.15, 0.95, 1.4]

    rows = [banner("1  \u00b7  SLS INTER-STOREY DRIFT CHECK",
                   f"NBC 105:2025 cl. 5.5.3   \u00b7   limit {limit:g}   \u00b7   unmultiplied deflections (cl. 5.5.1.2)",
                   NC, ("COMPLIANT" if ok else "NON-COMPLIANT", "ok" if ok else "bad"))]
    strip = []
    for d in ("X", "Y"):
        sub = res[res["Dir"] == d].dropna(subset=["gov_eff"])
        if sub.empty:
            txt = f"{d}  \u00b7  {names[d]}     no result"
        else:
            g = sub.loc[sub["gov_eff"].idxmax()]
            txt = f"{d}  \u00b7  {names[d]}     max {g['gov_eff']:.5f}   ({g['ratio'] * 100:.0f} % of limit, {g['Story']})"
        strip.append(cell(txt, span=4, bg=D_STRIP, ha="left", bold=True, color=D_INK, size=10.5))
    rows.append({"h": 0.48, "cells": strip})
    rows.append({"h": 0.40, "cells": [hcell(""), hcell(f"X direction  \u00b7  {names['X']}", 3),
                                      hcell(f"Y direction  \u00b7  {names['Y']}", 3), hcell("")]})
    rows.append({"h": 0.36, "cells": [hcell("Story"), hcell("Governing joint"), hcell("Drift"), hcell("Util."),
                                      hcell("Governing joint"), hcell("Drift"), hcell("Util."), hcell("Status")]})
    for i, s in enumerate(stories):
        bg = D_ZEBRA if i % 2 == 0 else "white"
        cells, row_ok, missing = [cell(s, bg=bg, ha="left", bold=True)], True, False
        for d in ("X", "Y"):
            r = get(d, s)
            if r is None or pd.isna(r.get("gov_eff")):
                cells += [cell("n/a", bg=bg, color=D_MUTED)] * 3
                missing = True
                continue
            row_ok = row_ok and bool(r["status"] == "PASS")
            cells += [cell(f"{sid(r.get('label'))}  ({sid(r.get('loc')).lower()})", bg=bg, color=D_MUTED, size=10),
                      cell(f"{r['gov_eff']:.5f}", bg=bg),
                      cell(f"{r['ratio'] * 100:.0f} %", bg=bg, bold=True, color=util_color(r["ratio"]))]
        cells.append(status_cell(None if missing else row_ok, "PASS", "FAIL", bg=bg))
        rows.append({"h": 0.44, "cells": cells})
    rows.append({"h": 0.38, "cells": [scell("Governing inter-storey drift ratio by story   \u00b7   worst corner / edge joint, all eccentricity steps enveloped", NC)]})
    notes = [note_row(f"Limit {limit:g} per NBC 105:2025 cl. 5.5.3   \u00b7   no factor applied to ETABS drifts (cl. 5.5.1.2)   \u00b7   "
                      f"{kd_txt}   \u00b7   utilisation = drift / limit", NC)]

    h1, hc, h3 = sum(r["h"] for r in rows), max(2.6, 0.42 * n + 1.5), sum(r["h"] for r in notes)
    total = h1 + hc + h3
    tw = sum(widths)
    widths = [w / tw * PANEL_W for w in widths]
    FW, FH = PANEL_W + 2 * PAD, total + 2 * PAD
    with plt.rc_context({"font.family": _font(), "mathtext.default": "regular"}):
        fig = plt.figure(figsize=(FW, FH), facecolor="white")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(-PAD, PANEL_W + PAD); ax.set_ylim(-PAD, total + PAD); ax.axis("off")
        y = _draw_rows(ax, rows, widths, total)
        ax.add_patch(Rectangle((0, y - hc), PANEL_W, hc, facecolor="white", edgecolor=D_EDGE, lw=0.7))
        cax = fig.add_axes([(PAD + 1.0) / FW, (PAD + y - hc + 0.62) / FH, (PANEL_W - 1.0 - 0.9) / FW, (hc - 1.15) / FH])
        ys = list(range(n))[::-1]
        vmax = max([limit] + [v for v in res["gov_eff"].dropna()])
        for off, d, colr in ((0.19, "X", C_X), (-0.19, "Y", C_Y)):
            vals = [get(d, s)["gov_eff"] if get(d, s) is not None else float("nan") for s in stories]
            cax.barh([yy + off for yy in ys], vals, height=0.34, color=colr, label=f"{d}  \u00b7  {names[d]}")
            for yy, v in zip(ys, vals):
                if pd.notna(v):
                    cax.text(v + vmax * 0.012, yy + off, f"{v:.5f}", va="center", fontsize=8.5, color="#333")
        cax.axvline(limit, color=C_LIM, ls="--", lw=1.5)
        cax.annotate(f"Limit {limit:g}", xy=(limit, 1.0), xycoords=("data", "axes fraction"), xytext=(5, 3),
                     textcoords="offset points", color=C_LIM, fontsize=9, fontweight="bold")
        cax.set_yticks(ys); cax.set_yticklabels(stories, fontsize=9.5)
        cax.set_xlim(0, vmax * 1.2); cax.set_ylim(-0.6, n - 0.4)
        cax.set_xlabel("Inter-storey drift ratio", fontsize=9, color=D_MUTED)
        cax.tick_params(axis="x", labelsize=8.5, colors=D_MUTED); cax.tick_params(axis="y", length=0)
        cax.grid(axis="x", alpha=0.35, color=D_EDGE)
        cax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            cax.spines[sp].set_visible(False)
        cax.spines["bottom"].set_color(D_EDGE)
        cax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=9)
        _draw_rows(ax, notes, widths, y - hc)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=DPI, format="jpg", facecolor="white", pil_kwargs={"quality": 95})
        plt.close(fig)
    return ok


# ----------------------------------------------------------------------------
# Displacement / torsion data (ULS + SLS)
# ----------------------------------------------------------------------------
def tidy_displacements(s14: pd.DataFrame | None, jdisp: pd.DataFrame | None, joint_story: dict[str, str],
                       cases: dict[str, str], scale: float = 1.0) -> pd.DataFrame:
    """Per story / case / direction / step: maximum and average displacement (mm) and their ratio.

    Primary source  : ETABS "Story Max Over Avg Displacements" (Maximum, Average, Ratio).
    Fallback source : ETABS "Joint Displacements"; per story and step the maximum joint displacement
                      and the average of the two extreme-point displacements, (max + min) / 2.
    ETABS results are in metres (extractor units kN-m) and are converted to mm. `scale` is 1.0 unless
    the engineer asks for a factor on the ULS results (--uls-scale)."""
    cols = ["Story", "Case", "Dir", "Step", "Max", "Avg", "Ratio", "Source"]
    frames = []
    cc, sc, dc = (col(s14, "OutputCase", "Case"), col(s14, "Story"), col(s14, "Direction")) if s14 is not None else (None,) * 3
    mc, ac, rc = (col(s14, "Maximum", "Max"), col(s14, "Average", "Avg"), col(s14, "Ratio")) if s14 is not None else (None,) * 3
    if s14 is not None and None not in (cc, sc, mc) and (ac or rc):
        for d, case in cases.items():
            sub = s14[s14[cc].astype(str).str.lower() == case.lower()]
            if dc:
                sub = sub[sub[dc].astype(str).str.upper().str.startswith(d)]
            if sub.empty:
                continue
            mx = pd.to_numeric(sub[mc], errors="coerce").abs() * 1000 * scale
            ratio = pd.to_numeric(sub[rc], errors="coerce") if rc else pd.Series(float("nan"), index=sub.index)
            av = pd.to_numeric(sub[ac], errors="coerce").abs() * 1000 * scale if ac else mx / ratio
            calc = mx / av.where(av > 0)
            frames.append(pd.DataFrame({"Story": sub[sc].map(sid), "Case": case, "Dir": d, "Step": step_label(sub),
                                        "Max": mx, "Avg": av, "Ratio": calc.fillna(ratio),
                                        "Source": "ETABS Story Max Over Avg Displacements"}))
    if frames:
        out = pd.concat(frames, ignore_index=True)
        return out.dropna(subset=["Max"]).reset_index(drop=True)

    rows = []
    if jdisp is not None:
        cc, uc, sc = col(jdisp, "OutputCase", "Case"), col(jdisp, "UniqueName"), col(jdisp, "Story")
        for d, case in cases.items():
            uc_d = col(jdisp, f"U{d}")
            if None in (cc, uc_d) or (uc is None and sc is None):
                continue
            sub = jdisp[jdisp[cc].astype(str).str.lower() == case.lower()]
            if sub.empty:
                continue
            story = sub[sc].map(sid) if sc else sub[uc].map(sid).map(lambda j: joint_story.get(j, ""))
            g = pd.DataFrame({"Story": story, "Step": step_label(sub),
                              "U": pd.to_numeric(sub[uc_d], errors="coerce") * 1000 * scale}).dropna(subset=["U"])
            g = g[g["Story"] != ""]
            for (s, step), grp in g.groupby(["Story", "Step"], sort=False):
                u = grp["U"].to_numpy()
                if len(u) < 2:
                    continue
                if u.mean() < 0:                      # work with the dominant sense of the displacement
                    u = -u
                mx, mn = float(u.max()), float(u.min())
                avg = (mx + mn) / 2
                rows.append({"Story": s, "Case": case, "Dir": d, "Step": step, "Max": mx, "Avg": abs(avg),
                             "Ratio": mx / abs(avg) if abs(avg) > 0 else float("nan"),
                             "Source": "Joint Displacements (computed)"})
    return pd.DataFrame(rows, columns=cols)


def max_displacement(dd: pd.DataFrame, d: str) -> float | None:
    sub = dd[dd["Dir"] == d] if not dd.empty else dd
    return None if sub.empty else float(sub["Max"].max())


def building_height(stories: pd.DataFrame, override_m: float | None) -> tuple[float | None, str]:
    """Total height H in mm and where it came from."""
    if override_m:
        return float(override_m) * 1000, "--height"
    h = stories["Height"]
    if len(h) and h.notna().all():
        return float(h.sum()) * 1000, "sum of story heights (ETABS Story Definitions)"
    e = stories["Elevation"].dropna()
    if len(e):
        return float(e.max()) * 1000, "top story elevation (base assumed at Z = 0)"
    return None, "unavailable"


def torsion_summary(dd: pd.DataFrame, cases: dict[str, str], limit: float, extreme: float) -> dict[str, dict]:
    """Governing story = story with the largest max/avg displacement ratio (all steps enveloped)."""
    out: dict[str, dict] = {}
    for d, case in cases.items():
        sub = dd[dd["Dir"] == d].dropna(subset=["Ratio"]) if not dd.empty else dd
        if sub.empty:
            continue
        r = sub.loc[sub["Ratio"].idxmax()]
        ratio = float(r["Ratio"])
        out[d] = {"case": case, "story": r["Story"], "dmax": float(r["Max"]), "davg": float(r["Avg"]), "ratio": ratio,
                  "step": r["Step"], "source": r["Source"], "status": "OK" if ratio <= limit else "NOT OK",
                  "category": "none" if ratio <= limit else ("irregular" if ratio <= extreme else "extreme")}
    return out


# ----------------------------------------------------------------------------
# Generic table renderer (shared by panels 2 and 3, the sheet header and the footer)
# ----------------------------------------------------------------------------
def _font() -> str:
    from matplotlib import font_manager
    have = {f.name for f in font_manager.fontManager.ttflist}
    return next((n for n in ("Arial", "Liberation Sans", "Helvetica", "DejaVu Sans") if n in have), "DejaVu Sans")


def cell(text: str = "", span: int = 1, bg: str = "white", ha: str = "center", color: str = D_TEXT,
         bold: bool = False, italic: bool = False, size: float = 11, pill: str | None = None,
         edge: str | None = None, sub: str | None = None) -> dict:
    return dict(text=text, span=span, bg=bg, ha=ha, color=color, bold=bold, italic=italic, size=size,
                pill=pill, edge=edge, sub=sub)


def hcell(text: str, span: int = 1, ha: str = "center") -> dict:
    """Column-header cell."""
    return cell(text, span, bg=D_HEAD, ha=ha, color=D_INK, bold=True, size=10.5, edge="white")


def scell(text: str, span: int) -> dict:
    """Section bar."""
    return cell(text, span, bg=D_SECT, ha="left", color="white", bold=True, size=10.5, edge=D_SECT)


def status_cell(ok: bool | None, text_ok: str = "OK", text_bad: str = "NOT OK", bg: str = "white") -> dict:
    if ok is None:
        return cell("n/a", bg=bg, pill="warn", bold=True, size=10)
    return cell(text_ok if ok else text_bad, bg=bg, pill="ok" if ok else "bad", bold=True, size=10)


def note_row(text: str, ncols: int, wrap: int = 170) -> dict:
    import textwrap
    text = textwrap.fill(text, wrap, subsequent_indent="   ")
    lines = text.count("\n") + 1
    return {"h": 0.22 + 0.19 * lines, "cells": [cell(text, span=ncols, ha="left", italic=True, color=D_MUTED, size=9.5)]}


def banner(title: str, sub: str, ncols: int, badge: tuple[str, str] | None = None, h: float = 0.82, size: float = 15) -> dict:
    return {"h": h, "badge": badge,
            "cells": [cell(title, span=ncols, bg=D_BAND, ha="left", color="white", bold=True, size=size, edge=D_BAND, sub=sub)]}


def _draw_rows(ax, rows: list[dict], widths: list[float], y_top: float, x0: float = 0.0) -> float:
    """Draw table rows top-down in inch coordinates; returns the y below the last row."""
    import textwrap
    from matplotlib.patches import FancyBboxPatch, Rectangle
    total_w, y = sum(widths), y_top
    for r in rows:
        h, x, i = r["h"], x0, 0
        for c in r["cells"]:
            w = sum(widths[i:i + c["span"]])
            ax.add_patch(Rectangle((x, y - h), w, h, facecolor=c["bg"], edgecolor=c["edge"] or D_EDGE, lw=0.7))
            text, size = c["text"], c["size"]
            if text and c["pill"]:
                pbg, ptx = PILL[c["pill"]]
                pw = min(w - 0.12, max(0.75, len(text) * size * 0.0085 + 0.36))
                ph = min(h - 0.12, 0.30)
                ax.add_patch(FancyBboxPatch((x + w / 2 - pw / 2, y - h / 2 - ph / 2), pw, ph,
                                            boxstyle=f"round,pad=0,rounding_size={ph / 2}", facecolor=pbg, edgecolor="none"))
                ax.text(x + w / 2, y - h / 2, text, ha="center", va="center_baseline", color=ptx, fontsize=size, fontweight="bold")
            elif text:
                avail = w - 0.3
                if "\n" not in text and "$" not in text and len(text) * size * 0.0070 > avail:
                    text = "\n".join(textwrap.wrap(text, max(8, int(avail / (size * 0.0070)))))
                tx = x + 0.14 if c["ha"] == "left" else (x + w - 0.14 if c["ha"] == "right" else x + w / 2)
                kw = dict(ha=c["ha"], va="center_baseline", fontsize=size, linespacing=1.25,
                          fontweight="bold" if c["bold"] else "normal", fontstyle="italic" if c["italic"] else "normal")
                if c["sub"]:
                    ax.text(tx, y - h / 2 + 0.13, text, color=c["color"], **kw)
                    ax.text(tx, y - h / 2 - 0.19, c["sub"], color=D_BAND_SUB, **{**kw, "fontsize": 9.5, "fontweight": "normal"})
                else:
                    ax.text(tx, y - h / 2, text, color=c["color"], **kw)
            x += w
            i += c["span"]
        if r.get("badge"):
            btxt, bst = r["badge"]
            pbg, ptx = PILL[bst]
            pw, ph = max(1.4, len(btxt) * 0.105 + 0.5), 0.36
            ax.add_patch(FancyBboxPatch((x0 + total_w - 0.22 - pw, y - h / 2 - ph / 2), pw, ph,
                                        boxstyle=f"round,pad=0,rounding_size={ph / 2}", facecolor=pbg, edgecolor="none", zorder=5))
            ax.text(x0 + total_w - 0.22 - pw / 2, y - h / 2, btxt, ha="center", va="center_baseline", color=ptx,
                    fontsize=10.5, fontweight="bold", zorder=6)
        y -= h
    return y


def draw_table(rows: list[dict], widths: list[float], path: Path, overlay=None) -> None:
    tw = sum(widths)
    widths = [w / tw * PANEL_W for w in widths]
    total = sum(r["h"] for r in rows)
    with plt.rc_context({"font.family": _font(), "mathtext.default": "regular"}):
        fig = plt.figure(figsize=(PANEL_W + 2 * PAD, total + 2 * PAD), facecolor="white")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(-PAD, PANEL_W + PAD); ax.set_ylim(-PAD, total + PAD); ax.axis("off")
        _draw_rows(ax, rows, widths, total)
        if overlay is not None:
            overlay(ax, widths, total)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=DPI, format="jpg", facecolor="white", pil_kwargs={"quality": 95})
        plt.close(fig)


def _fmt(v: Any, d: int) -> str:
    return "n/a" if v is None or (isinstance(v, float) and not math.isfinite(v)) else f"{v:.{d}f}"


# ----------------------------------------------------------------------------
# Panel 2: displacement and drift criteria
# ----------------------------------------------------------------------------
def render_criteria(path: Path, cfg, H_mm: float | None, disp: dict, drift: dict) -> dict:
    """disp / drift: {("ULS"|"SLS", dir): value}. Returns the table content (for JSON/CSV)."""
    lim_d = {"ULS": cfg.uls_disp_factor, "SLS": cfg.sls_disp_factor}
    lim_r = {"ULS": cfg.uls_limit, "SLS": cfg.limit}
    body = [{"h": 0.40, "cells": [hcell("Description", ha="left"), hcell("EQX"), hcell("EQY"), hcell("Allowable"), hcell("Status")]},
            {"h": 0.38, "cells": [scell("Displacement criteria  \u00b7  equivalent static method", 5)]}]
    content: dict[str, Any] = {"H_mm": H_mm, "rows": []}

    def line(label, vals, allow, allow_txt, d):
        ok = None if (allow is None or any(v is None for v in vals)) else all(v <= allow for v in vals)
        body.append({"h": 0.62, "cells": [cell(label, ha="left"), cell(_fmt(vals[0], d), bold=True), cell(_fmt(vals[1], d), bold=True),
                                          cell(allow_txt, size=10.5), status_cell(ok)]})
        content["rows"].append({"description": label, "EQX": vals[0], "EQY": vals[1], "allowable": allow,
                                "status": None if ok is None else ("OK" if ok else "NOT OK")})

    for lvl in ("ULS", "SLS"):
        allow = None if H_mm is None else lim_d[lvl] * H_mm
        line(f"Max. story displacement \u2014 {lvl} (mm)", [disp.get((lvl, "X")), disp.get((lvl, "Y"))], allow,
             f"{_fmt(allow, 2)}\n{lim_d[lvl]:g} \u00d7 H", 4)
    body.append({"h": 0.38, "cells": [scell("Drift criteria  \u00b7  equivalent static method", 5)]})
    for lvl in ("ULS", "SLS"):
        line(f"Max. inter-story drift ratio \u2014 {lvl}", [drift.get((lvl, "X")), drift.get((lvl, "Y"))], lim_r[lvl],
             f"{lim_r[lvl]:g}\nNBC 105:2025", 6)
    sts = [r["status"] for r in content["rows"]]
    state = "bad" if "NOT OK" in sts else ("warn" if None in sts else "ok")
    badge = {"ok": "ALL CHECKS OK", "bad": "NOT OK", "warn": "INCOMPLETE"}[state]
    content["state"] = state
    rows = [banner("2  \u00b7  DISPLACEMENT AND DRIFT CRITERIA",
                   f"ULS results \u00d7 R\u03bc = {cfg.uls_scale:g} (cl. 5.5.1.1)   \u00b7   SLS unmultiplied   \u00b7   H = {_fmt(H_mm, 0)} mm",
                   5, (badge, state))] + body
    draw_table(rows, [4.2, 1.55, 1.55, 2.0, 1.8], path)
    return content


# ----------------------------------------------------------------------------
# Panel 3: torsional irregularity
# ----------------------------------------------------------------------------
def render_torsion(path: Path, cfg, tors: dict[str, dict], cases: dict[str, str]) -> dict:
    lim, ext = cfg.torsion_limit, cfg.torsion_extreme
    g = lambda d, k: tors.get(d, {}).get(k)
    oks = [t["ratio"] <= lim for t in tors.values()]
    ok = None if len(tors) < len(cases) or not tors else all(oks)
    order = ["none", "irregular", "extreme"]
    worst = max((t["category"] for t in tors.values()), key=order.index) if tors else None
    dirs = " & ".join(d for d, t in tors.items() if t["category"] == worst)
    verdict = {None: "n/a", "none": f"Not torsionally irregular (ratio \u2264 {lim:g})",
               "irregular": f"Torsionally irregular in {dirs} (ratio > {lim:g})",
               "extreme": f"Extreme torsional irregularity in {dirs} (ratio > {ext:g})"}[worst]
    state = "warn" if ok is None else ("ok" if ok else "bad")
    badge = {None: "INCOMPLETE", "none": "NOT IRREGULAR", "irregular": "IRREGULAR", "extreme": "EXTREME IRREGULARITY"}[worst]
    pbg, ptx = PILL[state]
    rows = [banner("3  \u00b7  TORSIONAL IRREGULARITY CHECK",
                   "NBC 105:2025 cl. 5.4.2.2   \u00b7   ULS cases, ratio of maximum to average story displacement", 5, (badge, state)),
            {"h": 0.40, "cells": [hcell("Description", ha="left"), hcell(cases.get("X", "EQX-ULS")), hcell(cases.get("Y", "EQY-ULS")),
                                  hcell("Limit"), hcell("Status")]},
            {"h": 0.44, "cells": [cell("Governing story", ha="left"), cell(sid(g("X", "story")) or "n/a"),
                                  cell(sid(g("Y", "story")) or "n/a"), cell("\u2014", color=D_MUTED), cell("\u2014", color=D_MUTED)]}]
    for i, (label, key) in enumerate((("Max. edge displacement \u2014 $\\delta_{max}$ (mm)", "dmax"),
                                      ("Avg. displacement \u2014 $\\delta_{avg}$ (mm)", "davg"))):
        bg = "white" if i == 0 else D_ZEBRA
        rows.append({"h": 0.44, "cells": [cell(label, ha="left", bg=bg), cell(_fmt(g("X", key), 3), bg=bg, bold=True),
                                          cell(_fmt(g("Y", key), 3), bg=bg, bold=True),
                                          cell("\u2014", bg=bg, color=D_MUTED), cell("\u2014", bg=bg, color=D_MUTED)]})
    rows.append({"h": 0.50, "cells": [cell("Torsional ratio \u2014 $\\delta_{max}$ / $\\delta_{avg}$", ha="left", bold=True),
                                      cell(_fmt(g("X", "ratio"), 3), bold=True, size=12), cell(_fmt(g("Y", "ratio"), 3), bold=True, size=12),
                                      cell(f"\u2264 {lim:g}"), status_cell(ok)]})
    rows.append({"h": 0.52, "cells": [cell("Torsional irregularity", ha="left", bold=True),
                                      cell(verdict, span=2, bg=pbg, color=ptx, bold=True, size=10.5),
                                      cell(f"\u2264 {lim:g}"), status_cell(ok)]})
    rows.append(note_row(f"Torsional irregularity exists if \u03b4max / \u03b4avg > {lim:g}   \u00b7   extreme torsional irregularity if "
                         f"\u03b4max / \u03b4avg > {ext:g}   (NBC 105:2025 cl. 5.4.2.2)", 5))
    draw_table(rows, [4.45, 1.68, 1.68, 1.67, 1.66], path)
    return {"limit": lim, "extreme_limit": ext, "directions": tors, "status": None if ok is None else ("OK" if ok else "NOT OK"),
            "verdict": verdict, "state": state}


# ----------------------------------------------------------------------------
# Sheet header / footer and the merged single image
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# Panel 4: column reinforcement details (bars selected from the ETABS required steel)
# ----------------------------------------------------------------------------
_ORD = ["Ground", "First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth",
        "Eleventh", "Twelfth"]


def floor_name(i: int) -> str:
    return f"{_ORD[i]} Floor" if i < len(_ORD) else f"Floor {i}"


def nat_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def bar_area(parts) -> int:
    """3.14 d^2/4 per bar, summed, truncated to whole mm2 (convention of the reference sheet)."""
    return int(math.floor(sum(n * 3.14 * d * d / 4 for n, d in parts) + 1e-9))


def bar_text(parts) -> str:
    return " + ".join(f"{n}-{d}\u03c6" for n, d in parts)


def beam_bar_text(parts) -> str:
    """Compact bar text without spaces around +, matching the reference beam sheet style
    (e.g. '2-16\u03c6+1-12\u03c6')."""
    return "+".join(f"{n}-{d}\u03c6" for n, d in parts)


def bar_text_th_ex(through_parts, extra_parts) -> str:
    """Format bars in the reference sheet's through/extra style:
      * through_parts is None -> 'REVISE'
      * extra_parts is None (needed but not pickable) -> '(through)(Th.)\n+ EX REVISE'
      * extra_parts is [] (not needed) -> '(through)(Th.)'
      * extra_parts is a list -> '(through)(Th.)\n+(extra)(Ex.)'
    Used for the 'At Support' column of the beam reinforcement panel."""
    if through_parts is None:
        return "REVISE"
    th_text = beam_bar_text(through_parts)
    if extra_parts is None:
        return f"({th_text})(Th.)\n+ EX REVISE"
    if not extra_parts:
        return f"({th_text})(Th.)"
    return f"({th_text})(Th.)\n+({beam_bar_text(extra_parts)})(Ex.)"


def parse_ladder(text: str) -> list[tuple[list, int]]:
    out = []
    for opt in text.split(","):
        parts = []
        for term in opt.split("+"):
            m = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", term)
            if not m:
                raise SystemExit(f"--col-ladder: cannot read '{term}' in '{opt}' (use e.g. 4-20+4-16,8-20)")
            parts.append((int(m.group(1)), int(m.group(2))))
        out.append((parts, bar_area(parts)))
    return sorted(out, key=lambda t: t[1])

def select_ladder_area(required_mm2: float, ladder_text: str) -> tuple[list, int] | None:
    """Return the smallest configured bar combination covering required steel."""
    return next(((parts, area) for parts, area in parse_ladder(ladder_text) if area >= required_mm2), None)


def parse_percent(s: pd.Series) -> pd.Series:
    """ETABS reports the required steel as '1.05 %' (text) or as a number; return percent of gross area."""
    txt = s.astype(str)
    v = pd.to_numeric(txt.str.replace("%", "", regex=False).str.strip(), errors="coerce")
    if not txt.str.contains("%").any() and v.notna().any() and v.max() <= 0.1:
        v = v * 100                                   # stored as a fraction
    return v


def column_dims(name: str, rect: pd.DataFrame | None) -> tuple[float, float] | None:
    """(b, d) in mm from the section table, else from a name such as 'Column 355 x 355'."""
    if rect is not None:
        n, t3, t2 = col(rect, "Name"), col(rect, "t3", "Depth"), col(rect, "t2", "Width")
        if None not in (n, t3, t2):
            r = rect[rect[n].astype(str).str.strip() == str(name).strip()]
            if not r.empty:
                return float(r[t2].iloc[0]) * 1000, float(r[t3].iloc[0]) * 1000
    m = re.search(r"(\d+(?:\.\d+)?)\s*[xX\u00d7]\s*(\d+(?:\.\d+)?)", str(name))
    return (float(m.group(1)), float(m.group(2))) if m else None


def grid_lines(uls_dir: Path) -> tuple[list, list]:
    """([(ordinate, id)] for X lines, same for Y lines) from 13_Grid_Definitions."""
    g = read_csv(uls_dir, "13_Grid_Definitions")
    if g is None:
        return [], []
    lt, oc = col(g, "LineType", "Type"), col(g, "Ordinate")
    ic = col(g, "ID", "GridID", "LineID", "Label")
    if ic is None:                                    # 'Name' is the grid SYSTEM name unless it differs per row
        nc = col(g, "Name")
        ic = nc if nc and g[nc].astype(str).nunique() > 1 else None
    if None in (lt, oc, ic):
        return [], []
    xs, ys = [], []
    for _, r in g.iterrows():
        o = pd.to_numeric(r[oc], errors="coerce")
        if pd.isna(o):
            continue
        t = str(r[lt]).strip().upper()
        (xs if t.startswith("X") else ys if t.startswith("Y") else []).append((float(o), sid(r[ic])))
    return xs, ys


def grid_name(x: float, y: float, xs: list, ys: list, tol: float) -> str | None:
    if not xs or not ys:
        return None
    ox, oy = min(xs, key=lambda a: abs(a[0] - x)), min(ys, key=lambda a: abs(a[0] - y))
    if abs(ox[0] - x) > tol or abs(oy[0] - y) > tol:
        return None
    a, b = ox[1], oy[1]
    alpha = [v for v in (a, b) if re.fullmatch(r"[A-Za-z]+", v)]
    digit = [v for v in (a, b) if re.fullmatch(r"\d+", v)]
    return alpha[0] + digit[0] if len(alpha) == 1 and len(digit) == 1 else f"{a}-{b}"


def grid_designations(uls_dir: Path, design: pd.DataFrame, tol: float) -> tuple[dict, str]:
    """{ETABS column label: grid ID}. Positions: 34_Column_Locations.csv, else design-table UniqueName + frame/joint tables."""
    xs, ys = grid_lines(uls_dir)
    if not xs or not ys:
        return {}, "13_Grid_Definitions has no usable X/Y grid lines (need LineType, ID, Ordinate)"
    pos: dict[str, tuple[float, float]] = {}
    loc = read_csv(uls_dir, "34_Column_Locations")
    if loc is not None and col(loc, "Label") and col(loc, "X") and col(loc, "Y"):
        for lab, x, y in zip(loc[col(loc, "Label")].map(sid), pd.to_numeric(loc[col(loc, "X")], errors="coerce"),
                             pd.to_numeric(loc[col(loc, "Y")], errors="coerce")):
            if lab and pd.notna(x) and pd.notna(y):
                pos.setdefault(lab, (float(x), float(y)))
    if not pos:
        fm, jn, uc, lc = read_csv(uls_dir, "29_Frame_Members"), read_csv(uls_dir, "14_Joint_Coordinates"), \
            col(design, "UniqueName"), col(design, "Label", "Column")
        if None not in (fm, jn) and uc and lc and col(jn, "Joint"):
            xyz = {sid(j): (x, y) for j, x, y in zip(jn[col(jn, "Joint")], jn["GlobalX"], jn["GlobalY"])}
            ij = {sid(f): sid(a) for f, a in zip(fm[col(fm, "Frame")], fm[col(fm, "JointI")])}
            for u, lab in zip(design[uc].map(sid), design[lc].map(sid)):
                if u in ij and ij[u] in xyz:
                    pos.setdefault(lab, (float(xyz[ij[u]][0]), float(xyz[ij[u]][1])))
    if not pos:
        return {}, "no column positions (34_Column_Locations.csv missing: re-run etabs_extract_tables.py)"
    out = {lab: n for lab, (x, y) in pos.items() if (n := grid_name(x, y, xs, ys, tol))}
    return out, ""


def select_ties(cfg, uls_dir: Path, sect_dims: dict, warn: list, long_dias: list, story_h: float | None,
                labels: set | None = None, tag: str = "") -> dict:
    """Tie diameter and spacings per IS 13920 ductile detailing. Spacing is restricted to --tie-spacings (75/100/125/150).
    Called once per column type: sect_dims / long_dias / labels (ETABS column labels) describe that type only."""
    allowed = sorted({int(float(x)) for x in cfg.tie_spacings.split(",") if x.strip()})
    snap = lambda x: next((s for s in reversed(allowed) if s <= x + 1e-9), None)   # largest allowed value <= x
    legs, pref_end, pref_mid = cfg.tie_legs, cfg.tie_sp_end, cfg.tie_sp_mid
    dims = list(sect_dims.values())
    least = min((min(b, d) for b, d in dims), default=300.0)
    big = max((max(b, d) for b, d in dims), default=300.0)
    # --- code limits, rounded down to an allowed spacing (NBC 105:2025 Annex A)
    smallest_bar = min(long_dias, default=16)
    limit_end = snap(min(100.0, least / 4, 8 * smallest_bar)) or allowed[0]   # cl. 4.3b: min(Bc/4, 8*db, 100)
    limit_mid = snap(min(least / 2, 16 * smallest_bar, 300.0)) or allowed[0]  # cl. 4.2.3e: least/2 (16*db, 300 from IS 13920)
    lo = int(math.ceil(max(big, (story_h * 1000 / 6) if story_h else 0.0, 450.0) / 50.0) * 50)   # l0, log only
    min_dia = max(8.0, max(long_dias, default=0) / 4)                         # cl. 4.2.3c: min 8 mm (and >= 1/4 largest bar)
    dias = [int(float(x)) for x in cfg.tie_dias.split(",") if x.strip()]
    usable = [d for d in dias if d >= min_dia] or dias[-1:]
    if len(usable) < len(dias):
        print(f"[TIES]{tag} diameters below {min_dia:g} mm skipped (>= 8 mm per NBC 105 cl. 4.2.3c, and >= 1/4 of the largest longitudinal bar)")

    def ash_req(sp: float) -> float:
        out = 0.0
        for b, d in dims:
            bc, dc = b - 2 * cfg.col_cover, d - 2 * cfg.col_cover
            if bc > 0 and dc > 0:
                out = max(out, 0.18 * sp * max(bc, dc) * (cfg.fck / cfg.fy_tie) * (b * d / (bc * dc) - 1))
        return out

    # --- shear demand (mm2 of tie legs per mm of height) from ETABS, when available
    avs, shear_src, shear_why = 0.0, None, ""
    sh_path = uls_dir / "07c_Column_Shear_Env.csv"
    sh = read_csv(uls_dir, "07c_Column_Shear_Env")
    if sh is None:
        shear_why = (f"{sh_path.name} not found in {uls_dir} (ETABS table 'Concrete Column Shear Envelope' was missing or empty; "
                     "check etabs_extract_tables.py output for [MISSING]/[EMPTY] 07c, and that concrete design has been run)")
    else:
        lc = col(sh, "Label", "Column")
        if labels is not None and lc is not None:        # shear demand of THIS column type only
            sh = sh[sh[lc].map(sid).isin(labels)]
            if sh.empty:
                shear_why = f"no rows for columns {sorted(labels, key=nat_key)} in {sh_path.name}"
        elif labels is not None:
            warn.append(f"{tag.strip() or 'ties'}: {sh_path.name} has no Label column; shear demand taken over ALL columns")
    if sh is not None and not shear_why:
        def is_av(c) -> bool:
            n = norm(c)
            if n in ("av", "avs", "avmajor", "avminor", "avmaj", "avmin", "vmajrebar", "vminrebar"):   # ETABS: VMajRebar / VMinRebar
                return True
            return n.startswith("av") and any(k in n for k in ("major", "minor", "maj", "min", "22", "33", "2", "3"))
        cols = [c for c in sh.columns if is_av(c)]
        vals = {c: pd.to_numeric(sh[c], errors="coerce").abs().max() for c in cols}
        vals = {c: v for c, v in vals.items() if pd.notna(v)}
        if not cols:
            shear_why = f"no Av column in {sh_path.name}; columns found: {list(sh.columns)}"
        elif not vals:
            shear_why = f"Av columns {cols} in {sh_path.name} hold no numeric values"
        else:
            v = max(vals.values())
            avs = (v * 1e6 if v <= 0.1 else v) / 1000      # m2/m (kN-m units) or mm2/m  ->  mm2 per mm
            shear_src = f"07c_Column_Shear_Env ({', '.join(vals)})"
            if avs <= 0:
                shear_why = f"Av in {sh_path.name} is zero for every column (ETABS reports no shear steel required)"
                shear_src = None

    trials, chosen = [], None
    for dia in usable:
        prov = legs * 3.14 * dia * dia / 4
        end_cands = [s for s in reversed(allowed) if s <= min(pref_end, limit_end)]     # largest first
        s_end = next((sp for sp in end_cands if prov >= ash_req(sp) - 1e-9), None)
        s_mid, why = None, ""
        if s_end is not None:
            top = min(pref_mid, limit_mid, (prov / avs) if avs > 0 else 1e9)
            s_mid = snap(top)
            if s_mid is None:
                why = "shear needs a mid spacing below the smallest allowed spacing"
            elif s_mid < s_end:
                s_end = s_mid            # a tighter end spacing still satisfies Ash
        else:
            why = "confinement steel Ash not met at the smallest allowed end spacing"
        ok = s_end is not None and s_mid is not None
        trials.append({"dia": dia, "provided_mm2": prov, "s_end": s_end, "s_mid": s_mid, "ok": ok, "reason": why})
        if ok and chosen is None:
            chosen = trials[-1]
    if chosen is None:
        d = usable[-1]
        chosen = {"dia": d, "provided_mm2": legs * 3.14 * d * d / 4, "s_end": allowed[0], "s_mid": allowed[0], "ok": False}
        warn.append(f"{tag.strip()} no tie diameter in {usable} works with {legs} legs at spacings {allowed}; "
                    f"{d} mm @{allowed[0]} shown - use a larger bar or more legs")
    dia, s_end, s_mid = chosen["dia"], int(chosen["s_end"]), int(chosen["s_mid"])
    text = cfg.ties or f"{dia} mm \u03c6 {legs}-legged ties @{s_end} c/c near joints and @{s_mid} c/c at mid-height"
    print(f"[TIES]{tag} {dia} mm, {legs} legs, @{s_end}/{s_mid} mm (allowed {allowed}); l0 = {lo} mm; limits: end <= {limit_end}, mid <= {limit_mid}; "
          f"Ash req {ash_req(s_end):.0f} mm2 vs {chosen['provided_mm2']:.0f} provided"
          + (f"; shear Av/s req {avs:.3f} mm2/mm ({shear_src})" if shear_src else f"; SHEAR NOT CHECKED: {shear_why}"))
    if shear_src is None:
        warn.append(f"{tag.strip()} tie spacing was not checked against shear demand: {shear_why}".strip())
    return {"text": text, "dia": dia, "legs": legs, "s_end": s_end, "s_mid": s_mid, "l0_mm": lo,
            "limit_end": limit_end, "limit_mid": limit_mid, "ash_req_mm2": ash_req(s_end),
            "shear_req_mm2_per_mm": avs, "shear_source": shear_src, "shear_not_checked_reason": shear_why or None,
            "trials": trials}


def select_column_bars(cfg, uls_dir: Path, stories: pd.DataFrame) -> tuple[dict | None, str]:
    df, src_name = None, ""
    for stem in ("07b_Column_PMM_Env", "07_Column_Design"):
        t = read_csv(uls_dir, stem)
        if t is not None and col(t, "Story") and col(t, "Label", "Column") and col(t, "RatioRebar", "RebarRatio"):
            df, src_name = t, stem
            break
    if df is None:
        return None, f"no column design table with Story / Label / RatioRebar found in {uls_dir} (07b_Column_PMM_Env, 07_Column_Design)"
    sc, lc, rc, dc = col(df, "Story"), col(df, "Label", "Column"), col(df, "RatioRebar", "RebarRatio"), col(df, "DesignSect", "Section")
    t = pd.DataFrame({"Story": df[sc].map(sid), "Label": df[lc].map(sid), "Sect": df[dc].map(sid) if dc else "",
                      "Pct": parse_percent(df[rc])}).dropna(subset=["Pct"])
    t = t[(t["Story"] != "") & (t["Label"] != "")]
    if t.empty:
        return None, f"{src_name}: no numeric required-steel values in column '{rc}'"
    g = t.groupby(["Label", "Story"], sort=False).agg(Pct=("Pct", "max"), Sect=("Sect", "first")).reset_index()

    present = list(dict.fromkeys(t["Story"]))
    top_down = [s for s in stories["Story"] if s in present] + [s for s in present if s not in set(stories["Story"])]
    floors = top_down[::-1]                                         # ground floor first
    ladder = parse_ladder(cfg.col_ladder)
    rect = read_csv(uls_dir, "22b_Frame_Sect_Rect")
    rename, grid_msg = {}, ""
    if not cfg.no_grid_names:
        rename, grid_msg = grid_designations(uls_dir, df, cfg.grid_tol)
        miss = sorted({lab for lab in g["Label"].unique() if lab not in rename}, key=nat_key)
        if grid_msg:
            print(f"[WARN] Column grid IDs not used: {grid_msg}. ETABS labels shown.")
        elif miss:
            print(f"[WARN] No grid intersection within {cfg.grid_tol} m for: {miss}. ETABS labels shown for these.")
    rename.update(dict(kv.split("=", 1) for kv in cfg.col_names.split(",") if "=" in kv))
    warn: list[str] = []
    sect_dims: dict[str, tuple[float, float]] = {}
    per_label: dict[str, dict] = {}
    for lab in sorted(g["Label"].unique(), key=nat_key):
        cells, sects = {}, []
        for st in floors:
            r = g[(g["Label"] == lab) & (g["Story"] == st)]
            if r.empty:
                cells[st] = None
                continue
            sect = r["Sect"].iloc[0]
            dims = column_dims(sect, rect)
            if dims is None:
                warn.append(f"{lab}/{st}: size of section '{sect}' unknown; bars not selected")
                cells[st] = {"sect": sect, "sel": None, "area": None, "note": "size?"}
                continue
            sect_dims[sect] = dims
            sects.append((sect, dims))
            # --- NBC 105:2025 Annex A cl. 4.2.1 dimensional checks
            b_c, d_c = dims
            min_dim, max_dim = min(b_c, d_c), max(b_c, d_c)
            if min_dim < 300:
                warn.append(f"{lab}/{st}: section {b_c:g}x{d_c:g} has min dimension {min_dim:g} mm < 300 mm (NBC 105 cl. 4.2.1b)")
            if b_c / d_c < 0.45 and d_c / b_c < 0.45:
                warn.append(f"{lab}/{st}: section {b_c:g}x{d_c:g} b/D ratio < 0.45 (NBC 105 cl. 4.2.1c, preferable)")
            # cl. 4.2.1a: min dimension >= 20*db (db = largest beam bar through the column) - checked after bars are picked
            ag = dims[0] * dims[1]
            pct = max(float(r["Pct"].iloc[0]), cfg.col_min_steel)
            req = pct / 100 * ag
            pick = next(((p, a) for p, a in ladder if a >= req), None)
            cell = {"sect": sect, "ag": ag, "etabs_pct": float(r["Pct"].iloc[0]), "req_pct": pct, "req_mm2": req,
                    "sel": pick[0] if pick else None, "area": pick[1] if pick else None}
            cell["prov_pct"] = pick[1] / ag * 100 if pick else None
            cell["ok"] = bool(pick) and cell["prov_pct"] <= cfg.col_max_steel
            # --- NBC 105:2025 cl. 4.2.2(a,d): min 8 bars (rect), min 12 mm diameter
            if pick:
                n_bars = sum(n for n, _ in pick[0])
                min_dia_long = min(dd for _, dd in pick[0])
                max_dia_long = max(dd for _, dd in pick[0])
                if n_bars < 8:
                    warn.append(f"{lab}/{st}: {bar_text(pick[0])} = {n_bars} bars < 8 minimum (NBC 105 cl. 4.2.2a)")
                if min_dia_long < 12:
                    warn.append(f"{lab}/{st}: smallest bar {min_dia_long} mm < 12 mm minimum (NBC 105 cl. 4.2.2d)")
                # cl. 4.2.1a: min column dimension >= 20*db (here using the column's own largest bar as a proxy;
                # strictly db = largest beam longitudinal bar passing through/anchoring into the column)
                if min_dim < 20 * max_dia_long:
                    warn.append(f"{lab}/{st}: min dimension {min_dim:g} mm < 20 x {max_dia_long} mm largest bar "
                                f"(NBC 105 cl. 4.2.1a; check against beam bars through this column)")
            cells[st] = cell
        tp = []
        for sect, (b, d) in sects:
            txt = f"{b:g} x {d:g}"
            if txt not in tp:
                tp.append(txt)
        per_label[lab] = {"cells": cells, "size": " / ".join(tp) or "n/a",
                          "dims": {sect: dm for sect, dm in sects}}

    def cell_key(c):
        if c is None:
            return "-"
        return bar_text(c["sel"]) if c.get("sel") else "REVISE"
    groups: dict[tuple, dict] = {}
    for lab, d in per_label.items():
        k = (d["size"], tuple(cell_key(d["cells"][s]) for s in floors))
        grp = groups.setdefault(k, {"labels": [], "etabs": [], "dims": {}, "size": d["size"], "cells": d["cells"]})
        grp["labels"].append(rename.get(lab, lab))
        grp["etabs"].append(lab)
        grp["dims"].update(d["dims"])
        for s in floors:                                     # keep the largest requirement of the group for the CSV
            a, b = grp["cells"][s], d["cells"][s]
            if a and b and a.get("req_mm2") and b.get("req_mm2") and b["req_mm2"] > a["req_mm2"]:
                grp["cells"][s] = b
    for grp in groups.values():
        grp["labels"].sort(key=nat_key)
    groups = dict(sorted(groups.items(), key=lambda kv: nat_key(kv[1]["labels"][0])))
    for i, grp in enumerate(groups.values(), 1):             # one type per distinct size + reinforcement pattern
        grp["type"] = f"C{i} ({grp['size']})"
    ok = all(c is None or c.get("ok") for d in per_label.values() for c in d["cells"].values())
    csv_rows = [{"Label": rename.get(lab, lab), "Story": st, "Section": c["sect"], "ETABS_ratio_pct": c.get("etabs_pct"),
                 "Required_pct": c.get("req_pct"), "Required_mm2": c.get("req_mm2"),
                 "Provided": bar_text(c["sel"]) if c.get("sel") else "REVISE", "Provided_mm2": c.get("area"),
                 "Provided_pct": c.get("prov_pct")}
                for lab, d in per_label.items() for st, c in d["cells"].items() if c and c.get("req_mm2") is not None]
    story_h = None
    if "Height" in stories.columns and stories["Height"].notna().any():
        story_h = float(stories["Height"].max())
    ties_all = []
    for grp in groups.values():                              # ties are selected for each column type on its own
        lab_set = set(grp["etabs"])
        dias = sorted({dd for lab in lab_set for c in per_label[lab]["cells"].values() if c and c.get("sel") for _, dd in c["sel"]})
        grp["ties"] = select_ties(cfg, uls_dir, grp["dims"], warn, dias, story_h, labels=lab_set,
                                  tag=f" {grp['type'].split(' ')[0]}")
        ties_all.append({"type": grp["type"], "labels": grp["labels"], **{k: v for k, v in grp["ties"].items() if k != "trials"}})
    return {"source": src_name, "ties": ties_all, "floors": floors, "groups": list(groups.values()), "ladder": ladder, "ok": ok,
            "warnings": warn + ([f"grid IDs not used: {grid_msg}"] if grid_msg else []), "csv": csv_rows}, ""


def render_columns(path: Path, cfg, content: dict) -> None:
    from matplotlib.patches import Rectangle
    import textwrap
    floors, groups, nf = content["floors"], content["groups"], len(content["floors"])
    NC, RH, HB, HH = nf + 3, 0.72, 0.60, 0.40
    rows = [banner("COLUMN REINFORCEMENT DETAILS", "", NC, None, h=HB),
            {"h": HH, "cells": [hcell("Desig."), hcell("Column Type")] + [hcell(floor_name(i)) for i in range(nf)] + [hcell("Ties")]}]
    for i, gr in enumerate(groups):
        bg = D_ZEBRA if i % 2 == 0 else "white"
        cells = [cell(", ".join(gr["labels"]), bg=bg, bold=True), cell(gr["type"], bg=bg)]
        for s in floors:
            c = gr["cells"][s]
            if c is None:
                cells.append(cell("\u2014", bg=bg, color=D_MUTED))
            elif c.get("sel"):
                bad = not c.get("ok")
                cells.append(cell(f"{bar_text(c['sel'])}\n({c['area']})", bg=PILL["bad"][0] if bad else bg,
                                  color=PILL["bad"][1] if bad else D_TEXT, bold=bad, size=10.5))
            else:
                cells.append(cell("Revise\nsection", bg=PILL["bad"][0], color=PILL["bad"][1], bold=True, size=10.5))
        cells.append(cell("\n".join(textwrap.wrap(gr["ties"]["text"], 30)), bg=bg, size=10))   # ties of THIS column type
        rows.append({"h": RH, "cells": cells})
    widths = [1.9, 1.7] + [1.55] * nf + [2.6]

    draw_table(rows, widths, path)


def column_reinforcement_panel(cfg, uls_dir: Path, stories: pd.DataFrame, out: Path, checks: list):
    content, msg = select_column_bars(cfg, uls_dir, stories)
    if content is None:
        checks.append(("WARN", f"Column reinforcement image skipped: {msg}."))
        print(f"[SKIP] Column reinforcement details: {msg}")
        return None
    for w in content["warnings"]:
        checks.append(("WARN", f"Column reinforcement: {w}."))
    render_columns(out, cfg, content)
    pd.DataFrame(content["csv"]).to_csv(out.with_suffix(".csv"), index=False)
    checks.append(("PASS" if content["ok"] else "FAIL",
                   f"Column bars selected from {content['source']} for {len(content['csv'])} column-story entries."))
    return content


# ----------------------------------------------------------------------------
# Panel 5: beam reinforcement details (schedule: one row per beam type)
# ----------------------------------------------------------------------------
def _is_num(s: pd.Series) -> bool:
    v = pd.to_numeric(s, errors="coerce")
    return bool(len(s)) and bool(v.notna().mean() > 0.9)


def _area_scale(*series: pd.Series) -> float:
    """ETABS (kN-m units) reports areas in m2; values above 0.1 are taken to be mm2 already."""
    mx = max((pd.to_numeric(s, errors="coerce").abs().max() for s in series), default=float("nan"))
    return 1e6 if pd.notna(mx) and mx <= 0.1 else 1.0


def _station_col(df: pd.DataFrame, exclude=()) -> str | None:
    for c in df.columns:
        if c not in exclude and norm(c) in ("station", "stationloc", "stationlocation", "distance", "location", "loc") and _is_num(df[c]):
            return c
    return None


def _parse_beam_flexure(df: pd.DataFrame, lab: str, st: str, sect: str | None) -> tuple[pd.DataFrame | None, str]:
    """Standardise a beam flexure table to Story, Label, Sect, Station, Top, Bot (mm2).
    Handles a wide layout (top / bottom area columns) and a long layout (a Top/Bot location column + one area column)."""
    bad = ("combo", "ratio", "min", "max", "prov", "moment", "mu", "vu", "pu")
    area_like = lambda c: (norm(c).startswith("as") or "area" in norm(c) or "rebar" in norm(c)) and not any(b in norm(c) for b in bad)
    cands = [c for c in df.columns if area_like(c) and c not in (lab, st, sect)]
    top = [c for c in cands if "top" in norm(c)]
    bot = [c for c in cands if "bot" in norm(c)]
    base = {"Story": df[st].map(sid), "Label": df[lab].map(sid), "Sect": df[sect].map(sid) if sect else ""}
    if top and bot:
        sta = _station_col(df)
        k = _area_scale(df[top[0]], df[bot[0]])
        out = pd.DataFrame({**base, "Station": pd.to_numeric(df[sta], errors="coerce") if sta else float("nan"),
                            "Top": pd.to_numeric(df[top[0]], errors="coerce").abs() * k,
                            "Bot": pd.to_numeric(df[bot[0]], errors="coerce").abs() * k})
        return out, ""
    locc = None
    for c in df.columns:
        if c in (lab, st, sect) or _is_num(df[c]):
            continue
        vals = df[c].astype(str).str.strip().str.lower()
        if vals.str.startswith("top").any() and vals.str.startswith("bot").any():
            locc = c
            break
    rest = [c for c in cands if c != locc]
    if locc is None or not rest:
        return None, f"cannot find top/bottom required steel; columns found: {list(df.columns)}"
    pref = ("asreq", "reqrebar", "rebararea", "arearequired", "areareq", "area", "as", "rebar")
    area = next((c for p in pref for c in rest if norm(c) == p), rest[0])
    sta = _station_col(df, exclude=(locc,))
    k = _area_scale(df[area])
    v = pd.to_numeric(df[area], errors="coerce").abs() * k
    isT = df[locc].astype(str).str.strip().str.lower().str.startswith("top")
    out = pd.DataFrame({**base, "Station": pd.to_numeric(df[sta], errors="coerce") if sta else float("nan"),
                        "Top": v.where(isT), "Bot": v.where(~isT)})
    return out, ""


def read_beam_flexure(uls_dir: Path) -> tuple[pd.DataFrame | None, str, str]:
    why = f"no beam design table (08b_Beam_Flexure_Env, 08_Beam_Design) found in {uls_dir}"
    for stem in ("08b_Beam_Flexure_Env", "08_Beam_Design"):
        df = read_csv(uls_dir, stem)
        if df is None:
            continue
        lab, st, sect = col(df, "Beam", "Label"), col(df, "Story"), col(df, "DesignSect", "Section")
        if lab is None or st is None:
            why = f"{stem}: no Story / Beam (Label) column; columns found: {list(df.columns)}"
            continue
        out, msg = _parse_beam_flexure(df, lab, st, sect)
        if out is not None and (out["Top"].notna().any() or out["Bot"].notna().any()):
            return out[(out["Label"] != "") & (out["Story"] != "")], stem, ""
        why = f"{stem}: {msg or 'no numeric required steel'}"
    return None, "", why


def read_beam_shear(uls_dir: Path) -> tuple[pd.DataFrame | None, str]:
    """Required stirrup steel per unit length (mm2/mm) per beam, story, station."""
    df = read_csv(uls_dir, "08c_Beam_Shear_Env")
    if df is None:
        return None, "08c_Beam_Shear_Env.csv not found (ETABS table 'Concrete Beam Shear Envelope' missing or empty)"
    lab, st = col(df, "Beam", "Label"), col(df, "Story")
    if lab is None or st is None:
        return None, f"08c_Beam_Shear_Env: no Story / Beam column; columns found: {list(df.columns)}"
    cols = [c for c in df.columns if norm(c) in ("vrebar", "avrebar", "avs", "av", "avmajor", "avminor")
            or (("rebar" in norm(c)) and norm(c).startswith(("v", "av")) and "combo" not in norm(c))]
    if not cols:
        return None, f"08c_Beam_Shear_Env: no stirrup-steel column (VRebar); columns found: {list(df.columns)}"
    v = pd.concat([pd.to_numeric(df[c], errors="coerce").abs() for c in cols], axis=1).max(axis=1)
    mx = v.max()
    avs = (v * 1e6 if pd.notna(mx) and mx <= 0.1 else v) / 1000          # m2/m or mm2/m  ->  mm2 per mm
    sta = _station_col(df)
    return pd.DataFrame({"Story": df[st].map(sid), "Label": df[lab].map(sid),
                         "Station": pd.to_numeric(df[sta], errors="coerce") if sta else float("nan"), "AvS": avs}), ""


def _mark_ends(df: pd.DataFrame, frac_end: float) -> pd.DataFrame:
    """End = within frac_end of either support along the beam; Mid = the rest. Without stations every row is both."""
    df = df.copy()
    df["End"], df["Mid"] = True, True
    if "Station" in df and df["Station"].notna().any():
        g = df.groupby(["Label", "Story"])["Station"]
        span = g.transform("max") - g.transform("min")
        f = (df["Station"] - g.transform("min")) / span.where(span > 0)
        ok = f.notna()
        near = (f <= frac_end + 1e-9) | (f >= 1 - frac_end - 1e-9)
        df.loc[ok, "End"] = near[ok]
        df.loc[ok, "Mid"] = ~near[ok]
    return df


def select_beam_details(cfg, uls_dir: Path, stories: pd.DataFrame) -> tuple[dict | None, str]:
    fl, src_name, msg = read_beam_flexure(uls_dir)
    if fl is None:
        return None, msg
    sh, sh_msg = read_beam_shear(uls_dir)
    warn: list[str] = []
    if sh is None:
        warn.append(f"stirrups sized from ductile-detailing and minimum-steel limits only; shear demand unavailable: {sh_msg}")
    fl = _mark_ends(fl, cfg.beam_end_frac)
    if sh is not None:
        sh = _mark_ends(sh, cfg.beam_end_frac)
    rect = read_csv(uls_dir, "22b_Frame_Sect_Rect")
    ladder = parse_ladder(cfg.beam_ladder)
    min_bars = getattr(cfg, "beam_min_bars", 3)
    # Through bars must have at least --beam-min-bars bars (they run the whole beam); extra bars can be fewer
    through_ladder = [(p, a) for p, a in ladder if sum(n for n, _ in p) >= min_bars] or ladder
    rename = dict(kv.split("=", 1) for kv in cfg.beam_names.split(",") if "=" in kv)
    cant_labels = {s.strip() for s in cfg.beam_cantilevers.split(",") if s.strip()} if getattr(cfg, "beam_cantilevers", "") else set()
    allowed = sorted({int(float(x)) for x in cfg.beam_tie_spacings.split(",") if x.strip()})
    # snap_down: largest allowed value <= x (code-strict, used for the code limit itself)
    snap_down = lambda x: next((s for s in reversed(allowed) if s <= x + 1e-9), None)
    # snap_near: NEAREST allowed value to x (practical, what engineers do manually; e.g. snap_near(96)=100, not 75)
    snap_near = lambda x: min(allowed, key=lambda s: abs(s - x)) if allowed and x is not None else None
    snap = snap_near   # beam stirrups use nearest (practical rounding, not round-down)
    dias = [int(float(x)) for x in cfg.beam_tie_dias.split(",") if x.strip()]
    dias = [d for d in dias if d >= 6] or dias[-1:]
    legs = cfg.beam_legs
    present = list(dict.fromkeys(fl["Story"]))
    top_down = [s for s in stories["Story"] if s in present] + [s for s in present if s not in set(stories["Story"])]
    floors = top_down[::-1]                                                  # lowest beam level first

    def pick(req):
        return next(((p, a) for p, a in ladder if a >= req), None)

    def pick_through(req):
        """Pick through bars from the filtered ladder (>= --beam-min-bars)."""
        return next(((p, a) for p, a in through_ladder if a >= req), None)

    def pick_through_extra(through_req, total_req, ast_min_v, cap_v):
        """Pick THROUGH bars (continuous along the whole beam, marked 'Th.') and EXTRA bars
        (additional at the supports only, marked 'Ex.').

        Through meets: max(through_req, ast_min_v, 0.25 * cap_v)   (IS 13920 cl. 6.2.2: any section >= 25 % of the larger support steel)
        Through + extra meets: total_req                            (the support requirement)

        Returns dict with keys: through (parts|None), through_area (int|None),
        extra (parts|[]|None), extra_area (int|0|None), ok (bool), reason (str).
        `extra == []`  means no extra is needed (through already meets total_req);
        `extra is None` means extra IS needed but no ladder combination covers it (REVISE)."""
        th_req = max(through_req, ast_min_v, 0.25 * cap_v)
        th = pick_through(th_req)
        if th is None:
            return {"through": None, "through_area": None, "extra": None, "extra_area": None,
                    "ok": False, "reason": f"no through ladder combination (>= {min_bars} bars) meets the through requirement"}
        if th[1] >= total_req:
            return {"through": th[0], "through_area": th[1], "extra": [], "extra_area": 0, "ok": True}
        ex_req = total_req - th[1]
        ex = pick(ex_req)
        if ex is None:
            return {"through": th[0], "through_area": th[1], "extra": None, "extra_area": None,
                    "ok": False, "reason": f"no ladder combination meets the extra requirement ({ex_req:.0f} mm2)"}
        return {"through": th[0], "through_area": th[1], "extra": ex[0], "extra_area": ex[1], "ok": True}

    entries: list[dict] = []
    for (lab, st), g in fl.groupby(["Label", "Story"], sort=False):
        sect = next((s for s in g["Sect"] if s), "")
        dims = column_dims(sect, rect)
        if dims is None:
            warn.append(f"{lab}/{st}: size of section '{sect}' unknown; bars not selected")
            continue
        b, D = dims
        d = D - cfg.beam_cover
        # --- NBC 105:2025 Annex A cl. 4.1.1 dimensional checks
        if b < 200:
            warn.append(f"{lab}/{st}: beam width {b:g} mm < 200 mm (NBC 105 cl. 4.1.1b)")
        if b / D < 0.3:
            warn.append(f"{lab}/{st}: beam b/D = {b/D:.2f} < 0.3 (NBC 105 cl. 4.1.1a)")
        # cl. 4.1.1c: D <= L/4 (clear span) - checked if station data gives span
        if "Station" in g.columns and g["Station"].notna().any():
            span = float(g["Station"].max() - g["Station"].min())
            if span > 0 and D > span / 4:
                warn.append(f"{lab}/{st}: beam D={D:g} mm > L/4={span/4:.0f} mm (NBC 105 cl. 4.1.1c)")
        mx = lambda s: float(s.max()) if s.notna().any() else 0.0
        t_end, t_mid = mx(g.loc[g["End"], "Top"]), mx(g.loc[g["Mid"], "Top"])
        b_end, b_mid = mx(g.loc[g["End"], "Bot"]), mx(g.loc[g["Mid"], "Bot"])
        ast_min = 0.24 * math.sqrt(cfg.fck) / cfg.fy_long * b * d
        # --- Total at supports (with IS 13920 minimums); used to compute cap (larger support steel)
        te_req = max(t_end, ast_min)
        te = pick(te_req)
        be_req = max(b_end, 0.5 * (te[1] if te else te_req), ast_min)           # IS 13920: bot at joint face >= 50 % of top
        be = pick(be_req)
        cap = max(te[1] if te else te_req, be[1] if be else be_req)
        # --- Through (continuous) + Extra (at supports only) for top and bottom
        top_te = pick_through_extra(t_mid, te_req, ast_min, cap)
        bot_te = pick_through_extra(b_mid, be_req, ast_min, cap)
        # --- NBC 105:2025 cl. 4.1.2(a) + project preference: at least --beam-min-bars (default 3) bars, each >= 12 mm
        for face, te in (("top", top_te), ("bot", bot_te)):
            th = te.get("through")
            if th:
                n_bars_through = sum(n for n, _ in th)
                min_dia_through = min(dd for _, dd in th)
                if n_bars_through < min_bars or min_dia_through < 12:
                    warn.append(f"{lab}/{st}: {face} through bars {beam_bar_text(th)} = {n_bars_through}x{min_dia_through}mm; "
                                f"need >= {min_bars} bars of >= 12 mm (cl. 4.1.2a + --beam-min-bars)")
        sel = {
            "top_through": top_te["through"], "top_through_area": top_te["through_area"],
            "top_extra": top_te["extra"], "top_extra_area": top_te["extra_area"],
            "bot_through": bot_te["through"], "bot_through_area": bot_te["through_area"],
            "bot_extra": bot_te["extra"], "bot_extra_area": bot_te["extra_area"],
        }
        reqs = {"top_through_req": max(t_mid, ast_min), "top_total_req": te_req,
                "bot_through_req": max(b_mid, ast_min), "bot_total_req": be_req}
        top_total = (top_te["through_area"] or 0) + (top_te["extra_area"] or 0 if top_te["extra"] else 0)
        bot_total = (bot_te["through_area"] or 0) + (bot_te["extra_area"] or 0 if bot_te["extra"] else 0)
        ok = (top_te["ok"] and bot_te["ok"]
              and top_total / (b * d) * 100 <= cfg.beam_max_steel
              and bot_total / (b * d) * 100 <= cfg.beam_max_steel)
        # --- Smallest longitudinal bar diameter (for the stirrup spacing limits)
        all_dias = []
        for v in (top_te["through"], bot_te["through"]):
            if v: all_dias.extend([dd for _, dd in v])
        for v in (top_te["extra"], bot_te["extra"]):
            if v: all_dias.extend([dd for _, dd in v])
        dm = min(all_dias, default=16)
        # Raw code limits (NOT pre-snapped): end <= min(d/4, 8*db, 100), mid <= min(d/2, 300)
        lim_end_raw = min(d / 4, cfg.beam_hoop_mult * dm, 100.0)
        lim_mid_raw = min(d / 2, 300.0)
        avs_min = 0.4 * b / (0.87 * cfg.fy_tie)                                 # IS 456 cl. 26.5.1.6 minimum shear steel
        s_end_d = s_mid_d = 0.0
        if sh is not None:
            q = sh[(sh["Label"] == lab) & (sh["Story"] == st)]
            if not q.empty:
                s_end_d = float(q.loc[q["End"], "AvS"].max()) if q["End"].any() else 0.0
                s_mid_d = float(q.loc[q["Mid"], "AvS"].max()) if q["Mid"].any() else 0.0
        s_end_d, s_mid_d = max(s_end_d if pd.notna(s_end_d) else 0.0, avs_min), max(s_mid_d if pd.notna(s_mid_d) else 0.0, avs_min)
        is_cant = lab in cant_labels
        chosen = None
        for dia in dias:
            prov = legs * 3.14 * dia * dia / 4
            # Code limit: snap_near (practical rounding, e.g. 96 -> 100)
            se_code = snap_near(lim_end_raw)
            sm_code = snap_near(lim_mid_raw)
            # Shear limit: snap_down (STRICT — spacing must be <= prov/demand, never round up)
            # Returns None if even the smallest allowed spacing doesn't satisfy shear -> try bigger bar
            se_shear = snap_down(prov / s_end_d) if s_end_d > 0 else None
            sm_shear = snap_down(prov / s_mid_d) if s_mid_d > 0 else None
            # Final spacing = the MORE RESTRICTIVE of code and shear (min of the two)
            # If shear returns None (bar too small), skip this diameter and try the next one
            if se_shear is not None:
                se = min(se_code, se_shear) if se_code is not None else se_shear
            elif s_end_d > 0:
                continue  # 8mm doesn't work for shear, try 10mm
            else:
                se = se_code
            if is_cant:
                sm = se  # cantilever: entire span is end zone, no mid-span relaxation
            elif sm_shear is not None:
                sm = min(sm_code, sm_shear) if sm_code is not None else sm_shear
            elif s_mid_d > 0:
                continue  # shear not satisfied at this diameter
            else:
                sm = sm_code
            if se is not None and sm is not None:
                chosen = (dia, se, sm)
                break
        stir_ok = chosen is not None
        if chosen is None:
            chosen = (dias[-1], allowed[0], allowed[0])
        entries.append({"label": lab, "story": st, "sect": sect, "b": b, "D": D, "d": d, "sel": sel, "req": reqs,
                        "ok": ok and stir_ok, "stir": chosen, "stir_ok": stir_ok, "legs": legs,
                        "is_cantilever": is_cant,
                        "avs_end": s_end_d, "avs_mid": s_mid_d,
                        "lim_end_raw": lim_end_raw, "lim_mid_raw": lim_mid_raw,
                        "lim_end": snap_down(lim_end_raw) or allowed[0],
                        "lim_mid": snap_down(lim_mid_raw) or allowed[0]})
    if not entries:
        return None, f"{src_name}: no beam with a known section size"

    # --- Filter out beams smaller than --beam-min-size x --beam-min-size (default 230 x 230 mm)
    min_size = getattr(cfg, "beam_min_size", 230)
    filtered = [e for e in entries if min(e["b"], e["D"]) >= min_size]
    skipped = [e for e in entries if min(e["b"], e["D"]) < min_size]
    if skipped:
        skipped_labels = sorted({f"{e['label']}/{e['story']} ({e['b']:g}x{e['D']:g})" for e in skipped}, key=nat_key)
        print(f"[SKIP] {len(skipped)} beam-story entr{'y' if len(skipped)==1 else 'ies'} smaller than {min_size:g}x{min_size:g} mm ignored: {skipped_labels}")
    if not filtered:
        return None, f"{src_name}: no beam >= {min_size:g}x{min_size:g} mm found"
    entries = filtered

    th_ex_text = lambda th, ex: bar_text_th_ex(th, ex)
    mid_text = lambda th: ("REVISE" if th is None else f"({beam_bar_text(th)})")
    def stir_text(e):
        if cfg.beam_ties:
            return cfg.beam_ties
        return f"{e['legs']}L-{e['stir'][0]}mm\u03c6 @{e['stir'][1]}mm near joints, @{e['stir'][2]}mm at mid-span"
    # --- Group PER FLOOR: each floor gets its own set of beam types (B1, B2, ... on that floor).
    # The group key includes the story so beams on different floors are never merged into one row.
    groups: dict[tuple, dict] = {}
    for e in entries:
        size = f"{e['b']:g} x {e['D']:g}"
        s = e["sel"]
        st = e["story"]
        k = (st,
             size,
             th_ex_text(s["top_through"], s["top_extra"]),
             mid_text(s["top_through"]),
             th_ex_text(s["bot_through"], s["bot_extra"]),
             mid_text(s["bot_through"]),
             stir_text(e))
        grp = groups.setdefault(k, {"size": size, "b": e["b"], "D": e["D"], "sel": e["sel"], "ties": stir_text(e),
                                    "labels": [], "story": st, "ok": True})
        grp["labels"].append(rename.get(e["label"], e["label"]))
        grp["ok"] = grp["ok"] and e["ok"]
    for grp in groups.values():
        grp["labels"] = sorted(set(grp["labels"]), key=nat_key)
    # --- Order: lowest floor first, then LARGEST DEPTH FIRST (D desc, then b desc), then by first label
    ordered = sorted(groups.values(),
                     key=lambda gr: (floors.index(gr["story"]) if gr["story"] in floors else 99,
                                     -gr["D"], -gr["b"], nat_key(gr["labels"][0])))
    # --- Type numbering: B1, B2, ... PER FLOOR (each floor restarts at B1)
    type_counter: dict[str, int] = {}
    for grp in ordered:
        st = grp["story"]
        type_counter[st] = type_counter.get(st, 0) + 1
        grp["type"] = f"B{type_counter[st]}"
    csv_rows = []
    for e in entries:
        s = e["sel"]
        # Find the group this entry belongs to (match by story + bars + size + ties)
        st = e["story"]
        size = f"{e['b']:g} x {e['D']:g}"
        e_key = (st, size, th_ex_text(s["top_through"], s["top_extra"]), mid_text(s["top_through"]),
                 th_ex_text(s["bot_through"], s["bot_extra"]), mid_text(s["bot_through"]), stir_text(e))
        beam_type = groups[e_key]["type"] if e_key in groups else "?"
        row = {"Label": rename.get(e["label"], e["label"]), "Type": beam_type,
               "Story": st, "Section": e["sect"], "b_mm": e["b"], "D_mm": e["D"]}
        row["top_through_req_mm2"] = e["req"]["top_through_req"]
        row["top_total_req_mm2"] = e["req"]["top_total_req"]
        row["bot_through_req_mm2"] = e["req"]["bot_through_req"]
        row["bot_total_req_mm2"] = e["req"]["bot_total_req"]
        row["top_through"] = beam_bar_text(s["top_through"]) if s["top_through"] else "REVISE"
        row["top_through_mm2"] = s["top_through_area"]
        row["top_extra"] = beam_bar_text(s["top_extra"]) if s["top_extra"] else ("" if s["top_extra"] == [] else "REVISE")
        row["top_extra_mm2"] = s["top_extra_area"] if s["top_extra"] else 0
        row["bot_through"] = beam_bar_text(s["bot_through"]) if s["bot_through"] else "REVISE"
        row["bot_through_mm2"] = s["bot_through_area"]
        row["bot_extra"] = beam_bar_text(s["bot_extra"]) if s["bot_extra"] else ("" if s["bot_extra"] == [] else "REVISE")
        row["bot_extra_mm2"] = s["bot_extra_area"] if s["bot_extra"] else 0
        row.update({"stirrup_dia_mm": e["stir"][0], "stirrup_legs": e["legs"], "s_end_mm": e["stir"][1], "s_mid_mm": e["stir"][2],
                    "Av_per_s_end_req_mm2_per_mm": e["avs_end"], "Av_per_s_mid_req_mm2_per_mm": e["avs_mid"],
                    "is_cantilever": e.get("is_cantilever", False)})
        csv_rows.append(row)
    # --- Cantilever note: if cantilever beams need a different (bigger bar / tighter spacing) stirrup
    # than the regular beams, prepare a note to show at the bottom of the table.
    cant_entries = [e for e in entries if e.get("is_cantilever")]
    reg_entries = [e for e in entries if not e.get("is_cantilever")]
    cant_note = None
    if cant_entries:
        # Governing cantilever stirrup = biggest diameter, then tightest end spacing
        gov_cant = max(cant_entries, key=lambda e: (e["stir"][0], -e["stir"][1]))
        cant_dia, cant_s_end = gov_cant["stir"][0], gov_cant["stir"][1]
        cant_legs = gov_cant["legs"]
        if reg_entries:
            # Regular stirrup = smallest diameter, then widest end spacing (the "lightest" regular stirrup)
            gov_reg = min(reg_entries, key=lambda e: (e["stir"][0], -e["stir"][1]))
            reg_dia, reg_s_end = gov_reg["stir"][0], gov_reg["stir"][1]
        else:
            reg_dia, reg_s_end = 0, 9999
        # Note only if cantilever needs a bigger bar OR tighter spacing than regular
        if cant_dia > reg_dia or cant_s_end < reg_s_end:
            cant_note = f"All cantilever portions: {cant_legs}L-{cant_dia}mm\u03c6 @{cant_s_end}mm c/c"
        elif reg_entries:
            # Same stirrup but cantilever uses end-zone spacing throughout (no mid-span relaxation)
            cant_note = f"All cantilever portions: {cant_legs}L-{cant_dia}mm\u03c6 @{cant_s_end}mm c/c (same as end zone)"
    return {"source": src_name, "shear_source": None if sh is None else "08c_Beam_Shear_Env", "floors": floors,
            "groups": ordered, "ok": all(e["ok"] for e in entries), "warnings": warn, "csv": csv_rows,
            "cantilever_note": cant_note}, ""


def render_beams(path: Path, cfg, content: dict) -> None:
    import textwrap
    groups = content["groups"]
    NC, HB, HH = 8, 0.60, 0.55
    heads = ["Beam\nType", "Size\n(b x D)", "Floor",
             "Top Reinf.\nAt Support", "Top Reinf.\nAt Mid",
             "Bot. Reinf.\nAt Support", "Bot. Reinf.\nAt Mid", "Stirrups"]
    rows = [banner("BEAM REINFORCEMENT DETAILS", "", NC, None, h=HB),
            {"h": HH, "cells": [hcell(h) for h in heads]}]
    wrap = lambda t, n: textwrap.wrap(t, n) or [""]

    def support_cell(sel, which, b, D, bg):
        """At-Support cell: '(through)(Th.)\\n+(extra)(Ex.)\\n(total_area)' matching the reference sheet."""
        th = sel[f"{which}_through"]
        ex = sel[f"{which}_extra"]
        th_area = sel[f"{which}_through_area"] or 0
        ex_area = sel[f"{which}_extra_area"] if sel[f"{which}_extra_area"] else 0
        total_area = th_area + (ex_area or 0)
        if th is None:
            return cell("Revise\nsection", bg=PILL["bad"][0], color=PILL["bad"][1], bold=True, size=10.5), 2
        # Bad if: extra needed but not pickable, OR total exceeds max steel
        bad = (ex is None) or (total_area / (b * (D - cfg.beam_cover)) * 100 > cfg.beam_max_steel)
        text = bar_text_th_ex(th, ex) + f"\n({total_area})"
        n_lines = text.count("\n") + 1
        return cell(text, bg=PILL["bad"][0] if bad else bg,
                    color=PILL["bad"][1] if bad else D_TEXT, bold=bad, size=10), n_lines

    def mid_cell(sel, which, b, D, bg):
        """At-Mid cell: '(through)\\n(through_area)' - only the continuous bars run at mid-span."""
        th = sel[f"{which}_through"]
        th_area = sel[f"{which}_through_area"] or 0
        if th is None:
            return cell("Revise\nsection", bg=PILL["bad"][0], color=PILL["bad"][1], bold=True, size=10.5), 2
        bad = th_area / (b * (D - cfg.beam_cover)) * 100 > cfg.beam_max_steel
        text = f"({beam_bar_text(th)})\n({th_area})"
        return cell(text, bg=PILL["bad"][0] if bad else bg,
                    color=PILL["bad"][1] if bad else D_TEXT, bold=bad, size=10), 2

    for i, gr in enumerate(groups):
        bg = D_ZEBRA if i % 2 == 0 else "white"
        ties = wrap(gr["ties"], 28)
        s = gr["sel"]
        cells = [cell(gr["type"], bg=bg, bold=True), cell(gr["size"], bg=bg),
                 cell(gr["story"], bg=bg, size=10)]
        max_lines = max(len(ties), 2)
        for which in ("top", "bot"):
            sc, sc_lines = support_cell(s, which, gr["b"], gr["D"], bg)
            cells.append(sc)
            mc, mc_lines = mid_cell(s, which, gr["b"], gr["D"], bg)
            cells.append(mc)
            max_lines = max(max_lines, sc_lines, mc_lines)
        cells.append(cell("\n".join(ties), bg=bg, size=10))
        rows.append({"h": max(0.80, 0.19 * max_lines + 0.30), "cells": cells})
    # --- Cantilever note at the bottom (if cantilever beams need different stirrups)
    cant_note = content.get("cantilever_note")
    if cant_note:
        rows.append({"h": 0.45, "cells": [scell(cant_note, NC)]})
    draw_table(rows, [0.85, 1.40, 1.30, 1.80, 1.45, 1.80, 1.45, 2.55], path)


def beam_reinforcement_panel(cfg, uls_dir: Path, stories: pd.DataFrame, out: Path, checks: list):
    content, msg = select_beam_details(cfg, uls_dir, stories)
    if content is None:
        checks.append(("WARN", f"Beam reinforcement image skipped: {msg}."))
        print(f"[SKIP] Beam reinforcement details: {msg}")
        return None
    for w in content["warnings"]:
        checks.append(("WARN", f"Beam reinforcement: {w}."))
        print(f"[WARN] Beams: {w}")
    render_beams(out, cfg, content)
    pd.DataFrame(content["csv"]).to_csv(out.with_suffix(".csv"), index=False)
    checks.append(("PASS" if content["ok"] else "FAIL",
                   f"Beam bars and stirrups selected from {content['source']} for {len(content['csv'])} beam-story entries "
                   f"in {len(content['groups'])} beam types."))
    return content


# ----------------------------------------------------------------------------
# Panels 6 and 7: beam layout plan and column layout plan (one plan per floor)
# ----------------------------------------------------------------------------
BEAM_TYPE_COLORS = ["#2F5D8C", "#C0504D", "#4F9D5D", "#E39B2D", "#7B5EA7", "#2BA3A3", "#8C6D3F", "#D2527F"]


def _plan_inputs(uls_dir: Path):
    """Joint XY, frame members and (story, label) -> frames lookups for the plan drawings."""
    jn, fm, fa = read_csv(uls_dir, "14_Joint_Coordinates"), read_csv(uls_dir, "29_Frame_Members"), \
        read_csv(uls_dir, "17_Frame_Assignments")
    if jn is None or fm is None or fa is None:
        return None, "need 14_Joint_Coordinates, 29_Frame_Members and 17_Frame_Assignments (re-run etabs_extract_tables.py)"
    jc, jx, jy = col(jn, "Joint"), col(jn, "GlobalX"), col(jn, "GlobalY")
    fc, ic, jjc, fs = col(fm, "Frame"), col(fm, "JointI"), col(fm, "JointJ"), col(fm, "Story")
    ls, ll, lu = col(fa, "Story"), col(fa, "Label"), col(fa, "UniqueName")
    if None in (jc, jx, jy, fc, ic, jjc, fs, ls, ll, lu):
        return None, "unexpected column names in the joint / frame tables"
    xy = {sid(j): (float(x), float(y)) for j, x, y in zip(jn[jc], jn[jx], jn[jy])}
    ends = {(sid(st), sid(f)): (sid(a), sid(b)) for f, a, b, st in zip(fm[fc], fm[ic], fm[jjc], fm[fs])}
    by_label: dict[tuple[str, str], list[str]] = {}
    for st, lab, u in zip(fa[ls], fa[ll], fa[lu]):
        by_label.setdefault((sid(st), sid(lab)), []).append(sid(u))
    return {"xy": xy, "ends": ends, "by_label": by_label}, ""


def _draw_grid(ax, xs: list, ys: list, x0: float, y0: float, x1: float, y1: float, m: float = 0.55) -> None:
    for o, name in xs:
        ax.plot([o, o], [y0 - m, y1 + m], color="#9AA7B8", lw=0.5, ls=(0, (6, 3)), zorder=1)
        ax.text(o, y0 - m - 0.28, name, ha="center", va="center", fontsize=6.5, color=D_INK, zorder=6,
                bbox=dict(boxstyle="circle,pad=0.25", fc="white", ec=D_INK, lw=0.6))
    for o, name in ys:
        ax.plot([x0 - m, x1 + m], [o, o], color="#9AA7B8", lw=0.5, ls=(0, (6, 3)), zorder=1)
        ax.text(x0 - m - 0.28, o, name, ha="center", va="center", fontsize=6.5, color=D_INK, zorder=6,
                bbox=dict(boxstyle="circle,pad=0.25", fc="white", ec=D_INK, lw=0.6))


def _with_grid(bounds: tuple, xs: list, ys: list) -> tuple:
    """Widen (x0, y0, x1, y1) so every grid line (and its bubble) lies inside the plan."""
    x0, y0, x1, y1 = bounds
    if xs:
        x0, x1 = min(x0, min(o for o, _ in xs)), max(x1, max(o for o, _ in xs))
    if ys:
        y0, y1 = min(y0, min(o for o, _ in ys)), max(y1, max(o for o, _ in ys))
    return x0, y0, x1, y1


def _plan_canvas(title: str, sub: str, floors: list[str], bounds: tuple, pad: float = 1.6):
    """Navy title band + one axes per floor. Returns (fig, {floor: ax})."""
    import math as _m
    x0, y0, x1, y1 = bounds
    w, h = (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
    n = len(floors)
    ncols = min(n, 3)
    nrows = _m.ceil(n / ncols)
    axw = (PANEL_W - 0.3) / ncols
    axh = min(max(axw * h / w, 2.2), 7.5)
    band, leg = 0.8, 0.75
    H = band + nrows * (axh + leg + 0.25) + 0.1
    fig = plt.figure(figsize=(PANEL_W, H), dpi=DPI, facecolor="white")
    bx = fig.add_axes([0, 1 - band / H, 1, band / H]); bx.set_facecolor(D_BAND); bx.set_xticks([]); bx.set_yticks([])
    for sp in bx.spines.values():
        sp.set_visible(False)
    bx.text(0.02, 0.62, title, color="white", fontsize=15, fontweight="bold", va="center", transform=bx.transAxes, family=_font())
    bx.text(0.02, 0.2, sub, color=D_BAND_SUB, fontsize=8, va="center", transform=bx.transAxes, family=_font())
    axes = {}
    for i, fl in enumerate(floors):
        r, c = divmod(i, ncols)
        left = 0.15 / PANEL_W + c * axw / PANEL_W
        bottom = 1 - (band + (r + 1) * (axh + leg + 0.25) - leg) / H
        ax = fig.add_axes([left, bottom, axw / PANEL_W - 0.1 / PANEL_W, axh / H])
        ax.set_xlim(x0 - pad, x1 + pad); ax.set_ylim(y0 - pad, y1 + pad); ax.set_aspect("equal", adjustable="box")
        ax.axis("off")
        ax.set_title(fl.upper(), fontsize=10, fontweight="bold", color=D_INK, family=_font(), pad=4,
                     loc="left", bbox=dict(fc=D_HEAD, ec="none", pad=3))
        axes[fl] = ax
    return fig, axes


def beam_layout_plan(cfg, uls_dir: Path, content: dict, stories: pd.DataFrame, out: Path, checks: list):
    """Plan of every floor with each beam drawn and labelled with its type (B1, B2, ...) from the beam table."""
    geo, msg = _plan_inputs(uls_dir)
    if geo is None:
        checks.append(("WARN", f"Beam layout plan skipped: {msg}."))
        print(f"[SKIP] Beam layout plan: {msg}")
        return None
    inv = {v: k for k, v in (kv.split("=", 1) for kv in cfg.beam_names.split(",") if "=" in kv)}
    rows = pd.DataFrame(content["csv"])
    floors = list(content["floors"])
    segs: dict[str, list] = {f: [] for f in floors}
    types: dict[str, dict] = {f: {} for f in floors}
    xy, miss = geo["xy"], 0
    for r in rows.itertuples():
        for u in geo["by_label"].get((str(r.Story), inv.get(str(r.Label), str(r.Label))), []):
            e = geo["ends"].get((str(r.Story), u))
            if e and e[0] in xy and e[1] in xy:
                segs[str(r.Story)].append((xy[e[0]], xy[e[1]], str(r.Type), str(r.Label), bool(r.is_cantilever)))
                types[str(r.Story)].setdefault(str(r.Type), f"{r.b_mm:g} x {r.D_mm:g}")
            else:
                miss += 1
    pts = [pt for f in floors for a, b, *_ in segs[f] for pt in (a, b)]
    loc = read_csv(uls_dir, "34_Column_Locations")
    colpts = {}
    if loc is not None and col(loc, "Story") and col(loc, "X") and col(loc, "Y"):
        for st, x, y in zip(loc[col(loc, "Story")].map(sid), pd.to_numeric(loc[col(loc, "X")], errors="coerce"),
                            pd.to_numeric(loc[col(loc, "Y")], errors="coerce")):
            if pd.notna(x) and pd.notna(y):
                colpts.setdefault(st, []).append((float(x), float(y)))
        pts += [p for v in colpts.values() for p in v]
    if not pts:
        checks.append(("WARN", "Beam layout plan skipped: no beam geometry found for the beams in the table."))
        print("[SKIP] Beam layout plan: no beam geometry matched the beam table")
        return None
    bounds = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
    xs, ys = grid_lines(uls_dir)
    bounds = _with_grid(bounds, xs, ys)
    fig, axes = _plan_canvas("BEAM LAYOUT PLAN", "Beam types as in the Beam Reinforcement Details table (size b x D in mm)",
                             floors, bounds)
    from matplotlib.lines import Line2D
    for fl, ax in axes.items():
        _draw_grid(ax, xs, ys, *bounds)
        for (a, b, t, lab, cant) in segs[fl]:
            k = int(re.sub(r"\D", "", t) or 1) - 1
            colr = BEAM_TYPE_COLORS[k % len(BEAM_TYPE_COLORS)]
            ax.plot([a[0], b[0]], [a[1], b[1]], color=colr, lw=3.2, solid_capstyle="butt", zorder=3,
                    ls=(0, (4, 1.2)) if cant else "-")
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            ax.text(mx, my, t, ha="center", va="center", fontsize=6.3, fontweight="bold", color=colr, zorder=5,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.92))
        half = 0.355 / 2
        for (x, y) in colpts.get(fl, []):
            ax.add_patch(plt.Rectangle((x - half, y - half), 2 * half, 2 * half, fc=D_INK, ec=D_INK, zorder=4))
        hs = [Line2D([0], [0], color=BEAM_TYPE_COLORS[(int(re.sub(r"\D", "", t) or 1) - 1) % len(BEAM_TYPE_COLORS)], lw=3,
                     label=f"{t}  {sz}") for t, sz in sorted(types[fl].items(), key=lambda kv: nat_key(kv[0]))]
        if hs:
            ax.legend(handles=hs, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2, fontsize=7, frameon=False,
                      handlelength=1.6, columnspacing=1.4)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, facecolor="white", pil_kwargs={"quality": 92})
    plt.close(fig)
    n = sum(len(v) for v in segs.values())
    checks.append(("PASS" if not miss else "WARN", f"Beam layout plan drawn for {len(floors)} floors, {n} beams" +
                   (f"; {miss} beams had no geometry." if miss else ".")))
    return {"floors": floors, "beams_drawn": n, "beams_without_geometry": miss}


def column_layout_plan(cfg, uls_dir: Path, content: dict, stories: pd.DataFrame, out: Path, checks: list):
    """Plan of every floor with each column at its grid position, labelled with its designation and provided bars."""
    loc = read_csv(uls_dir, "34_Column_Locations")
    if loc is None or not (col(loc, "Label") and col(loc, "Story") and col(loc, "X") and col(loc, "Y")):
        checks.append(("WARN", "Column layout plan skipped: 34_Column_Locations.csv missing (re-run etabs_extract_tables.py)."))
        print("[SKIP] Column layout plan: 34_Column_Locations.csv missing")
        return None
    rename = {}
    if not cfg.no_grid_names:
        rename, _ = grid_designations(uls_dir, pd.DataFrame(), cfg.grid_tol)
    rename.update(dict(kv.split("=", 1) for kv in cfg.col_names.split(",") if "=" in kv))
    info = {(str(r["Label"]), str(r["Story"])): r for r in content["csv"]}
    rect = read_csv(uls_dir, "22b_Frame_Sect_Rect")
    cols = []
    for lab, st, x, y in zip(loc[col(loc, "Label")].map(sid), loc[col(loc, "Story")].map(sid),
                             pd.to_numeric(loc[col(loc, "X")], errors="coerce"), pd.to_numeric(loc[col(loc, "Y")], errors="coerce")):
        if pd.notna(x) and pd.notna(y):
            d = rename.get(lab, lab)
            cols.append({"story": st, "x": float(x), "y": float(y), "name": d, "row": info.get((d, st))})
    present = {c["story"] for c in cols}
    top_down = [s for s in stories["Story"] if s in present] + [s for s in sorted(present) if s not in set(stories["Story"])]
    floors = top_down[::-1]
    if not floors:
        return None
    bounds = (min(c["x"] for c in cols), min(c["y"] for c in cols), max(c["x"] for c in cols), max(c["y"] for c in cols))
    xs, ys = grid_lines(uls_dir)
    bounds = _with_grid(bounds, xs, ys)
    fig, axes = _plan_canvas("COLUMN LAYOUT PLAN", "Column designation (grid ID), section and provided longitudinal bars",
                             floors, bounds)
    for fl, ax in axes.items():
        _draw_grid(ax, xs, ys, *bounds)
        for c in [c for c in cols if c["story"] == fl]:
            dims = column_dims(c["row"]["Section"], rect) if c["row"] else None
            bw, bd = (dims[0] / 1000, dims[1] / 1000) if dims else (0.355, 0.355)
            ax.add_patch(plt.Rectangle((c["x"] - bw / 2, c["y"] - bd / 2), bw, bd, fc=D_INK, ec=D_INK, zorder=4))
            txt = c["name"] + (f"\n{c['row']['Provided']}" if c["row"] and c["row"].get("Provided") else "")
            ax.text(c["x"] + 0.28, c["y"] + 0.26, txt, ha="left", va="bottom", fontsize=6.3, color=D_INK, zorder=6,
                    fontweight="bold", linespacing=1.05,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.92))
        secs = sorted({c["row"]["Section"] for c in cols if c["story"] == fl and c["row"]})
        if secs:
            ax.text(0.5, -0.02, "   |   ".join(secs), transform=ax.transAxes, ha="center", va="top", fontsize=7, color=D_MUTED)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, facecolor="white", pil_kwargs={"quality": 92})
    plt.close(fig)
    unmatched = sum(1 for c in cols if c["row"] is None)
    checks.append(("PASS" if not unmatched else "WARN", f"Column layout plan drawn for {len(floors)} floors, {len(cols)} columns" +
                   (f"; {unmatched} had no matching row in the column table." if unmatched else ".")))
    return {"floors": floors, "columns_drawn": len(cols), "unmatched": unmatched}


def project_info(cfg, ctx: dict, manifest: dict) -> dict:
    def clean(v):
        s = "" if v is None else str(v).strip()
        return "\u2014" if not s or s.startswith("[") else s
    model = manifest.get("model_filename") or ctx.get("MODEL_FILENAME")
    model = Path(str(model).replace("\\", "/")).name if model else None
    client = cfg.client or ctx.get("CLIENT_NAME")
    project = (cfg.project or ctx.get("PROJECT_NAME")
               or (f"{ctx['BUILDING_USE']} building" if ctx.get("BUILDING_USE") else None)
               or (Path(model).stem if model else None))
    return {"Project": clean(project), "Client": clean(client),
            "Location": clean(cfg.location or ctx.get("SITE_ADDRESS") or ctx.get("LOCATION")), "Model file": clean(model),
            "Designer": clean(cfg.designer or ctx.get("DESIGNER")), "Checker": clean(cfg.checker or ctx.get("CHECKER")),
            "Report date": clean(ctx.get("REPORT_DATE") or datetime.now().strftime("%d %B %Y")), "Revision": clean(cfg.revision),
            "consultancy": clean(cfg.consultancy or ctx.get("CONSULTANCY_NAME")),
            "address": clean(cfg.address or ctx.get("CONSULTANCY_ADDRESS"))}


def merge_pages(parts: list[Path], info: dict, out: Path, fmt: str = "pdf") -> list[Path]:
    """One A4-landscape page per panel, with a slim project header and 'Page n of N' footer.
    fmt: pdf (multi-page PDF), tiff (multi-page TIFF) or both. Returns the files written."""
    from PIL import Image, ImageDraw, ImageFont
    from matplotlib import font_manager
    parts = [p for p in parts if p is not None and Path(p).exists()]
    W, H, m, top, bot = int(11.69 * DPI), int(8.27 * DPI), int(0.45 * DPI), int(0.62 * DPI), int(0.5 * DPI)
    fp = font_manager.findfont(font_manager.FontProperties(family=_font()))
    fb = font_manager.findfont(font_manager.FontProperties(family=_font(), weight="bold"))
    f_title, f_small = ImageFont.truetype(fb, 30), ImageFont.truetype(fp, 26)
    sub = " | ".join(v for v in (info["Project"], info["Client"], info["Location"]) if v != "\u2014")
    pages = []
    for n, p in enumerate(parts, 1):
        img = Image.open(p).convert("RGB")
        k = min((W - 2 * m) / img.width, (H - top - bot) / img.height)
        img = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
        page = Image.new("RGB", (W, H), "white")
        d = ImageDraw.Draw(page)
        d.text((m, int(0.17 * DPI)), "SLS / ULS Seismic Drift Check", font=f_title, fill=D_INK)
        d.text((W - m, int(0.19 * DPI)), sub, font=f_small, fill=D_MUTED, anchor="ra")
        d.line([(m, top - 12), (W - m, top - 12)], fill=D_EDGE, width=2)
        page.paste(img, ((W - img.width) // 2, top + int(0.12 * DPI)))
        d.line([(m, H - bot + 10), (W - m, H - bot + 10)], fill=D_EDGE, width=2)
        d.text((m, H - bot + 24), f"{info['consultancy']}  |  NBC 105:2025  |  {info['Report date']}  |  Rev. {info['Revision']}",
               font=f_small, fill=D_MUTED)
        d.text((W - m, H - bot + 24), f"Page {n} of {len(parts)}", font=f_small, fill=D_MUTED, anchor="ra")
        pages.append(page)
    written = []
    out.parent.mkdir(parents=True, exist_ok=True)
    if fmt in ("tiff", "both"):
        f = out.with_suffix(".tif")
        for comp in ("tiff_adobe_deflate", "tiff_lzw", None):      # first one this Pillow/libtiff build accepts
            try:
                kw = {"compression": comp} if comp else {}
                pages[0].save(f, save_all=True, append_images=pages[1:], dpi=(DPI, DPI), **kw)
                break
            except Exception as exc:
                print(f"[WARN] TIFF save with compression={comp}: {exc}")
                continue
        written.append(f)
    if fmt in ("pdf", "both"):
        f = out.with_suffix(".pdf")
        pages[0].save(f, "PDF", resolution=DPI, save_all=True, append_images=pages[1:])
        written.append(f)
    return written


# ----------------------------------------------------------------------------
def main() -> int:
    cfg = parse_args()
    if not cfg.tables.exists():
        raise SystemExit(f"Tables folder not found: {cfg.tables}")
    manifest = json.loads((cfg.tables / "sls_extraction_manifest.json").read_text(encoding="utf-8")) \
        if (cfg.tables / "sls_extraction_manifest.json").exists() else {}
    ctx = json.loads(cfg.context.read_text(encoding="utf-8")) if cfg.context and cfg.context.exists() else {}
    cases = {"X": cfg.case_x, "Y": cfg.case_y}

    jd, sd = read_csv(cfg.tables, "S02_Joint_Drifts"), read_csv(cfg.tables, "S01_Story_Drifts")
    coords = read_csv(cfg.tables, "S12_Joint_Coordinates")
    if jd is None and sd is None:
        raise SystemExit("Neither S01_Story_Drifts.csv nor S02_Joint_Drifts.csv found. Run etabs_extract_sls_drifts.py first.")
    tidy = tidy_joint_drifts(jd, coords, cases)
    sdt = tidy_story_drifts(sd, cases)
    if tidy.empty and sdt.empty:
        raise SystemExit(f"No drift rows found for {list(cases.values())}. Check the case names.")
    stories = build_stories(read_csv(cfg.tables, "S03_Story_Definitions"), tidy, sdt)
    res, hulls = evaluate(tidy, sdt, stories, cases, cfg.limit, cfg.kd, cfg.hull_tol)

    # ---- supporting model data
    extras: dict[str, Any] = {}
    modal_mass: dict[str, float] = {}
    per, mass = read_csv(cfg.tables, "S04_Modal_Periods"), read_csv(cfg.tables, "S05_Modal_Mass_Ratios")
    if per is not None and col(per, "Period"):
        extras["T1"] = float(pd.to_numeric(per[col(per, "Period")], errors="coerce").dropna().iloc[0])
    if mass is not None:
        mc, pc = col(mass, "Mode"), col(mass, "Period")
        for key, name, cum in (("modeX", "UX", "SumUX"), ("modeY", "UY", "SumUY")):
            c = col(mass, name)
            if c and mc and pc:
                v = pd.to_numeric(mass[c], errors="coerce")
                if v.notna().any():
                    i = v.idxmax()
                    extras[key] = (sid(mass.loc[i, mc]), float(mass.loc[i, pc]))
            cc = col(mass, cum)
            if cc and pd.to_numeric(mass[cc], errors="coerce").notna().any():
                modal_mass[cum] = float(pd.to_numeric(mass[cc], errors="coerce").dropna().iloc[-1])
    br = read_csv(cfg.tables, "S06_Base_Reactions")
    if br is not None and col(br, "OutputCase"):
        for key, c, case in (("VX", "FX", cfg.case_x), ("VY", "FY", cfg.case_y)):
            sub = br[br[col(br, "OutputCase")].astype(str).str.lower() == case.lower()]
            if col(sub, c) and not sub.empty:
                extras[key] = float(pd.to_numeric(sub[col(sub, c)], errors="coerce").abs().max())
    names = {c.lower() for c in cases.values()}
    for stem, key in (("S08_Load_Patterns", "patterns"), ("S09_Load_Cases", "loadcases")):
        t = read_csv(cfg.tables, stem)
        if t is not None and col(t, "Name"):
            sub = t[t[col(t, "Name")].astype(str).str.lower().isin(names)]
            keep = [c for c in t.columns if t[c].notna().any()][:6]
            if not sub.empty:
                extras[key] = (keep, [[sid(v) for v in row] for row in sub[keep].values.tolist()])

    checks = run_checks(res, tidy, sdt, manifest, cases, cfg, ctx, modal_mass)

    # ---- ULS drifts, displacements, torsion --------------------------------
    uls_cases = {"X": cfg.uls_x, "Y": cfg.uls_y}
    uls_dir = cfg.uls_tables or (Path("tables") if Path("tables").is_dir() else cfg.tables)
    if not uls_dir.exists():
        raise SystemExit(f"ULS tables folder not found: {uls_dir}")
    separate = uls_dir.resolve() != cfg.tables.resolve()
    print(f"ULS data read from: {uls_dir}")
    jd_u = read_first(uls_dir, "31_Joint_Drifts", "S02_Joint_Drifts")
    sd_u = read_first(uls_dir, "04_Story_Drifts", "S01_Story_Drifts")
    coords_u = read_first(uls_dir, "14_Joint_Coordinates", "S12_Joint_Coordinates")
    uls_manifest = {}
    for mf in ("extraction_manifest.json", "sls_extraction_manifest.json"):
        if (uls_dir / mf).exists():
            uls_manifest = json.loads((uls_dir / mf).read_text(encoding="utf-8")); break
    tidy_u, sdt_u = tidy_joint_drifts(jd_u, coords_u, uls_cases), tidy_story_drifts(sd_u, uls_cases)
    res_u = None
    if not (tidy_u.empty and sdt_u.empty):
        res_u, _ = evaluate(tidy_u, sdt_u, stories, uls_cases, cfg.uls_limit, cfg.uls_scale, cfg.hull_tol)
    else:
        checks.append(("WARN", f"No drift rows for the ULS cases {list(uls_cases.values())}; ULS drift shown as n/a."))
    def joint_story_map(j):
        if j is not None and col(j, "UniqueName") and col(j, "Story"):
            return dict(zip(j[col(j, "UniqueName")].map(sid), j[col(j, "Story")].map(sid)))
        return {}
    disp_s = tidy_displacements(read_csv(cfg.tables, "S14_Story_Max_Avg_Displacements"),
                                read_csv(cfg.tables, "S13_Joint_Displacements"), joint_story_map(jd), cases)
    disp_u = tidy_displacements(read_first(uls_dir, "33_Story_Max_Avg_Displacements", "S14_Story_Max_Avg_Displacements"),
                                read_first(uls_dir, "32_Joint_Displacements", "S13_Joint_Displacements"),
                                joint_story_map(jd_u), uls_cases, cfg.uls_scale)
    for lvl, dd, cs in (("SLS", disp_s, cases), ("ULS", disp_u, uls_cases)):
        if dd.empty:
            checks.append(("WARN", f"No displacement data for the {lvl} cases {list(cs.values())}; displacement shown as n/a."))
        else:
            checks.append(("PASS", f"{lvl} displacements from: {dd['Source'].iloc[0]}."))
    H_mm, h_src = building_height(stories, cfg.height)
    checks.append(("PASS" if H_mm else "WARN", f"Building height H = {H_mm:.0f} mm from {h_src}." if H_mm
                   else "Building height could not be determined; displacement limits shown as n/a (use --height)."))
    checks.append(("INFO", f"ULS displacements and drifts multiplied by Rmu = {cfg.uls_scale:g} (cl. 5.5.1.1); kd not applied."))
    same_model = separate and uls_manifest.get("model_filename") and manifest.get("model_filename") and \
        Path(str(uls_manifest["model_filename"])).stem.lower() == Path(str(manifest["model_filename"])).stem.lower()
    if same_model:
        checks.append(("WARN", f"The ULS and SLS tables were extracted from the same model file "
                               f"('{manifest['model_filename']}'): the ULS stiffness set is probably not applied."))
    checks.append(("INFO" if separate else "WARN",
                   f"ULS results read from {uls_dir} (model: {uls_manifest.get('model_filename', 'unknown')})." if separate else
                   "ULS results read from the same model/folder as SLS: SLS stiffness (0.7/0.9) is used instead of the "
                   "ULS stiffness of Table 3-1 (0.35/0.70). Use --uls-tables with the ULS-stiffness model."))
    tors = torsion_summary(disp_u, uls_cases, cfg.torsion_limit, cfg.torsion_extreme)
    if len(tors) < 2:
        checks.append(("WARN", "Torsional ratio not available for both ULS directions."))

    out = cfg.output.with_suffix(".jpg")
    out.parent.mkdir(parents=True, exist_ok=True)
    render_jpg(res, cfg, checks, out)

    gov = lambda r, d: (None if r is None or r[r["Dir"] == d].dropna(subset=["gov_eff"]).empty
                        else float(r[r["Dir"] == d]["gov_eff"].max()))
    disp_vals = {(lv, d): max_displacement(dd, d) for lv, dd in (("ULS", disp_u), ("SLS", disp_s)) for d in ("X", "Y")}
    drift_vals = {(lv, d): gov(r, d) for lv, r in (("ULS", res_u), ("SLS", res)) for d in ("X", "Y")}
    crit_path = (cfg.criteria_output or out.with_name("Displacement_Drift_Criteria.jpg")).with_suffix(".jpg")
    tors_path = (cfg.torsion_output or out.with_name("Torsional_Irregularity_Check.jpg")).with_suffix(".jpg")
    criteria = render_criteria(crit_path, cfg, H_mm, disp_vals, drift_vals)
    torsion = render_torsion(tors_path, cfg, tors, uls_cases) if tors else None
    col_path = (cfg.columns_output or out.with_name("Column_Reinforcement_Details.jpg")).with_suffix(".jpg")
    colres = None if cfg.no_columns else column_reinforcement_panel(cfg, uls_dir, stories, col_path, checks)
    beam_path = (cfg.beams_output or out.with_name("Beam_Reinforcement_Details.jpg")).with_suffix(".jpg")
    beamres = None if cfg.no_beams else beam_reinforcement_panel(cfg, uls_dir, stories, beam_path, checks)
    bplan_path = (cfg.beam_plan_output or out.with_name("Beam_Layout_Plan.jpg")).with_suffix(".jpg")
    cplan_path = (cfg.column_plan_output or out.with_name("Column_Layout_Plan.jpg")).with_suffix(".jpg")
    bplan = beam_layout_plan(cfg, uls_dir, beamres, stories, bplan_path, checks) if beamres and not cfg.no_plans else None
    cplan = column_layout_plan(cfg, uls_dir, colres, stories, cplan_path, checks) if colres and not cfg.no_plans else None

    # ---- merged multi-page file (one panel per page) ------------------------
    summary_base = (cfg.summary_output or out.with_name("SLS_ULS_Check_Summary")).with_suffix("")
    merged = merge_pages([out, crit_path, tors_path if torsion else None], project_info(cfg, ctx, manifest),
                         summary_base, cfg.summary_format)
    if torsion is None:
        print("[SKIP] Torsional irregularity table: no ULS displacement data found.")

    res.to_csv(out.with_suffix(".results.csv"), index=False)
    (out.with_suffix(".results.json")).write_text(json.dumps({
        "limit": cfg.limit, "kd_applied": cfg.kd, "cases": cases, "checks": checks,
        "results": json.loads(res.to_json(orient="records")),
        "uls_cases": uls_cases, "uls_scale": cfg.uls_scale, "height_mm": H_mm, "height_source": h_src,
        "criteria_table": criteria, "torsion_table": torsion,
        "column_table": None if colres is None else {k: v for k, v in colres.items() if k not in ("ladder", "groups")},
        "beam_table": None if beamres is None else {k: v for k, v in beamres.items() if k not in ("groups",)},
        "uls_results": json.loads(res_u.to_json(orient="records")) if res_u is not None else None,
    }, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    worst = res.dropna(subset=["gov"]).sort_values("ratio", ascending=False).head(1)
    if not worst.empty:
        w = worst.iloc[0]
        print(f"Governing: {w['Case']} {w['Story']} drift {w['gov_eff']:.5f} (utilisation {w['ratio'] * 100:.1f} %) -> {w['status']}")
    print("Overall:", "COMPLIANT" if (res["status"] == "PASS").all() else "NON-COMPLIANT")
    for r in criteria["rows"]:
        print(f"  {r['description']}: EQX={r['EQX']} EQY={r['EQY']} allowable={r['allowable']} -> {r['status']}")
    if torsion:
        for d, t in torsion["directions"].items():
            print(f"  Torsion {t['case']}: {t['story']} max {t['dmax']:.3f} / avg {t['davg']:.3f} = {t['ratio']:.3f} -> {t['status']}")
    print(f"Saved: {out.resolve()}")
    print(f"Saved: {crit_path.resolve()}")
    if colres:
        print(f"Saved: {col_path.resolve()}")
    if beamres:
        print(f"Saved: {beam_path.resolve()}")
    if bplan:
        print(f"Saved: {bplan_path.resolve()}")
    if cplan:
        print(f"Saved: {cplan_path.resolve()}")
    for f in merged:
        print(f"Saved: {f.resolve()}")
    if torsion:
        print(f"Saved: {tors_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
