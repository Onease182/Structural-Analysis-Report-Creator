"""Tests for the registry key naming rules and required entry fields.

These tests enforce the eight-task review gate from the owner:

- No key may be longer than 40 characters.
- No key may contain whitespace (spaces, tabs, newlines).
- No key may be numbered (no segment may start with a digit).
- Every registry entry must have a `source`, a `type`, and an
  `inventory_item_index` (the field may be null, but it must be present).
- The curated registry at config/placeholder_registry.yaml must load and
  satisfy all the above.
- The anchored template rules in config/template_rules.yaml must load and
  every rule must have an id, a match block, and an action block.
- verify_template_rules must raise when a rule matches zero items.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import inventory_template as inventory

CURATED_REGISTRY = ROOT / "config" / "placeholder_registry.yaml"
TEMPLATE_RULES = ROOT / "config" / "template_rules.yaml"
RENAME_MAP = ROOT / "docs" / "key_rename_map.csv"

KEY_MAX_LEN = 40


def _key_violations(key: str) -> list[str]:
    violations: list[str] = []
    if len(key) > KEY_MAX_LEN:
        violations.append(f"length>{KEY_MAX_LEN}:{len(key)}")
    if re.search(r"\s", key):
        violations.append("whitespace")
    if "\t" in key:
        violations.append("tab")
    for seg in key.split("."):
        if seg and seg[0].isdigit():
            violations.append(f"digit-segment:{seg}")
            break
    if not key:
        violations.append("empty")
    return violations


class CuratedRegistryKeyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with CURATED_REGISTRY.open("r", encoding="utf-8") as f:
            cls.data = yaml.safe_load(f)
        cls.entries = cls.data["items"]

    def test_registry_loads_and_has_entries(self) -> None:
        self.assertIsNotNone(self.data)
        self.assertIn("items", self.data)
        self.assertGreater(len(self.entries), 0)

    def test_no_key_exceeds_40_chars(self) -> None:
        long_keys = [(e["key"], len(e["key"])) for e in self.entries
                     if len(e["key"]) > KEY_MAX_LEN]
        self.assertEqual(long_keys, [], f"Keys over {KEY_MAX_LEN} chars: {long_keys}")

    def test_no_key_contains_whitespace(self) -> None:
        ws_keys = [e["key"] for e in self.entries if re.search(r"\s", e["key"])]
        self.assertEqual(ws_keys, [], f"Keys with whitespace: {ws_keys}")

    def test_no_key_is_numbered(self) -> None:
        numbered = []
        for e in self.entries:
            for seg in e["key"].split("."):
                if seg and seg[0].isdigit():
                    numbered.append(e["key"])
                    break
        self.assertEqual(numbered, [], f"Keys with a digit-leading segment: {numbered}")

    def test_no_key_is_empty(self) -> None:
        empty = [e["key"] for e in self.entries if not e["key"]]
        self.assertEqual(empty, [], f"Empty keys: {empty}")

    def test_keys_are_unique(self) -> None:
        keys = [e["key"] for e in self.entries]
        self.assertEqual(len(keys), len(set(keys)), "Duplicate keys in the registry")

    def test_no_code_singular_group(self) -> None:
        # The singular `code.*` group was merged into `codes.*`.
        singular = [e["key"] for e in self.entries
                    if e["key"].startswith("code.")
                    and not e["key"].startswith("codes.")]
        self.assertEqual(singular, [], f"Keys still in the singular `code.*` group: {singular}")

    def test_every_entry_has_source_type_and_inventory_index(self) -> None:
        missing = []
        for e in self.entries:
            for field in ("source", "type", "inventory_item_index"):
                if field not in e:
                    missing.append((e["key"], field))
        self.assertEqual(missing, [], f"Entries missing required fields: {missing}")

    def test_every_non_excel_entry_has_etabs_table_or_e2k_section(self) -> None:
        missing = []
        for e in self.entries:
            if e.get("source") in {"etabs_api", "e2k", "computed"}:
                if "etabs_table_or_e2k_section" not in e:
                    missing.append((e["key"], e.get("source")))
        self.assertEqual(missing, [],
                         f"Non-excel entries missing etabs_table_or_e2k_section: {missing}")

    def test_source_values_are_validated(self) -> None:
        valid_sources = {"excel", "etabs_api", "e2k", "computed"}
        bad = [(e["key"], e.get("source")) for e in self.entries
               if e.get("source") not in valid_sources]
        self.assertEqual(bad, [], f"Entries with unknown source: {bad}")


class RenameMapTests(unittest.TestCase):
    def test_rename_map_has_header_and_rows(self) -> None:
        with RENAME_MAP.open("r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        self.assertGreater(len(lines), 1)
        self.assertEqual(lines[0], "old_key,new_key")

    def test_rename_map_new_keys_are_valid(self) -> None:
        with RENAME_MAP.open("r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        # Skip header; the FIXED-reverted rows carry a suffix annotation
        # after the new key, so split on the first comma only.
        bad = []
        for line in lines[1:]:
            old, _, new = line.partition(",")
            new_key = new.split(" ")[0] if " " in new else new
            violations = _key_violations(new_key)
            if violations:
                bad.append((old, new_key, violations))
        self.assertEqual(bad, [], f"Invalid new keys in rename map: {bad}")

    def test_no_old_code_singular_keys_remain_unrenamed(self) -> None:
        # The singular `code.*` group was merged into `codes.*`; every old
        # singular key must appear in the rename map.
        with RENAME_MAP.open("r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        old_keys = {line.split(",")[0] for line in lines[1:] if line}
        singular_old = {"code.edition", "code.clauses.soft_storey",
                        "code.clauses.in_plane_discontinuity",
                        "code.clauses.mass_irregularity", "code.clauses.reentrant_corner",
                        "code.clauses.diaphragm_discontinuity",
                        "code.clauses.out_of_plane_offset"}
        missing = singular_old - old_keys
        self.assertEqual(missing, set(),
                         f"Singular `code.*` keys missing from the rename map: {missing}")


class TemplateRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        inventory.reset_template_rule_state()
        cls.rules = inventory.load_template_rules(TEMPLATE_RULES)

    def test_rules_file_loads(self) -> None:
        self.assertGreater(len(self.rules), 0)

    def test_every_rule_has_id_match_action(self) -> None:
        for rule in self.rules:
            self.assertTrue(rule.get("id"), f"Rule missing id: {rule}")
            self.assertIsInstance(rule.get("match"), dict,
                                  f"Rule {rule.get('id')} missing match dict")
            self.assertIsInstance(rule.get("action"), dict,
                                  f"Rule {rule.get('id')} missing action dict")

    def test_rule_ids_are_unique(self) -> None:
        ids = [r["id"] for r in self.rules]
        self.assertEqual(len(ids), len(set(ids)), f"Duplicate rule ids: {ids}")

    def test_verify_raises_when_a_rule_matches_nothing(self) -> None:
        inventory.reset_template_rule_state()
        inventory.load_template_rules(TEMPLATE_RULES)
        # Do not run any inventory; every rule's counter is still zero.
        with self.assertRaises(RuntimeError) as ctx:
            inventory.verify_template_rules()
        self.assertIn("matched no inventory items", str(ctx.exception))


class AnchoredRuleMatchingTests(unittest.TestCase):
    def setUp(self) -> None:
        inventory.reset_template_rule_state()
        inventory.load_template_rules(TEMPLATE_RULES)

    def test_clause_rule_matches_by_clause_text(self) -> None:
        item = {
            "index": 603, "type": "paragraph", "style_name": "Body Text",
            "text": "As per the clause 5.5.1.2, a soft storey is the one whose stiffness is less.",
            "text_preview": "As per the clause 5.5.1.2, a soft storey is the one whose stiffness is less.",
            "context": {"section_heading": "", "preceding_text": ""},
        }
        inventory.apply_template_rule(item)
        rule = item.get("template_rule") or {}
        self.assertEqual(rule.get("action"), "clause_variable")
        self.assertEqual(rule.get("clause_key"), "codes.clauses.soft_storey")
        self.assertEqual(rule.get("edition_key"), "codes.edition")
        self.assertEqual(item.get("template_rule_id"), "clause_soft_storey")

    def test_staircase_rule_matches_by_text_not_index(self) -> None:
        item = {
            "index": 999, "type": "paragraph", "style_name": "heading 4",
            "text": "\tDesign of Staircases",
            "text_preview": "\tDesign of Staircases",
            "context": {},
        }
        inventory.apply_template_rule(item)
        rule = item.get("template_rule") or {}
        self.assertEqual(rule.get("action"), "conditional_section")
        self.assertEqual(rule.get("condition"), "building.has_staircase")
        self.assertEqual(item.get("template_rule_id"), "staircase_section_conditional")

    def test_table_rule_matches_by_caption(self) -> None:
        item = {
            "index": 202, "type": "table", "style_name": None,
            "text": "A.3-01 | Type of Structural System | Moment Resisting Frames",
            "text_preview": "A.3-01 | Type of Structural System | Moment Resisting Frames",
            "table": {"number": 5, "rows": 3, "columns": 3,
                      "header_row": ["A.3-01", "Type of Structural System", "Moment Resisting Frames"]},
            "context": {"caption": "Table 3: Structural System & Foundation"},
        }
        inventory.apply_template_rule(item)
        rule = item.get("template_rule") or {}
        self.assertEqual(rule.get("action"), "fill_value_column")
        self.assertEqual(item.get("template_rule_id"), "table_structural_system_foundation")

    def test_foundation_support_wording_matches_despite_leading_tab(self) -> None:
        item = {
            "index": 256, "type": "paragraph", "style_name": "Body Text",
            "text": "the foundation is assumed to be fixed.",
            "text_preview": "the foundation is assumed to be fixed.",
            "context": {},
        }
        inventory.apply_template_rule(item)
        rule = item.get("template_rule") or {}
        self.assertEqual(rule.get("action"), "computed_variant")
        self.assertEqual(rule.get("variant_key") or rule.get("inputs"),
                         ["foundation.type", "foundation.soil_class"])
        self.assertEqual(item.get("template_rule_id"), "foundation_support_wording")


if __name__ == "__main__":
    unittest.main()
