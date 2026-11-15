"""
generate_etabs_figures.py

Generate report-ready PNG figures from the CSV package exported by
etabs_extract_tables.py. No ETABS screenshots are required.

Usage:
    pip install pandas matplotlib
    python generate_etabs_figures.py --tables tables --output figures

The output filenames are aligned with the reference-style report generator:
    01_key_frame_etabs.png   (new: extruded ETABS-style 3D view)
    01_key_frame.png
    02_grid_plan.png
    03_sectional_view.png
    04_mode_1.png
    05_modal_mass.png
    06_drift_x.png
    06_drift_y.png
    07_joint_reaction.png
    08_moment.png
    09_axial.png
    10_beam_design.png
    11_column_design.png
    12_reinforcement.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
except ImportError as exc:
    raise SystemExit("Install dependencies first: pip install pandas matplotlib") from exc


BLUE = "#1F4E79"
ORANGE = "#ED7D31"
GREEN = "#70AD47"
RED = "#C00000"
GREY = "#7F7F7F"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables", type=Path, default=Path("tables"))
    parser.add_argument("--output", type=Path, default=Path("figures"))
    parser.add_argument("--elev", type=float, default=32, help="3D view elevation (deg)")
    parser.add_argument("--azim", type=float, default=-135, help="3D view azimuth (deg)")
    return parser.parse_args()


def read(tables: Path, name: str) -> pd.DataFrame | None:
    path = tables / f"{name}.csv"
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception as exc:
        print(f"[WARN] Could not read {path}: {exc}")
        return None


def first_available(*frames: pd.DataFrame | None) -> pd.DataFrame | None:
    for frame in frames:
        if frame is not None:
            return frame
    return None


def save(figures: Path, name: str) -> None:
    path = figures / f"{name}.png"
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    print(f"[OK] {path}")


def style() -> None:
    plt.rcParams.update({
        "font.family": "Arial",
        "font.size": 9,
        "axes.titlesize": 12,
        "axes.labelsize": 9,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })



# ----------------------------------------------------------------------------
# ETABS-style extruded 3D view
# ----------------------------------------------------------------------------
FRAME_FACE = "#5A64C6"     # ETABS-like blue for extruded frame sections
FRAME_EDGE = "#262E7A"
SLAB_FACE = "#BDBDBD"
GRID_BLUE = "#BFD9F2"
BEAM_RGB = (0.40, 0.45, 0.82)   # ETABS-style blue for beams in the solid render
COL_RGB = (0.36, 0.41, 0.78)    # columns, slightly deeper


def _find_col(df: pd.DataFrame, *names: str) -> str | None:
    lower = {c.lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    return None


def _sid(v) -> str:
    """Stable id string: 12.0 / numpy ints -> '12', ' A1 ' -> 'A1'."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _load_joint_map(joints: pd.DataFrame) -> dict:
    """Return {joint_label: (x, y, z)}. Built column-wise so ids never get float-cast."""
    id_col = _find_col(joints, "Joint", "UniqueName", "Name", "Label")
    ids = joints[id_col] if id_col is not None else pd.Series(range(1, len(joints) + 1))
    return {_sid(k): (x, y, z) for k, x, y, z in
            zip(ids, joints["GlobalX"], joints["GlobalY"], joints["GlobalZ"])}


def _scan_connectivity(tables: Path):
    """Look through every CSV for frame (JointI/JointJ) and area (Joint1..4) tables."""
    frames, areas = None, None
    for path in sorted(tables.glob("*.csv")):
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        cols = {c.lower() for c in df.columns}
        if frames is None and {"jointi", "jointj"}.issubset(cols):
            frames = df
        if areas is None and {"joint1", "joint2", "joint3", "joint4"}.issubset(cols):
            areas = df
    return frames, areas


def _infer_members(jmap: dict, tol: float = 1e-3):
    """Fallback when no connectivity table exists: infer columns/beams/slabs from joint grid."""
    pts = [(k, np.array(v, dtype=float)) for k, v in jmap.items()]
    cols, beams = [], []

    def groups(keyfun, sortidx):
        d = {}
        for k, p in pts:
            d.setdefault(keyfun(p), []).append((p[sortidx], k))
        for g in d.values():
            g.sort()
            for (_, a), (_, b) in zip(g[:-1], g[1:]):
                yield a, b

    r = lambda v: round(float(v) / tol)
    cols = list(groups(lambda p: (r(p[0]), r(p[1])), 2))
    beams = list(groups(lambda p: (r(p[1]), r(p[2])), 0)) + list(groups(lambda p: (r(p[0]), r(p[2])), 1))
    frames = [(a, b, "column") for a, b in cols] + [(a, b, "beam") for a, b in beams]

    # slabs: rectangular panels whose 4 edges are all beams
    edge = {frozenset((a, b)) for a, b, t in frames if t == "beam"}
    areas = []
    zs = sorted({round(float(p[2]), 3) for _, p in pts})
    for z in zs:
        lvl = {k: p for k, p in pts if abs(p[2] - z) < 1e-2}
        xs = sorted({round(float(p[0]), 3) for p in lvl.values()})
        ys = sorted({round(float(p[1]), 3) for p in lvl.values()})
        at = {(round(float(p[0]), 3), round(float(p[1]), 3)): k for k, p in lvl.items()}
        for x0, x1 in zip(xs[:-1], xs[1:]):
            for y0, y1 in zip(ys[:-1], ys[1:]):
                c = [at.get((x0, y0)), at.get((x1, y0)), at.get((x1, y1)), at.get((x0, y1))]
                if None in c:
                    continue
                if all(frozenset((c[i], c[(i + 1) % 4])) in edge for i in range(4)):
                    areas.append(c)
    return frames, areas


def _section_sizes(tables: Path, frames_df: pd.DataFrame | None):
    """Optional: {frame_label: (b, d)} from section tables if they are present."""
    if frames_df is None:
        return {}
    fcol = _find_col(frames_df, "Frame", "UniqueName", "Name")
    scol = _find_col(frames_df, "AnalSect", "Section", "DesignSect")
    if fcol is None or scol is None:
        return {}
    dims = {}
    for path in tables.glob("*.csv"):
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        n, t3, t2 = _find_col(df, "Name", "SectionName"), _find_col(df, "t3", "D", "Depth"), _find_col(df, "t2", "B", "Width")
        if n and t3 and t2:
            for _, r in df.iterrows():
                try:
                    dims[str(r[n])] = (float(r[t2]), float(r[t3]))
                except (TypeError, ValueError):
                    pass
    return {str(r[fcol]): dims[str(r[scol])] for _, r in frames_df.iterrows() if str(r[scol]) in dims}


def _segments_cross(p, q, r, s) -> bool:
    d = lambda a, b, c: (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return d(p, q, r) * d(p, q, s) < 0 and d(r, s, p) * d(r, s, q) < 0


def _fix_polygon(pts):
    """Un-bow-tie a horizontal polygon whose vertices arrive out of order."""
    pts = [np.asarray(p, float) for p in pts]
    n = len(pts)
    if n < 4 or np.ptp([p[2] for p in pts]) > 1e-6:
        return pts
    bad = any(_segments_cross(pts[i], pts[(i + 1) % n], pts[j], pts[(j + 1) % n])
              for i in range(n) for j in range(i + 2, n) if not (i == 0 and j == n - 1))
    if bad:
        c = np.mean(pts, axis=0)
        pts.sort(key=lambda p: np.arctan2(p[1] - c[1], p[0] - c[0]))
    return pts


def _box(p0, p1, b, d, vertical: bool):
    """Return 6 quad faces of a rectangular prism running from p0 to p1."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    axis = p1 - p0
    L = np.linalg.norm(axis)
    if L < 1e-9:
        return []
    u = axis / L
    if vertical:
        v = np.array([1.0, 0.0, 0.0]); w = np.array([0.0, 1.0, 0.0])
        hv, hw = b / 2, d / 2
    else:
        w = np.array([0.0, 0.0, 1.0])          # depth acts vertically
        v = np.cross(w, u); v /= np.linalg.norm(v)
        hv, hw = b / 2, d / 2
        # beam top aligned with joint level, like ETABS "top" insertion point
        p0 = p0 - w * hw; p1 = p1 - w * hw
    corners = lambda c: [c + sv * hv * v + sw * hw * w for sv, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    a, c = corners(p0), corners(p1)
    faces = [[a[i], a[(i + 1) % 4], c[(i + 1) % 4], c[i]] for i in range(4)]
    faces += [a, c]
    return faces


def _grid_lines(tables: Path, mn, mx, span):
    """Grid lines from 13_Grid_Definitions: ([(ordinate,id)...] for X, same for Y)."""
    g = read(tables, "13_Grid_Definitions")
    xs, ys = [], []
    if g is None:
        return xs, ys
    lt, oc, ic = _find_col(g, "LineType", "Type"), _find_col(g, "Ordinate"), _find_col(g, "ID", "GridID", "Name")
    if None in (lt, oc):
        return xs, ys
    for _, r in g.iterrows():
        o = pd.to_numeric(r[oc], errors="coerce")
        if pd.isna(o):
            continue
        item = (float(o), str(r[ic]) if ic else "")
        t = str(r[lt]).strip().upper()
        (xs if t.startswith("X") else ys if t.startswith("Y") else []).append(item)
    ok = lambda v, lo, hi: all(lo - span <= a[0] <= hi + span for a in v)
    if not (ok(xs, mn[0], mx[0]) and ok(ys, mn[1], mx[1])):
        print("[3D] grid ordinates fall outside the model - grid box ignored")
        return [], []
    return xs, ys


def _rib_spacings(tables: Path):
    """{section_name: [spacings]} from any 23*.csv area-section table that has a *spacing* column."""
    spacing, seen = {}, []
    for path in sorted(tables.glob("23*.csv")):
        df = read(tables, path.stem)
        if df is None:
            continue
        seen.append(f"{path.stem}: {list(df.columns)}")
        nc = _find_col(df, "Name", "Section")
        cols = [c for c in df.columns if "spac" in c.lower()]
        if nc is None or not cols:
            continue
        for _, r in df.iterrows():
            v = [float(x) for x in pd.to_numeric(r[cols], errors="coerce") if pd.notna(x) and x > 0]
            if v:
                spacing[str(r[nc]).strip()] = v
    return spacing, seen


def _rib_segments(tables: Path, slab_meta):
    """Black rib lines across axis-aligned rectangular slab panels whose section defines rib spacing."""
    spacing, seen = _rib_spacings(tables)
    asg = read(tables, "18_Area_Assignments")
    if not spacing:
        print("[3D] no rib/waffle spacing found in 23*.csv (slabs drawn plain). Tables seen: "
              + (" | ".join(seen) if seen else "none"))
        return []
    idc = _find_col(asg, "UniqueName", "Area", "Name") if asg is not None else None
    sc = _find_col(asg, "Section", "SectionProperty", "Property", "AreaSection") if asg is not None else None
    if None in (idc, sc):
        print(f"[3D] ribs found for sections {sorted(spacing)} but cannot map areas to sections: "
              f"18_Area_Assignments columns = {None if asg is None else list(asg.columns)}")
        return []
    sec_of = {_sid(a): _sid(b) for a, b in zip(asg[idc], asg[sc])}
    segs, used = [], 0
    for poly, name in slab_meta:
        sp = spacing.get(sec_of.get(name or "", ""))
        if not sp:
            continue
        P = np.array(poly)
        x0, x1, y0, y1, z = P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max(), P[:, 2].mean()
        rect = all((abs(p[0] - x0) < 1e-6 or abs(p[0] - x1) < 1e-6) and
                   (abs(p[1] - y0) < 1e-6 or abs(p[1] - y1) < 1e-6) for p in P)
        if not rect:
            continue
        sx, sy = sp[0], sp[-1]                       # one value -> same both ways
        for x in np.arange(x0 + sx, x1 - 0.25 * sx, sx):
            segs.append([(x, y0, z), (x, y1, z)])
        for y in np.arange(y0 + sy, y1 - 0.25 * sy, sy):
            segs.append([(x0, y, z), (x1, y, z)])
        used += 1
    print(f"[3D] ribs: {used} slab panels ribbed, spacing by section = {spacing}")
    return segs


def _prism(poly, t):
    """Closed slab prism: top polygon at its level, bottom t below."""
    top = [np.asarray(p, float) for p in poly]
    bot = [p - np.array([0, 0, t]) for p in top]
    n = len(top)
    faces = [top, bot[::-1]]
    faces += [[top[i], top[(i + 1) % n], bot[(i + 1) % n], bot[i]] for i in range(n)]
    return faces


def _shade(face, base, light=np.array([-0.45, -0.6, 0.66])):
    p = np.asarray(face, float)
    nrm = np.cross(p[1] - p[0], p[2] - p[0])
    nl = np.linalg.norm(nrm)
    if nl < 1e-12:
        return base
    nrm /= nl
    k = 0.50 + 0.50 * abs(float(nrm @ (light / np.linalg.norm(light))))
    return tuple(min(1.0, c * k) for c in base) + (1.0,)


def realistic_3d(out: Path, slab_faces, beam_faces, col_faces, wall_faces, bounds, elev, azim, slab_t):
    """Solid, lit render: opaque concrete, slabs with thickness, no CAD furniture."""
    (mn, mx, span) = bounds
    faces, colors = [], []
    for poly in slab_faces:
        for f in _prism(poly, slab_t):
            faces.append(f); colors.append(_shade(f, (0.80, 0.79, 0.76)))
    for f in beam_faces:
        faces.append(f); colors.append(_shade(f, BEAM_RGB))
    for f in col_faces:
        faces.append(f); colors.append(_shade(f, COL_RGB))
    for f in wall_faces:
        faces.append(f); colors.append(_shade(f, (0.72, 0.71, 0.68)))
    fig = plt.figure(figsize=(7.5, 8.5))
    ax = fig.add_subplot(111, projection="3d", computed_zorder=False)   # honour our zorder; faces still depth-sort inside one collection
    ax.set_proj_type("persp", focal_length=0.9)
    pad = 0.3 * span
    z0 = mn[2]
    ground = [(mn[0] - pad, mn[1] - pad, z0), (mx[0] + pad, mn[1] - pad, z0),
              (mx[0] + pad, mx[1] + pad, z0), (mn[0] - pad, mx[1] + pad, z0)]
    ax.add_collection3d(Poly3DCollection([ground], facecolors="#E9EBEE", edgecolors="none", zorder=0))   # ground always behind
    coll = Poly3DCollection(faces, facecolors=colors, edgecolors=(0.25, 0.25, 0.25, 0.55), linewidths=.25,
                            zorder=5)
    ax.add_collection3d(coll)
    ax.set_xlim(mn[0] - pad, mx[0] + pad); ax.set_ylim(mn[1] - pad, mx[1] + pad)
    ax.set_zlim(z0, mx[2] + .05 * span)
    aspect = (mx[0] - mn[0] + 2 * pad, mx[1] - mn[1] + 2 * pad, (mx[2] - z0) + .05 * span)
    try:
        ax.set_box_aspect(aspect, zoom=1.3)
    except TypeError:
        ax.set_box_aspect(aspect)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    path = out / "01_key_frame_realistic.png"
    plt.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"[OK] {path}")


def etabs_style_3d(tables: Path, out: Path, elev: float = 32, azim: float = -135) -> bool:
    """Extruded, translucent ETABS-like 3D view. Returns False if it cannot be drawn."""
    joints = read(tables, "14_Joint_Coordinates")
    if joints is None or not {"GlobalX", "GlobalY", "GlobalZ"}.issubset(joints.columns):
        return False
    joints = joints.copy()
    for col in ("GlobalX", "GlobalY", "GlobalZ"):
        joints[col] = pd.to_numeric(joints[col], errors="coerce")
    joints = joints.dropna(subset=["GlobalX", "GlobalY", "GlobalZ"])
    if _find_col(joints, "Joint") is None:
        print("[WARN] 3D view skipped: 14_Joint_Coordinates.csv is the raw ETABS table, not the "
              "normalised one. Re-run etabs_extract_tables.py and look for the [GEOMETRY] line.")
        return False
    jmap = _load_joint_map(joints)

    members, panels = read(tables, "29_Frame_Members"), read(tables, "30_Slab_Panels")
    sizes, areas, wall_areas, area_names = {}, [], [], []
    if members is not None and {"JointI", "JointJ"}.issubset(members.columns):
        # package written by etabs_extract_tables.py (preferred)
        sid = _sid
        frames = []
        for _, r in members.iterrows():
            a, b = sid(r["JointI"]), sid(r["JointJ"])
            if a not in jmap or b not in jmap or str(r.get("Type", "")) == "brace":
                continue
            kind = str(r.get("Type", "")) or "beam"
            name = sid(r["Frame"]) if "Frame" in members.columns else None
            frames.append((a, b, kind, name))
            w, d = r.get("Width", np.nan), r.get("Depth", np.nan)
            if name and pd.notna(w) and pd.notna(d):
                sizes[name] = (float(w), float(d))
        if panels is not None:
            jc = sorted([c for c in panels.columns if c.startswith("Joint")], key=lambda c: int(c[5:]))
            for _, r in panels.iterrows():
                pts = [sid(r[c]) for c in jc if pd.notna(r[c]) and str(r[c]) != ""]
                if len(pts) >= 3 and all(p in jmap for p in pts):
                    if str(r.get("Type", "")) == "wall":
                        wall_areas.append(pts)
                    else:
                        areas.append(pts)
                        area_names.append(sid(r["Area"]) if "Area" in panels.columns else None)
    else:
        frames_df, areas_df = _scan_connectivity(tables)
        if frames_df is not None:
            ic, jc_ = _find_col(frames_df, "JointI"), _find_col(frames_df, "JointJ")
            fname = _find_col(frames_df, "Frame", "UniqueName", "Name")
            frames = []
            for _, r in frames_df.iterrows():
                a, b = str(r[ic]), str(r[jc_])
                if a in jmap and b in jmap:
                    dz = abs(jmap[a][2] - jmap[b][2])
                    horiz = np.hypot(jmap[a][0] - jmap[b][0], jmap[a][1] - jmap[b][1])
                    frames.append((a, b, "column" if dz > horiz else "beam", str(r[fname]) if fname else None))
            if areas_df is not None:
                for _, r in areas_df.iterrows():
                    c = [str(r[f"Joint{i}"]) for i in (1, 2, 3, 4)]
                    if all(k in jmap for k in c):
                        areas.append(c)
            sizes = _section_sizes(tables, frames_df)
        else:
            print("[INFO] No frame data found - inferring members from joint grid")
            frames, areas = _infer_members(jmap)
            frames = [(a, b, t, None) for a, b, t in frames]
    if not frames:
        print(f"[WARN] 3D view: 0 members matched the {len(jmap)} joints - check joint ids in "
              "14_Joint_Coordinates.csv vs 29_Frame_Members.csv")
        return False

    xyz = np.array(list(jmap.values()), dtype=float)
    span = float((xyz.max(0) - xyz.min(0))[:2].max()) or 1.0
    col_bd = (0.04 * span, 0.04 * span)      # fallback sizes scaled to model
    beam_bd = (0.03 * span, 0.05 * span)

    slab_faces, col_faces, beam_faces = [], [], []
    base_z = float(xyz[:, 2].min())
    wall_faces = [[jmap[k] for k in c] for c in wall_areas]
    n_fixed = 0
    slab_meta = []
    for ai, c in enumerate(areas):
        if min(jmap[k][2] for k in c) <= base_z + 1e-6:
            continue                              # no slab at the base level
        poly = [np.asarray(jmap[k], float) for k in c]
        fixed = _fix_polygon(poly)
        n_fixed += any(a is not b for a, b in zip(poly, fixed)) and [tuple(x) for x in poly] != [tuple(x) for x in fixed]
        slab_faces.append(fixed)
        slab_meta.append((fixed, area_names[ai] if ai < len(area_names) else None))
    for a, b, kind, name in frames:
        p0, p1 = jmap[a], jmap[b]
        bd = sizes.get(name) if name else None
        if kind == "column":
            col_faces += _box(p0, p1, *(bd or col_bd), vertical=True)
        else:
            beam_faces += _box(p0, p1, *(bd or beam_bd), vertical=False)

    # sanity check: ids that do not belong together give slanted "columns"
    bad_cols = [f for f in frames if f[2] == "column" and
                np.hypot(jmap[f[0]][0] - jmap[f[1]][0], jmap[f[0]][1] - jmap[f[1]][1]) > 0.05]
    if len(bad_cols) > 0.1 * max(1, sum(1 for f in frames if f[2] == "column")):
        print("[WARN] 3D view skipped: member ids do not match joint ids (many slanted columns). "
              "Re-run the extractor so 14, 29 and 30 come from the same run.")
        return False
    n_col = sum(1 for f in frames if f[2] == "column")
    n_sized = sum(1 for f in frames if f[3] in sizes)
    zs = sorted({round(p[2], 3) for p in jmap.values()})
    print(f"[3D] source={'29/30 package' if members is not None else 'other tables / inferred'}  "
          f"joints={len(jmap)}  columns={n_col}  beams/other={len(frames) - n_col}  "
          f"slab panels={len(slab_faces)} (reordered {n_fixed})  walls={len(wall_faces)}")
    print(f"[3D] members with real section size: {n_sized}/{len(frames)}  "
          f"(rest use fallback size)  levels z={zs}")
    sizes_used = sorted({tuple(round(x, 3) for x in v) for v in sizes.values()})
    print(f"[3D] distinct section sizes (b,d) m: {sizes_used}")

    fig = plt.figure(figsize=(7.5, 8.5))
    ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
    ax.set_proj_type("persp", focal_length=0.8)

    mn, mx = xyz.min(0), xyz.max(0)
    z0, ztop = mn[2], mx[2]
    gxs, gys = _grid_lines(tables, mn, mx, span)
    bx0 = min([g_[0] for g_ in gxs] + [mn[0]]); bx1 = max([g_[0] for g_ in gxs] + [mx[0]])
    by0 = min([g_[0] for g_ in gys] + [mn[1]]); by1 = max([g_[0] for g_ in gys] + [mx[1]])
    pad = 0.35 * span

    # fine light-blue ground grid, like the ETABS viewport
    step = max(1.0, round(span / 30.0))
    gx = np.arange(np.floor((bx0 - pad) / step) * step, bx1 + pad + step, step)
    gy = np.arange(np.floor((by0 - pad) / step) * step, by1 + pad + step, step)
    for x in gx:
        ax.plot([x, x], [gy[0], gy[-1]], [z0, z0], color=GRID_BLUE, lw=.4, zorder=0)
    for y in gy:
        ax.plot([gx[0], gx[-1]], [y, y], [z0, z0], color=GRID_BLUE, lw=.4, zorder=0)

    # thin grey bounding box of the grid system (ETABS shows the grid extents in 3D)
    box = "#B8B8B8"
    for z in (z0, ztop):
        ax.plot([bx0, bx1, bx1, bx0, bx0], [by0, by0, by1, by1, by0], [z] * 5, color=box, lw=.5, zorder=0)
    for x, y in ((bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)):
        ax.plot([x, x], [y, y], [z0, ztop], color=box, lw=.5, zorder=0)
    off = 0.04 * span
    bub = dict(boxstyle="circle,pad=0.25", fc="white", ec="#9A9A9A", lw=.5)
    for o, name in gxs:
        ax.text(o, by0 - off, z0, name, fontsize=6, color="#777", ha="center", va="center", bbox=bub, zorder=1)
    for o, name in gys:
        ax.text(bx0 - off, o, z0, name, fontsize=6, color="#777", ha="center", va="center", bbox=bub, zorder=1)

    if slab_faces:
        ax.add_collection3d(Poly3DCollection(slab_faces, facecolors=SLAB_FACE, edgecolors="#707070",
                                             linewidths=.3, alpha=.55, zorder=1))
        ribs = _rib_segments(tables, slab_meta)
        if ribs:
            from mpl_toolkits.mplot3d.art3d import Line3DCollection
            ax.add_collection3d(Line3DCollection(ribs, colors="#111111", linewidths=1.1, zorder=2))
    if wall_faces:
        ax.add_collection3d(Poly3DCollection(wall_faces, facecolors="#B9C2E8", edgecolors=FRAME_EDGE,
                                             linewidths=.4, alpha=.5, zorder=2))
    if beam_faces:
        ax.add_collection3d(Poly3DCollection(beam_faces, facecolors=FRAME_FACE, edgecolors=FRAME_EDGE,
                                             linewidths=.4, alpha=.55, zorder=3))
    if col_faces:
        ax.add_collection3d(Poly3DCollection(col_faces, facecolors=FRAME_FACE, edgecolors=FRAME_EDGE,
                                             linewidths=.4, alpha=.6, zorder=4))

    ax.set_xlim(bx0 - pad, bx1 + pad); ax.set_ylim(by0 - pad, by1 + pad); ax.set_zlim(z0, ztop + .05 * span)
    aspect = (bx1 - bx0 + 2 * pad, by1 - by0 + 2 * pad, (ztop - z0) + .05 * span)
    try:
        ax.set_box_aspect(aspect, zoom=1.3)        # fill the frame (matplotlib >= 3.3)
    except TypeError:
        ax.set_box_aspect(aspect)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()

    # ETABS-style global axes triad at the origin corner
    o = np.array([bx0, by0, z0]); L = 0.1 * span
    for vec, col, lab in (((L, 0, 0), "red", "X"), ((0, L, 0), "green", "Y"), ((0, 0, L), "blue", "Z")):
        end = o + np.array(vec)
        ax.plot([o[0], end[0]], [o[1], end[1]], [o[2], end[2]], color=col, lw=1.6, zorder=10)
        ax.text(*(end + np.array(vec) * .25), lab, color=col, fontsize=9, zorder=10)

    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    plt.savefig(out / "01_key_frame_etabs.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"[OK] {out / '01_key_frame_etabs.png'}")
    try:
        realistic_3d(out, slab_faces, beam_faces, col_faces, wall_faces, (mn, mx, span), elev, azim,
                     slab_t=0.12 * min(3.0, max(1.0, (ztop - z0) / max(1, len(zs) - 1)) / 3.0) or 0.12)
    except Exception as exc:
        print(f"[WARN] realistic render failed: {exc}")
    return True


def geometry_figures(tables: Path, out: Path, elev: float = 32, azim: float = -135) -> None:
    joints = read(tables, "14_Joint_Coordinates")
    if joints is None or not {"GlobalX", "GlobalY", "GlobalZ"}.issubset(joints.columns):
        print("[SKIP] Geometry figures: joint-coordinate table unavailable")
        return

    joints = joints.copy()
    for col in ("GlobalX", "GlobalY", "GlobalZ"):
        joints[col] = pd.to_numeric(joints[col], errors="coerce")
    joints = joints.dropna(subset=["GlobalX", "GlobalY", "GlobalZ"])

    try:
        if not etabs_style_3d(tables, out, elev, azim):
            print("[WARN] ETABS-style 3D skipped; using scatter only")
    except Exception as exc:  # never let the 3D view break the other figures
        print(f"[WARN] ETABS-style 3D failed: {exc}")

    fig = plt.figure(figsize=(8, 5.5))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(joints["GlobalX"], joints["GlobalY"], joints["GlobalZ"], s=8, c=BLUE)
    ax.set_title("ETABS Key Frame – Extracted Joint Geometry")
    ax.set_xlabel("Global X"); ax.set_ylabel("Global Y"); ax.set_zlabel("Global Z")
    save(out, "01_key_frame")

    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.scatter(joints["GlobalX"], joints["GlobalY"], s=9, c=BLUE)
    ax.set_title("Beam and Column Grid Plan – Extracted Joint Layout")
    ax.set_xlabel("Global X"); ax.set_ylabel("Global Y")
    ax.set_aspect("equal", adjustable="datalim"); ax.grid(alpha=.25)
    save(out, "02_grid_plan")

    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.scatter(joints["GlobalX"], joints["GlobalZ"], s=9, c=BLUE)
    ax.set_title("Beam and Column Sectional View – Extracted Joint Elevation")
    ax.set_xlabel("Global X"); ax.set_ylabel("Global Z"); ax.grid(alpha=.25)
    save(out, "03_sectional_view")


def modal_figures(tables: Path, out: Path) -> None:
    periods = read(tables, "01_Modal_Periods")
    if periods is not None and {"Mode", "Period"}.issubset(periods.columns):
        p = periods.copy().sort_values("Mode")
        p["Period"] = pd.to_numeric(p["Period"], errors="coerce")
        p = p.dropna(subset=["Period"])
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        ax.bar(p["Mode"].astype(str), p["Period"], color=BLUE)
        ax.set_title("Modal Periods")
        ax.set_xlabel("Mode"); ax.set_ylabel("Period (s)"); ax.grid(axis="y", alpha=.25)
        save(out, "04_mode_1")

    mass = read(tables, "02_Modal_Mass_Ratios")
    if mass is not None and {"Mode", "SumUX", "SumUY"}.issubset(mass.columns):
        m = mass.copy().sort_values("Mode")
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        ax.plot(m["Mode"], pd.to_numeric(m["SumUX"], errors="coerce"), marker="o", label="SumUX", color=BLUE)
        ax.plot(m["Mode"], pd.to_numeric(m["SumUY"], errors="coerce"), marker="o", label="SumUY", color=ORANGE)
        ax.axhline(.90, color=RED, linestyle="--", linewidth=1, label="90% reference")
        ax.set_title("Cumulative Modal Mass Participation")
        ax.set_xlabel("Mode"); ax.set_ylabel("Cumulative participation"); ax.set_ylim(0, 1.05)
        ax.legend(); ax.grid(alpha=.25)
        save(out, "05_modal_mass")


def drift_figures(tables: Path, out: Path) -> None:
    drifts = read(tables, "04_Story_Drifts")
    if drifts is None or not {"Story", "Drift", "Direction"}.issubset(drifts.columns):
        print("[SKIP] Drift figures: story-drift table unavailable")
        return
    for direction, filename in (("X", "06_drift_x"), ("Y", "06_drift_y")):
        subset = drifts[drifts["Direction"].astype(str).str.upper().str.contains(direction)].copy()
        subset["Drift"] = pd.to_numeric(subset["Drift"], errors="coerce")
        subset = subset.dropna(subset=["Drift"])
        if subset.empty:
            continue
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        ax.bar(subset["Story"].astype(str), subset["Drift"], color=GREEN)
        ax.set_title(f"Storey Drift in {direction} Direction")
        ax.set_xlabel("Story"); ax.set_ylabel("Drift")
        ax.tick_params(axis="x", rotation=45); ax.grid(axis="y", alpha=.25)
        save(out, filename)


def reaction_figures(tables: Path, out: Path) -> None:
    reactions = read(tables, "03_Base_Reactions")
    if reactions is None or not {"OutputCase", "FX", "FY"}.issubset(reactions.columns):
        print("[SKIP] Reaction figure: base-reaction table unavailable")
        return
    r = reactions.copy().head(20)
    r["FX"] = pd.to_numeric(r["FX"], errors="coerce")
    r["FY"] = pd.to_numeric(r["FY"], errors="coerce")
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    x = list(range(len(r))); width = .38
    ax.bar([i - width/2 for i in x], r["FX"], width, label="FX", color=BLUE)
    ax.bar([i + width/2 for i in x], r["FY"], width, label="FY", color=ORANGE)
    ax.set_title("Base Reaction Summary")
    ax.set_ylabel("Reaction"); ax.set_xticks(x)
    ax.set_xticklabels(r["OutputCase"].astype(str), rotation=45, ha="right")
    ax.legend(); ax.grid(axis="y", alpha=.25)
    save(out, "07_joint_reaction")


def member_figures(tables: Path, out: Path) -> None:
    beam_flex = first_available(read(tables, "08b_Beam_Flexure_Env"), read(tables, "08_Beam_Design"))
    if beam_flex is not None:
        if {"MomentTop", "MomentBot"}.issubset(beam_flex.columns):
            b = beam_flex.copy().head(50)
            fig, ax = plt.subplots(figsize=(7.5, 4.5))
            ax.plot(pd.to_numeric(b["MomentTop"], errors="coerce"), label="MomentTop", color=BLUE)
            ax.plot(pd.to_numeric(b["MomentBot"], errors="coerce"), label="MomentBot", color=ORANGE)
            ax.set_title("Beam Moment Demand Summary")
            ax.set_xlabel("Extracted beam row"); ax.set_ylabel("Moment")
            ax.legend(); ax.grid(alpha=.25)
            save(out, "08_moment")
        if {"AsTop", "AsBot"}.issubset(beam_flex.columns):
            b = beam_flex.copy().head(50)
            fig, ax = plt.subplots(figsize=(7.5, 4.5))
            ax.plot(pd.to_numeric(b["AsTop"], errors="coerce"), label="AsTop", color=BLUE)
            ax.plot(pd.to_numeric(b["AsBot"], errors="coerce"), label="AsBot", color=ORANGE)
            ax.set_title("Beam Reinforcement Demand")
            ax.set_xlabel("Extracted beam row"); ax.set_ylabel("Area of steel")
            ax.legend(); ax.grid(alpha=.25)
            save(out, "10_beam_design")

    column = first_available(read(tables, "07b_Column_PMM_Env"), read(tables, "07_Column_Design"))
    if column is not None:
        if "P" in column.columns:
            c = column.copy().head(50)
            fig, ax = plt.subplots(figsize=(7.5, 4.5))
            ax.bar(range(len(c)), pd.to_numeric(c["P"], errors="coerce"), color=GREY)
            ax.set_title("Column Axial Force Demand")
            ax.set_xlabel("Extracted column row"); ax.set_ylabel("Axial force")
            ax.grid(axis="y", alpha=.25)
            save(out, "09_axial")
        if "RatioRebar" in column.columns:
            c = column.copy().head(50)
            fig, ax = plt.subplots(figsize=(7.5, 4.5))
            ax.bar(range(len(c)), pd.to_numeric(c["RatioRebar"], errors="coerce"), color=GREY)
            ax.axhline(1.0, color=RED, linestyle="--", linewidth=1, label="Ratio = 1.0")
            ax.set_title("Column Reinforcement Ratio Demand")
            ax.set_xlabel("Extracted column row"); ax.set_ylabel("RatioRebar")
            ax.legend(); ax.grid(axis="y", alpha=.25)
            save(out, "11_column_design")

    beam = read(tables, "08_Beam_Design")
    if beam is not None and {"AsTop", "AsBot"}.issubset(beam.columns):
        b = beam.copy()
        b["AsTop"] = pd.to_numeric(b["AsTop"], errors="coerce")
        b["AsBot"] = pd.to_numeric(b["AsBot"], errors="coerce")
        max_values = [b["AsTop"].max(), b["AsBot"].max()]
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        ax.bar(["AsTop", "AsBot"], max_values, color=[BLUE, ORANGE])
        ax.set_title("Governing Reinforcement Areas")
        ax.set_ylabel("Area of steel"); ax.grid(axis="y", alpha=.25)
        save(out, "12_reinforcement")


def main() -> int:
    cfg = parse_args()
    cfg.output.mkdir(parents=True, exist_ok=True)
    style()
    geometry_figures(cfg.tables, cfg.output, cfg.elev, cfg.azim)
    modal_figures(cfg.tables, cfg.output)
    drift_figures(cfg.tables, cfg.output)
    reaction_figures(cfg.tables, cfg.output)
    member_figures(cfg.tables, cfg.output)
    print(f"Figures written to {cfg.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())