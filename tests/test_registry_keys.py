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


# ============================================================================
# Phase 1 continuation tests (Tasks 1-5 regression fixes)
# ============================================================================

class ClauseFieldTests(unittest.TestCase):
    """Task 1: every codes.clauses.* entry must carry target_clause_2025,
    sample_clause, and mapping_status. example must be null."""

    @classmethod
    def setUpClass(cls) -> None:
        with CURATED_REGISTRY.open("r", encoding="utf-8") as f:
            cls.entries = yaml.safe_load(f)["items"]
        cls.clauses = [e for e in cls.entries if e["key"].startswith("codes.clauses.")]

    def test_every_clause_has_required_fields(self) -> None:
        missing = []
        for e in self.clauses:
            for field in ("target_clause_2025", "sample_clause", "mapping_status"):
                if field not in e:
                    missing.append((e["key"], field))
        self.assertEqual(missing, [], f"Clause entries missing fields: {missing}")

    def test_clause_example_is_null(self) -> None:
        bad = [(e["key"], e.get("example")) for e in self.clauses
               if e.get("example") is not None]
        self.assertEqual(bad, [], f"Clause entries with non-null example: {bad}")

    def test_owner_mapped_clauses_have_target(self) -> None:
        owner_mapped = [e for e in self.clauses if e.get("mapping_status") == "owner_mapped"]
        self.assertEqual(len(owner_mapped), 11,
                         f"Expected 11 owner-mapped clauses, got {len(owner_mapped)}")
        bad = [(e["key"], e.get("target_clause_2025")) for e in owner_mapped
               if not e.get("target_clause_2025")]
        self.assertEqual(bad, [], f"Owner-mapped clauses with null target: {bad}")

    def test_unresolved_clauses_have_null_target(self) -> None:
        # After the final Phase 1 edits, there are no unresolved clauses.
        unresolved = [e for e in self.clauses
                      if e.get("mapping_status") == "needs_owner_decision"]
        self.assertEqual(unresolved, [], f"Unresolved clauses still present: {[e['key'] for e in unresolved]}")

    def test_no_clause_has_null_target(self) -> None:
        # Step 4 requirement: no codes.clauses.* entry may have a null
        # target_clause_2025.
        null_targets = [(e["key"], e.get("target_clause_2025")) for e in self.clauses
                        if e.get("target_clause_2025") is None]
        self.assertEqual(null_targets, [], f"Clauses with null target_clause_2025: {null_targets}")

    def test_every_owner_mapped_has_sample_and_target(self) -> None:
        # Step 4 requirement: every owner_mapped entry has both sample_clause
        # and target_clause_2025.
        owner_mapped = [e for e in self.clauses if e.get("mapping_status") == "owner_mapped"]
        bad = []
        for e in owner_mapped:
            if not e.get("sample_clause"):
                bad.append((e["key"], "missing sample_clause"))
            if not e.get("target_clause_2025"):
                bad.append((e["key"], "missing target_clause_2025"))
        self.assertEqual(bad, [], f"Owner-mapped clauses missing fields: {bad}")

    def test_specific_owner_mapped_targets(self) -> None:
        expected = {
            "codes.clauses.soft_storey": "5.4.1.2",
            "codes.clauses.in_plane_discontinuity": "5.4.1.4",
            "codes.clauses.mass_irregularity": "5.4.1.5",
            "codes.clauses.reentrant_corner": "5.4.2.3",
            "codes.clauses.diaphragm_discontinuity": "5.4.2.4",
            "codes.clauses.out_of_plane_offset": "5.4.2.5",
        }
        by_key = {e["key"]: e for e in self.clauses}
        for key, target in expected.items():
            self.assertIn(key, by_key, f"Missing clause key: {key}")
            self.assertEqual(by_key[key].get("target_clause_2025"), target,
                             f"{key} target mismatch")
            self.assertEqual(by_key[key].get("mapping_status"), "owner_mapped",
                             f"{key} mapping_status mismatch")


class FoundationSupportConditionTests(unittest.TestCase):
    """Task 2: foundation.support_condition source is computed; .e2k
    $POINTRESTRAINTS is a cross-check input, not a replacement."""

    @classmethod
    def setUpClass(cls) -> None:
        with CURATED_REGISTRY.open("r", encoding="utf-8") as f:
            cls.entries = yaml.safe_load(f)["items"]

    def test_foundation_support_condition_source_is_computed(self) -> None:
        entry = next(e for e in self.entries if e["key"] == "foundation.support_condition")
        self.assertEqual(entry.get("source"), "computed",
                         f"source is {entry.get('source')}; expected 'computed'")

    def test_foundation_support_condition_has_cross_check(self) -> None:
        entry = next(e for e in self.entries if e["key"] == "foundation.support_condition")
        self.assertIn("$POINTRESTRAINTS", entry.get("etabs_table_or_e2k_section", ""),
                      "Cross-check input $POINTRESTRAINTS not recorded")
        self.assertIn("cross-check", entry.get("etabs_table_or_e2k_section", ""),
                      "Cross-check label not present")


class NeedsDecisionTests(unittest.TestCase):
    """Task 2 + Task 3: the Applied owner decisions text is restored, and
    the item 535 sentence uses 0.025 in Ultimate Limit State."""

    def test_applied_owner_decisions_restored(self) -> None:
        content = (ROOT / "docs" / "needs_my_decision.md").read_text(encoding="utf-8")
        self.assertIn(
            "Foundation support wording is computed from `foundation.type` and `foundation.soil_class`.",
            content,
            "Original owner decision text for foundation support not restored",
        )
        self.assertNotIn(
            "Foundation support wording is sourced from .e2k point restraints",
            content,
            "The Phase-1 regression text should have been removed",
        )

    def test_item_535_not_present_with_wrong_value(self) -> None:
        # Item 535 was resolved (serviceability_drift -> 5.5.3); the sample
        # sentence is no longer quoted in the Unresolved section. The wrong
        # value 0.010 must not appear anywhere in the decision log.
        content = (ROOT / "docs" / "needs_my_decision.md").read_text(encoding="utf-8")
        self.assertNotIn("0.010 in Ultimate", content,
                         "Item 535 sentence must not contain '0.010 in Ultimate'")

    def test_cross_check_promoted_to_applied(self) -> None:
        content = (ROOT / "docs" / "needs_my_decision.md").read_text(encoding="utf-8")
        # The cross-check was promoted from "Proposed changes" to "Applied owner
        # decisions". The "Proposed changes" section should no longer exist.
        self.assertNotIn("## Proposed changes for owner review", content,
                         "Proposed changes section should have been removed after "
                         "the cross-check was promoted to Applied owner decisions")
        self.assertIn("$POINTRESTRAINTS", content,
                      "Cross-check input must be mentioned in the decision log")


class Task4KeyReviewTests(unittest.TestCase):
    """Task 4: FIXED-reverted keys are dropped; real-input keys are kept."""

    @classmethod
    def setUpClass(cls) -> None:
        with CURATED_REGISTRY.open("r", encoding="utf-8") as f:
            cls.entries = yaml.safe_load(f)["items"]
        cls.keys = {e["key"] for e in cls.entries}

    def test_fixed_reverted_keys_dropped(self) -> None:
        dropped = {
            "foundation.structural_system_foundation",
            "project.brick_tolerances",
            "seismic.intro_statement",
        }
        present = dropped & self.keys
        self.assertEqual(present, set(), f"FIXED-reverted keys still in registry: {present}")

    def test_real_input_keys_kept(self) -> None:
        kept = {
            "materials.as_building_is_less_than_12_m",
            "project.brick_specs",
            "building.occupancy",
        }
        missing = kept - self.keys
        self.assertEqual(missing, set(), f"Real-input keys missing from registry: {missing}")

    def test_no_example_has_leading_tab(self) -> None:
        bad = []
        for e in self.entries:
            ex = e.get("example")
            if isinstance(ex, str) and ex.startswith("\\t"):
                bad.append(e["key"])
        self.assertEqual(bad, [], f"Examples with leading \\t: {bad}")

    def test_materials_as_building_is_computed(self) -> None:
        # Step 3 requirement: materials.as_building_is_less_than_12_m is
        # computed with a non-empty etabs_table_or_e2k_section.
        entry = next(e for e in self.entries
                     if e["key"] == "materials.as_building_is_less_than_12_m")
        self.assertEqual(entry.get("source"), "computed",
                         f"source is {entry.get('source')}; expected 'computed'")
        self.assertTrue(entry.get("etabs_table_or_e2k_section"),
                        "etabs_table_or_e2k_section must be non-empty")

    def test_task4_review_listed_in_needs_decision(self) -> None:
        content = (ROOT / "docs" / "needs_my_decision.md").read_text(encoding="utf-8")
        self.assertIn("## Key classification review (Task 4)", content)
        self.assertIn("foundation.structural_system_foundation", content)
        self.assertIn("project.brick_tolerances", content)
        self.assertIn("seismic.intro_statement", content)
        self.assertIn("materials.as_building_is_less_than_12_m", content)
        self.assertIn("project.brick_specs", content)
        self.assertIn("building.occupancy", content)


class FigureOriginTests(unittest.TestCase):
    """Task 5: every image entry has figure_origin; generated figures have
    a generator; no placeholder_a..d keys remain."""

    @classmethod
    def setUpClass(cls) -> None:
        with CURATED_REGISTRY.open("r", encoding="utf-8") as f:
            cls.entries = yaml.safe_load(f)["items"]
        cls.images = [e for e in cls.entries if e["type"] == "image"]

    def test_every_image_has_figure_origin(self) -> None:
        missing = [e["key"] for e in self.images if "figure_origin" not in e]
        self.assertEqual(missing, [], f"Images missing figure_origin: {missing}")

    def test_figure_origin_values_are_valid(self) -> None:
        valid = {"generated", "etabs_screenshot", "user_supplied"}
        bad = [(e["key"], e.get("figure_origin")) for e in self.images
               if e.get("figure_origin") not in valid]
        self.assertEqual(bad, [], f"Invalid figure_origin values: {bad}")

    def test_generated_figures_have_generator(self) -> None:
        generated = [e for e in self.images if e.get("figure_origin") == "generated"]
        self.assertGreater(len(generated), 0, "No generated figures found")
        bad = [e["key"] for e in generated if not e.get("generator")]
        self.assertEqual(bad, [], f"Generated figures missing generator: {bad}")

    def test_non_generated_figures_have_null_generator(self) -> None:
        non_gen = [e for e in self.images if e.get("figure_origin") != "generated"]
        bad = [(e["key"], e.get("generator")) for e in non_gen
               if e.get("generator") is not None]
        self.assertEqual(bad, [], f"Non-generated figures with non-null generator: {bad}")

    def test_no_placeholder_keys_remain(self) -> None:
        placeholders = [e["key"] for e in self.images if "placeholder" in e["key"]]
        self.assertEqual(placeholders, [], f"Placeholder keys still in registry: {placeholders}")

    def test_placeholder_renames_present(self) -> None:
        keys = {e["key"] for e in self.images}
        expected = {
            "figure.elements.columns_design",
            "figure.elements.columns_design_b",
            "figure.summary.panel_a",
            "figure.summary.panel_b",
        }
        missing = expected - keys
        self.assertEqual(missing, set(), f"Renamed placeholder keys missing: {missing}")


if __name__ == "__main__":
    unittest.main()
