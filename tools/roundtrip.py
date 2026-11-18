#!/usr/bin/env python3
"""Round-trip comparison: render the template with a sample context and
compare to the original Chatra Bahadur Ramtel.docx.

Outputs:
  - docs/roundtrip_diff.csv: every difference (location, kind, expected,
    actual, classification: owner_approved / unexpected)
  - docs/roundtrip_report.md: summary tables generated from the CSV

Exits non-zero if any "unexpected" difference exists.

Usage:
    python tools/roundtrip.py
"""
from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

import yaml
from docx import Document
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Inches

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "master_template.docx"
SAMPLE = ROOT / "Chatra Bahadur Ramtel.docx"
REGISTRY = ROOT / "config" / "placeholder_registry.yaml"
ALLOWED = ROOT / "config" / "roundtrip_allowed.yaml"
DIFF_CSV = ROOT / "docs" / "roundtrip_diff.csv"
REPORT_MD = ROOT / "docs" / "roundtrip_report.md"
BUILD_DIR = ROOT / "build"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"


def normalize(text: str) -> str:
    """Normalise whitespace for comparison."""
    return re.sub(r"\s+", " ", text or "").strip()


def load_registry() -> list[dict[str, Any]]:
    with REGISTRY.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)["items"]


def load_allowed() -> dict[str, Any]:
    with ALLOWED.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_sample_context(entries: list[dict[str, Any]], tpl: DocxTemplate,
                          sample_doc: Document) -> dict[str, Any]:
    """Build a sample context from registry examples AND table data read
    from the original docx."""
    ctx: dict[str, Any] = {}

    def _set_nested(key: str, value: Any) -> None:
        parts = key.split(".")
        d = ctx
        for part in parts[:-1]:
            d = d.setdefault(part, {})
        d[parts[-1]] = value

    # Create dummy PNG
    dummy_png = BUILD_DIR / "dummy.png"
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    if not dummy_png.exists():
        sig = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', 100, 100, 8, 2, 0, 0, 0)
        ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
        ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
        raw = b'\x00' + b'\xc0\xc0' * 100
        raw = raw * 100
        compressed = zlib.compress(raw)
        idat_crc = zlib.crc32(b'IDAT' + compressed)
        idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
        iend_crc = zlib.crc32(b'IEND')
        iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
        dummy_png.write_bytes(sig + ihdr + idat + iend)

    for entry in entries:
        key = entry["key"]
        entry_type = entry.get("type", "text")
        example = entry.get("example")

        if entry_type == "image":
            _set_nested(key, InlineImage(tpl, str(dummy_png)))
        elif entry_type == "bool":
            _set_nested(key, True)
        elif entry_type == "table":
            # Read table data from the original docx
            inv_idx = entry.get("inventory_item_index")
            cols = entry.get("columns") or []
            col_names = [c.get("key", f"c{i}").split(".")[-1] for i, c in enumerate(cols)]
            rows = []
            # Try to read rows from the sample
            if inv_idx is not None:
                # Find the table in the sample by inventory index
                # (simplified: use table number from registry)
                pass  # Table data will be filled from sample comparison
            _set_nested(key, {"rows": rows if rows else [{c: key for c in col_names}]})
        elif entry_type == "number":
            _set_nested(key, example if example is not None else 1)
        else:
            _set_nested(key, example if example is not None else key)

    # Read table data from the original docx for loop tables
    # T9 (index 9), T10 (10), T11 (11), T14 (14)
    loop_tables = {
        9: ("table.seismic.vertical_force_dist",
            ["level", "wi", "hi", "hik", "wi_hik", "fi", "shear"]),
        10: ("table.modal.rayleigh_x",
             ["level", "wi", "di_mm", "di_m", "di2", "fi", "fi_di", "wi_di2"]),
        11: ("table.modal.rayleigh_y",
             ["level", "wi", "di_mm", "di_m", "di2", "fi", "fi_di", "wi_di2"]),
        14: ("table.modal.periods_mass_part",
             ["case", "mode", "period", "ux", "uy", "sum_ux", "sum_uy"]),
    }
    header_rows = {9: 1, 10: 1, 11: 1, 14: 2}

    for tbl_idx, (ctx_key, col_names) in loop_tables.items():
        if tbl_idx < len(sample_doc.tables):
            tbl = sample_doc.tables[tbl_idx]
            n_header = header_rows.get(tbl_idx, 1)
            rows = []
            for ri in range(n_header, len(tbl.rows)):
                row_data = {}
                for ci, col_name in enumerate(col_names):
                    if ci < len(tbl.rows[ri].cells):
                        row_data[col_name] = tbl.rows[ri].cells[ci].text.strip()
                rows.append(row_data)
            _set_nested(ctx_key, {"rows": rows})

    _set_nested("building.has_staircase", True)
    return ctx


def is_owner_approved(location: str, expected: str, actual: str,
                      allowed: dict[str, Any]) -> bool:
    """Check if a difference matches an owner-approved rule."""
    for rule in allowed.get("owner_approved", []):
        match_type = rule.get("match_type", "")
        if match_type == "heading_restyle":
            text_contains = rule.get("text_contains", "").lower()
            if text_contains in expected.lower() or text_contains in actual.lower():
                return True
        elif match_type == "computed_variant":
            key = rule.get("key", "")
            if key in actual or key in expected:
                return True
        elif match_type == "clause_change":
            for pattern in rule.get("patterns", []):
                if pattern in expected:
                    return True
        elif match_type == "table_replaced_with_image":
            if f"T{rule.get('table_index')}" in location:
                return True
        elif match_type == "table_pending":
            if f"T{rule.get('table_index')}" in location:
                return True
        elif match_type == "loop_table":
            for idx in rule.get("table_indices", []):
                if f"T{idx}" in location:
                    return True
        elif match_type == "sentence_template":
            # If the expected text contains registry key names, it's a
            # sentence-template replacement.
            if "{{" in expected or "{{" in actual:
                return True
        elif match_type == "table_cell_placeholder":
            if "cell" in location and ("{{" in expected or "{{" in actual):
                return True
    return False


def compare_paragraphs(sample_doc: Document, rendered_doc: Document,
                        allowed: dict[str, Any]) -> list[dict[str, str]]:
    """Compare paragraph text between sample and rendered."""
    diffs = []
    sample_paras = [(p.text, p.style.name if p.style else "") for p in sample_doc.paragraphs]
    rendered_paras = [(p.text, p.style.name if p.style else "") for p in rendered_doc.paragraphs]

    # Use difflib to find differences
    sample_texts = [normalize(t) for t, _ in sample_paras]
    rendered_texts = [normalize(t) for t, _ in rendered_paras]

    # Match paragraphs by position (simple approach)
    max_len = max(len(sample_texts), len(rendered_texts))
    for i in range(max_len):
        s_text = sample_texts[i] if i < len(sample_texts) else ""
        r_text = rendered_texts[i] if i < len(rendered_texts) else ""

        # Skip empty paragraphs (both)
        if not s_text and not r_text:
            continue

        # Skip image paragraphs (contain drawing elements)
        if i < len(sample_paras) and "drawing" in str(sample_paras[i][0]).lower():
            continue

        if s_text != r_text:
            # Check if this is a placeholder substitution (expected text
            # contains {{ }} or actual text is a key name)
            if "{{" in s_text:
                # This is a template paragraph — check if rendered matches
                # the expected value
                classification = "owner_approved" if is_owner_approved(
                    f"para {i}", s_text, r_text, allowed) else "unexpected"
                diffs.append({
                    "location": f"para {i}",
                    "kind": "text",
                    "expected": s_text[:100],
                    "actual": r_text[:100],
                    "classification": classification,
                })
            elif r_text and any(key in r_text for key in [
                "analysis.", "codes.", "building.", "seismic.", "modal.",
                "design.", "materials.", "foundation.", "project.",
            ]):
                # Rendered text is a key name (placeholder substitution)
                classification = "owner_approved" if is_owner_approved(
                    f"para {i}", s_text, r_text, allowed) else "unexpected"
                diffs.append({
                    "location": f"para {i}",
                    "kind": "text",
                    "expected": s_text[:100],
                    "actual": r_text[:100],
                    "classification": classification,
                })
            else:
                # Check if it's a clause change
                classification = "owner_approved" if is_owner_approved(
                    f"para {i}", s_text, r_text, allowed) else "unexpected"
                diffs.append({
                    "location": f"para {i}",
                    "kind": "text",
                    "expected": s_text[:100],
                    "actual": r_text[:100],
                    "classification": classification,
                })

    return diffs


def compare_tables(sample_doc: Document, rendered_doc: Document,
                   allowed: dict[str, Any]) -> list[dict[str, str]]:
    """Compare table cells between sample and rendered."""
    diffs = []
    n_tables = max(len(sample_doc.tables), len(rendered_doc.tables))
    for ti in range(n_tables):
        if ti >= len(sample_doc.tables):
            diffs.append({
                "location": f"T{ti}",
                "kind": "table_missing_in_sample",
                "expected": "(table exists)",
                "actual": "(table missing)",
                "classification": "owner_approved" if is_owner_approved(
                    f"T{ti}", "", "", allowed) else "unexpected",
            })
            continue
        if ti >= len(rendered_doc.tables):
            diffs.append({
                "location": f"T{ti}",
                "kind": "table_missing_in_rendered",
                "expected": "(table exists)",
                "actual": "(table removed)",
                "classification": "owner_approved" if is_owner_approved(
                    f"T{ti}", "", "", allowed) else "unexpected",
            })
            continue

        s_tbl = sample_doc.tables[ti]
        r_tbl = rendered_doc.tables[ti]

        # Compare row count
        s_rows = len(s_tbl.rows)
        r_rows = len(r_tbl.rows)
        if s_rows != r_rows:
            # Check if it's a loop table or T15
            classification = "owner_approved" if is_owner_approved(
                f"T{ti}", f"{s_rows} rows", f"{r_rows} rows", allowed) else "unexpected"
            diffs.append({
                "location": f"T{ti}",
                "kind": "row_count",
                "expected": f"{s_rows} rows",
                "actual": f"{r_rows} rows",
                "classification": classification,
            })

        # Compare cells
        max_rows = min(s_rows, r_rows)
        for ri in range(max_rows):
            s_cells = s_tbl.rows[ri].cells
            r_cells = r_tbl.rows[ri].cells
            max_cols = max(len(s_cells), len(r_cells))
            for ci in range(max_cols):
                s_val = normalize(s_cells[ci].text) if ci < len(s_cells) else ""
                r_val = normalize(r_cells[ci].text) if ci < len(r_cells) else ""
                if s_val != r_val:
                    classification = "owner_approved" if is_owner_approved(
                        f"T{ti} ({ri},{ci})", s_val, r_val, allowed) else "unexpected"
                    diffs.append({
                        "location": f"T{ti} ({ri},{ci})",
                        "kind": "cell",
                        "expected": s_val[:100],
                        "actual": r_val[:100],
                        "classification": classification,
                    })

    return diffs


def write_csv(diffs: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["location", "kind", "expected", "actual", "classification"])
        writer.writeheader()
        for d in diffs:
            writer.writerow(d)


def write_report(diffs: list[dict[str, str]], path: Path) -> None:
    """Generate docs/roundtrip_report.md from the diff data."""
    owner = [d for d in diffs if d["classification"] == "owner_approved"]
    unexpected = [d for d in diffs if d["classification"] == "unexpected"]
    lines = [
        "# Round-Trip Report",
        "",
        f"Generated by tools/roundtrip.py from docs/roundtrip_diff.csv.",
        "",
        "## Summary",
        "",
        f"| Classification | Count |",
        f"|----------------|-------|",
        f"| owner_approved | {len(owner)} |",
        f"| unexpected | {len(unexpected)} |",
        f"| **Total** | **{len(diffs)}** |",
        "",
        "## Unexpected differences",
        "",
    ]
    if unexpected:
        lines.append(f"**{len(unexpected)} unexpected differences found.**")
        lines.append("")
        lines.append("| # | Location | Kind | Expected | Actual |")
        lines.append("|---|----------|------|----------|--------|")
        for i, d in enumerate(unexpected[:50], 1):
            exp = d["expected"].replace("|", "\\|")[:60]
            act = d["actual"].replace("|", "\\|")[:60]
            lines.append(f"| {i} | {d['location']} | {d['kind']} | {exp} | {act} |")
        if len(unexpected) > 50:
            lines.append(f"\n... and {len(unexpected) - 50} more (see docs/roundtrip_diff.csv)")
    else:
        lines.append("None.")
    lines += [
        "",
        "## Owner-approved differences",
        "",
        f"{len(owner)} differences classified as owner-approved.",
        "",
        "### By kind:",
        "",
    ]
    from collections import Counter
    kind_counts = Counter(d["kind"] for d in owner)
    for kind, count in sorted(kind_counts.items()):
        lines.append(f"- {kind}: {count}")
    lines += [
        "",
        "## T6 (Load Assessment) status",
        "",
        "T6 is pending code-built implementation (Phase 3b). The table",
        "currently contains sample data in non-templated cells.",
        "",
        "## T15 (Slab Design) status",
        "",
        "T15 has been replaced with image placeholder `{{ figure.design.slab_sheet }}`",
        "per owner decision.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    entries = load_registry()
    allowed = load_allowed()

    # Build sample context
    sample_doc = Document(str(SAMPLE))
    tpl = DocxTemplate(str(TEMPLATE))
    ctx = build_sample_context(entries, tpl, sample_doc)

    # Render
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    rendered_path = BUILD_DIR / "roundtrip_rendered.docx"
    tpl.render(ctx)
    tpl.save(str(rendered_path))

    rendered_doc = Document(str(rendered_path))

    # Compare
    para_diffs = compare_paragraphs(sample_doc, rendered_doc, allowed)
    table_diffs = compare_tables(sample_doc, rendered_doc, allowed)
    all_diffs = para_diffs + table_diffs

    # Write outputs
    write_csv(all_diffs, DIFF_CSV)
    write_report(all_diffs, REPORT_MD)

    unexpected_count = sum(1 for d in all_diffs if d["classification"] == "unexpected")
    owner_count = sum(1 for d in all_diffs if d["classification"] == "owner_approved")

    print(f"[OK] Rendered: {rendered_path}")
    print(f"[OK] Diff CSV: {DIFF_CSV} ({len(all_diffs)} rows)")
    print(f"[OK] Report: {REPORT_MD}")
    print(f"     Owner-approved: {owner_count}")
    print(f"     Unexpected: {unexpected_count}")

    if unexpected_count > 0:
        print(f"\n[FAIL] {unexpected_count} unexpected differences found.")
        print("       See docs/roundtrip_diff.csv for details.")
        return 1
    else:
        print("\n[PASS] No unexpected differences.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
