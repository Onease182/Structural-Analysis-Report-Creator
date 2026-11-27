from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "figure_plan.md"
INVENTORY = ROOT / "docs" / "template_inventory.json"
REGISTRY = ROOT / "config" / "placeholder_registry.yaml"
TEMPLATE = ROOT / "templates" / "master_template.docx"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_figure_plan_is_generated_and_covers_every_inventory_image_slot():
    before = {path: digest(path) for path in (INVENTORY, REGISTRY, TEMPLATE)}
    subprocess.run([sys.executable, "tools/generate_figure_plan.py"], cwd=ROOT, check=True)
    assert PLAN.exists()
    text = PLAN.read_text(encoding="utf-8")
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    image_count = sum(item.get("type") == "image" for item in inventory["items"])
    figure_count = sum(str(item.get("key", "")).startswith("figure.") for item in registry["items"])
    rows = [line for line in text.splitlines() if line.startswith("|") and not line.startswith("|---")]
    # One header plus exactly one data row per image slot.
    assert len(rows) == image_count + 1
    assert f"Image slots in template inventory: **{image_count}**" in text
    assert f"Figure registry entries: **{figure_count}**" in text
    for phrase in (
        "Current origin",
        "Proposed replacement",
        "Source CSV / rationale",
        "Columns / filter",
        "Proposed table layout",
        "Page-count effect",
        "Open questions",
        "UNRESOLVED",
        "owner approval",
    ):
        assert phrase in text
    assert not re.search(r"(?:/home/|/tmp/|[A-Za-z]:\\)", text)
    assert all("../" not in line for line in text.splitlines())
    assert {path: digest(path) for path in (INVENTORY, REGISTRY, TEMPLATE)} == before
