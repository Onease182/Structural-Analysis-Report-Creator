#!/usr/bin/env python3
"""Tolerant section tokenizer for the ETABS .e2k text format.

Parses the .e2k file into a dict of named sections, each containing
header (column names) and rows (list of dicts). Unknown sections are
kept raw in the "unparsed" key.

Usage:
    from src.e2k_parser import E2KParser
    parser = E2KParser()
    data = parser.parse_file("path/to/model.e2k")
    print(data["stories"])
    parser.reconcile("tables/", "mismatch_report.md")
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any


class E2KParser:
    """Tolerant .e2k section tokenizer."""

    # Known section names and their canonical output keys
    SECTION_MAP: dict[str, str] = {
        "STORYDATA": "stories",
        "GRIDS": "grids",
        "POINTCOORD": "points",
        "FRAMEOBJ": "frames",
        "AREAOBJ": "areas",
        "FRAMESECTIONS": "frame_sections",
        "AREASECTIONS": "area_sections",
        "MATERIALS": "materials",
        "PROPMODIFIERS": "property_modifiers",
        "DIAPHRAGMS": "diaphragms",
        "POINTRESTRAINTS": "restraints",
        "LOADPATTS": "load_patterns",
        "LOADCOMBOS": "load_combos",
        "MASSSOURCE": "mass_source",
        "STIFFNESS": "stiffness",
    }

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.unparsed: list[str] = []

    def parse_file(self, path: str | Path) -> dict[str, Any]:
        """Parse an .e2k file into structured data."""
        path = Path(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        return self.parse_text(text)

    def parse_text(self, text: str) -> dict[str, Any]:
        """Parse .e2k text into structured data."""
        self.data = {}
        self.unparsed = []
        current_section: str | None = None
        current_lines: list[str] = []

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            # Detect section headers: "$ SECTIONNAME" or "$ Section Name"
            if stripped.startswith("$"):
                # Save previous section
                if current_section is not None:
                    self._process_section(current_section, current_lines)
                # Parse new section name
                section_raw = stripped[1:].strip()
                # Normalize: remove spaces, uppercase
                section_name = re.sub(r"\s+", "", section_raw).upper()
                current_section = section_name
                current_lines = []
            elif current_section is not None:
                current_lines.append(stripped)
            # Lines before any section header are ignored

        # Save last section
        if current_section is not None:
            self._process_section(current_section, current_lines)

        # Store unparsed sections
        if self.unparsed:
            self.data["unparsed"] = self.unparsed

        return self.data

    def _process_section(self, section_name: str, lines: list[str]) -> None:
        """Process a section's lines into structured data."""
        output_key = self.SECTION_MAP.get(section_name)
        if output_key is None:
            # Unknown section — keep raw
            self.unparsed.append(f"$ {section_name}\n" + "\n".join(lines))
            return

        if not lines:
            self.data[output_key] = []
            return

        # First non-empty line is the header
        header_line = lines[0]
        headers = re.split(r"\s+", header_line.strip())
        headers = [h.strip() for h in headers if h.strip()]

        # Remaining lines are data
        rows: list[dict[str, str]] = []
        for line in lines[1:]:
            values = re.split(r"\s+", line.strip())
            values = [v.strip() for v in values if v.strip() or True]  # keep empty
            # Pad or truncate to match headers
            while len(values) < len(headers):
                values.append("")
            values = values[:len(headers)]
            row = dict(zip(headers, values))
            rows.append(row)

        self.data[output_key] = rows

    def reconcile(self, tables_dir: str | Path, output_path: str | Path | None = None) -> list[str]:
        """Reconcile .e2k data against tables/ CSVs. Returns mismatch messages."""
        tables_dir = Path(tables_dir)
        mismatches: list[str] = []

        # Reconcile stories
        if "stories" in self.data and tables_dir.exists():
            story_csv = tables_dir / "Story Data.csv"
            if story_csv.exists():
                csv_stories = self._read_csv(story_csv)
                e2k_stories = {s.get("Story", ""): s for s in self.data["stories"]}
                for row in csv_stories:
                    name = row.get("Story", row.get("Name", ""))
                    if name and name not in e2k_stories:
                        mismatches.append(f"Story '{name}' in CSV but not in .e2k")
                for name in e2k_stories:
                    if name and not any(name == r.get("Story", r.get("Name", "")) for r in csv_stories):
                        mismatches.append(f"Story '{name}' in .e2k but not in CSV")
            else:
                mismatches.append(f"Story Data CSV not found at {story_csv}")
        else:
            if not tables_dir.exists():
                mismatches.append(f"tables/ directory not found: {tables_dir}")
            if "stories" not in self.data:
                mismatches.append("No stories section in .e2k")

        # Reconcile materials
        if "materials" in self.data and tables_dir.exists():
            mat_csv = tables_dir / "Material Properties.csv"
            if mat_csv.exists():
                csv_mats = self._read_csv(mat_csv)
                e2k_mats = {m.get("Material", "") for m in self.data["materials"]}
                for row in csv_mats:
                    name = row.get("Material", row.get("Name", ""))
                    if name and name not in e2k_mats:
                        mismatches.append(f"Material '{name}' in CSV but not in .e2k")

        # Reconcile load patterns
        if "load_patterns" in self.data and tables_dir.exists():
            lp_csv = tables_dir / "Load Patterns.csv"
            if lp_csv.exists():
                csv_lps = self._read_csv(lp_csv)
                e2k_lps = {lp.get("LoadPat", "") for lp in self.data["load_patterns"]}
                for row in csv_lps:
                    name = row.get("LoadPat", row.get("Name", ""))
                    if name and name not in e2k_lps:
                        mismatches.append(f"Load pattern '{name}' in CSV but not in .e2k")

        # Write mismatch report
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as f:
                if mismatches:
                    f.write("# E2K Reconciliation Mismatches\n\n")
                    for m in mismatches:
                        f.write(f"- {m}\n")
                else:
                    f.write("# E2K Reconciliation Mismatches\n\nNone.\n")

        return mismatches

    def _read_csv(self, path: Path) -> list[dict[str, str]]:
        """Read a CSV file into a list of dicts."""
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def get_stories(self) -> list[dict[str, str]]:
        return self.data.get("stories", [])

    def get_grids(self) -> list[dict[str, str]]:
        return self.data.get("grids", [])

    def get_points(self) -> list[dict[str, str]]:
        return self.data.get("points", [])

    def get_frames(self) -> list[dict[str, str]]:
        return self.data.get("frames", [])

    def get_areas(self) -> list[dict[str, str]]:
        return self.data.get("areas", [])

    def get_frame_sections(self) -> list[dict[str, str]]:
        return self.data.get("frame_sections", [])

    def get_area_sections(self) -> list[dict[str, str]]:
        return self.data.get("area_sections", [])

    def get_materials(self) -> list[dict[str, str]]:
        return self.data.get("materials", [])

    def get_restraints(self) -> list[dict[str, str]]:
        return self.data.get("restraints", [])

    def get_load_patterns(self) -> list[dict[str, str]]:
        return self.data.get("load_patterns", [])

    def get_load_combos(self) -> list[dict[str, str]]:
        return self.data.get("load_combos", [])

    def get_mass_source(self) -> list[dict[str, str]]:
        return self.data.get("mass_source", [])

    def get_diaphragms(self) -> list[dict[str, str]]:
        return self.data.get("diaphragms", [])

    def get_unparsed(self) -> list[str]:
        return self.unparsed


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, help="Path to .e2k file")
    p.add_argument("--tables", default="tables", help="Path to tables/ directory")
    p.add_argument("--output", default="e2k_mismatch_report.md", help="Mismatch report output path")
    args = p.parse_args()

    parser = E2KParser()
    data = parser.parse_file(args.input)
    print(f"[OK] Parsed {args.input}")
    for key, val in data.items():
        if key == "unparsed":
            print(f"  {key}: {len(val)} unparsed sections")
        else:
            print(f"  {key}: {len(val)} rows")

    mismatches = parser.reconcile(args.tables, args.output)
    print(f"[OK] Reconciliation: {len(mismatches)} mismatches")
    if mismatches:
        print(f"[OK] Report: {args.output}")
        for m in mismatches[:5]:
            print(f"  - {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
