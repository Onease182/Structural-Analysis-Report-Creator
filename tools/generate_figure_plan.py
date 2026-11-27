#!/usr/bin/env python3
"""Generate the owner-review figure-to-table plan without editing the DOCX or registry."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs" / "template_inventory.json"
REGISTRY = ROOT / "config" / "placeholder_registry.yaml"
OUTPUT = ROOT / "docs" / "figure_plan.md"


def _text(item: dict[str, Any]) -> str:
    return str(item.get("text") or item.get("text_preview") or "").strip()


def _section_heading(items: list[dict[str, Any]], position: int, section: Any) -> str:
    candidates: list[str] = []
    for item in items[:position]:
        if item.get("section") != section or item.get("type") != "paragraph":
            continue
        text = _text(item)
        style = str(item.get("style_name") or "").lower()
        if text and (style.startswith("heading") or style.startswith("title")):
            candidates.append(text)
    if candidates:
        return candidates[-1]
    return f"Template section {section}"


def _description(inv: dict[str, Any], reg: dict[str, Any] | None) -> str:
    if reg and reg.get("description"):
        return str(reg["description"]).replace("\n", " ").strip()
    image = inv.get("image") or {}
    target = image.get("target") or "no embedded target recorded"
    alt = image.get("alt_text") or image.get("title")
    if alt:
        return f"{alt}; embedded target: {target}"
    return f"Unmapped sample image slot; embedded target: {target}"


def _source_plan(key: str, origin: str, description: str) -> tuple[str, str, str, str, str]:
    """Return proposed type, source, columns/filter, layout, page effect."""
    if origin == "user_supplied":
        return (
            "user-supplied image",
            "UNRESOLVED — owner must supply or approve the image",
            "UNRESOLVED",
            "Retain the image slot with a caption; do not synthesize project/architectural/site evidence.",
            "No planned change; image footprint retained.",
        )
    if origin == "generated":
        k = key.lower()
        if "drift" in k:
            return (
                "generated chart",
                "sls_tables/S01_Story_Drifts.csv; tables/04_Story_Drifts.csv",
                "Story, Direction, Drift; filter by ULS/SLS and EQX/EQY where present",
                "One compact story-by-direction chart with a companion 4-column source table if required for auditability.",
                "Likely same page or +0.25 page depending on chart/table pairing.",
            )
        if "torsional" in k or "soft_story" in k or "irregular" in k:
            return (
                "data table",
                "sls_tables/S11_Centers_Mass_Rigid.csv; tables/09_Centers_Mass_Rigid.csv",
                "Story, CMX, CMY, CRX, CRY, eccentricity fields; filter by story and load case where present",
                "Story-level audit table: Story | governing case | computed check inputs | result; preserve UNRESOLVED when source columns are absent.",
                "Likely -0.25 to +0.25 page; owner approval required before replacing the figure.",
            )
        if "modal" in k:
            return (
                "generated chart",
                "sls_tables/S04_Modal_Periods.csv; sls_tables/S05_Modal_Mass_Ratios.csv",
                "Mode, Period, UX, UY, UZ or the exact available headers",
                "Modal-period/mass-participation chart with a small mode summary table.",
                "Likely same page; chart may reduce the current screenshot footprint.",
            )
        if "foundation" in k or "reaction" in k:
            return (
                "data table",
                "tables/03_Base_Reactions.csv; tables/11_Joint_Reactions.csv",
                "Load case/combo, FX, FY, FZ, MX, MY, MZ; filter to foundation/support reactions",
                "Governing reaction table: support or joint | combo | six reaction components | governing flag.",
                "Likely +0.25 to +0.5 page for a readable audit table.",
            )
        if "rebar" in k or "design" in k:
            return (
                "data table",
                "tables/07_Column_Design.csv; tables/08_Beam_Design.csv; tables/30_Slab_Panels.csv",
                "Use only columns present in the selected CSV; filter to the member/story represented by the slot",
                "Member design table: label/story | section | governing combination | demand | provided reinforcement | check/result.",
                "Likely +0.25 to +1 page depending on member count; pagination must be approved.",
            )
        return (
            "generated chart",
            "UNRESOLVED — generated source table/columns are not identifiable from the registry entry",
            "UNRESOLVED",
            "Owner must approve the source and layout before replacing the sample figure.",
            "UNRESOLVED; no page-count claim until source is identified.",
        )
    if origin == "etabs_screenshot":
        return (
            "data table",
            "UNRESOLVED — screenshot origin has no registry source CSV/columns",
            "UNRESOLVED",
            "Owner decision required: identify the ETABS table, columns, and filter before replacing the screenshot.",
            "UNRESOLVED; retain current screenshot footprint until approved.",
        )
    return (
        "UNRESOLVED / owner decision required",
        "UNRESOLVED",
        "UNRESOLVED",
        "No replacement is proposed until the slot origin and source evidence are identified.",
        "UNRESOLVED",
    )


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def generate() -> str:
    inventory_doc = json.loads(INVENTORY.read_text(encoding="utf-8"))
    registry_doc = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    items = inventory_doc.get("items", [])
    image_items = [(position, item) for position, item in enumerate(items) if item.get("type") == "image"]
    figures = [x for x in registry_doc.get("items", []) if str(x.get("key", "")).startswith("figure.")]
    by_index = {x.get("inventory_item_index"): x for x in figures if x.get("inventory_item_index") is not None}
    image_indices = {item.get("index") for _, item in image_items}
    direct_matches = image_indices & set(by_index)
    unmatched_registry = [x for x in figures if x.get("inventory_item_index") not in image_indices]
    unmatched_images = [item for _, item in image_items if item.get("index") not in by_index]

    lines = [
        "# Part 3 Figure-to-Table Plan",
        "",
        "Generated by `tools/generate_figure_plan.py` from `docs/template_inventory.json` and `config/placeholder_registry.yaml`.",
        "This is an owner-approval plan only. It does not modify `templates/master_template.docx` or `config/placeholder_registry.yaml`; no image slot is replaced by this document.",
        "",
        f"- Image slots in template inventory: **{len(image_items)}**",
        f"- Figure registry entries: **{len(figures)}**",
        f"- Direct inventory-index matches: **{len(direct_matches)}**",
        f"- Image slots without a direct registry entry: **{len(unmatched_images)}**",
        f"- Registry entries without a matching image slot: **{len(unmatched_registry)}**",
        "",
        "The index mismatch is intentionally exposed. Unmatched slots and registry entries are marked `UNRESOLVED` or owner-decision-required rather than inferred from image order.",
        "",
        "| Slot | Inventory index | Heading / section | What the sample image shows | Current origin | Proposed replacement | Source CSV / rationale | Columns / filter | Proposed table layout | Page-count effect | Open questions |",
        "|---:|---:|---|---|---|---|---|---|---|---|---|",
    ]
    for slot, (position, inv) in enumerate(image_items, start=1):
        idx = inv.get("index")
        reg = by_index.get(idx)
        key = str(reg.get("key")) if reg else "UNRESOLVED"
        origin = str(reg.get("figure_origin")) if reg and reg.get("figure_origin") else "UNRESOLVED"
        proposed, source, columns, layout, page_effect = _source_plan(key, origin, _description(inv, reg))
        questions: list[str] = []
        if not reg:
            questions.append("No direct figure-registry entry for this inventory index; identify slot purpose and source.")
        if origin == "etabs_screenshot":
            questions.append("Which ETABS export table, columns, load case/combo, and filter reproduce this screenshot?")
        if origin == "user_supplied":
            questions.append("Who supplies the image and confirms it is project-specific?")
        if proposed.startswith("UNRESOLVED") or "UNRESOLVED" in source:
            questions.append("Owner approval is required before any replacement or page-count change.")
        lines.append("| " + " | ".join(_cell(x) for x in (
            slot, idx, _section_heading(items, position, inv.get("section")), _description(inv, reg), origin,
            proposed, source, columns, layout, page_effect, "; ".join(questions) or "None beyond owner approval of this plan.",
        )) + " |")
    lines += [
        "",
        "## Registry reconciliation",
        "",
        "The following registry entries do not have a matching image-slot inventory index and therefore are not silently assigned to a slot:",
        "",
    ]
    for entry in unmatched_registry:
        lines.append(f"- `{entry.get('key')}` — inventory index `{entry.get('inventory_item_index', 'UNRESOLVED')}`; owner mapping required.")
    if not unmatched_registry:
        lines.append("- None.")
    lines += [
        "",
        "The 45 image slots without direct registry entries are already represented as rows above with `UNRESOLVED` mapping questions. Replacement, source selection, and page-count effects remain pending owner approval.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    OUTPUT.write_text(generate(), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
