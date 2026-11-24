#!/usr/bin/env python3
"""Open the generated SLS .e2k in the running ETABS and save it as an .EDB.

Replaces the manual "File > Import > ETABS .e2k Text File ... Save" step.
The analysis itself is run afterwards by etabs_extract_sls_drifts.py
(it runs the analysis when the model is not locked).

WARNING: File.OpenFile replaces the model currently open in ETABS (the ULS model).
Run it only after the ULS extraction, and save any ULS changes first.

Usage:
    python etabs_open_sls_model.py                       # newest *_SLS.e2k in sls_tables\\
    python etabs_open_sls_model.py --e2k path\\model_SLS.e2k [--edb path\\model_SLS.EDB]
Exit codes: 0 ok, 1 could not attach / open / save, 2 SLS cases missing after opening.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import comtypes.client
except ImportError:                    # lets the script be imported/tested without ETABS
    comtypes = None

HERE = Path(__file__).resolve().parent


def connect():
    if comtypes is None:
        sys.exit("comtypes is not installed: pip install comtypes")
    try:
        return comtypes.client.GetActiveObject("CSI.ETABS.API.ETABSObject").SapModel
    except Exception as exc:
        sys.exit(f"Could not attach to ETABS. Start ETABS first. ({exc})")


def ret_code(r):
    return r[-1] if isinstance(r, (tuple, list)) else r


def open_and_save(model, e2k: Path, edb: Path, cases=("EQX-SLS", "EQY-SLS")) -> int:
    try:
        ret = ret_code(model.File.OpenFile(str(e2k)))
    except Exception as exc:
        print(f"[OPEN-SLS] OpenFile raised: {exc}")
        return 1
    if ret not in (0, None):
        print(f"[OPEN-SLS] OpenFile returned {ret} - this ETABS build did not open the .e2k.")
        return 1
    print(f"[OPEN-SLS] opened {e2k}")

    names = [n.lower() for n in (model.LoadCases.GetNameList()[1] or [])]
    missing = [c for c in cases if c.lower() not in names]
    if missing:
        print(f"[OPEN-SLS] load cases missing after opening: {missing}")
        return 2

    try:
        ret = ret_code(model.File.Save(str(edb)))
    except Exception as exc:
        print(f"[OPEN-SLS] Save raised: {exc}")
        return 1
    if ret not in (0, None):
        print(f"[OPEN-SLS] Save returned {ret}")
        return 1
    print(f"[OPEN-SLS] saved   {edb}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--e2k", help="SLS .e2k (default: newest *_SLS.e2k in --sls-dir)")
    p.add_argument("--edb", help="where to save the .EDB (default: next to the .e2k)")
    p.add_argument("--sls-dir", default=str(HERE / "sls_tables"))
    p.add_argument("--sls-x", default="EQX-SLS"); p.add_argument("--sls-y", default="EQY-SLS")
    a = p.parse_args()

    if a.e2k:
        e2k = Path(a.e2k)
    else:
        found = sorted(Path(a.sls_dir).glob("*_SLS.e2k"), key=lambda f: f.stat().st_mtime, reverse=True)
        e2k = found[0] if found else None
    if not e2k or not e2k.exists():
        print(f"[OPEN-SLS] No SLS .e2k found (looked in {a.sls_dir}). Run make_sls_e2k.py first.")
        return 1
    e2k = e2k.resolve()
    edb = Path(a.edb).resolve() if a.edb else e2k.with_suffix(".EDB")
    return open_and_save(connect(), e2k, edb, (a.sls_x, a.sls_y))


if __name__ == "__main__":
    sys.exit(main())
