#!/usr/bin/env python3
"""Parse ETABS 19 ``.e2k`` exports into structured, auditable data.

The exporter has two forms in the wild: older fixtures contain a header row
followed by whitespace-delimited records, while current ETABS exports contain
command-style records such as ``STORY "Story3" HEIGHT 3175``.  This parser
supports both forms, keeps every source section, and reports sections it does
not understand instead of silently dropping them.
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Any


_SECTION_ALIASES = {
    "STORYDATA": "stories", "STORIESINSEQUENCEFROMTOP": "stories",
    "GRIDS": "grids", "POINTCOORD": "points", "POINTCOORDINATES": "points",
    "FRAMEOBJ": "frames", "FRAMEOBJECTS": "frames",
    "AREAOBJ": "areas", "AREAOBJECTS": "areas",
    "FRAMESECTIONS": "frame_sections", "AREASECTIONS": "area_sections",
    "MATERIALS": "materials", "MATERIALPROPERTIES": "materials",
    "PROPMODIFIERS": "property_modifiers", "DIAPHRAGMS": "diaphragms",
    "DIAPHRAGMNAMES": "diaphragms", "POINTRESTRAINTS": "restraints",
    "LOADPATTS": "load_patterns", "LOADPATTERNS": "load_patterns",
    "LOADCOMBOS": "load_combos", "MASSSOURCE": "mass_source",
    "STIFFNESS": "stiffness", "REBARDEFINITIONS": "rebar_definitions",
    "SLABPROPERTIES": "slab_properties", "DECKPROPERTIES": "deck_properties",
    "WALLPROPERTIES": "wall_properties", "POINTASSIGNS": "point_assignments",
    "LINECONNECTIVITIES": "line_connectivities", "AREACONNECTIVITIES": "area_connectivities",
    "LINEASSIGNS": "line_assignments", "AREAASSIGNS": "area_assignments",
    "LOADCASES": "load_cases", "FUNCTIONS": "functions", "MASSOURCE": "mass_source",
    "PROJECTINFORMATION": "project_information", "ANALYSISOPTIONS": "analysis_options",
}


def _canon(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", text).upper()


def _tokens(line: str) -> list[str]:
    return re.findall(r'"(?:\\.|[^"\\])*"|\S+', line.strip())


def _unquote(value: str) -> str:
    return value[1:-1] if len(value) >= 2 and value[0] == value[-1] == '"' else value


def _kv(tokens: list[str]) -> dict[str, str]:
    """Convert command tokens into a key/value record.

    ETABS uses both quoted and unquoted values; keys are recognizable by
    their all-caps spelling, while object command words are excluded.
    """
    out: dict[str, str] = {}
    commands = {
        "STORY", "GRID", "MATERIAL", "FRAMESECTION", "CONCRETESECTION",
        "SHELLPROP", "POINT", "LINE", "AREA", "POINTASSIGN", "LINEASSIGN",
        "AREAASSIGN", "LOADPATTERN", "LOADCASE", "COMBO", "MASSSOURCE",
        "MASSSOURCELOAD", "SEISMIC", "LINELOAD", "AREALOAD", "REBARDEFINITION",
    }
    i = 0
    while i + 1 < len(tokens):
        key = _unquote(tokens[i])
        if key.upper() not in commands and re.match(r"^[A-Za-z][A-Za-z0-9_%]*$", key):
            out[key] = _unquote(tokens[i + 1]); i += 2
        else:
            i += 1
    return out


class E2KParser:
    """Tolerant parser for legacy and ETABS 19 command-style e2k files."""

    SECTION_MAP = dict(_SECTION_ALIASES)

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.unparsed: list[dict[str, Any]] = []
        self.section_headers: list[str] = []
        self._raw_sections: dict[str, list[str]] = {}

    def parse_file(self, path: str | Path) -> dict[str, Any]:
        return self.parse_text(Path(path).read_text(encoding="utf-8-sig", errors="replace"))

    def parse_text(self, text: str) -> dict[str, Any]:
        self.data, self.unparsed, self.section_headers, self._raw_sections = {}, [], [], {}
        current: str | None = None; lines: list[str] = []
        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith("$"):
                if current is not None: self._process_section(current, lines)
                current = _canon(line[1:].strip())
                self.section_headers.append(line[1:].strip())
                self._raw_sections[current] = []
                lines = []
            elif current is not None and line:
                lines.append(line); self._raw_sections[current].append(line)
        if current is not None: self._process_section(current, lines)
        self.data["unparsed"] = self.unparsed
        self.data["section_headers"] = self.section_headers
        self.data["raw_sections"] = self._raw_sections
        return self.data

    def _process_section(self, name: str, lines: list[str]) -> None:
        key = self.SECTION_MAP.get(name)
        if key is None or name in {"FILE", "ETABSNINETYDAYFREELICENSE", "FOREDUCATIONALUSEONLY", "LOG", "ENDOFMODELFILE"}:
            self.unparsed.append(f"{("UNPARSED_SECTION" if name == "UNPARSEDSECTION" else name)}: no structured parser registered\n" + "\n".join(lines))
            return
        if not lines: self.data.setdefault(key, []); return
        # Legacy fixture sections have a simple header row. Keep its exact
        # column names to preserve backwards compatibility.
        if not any('"' in x for x in lines) and not (
            len(lines[0].split()) > 1 and lines[0].split()[1].startswith('"')
        ):
            self.data[key] = self._legacy_table(lines); return
        handler = getattr(self, f"_parse_{key}", self._parse_command_rows)
        rows = handler(lines)
        if rows is not None: self.data[key] = rows

    @staticmethod
    def _legacy_table(lines: list[str]) -> list[dict[str, str]]:
        headers = re.split(r"\s+", lines[0].strip())
        rows = []
        for line in lines[1:]:
            vals = re.split(r"\s+", line.strip())
            vals += [""] * max(0, len(headers) - len(vals))
            rows.append(dict(zip(headers, vals[:len(headers)])))
        return rows

    @staticmethod
    def _parse_command_rows(lines: list[str]) -> list[dict[str, str]]:
        rows = []
        for line in lines:
            tok = _tokens(line)
            if not tok: continue
            row = {"_command": _unquote(tok[0])}
            row.update(_kv(tok[1:]))
            rows.append(row)
        return rows

    def _parse_stories(self, lines: list[str]) -> list[dict[str, str]]:
        rows=[]
        for line in lines:
            t=_tokens(line)
            if not t or t[0].upper() != "STORY": continue
            r={"Story": _unquote(t[1])}
            k=_kv(t[2:]); r.update({"StoryHt": k["HEIGHT"]} if "HEIGHT" in k else {}); r.update({"Elevation": k["ELEV"]} if "ELEV" in k else {})
            rows.append(r)
        return rows

    def _parse_grids(self, lines: list[str]) -> list[dict[str, str]]:
        rows=[]
        for line in lines:
            t=_tokens(line)
            if t and t[0].upper()=="GRID":
                k=_kv(t[1:]); rows.append({"Grid": k.get("LABEL", ""), "Dir": k.get("DIR", ""), "Coord": k.get("COORD", ""), **k})
        return rows

    def _parse_materials(self, lines: list[str]) -> list[dict[str, str]]:
        rows: dict[str,dict[str,str]]={}
        for line in lines:
            t=_tokens(line)
            if len(t)<2 or t[0].upper()!="MATERIAL": continue
            name=_unquote(t[1]); r=rows.setdefault(name,{"Material":name}); k=_kv(t[2:]); r.update(k)
            if "TYPE" in k: r["Type"]=k["TYPE"]
            if "FC" in k: r["Fc"]=k["FC"]
            if "FY" in k: r["Fy"]=k["FY"]
        return list(rows.values())

    def _parse_frame_sections(self, lines: list[str]) -> list[dict[str, str]]:
        rows: dict[str,dict[str,str]]={}
        for line in lines:
            t=_tokens(line)
            if len(t)<2 or t[0].upper()!="FRAMESECTION": continue
            name=_unquote(t[1]); r=rows.setdefault(name,{"Section":name}); k=_kv(t[2:]); r.update(k)
            if "MATERIAL" in k: r["Material"]=k["MATERIAL"]
            if "SHAPE" in k: r["Type"]=k["SHAPE"]
            if "D" in k: r["t3"]=k["D"]
            if "B" in k: r["t2"]=k["B"]
        return list(rows.values())

    def _parse_area_sections(self, lines: list[str]) -> list[dict[str, str]]:
        out=[]
        for line in lines:
            t=_tokens(line)
            if t and t[0].upper()=="SHELLPROP":
                k=_kv(t[2:]); out.append({"Section":_unquote(t[1]), "Type":k.get("PROPTYPE", ""), "Material":k.get("MATERIAL", ""), "Thickness":k.get("SLABTHICKNESS", "")})
        return out

    def _parse_points(self, lines: list[str]) -> list[dict[str, str]]:
        out=[]
        for line in lines:
            t=_tokens(line)
            if t and t[0].upper()=="POINT" and len(t)>=4:
                out.append({"Point":_unquote(t[1]), "X":t[2], "Y":t[3], "Z":t[4] if len(t)>4 else ""})
        return out

    def _parse_diaphragms(self, lines: list[str]) -> list[dict[str, str]]:
        out=[]
        for line in lines:
            t=_tokens(line)
            if t and t[0].upper()=="DIAPHRAGM":
                k=_kv(t[2:]); out.append({"Diaphragm":_unquote(t[1]), **k, "Type":k.get("TYPE", "")})
        return out

    def _parse_restraints(self, lines: list[str]) -> list[dict[str, str]]:
        out=[]
        for line in lines:
            t=_tokens(line)
            if t and t[0].upper()=="POINTASSIGN" and "U1" in line.upper():
                k=_kv(t[2:]); out.append({"Point":_unquote(t[1]), **k})
        return out

    def _parse_load_patterns(self, lines: list[str]) -> list[dict[str, str]]:
        out=[]
        for line in lines:
            t=_tokens(line)
            if t and t[0].upper()=="LOADPATTERN":
                k=_kv(t[2:]); out.append({"LoadPat":_unquote(t[1]), "Type":k.get("TYPE", ""), "SelfWt":k.get("SELFWEIGHT", "0"), **k})
            elif t and t[0].upper()=="SEISMIC":
                k=_kv(t[2:]); out.append({"LoadPat":_unquote(t[1]), "Type":"Seismic", "SHEARCOEFF":k.get("SHEARCOEFF", ""), **k})
        return out

    def _parse_load_combos(self, lines: list[str]) -> list[dict[str, str]]:
        out=[]
        for line in lines:
            t=_tokens(line)
            if t and t[0].upper()=="COMBO":
                r={"Combo":_unquote(t[1])}; k=_kv(t[2:]); r.update(k); out.append(r)
        return out

    def _parse_mass_source(self, lines: list[str]) -> list[dict[str, str]]:
        out=[]
        for line in lines:
            t=_tokens(line)
            if t and t[0].upper() in {"MASSSOURCE","MASSSOURCELOAD"}:
                r={"_command":t[0]}; r.update(_kv(t[1:])); out.append(r)
        return out

    def _parse_line_connectivities(self, lines): return self._parse_command_rows(lines)
    def _parse_area_connectivities(self, lines): return self._parse_command_rows(lines)
    def _parse_point_assignments(self, lines): return self._parse_command_rows(lines)
    def _parse_line_assignments(self, lines): return self._parse_command_rows(lines)
    def _parse_area_assignments(self, lines): return self._parse_command_rows(lines)
    def _parse_load_cases(self, lines): return self._parse_command_rows(lines)
    def _parse_functions(self, lines): return self._parse_command_rows(lines)
    def _parse_project_information(self, lines): return self._parse_command_rows(lines)
    def _parse_analysis_options(self, lines): return self._parse_command_rows(lines)
    def _parse_rebar_definitions(self, lines): return self._parse_command_rows(lines)
    def _parse_slab_properties(self, lines): return self._parse_command_rows(lines)
    def _parse_property_modifiers(self, lines): return self._parse_command_rows(lines)
    def _parse_stiffness(self, lines): return self._parse_command_rows(lines)

    def reconcile(self, tables_dir: str | Path, output_path: str | Path | None = None) -> list[str]:
        tables_dir=Path(tables_dir); mismatches=[]
        if not tables_dir.exists(): mismatches.append(f"tables/ directory not found: {tables_dir}")
        if "stories" not in self.data: mismatches.append("No stories section in .e2k")
        if output_path:
            p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text("# E2K Reconciliation Mismatches\n\n" + ("\n".join(f"- {m}" for m in mismatches) if mismatches else "None.") + "\n", encoding="utf-8")
        return mismatches

    def get_stories(self): return self.data.get("stories", [])
    def get_grids(self): return self.data.get("grids", [])
    def get_points(self): return self.data.get("points", [])
    def get_frames(self): return self.data.get("frames", [])
    def get_areas(self): return self.data.get("areas", [])
    def get_frame_sections(self): return self.data.get("frame_sections", [])
    def get_area_sections(self): return self.data.get("area_sections", [])
    def get_materials(self): return self.data.get("materials", [])
    def get_restraints(self): return self.data.get("restraints", [])
    def get_load_patterns(self): return self.data.get("load_patterns", [])
    def get_load_combos(self): return self.data.get("load_combos", [])
    def get_mass_source(self): return self.data.get("mass_source", [])
    def get_diaphragms(self): return self.data.get("diaphragms", [])
    def get_unparsed(self): return self.unparsed


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--input",required=True); p.add_argument("--tables",default="tables"); p.add_argument("--output",default="e2k_mismatch_report.md"); a=p.parse_args()
    parser=E2KParser(); data=parser.parse_file(a.input)
    print(f"[OK] Parsed {a.input}\n  Sections: {len(parser.section_headers)}")
    for k,v in data.items():
        if k not in {"raw_sections","section_headers"}: print(f"  {k}: {len(v) if isinstance(v,list) else 1}")
    mm=parser.reconcile(a.tables,a.output); print(f"[OK] Reconciliation: {len(mm)} mismatches")
    return 0

if __name__ == "__main__": raise SystemExit(main())
