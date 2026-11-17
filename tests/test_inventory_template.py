from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lxml import etree
from tools import inventory_template as inventory


class InventoryTemplateTests(unittest.TestCase):
    def test_complex_and_simple_word_fields_are_inventory_only(self) -> None:
        xml = f'''<w:p xmlns:w="{inventory.W_NS}">
          <w:fldSimple w:instr=" PAGE "><w:r><w:t>4</w:t></w:r></w:fldSimple>
          <w:r><w:fldChar w:fldCharType="begin"/></w:r>
          <w:r><w:instrText xml:space="preserve"> REF _Ref123 </w:instrText></w:r>
          <w:r><w:fldChar w:fldCharType="separate"/></w:r>
          <w:r><w:t>Structural System</w:t></w:r>
          <w:r><w:fldChar w:fldCharType="end"/></w:r>
        </w:p>'''
        paragraph = etree.fromstring(xml.encode())
        fields = inventory.field_items(paragraph, section=1, parent_index=10)
        self.assertEqual([field["field"]["kind"] for field in fields], ["PAGE", "REF"])
        self.assertTrue(all(field["type"] == "field" for field in fields))
        self.assertTrue(all(inventory.classify(field)[0] == "COMPUTED" for field in fields))
        self.assertTrue(all("excluded" in inventory.classify(field)[1] for field in fields))

    def test_current_code_clause_becomes_variable(self) -> None:
        item = {
            "index": 41, "type": "paragraph", "style_name": "Body Text",
            "text": "As per Clause 3.2.1 of NBC 105:2025, the method applies.",
            "text_preview": "As per Clause 3.2.1 of NBC 105:2025, the method applies.",
            "context": {},
        }
        inventory.prepare_inventory([item])
        rule = item.get("template_rule", {})
        self.assertEqual(item["classification"], "VARIABLE")
        self.assertEqual(rule.get("action"), "clause_variable")
        self.assertEqual(rule.get("clause_key"), "codes.clauses.equivalent_static_method")
        entries = inventory.build_registry([item])
        clause = next(entry for entry in entries if entry["key"] == "codes.clauses.equivalent_static_method")
        self.assertEqual(clause["target_clause_2025"], "3.2.1")
        self.assertEqual(clause["mapping_status"], "sample_reference")

    def test_multi_value_building_template_preserves_original_words(self) -> None:
        text = ("brick walls. Each floor has a height of 3.175 meters. The building is laid out "
                "with a span of 4.216 meters horizontally (X-direction) and 10.058 meters vertically "
                "(Y-direction) between columns.")
        result = inventory.split_building_entries({"index": 165, "text": text})
        self.assertIsNotNone(result)
        entries, template = result
        self.assertEqual(len(entries), 4)
        self.assertIn("{{ building.infill_wall_material }} walls", template)
        self.assertIn("{{ building.story_height_m }} meters", template)
        self.assertIn("{{ building.span_x_m }} meters horizontally", template)
        self.assertIn("{{ building.span_y_m }} meters vertically", template)
        self.assertNotIn("{{ building.span_x_m }} pattern", template)

    def test_assignment_and_modal_templates_replace_values_safely(self) -> None:
        result = inventory.split_assignment_entries({
            "index": 384,
            "text": "k = 1.004; T = 0.508 s; Cd = 0.1458; Z = 0.35; soil C; I = 1.0; Rμ = 4; Ωu = 1.5.",
        })
        self.assertIsNotNone(result)
        entries, template = result
        self.assertGreaterEqual(len(entries), 8)
        self.assertIn("{{ seismic.distribution_exponent_k }}", template)
        self.assertIn("{{ seismic.design_period_used_s }} s", template)
        self.assertIn("{{ seismic.spectral_coefficient_cd }}", template)
        self.assertIn("soil {{ seismic.soil_class }}", template)
        self.assertNotIn("{{ seismic.{{", template)
        modal = inventory.split_modal_criteria({
            "index": 430,
            "text": "At least 90 percent total modal masses are considered in 12 modes.",
        })
        self.assertIsNotNone(modal)
        modal_entries, modal_template = modal
        self.assertIn("{{ codes.limits.modal_mass_participation_pct }}", modal_template)
        self.assertIn("{{ modal.modes_included_count }}", modal_template)
        self.assertEqual(len(modal_entries), 2)

    def test_structure_height_tuple_and_code_limits_split(self) -> None:
        height = inventory.split_structure_height({
            "index": 413,
            "text": "The total height of the building is 9.525 m (3 stories × 3.175 m).",
        })
        self.assertIsNotNone(height)
        height_entries, height_template = height
        self.assertEqual({entry["key"] for entry in height_entries}, {
            "building.total_height_m", "building.storeys_above_grade", "building.story_height_m",
        })
        self.assertIn("{{ building.total_height_m }}", height_template)
        self.assertIn("{{ building.storeys_above_grade }}", height_template)
        self.assertIn("{{ building.story_height_m }}", height_template)

        limits = inventory.split_code_limits({
            "index": 603,
            "text": "A soft storey has less than 70% adjacent stiffness or less than 80% average stiffness.",
        })
        self.assertIsNotNone(limits)
        limit_entries, limit_template = limits
        self.assertEqual([entry["example"] for entry in limit_entries], ["70", "80"])
        self.assertIn("{{ codes.limits.soft_storey_adjacent_stiffness_pct }}", limit_template)
        self.assertIn("{{ codes.limits.soft_storey_average_stiffness_pct }}", limit_template)

    def test_reinforcement_template_uses_valid_placeholders(self) -> None:
        item = {
            "index": 450,
            "text": "=1557/(355*355)*100% =1.24% <4% (OK)",
            "context": {"section_heading": "Check for Max Percentage Reinforcement Provided in Column"},
        }
        result = inventory.split_reinforcement_entries(item)
        self.assertIsNotNone(result)
        entries, template = result
        self.assertEqual(len(entries), 6)
        self.assertIn("{{ design.column.maximum_reinforcement.provided_reinforcement_area_mm2 }}", template)
        self.assertIn("{{ design.column.maximum_reinforcement.status }}", template)
        self.assertNotIn("{{ {{", template)

    def test_table_entry_has_unique_column_keys_and_row_metadata(self) -> None:
        item = {
            "index": 10, "type": "table", "classification": "TABLE", "text": "",
            "table": {"number": 7, "rows": 3, "columns": 2,
                      "header_row": ["Story", "Height (m)"], "cell_samples": [["Story", "Height (m)"]]},
            "context": {"caption": "Table 7: Load Assessment"},
        }
        entry = inventory.table_entry(item, set())
        self.assertEqual(entry["row_behavior"], "data-driven")
        self.assertEqual(entry["source"], "etabs_api")
        self.assertEqual(len(entry["columns"]), 2)
        self.assertEqual(len({column["key"] for column in entry["columns"]}), 2)
        self.assertEqual(entry["columns"][1]["unit"], "m")
        self.assertTrue(all(set(column) == {"key", "header", "unit", "format"} for column in entry["columns"]))

    def test_existing_curated_registry_is_redirected_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            curated = Path(tmp) / "placeholder_registry.yaml"
            curated.write_text("approved: true\n", encoding="utf-8")
            target = inventory.safe_registry_path(curated, curated)
            self.assertEqual(target.name, "placeholder_registry.generated.yaml")
            self.assertEqual(curated.read_text(encoding="utf-8"), "approved: true\n")
            new_target = Path(tmp) / "candidate.yaml"
            self.assertEqual(inventory.safe_registry_path(new_target, curated), new_target)

    def test_shared_key_does_not_reuse_another_items_sentence_template(self) -> None:
        item = {"index": 413, "type": "paragraph", "text": "Second source sentence.", "template_rule": {}}
        entries = [
            {"key": "building.storeys_above_grade", "inventory_item_index": 164,
             "inventory_item_indices": [164, 413], "sentence_template": "First source sentence."},
            {"key": "building.total_height_m", "inventory_item_index": 413,
             "inventory_item_indices": [413], "sentence_template": "Second source sentence with {{ building.total_height_m }}."},
        ]
        self.assertEqual(inventory.after_text_for_item(item, entries),
                         "Second source sentence with {{ building.total_height_m }}.")

    def test_metadata_and_hand_named_keys_are_complete_and_unique(self) -> None:
        items = [
            {"index": 0, "type": "paragraph", "style_name": "Body Text", "text": "A project building.", "text_preview": "A project building.", "context": {}},
            {"index": 1, "type": "field", "style_name": None, "text_preview": "PAGE", "field": {"instruction": "PAGE", "kind": "PAGE"}},
        ]
        inventory.prepare_inventory(items)
        entries = inventory.build_registry(items)
        keys = [entry["key"] for entry in entries]
        self.assertEqual(len(keys), len(set(keys)))
        manual = {
            "codes.edition", "codes.clauses.soft_storey", "codes.clauses.in_plane_discontinuity",
            "codes.clauses.mass_irregularity", "codes.clauses.reentrant_corner",
            "codes.clauses.diaphragm_discontinuity", "codes.clauses.out_of_plane_offset",
            "building.has_staircase", "foundation.type", "foundation.soil_class",
            "foundation.support_condition", "structural.system_type", "slab.type",
            "analysis.foundation_reaction_combination", "analysis.soft_storey_result",
            "analysis.in_plane_discontinuity_result", "analysis.mass_irregularity_result",
            "analysis.reentrant_corner_result",
        }
        self.assertTrue(manual.issubset(set(keys)))
        required_fields = {"description", "type", "unit", "format", "source", "required", "condition", "inventory_item_index", "example"}
        for entry in entries:
            self.assertTrue(required_fields.issubset(entry))
        field_indexes = {item["index"] for item in items if item["type"] == "field"}
        self.assertFalse(any(index in field_indexes for entry in entries
                             for index in entry.get("inventory_item_indices", [entry.get("inventory_item_index")])
                             if index is not None))


if __name__ == "__main__":
    unittest.main()
