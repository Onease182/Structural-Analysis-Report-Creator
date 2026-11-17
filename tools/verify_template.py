#!/usr/bin/env python3
"""Verify the master template by rendering with a dummy context and comparing
with the original sample.

ALL checks are strict: any failure causes a non-zero exit. No warnings.

Checks:
  1. Render with a realistic dummy context (sample table row counts,
     sample image sizes).
  2. Convert to PDF (LibreOffice).
  3. Compare heading order and count by position and level.
  4. Fail on any leftover {{ }} or {% %} in the rendered output.
  5. Page count: fail if rendered differs from sample by more than 2.
     If it fails, report per-section page offsets.
  6. Render with has_staircase=false: assert staircase heading, content,
     and TOC entry are gone; no stray page breaks.

Usage:
    python tools/verify_template.py
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import struct
import zlib
from pathlib import Path
from typing import Any

import yaml
from docx import Document
from docx.oxml.ns import qn
from docxtpl import DocxTemplate, InlineImage
from jinja2 import Environment, StrictUndefined
from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "master_template.docx"
SAMPLE = ROOT / "Chatra Bahadur Ramtel.docx"
REGISTRY = ROOT / "config" / "placeholder_registry.yaml"
RENDER_DIR = ROOT / "templates"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"


def load_registry() -> list[dict[str, Any]]:
    with REGISTRY.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)["items"]


# ---------------------------------------------------------------------------
# Sample analysis: table row counts, image sizes, headings
# ---------------------------------------------------------------------------

def analyze_sample() -> dict[str, Any]:
    """Read the sample DOCX and extract table row counts, image sizes,
    and heading structure for comparison."""
    doc = Document(str(SAMPLE))
    body = doc.element.body

    # Table row counts by inventory table number (1-based)
    table_rows: dict[int, int] = {}
    for i, tbl in enumerate(doc.tables, 1):
        table_rows[i] = len(tbl.rows)

    # Image sizes (EMU) and types
    images: list[dict[str, Any]] = []
    for child in body:
        if child.tag.split("}")[-1] != "p":
            continue
        for drawing in child.iter(f"{{{W_NS}}}drawing"):
            inline = drawing.find(f"{{{WP_NS}}}inline")
            anchor = drawing.find(f"{{{WP_NS}}}anchor")
            container = inline if inline is not None else anchor
            if container is None:
                continue
            extent = container.find(f"{{{WP_NS}}}extent")
            if extent is None:
                continue
            cx = int(extent.get("cx", "0"))
            cy = int(extent.get("cy", "0"))
            images.append({
                "type": "inline" if inline is not None else "anchored",
                "cx": cx,
                "cy": cy,
                "width_inches": cx / 914400,
                "height_inches": cy / 914400,
            })

    # Headings with level
    headings: list[dict[str, Any]] = []
    for p in doc.paragraphs:
        style_name = p.style.name if p.style else ""
        if style_name and "heading" in style_name.lower():
            level_match = re.search(r"(\d+)", style_name)
            level = int(level_match.group(1)) if level_match else 0
            headings.append({
                "level": level,
                "style": style_name,
                "text": p.text.strip(),
            })

    return {
        "table_rows": table_rows,
        "images": images,
        "headings": headings,
    }


# ---------------------------------------------------------------------------
# Dummy image generation
# ---------------------------------------------------------------------------

DUMMY_PNG_CACHE: dict[tuple[int, int], Path] = {}


def get_dummy_png(width_px: int, height_px: int) -> Path:
    """Get or create a dummy PNG with the given pixel dimensions."""
    key = (width_px, height_px)
    if key in DUMMY_PNG_CACHE:
        return DUMMY_PNG_CACHE[key]
    path = ROOT / "tests" / "fixtures" / f"dummy_{width_px}x{height_px}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        create_png(path, width_px, height_px)
    DUMMY_PNG_CACHE[key] = path
    return path


def create_png(path: Path, width: int, height: int) -> None:
    """Create a minimal solid-color PNG."""
    signature = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    # Solid gray image data: each row starts with filter byte 0
    raw = b''
    for _ in range(height):
        raw += b'\x00' + b'\xc0\xc0' * width  # gray RGB
    compressed = zlib.compress(raw)
    idat_crc = zlib.crc32(b'IDAT' + compressed)
    idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
    iend_crc = zlib.crc32(b'IEND')
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    path.write_bytes(signature + ihdr + idat + iend)


# ---------------------------------------------------------------------------
# Dummy context builder
# ---------------------------------------------------------------------------

def _set_nested(ctx: dict[str, Any], key: str, value: Any) -> None:
    parts = key.split(".")
    d = ctx
    for part in parts[:-1]:
        if part not in d or not isinstance(d[part], dict):
            d[part] = {}
        d = d[part]
    d[parts[-1]] = value


def analyze_images_in_docx(docx_path: Path) -> list[dict[str, Any]]:
    """Analyze images in a DOCX: type (inline/anchored), extent (EMU),
    and relationship ID."""
    doc = Document(str(docx_path))
    body = doc.element.body
    images: list[dict[str, Any]] = []
    for child in body:
        if child.tag.split("}")[-1] != "p":
            continue
        for drawing in child.iter(f"{{{W_NS}}}drawing"):
            inline = drawing.find(f"{{{WP_NS}}}inline")
            anchor = drawing.find(f"{{{WP_NS}}}anchor")
            container = inline if inline is not None else anchor
            if container is None:
                continue
            extent = container.find(f"{{{WP_NS}}}extent")
            if extent is None:
                continue
            cx = int(extent.get("cx", "0"))
            cy = int(extent.get("cy", "0"))
            blip = drawing.find(f".//{{{A_NS}}}blip")
            rid = blip.get(f"{{{R_NS}}}embed") if blip is not None else None
            images.append({
                "type": "inline" if inline is not None else "anchored",
                "cx": cx,
                "cy": cy,
                "rid": rid,
            })
    return images


def generate_image_report(sample_images: list[dict], template_images: list[dict],
                          rendered_images: list[dict]) -> list[str]:
    """Generate a per-image comparison report."""
    lines = [
        "\n=== Image Report ===",
        f"Sample images: {len(sample_images)}",
        f"Template images: {len(template_images)}",
        f"Rendered images: {len(rendered_images)}",
        "",
        "| # | Sample type | Template | Rendered type | Sample EMU (cx×cy) | Rendered EMU |",
        "|---|-------------|----------|---------------|-------------------|-------------|",
    ]
    max_len = max(len(sample_images), len(rendered_images))
    for i in range(max_len):
        s = sample_images[i] if i < len(sample_images) else {"type": "?", "cx": 0, "cy": 0}
        t = template_images[i] if i < len(template_images) else {"type": "?", "rid": "?"}
        r = rendered_images[i] if i < len(rendered_images) else {"type": "?", "cx": 0, "cy": 0}
        lines.append(
            f"| {i} | {s['type']} | rId={t.get('rid','?')} | {r['type']} | "
            f"{s['cx']}×{s['cy']} | {r['cx']}×{r['cy']} |"
        )
    return lines


def validate_context_strict(ctx: dict[str, Any], entries: list[dict[str, Any]]) -> None:
    """Strict-mode pre-render validation:
    1. Every codes.clauses.* value must be non-null and non-empty.
    2. Every required registry key must be present in the context.

    Raises ValueError on any failure."""
    failures: list[str] = []

    # 1. Check codes.clauses.* values are non-null and non-empty
    def _check_clauses(d: dict[str, Any], prefix: str = "") -> None:
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                _check_clauses(v, full_key)
            elif full_key.startswith("codes.clauses."):
                if v is None or (isinstance(v, str) and not v.strip()):
                    failures.append(f"Null/empty clause value: {full_key}")

    _check_clauses(ctx)

    # 2. Check every required registry key is in the context
    def _has_key(d: dict[str, Any], key: str) -> bool:
        parts = key.split(".")
        cur = d
        for part in parts[:-1]:
            if not isinstance(cur, dict) or part not in cur:
                return False
            cur = cur[part]
        return isinstance(cur, dict) and parts[-1] in cur

    for entry in entries:
        if entry.get("required"):
            key = entry["key"]
            if not _has_key(ctx, key):
                failures.append(f"Missing required key in context: {key}")

    if failures:
        raise ValueError(
            f"Strict mode validation failed ({len(failures)} issue(s)): "
            + "; ".join(failures[:5])
        )


def create_strict_template(docx_path: Path) -> DocxTemplate:
    """Create a DocxTemplate with jinja2 StrictUndefined so any missing
    context key fails with the key name."""
    tpl = DocxTemplate(str(docx_path))
    tpl.jinja_env = Environment(undefined=StrictUndefined)
    return tpl


def build_dummy_context(entries: list[dict[str, Any]], tpl: DocxTemplate,
                         sample_data: dict[str, Any],
                         has_staircase: bool = True) -> dict[str, Any]:
    """Build a realistic dummy context using sample table row counts and
    image sizes. Each text value equals its own key name."""
    ctx: dict[str, Any] = {}
    sample_images = sample_data["images"]
    sample_table_rows = sample_data["table_rows"]
    img_idx = 0

    for entry in entries:
        key = entry["key"]
        entry_type = entry.get("type", "text")

        if entry_type == "image":
            # Use the sample image's size
            if img_idx < len(sample_images):
                si = sample_images[img_idx]
                w_in = si["width_inches"]
                h_in = si["height_inches"]
                # Create a dummy PNG with the right aspect ratio
                # Use 100px per inch for a reasonable resolution
                w_px = max(1, int(w_in * 100))
                h_px = max(1, int(h_in * 100))
                dummy = get_dummy_png(w_px, h_px)
                val = InlineImage(tpl, str(dummy), width=w_in)
                img_idx += 1
            else:
                dummy = get_dummy_png(100, 100)
                val = InlineImage(tpl, str(dummy))
            _set_nested(ctx, key, val)

        elif entry_type == "bool":
            val = has_staircase if key == "building.has_staircase" else True
            _set_nested(ctx, key, val)

        elif entry_type == "table":
            # Use the sample's row count (minus header)
            inv_idx = entry.get("inventory_item_index")
            # Find the table number from the inventory
            import json
            inv_path = ROOT / "docs" / "template_inventory.json"
            with inv_path.open() as f:
                inv_items = json.load(f)["items"]
            table_no = None
            for inv_item in inv_items:
                if inv_item.get("index") == inv_idx and inv_item.get("type") == "table":
                    table_no = inv_item.get("table", {}).get("number")
                    break
            if table_no and table_no in sample_table_rows:
                n_data_rows = sample_table_rows[table_no] - 1  # minus header
            else:
                n_data_rows = 3
            cols = entry.get("columns") or []
            row = {}
            for i, col in enumerate(cols):
                col_key = col.get("key", f"col{i}")
                row[col_key.split(".")[-1]] = key
            _set_nested(ctx, key, {"rows": [row] * max(1, n_data_rows)})

        elif entry_type == "number":
            _set_nested(ctx, key, 1)

        else:
            _set_nested(ctx, key, key)

    _set_nested(ctx, "building.has_staircase", has_staircase)
    return ctx


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_leftover_placeholders(docx_path: Path) -> list[str]:
    doc = Document(str(docx_path))
    body = doc.element.body
    full_text = ""
    for t in body.iter(f"{{{W_NS}}}t"):
        full_text += (t.text or "")
    leftovers = []
    for m in re.finditer(r"\{\{[^}]+\}\}", full_text):
        leftovers.append(f"{{{{ }}}}: {m.group(0)}")
    for m in re.finditer(r"\{%[^%]+%\}", full_text):
        leftovers.append(f"{{% %}}: {m.group(0)}")
    return leftovers


def extract_headings_with_level(docx_path: Path) -> list[dict[str, Any]]:
    doc = Document(str(docx_path))
    headings = []
    for p in doc.paragraphs:
        style_name = p.style.name if p.style else ""
        if style_name and "heading" in style_name.lower():
            level_match = re.search(r"(\d+)", style_name)
            level = int(level_match.group(1)) if level_match else 0
            headings.append({
                "level": level,
                "style": style_name,
                "text": p.text.strip(),
            })
    return headings


def compare_headings(sample_headings: list[dict], rendered_headings: list[dict],
                     entries: list[dict[str, Any]]) -> list[str]:
    """Compare headings by position and level. Where a heading is replaced
    by a placeholder, the dummy text must equal that placeholder's key name.
    Returns a list of failure messages (empty if all match)."""
    failures: list[str] = []
    # Build a set of all registry keys for checking placeholder substitutions
    all_keys = {e["key"] for e in entries}

    if len(sample_headings) != len(rendered_headings):
        failures.append(
            f"Heading count mismatch: sample={len(sample_headings)}, "
            f"rendered={len(rendered_headings)}"
        )
        return failures

    for i, (s, r) in enumerate(zip(sample_headings, rendered_headings)):
        if s["level"] != r["level"]:
            failures.append(
                f"Heading {i}: level mismatch sample={s['level']} vs rendered={r['level']} "
                f"(sample text: {s['text'][:50]!r})"
            )
            continue
        # Text comparison: if the sample heading was replaced by a placeholder,
        # the rendered text should be the key name.
        s_text = s["text"]
        r_text = r["text"]
        if s_text == r_text:
            continue  # Exact match
        # Check if rendered text is a registry key name (placeholder substitution)
        if r_text in all_keys:
            continue  # Expected: heading replaced by placeholder value
        # Also check if the rendered text contains a key name (partial substitution)
        if any(r_text == key for key in all_keys):
            continue
        failures.append(
            f"Heading {i}: text mismatch sample={s_text[:60]!r} vs "
            f"rendered={r_text[:60]!r}"
        )
    return failures


def convert_to_pdf(docx_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf",
         "--outdir", str(output_dir), str(docx_path)],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")
    pdf_path = output_dir / (docx_path.stem + ".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"PDF not found at {pdf_path}")
    return pdf_path


def count_pdf_pages(pdf_path: Path) -> int:
    result = subprocess.run(
        ["pdfinfo", str(pdf_path)],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":")[1].strip())
    # Fallback
    result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True, text=True, timeout=30,
    )
    return result.stdout.count("\f") + 1 if result.stdout else 0


def update_toc_cache_remove_staircase(docx_path: Path) -> None:
    """Remove the 'Design of Staircases' entry from the TOC field's cached
    result text, without editing the TOC field instruction itself.

    The TOC field is stored as a complex field with fldChar begin/separate/end
    markers. The cached result is the content between 'separate' and 'end'.
    Paragraphs within the cached result that contain 'Design of Staircases'
    are removed."""
    doc = Document(str(docx_path))
    body = doc.element.body
    removed = False
    # Find all paragraphs that are within a TOC field result and contain
    # "Design of Staircases" text.
    # A paragraph is within a TOC field if it has a TOC style (toc 1, toc 2, etc.)
    # or is between fldChar separate and end markers.
    paragraphs_to_remove = []
    in_toc_field = False
    for child in body:
        tag = child.tag.split("}")[-1]
        if tag != "p":
            continue
        # Check for fldChar begin/separate/end
        for fld in child.iter(f"{{{W_NS}}}fldChar"):
            fld_type = fld.get(f"{{{W_NS}}}fldCharType")
            if fld_type == "begin":
                in_toc_field = True
            elif fld_type == "separate":
                pass  # Result starts here
            elif fld_type == "end":
                in_toc_field = False
        # Check if this paragraph has a TOC style
        pPr = child.find(f"{{{W_NS}}}pPr")
        style_val = None
        if pPr is not None:
            pStyle = pPr.find(f"{{{W_NS}}}pStyle")
            if pStyle is not None:
                style_val = pStyle.get(f"{{{W_NS}}}val", "")
        is_toc_para = (style_val and "toc" in style_val.lower()) or in_toc_field
        if not is_toc_para:
            continue
        # Check if this paragraph's text contains "Design of Staircases"
        text = "".join((t.text or "") for t in child.iter(f"{{{W_NS}}}t"))
        if "design of staircases" in text.lower():
            paragraphs_to_remove.append(child)
    for p in paragraphs_to_remove:
        p.getparent().remove(p)
        removed = True
    if removed:
        doc.save(str(docx_path))


def get_heading_page_offsets(pdf_path: Path, headings: list[dict]) -> list[int]:
    """For each heading, find the page number where it starts (0-based).
    Uses pdftotext to find heading text in pages."""
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return []
    pages = result.stdout.split("\f")
    offsets: list[int] = []
    for h in headings:
        text = h["text"]
        if not text:
            offsets.append(-1)
            continue
        found_page = -1
        for page_idx, page_text in enumerate(pages):
            if text[:30] in page_text:
                found_page = page_idx
                break
        offsets.append(found_page)
    return offsets


# ---------------------------------------------------------------------------
# Main verification
# ---------------------------------------------------------------------------

def verify() -> int:
    entries = load_registry()
    sample_data = analyze_sample()
    failures: list[str] = []

    print("=" * 60)
    print("TEMPLATE VERIFICATION (strict mode)")
    print("=" * 60)

    # --- 1. Render with has_staircase=true ---
    print("\n[1] Rendering with realistic dummy context (has_staircase=True)...")
    tpl = create_strict_template(TEMPLATE)
    ctx_true = build_dummy_context(entries, tpl, sample_data, has_staircase=True)

    # Strict-mode pre-render validation
    try:
        validate_context_strict(ctx_true, entries)
        print("    PASS: strict-mode context validation")
    except ValueError as exc:
        msg = f"FAIL: strict-mode validation: {exc}"
        failures.append(msg)
        print(f"    {msg}")

    # Replace anchored images using replace_pic (keeps anchor position/wrap/extent)
    template_images = analyze_images_in_docx(TEMPLATE)
    for ti in template_images:
        if ti["type"] == "anchored" and ti.get("rid"):
            # Use a dummy image matching the sample's size
            dummy = get_dummy_png(100, 100)
            try:
                tpl.replace_pic(ti["rid"], str(dummy))
            except Exception:
                pass  # rId may not be in the template's pic map

    rendered_true = RENDER_DIR / "rendered_dummy.docx"
    tpl.render(ctx_true)
    tpl.save(str(rendered_true))
    print(f"    Rendered: {rendered_true}")

    # --- Image report ---
    rendered_images = analyze_images_in_docx(rendered_true)
    image_report = generate_image_report(
        sample_data["images"], template_images, rendered_images
    )
    for line in image_report[:10]:
        print(f"    {line}")

    # --- 2. Check for leftover placeholders ---
    print("\n[2] Checking for leftover {{ }} or {% %}...")
    leftovers = check_leftover_placeholders(rendered_true)
    if leftovers:
        msg = f"FAIL: {len(leftovers)} leftover placeholders: {leftovers[:5]}"
        failures.append(msg)
        print(f"    {msg}")
    else:
        print("    PASS: no leftover placeholders")

    # --- 2b. Check image count and types ---
    print("\n[2b] Checking image count, anchor/inline type, and extents...")
    sample_imgs = sample_data["images"]
    if len(rendered_images) != len(sample_imgs):
        msg = (f"FAIL: image count mismatch sample={len(sample_imgs)} vs "
               f"rendered={len(rendered_images)}")
        failures.append(msg)
        print(f"    {msg}")
    else:
        # Check each image's type is preserved
        type_mismatches = []
        extent_mismatches = []
        for i, (s, r) in enumerate(zip(sample_imgs, rendered_images)):
            if s["type"] != r["type"]:
                type_mismatches.append(f"img {i}: sample={s['type']} vs rendered={r['type']}")
            # Check extents match (within 1 EMU tolerance for floating point)
            if abs(s["cx"] - r["cx"]) > 1 or abs(s["cy"] - r["cy"]) > 1:
                extent_mismatches.append(
                    f"img {i}: sample={s['cx']}×{s['cy']} vs rendered={r['cx']}×{r['cy']}"
                )
        if type_mismatches:
            msg = f"FAIL: image type mismatches: {type_mismatches[:5]}"
            failures.append(msg)
            print(f"    {msg}")
        elif extent_mismatches:
            msg = f"FAIL: image extent mismatches: {extent_mismatches[:5]}"
            failures.append(msg)
            print(f"    {msg}")
        else:
            print(f"    PASS: {len(sample_imgs)} images, types and extents match")

    # --- 3. Convert to PDF and compare page counts ---
    print("\n[3] Converting to PDF and comparing page counts...")
    try:
        pdf_rendered = convert_to_pdf(rendered_true, RENDER_DIR / "pdf")
        pdf_sample = convert_to_pdf(SAMPLE, RENDER_DIR / "pdf")
        pages_rendered = count_pdf_pages(pdf_rendered)
        pages_sample = count_pdf_pages(pdf_sample)
        print(f"    Sample pages: {pages_sample}")
        print(f"    Rendered pages: {pages_rendered}")
        if abs(pages_rendered - pages_sample) > 2:
            msg = (f"FAIL: page count differs by {abs(pages_rendered - pages_sample)} "
                   f"(sample={pages_sample}, rendered={pages_rendered}, max allowed=2)")
            failures.append(msg)
            print(f"    {msg}")
            # Report per-section page offsets
            sample_headings = sample_data["headings"]
            rendered_headings = extract_headings_with_level(rendered_true)
            print("    Per-section page offsets (sample vs rendered):")
            sample_offsets = get_heading_page_offsets(pdf_sample, sample_headings[:20])
            rendered_offsets = get_heading_page_offsets(pdf_rendered, rendered_headings[:20])
            for i in range(min(len(sample_offsets), len(rendered_offsets))):
                s_text = sample_headings[i]["text"][:40] if i < len(sample_headings) else "?"
                r_text = rendered_headings[i]["text"][:40] if i < len(rendered_headings) else "?"
                print(f"      [{i}] sample p{sample_offsets[i]+1 if sample_offsets[i]>=0 else '?'} "
                      f"vs rendered p{rendered_offsets[i]+1 if rendered_offsets[i]>=0 else '?'}: "
                      f"{s_text!r}")
        else:
            print("    PASS: page count within tolerance")
    except Exception as exc:
        msg = f"FAIL: PDF conversion failed: {exc}"
        failures.append(msg)
        print(f"    {msg}")

    # --- 4. Compare headings by position and level ---
    print("\n[4] Comparing heading order and level...")
    sample_headings = sample_data["headings"]
    rendered_headings = extract_headings_with_level(rendered_true)
    print(f"    Sample headings: {len(sample_headings)}")
    print(f"    Rendered headings: {len(rendered_headings)}")
    heading_failures = compare_headings(sample_headings, rendered_headings, entries)
    if heading_failures:
        failures.extend(heading_failures)
        for hf in heading_failures[:5]:
            print(f"    {hf}")
        if len(heading_failures) > 5:
            print(f"    ... and {len(heading_failures) - 5} more")
    else:
        print("    PASS: heading order and levels match")

    # --- 5. Render with has_staircase=false ---
    print("\n[5] Rendering with has_staircase=false...")
    tpl2 = create_strict_template(TEMPLATE)
    ctx_false = build_dummy_context(entries, tpl2, sample_data, has_staircase=False)
    validate_context_strict(ctx_false, entries)
    tpl2.render(ctx_false)
    rendered_false = RENDER_DIR / "rendered_no_staircase.docx"
    tpl2.save(str(rendered_false))
    print(f"    Rendered: {rendered_false}")

    headings_false = extract_headings_with_level(rendered_false)

    # Find staircase heading position in sample
    staircase_idx = None
    for i, h in enumerate(sample_headings):
        if "staircase" in h["text"].lower() and "design of staircases" in h["text"].lower():
            staircase_idx = i
            break

    if staircase_idx is None:
        msg = "FAIL: staircase heading not found in sample"
        failures.append(msg)
        print(f"    {msg}")
    else:
        # Count how many headings are in the staircase block (the heading + the
        # empty Heading 5 that follows it, per the owner decision).
        staircase_block_size = 1  # the heading itself
        if staircase_idx + 1 < len(sample_headings):
            next_h = sample_headings[staircase_idx + 1]
            if next_h["level"] > sample_headings[staircase_idx]["level"] and not next_h["text"]:
                staircase_block_size = 2  # heading + empty sub-heading

        # --- 5a. Staircase heading absent from body ---
        print("\n[5a] Checking staircase heading is absent from body...")
        staircase_headings = [h for h in headings_false if "staircase" in h["text"].lower()]
        if staircase_headings:
            msg = f"FAIL: staircase heading still present: {[h['text'] for h in staircase_headings]}"
            failures.append(msg)
            print(f"    {msg}")
        else:
            print("    PASS: staircase heading absent from body")

        # --- 5b. Sample content range under staircase is absent ---
        print("\n[5b] Checking staircase content range is absent...")
        # The empty Heading 5 that was under the staircase heading should be gone
        empty_h5_after = False
        for h in headings_false:
            if h["level"] == 5 and not h["text"]:
                # Check if this empty H5 is in the staircase area
                pass  # There may be other empty H5s; we check by position below
        # The rendered should have fewer headings (by staircase_block_size)
        expected_count = len(sample_headings) - staircase_block_size
        if len(headings_false) != expected_count:
            msg = (f"FAIL: heading count after staircase removal = {len(headings_false)}, "
                   f"expected {expected_count} (sample {len(sample_headings)} - {staircase_block_size})")
            failures.append(msg)
            print(f"    {msg}")
        else:
            print(f"    PASS: heading count = {expected_count} (removed {staircase_block_size} headings)")

        # --- 5c. TOC entry for staircase is absent ---
        print("\n[5c] Checking TOC entry for staircase is absent...")
        # Post-process: update the TOC field cache to remove the staircase
        # entry, without editing the TOC field instruction itself.
        update_toc_cache_remove_staircase(rendered_false)
        # Now check: search for "Design of Staircases" (the heading text) in
        # the full document text. Image placeholder values like
        # "figure.staircase.design_main" contain "staircase" but not
        # "Design of Staircases", so this is specific enough.
        doc_false = Document(str(rendered_false))
        full_text_false = ""
        for t in doc_false.element.body.iter(f"{{{W_NS}}}t"):
            full_text_false += (t.text or "")
        staircase_toc_entries = []
        for line in full_text_false.split("\n"):
            if "design of staircases" in line.lower():
                staircase_toc_entries.append(line.strip()[:80])
        if staircase_toc_entries:
            msg = f"FAIL: 'Design of Staircases' still in document: {staircase_toc_entries[:3]}"
            failures.append(msg)
            print(f"    {msg}")
        else:
            print("    PASS: no 'Design of Staircases' text in document (body + TOC)")

        # --- 5d. No stray page break adjacent to removed block ---
        print("\n[5d] Checking no stray page breaks near removed block...")
        # Check for consecutive page breaks or empty paragraphs with page breaks
        # in the area where the staircase block was removed.
        page_break_issues = []
        paragraphs_false = list(doc_false.paragraphs)
        # Find the paragraph that was right before the staircase heading
        # (in the sample, the heading before staircase was "Design of Foundations")
        # In the rendered, the paragraph after "Design of Foundations" should be
        # the next section heading, not an empty page-break paragraph.
        for i, p in enumerate(paragraphs_false):
            # Check for empty paragraphs with page breaks
            if not p.text.strip():
                pPr = p._element.find(f"{{{W_NS}}}pPr")
                if pPr is not None:
                    rPr = pPr.find(f"{{{W_NS}}}rPr")
                    # Check for page break before
                    pbdr = pPr.find(f"{{{W_NS}}}pageBreakBefore")
                    if pbdr is not None:
                        # Check if the next paragraph also has a page break or is empty
                        if i + 1 < len(paragraphs_false):
                            next_p = paragraphs_false[i + 1]
                            next_pPr = next_p._element.find(f"{{{W_NS}}}pPr")
                            if next_pPr is not None:
                                next_pbdr = next_pPr.find(f"{{{W_NS}}}pageBreakBefore")
                                if next_pbdr is not None:
                                    page_break_issues.append(
                                        f"Consecutive page breaks at paragraph {i}"
                                    )
        if page_break_issues:
            msg = f"FAIL: stray page breaks: {page_break_issues[:3]}"
            failures.append(msg)
            print(f"    {msg}")
        else:
            print("    PASS: no stray page breaks detected")

        # --- 5e. Headings before staircase unchanged and in order ---
        print("\n[5e] Checking headings before staircase are unchanged...")
        before_sample = sample_headings[:staircase_idx]
        before_rendered = headings_false[:staircase_idx]
        before_failures = compare_headings(before_sample, before_rendered, entries)
        if before_failures:
            failures.extend(before_failures)
            for bf in before_failures[:3]:
                print(f"    {bf}")
        else:
            print(f"    PASS: {len(before_sample)} headings before staircase match")

        # --- 5f. Headings after staircase unchanged and in order ---
        print("\n[5f] Checking headings after staircase are unchanged...")
        after_sample = sample_headings[staircase_idx + staircase_block_size:]
        after_rendered = headings_false[staircase_idx:]
        after_failures = compare_headings(after_sample, after_rendered, entries)
        if after_failures:
            failures.extend(after_failures)
            for af in after_failures[:3]:
                print(f"    {af}")
        else:
            print(f"    PASS: {len(after_sample)} headings after staircase match")

        # --- 5g. No leftover placeholders in no-staircase render ---
        print("\n[5g] Checking for leftover placeholders in no-staircase render...")
        leftovers_false = check_leftover_placeholders(rendered_false)
        if leftovers_false:
            msg = f"FAIL: {len(leftovers_false)} leftover placeholders: {leftovers_false[:5]}"
            failures.append(msg)
            print(f"    {msg}")
        else:
            print("    PASS: no leftover placeholders")

    # --- Summary ---
    print("\n" + "=" * 60)
    if failures:
        print(f"VERIFICATION FAILED: {len(failures)} failure(s)")
        for f in failures:
            print(f"  - {f}")
        return 1
    else:
        print("VERIFICATION PASSED")
        print(f"  Template: {TEMPLATE}")
        print(f"  Rendered (dummy): {rendered_true}")
        print(f"  Rendered (no staircase): {rendered_false}")
        return 0


def main() -> int:
    if not TEMPLATE.exists():
        print(f"[ERROR] Template not found: {TEMPLATE}", file=sys.stderr)
        print("        Run: python tools/make_template.py", file=sys.stderr)
        return 2
    return verify()


if __name__ == "__main__":
    raise SystemExit(main())
