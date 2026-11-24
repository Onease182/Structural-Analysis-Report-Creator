#!/usr/bin/env python3
"""Generate the SLS ETABS .e2k text model from the ULS .e2k (NBC 105:2025).

What changes between the ULS and SLS models (verified against
Chatra_bdr_ULS.e2k / Chatra_bdr_SLS.e2k):

1. Cracked-section stiffness modifiers (I2MOD / I3MOD) on frame sections.
     ULS (Table 3-1): beams 0.35, columns 0.70
     SLS            : beams 0.70, columns 0.90
2. Seismic load patterns / load cases / combos:  EQX-ULS -> EQX-SLS, EQY-ULS -> EQY-SLS
3. SHEARCOEFF of the user-coefficient seismic patterns.
     ULS: Cd = C(T) / (Rmu * Omega_u)
     SLS: Cd = 0.20 * C(T) / Omega_s
   so   Cd_SLS = Cd_ULS * 0.20 * Rmu * Omega_u / Omega_s
   (RC moment frame: 0.1458 * 0.20 * 4 * 1.5 / 1.25 = 0.13997, ETABS file has 0.14)

Nothing is guessed: a section that cannot be classified as beam or column or a
missing pattern stops the run (exit 2) unless --force is given. A modifier that is
not the standard ULS value (e.g. 0.0001 on a hidden beam) is kept unchanged and
reported; use --strict to stop on it instead. Line endings (CRLF) are preserved.

Usage:
    python make_sls_e2k.py                      # newest *.e2k in tables\\ -> sls_tables\\<name>_SLS.e2k
    python make_sls_e2k.py --uls model_ULS.e2k --out model_SLS.e2k
    python make_sls_e2k.py --compare Chatra_bdr_SLS.e2k   # diff against an existing SLS file
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def find_latest_e2k(folder: Path) -> Path | None:
    files = sorted(folder.glob("*.e2k"), key=lambda p: p.stat().st_mtime, reverse=True)
    files = [f for f in files if "SLS" not in f.stem.upper()]
    return files[0] if files else None


def classify_sections(lines: list[str]) -> dict[str, str]:
    """Section name -> 'Beam' | 'Column' from the $ CONCRETE SECTIONS block."""
    out: dict[str, str] = {}
    in_block = False
    for ln in lines:
        s = ln.strip()
        if s.startswith("$"):
            in_block = s.upper().startswith("$ CONCRETE SECTIONS")
            continue
        if in_block and s.startswith("CONCRETESECTION"):
            m = re.match(r'CONCRETESECTION\s+"([^"]+)"', s)
            t = re.search(r'\bTYPE\s+"([^"]+)"', s)
            if m and t:
                out[m.group(1)] = t.group(1).title()
    return out


def convert(text: str, args: argparse.Namespace) -> tuple[str, list[str], list[str]]:
    """Return (new_text, change_log, problems)."""
    lines = text.split("\n")  # keeps '\r' on each line, so CRLF survives
    log: list[str] = []
    problems: list[str] = []
    kinds = classify_sections(lines)
    ratio = args.cs_factor * args.rmu * args.omega_u / args.omega_s

    cases = [(args.uls_x, args.sls_x), (args.uls_y, args.sls_y)]
    section = ""
    seen_pat = {c[0]: False for c in cases}
    out: list[str] = []

    for ln in lines:
        s = ln.strip()
        if s.startswith("$"):
            section = s.upper()
            out.append(ln)
            continue
        new = ln

        # 1. stiffness modifiers
        if section.startswith("$ FRAME SECTIONS") and "I2MOD" in s:
            m = re.match(r'FRAMESECTION\s+"([^"]+)"', s)
            name = m.group(1) if m else ""
            kind = kinds.get(name)
            if kind not in ("Beam", "Column"):
                problems.append(f"cannot classify frame section '{name}' as Beam/Column "
                                f"(found: {kind!r}); no modifier written")
            else:
                exp = args.col_uls if kind == "Column" else args.beam_uls
                tgt = args.col_sls if kind == "Column" else args.beam_sls
                cur = re.search(r"I2MOD\s+([\d.]+)", s)
                if cur and abs(float(cur.group(1)) - exp) > 1e-9:
                    # Non-standard modifier (e.g. 0.0001 on a hidden / load-transfer beam).
                    # Keep it exactly as modelled and say so; --strict stops instead.
                    msg = (f"'{name}' ({kind}) has I2MOD {cur.group(1)} in the ULS model, "
                           f"not the standard {exp:g}")
                    if args.strict:
                        problems.append(msg)
                    else:
                        log.append(f"modifier  {name} ({kind}): {cur.group(1)} KEPT UNCHANGED - "
                                   f"not the standard ULS {exp:g}, assumed intentional")
                else:
                    new = re.sub(r"(I[23]MOD\s+)[\d.]+", lambda mm: f"{mm.group(1)}{tgt:g}", ln)
                    log.append(f"modifier  {name} ({kind}): {exp:g} -> {tgt:g}")

        # 2. seismic patterns, load cases, combos
        for uls, sls in cases:
            if f'"{uls}"' in new:
                if section.startswith("$ LOAD PATTERNS") and s.startswith("LOADPATTERN"):
                    seen_pat[uls] = True
                new = new.replace(f'"{uls}"', f'"{sls}"')

        # 3. base-shear coefficient
        if s.startswith("SEISMIC") and "SHEARCOEFF" in s:
            if any(f'"{sls}"' in new for _, sls in cases):
                m = re.search(r"SHEARCOEFF\s+([\d.]+)", new)
                if m:
                    cd_uls = float(m.group(1))
                    cd_sls = round(cd_uls * ratio, args.decimals)
                    new = new.replace(m.group(0), f"SHEARCOEFF {cd_sls:g}")
                    log.append(f"SHEARCOEFF {cd_uls:g} -> {cd_sls:g}  (x{ratio:.4f})")
        out.append(new)

    for uls, ok in seen_pat.items():
        if not ok:
            problems.append(f"load pattern '{uls}' not found in the ULS model")
    return "\n".join(out), log, problems


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--uls", help="ULS .e2k (default: newest non-SLS .e2k in --uls-dir)")
    p.add_argument("--uls-dir", default=str(HERE / "tables"))
    p.add_argument("--out", help="output SLS .e2k (default: <sls-dir>/<stem>_SLS.e2k)")
    p.add_argument("--sls-dir", default=str(HERE / "sls_tables"))
    p.add_argument("--uls-x", default="EQX-ULS"); p.add_argument("--uls-y", default="EQY-ULS")
    p.add_argument("--sls-x", default="EQX-SLS"); p.add_argument("--sls-y", default="EQY-SLS")
    p.add_argument("--beam-uls", type=float, default=0.35); p.add_argument("--col-uls", type=float, default=0.70)
    p.add_argument("--beam-sls", type=float, default=0.70); p.add_argument("--col-sls", type=float, default=0.90)
    p.add_argument("--rmu", type=float, default=4.0, help="ductility factor (Table 5-2)")
    p.add_argument("--omega-u", type=float, default=1.5, help="ULS overstrength")
    p.add_argument("--omega-s", type=float, default=1.25, help="SLS overstrength")
    p.add_argument("--cs-factor", type=float, default=0.20, help="SLS spectrum factor Cs = f*C")
    p.add_argument("--decimals", type=int, default=4)
    p.add_argument("--compare", help="existing SLS .e2k to diff the result against")
    p.add_argument("--strict", action="store_true",
                   help="stop if any ULS modifier is not the standard value (default: keep it and report)")
    p.add_argument("--force", action="store_true", help="write the file even if problems were found")
    a = p.parse_args()

    uls = Path(a.uls) if a.uls else find_latest_e2k(Path(a.uls_dir))
    if not uls or not uls.exists():
        print(f"[ERROR] No ULS .e2k found (looked in {a.uls_dir}). Use --uls.")
        return 1
    out = Path(a.out) if a.out else Path(a.sls_dir) / (re.sub(r"(?i)_?uls", "", uls.stem) + "_SLS.e2k")

    raw = uls.read_bytes().decode("utf-8", errors="replace")
    new, log, problems = convert(raw, a)

    print(f"[SLS-E2K] source : {uls}")
    for l in log:
        print(f"[SLS-E2K]   {l}")
    for pr in problems:
        print(f"[SLS-E2K] PROBLEM: {pr}")
    if problems and not a.force:
        print("[SLS-E2K] Stopped. Resolve the problems above or re-run with --force.")
        return 2

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(new.encode("utf-8"))
    print(f"[SLS-E2K] written: {out}")

    if a.compare:
        import difflib
        ref = Path(a.compare).read_bytes().decode("utf-8", errors="replace").split("\n")
        mine = new.split("\n")
        skip = lambda l: l.startswith("$ File") or l.startswith("ETABS ") or l.strip() in ("", "$ SECTION DESIGNER SECTIONS")
        d = [l for l in difflib.unified_diff([x for x in ref if not skip(x)],
                                             [x for x in mine if not skip(x)], lineterm="", n=0)
             if not l.startswith(("---", "+++", "@@"))]
        print(f"[SLS-E2K] differences vs {a.compare} (headers/log lines ignored): {len(d)}")
        for l in d[:20]:
            print("   ", l.rstrip())
        return 0 if not d else 3
    print("[SLS-E2K] Open this file in ETABS (File > Open), run analysis, save the .EDB, "
          "then run etabs_extract_sls_drifts.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
