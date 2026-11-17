# Placeholder Registry Review (Curated)

**Review gate:** this curated registry is owned by the structural engineer. Do not generate a production master template until the six unresolved NBC 105:2025 clause mappings in `docs/needs_my_decision.md` are answered.

Curated entries: **169**.
Types: bool: 1, image: 55, number: 40, table: 21, text: 52.
Sources: computed: 42, e2k: 7, etabs_api: 47, excel: 73.

## Counts per group

- `analysis`: 5
- `building`: 10
- `client`: 1
- `codes`: 30
- `design`: 19
- `figure`: 55
- `foundation`: 5
- `materials`: 2
- `modal`: 7
- `project`: 4
- `seismic`: 8
- `slab`: 1
- `structural`: 1
- `table`: 21

## Counts per source

- `computed`: 42
- `e2k`: 7
- `etabs_api`: 47
- `excel`: 73

## Key rename map

Full map in `docs/key_rename_map.csv`. Highlights:

- `code.*` merged into `codes.*` (7 keys).
- Every key longer than 40 characters renamed (77 keys).
- Every key whose last segment began with a digit renamed (e.g. `codes.clauses.5_6`).
- Every key whose last segment was a `\t` slug artifact renamed (`tdesign_of_*`, `tdisplacement_*`, `tbase_*`, `figure.project.t`).

## FIXED-reverted boilerplate (dropped from the registry)

- `materials.concrete_grade_min` — Minimum grade of structural concrete shall be M20, but M25 for buildings more than 12 m in height.
- `materials.rebar_grade_options_a` — Grade Fe 415 or less; or
- `materials.rebar_tmt_description` — High strength deformed steel bars produced by thermo-mechanical treatment process having elongation capacity of more tha…
- `materials.wall_thickness_range` — The minimum thickness is half-brick, while the maximum thickness is one brick. Internal walls have a thickness of up to …

## Unresolved NBC 105:2025 clause mappings

These six clause variables remain in the registry as `codes.clauses.*` text entries. The owner must answer the questions in `docs/needs_my_decision.md` before the template is built.

- item 208 — `codes.clauses.material_properties` (sample Cl. 2.1)
- item 418 — `codes.clauses.load_combinations` (sample Cl. 3.6.1)
- item 533 — `codes.clauses.serviceability_drift` (sample Cl. 5.6.3)
- item 535 — `codes.clauses.serviceability_drift` (sample Cl. 5.6.3)
- item 591 — `codes.clauses.irregularity_general` (sample Cl. 5.5)
- item 593 — `codes.clauses.torsional_irregularity` (sample Cl. 5.5.2.1)

## Files

- `config/placeholder_registry.yaml` — the curated registry.
- `docs/key_rename_map.csv` — old_key,new_key for every rename.
- `docs/registry_review_full.md` — the full before/after listing (Phase 1 review).
- `docs/needs_my_decision.md` — owner decision log + the six unresolved clause questions.
- `config/template_rules.yaml` — heading/text-anchored template rules.
- `tests/test_registry_keys.py` — key naming and required-field tests.

## Source priority

ETABS API/CSV > `.e2k` > Excel > computed. Disagreements are recorded, never silently resolved. Non-excel entries carry an `etabs_table_or_e2k_section` field naming the source table or `.e2k` section.
