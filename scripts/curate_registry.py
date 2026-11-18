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
    "figure.project.t": "figure.elements.columns_design",
    "figure.project.t_panel_b": "figure.elements.columns_design_b",
    "figure.project.t_panel_c": "figure.summary.panel_a",
    "figure.project.t_panel_d": "figure.summary.panel_b",
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
    # Task 3: computed narrative from building.total_height_m (e2k $STORYDATA)
    # and the concrete grade from ETABS Material Properties.
    "materials.as_building_is_less_than_12_m": ("computed", "$STORYDATA (height) + Material Properties (concrete grade)"),
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
            "5.6.3 of NBC 105:2077 is applied. The maximum deflection in any story due to the minimum specified design lateral force, with partial load factor of 1.0 shall not exceed 0.006 times the story height. Furthermore, the drift shall not exceed 0.006 in Serviceability Limit State and 0.025 in Ultimate Limit State case.",
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


# ============================================================================
# Phase 1 continuation — regression fixes (Tasks 1-5)
# ============================================================================

# ----------------------------------------------------------------------------
# 1b. CLAUSE FIELD METADATA (Task 1)
# ----------------------------------------------------------------------------
# Every codes.clauses.* entry gets:
#   target_clause_2025 : str | None  (null where unresolved)
#   sample_clause      : str         (just the sample clause number)
#   mapping_status     : str         (owner_mapped | sample_reference | needs_owner_decision)
# The example field is set to null; the sample clause lives in sample_clause.
CLAUSE_MAPPINGS: dict[str, dict[str, Any]] = {
    # Owner-approved mappings (6 clauses from the original Phase 1 OWNER_CLAUSE_MAP).
    "codes.clauses.soft_storey":             {"sample_clause": "5.5.1.2", "target_clause_2025": "5.4.1.2", "mapping_status": "owner_mapped"},
    "codes.clauses.in_plane_discontinuity":  {"sample_clause": "5.5.1.4", "target_clause_2025": "5.4.1.4", "mapping_status": "owner_mapped"},
    "codes.clauses.mass_irregularity":       {"sample_clause": "5.5.1.5", "target_clause_2025": "5.4.1.5", "mapping_status": "owner_mapped"},
    "codes.clauses.reentrant_corner":        {"sample_clause": "5.5.2.2", "target_clause_2025": "5.4.2.3", "mapping_status": "owner_mapped"},
    "codes.clauses.diaphragm_discontinuity": {"sample_clause": "5.5.2.3", "target_clause_2025": "5.4.2.4", "mapping_status": "owner_mapped"},
    "codes.clauses.out_of_plane_offset":     {"sample_clause": "5.5.2.4", "target_clause_2025": "5.4.2.5", "mapping_status": "owner_mapped"},
    # Sample-reference mappings (the sample cites a clause that is the same in 2025).
    "codes.clauses.eccentricity_intro":       {"sample_clause": "5.6",   "target_clause_2025": "5.6",   "mapping_status": "sample_reference"},
    "codes.clauses.vertical_force_dist":      {"sample_clause": "6.3",   "target_clause_2025": "6.3",   "mapping_status": "sample_reference"},
    "codes.clauses.spectral_shape_factor":    {"sample_clause": "4.1.2", "target_clause_2025": "4.1.2", "mapping_status": "sample_reference"},
    "codes.clauses.seismic_zoning_factor":    {"sample_clause": "4.1.4", "target_clause_2025": "4.1.4", "mapping_status": "sample_reference"},
    "codes.clauses.importance_factor":        {"sample_clause": "4.1.5", "target_clause_2025": "4.1.5", "mapping_status": "sample_reference"},
    "codes.clauses.equivalent_static_method": {"sample_clause": "3.2.1", "target_clause_2025": "3.2.1", "mapping_status": "sample_reference"},
    "codes.clauses.modal_mass_participation": {"sample_clause": "7.3",   "target_clause_2025": "7.3",   "mapping_status": "sample_reference"},
    # Owner-approved mappings — final Phase 1 decisions (all 5 previously
    # unresolved keys are now resolved; 6 clause questions, 5 distinct keys).
    "codes.clauses.material_properties":      {"sample_clause": "2.1",     "target_clause_2025": "Annex A, Cl. 2.1", "mapping_status": "owner_mapped"},
    "codes.clauses.load_combinations":        {"sample_clause": "3.6.1",   "target_clause_2025": "3.6.1",           "mapping_status": "owner_mapped"},
    "codes.clauses.serviceability_drift":     {"sample_clause": "5.6.3",   "target_clause_2025": "5.5.3",           "mapping_status": "owner_mapped"},
    "codes.clauses.irregularity_general":     {"sample_clause": "5.5",     "target_clause_2025": "5.4",             "mapping_status": "owner_mapped"},
    "codes.clauses.torsional_irregularity":   {"sample_clause": "5.5.2.1", "target_clause_2025": "5.4.2.1",         "mapping_status": "owner_mapped"},
}

# ----------------------------------------------------------------------------
# 2. FOUNDATION SUPPORT CONDITION (Task 2)
# ----------------------------------------------------------------------------
# The owner decision says the wording is computed from foundation.type and
# foundation.soil_class. .e2k $POINTRESTRAINTS is an ADDITIONAL cross-check
# input, not a replacement. Source is therefore `computed`; the
# etabs_table_or_e2k_section field names the cross-check input.
FOUNDATION_SUPPORT_OVERRIDE: dict[str, Any] = {
    "source": "computed",
    "etabs_table_or_e2k_section": "$POINTRESTRAINTS (cross-check input)",
    "condition": "Computed from foundation.type and foundation.soil_class per owner decision. .e2k $POINTRESTRAINTS provides a cross-check input.",
}

# ----------------------------------------------------------------------------
# 4. TASK-4 KEY CLASSIFICATIONS
# ----------------------------------------------------------------------------
# FIXED-reverted keys are dropped from the registry and listed in the review.
# Real-input keys keep VARIABLE.
TASK4_FIXED_REVERTED: dict[str, str] = {
    "foundation.structural_system_foundation":
        "Table 3: Structural System & Foundation (table caption heading; the table itself is table.design.system_foundation)",
    "project.brick_tolerances":
        "For thick walls, acceptable tolerances are -10 mm on length, -5 mm on width, and ±3 mm on thickness. (standard spec boilerplate; no project value)",
    "seismic.intro_statement":
        "The analysis and design in this report follow the codes and references listed below. Seismic loading, analysis and ductile detailing follow NBC 105:2025. (intro boilerplate; no project value)",
}
TASK4_REAL_INPUT: dict[str, str] = {
    "materials.as_building_is_less_than_12_m":
        "Real input / computed narrative. Project facts: height <12 m (from e2k $STORYDATA), grade M20 (from ETABS Material Properties). The sentence is computed from those facts.",
    "project.brick_specs":
        "Real input. Material spec with project values: crushing strength 3.5 N/mm², brick size 250x100x75 mm, mortar 10 mm. Source: excel (engineer-supplied spec).",
    "building.occupancy":
        "Real input. Project fact: residential occupancy. The IS 875 reference is boilerplate but the occupancy choice is a project decision. Source: excel.",
}

# ----------------------------------------------------------------------------
# 5. FIGURE ORIGIN (Task 5)
# ----------------------------------------------------------------------------
# figure_origin values:
#   generated        : produced by a script function (named in `generator`)
#   etabs_screenshot : user captures an ETABS view
#   user_supplied    : engineer provides an image file (e.g. cover, scanned drawing)
FIGURE_ORIGIN: dict[str, dict[str, Any]] = {
    # user_supplied
    "figure.project.cover":                     {"figure_origin": "user_supplied",    "generator": None},
    "figure.project.report_figure":             {"figure_origin": "user_supplied",    "generator": None},
    "figure.materials.concrete":                {"figure_origin": "user_supplied",    "generator": None},
    "figure.materials.material_property_rebar": {"figure_origin": "user_supplied",    "generator": None},
    "figure.staircase.design_main":             {"figure_origin": "user_supplied",    "generator": None},
    "figure.staircase.design_b":                {"figure_origin": "user_supplied",    "generator": None},
    "figure.staircase.design_c":                {"figure_origin": "user_supplied",    "generator": None},
    "figure.summary.design":                    {"figure_origin": "user_supplied",    "generator": None},
    "figure.summary.panel_a":                   {"figure_origin": "user_supplied",    "generator": None},
    "figure.summary.panel_b":                   {"figure_origin": "user_supplied",    "generator": None},
    # etabs_screenshot (user captures from ETABS)
    "figure.loads.wall_first":                  {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.loads.wall_second":                 {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.loads.wall_third":                  {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.building.finish_first":             {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.building.finish_second":            {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.loads.live_first":                  {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.loads.live_second":                 {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.loads.roof_live_second":            {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.loads.roof_live_top":               {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.loads.cases":                       {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.project.mass_sources_considered":   {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.project.mass_sources_b":            {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.irregularity.eqx_eccentricity":     {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.irregularity.eqx_eccentricity_b":   {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.irregularity.acc_eccentricity":     {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.irregularity.acc_eccentricity_b":   {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.elements.beams_design":             {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.elements.beams_design_b":           {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.elements.columns_design":           {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.elements.columns_design_b":         {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.foundation.design_main":            {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.foundation.design_b":               {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.foundation.design_c":               {"figure_origin": "etabs_screenshot", "generator": None},
    "figure.foundation.design_d":               {"figure_origin": "etabs_screenshot", "generator": None},
    # generated by generate_etabs_figures.py
    "figure.building.plan_of_building":         {"figure_origin": "generated", "generator": "generate_etabs_figures.py:geometry_figures (02_grid_plan.png)"},
    "figure.building.section_of_building":      {"figure_origin": "generated", "generator": "generate_etabs_figures.py:geometry_figures (03_sectional_view.png)"},
    "figure.modal.uls_force_distribution":      {"figure_origin": "generated", "generator": "generate_etabs_figures.py:drift_figures (06_drift_x/y.png)"},
    "figure.elements.design_for_frames":        {"figure_origin": "generated", "generator": "generate_etabs_figures.py:member_figures (10_beam_design.png, 11_column_design.png)"},
    "figure.foundation.reaction_uls":           {"figure_origin": "generated", "generator": "generate_etabs_figures.py:reaction_figures (07_joint_reaction.png)"},
    "figure.foundation.reaction_uls_b":         {"figure_origin": "generated", "generator": "generate_etabs_figures.py:reaction_figures (07_joint_reaction.png)"},
    "figure.foundation.reaction_uls_c":         {"figure_origin": "generated", "generator": "generate_etabs_figures.py:reaction_figures (07_joint_reaction.png)"},
    "figure.drift.displacement":                {"figure_origin": "generated", "generator": "generate_etabs_figures.py:drift_figures (06_drift_x/y.png)"},
    "figure.drift.displacement_b":              {"figure_origin": "generated", "generator": "generate_etabs_figures.py:drift_figures (06_drift_x/y.png)"},
    "figure.irregularity.soft_story":           {"figure_origin": "generated", "generator": "generate_etabs_figures.py:drift_figures (story stiffness check)"},
    "figure.irregularity.soft_story_panel_b":   {"figure_origin": "generated", "generator": "generate_etabs_figures.py:drift_figures (story stiffness check)"},
    "figure.irregularity.in_plane":             {"figure_origin": "generated", "generator": "generate_etabs_figures.py:member_figures (frame connectivity check)"},
    "figure.irregularity.re_entrant_corners":   {"figure_origin": "generated", "generator": "generate_etabs_figures.py:geometry_figures (plan projection check)"},
    "figure.irregularity.diaphragm":            {"figure_origin": "generated", "generator": "generate_etabs_figures.py:modal_figures (diaphragm CM / story mass)"},
    "figure.irregularity.out_of_plane_offset":  {"figure_origin": "generated", "generator": "generate_etabs_figures.py:member_figures (frame connectivity check)"},
    "figure.elements.rebar_grid_a":             {"figure_origin": "generated", "generator": "generate_etabs_figures.py:member_figures (12_reinforcement.png)"},
    "figure.elements.rebar_grid_b":             {"figure_origin": "generated", "generator": "generate_etabs_figures.py:member_figures (12_reinforcement.png)"},
    "figure.elements.rebar_story1":             {"figure_origin": "generated", "generator": "generate_etabs_figures.py:member_figures (12_reinforcement.png)"},
    "figure.elements.rebar_story2":             {"figure_origin": "generated", "generator": "generate_etabs_figures.py:member_figures (12_reinforcement.png)"},
    "figure.elements.rebar_story3":             {"figure_origin": "generated", "generator": "generate_etabs_figures.py:member_figures (12_reinforcement.png)"},
    # generated by generate_sls_drift_report.py
    "figure.irregularity.torsional":            {"figure_origin": "generated", "generator": "generate_sls_drift_report.py:torsion_summary (Torsional_Irregularity_Check.jpg)"},
}

# Placeholder figures renamed based on surrounding headings.
# placeholder_a/b (idx 475, 478) sit inside the "Design of Columns" heading.
# placeholder_c/d (idx 654, 657) sit inside the "Design Summary" heading.
PLACEHOLDER_RENAMES: dict[str, str] = {
    "figure.project.placeholder_a": "figure.elements.columns_design",
    "figure.project.placeholder_b": "figure.elements.columns_design_b",
    "figure.project.placeholder_c": "figure.summary.panel_a",
    "figure.project.placeholder_d": "figure.summary.panel_b",
}


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


# ----------------------------------------------------------------------------
# 3. CAPTION-ONLY KEYS (Task 3: captions must not be replaced)
# ----------------------------------------------------------------------------
# These keys mapped to whole caption paragraphs. Per the owner's Task 3
# requirement, caption paragraphs stay fixed (style, SEQ field, and "Table N:"
# label intact). Only variable fragments within the caption are substituted.
# These keys are dropped from the registry because their entire value was the
# caption text. They are listed in docs/needs_my_decision.md for review.
CAPTION_ONLY_KEYS: set[str] = {
    "project.empirical_period_intro",   # Table 8: Fundamental Time Period
    "modal.rayleigh_period_x_uls",      # Table 10: Rayleigh X-direction
    "modal.rayleigh_period_y_uls",      # Table 11: Rayleigh Y-direction
}


def fix_sentence_template(template: str | None, old_key: str, new_key: str) -> str | None:
    """Replace references to old_key in a sentence template with new_key."""
    if template is None:
        return None
    # Replace both {{ old_key }} and bare old_key references
    template = template.replace(f"{{{{ {old_key} }}}}", f"{{{{ {new_key} }}}}")
    template = template.replace(f"{{{{{old_key}}}}}", f"{{{{ {new_key} }}}}")
    return template


# Sentence templates for items that don't have one from the inventory tool.
# These are sub-paragraph templates: only the variable tokens are placeholders,
# the fixed wording stays.
EXTRA_SENTENCE_TEMPLATES: dict[str, str] = {
    "materials.as_building_is_less_than_12_m":
        "As the building is less than 12 m in height, {{ materials.concrete_grade_used }} concrete has been taken for all the structural components.",
    "materials.rebar_grade_used":
        "Steel Grade of {{ materials.rebar_grade_used }} has been used in the longitudinal and transverse reinforcement.",
    "modal.base_shear_etabs":
        "Base shear from ETABS {{ modal.base_shear_etabs }} kN.",
    "foundation.modeling_software":
        "The building was modeled using the {{ foundation.modeling_software }} software. {{ foundation.modeling_software }} is a specialized program designed specifically for the analysis and design of building systems. It offers a user-friendly interface and advanced features, making it both powerful and accessible for structural engineers.",
}


def strip_leading_tab(value: Any) -> Any:
    """Strip a leading literal "\\t" tab marker from a string example value."""
    if isinstance(value, str):
        return re.sub(r"^(?:\\t|\s)+", "", value)
    return value


# Supplementary registry entries: keys referenced in sentence templates
# that don't exist in the generated registry. These are added during
# curation so the registry is complete.
SUPPLEMENTARY_ENTRIES: list[dict[str, Any]] = [
    {
        "key": "materials.concrete_grade_used",
        "description": "Concrete grade used in the project (e.g. M20)",
        "type": "text", "unit": None, "format": {"decimals": None},
        "source": "etabs_api", "required": True, "condition": None,
        "inventory_item_index": 210, "example": "M20",
        "etabs_table_or_e2k_section": "Material Properties (concrete)",
    },
    {
        "key": "client.owner_name",
        "description": "Name of the building owner",
        "type": "text", "unit": None, "format": {"decimals": None},
        "source": "excel", "required": True, "condition": None,
        "inventory_item_index": None, "example": "Mr. Chatra Bahadur Ramtel",
    },
    {
        "key": "design.overstrength_serviceability",
        "description": "Serviceability overstrength factor",
        "type": "number", "unit": None, "format": {"decimals": 2},
        "source": "computed", "required": True, "condition": None,
        "inventory_item_index": None, "example": "1.25",
        "etabs_table_or_e2k_section": None,
    },
    {
        "key": "table.elements.col_desc",
        "description": "Column section description (e.g. 355 mm X 355 mm)",
        "type": "text", "unit": None, "format": {"decimals": None},
        "source": "etabs_api", "required": True, "condition": None,
        "inventory_item_index": None, "example": "355 mm X 355 mm",
        "etabs_table_or_e2k_section": "Frame Section Assignments",
    },
    {
        "key": "table.elements.beam_desc",
        "description": "Beam section description",
        "type": "text", "unit": None, "format": {"decimals": None},
        "source": "etabs_api", "required": True, "condition": None,
        "inventory_item_index": None, "example": "250 mm X 355 mm",
        "etabs_table_or_e2k_section": "Frame Section Assignments",
    },
    {
        "key": "table.elements.slab_desc",
        "description": "Slab section description",
        "type": "text", "unit": None, "format": {"decimals": None},
        "source": "etabs_api", "required": True, "condition": None,
        "inventory_item_index": None, "example": "125 mm",
        "etabs_table_or_e2k_section": "Shell Section Assignments",
    },
    {
        "key": "table.elements.wall_desc",
        "description": "Wall section description",
        "type": "text", "unit": None, "format": {"decimals": None},
        "source": "excel", "required": True, "condition": None,
        "inventory_item_index": None, "example": "230 mm",
    },
    {
        "key": "table.elements.stair_desc",
        "description": "Staircase section description",
        "type": "text", "unit": None, "format": {"decimals": None},
        "source": "excel", "required": True, "condition": None,
        "inventory_item_index": None, "example": "150 mm",
    },
    {
        "key": "table.design.beam_boundary",
        "description": "Boundary condition of beam (e.g. Continuous)",
        "type": "text", "unit": None, "format": {"decimals": None},
        "source": "excel", "required": True, "condition": None,
        "inventory_item_index": None, "example": "Continuous",
    },
    {
        "key": "seismic.alpha",
        "description": "Alpha factor (spectral acceleration coefficient)",
        "type": "number", "unit": None, "format": {"decimals": 2},
        "source": "computed", "required": True, "condition": None,
        "inventory_item_index": None, "example": "2.5",
        "etabs_table_or_e2k_section": None,
    },
    {
        "key": "seismic.spectral_shape_factor_cht",
        "description": "Spectral shape factor Ch(t)",
        "type": "number", "unit": None, "format": {"decimals": 2},
        "source": "computed", "required": True, "condition": None,
        "inventory_item_index": None, "example": "2.50",
        "etabs_table_or_e2k_section": None,
    },
    {
        "key": "seismic.elastic_site_spectra_c",
        "description": "Elastic site spectra for horizontal loading C(t)",
        "type": "number", "unit": None, "format": {"decimals": 3},
        "source": "computed", "required": True, "condition": None,
        "inventory_item_index": None, "example": "0.875",
        "etabs_table_or_e2k_section": None,
    },
    {
        "key": "seismic.elastic_site_spectra_cs",
        "description": "Elastic site spectra for serviceability limit state Cs",
        "type": "number", "unit": None, "format": {"decimals": 3},
        "source": "computed", "required": True, "condition": None,
        "inventory_item_index": None, "example": "0.175",
        "etabs_table_or_e2k_section": None,
    },
    {
        "key": "loads.slab_dead_load",
        "description": "Calculated dead load of slab (kN/m2)",
        "type": "number", "unit": "kN/m2", "format": {"decimals": 3},
        "source": "computed", "required": True, "condition": None,
        "inventory_item_index": None, "example": "3.175",
        "etabs_table_or_e2k_section": None,
    },
    # Totals for loop table footers
    {"key": "totals.wi_kg", "description": "Total weight Wi (kg)", "type": "number", "unit": "kg", "format": {"decimals": 2}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "167868.70", "etabs_table_or_e2k_section": None},
    {"key": "totals.wi_hik", "description": "Total Wi·hi^k", "type": "number", "unit": None, "format": {"decimals": 2}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "865221.01", "etabs_table_or_e2k_section": None},
    {"key": "totals.fi", "description": "Total ULS Fi (kN)", "type": "number", "unit": "kN", "format": {"decimals": 2}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "240.10", "etabs_table_or_e2k_section": None},
    {"key": "totals.fi_di_x", "description": "Total Fi·di (X-direction)", "type": "number", "unit": None, "format": {"decimals": 3}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "3.721", "etabs_table_or_e2k_section": None},
    {"key": "totals.wi_di2_x", "description": "Total Wi·di² (X-direction)", "type": "number", "unit": None, "format": {"decimals": 4}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "0.3347", "etabs_table_or_e2k_section": None},
    {"key": "totals.fi_di_y", "description": "Total Fi·di (Y-direction)", "type": "number", "unit": None, "format": {"decimals": 3}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "2.904", "etabs_table_or_e2k_section": None},
    {"key": "totals.wi_di2_y", "description": "Total Wi·di² (Y-direction)", "type": "number", "unit": None, "format": {"decimals": 4}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "0.2033", "etabs_table_or_e2k_section": None},
    {"key": "modal.rayleigh_period_x_s", "description": "Rayleigh time period X-direction result (s)", "type": "number", "unit": "s", "format": {"decimals": 3}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "0.602", "etabs_table_or_e2k_section": None},
    {"key": "modal.rayleigh_period_y_s", "description": "Rayleigh time period Y-direction result (s)", "type": "number", "unit": "s", "format": {"decimals": 3}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "0.531", "etabs_table_or_e2k_section": None},
    # T15 slab design as image placeholder
    {"key": "figure.design.slab_sheet", "description": "Slab design sheet image (user-supplied ETABS screenshot)", "type": "image", "unit": None, "format": {"decimals": None}, "source": "excel", "required": False, "condition": "User-supplied ETABS slab design screenshot", "inventory_item_index": None, "example": None, "figure_origin": "user_supplied", "generator": None},
    # New keys for T0 client details
    {"key": "client.designer_name", "description": "Name of the structural designer", "type": "text", "unit": None, "format": {"decimals": None}, "source": "excel", "required": True, "condition": None, "inventory_item_index": None, "example": "Mr. Sachin KC"},
    {"key": "client.designer_nec_reg", "description": "NEC registration number of the structural designer", "type": "text", "unit": None, "format": {"decimals": None}, "source": "excel", "required": True, "condition": None, "inventory_item_index": None, "example": "131xx\"Civil A\""},
    {"key": "client.designer_contact", "description": "Contact number of the structural designer", "type": "text", "unit": None, "format": {"decimals": None}, "source": "excel", "required": True, "condition": None, "inventory_item_index": None, "example": "9841xxxxxxx"},
    {"key": "client.municipality_reg", "description": "Municipality registration/application number", "type": "text", "unit": None, "format": {"decimals": None}, "source": "excel", "required": True, "condition": None, "inventory_item_index": None, "example": "Xxxx"},
    {"key": "client.application_date", "description": "Date of application in municipality", "type": "text", "unit": None, "format": {"decimals": None}, "source": "excel", "required": True, "condition": None, "inventory_item_index": None, "example": "2026/xx/xx"},
    # New keys for T2 building general info
    {"key": "building.occupancy_class", "description": "Occupancy class (e.g. Residential)", "type": "text", "unit": None, "format": {"decimals": None}, "source": "excel", "required": True, "condition": None, "inventory_item_index": None, "example": "Residential"},
    {"key": "building.occupancy_sentence", "description": "IS 875 live-load sentence for the occupancy type", "type": "text", "unit": None, "format": {"decimals": None}, "source": "excel", "required": True, "condition": None, "inventory_item_index": None, "example": "The live loads for the floor and roof are determined using IS 875 part 2, as referenced by the National Building Code."},
    {"key": "building.num_storeys_analysed", "description": "Number of storeys considered in the design", "type": "number", "unit": "storey", "format": {"decimals": 0}, "source": "e2k", "required": True, "condition": None, "inventory_item_index": None, "example": 3, "etabs_table_or_e2k_section": "$STORYDATA"},
    {"key": "building.num_basements", "description": "Number of basements", "type": "number", "unit": None, "format": {"decimals": 0}, "source": "excel", "required": True, "condition": None, "inventory_item_index": None, "example": 0},
    {"key": "building.height_ground_floor_m", "description": "Height of ground floor (m)", "type": "number", "unit": "m", "format": {"decimals": 3}, "source": "e2k", "required": True, "condition": None, "inventory_item_index": None, "example": 3.175, "etabs_table_or_e2k_section": "$STORYDATA"},
    {"key": "building.height_typical_floor_m", "description": "Height of typical floor (m)", "type": "number", "unit": "m", "format": {"decimals": 3}, "source": "e2k", "required": True, "condition": None, "inventory_item_index": None, "example": 3.175, "etabs_table_or_e2k_section": "$STORYDATA"},
    {"key": "building.height_period_m", "description": "Height considered for fundamental time period (m)", "type": "number", "unit": "m", "format": {"decimals": 3}, "source": "e2k", "required": True, "condition": None, "inventory_item_index": None, "example": 9.525, "etabs_table_or_e2k_section": "$STORYDATA"},
    # New keys for T3, T8, T12, T13, T16
    {"key": "table.elements.foundation_desc", "description": "Foundation description", "type": "text", "unit": None, "format": {"decimals": None}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "Combined Footing", "etabs_table_or_e2k_section": None},
    {"key": "foundation.soil_bearing", "description": "Soil bearing capacity (kN/m2)", "type": "text", "unit": None, "format": {"decimals": None}, "source": "excel", "required": True, "condition": None, "inventory_item_index": None, "example": "Soil Bearing Capacity is taken as 120 kN/m2"},
    {"key": "seismic.time_coefficient_kt", "description": "Time coefficient kt", "type": "number", "unit": None, "format": {"decimals": 3}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": 0.075, "etabs_table_or_e2k_section": None},
    {"key": "modal.empirical_period_unamplified_s", "description": "Unamplified approximate fundamental time period (s)", "type": "number", "unit": "s", "format": {"decimals": 3}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": 0.407, "etabs_table_or_e2k_section": None},
    {"key": "seismic.site_soil_category", "description": "Site soil category", "type": "text", "unit": None, "format": {"decimals": None}, "source": "excel", "required": True, "condition": None, "inventory_item_index": None, "example": "Very Soft Soil"},
    {"key": "seismic.tc", "description": "Tc value", "type": "number", "unit": None, "format": {"decimals": 1}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": 1, "etabs_table_or_e2k_section": None},
    {"key": "seismic.structural_type", "description": "Structural type for seismic parameters", "type": "text", "unit": None, "format": {"decimals": None}, "source": "excel", "required": True, "condition": None, "inventory_item_index": None, "example": "Ordinary Structures"},
    {"key": "seismic.hsc_uls", "description": "Horizontal seismic coefficient for ULS", "type": "number", "unit": None, "format": {"decimals": 3}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": 0.146, "etabs_table_or_e2k_section": None},
    {"key": "seismic.hsc_sls", "description": "Horizontal seismic coefficient for SLS", "type": "number", "unit": None, "format": {"decimals": 3}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": 0.140, "etabs_table_or_e2k_section": None},
    {"key": "table.design.beam_effective_span", "description": "Effective span of beam (mm)", "type": "text", "unit": None, "format": {"decimals": None}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "4191 mm", "etabs_table_or_e2k_section": None},
    {"key": "table.design.beam_overall_depth", "description": "Overall depth of beam (mm)", "type": "text", "unit": None, "format": {"decimals": None}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "430 mm", "etabs_table_or_e2k_section": None},
    {"key": "table.design.beam_effective_depth", "description": "Effective depth of beam (mm)", "type": "text", "unit": None, "format": {"decimals": None}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "395 mm", "etabs_table_or_e2k_section": None},
    {"key": "table.design.beam_basic_ld_ratio", "description": "Basic L/d ratio", "type": "text", "unit": None, "format": {"decimals": None}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "26", "etabs_table_or_e2k_section": None},
    {"key": "table.design.beam_ast_req", "description": "Required steel area (bottom, ETABS)", "type": "text", "unit": None, "format": {"decimals": None}, "source": "etabs_api", "required": True, "condition": None, "inventory_item_index": None, "example": "186 mm²", "etabs_table_or_e2k_section": "Beam Design Output"},
    {"key": "table.design.beam_ast_prov", "description": "Provided steel area", "type": "text", "unit": None, "format": {"decimals": None}, "source": "excel", "required": True, "condition": None, "inventory_item_index": None, "example": "226 mm²"},
    {"key": "table.design.beam_pt", "description": "Tension reinforcement percentage", "type": "text", "unit": None, "format": {"decimals": None}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "0.229 %", "etabs_table_or_e2k_section": None},
    {"key": "table.design.beam_fs", "description": "fs value (N/mm²)", "type": "text", "unit": None, "format": {"decimals": None}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "239 N/mm²", "etabs_table_or_e2k_section": None},
    {"key": "table.design.beam_mod_factor", "description": "Modification factor", "type": "text", "unit": None, "format": {"decimals": None}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "≈ 1.68", "etabs_table_or_e2k_section": None},
    {"key": "table.design.beam_permissible_ld", "description": "Permissible L/d", "type": "text", "unit": None, "format": {"decimals": None}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "43.7", "etabs_table_or_e2k_section": None},
    {"key": "table.design.beam_provided_ld", "description": "Provided L/d", "type": "text", "unit": None, "format": {"decimals": None}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "10.61", "etabs_table_or_e2k_section": None},
    {"key": "table.design.beam_check_result", "description": "Beam deflection check result", "type": "text", "unit": None, "format": {"decimals": None}, "source": "computed", "required": True, "condition": None, "inventory_item_index": None, "example": "10.61 < 43.7, OK", "etabs_table_or_e2k_section": None},
]

# When a sentence template is added (EXTRA_SENTENCE_TEMPLATES), update the
# entry's example to be just the variable value (not the whole sentence).
SENTENCE_TEMPLATE_EXAMPLE_UPDATES: dict[str, Any] = {
    "materials.as_building_is_less_than_12_m": "M20",  # The concrete grade
    "materials.rebar_grade_used": "Fe500",  # The rebar grade
    "modal.base_shear_etabs": "240.02",  # The base shear value in kN
    "foundation.modeling_software": "ETABS 19.0.0",  # The software version
}


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

        # Task 4: drop FIXED-reverted boilerplate identified in the key review.
        if new_key in TASK4_FIXED_REVERTED:
            dropped_fixed.append(new_key)
            continue

        # Task 3: drop caption-only keys (their value was the caption text;
        # captions now stay fixed with partial fragment substitution only).
        if new_key in CAPTION_ONLY_KEYS:
            dropped_fixed.append(new_key)
            continue

        item = dict(item)
        item["key"] = new_key
        for col in item.get("columns", []) or []:
            if col["key"].startswith(old_key + "."):
                col["key"] = new_key + col["key"][len(old_key):]

        reassign_source(item)

        # Task 4: strip leading \t tab markers from every example value.
        if "example" in item:
            item["example"] = strip_leading_tab(item["example"])

        # Fix sentence_template: replace old key references with new keys.
        if item.get("sentence_template"):
            for old_k, new_k in RENAME_MAP.items():
                item["sentence_template"] = fix_sentence_template(
                    item["sentence_template"], old_k, new_k
                )

        # Add extra sentence templates for items that don't have one.
        if new_key in EXTRA_SENTENCE_TEMPLATES and not item.get("sentence_template"):
            item["sentence_template"] = EXTRA_SENTENCE_TEMPLATES[new_key]
            # Update the example to be just the variable value
            if new_key in SENTENCE_TEMPLATE_EXAMPLE_UPDATES:
                item["example"] = SENTENCE_TEMPLATE_EXAMPLE_UPDATES[new_key]

        # For entries with a sentence_template, update the example to be
        # just the variable value (not the whole sentence). This makes the
        # example consistent with the sub-paragraph placeholder approach.

        # Task 1: codes.clauses.* get target_clause_2025, sample_clause,
        # mapping_status. example is set to null (sample clause lives in
        # sample_clause).
        if new_key in CLAUSE_MAPPINGS:
            mapping = CLAUSE_MAPPINGS[new_key]
            item["sample_clause"] = mapping["sample_clause"]
            item["target_clause_2025"] = mapping["target_clause_2025"]
            item["mapping_status"] = mapping["mapping_status"]
            item["example"] = None
            # Update condition text: owner-mapped clauses get a consistent
            # "Owner-approved mapping." label. This overrides any stale text
            # from the generator (e.g. "No owner-approved mapping supplied.").
            if mapping["mapping_status"] == "owner_mapped":
                item["condition"] = "Owner-approved mapping."

        # Task 2: foundation.support_condition — restore computed source,
        # keep $POINTRESTRAINTS as cross-check input.
        if new_key == "foundation.support_condition":
            item.update(FOUNDATION_SUPPORT_OVERRIDE)

        # Task 5: figures — add figure_origin and generator.
        if item.get("type") == "image":
            origin = FIGURE_ORIGIN.get(new_key)
            if origin is None:
                raise ValueError(f"Image key {new_key} has no figure_origin mapping")
            item["figure_origin"] = origin["figure_origin"]
            item["generator"] = origin["generator"]

        # T6 guard: mark the load assessment table as pending implementation.
        # Strict mode must fail while this flag is set.
        if new_key == "table.loads.load_assessment":
            item["status"] = "pending_implementation"

        if new_key in seen_new_keys:
            raise ValueError(f"Duplicate new key after rename: {new_key}")
        seen_new_keys.add(new_key)

        curated.append(item)

    # Add supplementary entries (keys referenced in sentence templates
    # that don't exist in the generated registry).
    for supp in SUPPLEMENTARY_ENTRIES:
        if supp["key"] not in seen_new_keys:
            curated.append(dict(supp))
            seen_new_keys.add(supp["key"])

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
        "## Clause mapping status",
        "",
        f"All {len([e for e in entries if e.get('key', '').startswith('codes.clauses.')])} "
        "codes.clauses.* entries have non-null target_clause_2025. "
        f"Owner-mapped: {sum(1 for e in entries if e.get('mapping_status') == 'owner_mapped')}, "
        f"sample-reference: {sum(1 for e in entries if e.get('mapping_status') == 'sample_reference')}, "
        f"unresolved: {sum(1 for e in entries if e.get('mapping_status') == 'needs_owner_decision')}.",
        "No unresolved clause mappings remain.",
        "",
        "## FIXED-reverted boilerplate (Task 4 key review)",
        "",
        "Three additional keys reverted to FIXED and dropped from the registry:",
        "",
    ]
    for key, text in sorted(TASK4_FIXED_REVERTED.items()):
        preview = text[:120] + ("…" if len(text) > 120 else "")
        lines.append(f"- `{key}` — {preview}")
    lines += [
        "",
        "Three keys kept as real-input VARIABLE:",
        "",
    ]
    for key, text in sorted(TASK4_REAL_INPUT.items()):
        preview = text[:120] + ("…" if len(text) > 120 else "")
        lines.append(f"- `{key}` — {preview}")
    lines += [
        "",
        "## Figure origin (Task 5)",
        "",
    ]
    origin_counts: Counter[str] = Counter()
    for e in entries:
        if e.get("type") == "image":
            origin_counts[e.get("figure_origin", "unknown")] += 1
    for origin, count in sorted(origin_counts.items()):
        lines.append(f"- `{origin}`: {count}")
    lines += [
        "",
        "Placeholder figures `figure.project.placeholder_a..d` renamed based on their "
        "surrounding headings:",
        "- placeholder_a/b (in \"Design of Columns\" section) → `figure.elements.columns_design`, "
        "`figure.elements.columns_design_b`",
        "- placeholder_c/d (in \"Design Summary\" section) → `figure.summary.panel_a`, "
        "`figure.summary.panel_b`",
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
        "- Foundation support wording is computed from `foundation.type` and `foundation.soil_class`.",
        "- `foundation.support_condition` carries `.e2k` `$POINTRESTRAINTS` as an additional "
        "cross-check input (`etabs_table_or_e2k_section: \"$POINTRESTRAINTS (cross-check input)\"`); "
        "the computation from `foundation.type` and `foundation.soil_class` does not change.",
        "- Clause citations are variables: the sample 2020 clauses map to NBC 105:2025 "
        "clauses recorded in the registry. All clause mappings are now owner-approved:",
        "  - `codes.clauses.material_properties` → \"Annex A, Cl. 2.1\" (item 208)",
        "  - `codes.clauses.load_combinations` → \"3.6.1\" (item 418)",
        "  - `codes.clauses.serviceability_drift` → \"5.5.3\" (items 533 and 535)",
        "  - `codes.clauses.irregularity_general` → \"5.4\" (item 591)",
        "  - `codes.clauses.torsional_irregularity` → \"5.4.2.1\" (item 593)",
        "  - `codes.clauses.soft_storey` → \"5.4.1.2\" (item 603)",
        "  - `codes.clauses.in_plane_discontinuity` → \"5.4.1.4\" (item 610)",
        "  - `codes.clauses.mass_irregularity` → \"5.4.1.5\" (item 617)",
        "  - `codes.clauses.reentrant_corner` → \"5.4.2.3\" (item 624)",
        "  - `codes.clauses.diaphragm_discontinuity` → \"5.4.2.4\" (item 632)",
        "  - `codes.clauses.out_of_plane_offset` → \"5.4.2.5\" (item 640)",
        "- In-plane and mass-irregularity conclusion paragraphs are computed variants "
        "and restyled to Body Text; the re-entrant conclusion has rectangular/no-re-entrant "
        "variants.",
        "- The foundation reaction image is retained; only its combination text is variable.",
        "",
        "## Unresolved NBC 105:2025 clause mappings",
        "",
        "None. All clause mappings are owner-approved and recorded above.",
        "",
        "## Key classification review (Task 4)",
        "",
        "Six keys were reviewed for FIXED boilerplate / TABLE / real input. The three "
        "FIXED-reverted keys below are dropped from the registry; the three real-input "
        "keys remain as VARIABLE.",
        "",
        "### FIXED-reverted (dropped from registry)",
        "",
    ]
    for key, text in sorted(TASK4_FIXED_REVERTED.items()):
        preview = text[:140] + ("…" if len(text) > 140 else "")
        lines.append(f"- `{key}` — {preview}")
    lines += ["", "### Real input (kept as VARIABLE)", ""]
    for key, text in sorted(TASK4_REAL_INPUT.items()):
        lines.append(f"- `{key}` — {text}")
    lines += [
        "",
        "## Caption-only keys removed from registry (Task 3)",
        "",
        "These keys mapped to whole caption paragraphs. Per the owner's Task 3 "
        "requirement, caption paragraphs stay fixed (style, SEQ field, and "
        "'Table N:' label intact). Only variable fragments within the caption "
        "are substituted (e.g. 'NBC 105:2025' -> {{ codes.edition }}, 'Damak' "
        "-> {{ building.location }}). These keys are dropped because their "
        "entire value was the caption text. Confirm whether each key should be:",
        "  (a) removed entirely, or",
        "  (b) moved to the real variable content beside the caption.",
        "",
    ]
    caption_descs = {
        "project.empirical_period_intro": "Table 8: Fundamental Time Period Based on Empirical Formula",
        "modal.rayleigh_period_x_uls": "Table 10: Rayleigh time period, X-direction (EQX-ULS)",
        "modal.rayleigh_period_y_uls": "Table 11: Rayleigh time period, Y-direction (EQY-ULS)",
    }
    for key in sorted(CAPTION_ONLY_KEYS):
        lines.append(f"- `{key}` — was: \"{caption_descs.get(key, '')}\"")
    lines += [
        "",
        "## Irregular tables needing owner decision (Task 2)",
        "",
        "T6 (Load Assessment, 39×6) and T15 (Slab Design, 88×8) are too irregular",
        "for a simple `{%tr for %}` loop. Choose one option per table:",
        "",
        "### T6 (Load Assessment)",
        "- Merged cells, mixed structure (wall loads, floor finish, live loads,",
        "  load cases, mass sources all in one table).",
        "- **Option A**: docxtpl Subdoc — build the table as a separate DOCX",
        "  fragment and insert via Subdoc.",
        "- **Option B**: Code-built table — build programmatically using",
        "  python-docx, reusing the sample's cell formatting.",
        "- **Option C**: Split into multiple tables — break into separate tables",
        "  (wall loads, live loads, load cases, mass sources) each with its own loop.",
        "",
        "### T15 (Slab Design, 88×8)",
        "- ETABS slab design output with blank headers. 88 rows of raw ETABS data.",
        "- **Option A**: Code-built table — build programmatically from ETABS CSV data.",
        "- **Option B**: Keep as image — replace the table with a screenshot of the",
        "  ETABS slab design output.",
        "- **Option C**: Skip entirely — omit the slab design table if the data is",
        "  not available.",
        "",
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
