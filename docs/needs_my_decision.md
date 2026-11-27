# Needs My Decision

This file is the single owner decision log. The previous generated copy at `docs/needs_my_decision.generated.md` has been removed and merged here.

## Applied owner decisions

- TOC entries for B.3, F.7, and the irregularity checks are `FIXED`; F.8 is fixed but controlled by `building.has_staircase`.
- When `has_staircase` is false, remove the staircase heading and the sample content range through the empty Heading 5; do not alter the DOCX during inventory.
- Foundation support wording is computed from `foundation.type` and `foundation.soil_class`.
- `foundation.support_condition` carries `.e2k` `$POINTRESTRAINTS` as an additional cross-check input (`etabs_table_or_e2k_section: "$POINTRESTRAINTS (cross-check input)"`); the computation from `foundation.type` and `foundation.soil_class` does not change.
- Clause citations are variables: the sample 2020 clauses map to NBC 105:2025 clauses recorded in the registry. All clause mappings are now owner-approved:
  - `codes.clauses.material_properties` → "Annex A, Cl. 2.1" (item 208)
  - `codes.clauses.load_combinations` → "3.6.1" (item 418)
  - `codes.clauses.serviceability_drift` → "5.5.3" (items 533 and 535)
  - `codes.clauses.irregularity_general` → "5.4" (item 591)
  - `codes.clauses.torsional_irregularity` → "5.4.2.1" (item 593)
  - `codes.clauses.soft_storey` → "5.4.1.2" (item 603)
  - `codes.clauses.in_plane_discontinuity` → "5.4.1.4" (item 610)
  - `codes.clauses.mass_irregularity` → "5.4.1.5" (item 617)
  - `codes.clauses.reentrant_corner` → "5.4.2.3" (item 624)
  - `codes.clauses.diaphragm_discontinuity` → "5.4.2.4" (item 632)
  - `codes.clauses.out_of_plane_offset` → "5.4.2.5" (item 640)
- In-plane and mass-irregularity conclusion paragraphs are computed variants and restyled to Body Text; the re-entrant conclusion has rectangular/no-re-entrant variants.
- The foundation reaction image is retained; only its combination text is variable.

## Unresolved NBC 105:2025 clause mappings

None. All clause mappings are owner-approved and recorded above.

## Key classification review (Task 4)

Six keys were reviewed for FIXED boilerplate / TABLE / real input. The three FIXED-reverted keys below are dropped from the registry; the three real-input keys remain as VARIABLE.

### FIXED-reverted (dropped from registry)

- `foundation.structural_system_foundation` — Table 3: Structural System & Foundation (table caption heading; the table itself is table.design.system_foundation)
- `project.brick_tolerances` — For thick walls, acceptable tolerances are -10 mm on length, -5 mm on width, and ±3 mm on thickness. (standard spec boilerplate; no project …
- `seismic.intro_statement` — The analysis and design in this report follow the codes and references listed below. Seismic loading, analysis and ductile detailing follow …

### Real input (kept as VARIABLE)

- `materials.as_building_is_less_than_12_m` — Real input / computed narrative. Project facts: height <12 m (from e2k $STORYDATA), grade M20 (from ETABS Material Properties). The sentence is computed from those facts.
- `project.brick_specs` — Real input. Material spec with project values: crushing strength 3.5 N/mm², brick size 250x100x75 mm, mortar 10 mm. Source: excel (engineer-supplied spec).

## Caption-only keys removed from registry (Task 3)

These keys mapped to whole caption paragraphs. Per the owner's Task 3 requirement, caption paragraphs stay fixed (style, SEQ field, and 'Table N:' label intact). Only variable fragments within the caption are substituted (e.g. 'NBC 105:2025' -> {{ codes.edition }}, 'Damak' -> {{ building.location }}). These keys are dropped because their entire value was the caption text. Confirm whether each key should be:
  (a) removed entirely, or
  (b) moved to the real variable content beside the caption.

- `modal.rayleigh_period_x_uls` — was: "Table 10: Rayleigh time period, X-direction (EQX-ULS)"
- `modal.rayleigh_period_y_uls` — was: "Table 11: Rayleigh time period, Y-direction (EQY-ULS)"
- `project.empirical_period_intro` — was: "Table 8: Fundamental Time Period Based on Empirical Formula"

## Irregular tables needing owner decision (Task 2)

T6 (Load Assessment, 39×6) and T15 (Slab Design, 88×8) are too irregular
for a simple `{%tr for %}` loop. Choose one option per table:

### T6 (Load Assessment)
- Merged cells, mixed structure (wall loads, floor finish, live loads,
  load cases, mass sources all in one table).
- **Option A**: docxtpl Subdoc — build the table as a separate DOCX
  fragment and insert via Subdoc.
- **Option B**: Code-built table — build programmatically using
  python-docx, reusing the sample's cell formatting.
- **Option C**: Split into multiple tables — break into separate tables
  (wall loads, live loads, load cases, mass sources) each with its own loop.

**Implementation record:** The owner-directed code-built approach is implemented in `src/input_workbook.py` as a 39×6 table using confirmed workbook inputs, with `UNRESOLVED` for unavailable engineering inputs. Independent structure and arithmetic tests pass; the former pending implementation allowance has been removed.

### T15 (Slab Design, 88×8)
- ETABS slab design output with blank headers. 88 rows of raw ETABS data.
- **Option A**: Code-built table — build programmatically from ETABS CSV data.
- **Option B**: Keep as image — replace the table with a screenshot of the
  ETABS slab design output.
- **Option C**: Skip entirely — omit the slab design table if the data is
  not available.

## Classification policy

The tool classifies headings and general method/boilerplate as `FIXED`, project facts as `VARIABLE`, data-driven tables as `TABLE`, replacement figures as `IMAGE`, derived results as `COMPUTED`, and condition-specific content as `CONDITIONAL`. Review all non-FIXED items before using the registry to drive report generation.

## Follow-up items requiring owner input

Beam deflection check keys require the authoritative source table/columns and approved calculation inputs; the current exports do not provide enough labeled source data to resolve them without guessing. The three tables with unlabelled headers require an owner choice between raw ETABS evidence, owner-supplied headers, or omission. Please confirm `foundation.type`; it is not inferred from point restraints. Please also confirm the approved in-plane and re-entrant irregularity declarations and their source evidence.

## Reinforcement golden mismatch requiring source confirmation

The sample report values `1.026%` (column minimum) and `0.764%` (beam steel) are confirmed report references, but the committed ETABS CSV design exports resolve to different values. Git history before `747525d` contained the sample beam arithmetic `678.584/(250*355)*100`, not a source-backed derivation of the report's design-output totals. The builder therefore retains the real CSV values and does not invent an effective-section formula; `docs/sample_comparison.md` records the numerical differences and provenance. Please provide the authoritative ETABS design-output columns/rows if exact reconciliation is required.

## Proposed changes requiring owner review

- **Torsion-clause wording:** The sample card cites clause `5.4.2.2` for both torsional thresholds. NBC 105:2025 distinguishes `5.4.2.1` (torsional irregularity) from `5.4.2.2` (extreme torsional irregularity). `generate_sls_drift_report.py` currently uses the sample-style wording; confirm whether the report should cite the distinct clauses by threshold, or retain the sample wording for format compatibility.
