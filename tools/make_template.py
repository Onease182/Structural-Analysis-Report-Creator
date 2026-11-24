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
BUILD_DIR = ROOT / "build"


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


def check_pending_implementation(entries: list[dict[str, Any]], fail: bool = False) -> list[str]:
    """Check for entries with status=pending_implementation.
    Returns the list of pending keys. If fail=True, raises ValueError."""
    pending = [e["key"] for e in entries if e.get("status") == "pending_implementation"]
    if pending and fail:
        raise ValueError(
            f"Strict mode: entries with status=pending_implementation block the build: {pending}. "
            f"These must be implemented before the template can be used in production."
        )
    return pending


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
        (r"Cl\.\s*6\.3", "Cl. {{ codes.clauses.vertical_force_dist }}"),
        (r"Cl\.\s*2\.1", "Cl. {{ codes.clauses.material_properties }}"),
    ]:
        m = re.search(clause_pattern[0], text, re.I)
        if m:
            text = text.replace(m.group(0), clause_pattern[1])
            modified = True

    # Also handle bare clause numbers in captions that don't have "Cl." prefix
    # but already have the NBC edition replaced
    if "{{ codes.edition }}" in text and "codes.clauses." not in text:
        for clause_num, clause_key in [
            ("6.3", "codes.clauses.vertical_force_dist"),
            ("2.1", "codes.clauses.material_properties"),
        ]:
            if clause_num in text:
                text = text.replace(clause_num, f"{{{{ {clause_key} }}}}")
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


def scrub_sample_literals(doc) -> None:
    """Remove sample-specific literals from every text node in the DOCX.

    This runs after all anchored replacements and table/conditional rewrites.
    Those operations can copy source paragraphs or rows, undoing an earlier
    paragraph-only scrub. The walk covers the main document and headers/footers.
    """
    replacements = {
        "ETABS 19.0.0": "{{ foundation.modeling_software }}",
        "3.175": "{{ building.story_height_m }}",
        "4.216": "{{ building.span_x_m }}",
        "10.058": "{{ building.span_y_m }}",
        "240.02": "{{ modal.base_shear_etabs }}",
        "1.004": "{{ seismic.distribution_exponent_k }}",
        "0.508": "{{ modal.empirical_period_s }}",
    }
    elements = [doc.element]
    for section in doc.sections:
        elements.extend([
            section.header._element,
            section.first_page_header._element,
            section.even_page_header._element,
            section.footer._element,
            section.first_page_footer._element,
            section.even_page_footer._element,
        ])
    seen: set[int] = set()
    for element in elements:
        if id(element) in seen:
            continue
        seen.add(id(element))
        # Word commonly splits a visible phrase across several runs. Handle
        # complete paragraphs first so replacements also catch those splits.
        for paragraph in element.iter(f"{{{W_NS}}}p"):
            text = get_paragraph_text(paragraph)
            replaced = text
            for literal, placeholder in replacements.items():
                replaced = replaced.replace(literal, placeholder)
            if replaced != text:
                replace_paragraph_text_with_placeholder(paragraph, replaced)
        for text_node in element.iter(f"{{{W_NS}}}t"):
            text = text_node.text or ""
            for literal, placeholder in replacements.items():
                text = text.replace(literal, placeholder)
            text_node.text = text


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

    # Strict-mode validation (clauses only — always enforced)
    validate_registry_strict(entries)

    # Check for pending_implementation (warn during template generation,
    # fail during strict builds)
    pending = check_pending_implementation(entries, fail=False)
    if pending:
        print(f"[WARN] Pending implementation: {pending}. Strict builds will fail.", file=sys.stderr)

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
    paragraph_idx_applied: set[int] = set()  # Track which paragraphs got a sentence_template

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

        # Skip caption paragraphs
        if is_caption(p_element):
            continue

        # PRIORITY 1: Apply sentence_template if:
        # - The template has multiple keys (not just "{{ key }}")
        # - The paragraph has NOT already been processed by a sentence_template
        #   from a previous entry (tracked by paragraph_idx_applied set)
        # - OR the paragraph has {{ }} from a clause citation but NOT from a
        #   sentence_template (tracked by paragraph_idx_applied)
        sentence_template = entry.get("sentence_template")
        if sentence_template and "{{" in sentence_template:
            stripped_tmpl = sentence_template.strip()
            is_whole_para = stripped_tmpl == f"{{{{ {key} }}}}"
            already_has_template = child_idx in paragraph_idx_applied
            if not is_whole_para and not already_has_template:
                replace_paragraph_text_with_placeholder(p_element, sentence_template)
                logger.log(f"paragraph idx={idx} (sentence template)", old_text[:100], sentence_template[:100])
                paragraph_idx_applied.add(child_idx)
                continue

        # Skip if already processed by a sentence_template
        if child_idx in paragraph_idx_applied:
            continue
        # Skip if already has {{ from a previous non-template entry (clause citation)
        if "{{" in old_text:
            continue

        # PRIORITY 2: Computed variants — whole-paragraph replacement is
        # allowed ONLY where the owner decision defines computed variants.
        if key.startswith("analysis.") and key.endswith("result"):
            replace_paragraph_text_with_placeholder(p_element, f"{{{{ {key} }}}}")
            logger.log(f"paragraph idx={idx}", old_text, f"{{{{ {key} }}}}")
        elif key == "foundation.support_condition":
            replace_paragraph_text_with_placeholder(p_element, f"{{{{ {key} }}}}")
            logger.log(f"paragraph idx={idx}", old_text, f"{{{{ {key} }}}}")
        elif key == "analysis.foundation_reaction_combination":
            replace_paragraph_text_with_placeholder(p_element, f"{{{{ {key} }}}}")
            logger.log(f"paragraph idx={idx}", old_text, f"{{{{ {key} }}}}")
        elif key.startswith("codes.clauses."):
            # Clause citation: replace the sample clause with {{ key }}.
            # Try "Cl." + sample_clause first (e.g., "Cl.2.1") to avoid
            # double "Cl." when the value also contains "Cl.".
            sample_clause = entry.get("sample_clause", "")
            target = entry.get("target_clause_2025", "")
            if sample_clause:
                # Convention: the value holds everything AFTER the word "clause".
                # The word "clause" stays as fixed text in the template.
                # Only replace "Cl.NUMBER" and "Cl. NUMBER" (because "Cl." would
                # duplicate if the value also contains "Cl."). For "clause NUMBER",
                # only replace the NUMBER, keeping "clause" as fixed text.
                replaced = False
                for prefix in [f"Cl.{sample_clause}", f"Cl. {sample_clause}"]:
                    if prefix in old_text:
                        replace_text_in_paragraph(p_element, prefix, f"{{{{ {key} }}}}")
                        replaced = True
                        break
                if not replaced and sample_clause in old_text:
                    replace_text_in_paragraph(
                        p_element, sample_clause, f"{{{{ {key} }}}}"
                    )
                # Also replace NBC edition
                full_text = get_paragraph_text(p_element)
                if re.search(r"NBC\s*105\s*:\s*\d{4}", full_text):
                    replace_text_in_paragraph(
                        p_element,
                        re.search(r"NBC\s*105\s*:\s*\d{4}", full_text).group(0),
                        "{{ codes.edition }}",
                    )
                logger.log(f"paragraph idx={idx}", old_text, f"{{{{ {key} }}}}")
        elif entry.get("source") == "computed" and entry.get("type") == "text":
            # Computed text without sentence template: replace entire paragraph
            replace_paragraph_text_with_placeholder(p_element, f"{{{{ {key} }}}}")
            logger.log(f"paragraph idx={idx}", old_text, f"{{{{ {key} }}}}")
        elif old_text.strip() and "{{" not in old_text:
            # General text replacement: replace entire paragraph with placeholder
            # But only if the paragraph text is short (likely a simple value)
            if len(old_text.strip()) < 200:
                replace_paragraph_text_with_placeholder(p_element, f"{{{{ {key} }}}}")
                logger.log(f"paragraph idx={idx}", old_text, f"{{{{ {key} }}}}")

    # Current sample cover fields are deliberately anchored by text rather
    # than stale inventory positions so edits to the cover remain safe.
    for child in body_children:
        if child.tag.split("}")[-1] != "p":
            continue
        text = get_paragraph_text(child)
        if text.strip() == "Swarup Engineering Consultancy":
            replace_paragraph_text_with_placeholder(child, "{{ consultancy.name }}")
        elif text.strip() == "Dharan-16, Sunsari":
            replace_paragraph_text_with_placeholder(child, "{{ consultancy.address }}")
        elif text.strip() == "Er. Anij Bhandari":
            replace_paragraph_text_with_placeholder(child, "{{ designer.name }}")
        elif text.strip().startswith("NEC No.13925"):
            replace_paragraph_text_with_placeholder(child, "NEC No.{{ designer.nec_no }} {{ designer.nec_category }}")
        elif text.strip().startswith("This report comprises the summary"):
            replace_paragraph_text_with_placeholder(child, "This report comprises the summary of the residential building of {{ client.owner_name }} {{ building.location }}, Nepal. The reports consist of the design procedures adopted, the assumptions made, the inputs made in the design and the design output. During the design, it is assumed that the client will completely follow the architectural as well as the structural design. It is also assumed that the construction will be supervised by professional engineer.")

    # Normalize legacy replacements that may already have been applied by the
    # registry-index pass before the current cover anchors are handled.
    for child in body_children:
        if child.tag.split("}")[-1] != "p":
            continue
        text = get_paragraph_text(child)
        if "{{ client.consultant_name }}" in text:
            replace_paragraph_text_with_placeholder(child, "{{ consultancy.name }}")
        elif "{{ building.location }}" == text.strip() and child is not body_children[10]:
            # Keep location variables elsewhere; this exact early cover line is
            # the address field in the current sample.
            pass
        elif "{{ designer" not in text and text.strip() == "Er. Anij Bhandari":
            replace_paragraph_text_with_placeholder(child, "{{ designer.name }}")
    # Paragraph positions 9/10 are anchored by their cover order after the
    # sample's text pass; this avoids binding to a stale inventory index.
    if len(body_children) > 10:
        if get_paragraph_text(body_children[9]).strip() in {"{{ client.consultant_name }}", "Swarup Engineering Consultancy"}:
            replace_paragraph_text_with_placeholder(body_children[9], "{{ consultancy.name }}")
        if get_paragraph_text(body_children[10]).strip() == "{{ building.location }}":
            replace_paragraph_text_with_placeholder(body_children[10], "{{ consultancy.address }}")
    for child in body_children:
        text = get_paragraph_text(child)
        if text.strip() in {"{{ designer.nec_no }}", "{{ client.designer_nec_reg }}"}:
            replace_paragraph_text_with_placeholder(child, "NEC No.{{ designer.nec_no }} {{ designer.nec_category }}")
        elif text.strip() == "Er. Anij Bhandari":
            replace_paragraph_text_with_placeholder(child, "{{ designer.name }}")
        elif text.strip().startswith("NEC No.13925"):
            replace_paragraph_text_with_placeholder(child, "NEC No.{{ designer.nec_no }} {{ designer.nec_category }}")

    # Remove known sample-only literals from both paragraphs and table cells.
    # Values remain data-layer placeholders; the sample context supplies the
    # regression values and real projects supply computed/source values.
    literal_map = {
        "ETABS 19.0.0": "{{ foundation.modeling_software }}",
        "3.175": "{{ building.story_height_m }}",
        "4.216": "{{ building.span_x_m }}",
        "10.058": "{{ building.span_y_m }}",
        "240.02": "{{ modal.base_shear_etabs }}",
        "1.004": "{{ seismic.distribution_exponent_k }}",
        "0.508": "{{ modal.empirical_period_s }}",
    }
    for node in body.iter(f"{{{W_NS}}}t"):
        value = node.text or ""
        for old, new in literal_map.items():
            value = value.replace(old, new)
        node.text = value

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

    # --- Process table cell placeholders ---
    # For tables classified as "cell-placeholders" in docs/table_plan.md,
    # replace specific cells containing sample data with {{ key }}.
    # The mapping is (table_index_in_doc, row, col) -> registry key.
    TABLE_CELL_MAP: dict[tuple[int, int, int], str] = {
        # T0 (Client details) — derived from row label in col 1
        (0, 1, 2): "client.owner_name",
        (0, 2, 2): "building.location",
        (0, 3, 2): "building.occupancy_class",
        (0, 4, 2): "client.designer_name",
        (0, 5, 2): "client.designer_nec_reg",
        (0, 6, 2): "client.designer_contact",
        (0, 7, 2): "client.consultant_name",
        (0, 8, 2): "client.municipality_reg",
        (0, 9, 2): "client.application_date",
        # T2 (Building general info) — derived from row label in col 1
        (2, 0, 2): "building.location",
        (2, 1, 2): "building.storeys_count_numeric",
        (2, 2, 2): "building.num_storeys_analysed",
        (2, 3, 2): "building.num_basements",
        (2, 4, 2): "building.height_ground_floor_m",
        (2, 5, 2): "building.height_typical_floor_m",
        (2, 6, 2): "building.total_height_m",
        (2, 7, 2): "building.height_period_m",
        (2, 8, 2): "building.occupancy_class",
        # T3 (Element sizes) — col 1 = description, col 2 = grade
        (3, 1, 1): "table.elements.col_desc",
        (3, 1, 2): "materials.concrete_grade_used",
        (3, 2, 1): "table.elements.beam_desc",
        (3, 2, 2): "materials.concrete_grade_used",
        (3, 3, 1): "table.elements.stair_desc",
        (3, 3, 2): "materials.concrete_grade_used",
        (3, 4, 1): "table.elements.slab_desc",
        (3, 4, 2): "materials.concrete_grade_used",
        (3, 5, 1): "table.elements.foundation_desc",
        (3, 5, 2): "materials.concrete_grade_used",
        (3, 5, 3): "foundation.soil_bearing",
        # T4 (Structural system & foundation)
        (4, 0, 2): "structural.system_type_generic",
        (4, 1, 2): "foundation.type",
        (4, 2, 2): "slab.type",
        # T8 (Empirical period)
        (8, 0, 5): "building.total_height_m",
        (8, 1, 1): "structural.system_type_period_category",
        (8, 2, 1): "seismic.time_coefficient_kt",
        (8, 3, 4): "modal.empirical_period_unamplified_s",
        (8, 5, 3): "modal.empirical_period_s",
        # T12 (Seismic design parameters)
        (12, 0, 2): "modal.empirical_period_s",
        (12, 2, 2): "seismic.site_soil_category",
        (12, 3, 3): "seismic.tc",
        (12, 4, 2): "seismic.soil_class",
        (12, 5, 1): "seismic.alpha",
        (12, 5, 3): "seismic.distribution_exponent_k",
        (12, 6, 2): "seismic.spectral_shape_factor_cht",
        (12, 7, 1): "building.location",
        (12, 7, 3): "seismic.zone_factor_z",
        (12, 8, 2): "seismic.structural_type",
        (12, 9, 2): "seismic.importance_factor_i_table",
        (12, 10, 3): "seismic.elastic_site_spectra_c",
        (12, 11, 3): "seismic.elastic_site_spectra_cs",
        (12, 13, 3): "structural.system_type_table_5_2",
        (12, 14, 3): "seismic.response_modification_factor_rmu",
        # T13 (Overstrength factors)
        (13, 0, 1): "design.overstrength_ultimate",
        (13, 1, 1): "design.overstrength_serviceability",
        (13, 2, 1): "seismic.hsc_uls",
        (13, 3, 1): "seismic.hsc_sls",
        # T16 (Beam deflection check)
        (16, 1, 1): "table.design.beam_boundary",
        (16, 2, 1): "table.design.beam_effective_span",
        (16, 3, 1): "table.design.beam_overall_depth",
        (16, 4, 1): "table.design.beam_effective_depth",
        (16, 5, 1): "table.design.beam_basic_ld_ratio",
        (16, 6, 1): "table.design.beam_ast_req",
        (16, 7, 1): "table.design.beam_ast_prov",
        (16, 8, 1): "table.design.beam_pt",
        (16, 9, 1): "table.design.beam_fs",
        (16, 10, 1): "table.design.beam_mod_factor",
        (16, 11, 1): "table.design.beam_permissible_ld",
        (16, 12, 1): "table.design.beam_provided_ld",
        (16, 13, 1): "table.design.beam_check_result",
        # T6 (Load assessment) — specific cell with story height
        (6, 11, 1): "building.story_height_m",
        # T15 removed → image placeholder (no cell map needed)
    }

    # Cell suffixes: fixed text appended after the placeholder in specific cells
    CELL_SUFFIXES: dict[tuple[int, int, int], str] = {
        # T2 height cells have " meters" suffix in the sample
        (2, 4, 2): " meters",
        (2, 5, 2): " meters",
        (2, 6, 2): " meters",
        (2, 7, 2): " meters",
        # T2 occupancy row 8 has " Building" suffix
        (2, 8, 2): " Building",
    }

    # Apply cell placeholders
    for (tbl_idx, row_idx, col_idx), key in TABLE_CELL_MAP.items():
        if tbl_idx < len(doc.tables):
            tbl = doc.tables[tbl_idx]
            if row_idx < len(tbl.rows) and col_idx < len(tbl.rows[row_idx].cells):
                cell = tbl.rows[row_idx].cells[col_idx]
                old_cell_text = cell.text.strip()
                if old_cell_text and "{{" not in old_cell_text:
                    suffix = CELL_SUFFIXES.get((tbl_idx, row_idx, col_idx), "")
                    placeholder = f"{{{{ {key} }}}}{suffix}"
                    # Replace cell text with placeholder
                    for p in cell.paragraphs:
                        for run in p.runs:
                            run.text = ""
                    if cell.paragraphs:
                        p = cell.paragraphs[0]
                        if p.runs:
                            p.runs[0].text = placeholder
                        else:
                            p.add_run(placeholder)
                    logger.log(
                        f"table T{tbl_idx} cell ({row_idx},{col_idx})",
                        old_cell_text[:60],
                        placeholder,
                    )

    # --- T15: Replace slab design table with image placeholder ---
    # Per owner decision: T15 (slab design, 88×8) → image placeholder
    # figure.design.slab_sheet (user_supplied).
    if len(doc.tables) > 15:
        tbl15 = doc.tables[15]
        tbl15_element = tbl15._tbl
        # Get the paragraph before the table (caption)
        prev = tbl15_element.getprevious()
        # Replace the table with a paragraph containing the image placeholder
        replacement_p = etree.Element(f"{{{W_NS}}}p")
        replacement_r = etree.SubElement(replacement_p, f"{{{W_NS}}}r")
        replacement_t = etree.SubElement(replacement_r, f"{{{W_NS}}}t")
        replacement_t.text = "{{ figure.design.slab_sheet }}"
        replacement_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        tbl15_element.addprevious(replacement_p)
        tbl15_element.getparent().remove(tbl15_element)
        logger.log("table T15", "[88×8 slab design table]",
                   "{{ figure.design.slab_sheet }} (image placeholder)")

    # --- Fix hard-coded clause references in ALL paragraphs ---
    # Replace "4.1.4" → {{ codes.clauses.seismic_zoning_factor }}
    # Replace "4.1.5" → {{ codes.clauses.importance_factor }}
    # Replace "(Cl. 3.6.1)" → ({{ codes.clauses.load_combinations }})
    # These appear in body paragraphs (the Ch(t) definition line and the
    # "For Parallel System" paragraph), not just table cells.
    PARA_CLAUSE_REPLACEMENTS = [
        ("4.1.4", "{{ codes.clauses.seismic_zoning_factor }}"),
        ("4.1.5", "{{ codes.clauses.importance_factor }}"),
        ("(Cl. 3.6.1)", "(Cl. {{ codes.clauses.load_combinations }})"),
        # Don't replace bare "Cl. 3.6.1" — it's already handled by the "(Cl. ...)" form above.
    ]
    for child in body_children:
        tag = child.tag.split("}")[-1]
        if tag != "p":
            continue
        text = get_paragraph_text(child)
        # Do NOT skip paragraphs that already have placeholders — they may
        # also contain hard-coded clause values (e.g., the Ch(t) paragraph
        # has {{ codes.clauses.spectral_shape_factor }} but also "4.1.4").
        modified = False
        new_text = text
        for old_val, replacement in PARA_CLAUSE_REPLACEMENTS:
            if old_val in new_text:
                new_text = new_text.replace(old_val, replacement)
                modified = True
        if modified:
            replace_paragraph_text_with_placeholder(child, new_text)
            logger.log("hard-coded clause in paragraph", text[:80], new_text[:80])

    # --- Fix hard-coded clause references in table cells ---
    # Replace "4.1.4" → {{ codes.clauses.seismic_zoning_factor }}
    # Replace "4.1.5" → {{ codes.clauses.importance_factor }}
    # Replace "(Cl. 3.6.1)" → ({{ codes.clauses.load_combinations }})
    HARD_CODED_CLAUSES = {
        "4.1.4": "codes.clauses.seismic_zoning_factor",
        "4.1.5": "codes.clauses.importance_factor",
        "(Cl. 3.6.1)": "({{ codes.clauses.load_combinations }})",
        "Cl. 3.6.1": "{{ codes.clauses.load_combinations }}",
    }
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                cell_text = cell.text
                modified = False
                new_text = cell_text
                for old_val, replacement in HARD_CODED_CLAUSES.items():
                    if old_val in new_text and "{{" not in new_text:
                        if old_val.startswith("("):
                            new_text = new_text.replace(old_val, replacement)
                        else:
                            new_text = new_text.replace(old_val, f"{{{{ {replacement} }}}}")
                        modified = True
                if modified:
                    for p in cell.paragraphs:
                        for run in p.runs:
                            run.text = ""
                    if cell.paragraphs:
                        p = cell.paragraphs[0]
                        if p.runs:
                            p.runs[0].text = new_text
                        else:
                            p.add_run(new_text)
                    logger.log("hard-coded clause in table cell", cell_text[:60], new_text[:60])

    # --- Process table entries (data-driven tables get row templates) ---
    # Data-driven loop tables: T9, T10, T11, T14
    # Structure: header row(s) + for-row + template-row + endfor-row + footer row(s)
    # Footer rows (Total, Rayleigh result) are restored with placeholders.
    LOOP_TABLE_COLUMNS: dict[int, list[str]] = {
        9: ["level", "wi", "hi", "hik", "wi_hik", "fi", "shear"],
        10: ["level", "wi", "di_mm", "di_m", "di2", "fi", "fi_di", "wi_di2"],
        11: ["level", "wi", "di_mm", "di_m", "di2", "fi", "fi_di", "wi_di2"],
        14: ["case", "mode", "period", "ux", "uy", "sum_ux", "sum_uy"],
    }
    LOOP_TABLE_HEADER_ROWS: dict[int, int] = {
        9: 1, 10: 1, 11: 1, 14: 2,
    }
    # Context key path for each loop table (dotted path to the {"rows": [...]} dict)
    LOOP_TABLE_CTX_KEYS: dict[int, str] = {
        9: "table.seismic.vertical_force_dist",
        10: "table.modal.rayleigh_x",
        11: "table.modal.rayleigh_y",
        14: "table.modal.periods_mass_part",
    }
    # Footer rows: (table_index, row_index_in_original, placeholder_map)
    # placeholder_map: {col_index: registry_key}
    LOOP_TABLE_FOOTERS: dict[int, list[dict]] = {
        9: [
            {"row_idx": 5, "cells": {1: "totals.wi_kg", 4: "totals.wi_hik", 5: "totals.fi"}, "label_col": 0, "label": "Total"},
        ],
        10: [
            {"row_idx": 5, "cells": {5: "totals.fi", 6: "totals.fi_di_x", 7: "totals.wi_di2_x"}, "label_col": 0, "label": "Total"},
            {"row_idx": 6, "cells": {7: "modal.rayleigh_period_x_s"}, "label": "Rayleigh time period, T ="},
        ],
        11: [
            {"row_idx": 5, "cells": {5: "totals.fi", 6: "totals.fi_di_y", 7: "totals.wi_di2_y"}, "label_col": 0, "label": "Total"},
            {"row_idx": 6, "cells": {7: "modal.rayleigh_period_y_s"}, "label": "Rayleigh time period, T ="},
        ],
        14: [],  # No footer rows for modal periods table
    }

    for tbl_idx, col_names in LOOP_TABLE_COLUMNS.items():
        if tbl_idx >= len(doc.tables):
            continue
        tbl = doc.tables[tbl_idx]
        tbl_element = tbl._tbl
        rows = tbl_element.findall(f"{{{W_NS}}}tr")
        n_header = LOOP_TABLE_HEADER_ROWS.get(tbl_idx, 1)
        if len(rows) <= n_header:
            continue

        # Save footer rows BEFORE modifying
        footers = LOOP_TABLE_FOOTERS.get(tbl_idx, [])
        saved_footer_rows = []
        for fdef in footers:
            ridx = fdef["row_idx"]
            if ridx < len(rows):
                # Deep-copy the footer row to preserve formatting
                saved_footer_rows.append((fdef, rows[ridx]))

        # Step 1: Modify the first data row to be the TEMPLATE row.
        template_row = rows[n_header]
        cells = template_row.findall(f"{{{W_NS}}}tc")
        for ci, cell in enumerate(cells):
            if ci < len(col_names):
                col_name = col_names[ci]
                paras = cell.findall(f"{{{W_NS}}}p")
                if paras:
                    p = paras[0]
                    for r in p.findall(f"{{{W_NS}}}r"):
                        p.remove(r)
                    new_r = etree.SubElement(p, f"{{{W_NS}}}r")
                    new_t = etree.SubElement(new_r, f"{{{W_NS}}}t")
                    new_t.text = f"{{{{ r.{col_name} }}}}"
                    new_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                    for extra_p in paras[1:]:
                        cell.remove(extra_p)

        # Step 2: Create for-row BEFORE the template row.
        # Use the full dotted context path so docxtpl can resolve it.
        ctx_key = LOOP_TABLE_CTX_KEYS.get(tbl_idx, "")
        for_tag = f"{{%tr for r in {ctx_key}.rows %}}" if ctx_key else "{%tr for r in rows %}"
        for_row = etree.Element(f"{{{W_NS}}}tr")
        for_cell = etree.SubElement(for_row, f"{{{W_NS}}}tc")
        for_p = etree.SubElement(for_cell, f"{{{W_NS}}}p")
        for_r = etree.SubElement(for_p, f"{{{W_NS}}}r")
        for_t = etree.SubElement(for_r, f"{{{W_NS}}}t")
        for_t.text = for_tag
        for_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        template_row.addprevious(for_row)

        # Step 3: Create endfor-row AFTER the template row.
        endfor_row = etree.Element(f"{{{W_NS}}}tr")
        endfor_cell = etree.SubElement(endfor_row, f"{{{W_NS}}}tc")
        endfor_p = etree.SubElement(endfor_cell, f"{{{W_NS}}}p")
        endfor_r = etree.SubElement(endfor_p, f"{{{W_NS}}}r")
        endfor_t = etree.SubElement(endfor_r, f"{{{W_NS}}}t")
        endfor_t.text = "{%tr endfor %}"
        endfor_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        template_row.addnext(endfor_row)

        # Step 4: Restore footer rows with placeholders.
        insert_after = endfor_row
        for fdef, orig_row in saved_footer_rows:
            # Deep-copy the original footer row
            footer_row = copy.deepcopy(orig_row)
            # Replace specified cells with placeholders
            footer_cells = footer_row.findall(f"{{{W_NS}}}tc")
            for col_idx, key in fdef.get("cells", {}).items():
                if col_idx < len(footer_cells):
                    cell = footer_cells[col_idx]
                    paras = cell.findall(f"{{{W_NS}}}p")
                    if paras:
                        p = paras[0]
                        for r in p.findall(f"{{{W_NS}}}r"):
                            p.remove(r)
                        new_r = etree.SubElement(p, f"{{{W_NS}}}r")
                        new_t = etree.SubElement(new_r, f"{{{W_NS}}}t")
                        new_t.text = f"{{{{ {key} }}}}"
                        new_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            # Set label cell if specified
            label_col = fdef.get("label_col")
            label_text = fdef.get("label")
            if label_col is not None and label_text and label_col < len(footer_cells):
                cell = footer_cells[label_col]
                paras = cell.findall(f"{{{W_NS}}}p")
                if paras:
                    p = paras[0]
                    for r in p.findall(f"{{{W_NS}}}r"):
                        p.remove(r)
                    new_r = etree.SubElement(p, f"{{{W_NS}}}r")
                    new_t = etree.SubElement(new_r, f"{{{W_NS}}}t")
                    new_t.text = label_text
                    new_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            insert_after.addnext(footer_row)
            insert_after = footer_row
            logger.log(f"table T{tbl_idx} footer", f"[row {fdef['row_idx']}]",
                       f"placeholders: {list(fdef.get('cells',{}).values())}")

        # Step 5: Remove ALL original extra rows (data rows + original footer rows)
        # We've already deep-copied footer rows and inserted them.
        # Remove everything after the template row except our inserted rows.
        all_rows = tbl_element.findall(f"{{{W_NS}}}tr")
        # Find template row position
        template_pos = None
        for i, r in enumerate(all_rows):
            if r is template_row:
                template_pos = i
                break
        if template_pos is not None:
            # Remove original rows that come after our inserted structure
            # Our structure: header(0..n_header-1), for_row(n_header), template(n_header+1),
            # endfor(n_header+2), footers(n_header+3..)
            # Original rows after template_pos+1 that are NOT our inserted rows
            our_rows = {for_row, template_row, endfor_row}
            our_rows.update(fr for _, fr in saved_footer_rows)  # original refs, not copies
            # Actually, we need to remove original data/footer rows, not our copies
            for r in list(all_rows):
                if r in our_rows:
                    continue
                # Check if it's one of our inserted footer copies
                is_our_footer = False
                for fr in tbl_element.findall(f"{{{W_NS}}}tr"):
                    pass  # Can't easily check identity of copies
                # Simple approach: remove all original rows after template that are
                # not the for_row, endfor_row, or our footer copies.
                # Since we inserted copies AFTER endfor_row, and original rows are
                # still in the tree, we need to remove originals.
                pass

            # Simpler: just remove all rows that are original data/footer rows.
            # The original data rows start at index n_header+1 (after template).
            # The original footer rows are at their original indices.
            # We've already copied footers. Remove all original non-header rows
            # except the template_row.
            rows_to_remove = []
            for i, r in enumerate(all_rows):
                if i < n_header:
                    continue  # Keep header rows
                if r is template_row:
                    continue  # Keep template row
                if r is for_row or r is endfor_row:
                    continue  # Keep our inserted rows
                # Check if it's one of our footer copies (they're new elements)
                # Original rows have the same identity as in `rows` list
                if r in rows:
                    rows_to_remove.append(r)
            for r in rows_to_remove:
                tbl_element.remove(r)

        n_footers = len(saved_footer_rows)
        logger.log(f"table T{tbl_idx} (loop)", f"[{len(rows)} rows → {n_header + 3 + n_footers} rows]",
                   f"for + template + endfor + {n_footers} footer(s)")

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
    scrub_sample_literals(doc)
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
