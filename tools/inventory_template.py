#!/usr/bin/env python3
"""Inventory a DOCX template in document order without modifying the input file.

The inventory walks ``word/document.xml`` body children and nested paragraph
content so paragraphs, tables, images, section breaks, and fields are visible
as separate items. It writes JSON, Markdown, a non-destructive registry candidate, and a review log.

Example:
    python tools/inventory_template.py \
        --input "Chatra Bahadur Ramtel.docx" \
        --json docs/template_inventory.json \
        --markdown docs/template_inventory.md \
        --registry config/placeholder_registry.yaml \
        --decisions docs/needs_my_decision.generated.md \
        --review docs/registry_review.md
"""

from __future__ import annotations

import argparse
import difflib
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
    p.add_argument("--registry", type=Path, default=Path("config/placeholder_registry.yaml"))
    p.add_argument("--curated-registry", type=Path, default=Path("config/placeholder_registry.yaml"),
                   help="curated registry used only for a concise generated-vs-curated diff")
    p.add_argument("--decisions", type=Path, default=Path("docs/needs_my_decision.generated.md"))
    p.add_argument("--review", type=Path, default=Path("docs/registry_review_full.md"),
                   help="full before/after listing; the short curated summary lives at docs/registry_review.md and is not overwritten by this tool")
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
    """Attach deterministic rules supplied by the template owner.

    Rules are loaded from ``config/template_rules.yaml`` (see
    :func:`load_template_rules`). Matching is text/heading-anchored so
    editing the sample DOCX cannot silently break a rule; if any rule
    matches zero items, :func:`verify_template_rules` raises a loud error
    after the inventory pass.
    """
    text = item.get("text", item.get("text_preview", "")) or ""
    low = text.lower()
    style = (item.get("style_name") or "").lower()
    context = item.get("context") or {}
    heading = (context.get("section_heading") or "").lower()
    caption = (context.get("caption") or "").lower()
    table = item.get("table") or {}
    table_headers = [str(h or "").lower() for h in table.get("header_row", [])]
    for rule in _TEMPLATE_RULES:
        match = rule.get("match") or {}
        if not _rule_matches(item, match, low, style, heading, caption, table, table_headers):
            continue
        action = rule.get("action") or {}
        # Replace any prior template_rule so the most specific match wins
        # (rules are ordered most-specific first in the YAML).
        item["template_rule"] = dict(action)
        item["template_rule_id"] = rule.get("id")
        # Count distinct (rule_id, item_index) pairs so the same item being
        # processed twice (inventory_docx + prepare_inventory) does not
        # inflate the match count.
        pair = (rule.get("id"), item.get("index"))
        if pair not in _RULE_MATCHED_ITEMS:
            _RULE_MATCHED_ITEMS.add(pair)
            _RULE_MATCH_COUNTS[rule.get("id")] += 1
        return


_TEMPLATE_RULES: list[dict[str, Any]] = []
_RULE_MATCH_COUNTS: dict[str | None, int] = defaultdict(int)
_RULE_MATCHED_ITEMS: set[tuple[str | None, int | None]] = set()
_TEMPLATE_RULES_LOADED = False


def load_template_rules(path: Path | None = None) -> list[dict[str, Any]]:
    """Load and cache the heading/text-anchored rules from config/template_rules.yaml."""
    global _TEMPLATE_RULES, _TEMPLATE_RULES_LOADED
    if _TEMPLATE_RULES_LOADED:
        return _TEMPLATE_RULES
    if path is None:
        path = Path(__file__).resolve().parent.parent / "config" / "template_rules.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"Template rules file not found: {path}. The inventory tool refuses to run "
            "without the anchored rules; create the file or restore it from git."
        )
    try:
        import yaml as _yaml  # local import so module import stays light
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to load config/template_rules.yaml") from exc
    data = _yaml.safe_load(path.read_text(encoding="utf-8"))
    rules = data.get("rules") if isinstance(data, dict) else None
    if not isinstance(rules, list) or not rules:
        raise ValueError(f"{path} must contain a non-empty 'rules' list.")
    for rule in rules:
        if not rule.get("id"):
            raise ValueError(f"Every rule in {path} must have an 'id'.")
        if not isinstance(rule.get("match"), dict):
            raise ValueError(f"Rule {rule.get('id')} must have a 'match' mapping.")
        if not isinstance(rule.get("action"), dict):
            raise ValueError(f"Rule {rule.get('id')} must have an 'action' mapping.")
    _TEMPLATE_RULES = rules
    _TEMPLATE_RULES_LOADED = True
    return rules


def reset_template_rule_state() -> None:
    """Reset the loaded rules and match counters (used by tests)."""
    global _TEMPLATE_RULES, _TEMPLATE_RULES_LOADED
    _TEMPLATE_RULES = []
    _TEMPLATE_RULES_LOADED = False
    _RULE_MATCH_COUNTS.clear()
    _RULE_MATCHED_ITEMS.clear()


def _rule_matches(item: dict[str, Any], match: dict[str, Any], low: str, style: str,
                  heading: str, caption: str, table: dict[str, Any],
                  table_headers: list[str]) -> bool:
    typ = item.get("type")
    if "item_type" in match and typ != match["item_type"]:
        return False
    if "style_prefix" in match and not style.startswith(match["style_prefix"].lower()):
        return False
    # Strip leading literal "\t" tab markers (added by paragraph_text) and
    # whitespace so a heading that begins with a tab still matches a
    # paragraph_starts_with rule. The literal "\t" is two characters
    # (backslash + t); match it as a sequence, not as a character class.
    low_stripped = re.sub(r"^(?:\\t|\s)+", "", low)
    if "paragraph_starts_with" in match and not low_stripped.startswith(match["paragraph_starts_with"].lower()):
        return False
    if "paragraph_starts_with_any" in match:
        opts = [opt.lower() for opt in match["paragraph_starts_with_any"]]
        if not any(low_stripped.startswith(opt) for opt in opts):
            return False
    if "paragraph_contains" in match and match["paragraph_contains"].lower() not in low:
        return False
    if "paragraph_contains_any" in match:
        opts = [opt.lower() for opt in match["paragraph_contains_any"]]
        if not any(opt in low for opt in opts):
            return False
    if "heading_contains" in match and match["heading_contains"].lower() not in heading:
        return False
    if "table_caption_contains" in match:
        if match["table_caption_contains"].lower() not in caption:
            return False
    if "table_header_contains" in match:
        needle = match["table_header_contains"].lower()
        if not any(needle in h for h in table_headers):
            return False
    if "table_number" in match and table.get("number") != match["table_number"]:
        return False
    return True


def verify_template_rules() -> None:
    """Fail loudly if any anchored rule matched zero items in the last pass."""
    missing = [rid for rid, count in _RULE_MATCH_COUNTS.items() if count == 0]
    # Also include rules that never had a counter entry (loaded but unmatched).
    for rule in _TEMPLATE_RULES:
        rid = rule.get("id")
        if rid not in _RULE_MATCH_COUNTS:
            missing.append(rid)
    if missing:
        raise RuntimeError(
            "Template rules matched no inventory items: "
            + ", ".join(sorted(r for r in missing if r))
            + ". The sample DOCX has changed in a way that breaks anchored matching; "
            "update config/template_rules.yaml or restore the sample."
        )


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
            lines.append(f"- **Item {item['index']} — Word field** `{item.get('field', {}).get('instruction') or '(field code not exposed)'}`; classification `{item['classification']}`; regenerated by Word and excluded from the value registry{rule_text(item)}")
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
    """Stable variables explicitly requested by the template owner.

    All clause keys live under the `codes.*` group; the singular `code.*`
    prefix has been merged into `codes.*` per the registry review gate.
    """
    specs = [
        ("codes.edition", "Code edition used in clause citations.", "text", None, "excel", True, "NBC 105:2025"),
        ("codes.clauses.soft_storey", "NBC clause for the soft-storey check.", "text", None, "excel", True, "5.4.1.2"),
        ("codes.clauses.in_plane_discontinuity", "NBC clause for the in-plane discontinuity check.", "text", None, "excel", True, "5.4.1.4"),
        ("codes.clauses.mass_irregularity", "NBC clause for the mass-irregularity check.", "text", None, "excel", True, "5.4.1.5"),
        ("codes.clauses.reentrant_corner", "NBC clause for the re-entrant-corner check.", "text", None, "excel", True, "5.4.2.3"),
        ("codes.clauses.diaphragm_discontinuity", "NBC clause for the diaphragm-discontinuity check.", "text", None, "excel", True, "5.4.2.4"),
        ("codes.clauses.out_of_plane_offset", "NBC clause for the out-of-plane-offset check.", "text", None, "excel", True, "5.4.2.5"),
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


WORD_REGENERATED_FIELDS = {"TOC", "PAGEREF", "PAGE", "NUMPAGES", "HYPERLINK", "SEQ", "REF", "STYLEREF"}
# Owner clause map: sample 2020 clause -> (codes.clauses.* registry key, 2025 target).
# All clause keys live under the `codes.*` group; the singular `code.*` prefix
# has been merged into `codes.*` per the registry review gate.
# All 11 clauses below are owner-approved; there are no unresolved clauses.
OWNER_CLAUSE_MAP = {
    "5.5.1.2": ("codes.clauses.soft_storey", "5.4.1.2"),
    "5.5.1.4": ("codes.clauses.in_plane_discontinuity", "5.4.1.4"),
    "5.5.1.5": ("codes.clauses.mass_irregularity", "5.4.1.5"),
    "5.5.2.2": ("codes.clauses.reentrant_corner", "5.4.2.3"),
    "5.5.2.3": ("codes.clauses.diaphragm_discontinuity", "5.4.2.4"),
    "5.5.2.4": ("codes.clauses.out_of_plane_offset", "5.4.2.5"),
    # Final Phase 1 decisions — previously unresolved, now owner-approved.
    "2.1": ("codes.clauses.material_properties", "Annex A, Cl. 2.1"),
    "3.6.1": ("codes.clauses.load_combinations", "3.6.1"),
    "5.5": ("codes.clauses.irregularity_general", "5.4"),
    "5.5.2.1": ("codes.clauses.torsional_irregularity", "5.4.2.1"),
    "5.6.3": ("codes.clauses.serviceability_drift", "5.5.3"),
}
UNRESOLVED_CLAUSE_KEYS: dict[str, tuple[str, str]] = {}
CURRENT_CLAUSE_KEYS = {
    "3.2.1": "codes.clauses.equivalent_static_method",
    "4.1.2": "codes.clauses.spectral_shape_factor",
    "4.1.4": "codes.clauses.seismic_zoning_factor",
    "4.1.5": "codes.clauses.importance_factor",
    "6.3": "codes.clauses.vertical_force_distribution",
    "3.6.1": "codes.clauses.load_combinations",
    "7.3": "codes.clauses.modal_mass_participation",
}


def word_field_kind(instruction: str) -> str:
    match = re.match(r"\s*([A-Za-z]+)", instruction or "")
    return match.group(1).upper() if match else "UNKNOWN"


def field_items(p: etree._Element, section: int, parent_index: int) -> list[dict[str, Any]]:
    """Return simple and complex Word fields with their field instructions."""
    result: list[dict[str, Any]] = []
    nodes = list(p.iter())
    for pos, node in enumerate(nodes):
        name = local_name(node.tag)
        if name == "fldSimple":
            instruction = clean_text(node.get(f"{{{W_NS}}}instr", ""))
        elif name == "fldChar" and node.get(f"{{{W_NS}}}fldCharType") == "begin":
            instructions: list[str] = []
            for following in nodes[pos + 1:]:
                if local_name(following.tag) == "fldChar" and following.get(f"{{{W_NS}}}fldCharType") in {"begin", "end"}:
                    break
                if local_name(following.tag) == "instrText":
                    instructions.append(following.text or "")
            instruction = clean_text("".join(instructions))
        else:
            continue
        result.append({
            "type": "field", "style_name": None, "section": section,
            "text_preview": preview(instruction),
            "field": {"instruction": instruction or None, "kind": word_field_kind(instruction)},
            "parent_paragraph_index": parent_index,
        })
    return result


def classify(item: dict[str, Any]) -> tuple[str, str | None]:
    """Conservative classification; Word fields remain inventory-only metadata."""
    typ = item.get("type")
    text = item.get("text", item.get("text_preview", "")) or ""
    low = text.lower()
    if typ == "image":
        return "IMAGE", None
    if typ == "table":
        return "TABLE", None
    if typ == "section_break":
        return "FIXED", None
    if typ == "field":
        return "COMPUTED", "Regenerated by Word; excluded from the value registry."
    if typ != "paragraph":
        return "FIXED", None

    style = (item.get("style_name") or "").lower()
    context = item.get("context") or {}
    previous = (context.get("preceding_text") or "").lower()
    # TOC text is fixed; page numbers and field results are regenerated by Word.
    if style.startswith("toc"):
        return "FIXED", None
    if style == "caption" and "foundation reaction" not in low:
        if re.search(r"NBC\s*105\s*:\s*\d{4}|\bdamak\b", low):
            return "VARIABLE", None
        return "FIXED", None
    if text.strip().endswith(":") and not re.search(r"\d", text):
        return "FIXED", None
    if "structural design consultant:" in previous or "consultant:" in previous:
        return "VARIABLE", None
    if ("b.3" in low and "structural system and foundation" in low) or (
        "f.7" in low and "design of foundations" in low
    ):
        return "FIXED", None
    if "f.8" in low and "design of staircases" in low:
        return "FIXED", None
    if "support condition" in low and "foundation is assumed" not in low:
        return "FIXED", None
    if "foundation is assumed to be fixed" in low or "foundation is assumed to be pinned" in low:
        return "COMPUTED", None
    if "foundation reaction" in low:
        return "VARIABLE", None
    if low.startswith("no soft stoy") or low.startswith("no soft story") or low.startswith(
        ("no in-plane discontinuity", "no mass irregularity", "the building is rectangular")
    ):
        return "COMPUTED", None

    # Keep the owner's established conditional section choices intact.
    if low.strip().startswith("table 3:") and "structural system" in low and "foundation" in low:
        return "CONDITIONAL", "Include this section/table only when its configured content applies."
    if "the building was modeled using" in low and "etabs" in low:
        return "CONDITIONAL", "The software/version narrative is project-specific and may be omitted."

    # Old code citations must be variables even when the surrounding prose is fixed.
    clause_citation = re.search(r"(?:nbc\s*105\s*:\s*\d{4}|\bcl(?:ause)?\.?\s*\d+(?:\.\d+)+)", low)
    if clause_citation:
        return "VARIABLE", "Clause edition/number requires the owner-approved mapping."

    heading = heading_level(item.get("style_name"), text)
    if heading:
        return "FIXED", None
    section_text = ((context.get("section_heading") or "") + " " + previous).lower()
    if any(term in low for term in ("soft storey", "soft story", "in-plane discontinuity", "mass irregularity",
                                    "re-entrant", "out-of-plane offset", "staircase", "basement")):
        return "CONDITIONAL", "Confirm applicability from the project configuration and owner decisions."

    numerical_pattern = re.search(
        r"\b\d+(?:\.\d+)?\s*(?:%|mm\b|cm\b|m\b|meters?\b|metres?\b|kn\b|kn/m\s*\^?\s*2|mpa\b|sec(?:ond)?s?\b|s\b)",
        low,
    )
    assignment_pattern = re.search(r"\b(?:k|t|cd|z|i|r\s*[μu]|ω\s*u)\s*=\s*[-+]?\d", low)
    grade_pattern = re.search(r"\b(?:m\s*\d{2,3}|fe\s*\d{3,4}|grade\s+[a-z]*\d+)", low)
    date_pattern = re.search(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|\d{1,2}\s+[a-z]{3,9}\s+\d{4})\b", low)
    word_storey = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(?:floors?|stories|storeys)\b", low)
    if assignment_pattern or ("%" in low and re.search(r"[=<>]", text)):
        return "COMPUTED", None
    if re.search(r"\b(?:lesser|greater) than\b", low) and "period" in low:
        return "COMPUTED", None
    if numerical_pattern or grade_pattern or date_pattern or word_storey:
        if re.search(r"[=<>]|\b(?:ok|pass(?:ed)?|fail(?:ed)?|compliant)\b", low):
            return "COMPUTED", None
        return "VARIABLE", None
    if any(term in low for term in ("base shear", "drift ratio", "fundamental time period", "rayleigh",
                                    "torsional ratio", "calculated", "computed result")):
        return "COMPUTED", None
    if any(term in low for term in ("chatra bahadur", "damak", "residential", "owner", "designer",
                                    "consult", "registration", "contact number", "application no",
                                    "number of story", "story height", "span of", "etabs 19")):
        return "VARIABLE", None
    if "loads" in section_text and re.search(r"\b\d+(?:\.\d+)?\b", low):
        return "VARIABLE", None
    return "FIXED", None


_ORIGINAL_APPLY_TEMPLATE_RULE = apply_template_rule


def apply_template_rule(item: dict[str, Any]) -> None:
    _ORIGINAL_APPLY_TEMPLATE_RULE(item)
    if item.get("type") == "field":
        instruction = (item.get("field") or {}).get("instruction") or ""
        item["regenerated_by"] = "Word"
        item["registry_excluded_reason"] = "Word fields are regenerated by Word and are not value placeholders."
        item.setdefault("field", {})["kind"] = word_field_kind(instruction)
        return
    text = item.get("text", "") or ""
    low = text.lower()
    edition = re.search(r"NBC\s*105\s*:\s*(2020|2077|2025)", text, flags=re.I)
    known_rule = item.get("template_rule") or {}
    if known_rule.get("action") != "clause_variable" or not known_rule.get("clause_key"):
        clauses = []
        for match in re.finditer(r"\b(?:cl(?:ause)?\.?\s*|as\s+per\s+)(\d+(?:\.\d+)+)", text, flags=re.I):
            clause = match.group(1)
            if clause not in clauses:
                clauses.append(clause)
        for match in re.finditer(r"\b(\d+(?:\.\d+)+)\s+(?:of|in)\s+NBC\s*105", text, flags=re.I):
            clause = match.group(1)
            if clause not in clauses:
                clauses.append(clause)
        if clauses:
            references = []
            for clause in clauses:
                if clause in OWNER_CLAUSE_MAP:
                    key, target = OWNER_CLAUSE_MAP[clause]
                    status, decision = "owner_mapped", None
                elif edition and edition.group(1) in {"2020", "2077"}:
                    key, decision = UNRESOLVED_CLAUSE_KEYS.get(
                        clause, ("codes.clauses." + readable_slug(clause, "unmapped_clause"),
                                 "No owner-approved NBC 105:2025 mapping supplied."))
                    target, status = None, "needs_owner_decision"
                else:
                    key = CURRENT_CLAUSE_KEYS.get(clause, "codes.clauses." + readable_slug(clause, "reference"))
                    target, status, decision = clause, "sample_reference", None
                references.append({"clause_key": key, "sample_clause": clause,
                                   "target_clause_2025": target, "mapping_status": status,
                                   "decision": decision})
            if len(references) == 1:
                ref = references[0]
                item["template_rule"] = {"action": "clause_variable", **ref, "edition_key": "codes.edition"}
            else:
                item["template_rule"] = {"action": "clause_variable", "clause_variables": references,
                                         "edition_key": "codes.edition"}
    if item.get("type") == "paragraph" and low.startswith("no soft story"):
        item["template_rule"] = {"action": "computed_variant", "variant_key": "soft_storey_result", "variants": ["present", "not_present"]}
    if item.get("type") == "paragraph" and "no in-plane discontinuity" in low:
        item["template_rule"] = {"action": "computed_variant", "style_override": "Body Text", "variant_key": "in_plane_discontinuity_result", "variants": ["present", "not_present"]}
    if item.get("type") == "paragraph" and "no mass irregularity" in low:
        item["template_rule"] = {"action": "computed_variant", "style_override": "Body Text", "variant_key": "mass_irregularity_result", "variants": ["present", "not_present"]}


def prepare_inventory(items: list[dict[str, Any]]) -> None:
    """Attach neighboring report context, then reclassify and mark Word fields."""
    active_heading: str | None = None
    previous_text = ""
    for item in items:
        text = item.get("text", "") or item.get("text_preview", "") or ""
        if item.get("type") == "paragraph":
            level = (item.get("paragraph") or {}).get("heading_level")
            if level and text.strip():
                active_heading = clean_text(text)
            item["context"] = {"section_heading": active_heading, "preceding_text": previous_text}
            item["classification"], note = classify(item)
            if note and item.get("text_preview") and note != "Regenerated by Word; excluded from the value registry.":
                item["classification_note"] = note
            apply_template_rule(item)
            if (item.get("template_rule") or {}).get("action") == "clause_variable":
                item["classification"] = "VARIABLE"
            if text.strip():
                previous_text = clean_text(text)
        else:
            item["context"] = {"section_heading": active_heading}
            if item.get("type") == "field":
                item["classification"] = "COMPUTED"
                apply_template_rule(item)
    for pos, item in enumerate(items):
        if item.get("type") == "image":
            parent = next((candidate for candidate in items
                           if candidate.get("index") == item.get("parent_paragraph_index")), None)
            if parent and (parent.get("text") or "").strip():
                item["context"]["parent_text"] = clean_text(parent["text"])
            for neighbor in items[pos + 1:pos + 9]:
                if neighbor.get("type") == "paragraph" and re.match(r"\s*(?:figure|table)\s+\d+", neighbor.get("text", ""), re.I):
                    item["context"]["caption"] = clean_text(neighbor.get("text", ""))
                    break
        elif item.get("type") == "table":
            for neighbor in reversed(items[max(0, pos - 4):pos]):
                if neighbor.get("type") == "paragraph" and re.match(r"\s*table\s+\d+\s*:", neighbor.get("text", ""), re.I):
                    item["context"]["caption"] = clean_text(neighbor.get("text", ""))
                    break
    # Final pass: re-apply anchored template rules now that every item's
    # context (section_heading + caption) is populated. Tables and images
    # first received apply_template_rule during inventory_docx when context
    # was empty; this re-run lets table_caption_contains / heading_contains
    # matchers fire correctly.
    for item in items:
        if item.get("type") in {"table", "image"}:
            apply_template_rule(item)


def report_group(item: dict[str, Any]) -> str:
    context = item.get("context") or {}
    text = " ".join(str(value or "") for value in (
        context.get("section_heading"), context.get("caption"), item.get("text"))).lower()
    for terms, group in [
        (("staircase",), "staircase"), (("foundation",), "foundation"),
        (("irregularity", "soft storey", "soft story", "torsion", "eccentricity", "re-entrant", "diaphragm discontinuity", "in-plane", "out-of-plane"), "irregularity"),
        (("drift", "displacement",), "drift"), (("modal", "rayleigh", "mass participation"), "modal"),
        (("seismic", "earthquake", "base shear"), "seismic"),
        (("design summary", "summary"), "summary"), (("beam", "column", "slab", "element"), "elements"),
        (("material", "concrete", "steel", "rebar"), "materials"),
        (("stiffness modifier", "modifier"), "modifiers"), (("load", "dead load", "live load"), "loads"),
        (("code", "clause", "reference"), "codes"),
        (("client", "consultant", "owner", "contact", "address"), "client"),
        (("building", "story", "storey", "floor", "grid", "location"), "building"),
    ]:
        if any(term in text for term in terms):
            return group
    return "project"


def readable_slug(text: str, fallback: str = "project_data") -> str:
    if not clean_text(text):
        return fallback
    text = re.sub(r"^\s*(?:figure|table)\s+\d+\s*[:.-]?\s*", "", text or "", flags=re.I)
    words = slug(text)
    words = re.sub(r"(?:^|_)(?:the|and|for|from|with|used|based|check|table|figure)(?:_|$)", "_", words)
    words = re.sub(r"_+", "_", words).strip("_")
    return "_".join(words.split("_")[:7]) or fallback


def unique_key(base: str, used: set[str], suffix_label: str = "variant") -> str:
    if base not in used:
        used.add(base)
        return base
    suffix = 2
    while True:
        letters = ""
        n = suffix
        while n:
            n, rem = divmod(n - 1, 26)
            letters = chr(97 + rem) + letters
        result = f"{base}_{suffix_label}_{letters}"
        if result not in used:
            break
        suffix += 1
    used.add(result)
    return result


def inferred_unit(text: str) -> str | None:
    low = (text or "").lower().replace("²", "^2")
    if "%" in low:
        return "%"
    if "kn/m" in low:
        return "kN/m²"
    if re.search(r"\bkn\b", low):
        return "kN"
    if re.search(r"\bmm\b", low):
        return "mm"
    if re.search(r"\b(m|meter|meters|metre|metres)\b", low):
        return "m"
    if re.search(r"\b(sec|secs|second|seconds)\b", low) or re.search(r"\bt\s*=", low):
        return "s"
    if "ratio" in low or "drift" in low:
        return "ratio"
    return None


def decimal_places(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    match = re.search(r"\.(\d+)", str(value))
    return len(match.group(1)) if match else 0


def entry_base(key: str, description: str, value_type: str, unit: str | None, source: str,
               required: bool, condition: str | None, index: int | None, example: Any,
               decimals: int | None = None) -> dict[str, Any]:
    return {"key": key, "description": description, "type": value_type, "unit": unit,
            "format": {"decimals": decimals}, "source": source, "required": required,
            "condition": condition, "inventory_item_index": index, "example": example}


def split_assignment_entries(item: dict[str, Any]) -> tuple[list[dict[str, Any]], str] | None:
    text = item.get("text", "") or ""
    assignments = list(re.finditer(r"\b(k|T|Cd|Z|I|R\s*[μu]|Ω\s*u)\s*=\s*([-+]?\d+(?:\.\d+)?)", text, re.I))
    if len(assignments) < 2:
        return None
    key_map = {
        "k": ("seismic.distribution_exponent_k", "Exponent used for vertical force distribution", None, "computed"),
        "t": ("seismic.design_period_used_s", "Fundamental period used in the seismic calculation", "s", "computed"),
        "cd": ("seismic.spectral_coefficient_cd", "Seismic spectral coefficient Cd", None, "computed"),
        "z": ("seismic.zone_factor_z", "Seismic zoning factor Z", None, "excel"),
        "i": ("seismic.importance_factor_i", "Importance factor I", None, "excel"),
        "rμ": ("seismic.response_modification_factor_rmu", "Response modification factor Rμ", None, "computed"),
        "ru": ("seismic.response_modification_factor_rmu", "Response modification factor Rμ", None, "computed"),
        "ωu": ("design.overstrength_factor_ultimate_omega_u", "Ultimate overstrength factor Ωu", None, "computed"),
    }
    entries: list[dict[str, Any]] = []
    template = text
    keys: set[str] = set()
    replacements: list[tuple[int, int, str]] = []
    for match in assignments:
        token = re.sub(r"\s+", "", match.group(1)).lower()
        spec = key_map.get(token)
        if not spec:
            continue
        key, description, unit, source = spec
        normalized = unique_key(key, keys)
        example = match.group(2)
        entries.append(entry_base(normalized, description, "number", unit, source, True, None,
                                  item.get("index"), example, decimal_places(example)))
        replacements.append((match.start(2), match.end(2), "{{ " + normalized + " }}"))
    for start, end, replacement in sorted(replacements, reverse=True):
        template = template[:start] + replacement + template[end:]
    soil = re.search(r"\bsoil\s+([A-Z])\b", text, re.I)
    if soil:
        key = "seismic.soil_class"
        entries.append(entry_base(key, "Soil class stated with the seismic parameters", "text", None,
                                  "excel", True, None, item.get("index"), soil.group(1)))
        template = re.sub(r"\bsoil\s+[A-Z]\b", "soil {{ seismic.soil_class }}", template, count=1, flags=re.I)
    return entries, template


def split_building_entries(item: dict[str, Any]) -> tuple[list[dict[str, Any]], str] | None:
    text = item.get("text", "") or ""
    patterns = [
        (r"height of\s+(\d+(?:\.\d+)?)\s*(?:meters?|metres?|m)\b", "building.story_height_m", "Typical storey height", "m"),
        (r"span of\s+(\d+(?:\.\d+)?)\s*(?:meters?|metres?|m)\s+horizontally\s*\(x-direction\)", "building.span_x_m", "Typical horizontal X-direction span", "m"),
        (r"(\d+(?:\.\d+)?)\s*(?:meters?|metres?|m)\s+vertically\s*\(y-direction\)", "building.span_y_m", "Typical vertical Y-direction span", "m"),
    ]
    matches: list[tuple[re.Match[str], str, str, str]] = []
    for pattern, key, description, unit in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            matches.append((match, key, description, unit))
    if len(matches) < 2:
        return None
    result = []
    template = text
    replacements: list[tuple[int, int, str]] = []
    if re.search(r"\bbrick\s+walls?\b", text, re.I):
        key = "building.infill_wall_material"
        result.append(entry_base(key, "Infill wall material", "text", None, "excel", True,
                                 None, item.get("index"), "brick"))
        wall = re.search(r"\bbrick(?=\s+walls?)", text, re.I)
        if wall:
            replacements.append((wall.start(), wall.end(), "{{ building.infill_wall_material }}"))
    for match, key, description, unit in sorted(matches, key=lambda x: x[0].start(1), reverse=True):
        value = match.group(1)
        result.append(entry_base(key, description, "number", unit, "excel", True, None,
                                 item.get("index"), value, decimal_places(value)))
        replacements.append((match.start(1), match.end(1), "{{ " + key + " }}"))
    for start, end, replacement in sorted(replacements, reverse=True):
        template = template[:start] + replacement + template[end:]
    return result, template


def split_storey_description(item: dict[str, Any]) -> tuple[list[dict[str, Any]], str] | None:
    text = item.get("text", "") or ""
    match = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(floors?|stories|storeys)\b", text, re.I)
    if not match:
        return None
    word_to_number = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                      "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
    raw = match.group(1)
    count = word_to_number.get(raw.lower(), int(raw) if raw.isdigit() else raw)
    count_key = "building.storeys_above_grade"
    result = [entry_base(count_key, "Number of above-grade storeys in the project", "number", "storey",
                         "excel", True, None, item.get("index"), count, 0)]
    template = text[:match.start(1)] + "{{ " + count_key + " }}" + text[match.end(1):]
    material = re.search(r"made\s+of\s+(reinforced\s+concrete|steel|timber)\s+frames?", text, re.I)
    if material:
        key = "building.primary_frame_material"
        result.append(entry_base(key, "Primary structural frame material", "text", None,
                                 "excel", True, None, item.get("index"), material.group(1)))
        template = re.sub(re.escape(material.group(1)), "{{ " + key + " }}", template, count=1, flags=re.I)
    return result, template


def split_period_comparison(item: dict[str, Any]) -> tuple[list[dict[str, Any]], str] | None:
    text = item.get("text", "") or ""
    if "period" not in text.lower() or not re.search(r"\b(?:lesser|greater) than\b", text, re.I):
        return None
    matches = list(re.finditer(r"(empirical|rayleigh) time period\s*\((\d+(?:\.\d+)?)\s*(?:sec|s)\)", text, re.I))
    if len(matches) < 2:
        return None
    entries = []
    template = text
    for match in reversed(matches):
        label = match.group(1).lower()
        key = f"modal.{label}_period_s"
        value = match.group(2)
        entries.append(entry_base(key, f"{label.title()} fundamental period", "number", "s",
                                  "computed", True, None, item.get("index"), value, decimal_places(value)))
        template = template[:match.start(2)] + "{{ " + key + " }}" + template[match.end(2):]
    selected_key = "modal.selected_period_method"
    entries.append(entry_base(selected_key, "Method selected for the design period based on the code comparison",
                              "text", None, "computed", True, None, item.get("index"), "empirical"))
    template = re.sub(r"use\s+(?:the\s+)?empirical\s+time\s+period", "use {{ modal.selected_period_method }} time period", template, flags=re.I)
    return entries, template


def split_structure_height(item: dict[str, Any]) -> tuple[list[dict[str, Any]], str] | None:
    text = item.get("text", "") or ""
    match = re.search(r"total height of the building is\s+(\d+(?:\.\d+)?)\s*m\s*\(\s*(\d+)\s+stories?\s*[×x]\s*(\d+(?:\.\d+)?)\s*m\s*\)", text, re.I)
    if not match:
        return None
    values = [
        ("building.total_height_m", "Total building height", match.group(1), "m", "computed"),
        ("building.storeys_above_grade", "Number of above-grade storeys", match.group(2), "storey", "excel"),
        ("building.story_height_m", "Typical storey height", match.group(3), "m", "excel"),
    ]
    entries = []
    template = text
    for key, description, value, unit, source in reversed(values):
        entries.append(entry_base(key, description, "number", unit, source, True, None,
                                  item.get("index"), value, decimal_places(value)))
        n = values.index((key, description, value, unit, source))
        template = template[:match.start(n + 1)] + "{{ " + key + " }}" + template[match.end(n + 1):]
    return entries, template


def split_modal_criteria(item: dict[str, Any]) -> tuple[list[dict[str, Any]], str] | None:
    text = item.get("text", "") or ""
    if "modal masses" not in text.lower() and "mass participation" not in text.lower():
        return None
    entries = []
    template = text
    replacements: list[tuple[int, int, str]] = []
    percent = re.search(r"(\d+(?:\.\d+)?)\s*percent", text, re.I)
    modes = re.search(r"\b(\d+)\s+modes?\b", text, re.I)
    if percent:
        key = "codes.limits.modal_mass_participation_pct"
        value = percent.group(1)
        entries.append(entry_base(key, "Minimum modal mass participation threshold", "number", "%",
                                  "excel", True, "Verify this code limit against the approved edition.",
                                  item.get("index"), value, decimal_places(value)))
        replacements.append((percent.start(1), percent.end(1), "{{ " + key + " }}"))
    if modes:
        key = "modal.modes_included_count"
        value = modes.group(1)
        entries.append(entry_base(key, "Number of modes included in the ETABS analysis", "number", "mode",
                                  "etabs_api", True, None, item.get("index"), value, 0))
        replacements.append((modes.start(1), modes.end(1), "{{ " + key + " }}"))
    for start, end, replacement in sorted(replacements, reverse=True):
        template = template[:start] + replacement + template[end:]
    return (entries, template) if entries else None


def split_code_limits(item: dict[str, Any]) -> tuple[list[dict[str, Any]], str] | None:
    text = item.get("text", "") or ""
    low = text.lower()
    specs: list[tuple[str, str, str, re.Pattern[str]]] = []
    if "soft storey" in low or "soft story" in low:
        specs = [
            ("codes.limits.soft_storey_adjacent_stiffness_pct", "Soft-storey adjacent-storey stiffness threshold", "%", re.compile(r"(\d+(?:\.\d+)?)\s*%")),
            ("codes.limits.soft_storey_average_stiffness_pct", "Soft-storey three-storey average stiffness threshold", "%", re.compile(r"(\d+(?:\.\d+)?)\s*%")),
        ]
    elif "mass irregularity" in low:
        specs = [("codes.limits.mass_irregularity_effective_mass_difference_pct", "Mass-irregularity effective-mass difference threshold", "%", re.compile(r"(\d+(?:\.\d+)?)\s*%"))]
    elif "re-entrant" in low:
        specs = [("codes.limits.reentrant_corner_projection_pct", "Re-entrant-corner projection threshold", "%", re.compile(r"(\d+(?:\.\d+)?)\s*%"))]
    elif "diaphragm" in low:
        specs = [
            ("codes.limits.diaphragm_opening_area_pct", "Diaphragm opening-area threshold", "%", re.compile(r"(\d+(?:\.\d+)?)\s*%")),
            ("codes.limits.diaphragm_stiffness_change_pct", "Diaphragm stiffness-change threshold", "%", re.compile(r"(\d+(?:\.\d+)?)\s*%")),
        ]
    elif "torsion irregularity" in low or "torsional irregularity" in low:
        specs = [("codes.limits.torsional_displacement_ratio", "Torsional irregularity displacement ratio threshold", "ratio", re.compile(r"(\d+(?:\.\d+)?)\s+times"))]
    elif "story drift" in low or "story height" in low or "deflection" in low:
        specs = [
            ("codes.limits.maximum_story_deflection_ratio", "Maximum story deflection-to-height ratio", "ratio", re.compile(r"(0\.\d+)\s+times the story height")),
            ("codes.limits.serviceability_story_drift_ratio", "Serviceability-limit story drift ratio", "ratio", re.compile(r"drift shall not exceed\s+(0\.\d+)")),
            ("codes.limits.ultimate_story_drift_ratio", "Ultimate-limit story drift ratio", "ratio", re.compile(r"and\s+(0\.\d+)\s+in Ultimate", re.I)),
        ]
    if not specs:
        return None
    entries: list[dict[str, Any]] = []
    replacements: list[tuple[int, int, str]] = []
    template = text
    for key, description, unit, pattern in specs:
        matches = list(pattern.finditer(text))
        for n, match in enumerate(matches):
            if key.endswith(("adjacent_stiffness_pct", "opening_area_pct")) and n > 0:
                continue
            resolved_key = key
            if key.endswith(("average_stiffness_pct", "stiffness_change_pct")):
                if n == 0:
                    continue
            value = match.group(1)
            entries.append(entry_base(resolved_key, description, "number", unit, "excel", True,
                                      "Owner/engineer must verify against the approved NBC 105:2025 edition before use.",
                                      item.get("index"), value, decimal_places(value)))
            replacements.append((match.start(1), match.end(1), "{{ " + resolved_key + " }}"))
            # The same regex is used for paired thresholds; bind the later match to the second semantic key.
            if key.endswith(("adjacent_stiffness_pct", "opening_area_pct")) and n == 0:
                pass
    if not entries:
        return None
    for start, end, replacement in sorted(replacements, reverse=True):
        template = template[:start] + replacement + template[end:]
    return entries, template


def split_reinforcement_entries(item: dict[str, Any]) -> tuple[list[dict[str, Any]], str] | None:
    text = item.get("text", "") or ""
    context = item.get("context") or {}
    prefix = ((context.get("section_heading") or "") + " " + context.get("preceding_text", "")).lower()
    member = "beam" if "beam" in prefix else "column" if "column" in prefix else None
    if member is None or "%" not in text:
        return None
    mode = "minimum" if "minimum" in prefix else "maximum"
    q = f"design.{member}.{mode}_reinforcement"
    formula = re.search(r"=\s*([\d.]+)\s*/\s*\(\s*([\d.]+)\s*\*\s*([\d.]+)\s*\).*?=\s*([\d.]+)\s*%\s*([<>])\s*([\d.]+)\s*%", text)
    entries: list[dict[str, Any]] = []
    if formula:
        values = [formula.group(i) for i in (1, 2, 3, 4, 6)]
        labels = ["provided_reinforcement_area_mm2", "section_width_mm", "section_depth_mm", "provided_pct", "limit_pct"]
        units = ["mm²", "mm", "mm", "%", "%"]
        templates = []
        for suffix, value, unit in zip(labels, values, units):
            key = f"{q}.{suffix}"
            entries.append(entry_base(key, f"{member.title()} {mode} reinforcement {suffix.replace('_', ' ')}",
                                      "number", unit, "computed", True, None, item.get("index"), value,
                                      decimal_places(value)))
            templates.append(key)
        status_key = f"{q}.status"
        status = "pass" if re.search(r"\bok\b", text, re.I) else "unresolved"
        entries.append(entry_base(status_key, f"{member.title()} {mode} reinforcement check status",
                                  "text", None, "computed", True, None, item.get("index"), status))
        template = (f"= {{{{ {templates[0]} }}}}/({{{{ {templates[1]} }}}}*{{{{ {templates[2]} }}}})*100% "
                    f"= {{{{ {templates[3]} }}}}% {formula.group(5)} {{{{ {templates[4]} }}}}% ({{{{ {status_key} }}}})")
        return entries, template
    percentages = re.findall(r"(\d+(?:\.\d+)?)\s*%", text)
    if len(percentages) < 2:
        return None
    for suffix, value, desc in (("provided_pct", percentages[0], "Provided reinforcement percentage"),
                                ("limit_pct", percentages[1], "Code/project comparison percentage")):
        entries.append(entry_base(f"{q}.{suffix}", f"{member.title()} {mode} reinforcement: {desc}",
                                  "number", "%", "computed", True, None, item.get("index"), value,
                                  decimal_places(value)))
    status = "pass" if re.search(r"\bok\b", text, re.I) else "unresolved"
    status_key = f"{q}.status"
    entries.append(entry_base(status_key, f"{member.title()} {mode} reinforcement check status",
                              "text", None, "computed", True, None, item.get("index"), status))
    template = re.sub(r"(\d+(?:\.\d+)?)\s*%", "{{ PLACEHOLDER }}%", text, count=2)
    template = template.replace("{{ PLACEHOLDER }}", f"{{{{ {q}.provided_pct }}}}", 1).replace(
        "{{ PLACEHOLDER }}", f"{{{{ {q}.limit_pct }}}}", 1)
    template = re.sub(r"\bOk\b", f"{{{{ {status_key} }}}}", template, flags=re.I)
    return entries, template


TABLE_SPECS = {
    1: ("client.general_information", "excel", "fixed", "Fixed intake labels; values supplied from project/client input."),
    2: ("codes.references", "excel", "fixed", "Applicable code rows are selected from the approved project code list."),
    3: ("building.general_information", "excel", "fixed", "Fixed fields for site, permit/design storey counts, and project facts."),
    4: ("elements.sizes_and_materials", "etabs_api", "fixed", "Fixed element rows populated from ETABS section/material assignments."),
    5: ("design.structural_system_and_foundation", "excel", "fixed", "Fixed three-row owner-defined table; the foundation row depends on the approved selection."),
    6: ("modifiers.effective_stiffness", "excel", "fixed", "Fixed component rows; values require project/code confirmation."),
    7: ("loads.load_assessment", "etabs_api", "data-driven", "Load rows from ETABS tables/.e2k and confirmed user load inputs."),
    8: ("loads.live_load_intensity", "excel", "data-driven", "Rows depend on occupancy/room types and applicable load criteria."),
    9: ("seismic.empirical_period_calculation", "computed", "fixed", "Fixed calculation rows with project-specific inputs/results."),
    10: ("seismic.vertical_force_distribution", "computed", "data-driven", "One row per modeled storey; derived from project seismic weight and elevation."),
    11: ("modal.rayleigh_x", "computed", "data-driven", "One row per storey for the X-direction Rayleigh calculation."),
    12: ("modal.rayleigh_y", "computed", "data-driven", "One row per storey for the Y-direction Rayleigh calculation."),
    13: ("seismic.design_parameters", "computed", "fixed", "Fixed parameter labels; values sourced from approved code/project inputs and calculations."),
    14: ("design.overstrength_factors", "computed", "fixed", "Fixed parameter rows with project/code-dependent values."),
    15: ("modal.periods_and_mass_participation", "etabs_api", "data-driven", "One row per requested ETABS mode; include the mass-adequacy threshold check."),
    16: ("design.slab_design_output", "etabs_api", "data-driven", "ETABS slab design records; column/header semantics are unresolved because the sample header is blank."),
    17: ("design.beam_deflection_check", "computed", "fixed", "Fixed check labels; values/results depend on the project and calculation."),
    18: ("drift.uls_displacement_figures_x_y", "etabs_api", "fixed", "Two directional figure slots in a fixed layout table."),
    19: ("drift.sls_displacement_figures_x_y", "etabs_api", "fixed", "Two directional figure slots in a fixed layout table."),
    20: ("drift.uls_story_drift_figures_x_y", "etabs_api", "fixed", "Two directional figure slots in a fixed layout table."),
    21: ("drift.sls_story_drift_figures_x_y", "etabs_api", "fixed", "Two directional figure slots in a fixed layout table."),
}


def table_entry(item: dict[str, Any], used: set[str]) -> dict[str, Any]:
    number = (item.get("table") or {}).get("number")
    fallback_group = report_group(item)
    base, source, behavior, row_source = TABLE_SPECS.get(
        number, (f"{fallback_group}.data_table", "excel", "fixed", "Project-specific table source requires confirmation."))
    key = unique_key("table." + base, used)
    header = (item.get("table") or {}).get("header_row") or []
    if number in {18, 19, 20, 21}:
        header = ["X-direction figure slot", "Y-direction figure slot"]
    columns = []
    unresolved_header = False
    for column_no in range(max((item.get("table") or {}).get("columns", 0), len(header))):
        raw = header[column_no] if column_no < len(header) else ""
        label = clean_text(raw) or f"Unlabelled column {column_no + 1}"
        unresolved_header = unresolved_header or not bool(clean_text(raw))
        col_key = unique_key(f"{key}.{readable_slug(label, f'column_{column_no + 1}')}", used, "column")
        columns.append({"key": col_key, "header": label, "unit": inferred_unit(label), "format": {"decimals": None}})
    condition = "Column schema needs owner review; sample table has blank/unlabelled headers." if unresolved_header else None
    table = item.get("table") or {}
    return {
        "key": key,
        "description": clean_text((item.get("context") or {}).get("caption") or "") or f"Table {number}: {clean_text(item.get('text', '')) or base.replace('.', ' ')}",
        "type": "table", "unit": None, "format": {"decimals": None}, "source": source,
        "required": True, "condition": condition, "inventory_item_index": item.get("index"),
        "example": {"rows": table.get("rows"), "columns": table.get("columns"), "header_row": header},
        "columns": columns, "row_source": row_source, "row_behavior": behavior,
    }


def clause_template(text: str, rule: dict[str, Any]) -> str:
    references = rule.get("clause_variables") or ([rule] if rule.get("clause_key") else [])
    template = text
    for ref in references:
        clause = str(ref.get("sample_clause", ""))
        key = ref.get("clause_key")
        if clause and key:
            template = re.sub(r"\b" + re.escape(clause) + r"\b", "{{ " + key + " }}", template, count=1)
    template = re.sub(r"NBC\s*105\s*:\s*(?:2020|2077|2025)", "{{ codes.edition }}", template, flags=re.I)
    if references and "{{ codes.edition }}" not in template:
        for ref in references:
            key = ref.get("clause_key")
            if key:
                template = re.sub(r"(\{\{\s*" + re.escape(key) + r"\s*\}\})",
                                  r"\1 of {{ codes.edition }}", template, count=1)
    return template


def entry_for_item(item: dict[str, Any], key: str, used: set[str]) -> dict[str, Any] | list[dict[str, Any]]:
    cls = item.get("classification")
    typ = item.get("type")
    text = item.get("text", "") or item.get("text_preview", "") or ""
    group = report_group(item)
    if typ == "image":
        context = item.get("context") or {}
        image = item.get("image") or {}
        caption = (image.get("alt_text") or image.get("title") or context.get("caption")
                   or context.get("parent_text") or text or context.get("section_heading", ""))
        full_key = unique_key(f"figure.{group}.{readable_slug(caption, 'report_figure')}", used, "panel")
        return entry_base(full_key, caption or "Report figure slot; generated or supplied by the engineer.",
                          "image", None, "excel", False,
                          "Generated from ETABS or supplied by the user; the figure manager must resolve its source.",
                          item.get("index"), {"alt_text": image.get("alt_text"), "width_inches": image.get("width_inches"), "height_inches": image.get("height_inches")})

    if typ == "paragraph":
        rule = item.get("template_rule") or {}
        if rule.get("variant_key"):
            variant_key = rule["variant_key"]
            full_key = variant_key if "." in variant_key else f"analysis.{variant_key}"
            return entry_base(full_key, text or "Computed report conclusion variant", "text", None,
                              "computed", True, None, item.get("index"), text)

        generated: list[dict[str, Any]] = []
        clause_entry_count = 0
        clause_refs = rule.get("clause_variables") or ([rule] if rule.get("clause_key") else [])
        for ref in clause_refs:
            clause_key = ref.get("clause_key")
            if not clause_key:
                continue
            entry = entry_base(clause_key, f"Clause citation value for {ref.get('sample_clause', clause_key)}",
                               "text", None, "excel", True, ref.get("decision"),
                               item.get("index"), f"{ref.get('sample_clause')} (sample citation)")
            entry["target_clause_2025"] = ref.get("target_clause_2025")
            entry["mapping_status"] = ref.get("mapping_status")
            generated.append(entry)
        clause_entry_count = len(generated)

        split_result = None
        splitters = (split_building_entries, split_structure_height, split_storey_description,
                     split_period_comparison, split_modal_criteria, split_code_limits,
                     split_assignment_entries, split_reinforcement_entries)
        for splitter in splitters:
            split_result = splitter(item)
            if split_result:
                break
        template = split_result[1] if split_result else text
        if clause_refs:
            template = clause_template(template, rule)
        if split_result:
            generated.extend(split_result[0])
        if generated:
            for entry in generated[clause_entry_count:]:
                entry["sentence_template"] = template
            return generated

        if (item.get("style_name") or "").lower() == "caption":
            caption_entries = []
            template = text
            year = re.search(r"NBC\s*105\s*:\s*(\d{4})", text, re.I)
            if year:
                entry = entry_base("codes.edition", "Code edition printed in this caption", "text", None,
                                   "excel", True, None, item.get("index"), f"NBC 105:{year.group(1)}")
                caption_entries.append(entry)
                template = re.sub(r"NBC\s*105\s*:\s*\d{4}", "{{ codes.edition }}", template, flags=re.I)
            city = re.search(r"\bDamak\b", text, re.I)
            if city:
                entry = entry_base("building.location", "Project location used in the report caption", "text", None,
                                   "excel", True, None, item.get("index"), city.group(0))
                caption_entries.append(entry)
                template = re.sub(r"\bDamak\b", "{{ building.location }}", template, flags=re.I)
            if caption_entries:
                for entry in caption_entries:
                    entry["sentence_template"] = template
                return caption_entries

        # Explicit semantic names for common project fields; all remaining names use section + topic text.
        low = text.lower()
        previous = ((item.get("context") or {}).get("preceding_text") or "").lower()
        if "structural design consultant" in previous or "consultant:" in previous:
            key = "client.consultant_name"
        elif "structural report of" in low:
            key = "project.report_title"
        elif low.strip() == "damak" or "location of building" in previous or "address:" in previous:
            key = "building.location"
        elif "residential" in low and ("intended" in low or "purpose" in low):
            key = "building.occupancy"
        elif re.search(r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(?:floors?|stories|storeys)\b", low):
            key = "building.storey_description"
        else:
            base = readable_slug(text, "project_fact")
            key = f"{group}.{base}"
        key = unique_key(key, used)
        value_type = "text"
        value = text
        unit = inferred_unit(text)
        source = "computed" if cls == "COMPUTED" else "excel"
        if "etabs" in low:
            source = "etabs_api"
        elif ".e2k" in low:
            source = "e2k"
        if re.fullmatch(r"\d+(?:\.\d+)?", text.strip()):
            value_type, value, source = "number", text.strip(), "excel"
        elif item.get("template_rule", {}).get("action") == "conditional_section":
            value_type, source = "text", "excel"
        return entry_base(key, text or key.replace(".", " "), value_type, unit, source,
                          cls != "CONDITIONAL", item.get("classification_note") if cls == "CONDITIONAL" else None,
                          item.get("index"), value, decimal_places(value) if value_type == "number" else None)
    if typ == "table":
        return table_entry(item, used)
    return entry_base(key, text or key.replace(".", " "), "text", None, "excel", False, None,
                      item.get("index"), text)


# Inventory indices are intentionally NOT used to bind owner entries to
# items. The anchored rules in config/template_rules.yaml find the items by
# text/heading/caption content; this map only carries the rule_id that
# covers each manual entry, so build_registry can skip items whose
# template_rule_id appears here without relying on positional indices.
MANUAL_COVERED_RULE_IDS: dict[str, str] = {
    "codes.edition": "clause_soft_storey",  # edition is global; any clause rule attaches it
    "codes.clauses.soft_storey": "clause_soft_storey",
    "codes.clauses.in_plane_discontinuity": "clause_in_plane_discontinuity",
    "codes.clauses.mass_irregularity": "clause_mass_irregularity",
    "codes.clauses.reentrant_corner": "clause_reentrant_corner",
    "codes.clauses.diaphragm_discontinuity": "clause_diaphragm_discontinuity",
    "codes.clauses.out_of_plane_offset": "clause_out_of_plane_offset",
    "foundation.support_condition": "foundation_support_wording",
    "analysis.foundation_reaction_combination": "foundation_reaction_caption",
    "analysis.soft_storey_result": "soft_storey_conclusion",
    "analysis.in_plane_discontinuity_result": "in_plane_discontinuity_conclusion",
    "analysis.mass_irregularity_result": "mass_irregularity_conclusion",
    "analysis.reentrant_corner_result": "reentrant_corner_conclusion",
}


# Owner-approved NBC 105:2025 clause mappings. These are emitted on the
# corresponding codes.clauses.* entries as target_clause_2025,
# sample_clause, and mapping_status="owner_mapped" so the inventory tool's
# output matches the curated registry.
OWNER_CLAUSE_TARGETS: dict[str, tuple[str, str]] = {
    "codes.clauses.soft_storey":             ("5.5.1.2", "5.4.1.2"),
    "codes.clauses.in_plane_discontinuity":  ("5.5.1.4", "5.4.1.4"),
    "codes.clauses.mass_irregularity":       ("5.5.1.5", "5.4.1.5"),
    "codes.clauses.reentrant_corner":        ("5.5.2.2", "5.4.2.3"),
    "codes.clauses.diaphragm_discontinuity": ("5.5.2.3", "5.4.2.4"),
    "codes.clauses.out_of_plane_offset":     ("5.5.2.4", "5.4.2.5"),
}


def enriched_owner_entries() -> list[dict[str, Any]]:
    # No inventory_item_index is hardcoded. Items are found by anchored
    # rules; the registry entry's inventory_item_index is filled in by
    # build_registry when a matching rule_id is found on an item.
    item_for_key: dict[str, None] = {key: None for key in MANUAL_COVERED_RULE_IDS}
    entries = []
    for original in owner_registry_entries():
        entry = dict(original)
        key = entry["key"]
        entry.update({"format": {"decimals": None}, "condition": None,
                      "inventory_item_index": item_for_key.get(key),
                      "sentence_template": "{{ " + key + " }}"})
        entry["inventory_item_indices"] = [entry["inventory_item_index"]] if entry["inventory_item_index"] is not None else []
        if key == "building.has_staircase":
            entry["condition"] = "Controls inclusion/removal of the staircase block and TOC entry."
        elif key.startswith("codes.clauses."):
            entry["condition"] = "Owner-approved mapping."
            # Emit target_clause_2025, sample_clause, mapping_status for
            # owner-mapped clauses. example is null; the sample clause lives
            # in sample_clause.
            if key in OWNER_CLAUSE_TARGETS:
                sample, target = OWNER_CLAUSE_TARGETS[key]
                entry["sample_clause"] = sample
                entry["target_clause_2025"] = target
                entry["mapping_status"] = "owner_mapped"
                entry["example"] = None
        elif key == "foundation.support_condition":
            entry["condition"] = "Computed from foundation.type and foundation.soil_class per owner decision."
        elif key.startswith("analysis.") and key.endswith("result"):
            entry["condition"] = "Select the result variant from computed project checks."
        elif key == "analysis.foundation_reaction_combination":
            entry["condition"] = "Caption text is variable; retain the existing foundation reaction image."
        entries.append(entry)
    return entries


def build_registry(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manual = enriched_owner_entries()
    # Build a rule_id -> manual_key index so items whose template_rule was
    # set by a covered rule can be skipped without using inventory indices.
    covered_rule_ids: dict[str, list[str]] = defaultdict(list)
    for key, rule_id in MANUAL_COVERED_RULE_IDS.items():
        covered_rule_ids[rule_id].append(key)
    manual_keys = {entry["key"] for entry in manual}
    used: set[str] = set(manual_keys)
    output: list[dict[str, Any]] = []
    by_key: dict[str, dict[str, Any]] = {}

    def add_entry(entry: dict[str, Any]) -> None:
        index = entry.get("inventory_item_index")
        entry.setdefault("inventory_item_indices", [index] if index is not None else [])
        existing = by_key.get(entry["key"])
        if existing is not None:
            if index is not None and index not in existing.setdefault("inventory_item_indices", []):
                existing["inventory_item_indices"].append(index)
            return
        by_key[entry["key"]] = entry
        output.append(entry)

    for item in items:
        if item.get("type") == "field" or item.get("classification") == "FIXED":
            continue
        if item.get("type") == "paragraph":
            rule = item.get("template_rule") or {}
            multi_keys = {ref.get("clause_key") for ref in rule.get("clause_variables", [])}
            rule_id = item.get("template_rule_id")
            covered_keys = covered_rule_ids.get(rule_id, [])
            if ((covered_keys and not split_code_limits(item))
                    or (rule.get("clause_key") in manual_keys and not split_code_limits(item))
                    or rule.get("variant_key") in manual_keys):
                # Carry the item's inventory index onto the manual entries
                # whose rule_id matched this item.
                for key in covered_keys:
                    for entry in manual:
                        if entry["key"] == key:
                            idx = item.get("index")
                            if idx is not None:
                                entry["inventory_item_index"] = idx
                                entry.setdefault("inventory_item_indices", [])
                                if idx not in entry["inventory_item_indices"]:
                                    entry["inventory_item_indices"].append(idx)
                continue
            if multi_keys and multi_keys.issubset(manual_keys):
                continue
        if item.get("type") == "table":
            add_entry(table_entry(item, used))
            continue
        base = f"{report_group(item)}.{readable_slug(item.get('text', '') or (item.get('context') or {}).get('caption', ''), 'project_fact')}"
        result = entry_for_item(item, base, used)
        if isinstance(result, list):
            for entry in result:
                add_entry(entry)
        else:
            add_entry(result)
    for entry in manual:
        add_entry(entry)
    return output


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def yaml_lines(value: Any, indent: int = 0) -> list[str]:
    pad = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, child in value.items():
            key_text = yaml_quote(str(key))
            if isinstance(child, (dict, list)):
                if child:
                    lines.append(f"{pad}{key_text}:")
                    lines.extend(yaml_lines(child, indent + 2))
                else:
                    lines.append(f"{pad}{key_text}: " + ("{}" if isinstance(child, dict) else "[]"))
            else:
                lines.append(f"{pad}{key_text}: {yaml_scalar(child)}")
        return lines
    if isinstance(value, list):
        lines = []
        for child in value:
            if isinstance(child, (dict, list)):
                lines.append(f"{pad}-")
                lines.extend(yaml_lines(child, indent + 2))
            else:
                lines.append(f"{pad}- {yaml_scalar(child)}")
        return lines
    return [pad + yaml_scalar(value)]


def write_yaml_registry(path: Path, entries: list[dict[str, Any]]) -> None:
    text = "# Curated candidate registry. Word-generated fields are intentionally excluded.\n"
    text += "\n".join(yaml_lines({"items": entries})) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def after_text_for_item(item: dict[str, Any], entries: list[dict[str, Any]]) -> str:
    if item.get("type") == "field":
        return "Regenerated by Word; excluded from the value registry."
    index = item.get("index")
    selected = [entry for entry in entries if entry.get("inventory_item_index") == index
                or index in entry.get("inventory_item_indices", [])]
    if item.get("type") == "paragraph":
        rule = item.get("template_rule") or {}
        for entry in selected:
            template = entry.get("sentence_template")
            if (entry.get("inventory_item_index") == index and template
                    and template != "{{ " + entry.get("key", "") + " }}"):
                return template
        if rule.get("action") == "clause_variable":
            return clause_template(item.get("text", "") or "", rule)
        if selected and selected[0].get("sentence_template"):
            return selected[0]["sentence_template"]
        if selected:
            return "{{ " + selected[0]["key"] + " }}"
    if selected:
        return "{{ " + selected[0]["key"] + " }}"
    return "[review mapping required]"


def write_registry_review(path: Path, items: list[dict[str, Any]], previous: list[dict[str, Any]], entries: list[dict[str, Any]]) -> None:
    previous_by_index = {item.get("index"): item for item in previous}
    entries_by_index: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        for index in entry.get("inventory_item_indices", [entry.get("inventory_item_index")]):
            if index is not None:
                entries_by_index[index].append(entry)
    source_counts: dict[str, int] = defaultdict(int)
    type_counts: dict[str, int] = defaultdict(int)
    for entry in entries:
        source_counts[entry.get("source", "unknown")] += 1
        type_counts[entry.get("type", "unknown")] += 1
    lines = [
        "# Placeholder Registry Review — Full Before/After Listing", "",
        "> **Full listing.** This is the complete per-item before/after output from "
        "`tools/inventory_template.py`. The short curated summary lives in "
        "`docs/registry_review.md`; the live registry is "
        "`config/placeholder_registry.yaml`. This file is regenerated whenever the "
        "inventory tool runs.", "",
        "# Placeholder Registry Review (Phase 1)", "",
        "**Review gate:** this is a proposed registry. Do not generate a production master template until the owner approves it.", "",
        f"Registry entries: **{len(entries)}**. Entry types: " + ", ".join(f"{k}: {v}" for k, v in sorted(type_counts.items())) + ".",
        "Source counts: " + ", ".join(f"{k}: {v}" for k, v in sorted(source_counts.items())) + ".",
        "",
        "## Classification and Word-field handling", "",
        "The previous inventory had 223 non-FIXED rows, including Word field codes. All Word fields remain visible in the inventory with `regenerated_by: Word` and are omitted from the value registry. The curated registry keeps the 18 owner-defined hand-named keys. Table entries now carry columns, a row source, and a fixed/data-driven row model. Numeric expressions and sample ratios are represented as project/example values or computed outputs; this does not validate their engineering correctness.", "",
        "## NBC clause references changed to registry variables", "",
        "No source DOCX text was edited. These are proposed placeholder substitutions in the registry/template map. Only mappings explicitly recorded in the owner's existing decisions are assigned a 2025 target clause; all others remain unresolved.", "",
    ]
    citation_found = []
    for item in items:
        text = item.get("text", "") or ""
        matches = re.findall(r"(?:NBC\s*105\s*:\s*(?:2020|2077))", text, flags=re.I)
        if matches:
            rule = item.get("template_rule") or {}
            citation_found.append((item.get("index"), rule.get("sample_clause", "see text"), rule.get("target_clause_2025"), rule.get("clause_key")))
    for idx, clause, target, key in citation_found:
        mapped = f"→ NBC 105:2025 §{target} ({key})" if target else f"→ {key or 'codes.clauses.*'}; target mapping unresolved"
        lines.append(f"- Inventory item {idx}, sample clause {clause}: {mapped}.")
    lines += ["", "## VARIABLE / COMPUTED / CONDITIONAL / TABLE / IMAGE items: before and proposed after", ""]
    selected = []
    for item in items:
        before = previous_by_index.get(item.get("index"), {})
        old_class = before.get("classification", "not in previous inventory")
        cls = item.get("classification", "FIXED")
        if cls != "FIXED" or old_class in {"VARIABLE", "COMPUTED", "CONDITIONAL", "TABLE", "IMAGE"} or item.get("type") == "field":
            selected.append((item, before, old_class))
    for item, before, old_class in selected:
        idx = item.get("index")
        entries_for_item = entries_by_index.get(idx, [])
        new_class = item.get("classification", "FIXED")
        labels = ", ".join(entry["key"] for entry in entries_for_item) or "(no registry key; Word regenerates this field or content is fixed)"
        before_text = item.get("text", "") or item.get("text_preview", "") or ""
        if item.get("type") == "field":
            before_text = (item.get("field") or {}).get("instruction") or "Word field code (instruction not exposed)"
        elif item.get("type") == "table":
            tab = item.get("table") or {}
            before_text = f"Table {tab.get('number')}: {tab.get('rows')} rows × {tab.get('columns')} columns; sample headers: {tab.get('header_row')}"
        elif item.get("type") == "image":
            im = item.get("image") or {}
            before_text = f"Image {im.get('number')}: caption={((item.get('context') or {}).get('caption') or '(none)')}; size={im.get('width_inches')} × {im.get('height_inches')} in"
        proposed = after_text_for_item(item, entries)
        lines += [f"### Item {idx} — {item.get('type')} — {old_class} → {new_class}", "",
                  f"Keys: {labels}.", "", "**Before:**", "", "```text", before_text, "```", "",
                  "**Proposed after:**", "", "```text", proposed, "```", ""]
    lines += [
        "## Needs my decision", "",
        "1. Confirm the NBC 105:2025 target clauses for sample references **NBC 105:2020 Cl. 2.1 (item 208)**, **Cl. 3.6.1 (item 418)**, **Cl. 5.5 (item 591)**, and **Cl. 5.5.2.1 (item 593)**. No target clause was invented.",
        "2. Confirm the correct NBC 105:2025 mapping for **NBC 105:2077 Cl. 5.6.3 (items 533 and 535)**. These remain explicit unresolved `codes.clauses.serviceability_drift` variables.",
        "3. Confirm source/meaning of table 16 (88 × 8, blank sample header) before assigning its final column keys and row-level source schema.",
        "4. Confirm that tables 18–21 are fixed image-layout containers (two directional figure slots each), not conventional data tables.",
        "5. Confirm which report figures will be generated from ETABS and which are engineer-supplied; the registry currently treats figure slots as optional Excel/user-file inputs pending Phase 4.",
        "6. Confirm project input vs ETABS/e2k source for mixed-source tables (especially loads, building geometry, materials, and design schedules). The proposed `source` is a primary source label, not a silent conflict-resolution rule.",
        "7. Confirm the project-specific values shown as examples (including storey count, grades, seismic factors, and reinforcement ratios); examples are copied from the sample and are not engineering recommendations.",
        "",
        "## Table row models", "",
    ]
    for entry in entries:
        if entry.get("type") == "table":
            lines.append(f"- `{entry['key']}` — `{entry['row_behavior']}` rows; source: {entry['row_source']}; columns: {len(entry.get('columns', []))}.")
    lines += ["", "## Source priority and unresolved data", "",
              "Apply the project rule ETABS API/CSV > `.e2k` > Excel > computed. Record disagreements in a conflict log; do not silently choose. The source counts above are classifications for registry planning, not evidence that sample values have been revalidated.", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def print_diff_summary(existing_path: Path, candidate_entries: list[dict[str, Any]]) -> None:
    if not existing_path.exists():
        print(f"[DIFF] No existing curated registry at {existing_path}; this is an initial candidate.")
        return
    old_text = existing_path.read_text(encoding="utf-8")
    new_text = "# Curated candidate registry. Word-generated fields are intentionally excluded.\n"
    new_text += "\n".join(yaml_lines({"items": candidate_entries})) + "\n"
    old_keys = set(re.findall(r'^\s*"?key"?:\s*"?([^\s",]+)', old_text, flags=re.M))
    new_keys = {entry["key"] for entry in candidate_entries}
    new_keys.update(column["key"] for entry in candidate_entries for column in entry.get("columns", []))
    shared = len(old_keys & new_keys)
    changed = shared if old_text != new_text else 0
    print(f"[DIFF] {existing_path}: {len(new_keys-old_keys)} candidate key(s) added, {len(old_keys-new_keys)} existing key(s) absent, {shared} shared key(s); review content changes for shared keys: {changed}.")
    diff = list(difflib.unified_diff(old_text.splitlines(), new_text.splitlines(), fromfile=str(existing_path), tofile="candidate", lineterm=""))
    if diff:
        print("[DIFF] Unified diff preview (first 24 lines):")
        print("\n".join(diff[:24]))


def safe_registry_path(requested: Path, curated: Path) -> Path:
    """Never write over an existing curated registry; return a sibling candidate path."""
    if requested.resolve() == curated.resolve() and requested.exists():
        return requested.with_name(requested.stem + ".generated" + requested.suffix)
    return requested


def main() -> int:
    args = parse_args()
    registry_path = safe_registry_path(args.registry, args.curated_registry)
    if registry_path != args.registry:
        print(f"[SAFE] Curated registry exists; candidate redirected to {registry_path}.")
    decisions_path = args.decisions
    if decisions_path.resolve() == Path("docs/needs_my_decision.md").resolve() and decisions_path.exists():
        decisions_path = decisions_path.with_name(decisions_path.stem + ".generated" + decisions_path.suffix)
        print(f"[SAFE] Owner decision record exists; generated notes redirected to {decisions_path}.")
    outputs = [args.json, args.markdown, registry_path, decisions_path, args.review]
    existing = [path for path in outputs if path.exists()]
    if existing and not args.force:
        print("[ERROR] Refusing to overwrite existing output(s): " + ", ".join(map(str, existing)) + ". Use --force to replace them.", file=sys.stderr)
        return 2
    previous_items: list[dict[str, Any]] = []
    if args.json.exists():
        try:
            previous_items = json.loads(args.json.read_text(encoding="utf-8")).get("items", [])
        except (OSError, ValueError, AttributeError):
            previous_items = []
    # Load the anchored template rules BEFORE inventory_docx so every call
    # to apply_template_rule (during both inventory_docx and
    # prepare_inventory) sees the loaded rules. verify_template_rules
    # after the pass fails loudly if any rule matched zero items, which is
    # the portability guarantee: editing the sample DOCX cannot silently
    # drop a rule.
    load_template_rules()
    try:
        items, decisions, stats = inventory_docx(args.input)
    except (OSError, ValueError, etree.XMLSyntaxError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    prepare_inventory(items)
    try:
        verify_template_rules()
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    registry = build_registry(items)
    decisions = [
        f"- **Item {item['index']} ({item['classification']})**: {item.get('text_preview', '')}\n  - Suggestion: {item['classification_note']}"
        for item in items if item.get("classification_note")
    ]
    print_diff_summary(args.curated_registry, registry)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps({"source": str(args.input), "statistics": stats, "items": items}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(args.markdown, items, stats)
    write_yaml_registry(registry_path, registry)
    write_decisions(decisions_path, decisions, items)
    write_registry_review(args.review, items, previous_items, registry)
    print(f"[OK] Inventory: {args.json} ({len(items)} items)")
    print(f"[OK] Outline: {args.markdown}")
    print(f"[OK] Registry candidate: {registry_path} ({len(registry)} entries)")
    print(f"[OK] Decisions: {decisions_path}")
    print(f"[OK] Registry review: {args.review}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
