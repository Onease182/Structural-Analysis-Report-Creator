#!/usr/bin/env python3
"""Curate config/placeholder_registry.generated.yaml into config/placeholder_registry.yaml.

Implements the eight-task review gate from the owner:

1. KEY NAMES: rename every key over 40 chars or with a sentence fragment /
   leading-digit segment; merge `code.*` into `codes.*`. Emit
   docs/key_rename_map.csv (old_key,new_key).
2. OVER-DETECTION: revert code-boilerplate `materials.*` text keys (IS/NBC
   quoted requirements with no project value) to FIXED; drop them from the
   curated registry and list them in the review.
3. SOURCES: re-assign source per data availability. Anything derivable from
   ETABS tables or the .e2k becomes etabs_api or e2k. Keep excel only for
   facts ETABS cannot know. Add `etabs_table_or_e2k_section` for every
   non-excel entry.
4. CLAUSES: keep the 6 unresolved NBC 105:2025 clause mappings as variables
   in the registry and surface them in docs/needs_my_decision.md with the
   sample sentence (do not invent target clauses).
5. FILES: write config/placeholder_registry.yaml (curated); the stale
   docs/placeholder_registry.yaml and docs/needs_my_decision.generated.md
   are removed via git rm outside this script.
6/7/8: the portable template rules, review summary, and tests live in their
own files; this script writes only the registry, the rename map, and the
short review summary.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

REPO = Path("/home/z/my-project/repo")
SRC = REPO / "config/placeholder_registry.generated.yaml"
DST_REGISTRY = REPO / "config/placeholder_registry.yaml"
DST_RENAME_MAP = REPO / "docs/key_rename_map.csv"
DST_REVIEW_SHORT = REPO / "docs/registry_review.md"
DST_REVIEW_FULL = REPO / "docs/registry_review_full.md"
DST_NEEDS_DECISION = REPO / "docs/needs_my_decision.md"

# ----------------------------------------------------------------------------
# 1. KEY RENAME MAP (old -> new)
# ----------------------------------------------------------------------------
RENAME_MAP: dict[str, str] = {
    # Merge code.* -> codes.* (singular -> plural group).
    "code.edition": "codes.edition",
    "code.clauses.soft_storey": "codes.clauses.soft_storey",
    "code.clauses.in_plane_discontinuity": "codes.clauses.in_plane_discontinuity",
    "code.clauses.mass_irregularity": "codes.clauses.mass_irregularity",
    "code.clauses.reentrant_corner": "codes.clauses.reentrant_corner",
    "code.clauses.diaphragm_discontinuity": "codes.clauses.diaphragm_discontinuity",
    "code.clauses.out_of_plane_offset": "codes.clauses.out_of_plane_offset",

    # Leading-digit segment (e.g. codes.clauses.5_6).
    "codes.clauses.5_6": "codes.clauses.eccentricity_intro",

    # Sentence-derived materials.* / project.* / seismic.* / foundation.* keys.
    "seismic.analysis_design_in_this_report_follow_codes": "seismic.intro_statement",
    "foundation.building_was_modeled_using_etabs_19_0": "foundation.modeling_software",
    "project.standard_rectangular_bricks_are_which_are_well": "project.brick_specs",
    "project.thick_walls_acceptable_tolerances_are_10_mm": "project.brick_tolerances",
    "project.fundamental_time_period_on_empirical_formula": "project.empirical_period_intro",
    "materials.minimum_grade_of_structural_concrete_shall_be": "materials.concrete_grade_min",
    "materials.thigh_strength_deformed_steel_bars_produced_by": "materials.rebar_tmt_description",
    "materials.steel_grade_of_fe500_has_been_in": "materials.rebar_grade_used",
    "materials.minimum_thickness_is_half_brick_while_maximum": "materials.wall_thickness_range",
    "materials.tgrade_fe_415_or_less_or": "materials.rebar_grade_options_a",
    "table.design.structural_system_and_foundation": "table.design.system_foundation",
    "table.seismic.empirical_period_calculation": "table.seismic.empirical_period",
    "table.seismic.vertical_force_distribution": "table.seismic.vertical_force_dist",
    "table.modal.periods_and_mass_participation": "table.modal.periods_mass_part",
    "design.overstrength_factor_ultimate_omega_u": "design.overstrength_ultimate",
    "modal.rayleigh_time_period_x_direction_eqx_uls": "modal.rayleigh_period_x_uls",
    "modal.rayleigh_time_period_y_direction_eqy_uls": "modal.rayleigh_period_y_uls",
    "modal.tbase_shear_etabs_240_02_kn": "modal.base_shear_etabs",
    "codes.clauses.vertical_force_distribution": "codes.clauses.vertical_force_dist",
    "codes.limits.modal_mass_participation_pct": "codes.limits.modal_mass_part_pct",
    "codes.limits.maximum_story_deflection_ratio": "codes.limits.max_deflection_ratio",
    "codes.limits.serviceability_story_drift_ratio": "codes.limits.sls_drift_ratio",
    "codes.clauses.structural_irregularity_general": "codes.clauses.irregularity_general",
    "codes.limits.torsional_displacement_ratio": "codes.limits.torsional_disp_ratio",
    "codes.limits.soft_storey_adjacent_stiffness_pct": "codes.limits.soft_storey_adj_pct",
    "codes.limits.soft_storey_average_stiffness_pct": "codes.limits.soft_storey_avg_pct",
    "codes.limits.mass_irregularity_effective_mass_difference_pct": "codes.limits.mass_irregularity_diff_pct",
    "codes.limits.reentrant_corner_projection_pct": "codes.limits.reentrant_proj_pct",
    "codes.limits.diaphragm_stiffness_change_pct": "codes.limits.diaphragm_stiffness_pct",

    # Figure keys > 40 chars or with "t" slug artifact (from "\t..." alt text).
    "figure.project.structural_analysis_design_report": "figure.project.cover",
    "figure.materials.material_property_concrete": "figure.materials.concrete",
    "figure.irregularity.eqxeqxdesign_eccentricity_edi_y_esi_y_0": "figure.irregularity.eqx_eccentricity",
    "figure.irregularity.eqxeqxdesign_eccentricity_edi_y_esi_y_0_panel_b": "figure.irregularity.eqx_eccentricity_b",
    "figure.irregularity.cresi_ycmedi_ycm_cresi_ycmedi_ycm_5": "figure.irregularity.acc_eccentricity",
    "figure.irregularity.cresi_ycmedi_ycm_cresi_ycmedi_ycm_5_panel_b": "figure.irregularity.acc_eccentricity_b",
    "figure.loads.wall_load_first_floor_in_kn_m": "figure.loads.wall_first",
    "figure.loads.wall_load_second_floor_in_kn_m": "figure.loads.wall_second",
    "figure.loads.wall_load_third_floor_in_kn_m": "figure.loads.wall_third",
    "figure.building.floor_finish_first_floor_in_kn_m2": "figure.building.finish_first",
    "figure.building.floor_finish_second_floor_in_kn_m2": "figure.building.finish_second",
    "figure.loads.live_load_first_floor_in_kn_m2": "figure.loads.live_first",
    "figure.loads.live_load_second_floor_in_kn_m2": "figure.loads.live_second",
    "figure.loads.roof_live_second_floor_in_kn_m2": "figure.loads.roof_live_second",
    "figure.loads.roof_live_top_floor_in_kn_m2": "figure.loads.roof_live_top",
    "figure.loads.load_cases_considered_in_software": "figure.loads.cases",
    "figure.project.mass_sources_considered_panel_b": "figure.project.mass_sources_b",
    "figure.modal.vertical_distribution_of_uls_seismic_forces_nbc": "figure.modal.uls_force_distribution",
    "figure.foundation.foundation_reaction_1_5dl_1_5ll": "figure.foundation.reaction_uls",
    "figure.foundation.foundation_reaction_1_5dl_1_5ll_panel_b": "figure.foundation.reaction_uls_b",
    "figure.foundation.foundation_reaction_1_5dl_1_5ll_panel_c": "figure.foundation.reaction_uls_c",
    "figure.foundation.tdesign_of_foundations": "figure.foundation.design_main",
    "figure.foundation.tdesign_of_foundations_panel_b": "figure.foundation.design_b",
    "figure.foundation.tdesign_of_foundations_panel_c": "figure.foundation.design_c",
    "figure.foundation.tdesign_of_foundations_panel_d": "figure.foundation.design_d",
    "figure.staircase.tdesign_of_staircases": "figure.staircase.design_main",
    "figure.staircase.tdesign_of_staircases_panel_b": "figure.staircase.design_b",
    "figure.staircase.tdesign_of_staircases_panel_c": "figure.staircase.design_c",
    "figure.drift.tdisplacement_drift": "figure.drift.displacement",
    "figure.drift.tdisplacement_drift_panel_b": "figure.drift.displacement_b",
    "figure.irregularity.torsional_irregularity": "figure.irregularity.torsional",
    "figure.irregularity.in_plane_discontinuity": "figure.irregularity.in_plane",
    "figure.irregularity.diaphragm_discontinuity": "figure.irregularity.diaphragm",
    "figure.summary.tdesign_summary": "figure.summary.design",
    "figure.elements.tdesign_of_beams": "figure.elements.beams_design",
    "figure.elements.tdesign_of_beams_panel_b": "figure.elements.beams_design_b",
    "figure.project.t": "figure.project.placeholder_a",
    "figure.project.t_panel_b": "figure.project.placeholder_b",
    "figure.project.t_panel_c": "figure.project.placeholder_c",
    "figure.project.t_panel_d": "figure.project.placeholder_d",
    "figure.elements.required_longitudinal_reinforcement_mm_in_beams_columns": "figure.elements.rebar_grid_a",
    "figure.elements.required_longitudinal_reinforcement_mm_in_beams_columns_panel_b": "figure.elements.rebar_grid_b",
    "figure.elements.required_longitudinal_reinforcement_mm_in_beams_at": "figure.elements.rebar_story1",
    "figure.elements.required_longitudinal_reinforcement_mm_in_beams_at_panel_b": "figure.elements.rebar_story2",
    "figure.elements.required_longitudinal_reinforcement_mm_in_beams_at_panel_c": "figure.elements.rebar_story3",

    # Reinforcement check sub-keys (>40 chars).
    "design.column.maximum_reinforcement.provided_reinforcement_area_mm2": "design.column.max_rebar_area_mm2",
    "design.column.maximum_reinforcement.section_width_mm": "design.column.max_section_width_mm",
    "design.column.maximum_reinforcement.section_depth_mm": "design.column.max_section_depth_mm",
    "design.column.maximum_reinforcement.provided_pct": "design.column.max_provided_pct",
    "design.column.maximum_reinforcement.limit_pct": "design.column.max_limit_pct",
    "design.column.maximum_reinforcement.status": "design.column.max_status",
    "design.column.minimum_reinforcement.provided_pct": "design.column.min_provided_pct",
    "design.column.minimum_reinforcement.limit_pct": "design.column.min_limit_pct",
    "design.column.minimum_reinforcement.status": "design.column.min_status",
    "design.beam.maximum_reinforcement.provided_reinforcement_area_mm2": "design.beam.max_rebar_area_mm2",
    "design.beam.maximum_reinforcement.section_width_mm": "design.beam.max_section_width_mm",
    "design.beam.maximum_reinforcement.section_depth_mm": "design.beam.max_section_depth_mm",
    "design.beam.maximum_reinforcement.provided_pct": "design.beam.max_provided_pct",
    "design.beam.maximum_reinforcement.limit_pct": "design.beam.max_limit_pct",
    "design.beam.minimum_reinforcement.provided_pct": "design.beam.min_provided_pct",
    "design.beam.minimum_reinforcement.limit_pct": "design.beam.min_limit_pct",
}

# ----------------------------------------------------------------------------
# 2. FIXED-REVERTED BOILERPLATE KEYS (drop from curated registry)
# ----------------------------------------------------------------------------
FIXED_REVERTED: dict[str, str] = {
    "materials.concrete_grade_min":
        "Minimum grade of structural concrete shall be M20, but M25 for buildings more than 12 m in height.",
    "materials.rebar_tmt_description":
        "High strength deformed steel bars produced by thermo-mechanical treatment process having elongation capacity of more than 15 percent; e.g. Grade Fe 500 and Fe 550.",
    "materials.wall_thickness_range":
        "The minimum thickness is half-brick, while the maximum thickness is one brick. Internal walls have a thickness of up to 115 mm for brick walls or equivalent materials, while external walls have a thickness of up to 230 mm for brick walls or equivalent materials.",
    "materials.rebar_grade_options_a":
        "Grade Fe 415 or less; or",
}
# Map the original (pre-rename) boilerplate keys to the new names so the
# rename CSV records the transition even when the new key is reverted to FIXED.
FIXED_REVERTED_OLD_KEYS: dict[str, str] = {
    "materials.tgrade_fe_415_or_less_or": "materials.rebar_grade_options_a",
    "materials.minimum_grade_of_structural_concrete_shall_be": "materials.concrete_grade_min",
    "materials.thigh_strength_deformed_steel_bars_produced_by": "materials.rebar_tmt_description",
    "materials.minimum_thickness_is_half_brick_while_maximum": "materials.wall_thickness_range",
}

# ----------------------------------------------------------------------------
# 3. SOURCE REASSIGNMENT  (key -> (source, etabs_table_or_e2k_section))
# ----------------------------------------------------------------------------
SOURCE_REASSIGN: dict[str, tuple[str, str]] = {
    "building.storeys_above_grade": ("e2k", "$STORYDATA"),
    "building.story_height_m": ("e2k", "$STORYDATA"),
    "building.span_x_m": ("e2k", "$FRAMEOBJCONN"),
    "building.span_y_m": ("e2k", "$FRAMEOBJCONN"),
    "building.total_height_m": ("e2k", "$STORYDATA"),
    "building.primary_frame_material": ("etabs_api", "Material Properties + Frame Section Assignments"),
    "materials.rebar_grade_used": ("etabs_api", "Material Properties (rebar)"),
    "modal.modes_included_count": ("etabs_api", "Modal Load Case"),
    "modal.base_shear_etabs": ("etabs_api", "Base Reactions / Story Forces"),
    "foundation.support_condition": ("e2k", "$POINTRESTRAINTS"),
    "slab.type": ("e2k", "$SLABSECTIONS / Shell Section Assignments"),
    "structural.system_type": ("etabs_api", "Frame Section Assignments + Connectivity"),
    "figure.materials.concrete": ("etabs_api", "Material Properties (concrete)"),
    "figure.loads.cases": ("etabs_api", "Load Patterns / Load Cases"),
    "figure.project.mass_sources_b": ("etabs_api", "Mass Source"),
    "figure.project.mass_sources_considered": ("etabs_api", "Mass Source"),
    "figure.modal.uls_force_distribution": ("computed", "Vertical distribution from ETABS story forces"),
    "figure.elements.beams_design": ("etabs_api", "Beam Design Output"),
    "figure.elements.beams_design_b": ("etabs_api", "Beam Design Output"),
    "figure.elements.design_for_frames": ("etabs_api", "Concrete Frame Design Output"),
    "figure.elements.rebar_grid_a": ("etabs_api", "Beam/Column Reinforcing Output"),
    "figure.elements.rebar_grid_b": ("etabs_api", "Beam/Column Reinforcing Output"),
    "figure.elements.rebar_story1": ("etabs_api", "Beam Reinforcing Output (Story 1)"),
    "figure.elements.rebar_story2": ("etabs_api", "Beam Reinforcing Output (Story 2)"),
    "figure.elements.rebar_story3": ("etabs_api", "Beam Reinforcing Output (Story 3)"),
    "figure.foundation.reaction_uls": ("etabs_api", "Foundation Reactions (combo 1.5DL+1.5LL)"),
    "figure.foundation.reaction_uls_b": ("etabs_api", "Foundation Reactions (combo 1.5DL+1.5LL)"),
    "figure.foundation.reaction_uls_c": ("etabs_api", "Foundation Reactions (combo 1.5DL+1.5LL)"),
    "figure.foundation.design_main": ("etabs_api", "Foundation Design Output"),
    "figure.foundation.design_b": ("etabs_api", "Foundation Design Output"),
    "figure.foundation.design_c": ("etabs_api", "Foundation Design Output"),
    "figure.foundation.design_d": ("etabs_api", "Foundation Design Output"),
    "figure.drift.displacement": ("etabs_api", "Story Displacements"),
    "figure.drift.displacement_b": ("etabs_api", "Story Displacements"),
    "figure.irregularity.eqx_eccentricity": ("etabs_api", "Load Case Eccentricity (EQX)"),
    "figure.irregularity.eqx_eccentricity_b": ("etabs_api", "Load Case Eccentricity (EQX)"),
    "figure.irregularity.acc_eccentricity": ("etabs_api", "Accidental Eccentricity"),
    "figure.irregularity.acc_eccentricity_b": ("etabs_api", "Accidental Eccentricity"),
    "figure.irregularity.torsional": ("etabs_api", "Story Displacements (max/avg corner)"),
    "figure.irregularity.soft_story": ("etabs_api", "Story Stiffness"),
    "figure.irregularity.soft_story_panel_b": ("etabs_api", "Story Stiffness"),
    "figure.irregularity.in_plane": ("etabs_api", "Frame Connectivity"),
    "figure.irregularity.re_entrant_corners": ("etabs_api", "Plan Geometry"),
    "figure.irregularity.diaphragm": ("etabs_api", "Diaphragm CMs / Story Mass"),
    "figure.irregularity.out_of_plane_offset": ("etabs_api", "Frame Connectivity"),
    "table.elements.sizes_and_materials": ("etabs_api", "Frame Section Assignments + Material Properties"),
    "table.loads.load_assessment": ("etabs_api", "Load Patterns + Floor Loads"),
    "table.modal.periods_mass_part": ("etabs_api", "Modal Participating Mass Ratios"),
    "table.design.slab_design_output": ("etabs_api", "Slab Design Output"),
    "table.drift.uls_displacement_figures_x_y": ("etabs_api", "Story Displacements (ULS)"),
    "table.drift.sls_displacement_figures_x_y": ("etabs_api", "Story Displacements (SLS)"),
    "table.drift.uls_story_drift_figures_x_y": ("etabs_api", "Story Drifts (ULS)"),
    "table.drift.sls_story_drift_figures_x_y": ("etabs_api", "Story Drifts (SLS)"),
    "analysis.foundation_reaction_combination": ("etabs_api", "Load Combinations"),
}

# ----------------------------------------------------------------------------
# 4. UNRESOLVED NBC 105:2025 CLAUSES
# ----------------------------------------------------------------------------
UNRESOLVED_CLAUSES: list[dict[str, Any]] = [
    {
        "item_index": 208,
        "key": "codes.clauses.material_properties",
        "sample_clause": "2.1",
        "sample_sentence":
            "According to NBC105:2020, The material should be taken as per Cl.2.1.",
        "question": "Which NBC 105:2025 clause replaces the sample's Cl. 2.1 (material properties)?",
    },
    {
        "item_index": 418,
        "key": "codes.clauses.load_combinations",
        "sample_clause": "3.6.1",
        "sample_sentence":
            "When lateral load resisting elements are oriented along mutually orthogonal horizontal directions, the structure system is considered to be parallel and load combinations as specified in clause 3.6.1 of NBC 105:2020 is used for design.",
        "question": "Which NBC 105:2025 clause replaces the sample's Cl. 3.6.1 (parallel-system load combinations)?",
    },
    {
        "item_index": 533,
        "key": "codes.clauses.serviceability_drift",
        "sample_clause": "5.6.3",
        "sample_sentence":
            "5.6.3 of NBC 105:2077 is proposed to be used.",
        "question": "Which NBC 105:2025 clause replaces the sample's NBC 105:2077 Cl. 5.6.3 (serviceability drift)?",
    },
    {
        "item_index": 535,
        "key": "codes.clauses.serviceability_drift",
        "sample_clause": "5.6.3",
        "sample_sentence":
            "5.6.3 of NBC 105:2077 is applied. The maximum deflection in any story due to the minimum specified design lateral force, with partial load factor of 1.0 shall not exceed 0.006 times the story height. Furthermore, the drift shall not exceed 0.006 in Serviceability and 0.010 in Ultimate limit states.",
        "question": "Which NBC 105:2025 clause replaces the sample's NBC 105:2077 Cl. 5.6.3 (applied drift limit)?",
    },
    {
        "item_index": 591,
        "key": "codes.clauses.irregularity_general",
        "sample_clause": "5.5",
        "sample_sentence":
            "One of the basic virtues of earthquake resistant design of structures is that the structure shall be regular as much as possible. It is observed that the structures with simple and regular configurations suffer much less damage during a la…",
        "question": "Which NBC 105:2025 clause replaces the sample's Cl. 5.5 (general structural irregularity)?",
    },
    {
        "item_index": 593,
        "key": "codes.clauses.torsional_irregularity",
        "sample_clause": "5.5.2.1",
        "sample_sentence":
            "As per the clause 5.5.2.1 of NBC 105:2020, torsion irregularity is considered to exist when the maximum horizontal displacement of any floor in the direction of the lateral force, applied at the centre of mass, at one end of the storey is…",
        "question": "Which NBC 105:2025 clause replaces the sample's Cl. 5.5.2.1 (torsional irregularity)?",
    },
]


def validate_key(key: str) -> list[str]:
    violations: list[str] = []
    if len(key) > 40:
        violations.append(f"length>{40}:{len(key)}")
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


def load_source() -> list[dict[str, Any]]:
    with SRC.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["items"]


def rename_key(old: str) -> str:
    return RENAME_MAP.get(old, old)


def reassign_source(entry: dict[str, Any]) -> None:
    """Apply SOURCE_REASSIGN and fill etabs_table_or_e2k_section for every
    non-excel entry. Excel entries do not carry the column (per the owner spec)."""
    key = entry["key"]
    if key in SOURCE_REASSIGN:
        source, table = SOURCE_REASSIGN[key]
        entry["source"] = source
        entry["etabs_table_or_e2k_section"] = table
    elif entry.get("source") in {"etabs_api", "e2k"}:
        # Default etabs/e2k keys without an explicit table mapping get None
        # rather than a missing column, so the column is always present on
        # non-excel rows.
        entry["etabs_table_or_e2k_section"] = None
    elif entry.get("source") == "computed":
        # Computed entries are derived from other registry values; they have
        # no direct ETABS/.e2k table, so the column is present but null.
        entry["etabs_table_or_e2k_section"] = None
    # Excel entries: leave the field absent so the column only applies to
    # non-excel keys (per the owner spec).


def curate_entries(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    curated: list[dict[str, Any]] = []
    dropped_fixed: list[str] = []
    seen_new_keys: set[str] = set()

    for item in items:
        old_key = item["key"]
        new_key = rename_key(old_key)

        violations = validate_key(new_key)
        if violations:
            raise ValueError(f"New key '{new_key}' (from '{old_key}') violates: {violations}")

        if new_key in FIXED_REVERTED:
            dropped_fixed.append(new_key)
            continue

        item = dict(item)
        item["key"] = new_key
        for col in item.get("columns", []) or []:
            if col["key"].startswith(old_key + "."):
                col["key"] = new_key + col["key"][len(old_key):]

        reassign_source(item)

        if new_key in seen_new_keys:
            raise ValueError(f"Duplicate new key after rename: {new_key}")
        seen_new_keys.add(new_key)

        curated.append(item)

    return curated, dropped_fixed


def write_rename_map_csv() -> None:
    DST_RENAME_MAP.parent.mkdir(parents=True, exist_ok=True)
    with DST_RENAME_MAP.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["old_key", "new_key"])
        for old, new in sorted(RENAME_MAP.items()):
            writer.writerow([old, new])
        for old, new in sorted(FIXED_REVERTED_OLD_KEYS.items()):
            writer.writerow([old, f"{new} (FIXED-reverted, dropped from registry)"])


def write_curated_registry(entries: list[dict[str, Any]]) -> None:
    DST_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# Curated placeholder registry.\n"
        "# Generated from config/placeholder_registry.generated.yaml by\n"
        "# scripts/curate_registry.py. Owner review gate applies: do not\n"
        "# build a master template from this file until the unresolved\n"
        "# NBC 105:2025 clause mappings in docs/needs_my_decision.md are\n"
        "# answered.\n"
    )
    with DST_REGISTRY.open("w", encoding="utf-8") as f:
        f.write(header)
        yaml.safe_dump({"items": entries}, f, sort_keys=False,
                       allow_unicode=True, default_flow_style=False, width=100)


def write_review_short(entries: list[dict[str, Any]], dropped_fixed: list[str]) -> None:
    type_counts = Counter(e.get("type") for e in entries)
    source_counts = Counter(e.get("source") for e in entries)
    group_counts: Counter[str] = Counter()
    for e in entries:
        group_counts[e["key"].split(".")[0]] += 1

    lines: list[str] = [
        "# Placeholder Registry Review (Curated)",
        "",
        "**Review gate:** this curated registry is owned by the structural engineer. "
        "Do not generate a production master template until the six unresolved "
        "NBC 105:2025 clause mappings in `docs/needs_my_decision.md` are answered.",
        "",
        f"Curated entries: **{len(entries)}**.",
        f"Types: {', '.join(f'{k}: {v}' for k, v in sorted(type_counts.items()))}.",
        f"Sources: {', '.join(f'{k}: {v}' for k, v in sorted(source_counts.items()))}.",
        "",
        "## Counts per group",
        "",
    ]
    for group, count in sorted(group_counts.items()):
        lines.append(f"- `{group}`: {count}")
    lines += ["", "## Counts per source", ""]
    for source, count in sorted(source_counts.items()):
        lines.append(f"- `{source}`: {count}")
    lines += [
        "",
        "## Key rename map",
        "",
        "Full map in `docs/key_rename_map.csv`. Highlights:",
        "",
        "- `code.*` merged into `codes.*` (7 keys).",
        "- Every key longer than 40 characters renamed (77 keys).",
        "- Every key whose last segment began with a digit renamed (e.g. `codes.clauses.5_6`).",
        "- Every key whose last segment was a `\\t` slug artifact renamed (`tdesign_of_*`, "
        "`tdisplacement_*`, `tbase_*`, `figure.project.t`).",
        "",
        "## FIXED-reverted boilerplate (dropped from the registry)",
        "",
    ]
    for key in dropped_fixed:
        text = FIXED_REVERTED.get(key, "")
        preview = text[:120] + ("…" if len(text) > 120 else "")
        lines.append(f"- `{key}` — {preview}")
    lines += [
        "",
        "## Unresolved NBC 105:2025 clause mappings",
        "",
        "These six clause variables remain in the registry as `codes.clauses.*` text "
        "entries. The owner must answer the questions in `docs/needs_my_decision.md` "
        "before the template is built.",
        "",
    ]
    for entry in UNRESOLVED_CLAUSES:
        lines.append(f"- item {entry['item_index']} — `{entry['key']}` (sample Cl. {entry['sample_clause']})")
    lines += [
        "",
        "## Files",
        "",
        "- `config/placeholder_registry.yaml` — the curated registry.",
        "- `docs/key_rename_map.csv` — old_key,new_key for every rename.",
        "- `docs/registry_review_full.md` — the full before/after listing (Phase 1 review).",
        "- `docs/needs_my_decision.md` — owner decision log + the six unresolved clause questions.",
        "- `config/template_rules.yaml` — heading/text-anchored template rules.",
        "- `tests/test_registry_keys.py` — key naming and required-field tests.",
        "",
        "## Source priority",
        "",
        "ETABS API/CSV > `.e2k` > Excel > computed. Disagreements are recorded, "
        "never silently resolved. Non-excel entries carry an "
        "`etabs_table_or_e2k_section` field naming the source table or `.e2k` section.",
        "",
    ]
    DST_REVIEW_SHORT.parent.mkdir(parents=True, exist_ok=True)
    DST_REVIEW_SHORT.write_text("\n".join(lines), encoding="utf-8")


def write_needs_decision() -> None:
    lines: list[str] = [
        "# Needs My Decision",
        "",
        "This file is the single owner decision log. The previous generated copy at "
        "`docs/needs_my_decision.generated.md` has been removed and merged here.",
        "",
        "## Applied owner decisions",
        "",
        "- TOC entries for B.3, F.7, and the irregularity checks are `FIXED`; "
        "F.8 is fixed but controlled by `building.has_staircase`.",
        "- When `has_staircase` is false, remove the staircase heading and the sample "
        "content range through the empty Heading 5; do not alter the DOCX during inventory.",
        "- Foundation support wording is sourced from .e2k point restraints "
        "(`foundation.support_condition`, `etabs_table_or_e2k_section=$POINTRESTRAINTS`).",
        "- Clause citations are variables: the sample 2020 clauses map to NBC 105:2025 "
        "clauses recorded in the registry. Six mappings remain unresolved (see below).",
        "- In-plane and mass-irregularity conclusion paragraphs are computed variants "
        "and restyled to Body Text; the re-entrant conclusion has rectangular/no-re-entrant "
        "variants.",
        "- The foundation reaction image is retained; only its combination text is variable.",
        "",
        "## Unresolved NBC 105:2025 clause mappings",
        "",
        "Do not invent target clauses. Answer the question for each entry; the curated "
        "registry will then be updated and the corresponding `codes.clauses.*` entry "
        "will receive a `target_clause_2025` value.",
        "",
    ]
    for entry in UNRESOLVED_CLAUSES:
        lines += [
            f"- **Item {entry['item_index']} — `{entry['key']}` (sample Cl. {entry['sample_clause']})**",
            f"  - Sample sentence: \"{entry['sample_sentence']}\"",
            f"  - Question for the owner: {entry['question']}",
            "",
        ]
    lines += [
        "## Classification policy",
        "",
        "The tool classifies headings and general method/boilerplate as `FIXED`, "
        "project facts as `VARIABLE`, data-driven tables as `TABLE`, replacement "
        "figures as `IMAGE`, derived results as `COMPUTED`, and condition-specific "
        "content as `CONDITIONAL`. Review all non-FIXED items before using the "
        "registry to drive report generation.",
        "",
    ]
    DST_NEEDS_DECISION.parent.mkdir(parents=True, exist_ok=True)
    DST_NEEDS_DECISION.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    items = load_source()
    curated, dropped_fixed = curate_entries(items)
    write_rename_map_csv()
    write_curated_registry(curated)
    write_review_short(curated, dropped_fixed)
    write_needs_decision()
    print(f"[OK] Curated registry: {DST_REGISTRY} ({len(curated)} entries)")
    print(f"[OK] Rename map: {DST_RENAME_MAP} ({len(RENAME_MAP)} renames)")
    print(f"[OK] Review summary: {DST_REVIEW_SHORT}")
    print(f"[OK] Owner decisions: {DST_NEEDS_DECISION}")
    print(f"[OK] FIXED-reverted boilerplate dropped: {len(dropped_fixed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
