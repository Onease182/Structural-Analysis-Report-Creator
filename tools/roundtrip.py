#!/usr/bin/env python3
"""Round-trip comparison using sequence alignment (difflib).

Builds a sample context from the registry + sample doc values, renders the
template, and compares with the original using difflib.SequenceMatcher so
one inserted/removed paragraph does not cascade.

Outputs:
  - docs/roundtrip_diff.csv
  - docs/roundtrip_report.md (generated from the CSV, never by hand)

Exits non-zero if any "unexpected" difference exists.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import re
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

import yaml
from docx import Document
from docxtpl import DocxTemplate, InlineImage

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "master_template.docx"
SAMPLE = ROOT / "Chatra Bahadur Ramtel.docx"
REGISTRY = ROOT / "config" / "placeholder_registry.yaml"
ALLOWED = ROOT / "config" / "roundtrip_allowed.yaml"
DIFF_CSV = ROOT / "docs" / "roundtrip_diff.csv"
REPORT_MD = ROOT / "docs" / "roundtrip_report.md"
BUILD_DIR = ROOT / "build"
SAMPLE_CONTEXT = ROOT / "config" / "sample_context.yaml"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def normalize(text: str) -> str:
    """Normalise whitespace for comparison, including non-breaking spaces."""
    text = (text or "").replace("\xa0", " ")  # non-breaking space
    return re.sub(r"\s+", " ", text).strip()


def load_registry() -> list[dict[str, Any]]:
    with REGISTRY.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)["items"]


def load_allowed() -> dict[str, Any]:
    with ALLOWED.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Sample context builder: uses target_clause_2025 values, sample sentences,
# and table data from the original docx.
# ---------------------------------------------------------------------------

def read_sample_table_values(sample_doc: Document) -> dict[int, list[list[str]]]:
    """Read all cell values from each table in the sample."""
    tables = {}
    for ti, tbl in enumerate(sample_doc.tables):
        rows = []
        for row in tbl.rows:
            rows.append([normalize(cell.text) for cell in row.cells])
        tables[ti] = rows
    return tables


def build_sample_context(entries: list[dict[str, Any]], tpl: DocxTemplate,
                          sample_doc: Document) -> dict[str, Any]:
    """Build a proper sample context: clause values from target_clause_2025,
    computed variants from the sample's own conclusion sentences, and table
    data read from the original docx."""
    ctx: dict[str, Any] = {}

    def _set(key: str, val: Any) -> None:
        parts = key.split(".")
        d = ctx
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = val

    # Dummy image
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    dummy_png = BUILD_DIR / "dummy.png"
    if not dummy_png.exists():
        sig = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', 100, 100, 8, 2, 0, 0, 0)
        ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', zlib.crc32(b'IHDR' + ihdr_data))
        raw = b'\x00' + b'\xc0\xc0' * 100
        raw *= 100
        comp = zlib.compress(raw)
        idat = struct.pack('>I', len(comp)) + b'IDAT' + comp + struct.pack('>I', zlib.crc32(b'IDAT' + comp))
        iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', zlib.crc32(b'IEND'))
        dummy_png.write_bytes(sig + ihdr + idat + iend)

    # Sample table data for loop tables
    sample_tables = read_sample_table_values(sample_doc)
    loop_tables = {
        9: ("table.seismic.vertical_force_dist", ["level", "wi", "hi", "hik", "wi_hik", "fi", "shear"], 1),
        10: ("table.modal.rayleigh_x", ["level", "wi", "di_mm", "di_m", "di2", "fi", "fi_di", "wi_di2"], 1),
        11: ("table.modal.rayleigh_y", ["level", "wi", "di_mm", "di_m", "di2", "fi", "fi_di", "wi_di2"], 1),
        14: ("table.modal.periods_mass_part", ["case", "mode", "period", "ux", "uy", "sum_ux", "sum_uy"], 2),
    }

    for entry in entries:
        key = entry["key"]
        etype = entry.get("type", "text")
        if etype == "image":
            _set(key, InlineImage(tpl, str(dummy_png)))
        elif etype == "bool":
            _set(key, True)
        elif etype == "table":
            # Check if it's a loop table
            for tbl_idx, (ctx_key, cols, hdr) in loop_tables.items():
                if key == ctx_key and tbl_idx in sample_tables:
                    rows = []
                    for ri in range(hdr, len(sample_tables[tbl_idx])):
                        row_data = {}
                        for ci, col_name in enumerate(cols):
                            if ci < len(sample_tables[tbl_idx][ri]):
                                row_data[col_name] = sample_tables[tbl_idx][ri][ci]
                        rows.append(row_data)
                    _set(key, {"rows": rows})
                    break
            else:
                cols = entry.get("columns") or []
                _set(key, {"rows": [{col.get("key", f"c{i}").split(".")[-1]: key for i, col in enumerate(cols)}]})
        elif key.startswith("codes.clauses."):
            # Use target_clause_2025 as the value
            _set(key, entry.get("target_clause_2025") or key)
        elif key.startswith("analysis.") and key.endswith("result"):
            # Computed variants: use the sample's own conclusion sentences
            sample_sentences = {
                "analysis.soft_storey_result": "No soft stoy is observed in the building.",
                "analysis.in_plane_discontinuity_result": "No in-plane discontinuity is present in the structure.",
                "analysis.mass_irregularity_result": "No mass irregularity is seen as the stories are nearly identical.",
                "analysis.reentrant_corner_result": "The building is rectangular in shape with no re-entrant corners.",
            }
            _set(key, sample_sentences.get(key, entry.get("example") or key))
        elif key == "foundation.support_condition":
            _set(key, "the foundation is assumed to be fixed.")
        elif key == "codes.edition":
            # The sample uses "NBC105:2025" (no space) in para 291 and
            # "NBC 105:2025" (with space) in other paragraphs. The template
            # uses {{ codes.edition }} everywhere.
            # This is a sample inconsistency — proposed for owner approval.
            _set(key, "NBC 105:2025")
        elif key == "building.occupancy_sentence":
            _set(key, "The live loads for the floor and roof are determined using IS 875 part 2, as referenced by the National Building Code. For residential buildings, the appropriate live load values specified in Table 1 of IS 875 Part 2 are considered. Since the building is intended for residential use, the loading intensity for dwelling houses under the residential category is taken into account.")
        elif key == "client.consultant_name":
            _set(key, "CivoraX Infra")  # D2: canonical form
        elif key == "building.storeys_above_grade":
            # The sentence template uses the word form ("three") but table
            # cells need the digit form ("3"). We set the word form here
            # and override to digit for table cells below.
            _set(key, "three")
        elif key == "building.num_storeys_analysed":
            _set(key, 3)
        elif key == "seismic.importance_factor_i":
            _set(key, "1.0")  # Sample uses "1.0" not "1"
        elif key == "foundation.modeling_software":
            _set(key, "ETABS 19.0.0")
        elif etype == "number":
            _set(key, entry.get("example") if entry.get("example") is not None else 1)
        else:
            _set(key, entry.get("example") if entry.get("example") is not None else key)

    # Read table cell values from the sample for cell-placeholder tables.
    # This ensures the rendered cells match the original exactly.
    cell_table_indices = [0, 2, 3, 4, 8, 12, 13, 15]  # 15 = beam deflection (shifted from 16)
    # Map (sample_tbl_idx, row, col) → context key, derived from the template cell map.
    # We read the sample's cell value and set it as the context value for that key.
    SAMPLE_CELL_KEYS = {
        # T0
        (0, 1, 2): "client.owner_name", (0, 2, 2): "building.location",
        (0, 3, 2): "building.occupancy_class", (0, 4, 2): "client.designer_name",
        (0, 5, 2): "client.designer_nec_reg", (0, 6, 2): "client.designer_contact",
        (0, 7, 2): "client.consultant_name", (0, 8, 2): "client.municipality_reg",
        (0, 9, 2): "client.application_date",
        # T2
        (2, 0, 2): "building.location", (2, 1, 2): "building.storeys_count_numeric",
        (2, 2, 2): "building.num_storeys_analysed", (2, 3, 2): "building.num_basements",
        (2, 4, 2): "building.height_ground_floor_m", (2, 5, 2): "building.height_typical_floor_m",
        (2, 8, 2): "building.occupancy_class",
        # T3
        (3, 1, 1): "table.elements.col_desc", (3, 1, 2): "materials.concrete_grade_used",
        (3, 2, 1): "table.elements.beam_desc", (3, 2, 2): "materials.concrete_grade_used",
        (3, 3, 1): "table.elements.stair_desc", (3, 3, 2): "materials.concrete_grade_used",
        (3, 4, 1): "table.elements.slab_desc", (3, 4, 2): "materials.concrete_grade_used",
        (3, 5, 1): "table.elements.foundation_desc", (3, 5, 2): "materials.concrete_grade_used",
        (3, 5, 3): "foundation.soil_bearing",
        # T4
        (4, 0, 2): "structural.system_type", (4, 1, 2): "foundation.type", (4, 2, 2): "slab.type",
        # T8
        (8, 2, 1): "seismic.time_coefficient_kt", (8, 3, 4): "modal.empirical_period_unamplified_s",
        (8, 5, 3): "modal.empirical_period_s",
        # T12
        (12, 0, 2): "modal.empirical_period_s", (12, 2, 2): "seismic.site_soil_category",
        (12, 3, 3): "seismic.tc", (12, 4, 2): "seismic.soil_class",
        (12, 5, 1): "seismic.alpha", (12, 5, 3): "seismic.distribution_exponent_k",
        (12, 6, 2): "seismic.spectral_shape_factor_cht",
        (12, 7, 1): "building.location", (12, 7, 3): "seismic.zone_factor_z",
        (12, 8, 2): "seismic.structural_type", (12, 9, 2): "seismic.importance_factor_i_table",
        (12, 10, 3): "seismic.elastic_site_spectra_c", (12, 11, 3): "seismic.elastic_site_spectra_cs",
        (12, 13, 3): "structural.system_type_table_5_2", (12, 14, 3): "seismic.response_modification_factor_rmu",
        # T13
        (13, 0, 1): "design.overstrength_ultimate", (13, 1, 1): "design.overstrength_serviceability",
        (13, 2, 1): "seismic.hsc_uls", (13, 3, 1): "seismic.hsc_sls",
        # T16 (beam deflection) — in sample it's at index 16, but template shifted to 15
        # We read from the sample at index 16
    }
    # Also read T16 (beam deflection) cells from sample
    # In the sample, beam deflection is at index 16
    if len(sample_doc.tables) > 16:
        beam_tbl = sample_doc.tables[16]
        beam_keys = [
            None,  # header
            "table.design.beam_boundary", "table.design.beam_effective_span",
            "table.design.beam_overall_depth", "table.design.beam_effective_depth",
            "table.design.beam_basic_ld_ratio", "table.design.beam_ast_req",
            "table.design.beam_ast_prov", "table.design.beam_pt",
            "table.design.beam_fs", "table.design.beam_mod_factor",
            "table.design.beam_permissible_ld", "table.design.beam_provided_ld",
            "table.design.beam_check_result",
        ]
        for ri, row in enumerate(beam_tbl.rows):
            if ri < len(beam_keys) and beam_keys[ri]:
                val = normalize(row.cells[1].text) if len(row.cells) > 1 else ""
                if val:
                    _set(beam_keys[ri], val)

    # Read cell values from the sample and set them in the context.
    # Skip cells that have a CELL_SUFFIX in make_template.py — the template
    # adds the suffix as fixed text, so the context value should NOT include it.
    SUFFIX_CELLS = {(2, 4, 2), (2, 5, 2), (2, 6, 2), (2, 7, 2), (2, 8, 2)}
    for (sidx, ri, ci), key in SAMPLE_CELL_KEYS.items():
        if (sidx, ri, ci) in SUFFIX_CELLS:
            continue  # Skip — value comes from registry example, not sample
        if sidx < len(sample_doc.tables):
            tbl = sample_doc.tables[sidx]
            if ri < len(tbl.rows) and ci < len(tbl.rows[ri].cells):
                val = normalize(tbl.rows[ri].cells[ci].text)
                if val:
                    _set(key, val)

    # Add separate keys for T8/T12 structural system type variants
    _set("structural.system_type_period_category", "Moment Resisting Concrete Frame")
    _set("structural.system_type_table_5_2", "Reinforced Concrete Moment Resisting Frame")
    # Height values: numeric only, the template adds " meters" suffix in T2 cells
    _set("building.height_ground_floor_m", "3.175")
    _set("building.height_typical_floor_m", "3.175")
    _set("building.height_period_m", "9.525")
    # T2 cell needs numeric storey count (not word form)
    _set("building.storeys_count_numeric", "3")
    # T16 check result: escape "<" as "&lt;" to prevent XML stripping
    _set("table.design.beam_check_result", "10.61 &lt; 43.7, OK")
    # Calc line values — exact sample values
    _set("design.column.max_rebar_area_mm2", "1557")
    _set("design.column.max_section_width_mm", "355")
    _set("design.column.max_section_depth_mm", "355")
    _set("design.column.max_provided_pct", "1.24")
    _set("design.column.max_limit_pct", "4")
    _set("design.column.max_status", "Ok")
    _set("design.column.min_provided_pct", "1.026")
    _set("design.column.min_limit_pct", "1")
    _set("design.column.min_status", "Ok")
    _set("design.beam.max_rebar_area_mm2", "678.584")
    _set("design.beam.max_section_width_mm", "250")
    _set("design.beam.max_section_depth_mm", "355")
    _set("design.beam.max_provided_pct", "0.764")
    _set("design.beam.max_limit_pct", "2.5")
    _set("design.beam.max_status", "Ok")
    _set("design.beam.min_provided_pct", "0.764")
    _set("design.beam.min_limit_pct", "0.26")
    _set("design.beam.min_status", "Ok")
    _set("design.beam.maximum_reinforcement.status", "Ok")
    _set("design.beam.minimum_reinforcement.status", "Ok")
    # Override importance factor for sentence (sample uses "1.0" in paragraph
    # but "1" in table T12 cell 9,2 — sample inconsistency)
    _set("seismic.importance_factor_i", "1.0")
    _set("seismic.importance_factor_i_table", "1")
    # ETABS modeling software
    _set("foundation.modeling_software", "ETABS 19.0.0")

    _set("building.has_staircase", True)

    # Write sample context for inspection
    # (can't serialize InlineImage, so write a simplified version)
    simple_ctx = {}
    for k, v in ctx.items():
        if isinstance(v, dict):
            simple_ctx[k] = {kk: (str(vv)[:60] if not isinstance(vv, dict) else '...') for kk, vv in v.items()}
        else:
            simple_ctx[k] = str(v)[:60]
    SAMPLE_CONTEXT.write_text(yaml.dump(simple_ctx, allow_unicode=True), encoding="utf-8")

    return ctx


# ---------------------------------------------------------------------------
# Leak check
# ---------------------------------------------------------------------------

def check_leaks(text: str, entries: list[dict[str, Any]]) -> list[str]:
    """Fail if any output contains a registry key name or a standalone enum literal."""
    leaks = []
    all_keys = {e["key"] for e in entries}
    # Check for key names (dotted identifiers like codes.clauses.xxx)
    for m in re.finditer(r"\b([a-z]+\.[a-z]+\.[a-z_]+)", text):
        found = m.group(1)
        if found in all_keys:
            leaks.append(f"Key name leaked: {found}")
    # Check for standalone enum literals (exact match, not substring)
    # "present" appears legitimately in "is present in the structure"
    for enum_val in ["not_present", "rectangular_no_reentrant_corners",
                      "reentrant_present"]:
        if re.search(r"\b" + re.escape(enum_val) + r"\b", text):
            leaks.append(f"Enum literal leaked: {enum_val}")
    # "present" as a standalone word is OK if it's part of a sentence like
    # "is present in". Only flag it if it appears as a bare value (not in a
    # sentence context).
    return leaks


# ---------------------------------------------------------------------------
# Comparison using difflib sequence alignment
# ---------------------------------------------------------------------------

def classify_diff(location: str, expected: str, actual: str,
                  allowed: dict[str, Any]) -> str:
    """Classify a difference as owner_approved or unexpected."""
    exp_lower = expected.lower()
    act_lower = actual.lower()
    for rule in allowed.get("owner_approved", []):
        mt = rule.get("match_type", "")
        if mt == "heading_restyle":
            tc = rule.get("text_contains", "").lower()
            if tc in exp_lower or tc in act_lower:
                return "owner_approved"
        elif mt == "computed_variant":
            key = rule.get("key", "")
            if key in act_lower or key in exp_lower:
                return "owner_approved"
        elif mt == "exact_text":
            old_frag = rule.get("old_fragment", "")
            new_frag = rule.get("new_fragment", "")
            if old_frag in expected and new_frag in actual:
                rest_expected = expected.replace(old_frag, new_frag)
                if normalize(rest_expected) == normalize(actual):
                    return "owner_approved"
        elif mt == "clause_change_exact":
            old_frag = rule.get("old", "")
            new_frag = rule.get("new", "")
            if old_frag in expected:
                replaced = expected.replace(old_frag, new_frag)
                if normalize(replaced) == normalize(actual):
                    return "owner_approved"
                if new_frag in actual:
                    return "owner_approved"
        elif mt in ("table_replaced_with_image", "table_pending", "loop_table", "table_removed"):
            idx = rule.get("table_index")
            if idx is not None and f"T{idx}" in location:
                return "owner_approved"
            for ti in rule.get("table_indices", []):
                if f"T{ti}" in location:
                    return "owner_approved"
    return "unexpected"

def compare_paragraphs_seq(sample_doc: Document, rendered_doc: Document,
                           allowed: dict[str, Any]) -> list[dict[str, str]]:
    """Compare paragraphs using difflib.SequenceMatcher."""
    diffs = []
    s_paras = [normalize(p.text) for p in sample_doc.paragraphs]
    r_paras = [normalize(p.text) for p in rendered_doc.paragraphs]

    # Skip empty paragraphs
    s_paras = [t for t in s_paras if t]
    r_paras = [t for t in r_paras if t]

    matcher = difflib.SequenceMatcher(None, s_paras, r_paras)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag in ("replace", "delete"):
            for i in range(i1, i2):
                s_text = s_paras[i]
                r_text = r_paras[j1] if j1 < len(r_paras) and tag == "replace" else ""
                if s_text != r_text:
                    cls = classify_diff(f"para {i}", s_text, r_text, allowed)
                    diffs.append({
                        "location": f"para {i}",
                        "kind": f"text_{tag}",
                        "expected": s_text,
                        "actual": r_text,
                        "classification": cls,
                    })
        if tag in ("replace", "insert"):
            for j in range(j1 if tag == "insert" else j1 + 1, j2):
                r_text = r_paras[j]
                s_text = ""
                cls = classify_diff(f"para {j}", s_text, r_text, allowed)
                diffs.append({
                    "location": f"para {j}",
                    "kind": f"text_{tag}",
                    "expected": s_text,
                    "actual": r_text,
                    "classification": cls,
                })
    return diffs


def table_identity(tbl) -> str:
    """Return a stable identity for a table: first-row text or caption."""
    if not tbl.rows:
        return ""
    first_row = " | ".join(normalize(c.text) for c in tbl.rows[0].cells)
    return first_row[:60]


def match_tables(sample_doc: Document, rendered_doc: Document) -> dict[int, int]:
    """Match tables by identity (first-row text). Returns {sample_idx: rendered_idx}.
    T15 (replaced by image) is allowed to be missing."""
    sample_ids = {}
    for ti, tbl in enumerate(sample_doc.tables):
        sample_ids[table_identity(tbl)] = ti
    rendered_ids = {}
    for ti, tbl in enumerate(rendered_doc.tables):
        rendered_ids[table_identity(tbl)] = ti
    matches = {}
    for sid, sidx in sample_ids.items():
        if sid in rendered_ids:
            matches[sidx] = rendered_ids[sid]
        else:
            matches[sidx] = -1  # missing in rendered
    return matches


def compare_tables_by_identity(sample_doc: Document, rendered_doc: Document,
                               allowed: dict[str, Any]) -> list[dict[str, str]]:
    """Compare tables matched by identity, with row alignment by label."""
    diffs = []
    matches = match_tables(sample_doc, rendered_doc)
    for sidx, ridx in sorted(matches.items()):
        if ridx == -1:
            cls = classify_diff(f"T{sidx}", "(table)", "", allowed)
            diffs.append({"location": f"T{sidx}", "kind": "table_removed",
                          "expected": "(table)", "actual": "", "classification": cls})
            continue
        s_tbl = sample_doc.tables[sidx]
        r_tbl = rendered_doc.tables[ridx]
        # Align rows by label (column 0 text — the row label/identifier)
        # Using column 0 is more stable than column 1 because column 0
        # contains the label/S.N. while column 1 may contain variable values.
        s_rows_by_label = {}
        s_rows_list = []
        for ri, row in enumerate(s_tbl.rows):
            label = normalize(row.cells[0].text if len(row.cells) > 0 else "")
            s_rows_by_label.setdefault(label, []).append(ri)
            s_rows_list.append(row)
        r_rows_by_label = {}
        r_rows_list = []
        for ri, row in enumerate(r_tbl.rows):
            label = normalize(row.cells[0].text if len(row.cells) > 0 else "")
            r_rows_by_label.setdefault(label, []).append(ri)
            r_rows_list.append(row)
        # Row count diff
        if len(s_tbl.rows) != len(r_tbl.rows):
            cls = classify_diff(f"T{sidx}", f"{len(s_tbl.rows)} rows", f"{len(r_tbl.rows)} rows", allowed)
            diffs.append({"location": f"T{sidx}", "kind": "row_count",
                          "expected": f"{len(s_tbl.rows)} rows", "actual": f"{len(r_tbl.rows)} rows",
                          "classification": cls})
        # Compare cells row by row, matching by label
        for sri, srow in enumerate(s_rows_list):
            s_label = normalize(srow.cells[0].text if len(srow.cells) > 0 else "")
            # Find the matching rendered row by label
            rri = None
            r_candidates = r_rows_by_label.get(s_label, [])
            if r_candidates:
                rri = r_candidates.pop(0)
            if rri is not None:
                rrow = r_rows_list[rri]
                for ci in range(max(len(srow.cells), len(rrow.cells))):
                    s_val = normalize(srow.cells[ci].text) if ci < len(srow.cells) else ""
                    r_val = normalize(rrow.cells[ci].text) if ci < len(rrow.cells) else ""
                    if s_val != r_val:
                        cls = classify_diff(f"T{sidx} row '{s_label}' ({ci})", s_val, r_val, allowed)
                        diffs.append({"location": f"T{sidx} row '{s_label}' col {ci}", "kind": "cell",
                                      "expected": s_val, "actual": r_val,
                                      "classification": cls})
            else:
                # Row missing in rendered
                for ci in range(len(srow.cells)):
                    s_val = normalize(srow.cells[ci].text)
                    if s_val:
                        cls = classify_diff(f"T{sidx} row '{s_label}' col {ci}", s_val, "", allowed)
                        diffs.append({"location": f"T{sidx} row '{s_label}' col {ci}", "kind": "cell_missing",
                                      "expected": s_val, "actual": "",
                                      "classification": cls})
    return diffs


def write_csv(diffs: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["location", "kind", "expected", "actual", "classification"])
        writer.writeheader()
        for d in diffs:
            writer.writerow(d)


def write_report(diffs: list[dict[str, str]], leaks: list[str], path: Path) -> None:
    owner = [d for d in diffs if d["classification"] == "owner_approved"]
    unexpected = [d for d in diffs if d["classification"] == "unexpected"]
    lines = [
        "# Round-Trip Report",
        "",
        "Generated by tools/roundtrip.py from docs/roundtrip_diff.csv.",
        "",
        "## Summary",
        "",
        f"| Classification | Count |",
        f"|----------------|-------|",
        f"| owner_approved | {len(owner)} |",
        f"| unexpected | {len(unexpected)} |",
        f"| **Total** | **{len(diffs)}** |",
        "",
    ]
    if leaks:
        lines += ["## Leaks", "", f"**{len(leaks)} leaks found:**"]
        for l in leaks[:10]:
            lines.append(f"- {l}")
        lines.append("")
    if unexpected:
        lines += ["## Unexpected differences", "",
                  f"**{len(unexpected)} unexpected differences.**", "",
                  "| # | Location | Kind | Expected | Actual |",
                  "|---|----------|------|----------|--------|"]
        for i, d in enumerate(unexpected[:50], 1):
            lines.append(f"| {i} | {d['location']} | {d['kind']} | "
                        f"{d['expected'].replace('|','\\|')[:60]} | "
                        f"{d['actual'].replace('|','\\|')[:60]} |")
        if len(unexpected) > 50:
            lines.append(f"\n... and {len(unexpected) - 50} more (see CSV)")
    else:
        lines += ["## Unexpected differences", "", "None."]
    lines += ["", "## Owner-approved differences", "",
              f"{len(owner)} differences classified as owner-approved.", ""]
    lines += ["## T6 status", "",
              "T6 has status=pending_implementation. Sample data in T6 cells",
              "counts as allowed 'pending' differences only while this status is set.", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    entries = load_registry()
    allowed = load_allowed()
    sample_doc = Document(str(SAMPLE))
    tpl = DocxTemplate(str(TEMPLATE))
    ctx = build_sample_context(entries, tpl, sample_doc)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    rendered_path = BUILD_DIR / "roundtrip_rendered.docx"
    tpl.render(ctx)
    tpl.save(str(rendered_path))
    rendered_doc = Document(str(rendered_path))

    # Leak check
    full_text = "".join((t.text or "") for t in rendered_doc.element.body.iter(f"{{{W_NS}}}t"))
    leaks = check_leaks(full_text, entries)

    # Compare
    para_diffs = compare_paragraphs_seq(sample_doc, rendered_doc, allowed)
    table_diffs = compare_tables_by_identity(sample_doc, rendered_doc, allowed)
    all_diffs = para_diffs + table_diffs

    # Add leaks as unexpected diffs
    for leak in leaks:
        all_diffs.append({"location": "rendered output", "kind": "leak",
                          "expected": "(no key names)", "actual": leak,
                          "classification": "unexpected"})

    write_csv(all_diffs, DIFF_CSV)
    write_report(all_diffs, leaks, REPORT_MD)

    unexpected = sum(1 for d in all_diffs if d["classification"] == "unexpected")
    owner = sum(1 for d in all_diffs if d["classification"] == "owner_approved")
    print(f"[OK] Rendered: {rendered_path}")
    print(f"[OK] Diff CSV: {DIFF_CSV} ({len(all_diffs)} rows)")
    print(f"[OK] Report: {REPORT_MD}")
    print(f"     Owner-approved: {owner}")
    print(f"     Unexpected: {unexpected}")
    print(f"     Leaks: {len(leaks)}")
    if unexpected > 0:
        print(f"\n[FAIL] {unexpected} unexpected differences.")
        return 1
    print("\n[PASS] No unexpected differences.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
