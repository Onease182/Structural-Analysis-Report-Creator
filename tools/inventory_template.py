#!/usr/bin/env python3
"""Inventory a DOCX template in document order without modifying the input file.

The inventory walks ``word/document.xml`` body children and nested paragraph
content so paragraphs, tables, images, section breaks, and fields are visible
as separate items. It writes JSON, Markdown, YAML, and a decision log.

Example:
    python tools/inventory_template.py \
        --input "Chatra Bahadur Ramtel.docx" \
        --json docs/template_inventory.json \
        --markdown docs/template_inventory.md \
        --registry docs/placeholder_registry.yaml \
        --decisions docs/needs_my_decision.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable
from zipfile import ZipFile

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"w": W_NS, "a": A_NS, "wp": WP_NS, "pic": PIC_NS, "r": R_NS}
EMU_PER_INCH = 914400


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=Path("Chatra Bahadur Ramtel.docx"))
    p.add_argument("--json", type=Path, default=Path("docs/template_inventory.json"))
    p.add_argument("--markdown", type=Path, default=Path("docs/template_inventory.md"))
    p.add_argument("--registry", type=Path, default=Path("docs/placeholder_registry.yaml"))
    p.add_argument("--decisions", type=Path, default=Path("docs/needs_my_decision.md"))
    p.add_argument("--force", action="store_true", help="replace existing output artifacts")
    return p.parse_args()


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def preview(text: str, limit: int = 240) -> str:
    text = clean_text(text)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def relationship_targets(z: ZipFile) -> dict[str, str]:
    rels = etree.fromstring(z.read("word/_rels/document.xml.rels"))
    out: dict[str, str] = {}
    for rel in rels:
        rid = rel.get("Id")
        target = rel.get("Target", "")
        if rid:
            out[rid] = target
    return out


def paragraph_text(p: etree._Element) -> str:
    parts: list[str] = []
    for node in p.xpath(".//w:t | .//w:tab | .//w:br | .//w:cr", namespaces=NS):
        if local_name(node.tag) == "t":
            parts.append(node.text or "")
        elif local_name(node.tag) == "tab":
            parts.append("\\t")
        else:
            parts.append("\\n")
    return clean_text("".join(parts))


def style_name(p: etree._Element, styles: dict[str, str]) -> str | None:
    sid = p.xpath("string(./w:pPr/w:pStyle/@w:val)", namespaces=NS)
    return styles.get(sid, sid or None)


def load_styles(z: ZipFile) -> dict[str, str]:
    if "word/styles.xml" not in z.namelist():
        return {}
    root = etree.fromstring(z.read("word/styles.xml"))
    result: dict[str, str] = {}
    for style in root.xpath(".//w:style", namespaces=NS):
        sid = style.get(f"{{{W_NS}}}styleId")
        name = style.xpath("string(./w:name/@w:val)", namespaces=NS)
        if sid:
            result[sid] = name or sid
    return result


def table_info(tbl: etree._Element) -> tuple[int, int, list[str]]:
    rows = tbl.xpath("./w:tr", namespaces=NS)
    shape = []
    for row in rows:
        cells = row.xpath("./w:tc", namespaces=NS)
        shape.append(len(cells))
    cols = max(shape, default=0)
    header: list[str] = []
    if rows:
        for cell in rows[0].xpath("./w:tc", namespaces=NS):
            header.append(clean_text("".join(cell.xpath(".//w:t/text()", namespaces=NS))))
    return len(rows), cols, header


def section_number_for_body_child(child: etree._Element, current: int) -> int:
    if child.xpath(".//w:pPr/w:sectPr", namespaces=NS) or local_name(child.tag) == "sectPr":
        return current + 1
    return current


def image_items(p: etree._Element, rels: dict[str, str], section: int, parent_index: int) -> list[dict[str, Any]]:
    result = []
    for drawing in p.xpath(".//w:drawing", namespaces=NS):
        inline = drawing.xpath("./wp:inline | ./wp:anchor", namespaces=NS)
        container = inline[0] if inline else drawing
        extent = container.find(f"{{{WP_NS}}}extent")
        cx = int(extent.get("cx", "0")) if extent is not None else 0
        cy = int(extent.get("cy", "0")) if extent is not None else 0
        docpr = container.find(f"{{{WP_NS}}}docPr")
        alt = ""
        title = ""
        doc_id = None
        if docpr is not None:
            alt = docpr.get("descr", "")
            title = docpr.get("title", "")
            doc_id = docpr.get("id")
        rid = drawing.xpath("string(.//a:blip/@r:embed)", namespaces=NS)
        target = rels.get(rid, "")
        if target and not target.startswith("word/"):
            target = "word/" + target.lstrip("/")
        result.append({
            "type": "image",
            "style_name": None,
            "section": section,
            "text_preview": preview(alt or title),
            "image": {
                "relationship_id": rid or None,
                "target": target or None,
                "alt_text": alt or None,
                "title": title or None,
                "doc_property_id": int(doc_id) if doc_id and doc_id.isdigit() else doc_id,
                "width_emu": cx,
                "height_emu": cy,
                "width_inches": round(cx / EMU_PER_INCH, 4) if cx else None,
                "height_inches": round(cy / EMU_PER_INCH, 4) if cy else None,
            },
            "parent_paragraph_index": parent_index,
        })
    return result


def field_items(p: etree._Element, section: int, parent_index: int) -> list[dict[str, Any]]:
    result = []
    for fld in p.xpath(".//w:fldSimple | .//w:fldChar[@w:fldCharType='begin']", namespaces=NS):
        if local_name(fld.tag) == "fldSimple":
            instruction = fld.get(f"{{{W_NS}}}instr", "")
        else:
            instruction = ""
            for node in fld.xpath("following-sibling::w:instrText[1] | ancestor::w:r/following-sibling::w:r/w:instrText[1]", namespaces=NS):
                instruction = clean_text(node.text or "")
                if instruction:
                    break
        result.append({
            "type": "field",
            "style_name": style_name(p, {}),
            "section": section,
            "text_preview": preview(instruction),
            "field": {"instruction": instruction or None},
            "parent_paragraph_index": parent_index,
        })
    return result


def heading_level(style: str | None, text: str) -> int | None:
    if style:
        m = re.search(r"heading\s*([1-9])", style, flags=re.I)
        if m:
            return int(m.group(1))
    if re.match(r"^(?:[A-Z](?:\.[0-9]+)*|[A-Z]+\.)\s+", text):
        return 1
    return None


def classify(item: dict[str, Any]) -> tuple[str, str | None]:
    typ = item["type"]
    text = item.get("text", item.get("text_preview", ""))
    low = text.lower()
    if typ == "image":
        return "IMAGE", None
    if typ == "table":
        return "TABLE", None
    if typ == "section_break":
        return "FIXED", None
    if typ == "field":
        instr = (item.get("field") or {}).get("instruction", "") or ""
        return ("COMPUTED" if any(x in instr.upper() for x in ("PAGE", "NUMPAGES", "TOC", "PAGEREF", "SEQ")) else "FIXED"), None
    if typ == "paragraph":
        p_no = item.get("paragraph", {}).get("number")
        style = (item.get("style_name") or "").lower()
        if (("b.3" in low and "structural system and foundation" in low)
                or ("f.7" in low and "design of foundations" in low)
                or (style.startswith("toc") and any(x in low for x in (
                    "soft storey", "in-plane discontinuity", "mass irregularity",
                    "re-entrant corner", "diaphragm discontinuity", "out-of-plane offset")))):
            return "FIXED", None
        if "f.8" in low and "design of staircases" in low:
            return "FIXED", None
        if p_no == 161 or "support condition" in low:
            return "FIXED", None
        if p_no == 162 or ("foundation is assumed to be fixed" in low and "less firm" in low):
            return "COMPUTED", None
        if ("foundation reaction" in low or low.startswith("figure 27:")
                or low.startswith("figure 28:") or low.startswith("figure 29:")):
            return "IMAGE", None
        if (low.startswith("no soft stoy") or low.startswith("no soft story")
                or low.startswith("no in-plane discontinuity")
                or low.startswith("no mass irregularity")
                or low.startswith("the building is rectangular")):
            return "COMPUTED", None
        if any(x in low for x in ("as per the clause 5.5.1.2", "as per the clause 5.5.1.4",
                                  "clause 5.5.1.5", "clause 5.5.2.2", "clause 5.5.2.3", "clause 5.5.2.4")):
            return "FIXED", None
        if "system and present the same in tabular form" in low:
            return "FIXED", None
    if heading_level(item.get("style_name"), text):
        return "FIXED", None
    conditional_terms = ("basement", "staircase", "soft storey", "soft story", "in-plane discontinuity",
                         "mass irregularity", "re-entrant", "out-of-plane offset", "foundation")
    if any(term in low for term in conditional_terms):
        return "CONDITIONAL", "The text mentions a condition-specific building element or check; confirm whether it should be included by project configuration."
    computed_terms = ("base shear", "drift ratio", "fundamental time period", "rayleigh", "torsional ratio",
                      "pass", "failed", "compliant", "separation between blocks", "calculated")
    if any(term in low for term in computed_terms):
        return "COMPUTED", None
    variable_terms = ("chatra bahadur", "damak", "residential", "owner", "designer", "consult", "registration",
                      "contact number", "application no", "date of application", "number of story", "height of",
                      "span of", "m20", "m25", "fe 415", "fe500", "fe 500", "kn /m", "meters", "metres",
                      "etabs 19", "355", "430", "150 mm", "125 mm", "120 kn")
    if any(term in low for term in variable_terms) or re.search(r"\b\d+(?:\.\d+)?\s*(?:m|mm|kn|mpa|%|meters?|metres?)\b", low):
        return "VARIABLE", None
    return "FIXED", None


def apply_template_rule(item: dict[str, Any]) -> None:
    """Attach deterministic rules supplied by the template owner."""
    text = item.get("text", item.get("text_preview", ""))
    low = text.lower()
    p_no = item.get("paragraph", {}).get("number")
    if item["type"] == "table" and item.get("table", {}).get("number") == 3:
        item["template_rule"] = {
            "action": "fill_rows",
            "source": ["excel", "computed"],
            "note": "Fill rows from intake and the Phase 2.5 foundation choice; preserve the SEQ field.",
            "seq_field": "preserve",
        }
    elif item["type"] == "table" and item.get("table", {}).get("number") == 5:
        item["template_rule"] = {
            "action": "fill_value_column",
            "classification": "TABLE",
            "shape": {"rows": 3, "columns": 3},
            "columns": {
                "code": "fixed",
                "parameter": "fixed",
                "value": "project_data",
            },
            "rows": [
                {"code": "A.3-01", "parameter": "Type of Structural System", "value_key": "structural.system_type", "source": "excel", "note": "Also drives Rμ/Ωu/Ωs."},
                {"code": "A.3-02", "parameter": "Type of Foundation", "value_key": "foundation.type", "source": "computed", "note": "Phase 2.5 choice from column loads, q_a, and boundary answer."},
                {"code": "A.3-03", "parameter": "Type of Slab used", "value_key": "slab.type", "source": ["excel", "e2k"], "note": "A flat slab or waffle slab may be identified from .e2k shell sections."},
            ],
        }
    elif item["type"] == "paragraph" and "f.8" in low and "design of staircases" in low:
        item["template_rule"] = {
            "action": "conditional_section",
            "condition": "building.has_staircase",
            "when_false": "remove_heading_and_content_until_empty_heading_5",
            "source_body_indices": [370, 371, 372, 373, 374],
            "inventory_items_to_remove_in_sample": [516, 518, 520, 522, 523],
            "next_section_inventory_item": 530,
        }
    elif item["type"] == "paragraph" and "b.3" in low and "structural system and foundation" in low:
        item["template_rule"] = {"action": "toc_entry", "always_present": True, "target_heading_text": "Structural System and Foundation"}
    elif item["type"] == "paragraph" and "f.7" in low and "design of foundations" in low:
        item["template_rule"] = {"action": "toc_entry", "always_present": True, "target_heading_text": "Design of Foundations"}
    elif item["type"] == "paragraph" and (item.get("style_name") or "").lower().startswith("toc") and any(x in low for x in ("soft storey", "in-plane discontinuity", "mass irregularity", "re-entrant corner", "diaphragm discontinuity", "out-of-plane offset")):
        item["template_rule"] = {"action": "toc_entry", "always_present": True, "generated_heading": True}
    elif item["type"] == "paragraph" and p_no == 161:
        item["template_rule"] = {"action": "replace_text", "remove_designer_instruction_sentence": True, "preserve_support_condition_rule": True}
    elif item["type"] == "paragraph" and p_no == 162:
        item["template_rule"] = {
            "action": "computed_variant",
            "inputs": ["foundation.type", "foundation.soil_class"],
            "variants": {"fixed": "the foundation is assumed to be fixed.", "pinned": "the foundation is assumed to be pinned."},
        }
    elif item["type"] == "paragraph" and ("foundation reaction" in low or low.startswith("figure 27:") or low.startswith("figure 28:") or low.startswith("figure 29:")):
        item["template_rule"] = {"action": "retain_image_or_caption", "caption_combination_variable": "analysis.foundation_reaction_combination"}
    elif item["type"] == "paragraph" and "no soft stoy" in low:
        item["template_rule"] = {"action": "computed_variant", "variant_key": "soft_storey_result", "variants": ["present", "not_present"]}
    elif item["type"] == "paragraph" and "no in-plane discontinuity" in low:
        item["template_rule"] = {"action": "computed_variant", "style_override": "Body Text", "variant_key": "in_plane_discontinuity_result", "variants": ["present", "not_present"]}
    elif item["type"] == "paragraph" and "no mass irregularity" in low:
        item["template_rule"] = {"action": "computed_variant", "style_override": "Body Text", "variant_key": "mass_irregularity_result", "variants": ["present", "not_present"]}
    elif item["type"] == "paragraph" and low.startswith("the building is rectangular"):
        item["template_rule"] = {"action": "computed_variant", "variant_key": "reentrant_corner_result", "variants": ["reentrant_present", "rectangular_no_reentrant_corners"]}
    elif item["type"] == "paragraph" and "clause 5.5.1.2" in low:
        item["template_rule"] = {"action": "clause_variable", "clause_key": "code.clauses.soft_storey", "sample_clause": "5.5.1.2", "target_clause_2025": "5.4.1.2", "edition_key": "code.edition", "insert_code_name_if_missing": True}
    elif item["type"] == "paragraph" and "clause 5.5.1.4" in low:
        item["template_rule"] = {"action": "clause_variable", "clause_key": "code.clauses.in_plane_discontinuity", "sample_clause": "5.5.1.4", "target_clause_2025": "5.4.1.4", "edition_key": "code.edition"}
    elif item["type"] == "paragraph" and "clause 5.5.1.5" in low:
        item["template_rule"] = {"action": "clause_variable", "clause_key": "code.clauses.mass_irregularity", "sample_clause": "5.5.1.5", "target_clause_2025": "5.4.1.5", "edition_key": "code.edition"}
    elif item["type"] == "paragraph" and "clause 5.5.2.2" in low:
        item["template_rule"] = {"action": "clause_variable", "clause_key": "code.clauses.reentrant_corner", "sample_clause": "5.5.2.2", "target_clause_2025": "5.4.2.3", "edition_key": "code.edition"}
    elif item["type"] == "paragraph" and "clause 5.5.2.3" in low:
        item["template_rule"] = {"action": "clause_variable", "clause_key": "code.clauses.diaphragm_discontinuity", "sample_clause": "5.5.2.3", "target_clause_2025": "5.4.2.4", "edition_key": "code.edition"}
    elif item["type"] == "paragraph" and "clause 5.5.2.4" in low:
        item["template_rule"] = {"action": "clause_variable", "clause_key": "code.clauses.out_of_plane_offset", "sample_clause": "5.5.2.4", "target_clause_2025": "5.4.2.5", "edition_key": "code.edition"}
    elif item["type"] == "paragraph" and "system and present the same in tabular form" in low:
        item["template_rule"] = {"action": "drop_sentence", "note": "Drop the designer instruction sentence; merge the preceding mass-irregularity definition."}


def slug(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "item"


def registry_key(item: dict[str, Any], used: defaultdict[str, int]) -> str:
    text = item.get("text_preview", "")
    low = text.lower()
    if item["type"] == "image":
        base = "figure.image"
    elif item["type"] == "table":
        base = "table.generated"
    elif "seismic" in low or "earthquake" in low:
        base = "seismic.parameters"
    elif "story" in low or "storey" in low:
        base = "building.story_data"
    elif any(x in low for x in ("owner", "designer", "client", "consult", "address", "contact")):
        base = "project.contact_data"
    elif any(x in low for x in ("material", "concrete", "steel", "rebar")):
        base = "materials.properties"
    elif any(x in low for x in ("load", "dead", "live")):
        base = "loading.parameters"
    elif item["classification"] == "COMPUTED":
        base = "analysis.computed_result"
    elif item["classification"] == "CONDITIONAL":
        base = "scope.conditional_section"
    else:
        base = "project.variable_text"
    used[base] += 1
    return f"{base}_{used[base]}"


def infer_registry_fields(item: dict[str, Any], key: str) -> dict[str, Any]:
    text = item.get("text_preview", "")
    low = text.lower()
    cls = item["classification"]
    typ = item["type"]
    if typ == "image":
        value_type, source, unit = "image", "excel", None
    elif typ == "table":
        value_type, source, unit = "table", "etabs_api", None
    elif cls == "COMPUTED":
        value_type, source, unit = ("number", "computed", "ratio" if "ratio" in low else None)
    elif any(x in low for x in ("number of", "height", "span", "grade", "capacity", "factor", "date")):
        value_type, source, unit = "number", "excel", None
    else:
        value_type, source, unit = "text", "excel", None
    if "drift" in low:
        unit = "ratio"
    elif any(x in low for x in ("height", "span", "meters", "metres")):
        unit = "m"
    elif "kn" in low:
        unit = "kN"
    example = item.get("text_preview") or item.get("image", {}).get("alt_text") or item.get("table", {}).get("header_row")
    return {
        "key": key,
        "description": text or f"Generated item {item['index']}",
        "type": value_type,
        "unit": unit,
        "source": source,
        "required": cls in {"VARIABLE", "COMPUTED"},
        "example": example,
    }


def make_item_base(index: int, typ: str, style: str | None, section: int, text: str) -> dict[str, Any]:
    return {"index": index, "type": typ, "style_name": style, "section": section,
            "text": text, "text_preview": preview(text)}


def inventory_docx(path: Path) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input DOCX does not exist: {path}")
    with ZipFile(path) as z:
        if "word/document.xml" not in z.namelist():
            raise ValueError("The DOCX has no word/document.xml part")
        root = etree.fromstring(z.read("word/document.xml"))
        styles = load_styles(z)
        rels = relationship_targets(z)
        body = root.find(f"{{{W_NS}}}body")
        if body is None:
            raise ValueError("word/document.xml has no w:body")
        items: list[dict[str, Any]] = []
        section = 1
        paragraph_no = 0
        table_no = 0
        image_no = 0
        decision_notes: list[str] = []

        def append(item: dict[str, Any]) -> None:
            nonlocal image_no, table_no
            item["index"] = len(items)
            if item["type"] == "table":
                table_no += 1
                item["table"]["number"] = table_no
            if item["type"] == "image":
                image_no += 1
                item["image"]["number"] = image_no
            cls, note = classify(item)
            item["classification"] = cls
            apply_template_rule(item)
            if note and item.get("text_preview"):
                decision_notes.append(f"- **Item {item['index']} ({cls})**: {item['text_preview']}\n  - Suggestion: {note}")
            items.append(item)

        for child in body:
            tag = local_name(child.tag)
            if tag == "p":
                paragraph_no += 1
                p_style = style_name(child, styles)
                text = paragraph_text(child)
                p_item = make_item_base(len(items), "paragraph", p_style, section, text)
                p_item["paragraph"] = {"number": paragraph_no, "heading_level": heading_level(p_style, text)}
                append(p_item)
                parent_index = p_item["index"]
                image_events = image_items(child, rels, section, parent_index)
                field_events = field_items(child, section, parent_index)
                image_pos = 0
                field_pos = 0
                for node in child.iter():
                    if local_name(node.tag) == "drawing":
                        if image_pos < len(image_events):
                            append(image_events[image_pos])
                            image_pos += 1
                    elif local_name(node.tag) == "fldSimple" or (
                        local_name(node.tag) == "fldChar" and node.get(f"{{{W_NS}}}fldCharType") == "begin"
                    ):
                        if field_pos < len(field_events):
                            nested = field_events[field_pos]
                            field_pos += 1
                        else:
                            continue
                        nested["style_name"] = p_style
                        append(nested)
                if child.xpath("./w:pPr/w:sectPr", namespaces=NS):
                    append({
                        "type": "section_break",
                        "style_name": p_style,
                        "section": section,
                        "text_preview": "Section break",
                        "section_break": {"kind": "paragraph_section_properties", "paragraph_number": paragraph_no},
                    })
                    section += 1
            elif tag == "tbl":
                rows, cols, header = table_info(child)
                item = make_item_base(len(items), "table", None, section, " | ".join(header))
                item["table"] = {"rows": rows, "columns": cols, "header_row": header}
                append(item)
            elif tag == "sectPr":
                append({
                    "type": "section_break",
                    "style_name": None,
                    "section": section,
                    "text_preview": "Section break",
                    "section_break": {"kind": "body_section_properties"},
                })
                section += 1
            else:
                append(make_item_base(len(items), tag, None, section, clean_text("".join(child.itertext()))))

        stats = {"paragraphs": paragraph_no, "tables": table_no, "images": image_no, "sections": section - 1,
                 "items": len(items)}
        return items, decision_notes, stats


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{text}"'


def write_yaml_registry(path: Path, entries: list[dict[str, Any]]) -> None:
    lines = ["# Generated by tools/inventory_template.py", "# One entry per non-FIXED inventory item.", "items:"]
    for entry in entries:
        lines.append("  -")
        for key in ("key", "description", "type", "unit", "source", "required", "example"):
            lines.append(f"    {key}: {yaml_scalar(entry.get(key))}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown(path: Path, items: list[dict[str, Any]], stats: dict[str, Any]) -> None:
    lines = ["# DOCX Template Inventory", "", f"Generated by `tools/inventory_template.py`. Items: {stats['items']}; paragraphs: {stats['paragraphs']}; tables: {stats['tables']}; images: {stats['images']}; sections: {stats['sections']}.", ""]
    current_heading = None
    def rule_text(item: dict[str, Any]) -> str:
        rule = item.get("template_rule")
        return f"; rule `{json.dumps(rule, ensure_ascii=False, sort_keys=True)}`" if rule else ""

    for item in items:
        if item["type"] == "paragraph" and item.get("paragraph", {}).get("heading_level"):
            current_heading = item["text_preview"] or "(blank heading)"
            lines.append(f"\n### {current_heading}")
        if item["type"] == "table":
            t = item["table"]
            lines.append(f"- **Item {item['index']} — Table {t['number']}** ({t['rows']} rows × {t['columns']} columns; section {item['section']}; classification `{item['classification']}`{rule_text(item)})")
            lines.append(f"  - Header row: {', '.join(t['header_row']) if t['header_row'] else '(none detected)'}")
        elif item["type"] == "image":
            im = item["image"]
            cap = im.get("alt_text") or im.get("title") or item.get("text_preview") or "(no alt text/caption detected)"
            lines.append(f"- **Item {item['index']} — Image {im['number']}** ({im.get('width_inches')} × {im.get('height_inches')} in; section {item['section']}; classification `{item['classification']}`{rule_text(item)}): {cap}")
        elif item["type"] == "section_break":
            lines.append(f"- **Item {item['index']} — Section break** (section {item['section']})")
        elif item["type"] == "field":
            lines.append(f"- **Item {item['index']} — Word field** `{item.get('field', {}).get('instruction') or '(field code not exposed)'}`; classification `{item['classification']}`{rule_text(item)}")
        elif item["type"] == "paragraph" and item["text_preview"]:
            lines.append(f"- Item {item['index']} — `{item.get('style_name') or 'unstyled'}` — `{item['classification']}`{rule_text(item)}: {item['text_preview']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decisions(path: Path, notes: list[str], items: list[dict[str, Any]]) -> None:
    lines = ["# Needs My Decision", "", "This file records heuristic classifications that should be confirmed before a production placeholder map is implemented.", ""]
    if notes:
        lines.extend(notes)
    else:
        lines.append("No conditional/ambiguous text was detected by the current heuristics.")
    lines += [
        "",
        "## Applied owner decisions",
        "",
        "- TOC entries for B.3, F.7, and the irregularity checks are `FIXED`; F.8 is fixed but controlled by `building.has_staircase`.",
        "- When `has_staircase` is false, remove the staircase heading and the sample content range through the empty Heading 5; do not alter the DOCX during inventory.",
        "- Foundation support wording is computed from `foundation.type` and `foundation.soil_class`.",
        "- Clause citations are variables: the sample 2020 clauses map to NBC 105:2025 §5.4 clauses recorded in the registry.",
        "- In-plane and mass-irregularity conclusion paragraphs are computed variants and restyled to Body Text; the re-entrant conclusion has rectangular/no-re-entrant variants.",
        "- The foundation reaction image is retained; only its combination text is variable.",
        "",
        "## Classification policy",
        "",
        "The tool classifies headings and general method/boilerplate as `FIXED`, project facts as `VARIABLE`, data-driven tables as `TABLE`, replacement figures as `IMAGE`, derived results as `COMPUTED`, and condition-specific content as `CONDITIONAL`. Review all non-FIXED items before using the registry to drive report generation.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def owner_registry_entries() -> list[dict[str, Any]]:
    """Stable variables explicitly requested by the template owner."""
    specs = [
        ("code.edition", "Code edition used in clause citations.", "text", None, "excel", True, "NBC 105:2025"),
        ("code.clauses.soft_storey", "NBC clause for the soft-storey check.", "text", None, "excel", True, "5.4.1.2"),
        ("code.clauses.in_plane_discontinuity", "NBC clause for the in-plane discontinuity check.", "text", None, "excel", True, "5.4.1.4"),
        ("code.clauses.mass_irregularity", "NBC clause for the mass-irregularity check.", "text", None, "excel", True, "5.4.1.5"),
        ("code.clauses.reentrant_corner", "NBC clause for the re-entrant-corner check.", "text", None, "excel", True, "5.4.2.3"),
        ("code.clauses.diaphragm_discontinuity", "NBC clause for the diaphragm-discontinuity check.", "text", None, "excel", True, "5.4.2.4"),
        ("code.clauses.out_of_plane_offset", "NBC clause for the out-of-plane-offset check.", "text", None, "excel", True, "5.4.2.5"),
        ("building.has_staircase", "Whether the project includes a staircase section.", "bool", None, "excel", True, True),
        ("foundation.type", "Foundation type chosen in Phase 2.5 from column loads, q_a, and the boundary answer.", "text", None, "computed", True, "Combined Footing"),
        ("foundation.soil_class", "Soil class/firmness used for the support-condition wording.", "text", None, "excel", True, "firm soil"),
        ("foundation.support_condition", "Computed fixed or pinned support-condition wording.", "text", None, "computed", True, "fixed"),
        ("structural.system_type", "Structural system type shown in Table 5; also drives Rμ/Ωu/Ωs.", "text", None, "excel", True, "Moment Resisting Frames"),
        ("slab.type", "Slab type shown in Table 5; may be supplied by intake or identified from .e2k shell sections.", "text", None, "excel", True, "Conventional"),
        ("analysis.foundation_reaction_combination", "Combination text shown in the retained foundation-reaction caption.", "text", None, "etabs_api", False, "1.5DL+1.5LL"),
        ("analysis.soft_storey_result", "Computed soft-storey conclusion variant.", "text", None, "computed", True, "not_present"),
        ("analysis.in_plane_discontinuity_result", "Computed in-plane-discontinuity conclusion variant.", "text", None, "computed", True, "not_present"),
        ("analysis.mass_irregularity_result", "Computed mass-irregularity conclusion variant.", "text", None, "computed", True, "not_present"),
        ("analysis.reentrant_corner_result", "Computed re-entrant-corner conclusion variant.", "text", None, "computed", True, "rectangular_no_reentrant_corners"),
    ]
    return [{"key": key, "description": description, "type": typ, "unit": unit,
             "source": source, "required": required, "example": example}
            for key, description, typ, unit, source, required, example in specs]


def main() -> int:
    args = parse_args()
    outputs = [args.json, args.markdown, args.registry, args.decisions]
    existing = [path for path in outputs if path.exists()]
    if existing and not args.force:
        print("[ERROR] Refusing to overwrite existing output(s): " + ", ".join(map(str, existing)) + ". Use --force to replace them.", file=sys.stderr)
        return 2
    try:
        items, decisions, stats = inventory_docx(args.input)
    except (OSError, ValueError, etree.XMLSyntaxError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    used: defaultdict[str, int] = defaultdict(int)
    registry = []
    for item in items:
        if item["classification"] != "FIXED":
            key = registry_key(item, used)
            registry.append(infer_registry_fields(item, key))
    registry.extend(owner_registry_entries())
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps({"source": str(args.input), "statistics": stats, "items": items}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(args.markdown, items, stats)
    write_yaml_registry(args.registry, registry)
    write_decisions(args.decisions, decisions, items)
    print(f"[OK] Inventory: {args.json} ({len(items)} items)")
    print(f"[OK] Outline: {args.markdown}")
    print(f"[OK] Registry: {args.registry} ({len(registry)} entries)")
    print(f"[OK] Decisions: {args.decisions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
