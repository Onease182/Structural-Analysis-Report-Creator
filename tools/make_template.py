#!/usr/bin/env python3
"""Generate templates/master_template.docx from the sample DOCX using docxtpl
placeholders.

The generator reads:
  - Chatra Bahadur Ramtel.docx (the original sample, never modified)
  - config/placeholder_registry.yaml (the curated registry)
  - docs/template_inventory.json (item positions)
  - config/template_rules.yaml (anchored rules)

It writes:
  - templates/master_template.docx (the docxtpl template)
  - docs/template_replacement_log.md (what was replaced and where)

Placeholder syntax:
  - Text:  {{ key }}
  - Table rows:  {%tr for r in rows %}...{%tr endfor %}
  - Images:  {{ figure.key }} (rendered via InlineImage at the sample's size)
  - Conditionals:  {%p if condition %}...{%p endif %}

Strict mode: the generator fails if any codes.clauses.* entry has a null
or empty target_clause_2025, or if any required registry key is missing
from the context during rendering.

Usage:
    python tools/make_template.py
    python tools/make_template.py --input "Chatra Bahadur Ramtel.docx" \
        --output templates/master_template.docx
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import copy
from pathlib import Path
from typing import Any

import yaml
from docx import Document
from docx.oxml.ns import qn
from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NSMAP = {"w": W_NS, "wp": WP_NS, "a": A_NS, "pic": PIC_NS, "r": R_NS}

SAMPLE_DOCX = ROOT / "Chatra Bahadur Ramtel.docx"
REGISTRY_YAML = ROOT / "config" / "placeholder_registry.yaml"
INVENTORY_JSON = ROOT / "docs" / "template_inventory.json"
TEMPLATE_RULES_YAML = ROOT / "config" / "template_rules.yaml"
OUTPUT_DOCX = ROOT / "templates" / "master_template.docx"
REPLACEMENT_LOG = ROOT / "docs" / "template_replacement_log.md"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=SAMPLE_DOCX)
    p.add_argument("--output", type=Path, default=OUTPUT_DOCX)
    p.add_argument("--registry", type=Path, default=REGISTRY_YAML)
    p.add_argument("--inventory", type=Path, default=INVENTORY_JSON)
    p.add_argument("--rules", type=Path, default=TEMPLATE_RULES_YAML)
    p.add_argument("--log", type=Path, default=REPLACEMENT_LOG)
    return p.parse_args()


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_registry(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["items"]


def load_inventory(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["items"]


def load_rules(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["rules"]


# ---------------------------------------------------------------------------
# Strict-mode validation
# ---------------------------------------------------------------------------

def validate_registry_strict(entries: list[dict[str, Any]]) -> None:
    """Fail if any codes.clauses.* entry has a null/empty target_clause_2025."""
    bad = []
    for e in entries:
        if e["key"].startswith("codes.clauses."):
            target = e.get("target_clause_2025")
            if not target or not str(target).strip():
                bad.append(e["key"])
    if bad:
        raise ValueError(
            f"Strict mode: codes.clauses.* entries with null/empty target_clause_2025: {bad}"
        )


# ---------------------------------------------------------------------------
# Build item-index -> (body_child_index, sub_type) mapping
# ---------------------------------------------------------------------------

def build_item_mapping(body_element) -> list[tuple[int, int, str]]:
    """Walk body children the same way inventory_docx does and return a list
    of (item_index, body_child_index, item_type) tuples."""
    body_children = list(body_element)
    mapping: list[tuple[int, int, str]] = []
    item_idx = 0
    for child_idx, child in enumerate(body_children):
        tag = child.tag.split("}")[-1]
        if tag == "p":
            mapping.append((item_idx, child_idx, "paragraph"))
            item_idx += 1
            # Images within paragraph
            inline = child.findall(f".//{{{WP_NS}}}inline")
            anchor = child.findall(f".//{{{WP_NS}}}anchor")
            for _ in inline + anchor:
                mapping.append((item_idx, child_idx, "image"))
                item_idx += 1
            # Fields within paragraph
            fld_simple = child.findall(f".//{{{W_NS}}}fldSimple")
            fld_chars = child.findall(
                f".//{{{W_NS}}}fldChar[@{{{W_NS}}}fldCharType='begin']"
            )
            for _ in fld_simple + fld_chars:
                mapping.append((item_idx, child_idx, "field"))
                item_idx += 1
            # Section break within paragraph
            sect_pr = child.find(f".//{{{W_NS}}}sectPr")
            if sect_pr is not None:
                mapping.append((item_idx, child_idx, "section_break"))
                item_idx += 1
        elif tag == "tbl":
            mapping.append((item_idx, child_idx, "table"))
            item_idx += 1
        elif tag == "sectPr":
            mapping.append((item_idx, child_idx, "section_break"))
            item_idx += 1
    return mapping


def apply_style_overrides(body_children, idx_to_child, rules, logger) -> None:
    """For template rules with a style_override, change the paragraph style
    in the template. Used to restyle conclusion headings to Body Text."""
    # Build a map of variant_key -> style_override from the rules
    overrides: dict[str, str] = {}
    for rule in rules:
        action = rule.get("action") or {}
        if action.get("style_override"):
            variant_key = action.get("variant_key")
            if variant_key:
                overrides[variant_key] = action["style_override"]

    if not overrides:
        return

    # Style ID mapping: style name -> style ID in the DOCX
    # Body Text -> BodyText, Heading 4 -> Heading4, etc.
    style_id_map = {
        "Body Text": "BodyText",
        "BodyText": "BodyText",
        "Normal": "Normal",
    }

    # For each override, find the paragraph and change its style
    for variant_key, style_name in overrides.items():
        # The variant_key is like "analysis.in_plane_discontinuity_result"
        # Find the registry entry for this key to get the inventory_item_index
        # We need to search the body for paragraphs that contain this placeholder
        target_style_id = style_id_map.get(style_name, style_name)
        for child in body_children:
            tag = child.tag.split("}")[-1]
            if tag != "p":
                continue
            text = get_paragraph_text(child)
            if f"{{{{ {variant_key} }}}}" in text:
                # Found the paragraph — change its style
                pPr = child.find(f"{{{W_NS}}}pPr")
                if pPr is None:
                    pPr = etree.SubElement(child, f"{{{W_NS}}}pPr")
                    child.insert(0, pPr)
                pStyle = pPr.find(f"{{{W_NS}}}pStyle")
                if pStyle is None:
                    pStyle = etree.SubElement(pPr, f"{{{W_NS}}}pStyle")
                old_style = pStyle.get(f"{{{W_NS}}}val", "")
                pStyle.set(f"{{{W_NS}}}val", target_style_id)
                logger.log(
                    f"style override for {variant_key}",
                    f"style: {old_style}",
                    f"style: {target_style_id}",
                )


# ---------------------------------------------------------------------------
# Caption detection
# ---------------------------------------------------------------------------

CAPTION_PATTERN = re.compile(r"^(Table|Figure)\s+\d+\s*:", re.I)


def is_caption(p_element) -> bool:
    """Check if a paragraph is a caption (Table/Figure label with SEQ field,
    or Caption style, or text starting with 'Table N:' / 'Figure N:')."""
    text = get_paragraph_text(p_element)
    if CAPTION_PATTERN.match(text.strip()):
        return True
    # Check for SEQ field
    for instr in p_element.iter(f"{{{W_NS}}}instrText"):
        if instr.text and "SEQ" in instr.text.upper():
            return True
    for fld in p_element.iter(f"{{{W_NS}}}fldSimple"):
        instr = fld.get(f"{{{W_NS}}}instr", "")
        if "SEQ" in instr.upper():
            return True
    # Check for Caption style
    pPr = p_element.find(f"{{{W_NS}}}pPr")
    if pPr is not None:
        pStyle = pPr.find(f"{{{W_NS}}}pStyle")
        if pStyle is not None:
            style_val = pStyle.get(f"{{{W_NS}}}val", "")
            if "caption" in style_val.lower():
                return True
    return False


def substitute_caption_fragments(p_element, logger, idx: int) -> None:
    """For a caption paragraph, only substitute genuinely variable fragments:
    - NBC 105:YYYY -> {{ codes.edition }}
    - Damak -> {{ building.location }}
    - Clause numbers -> {{ codes.clauses.* }}
    Keep the 'Table N:' label, SEQ field, and style intact."""
    text = get_paragraph_text(p_element)
    original_text = text
    modified = False

    # NBC edition
    m = re.search(r"NBC\s*105\s*:\s*\d{4}", text)
    if m:
        text = text.replace(m.group(0), "{{ codes.edition }}")
        modified = True

    # Building location (Damak)
    if "Damak" in text:
        text = text.replace("Damak", "{{ building.location }}")
        modified = True

    # Clause numbers — replace sample clauses with {{ codes.clauses.* }}
    # Only do this if the clause number appears in the caption.
    # We check against the OWNER_CLAUSE_MAP and CURRENT_CLAUSE_KEYS from
    # inventory_template. For simplicity, we check common patterns.
    for clause_pattern in [
        (r"Cl\.\s*6\.3", "codes.clauses.vertical_force_dist"),
        (r"Cl\.\s*2\.1", "codes.clauses.material_properties"),
    ]:
        m = re.search(clause_pattern[0], text, re.I)
        if m:
            text = text.replace(m.group(0), f"{{{{ {clause_pattern[1]} }}}}")
            modified = True

    if modified:
        replace_paragraph_text_with_placeholder(p_element, text)
        logger.log(f"caption idx={idx} (partial)", original_text[:100], text[:100])


# ---------------------------------------------------------------------------
# Run helpers
# ---------------------------------------------------------------------------

def get_paragraph_text(p_element) -> str:
    """Concatenate all w:t text within a paragraph element."""
    texts = []
    for t in p_element.iter(f"{{{W_NS}}}t"):
        texts.append(t.text or "")
    return "".join(texts)


def merge_same_format_runs(p_element) -> None:
    """Merge adjacent runs with identical rPr (run properties) into a single
    run. The first run's rPr is kept; subsequent runs' text is appended."""
    runs = list(p_element.findall(f"{{{W_NS}}}r"))
    if len(runs) <= 1:
        return
    merged: list = []
    for run in runs:
        rpr = run.find(f"{{{W_NS}}}rPr")
        rpr_key = etree.tostring(rpr) if rpr is not None else b""
        if merged and merged[-1][1] == rpr_key:
            # Same formatting — append text to the previous run
            for t in run.findall(f"{{{W_NS}}}t"):
                prev_t = merged[-1][0].find(f"{{{W_NS}}}t")
                if prev_t is not None:
                    prev_t.text = (prev_t.text or "") + (t.text or "")
                else:
                    # Move the t element to the previous run
                    merged[-1][0].append(t)
            # Remove the now-empty run
            p_element.remove(run)
        else:
            merged.append((run, rpr_key))


def replace_paragraph_text_with_placeholder(p_element, placeholder: str) -> None:
    """Replace all text in a paragraph with a single placeholder string,
    keeping the first run's formatting."""
    runs = list(p_element.findall(f"{{{W_NS}}}r"))
    if not runs:
        # Create a new run
        r = etree.SubElement(p_element, f"{{{W_NS}}}r")
        t = etree.SubElement(r, f"{{{W_NS}}}t")
        t.text = placeholder
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        return
    # Keep the first run, clear its text, set the placeholder
    first_run = runs[0]
    # Remove all w:t elements from the first run
    for t in first_run.findall(f"{{{W_NS}}}t"):
        first_run.remove(t)
    # Also remove w:br, w:tab, etc.
    for tag in ("br", "tab", "cr"):
        for el in first_run.findall(f"{{{W_NS}}}{tag}"):
            first_run.remove(el)
    # Add a single w:t with the placeholder
    t = etree.SubElement(first_run, f"{{{W_NS}}}t")
    t.text = placeholder
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    # Remove all other runs
    for run in runs[1:]:
        p_element.remove(run)


def replace_text_in_paragraph(p_element, old_text: str, new_text: str) -> bool:
    """Replace old_text with new_text within a paragraph. Merges runs first,
    then does the replacement in the merged run. Returns True if replaced."""
    merge_same_format_runs(p_element)
    full_text = get_paragraph_text(p_element)
    if old_text not in full_text:
        return False
    new_full = full_text.replace(old_text, new_text)
    replace_paragraph_text_with_placeholder(p_element, new_full)
    return True


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def replace_image_with_placeholder(p_element, placeholder: str, image_index: int) -> bool:
    """Replace the Nth image (0-based) in a paragraph with a text placeholder.
    Handles both inline and anchored images."""
    drawings = list(p_element.iter(f"{{{W_NS}}}drawing"))
    if image_index >= len(drawings):
        return False
    drawing = drawings[image_index]
    # Get the parent run of this drawing
    parent_run = drawing.getparent()
    while parent_run is not None and parent_run.tag != f"{{{W_NS}}}r":
        parent_run = parent_run.getparent()
    if parent_run is None:
        return False
    # Replace the drawing with a text element in the run
    drawing.getparent().remove(drawing)
    # Add a text element to the run
    t = etree.SubElement(parent_run, f"{{{W_NS}}}t")
    t.text = placeholder
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return True


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------

def add_table_row_template(tbl_element, rule: dict[str, Any]) -> None:
    """Add {%tr for r in rows %}...{%tr endfor %} markers around the data
    rows of a table. The first row (header) is kept; subsequent rows become
    the template."""
    rows = tbl_element.findall(f"{{{W_NS}}}tr")
    if len(rows) < 2:
        return
    # Insert a paragraph with {%tr for %} before the second row
    # docxtpl uses {%tr %} in a special way: it looks for these tags in the
    # first cell of a row. We'll add the tag to the first data row.
    # Actually, docxtpl table row syntax is:
    #   {%tr for r in rows %}  cell content  {%tr endfor %}
    # These tags go INSIDE the cell paragraphs, as the first/last text.
    # For simplicity, we add the for-tag to the first cell of the first data row,
    # and the endfor-tag to the last cell of the last data row.
    first_data_row = rows[1]
    first_cell = first_data_row.find(f"{{{W_NS}}}tc")
    if first_cell is not None:
        first_p = first_cell.find(f"{{{W_NS}}}p")
        if first_p is not None:
            # Prepend {%tr for r in rows %} to the paragraph text
            prepend_text_to_paragraph(first_p, "{%tr for r in rows %}")

    last_data_row = rows[-1]
    last_cell = last_data_row.findall(f"{{{W_NS}}}tc")[-1] if last_data_row.findall(f"{{{W_NS}}}tc") else None
    if last_cell is not None:
        last_p = last_cell.find(f"{{{W_NS}}}p")
        if last_p is not None:
            append_text_to_paragraph(last_p, "{%tr endfor %}")


def prepend_text_to_paragraph(p_element, text: str) -> None:
    """Prepend text to the beginning of a paragraph's first run."""
    runs = p_element.findall(f"{{{W_NS}}}r")
    if runs:
        first_run = runs[0]
        t = first_run.find(f"{{{W_NS}}}t")
        if t is not None:
            t.text = text + (t.text or "")
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        else:
            new_t = etree.SubElement(first_run, f"{{{W_NS}}}t")
            new_t.text = text
            new_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    else:
        r = etree.SubElement(p_element, f"{{{W_NS}}}r")
        t = etree.SubElement(r, f"{{{W_NS}}}t")
        t.text = text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def append_text_to_paragraph(p_element, text: str) -> None:
    """Append text to the end of a paragraph's last run."""
    runs = p_element.findall(f"{{{W_NS}}}r")
    if runs:
        last_run = runs[-1]
        t = last_run.find(f"{{{W_NS}}}t")
        if t is not None:
            t.text = (t.text or "") + text
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        else:
            new_t = etree.SubElement(last_run, f"{{{W_NS}}}t")
            new_t.text = text
            new_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    else:
        r = etree.SubElement(p_element, f"{{{W_NS}}}r")
        t = etree.SubElement(r, f"{{{W_NS}}}t")
        t.text = text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


# ---------------------------------------------------------------------------
# Conditional helpers (staircase)
# ---------------------------------------------------------------------------

def insert_conditional_around_paragraphs(body_element, start_child_idx: int,
                                          end_child_idx: int, condition: str) -> None:
    """Insert {%p if condition %} before start_child_idx and {%p endif %}
    after end_child_idx. The {%p %} syntax tells docxtpl to remove the
    paragraph containing the tag and apply the conditional to the
    paragraphs between."""
    body_children = list(body_element)
    # Insert {%p endif %} after the end paragraph
    end_p = body_children[end_child_idx]
    endif_p = create_conditional_paragraph("{%p endif %}")
    end_p.addnext(endif_p)
    # Insert {%p if %} before the start paragraph
    start_p = body_children[start_child_idx]
    if_p = create_conditional_paragraph(f"{{%p if {condition} %}}")
    start_p.addprevious(if_p)


def create_conditional_paragraph(tag_text: str):
    """Create a minimal paragraph element containing a docxtpl conditional tag."""
    p = etree.Element(f"{{{W_NS}}}p")
    r = etree.SubElement(p, f"{{{W_NS}}}r")
    t = etree.SubElement(r, f"{{{W_NS}}}t")
    t.text = tag_text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return p


# ---------------------------------------------------------------------------
# Main generation logic
# ---------------------------------------------------------------------------

class ReplacementLogger:
    def __init__(self) -> None:
        self.entries: list[dict[str, str]] = []

    def log(self, location: str, old_text: str, placeholder: str) -> None:
        self.entries.append({
            "location": location,
            "old_text": old_text[:200],
            "placeholder": placeholder,
        })

    def write(self, path: Path) -> None:
        lines = [
            "# Template Replacement Log",
            "",
            f"Total replacements: **{len(self.entries)}**.",
            "",
            "| # | Location | Old text (preview) | Placeholder |",
            "|---|----------|-------------------|-------------|",
        ]
        for i, e in enumerate(self.entries, 1):
            old = e["old_text"].replace("|", "\\|").replace("\n", " ")[:100]
            lines.append(f"| {i} | {e['location']} | {old} | `{e['placeholder']}` |")
        lines.append("")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")


def generate_template(args: argparse.Namespace) -> ReplacementLogger:
    # Load everything
    entries = load_registry(args.registry)
    inv_items = load_inventory(args.inventory)
    rules = load_rules(args.rules)

    # Strict-mode validation
    validate_registry_strict(entries)

    # Load the sample DOCX
    doc = Document(str(args.input))
    body = doc.element.body

    # Build item -> body child mapping
    mapping = build_item_mapping(body)

    # Build lookup: inventory_item_index -> (body_child_idx, item_type)
    idx_to_child: dict[int, tuple[int, str]] = {}
    for item_idx, child_idx, item_type in mapping:
        idx_to_child[item_idx] = (child_idx, item_type)

    # Build registry lookup by inventory_item_index
    reg_by_idx: dict[int, list[dict[str, Any]]] = {}
    for entry in entries:
        idx = entry.get("inventory_item_index")
        if idx is not None:
            reg_by_idx.setdefault(idx, []).append(entry)

    logger = ReplacementLogger()
    body_children = list(body)

    # --- Process text entries (paragraphs with placeholders) ---
    # Keys that map to whole caption paragraphs and should NOT be replaced
    # as whole text. The caption stays fixed; only variable fragments within
    # the caption are substituted. These keys are removed from the registry
    # and listed in docs/needs_my_decision.md.
    CAPTION_ONLY_KEYS = {
        "project.empirical_period_intro",   # Table 8 caption
        "modal.rayleigh_period_x_uls",      # Table 10 caption
        "modal.rayleigh_period_y_uls",      # Table 11 caption
    }

    for entry in entries:
        if entry["type"] not in ("text", "number", "bool"):
            continue
        key = entry["key"]
        # Skip caption-only keys — they are handled by the caption loop below.
        if key in CAPTION_ONLY_KEYS:
            continue
        idx = entry.get("inventory_item_index")
        if idx is None or idx not in idx_to_child:
            continue
        child_idx, item_type = idx_to_child[idx]
        if item_type != "paragraph":
            continue
        p_element = body_children[child_idx]
        old_text = get_paragraph_text(p_element)

        # Skip if already processed (e.g., by clause citation logic)
        if "{{" in old_text:
            continue

        # Skip caption paragraphs — they are handled separately by
        # substitute_caption_fragments() to preserve style/SEQ/label.
        if is_caption(p_element):
            continue

        # Determine the replacement
        if key.startswith("codes.clauses."):
            # Clause citation: replace the sample clause with {{ key }}
            sample_clause = entry.get("sample_clause", "")
            target = entry.get("target_clause_2025", "")
            if sample_clause and sample_clause in old_text:
                replaced = replace_text_in_paragraph(
                    p_element, sample_clause, f"{{{{ {key} }}}}"
                )
                if replaced:
                    # Also replace NBC edition
                    full_text = get_paragraph_text(p_element)
                    if re.search(r"NBC\s*105\s*:\s*\d{4}", full_text):
                        replace_text_in_paragraph(
                            p_element,
                            re.search(r"NBC\s*105\s*:\s*\d{4}", full_text).group(0),
                            "{{ codes.edition }}",
                        )
                    logger.log(f"paragraph idx={idx}", old_text, f"{{{{ {key} }}}}")
        elif key.startswith("analysis.") and key.endswith("result"):
            # Computed variant: replace entire paragraph
            replace_paragraph_text_with_placeholder(p_element, f"{{{{ {key} }}}}")
            logger.log(f"paragraph idx={idx}", old_text, f"{{{{ {key} }}}}")
        elif key == "foundation.support_condition":
            # Support condition: replace with computed variant
            replace_paragraph_text_with_placeholder(p_element, f"{{{{ {key} }}}}")
            logger.log(f"paragraph idx={idx}", old_text, f"{{{{ {key} }}}}")
        elif key == "analysis.foundation_reaction_combination":
            # Foundation reaction caption: replace combination text
            replace_paragraph_text_with_placeholder(p_element, f"{{{{ {key} }}}}")
            logger.log(f"paragraph idx={idx}", old_text, f"{{{{ {key} }}}}")
        elif entry.get("source") == "computed" and entry.get("type") == "text":
            # Computed text: replace entire paragraph
            replace_paragraph_text_with_placeholder(p_element, f"{{{{ {key} }}}}")
            logger.log(f"paragraph idx={idx}", old_text, f"{{{{ {key} }}}}")
        elif old_text.strip() and "{{" not in old_text:
            # General text replacement: replace entire paragraph with placeholder
            # But only if the paragraph text is short (likely a simple value)
            if len(old_text.strip()) < 200:
                replace_paragraph_text_with_placeholder(p_element, f"{{{{ {key} }}}}")
                logger.log(f"paragraph idx={idx}", old_text, f"{{{{ {key} }}}}")

    # --- Process caption paragraphs (partial substitution only) ---
    # Captions keep their style, SEQ field, and "Table N:" label intact.
    # Only genuinely variable fragments are substituted.
    for child_idx, child in enumerate(body_children):
        tag = child.tag.split("}")[-1]
        if tag != "p":
            continue
        if is_caption(child):
            # Find the inventory item index for this paragraph
            for item_idx, c_idx, i_type in mapping:
                if c_idx == child_idx and i_type == "paragraph":
                    substitute_caption_fragments(child, logger, item_idx)
                    break

    # --- Apply style overrides (e.g., conclusion headings -> Body Text) ---
    apply_style_overrides(body_children, idx_to_child, rules, logger)

    # --- Process clause citation paragraphs (NBC edition replacement) ---
    for entry in entries:
        if entry["key"] == "codes.edition":
            idx = entry.get("inventory_item_index")
            if idx is None or idx not in idx_to_child:
                continue
            child_idx, item_type = idx_to_child[idx]
            if item_type != "paragraph":
                continue
            p_element = body_children[child_idx]
            old_text = get_paragraph_text(p_element)
            if re.search(r"NBC\s*105\s*:\s*\d{4}", old_text) and "{{ codes.edition }}" not in old_text:
                replace_text_in_paragraph(
                    p_element,
                    re.search(r"NBC\s*105\s*:\s*\d{4}", old_text).group(0),
                    "{{ codes.edition }}",
                )
                logger.log(f"paragraph idx={idx}", old_text, "{{ codes.edition }}")

    # --- Process image entries ---
    # Inline images are replaced with {{ figure.key }} text placeholders
    # (rendered via InlineImage at render time).
    # Anchored images are PRESERVED as-is (position, wrap, extent kept).
    # They are NOT converted to inline. At render time, use
    # DocxTemplate.replace_pic() to swap the image binary.
    anchored_images: list[dict[str, Any]] = []
    for entry in entries:
        if entry["type"] != "image":
            continue
        idx = entry.get("inventory_item_index")
        if idx is None or idx not in idx_to_child:
            continue
        child_idx, item_type = idx_to_child[idx]
        p_element = body_children[child_idx]
        key = entry["key"]
        images_in_para = [
            m for m in mapping
            if m[1] == child_idx and m[2] == "image"
        ]
        image_seq = next(
            (i for i, m in enumerate(images_in_para) if m[0] == idx),
            0,
        )
        # Check if this image is inline or anchored
        drawings = list(p_element.iter(f"{{{W_NS}}}drawing"))
        if image_seq < len(drawings):
            drawing = drawings[image_seq]
            inline_el = drawing.find(f"{{{WP_NS}}}inline")
            anchor_el = drawing.find(f"{{{WP_NS}}}anchor")
            if anchor_el is not None and inline_el is None:
                # Anchored image — preserve it, don't replace with placeholder
                extent = anchor_el.find(f"{{{WP_NS}}}extent")
                cx = int(extent.get("cx", "0")) if extent is not None else 0
                cy = int(extent.get("cy", "0")) if extent is not None else 0
                # Get the relationship ID for replace_pic
                blip = drawing.find(f".//{{{A_NS}}}blip")
                rid = blip.get(f"{{{R_NS}}}embed") if blip is not None else None
                anchored_images.append({
                    "key": key,
                    "idx": idx,
                    "rid": rid,
                    "cx": cx,
                    "cy": cy,
                })
                logger.log(f"anchored image idx={idx} (preserved)",
                           f"[anchored image, cx={cx} cy={cy}]",
                           f"preserved (use replace_pic with rId={rid})")
                continue
        # Inline image — replace with placeholder
        old_text = f"[image #{idx}]"
        replaced = replace_image_with_placeholder(p_element, f"{{{{ {key} }}}}", image_seq)
        if replaced:
            logger.log(f"image idx={idx}", old_text, f"{{{{ {key} }}}}")

    # --- Process table entries (data-driven tables get row templates) ---
    data_driven_tables = {
        "table.loads.load_assessment",
        "table.loads.live_load_intensity",
        "table.seismic.vertical_force_dist",
        "table.modal.rayleigh_x",
        "table.modal.rayleigh_y",
        "table.modal.periods_mass_part",
        "table.design.slab_design_output",
    }
    for entry in entries:
        if entry["type"] != "table":
            continue
        key = entry["key"]
        if key not in data_driven_tables:
            continue
        idx = entry.get("inventory_item_index")
        if idx is None or idx not in idx_to_child:
            continue
        child_idx, item_type = idx_to_child[idx]
        if item_type != "table":
            continue
        tbl_element = body_children[child_idx]
        add_table_row_template(tbl_element, {})
        logger.log(f"table idx={idx}", f"[table {key}]", "{%tr for r in rows %}...{%tr endfor %}")

    # --- Process staircase conditional ---
    # Find the staircase HEADING paragraph (not the TOC entry).
    # The heading has a "heading" style; the TOC entry has a "toc" style.
    staircase_children: list[int] = []
    for i, child in enumerate(body_children):
        tag = child.tag.split("}")[-1]
        if tag != "p":
            continue
        text = get_paragraph_text(child).lower()
        if "design of staircases" not in text:
            continue
        # Check style — only match heading paragraphs, not TOC entries
        style_el = child.find(f".//{{{W_NS}}}pPr/{{{W_NS}}}pStyle")
        style_val = style_el.get(f"{{{W_NS}}}val") if style_el is not None else None
        if not style_val or "heading" not in style_val.lower():
            continue
        # Found the heading; collect all children until the next heading of
        # the same or higher level, or "ANNEX".
        staircase_children.append(i)
        for j in range(i + 1, len(body_children)):
            next_child = body_children[j]
            next_tag = next_child.tag.split("}")[-1]
            if next_tag == "sectPr":
                break
            if next_tag != "p":
                continue
            next_text = get_paragraph_text(next_child)
            next_style_el = next_child.find(f".//{{{W_NS}}}pPr/{{{W_NS}}}pStyle")
            next_style_val = next_style_el.get(f"{{{W_NS}}}val") if next_style_el is not None else None
            # Stop at the next heading of same/higher level or ANNEX
            if next_style_val and "heading" in next_style_val.lower():
                try:
                    level = int(re.search(r"(\d+)", next_style_val).group(1))
                    heading_level_match = re.search(r"(\d+)", style_val)
                    if heading_level_match:
                        current_level = int(heading_level_match.group(1))
                        if level <= current_level:
                            break
                except (AttributeError, ValueError):
                    pass
            if "annex" in next_text.lower():
                break
            staircase_children.append(j)
        break

    if staircase_children:
        insert_conditional_around_paragraphs(
            body,
            staircase_children[0],
            staircase_children[-1],
            "building.has_staircase",
        )
        logger.log(
            f"paragraphs idx={staircase_children[0]}..{staircase_children[-1]}",
            "Design of Staircases block",
            "{%p if building.has_staircase %}...{%p endif %}",
        )
        # Refresh body_children after insertion
        body_children = list(body)

    # --- Save ---
    args.output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(args.output))
    return logger


def main() -> int:
    args = parse_args()
    try:
        logger = generate_template(args)
    except (ValueError, KeyError, etree.XMLSyntaxError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    logger.write(args.log)
    print(f"[OK] Template: {args.output}")
    print(f"[OK] Replacement log: {args.log} ({len(logger.entries)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
