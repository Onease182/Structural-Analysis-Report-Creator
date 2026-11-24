# Placeholder Registry Review — Full Before/After Listing

> **Full listing.** This is the complete per-item before/after output from `tools/inventory_template.py`. The short curated summary lives in `docs/registry_review.md`; the live registry is `config/placeholder_registry.yaml`. This file is regenerated whenever the inventory tool runs.

# Placeholder Registry Review (Phase 1)

**Review gate:** this is a proposed registry. Do not generate a production master template until the owner approves it.

Registry entries: **174**. Entry types: bool: 1, image: 55, number: 40, table: 21, text: 57.
Source counts: computed: 43, etabs_api: 12, excel: 119.

## Classification and Word-field handling

The previous inventory had 223 non-FIXED rows, including Word field codes. All Word fields remain visible in the inventory with `regenerated_by: Word` and are omitted from the value registry. The curated registry keeps the 18 owner-defined hand-named keys. Table entries now carry columns, a row source, and a fixed/data-driven row model. Numeric expressions and sample ratios are represented as project/example values or computed outputs; this does not validate their engineering correctness.

## NBC clause references changed to registry variables

No source DOCX text was edited. These are proposed placeholder substitutions in the registry/template map. Only mappings explicitly recorded in the owner's existing decisions are assigned a 2025 target clause; all others remain unresolved.

- Inventory item 238, sample clause 2.1: → NBC 105:2025 §Annex A, Cl. 2.1 (codes.clauses.material_properties).
- Inventory item 448, sample clause 3.6.1: → NBC 105:2025 §3.6.1 (codes.clauses.load_combinations).
- Inventory item 563, sample clause 5.6.3: → NBC 105:2025 §5.5.3 (codes.clauses.serviceability_drift).
- Inventory item 565, sample clause 5.6.3: → NBC 105:2025 §5.5.3 (codes.clauses.serviceability_drift).
- Inventory item 621, sample clause 5.5: → NBC 105:2025 §5.4 (codes.clauses.irregularity_general).
- Inventory item 623, sample clause 5.5.2.1: → NBC 105:2025 §5.4.2.1 (codes.clauses.torsional_irregularity).
- Inventory item 640, sample clause 5.5.1.4: → NBC 105:2025 §5.4.1.4 (codes.clauses.in_plane_discontinuity).
- Inventory item 647, sample clause 5.5.1.5: → NBC 105:2025 §5.4.1.5 (codes.clauses.mass_irregularity).
- Inventory item 654, sample clause 5.5.2.2: → NBC 105:2025 §5.4.2.3 (codes.clauses.reentrant_corner).
- Inventory item 662, sample clause 5.5.2.3: → NBC 105:2025 §5.4.2.4 (codes.clauses.diaphragm_discontinuity).
- Inventory item 670, sample clause 5.5.2.4: → NBC 105:2025 §5.4.2.5 (codes.clauses.out_of_plane_offset).

## VARIABLE / COMPUTED / CONDITIONAL / TABLE / IMAGE items: before and proposed after

### Item 0 — paragraph — VARIABLE → VARIABLE

Keys: project.report_title.

**Before:**

```text
Structural report of Residence Building of Chatra Bahadur Ramtel
```

**Proposed after:**

```text
{{ project.report_title }}
```

### Item 2 — image — IMAGE → IMAGE

Keys: figure.project.structural_analysis_design_report.

**Before:**

```text
Image 1: caption=(none); size=6.6146 × 0.0493 in
```

**Proposed after:**

```text
{{ figure.project.structural_analysis_design_report }}
```

### Item 5 — image — IMAGE → IMAGE

Keys: figure.project.report_figure.

**Before:**

```text
Image 2: caption=(none); size=6.9924 × 6.5 in
```

**Proposed after:**

```text
{{ figure.project.report_figure }}
```

### Item 11 — paragraph — VARIABLE → VARIABLE

Keys: client.consultant_name.

**Before:**

```text
Swarup Engineering Consultancy
```

**Proposed after:**

```text
{{ client.consultant_name }}
```

### Item 12 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Dharan-16, Sunsari
```

**Proposed after:**

```text
[review mapping required]
```

### Item 21 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 22 — paragraph — COMPUTED → VARIABLE

Keys: summary.designer_will_not_be_responsible_if_any.

**Before:**

```text
The designer will not be responsible if any alterations to the structural system made by the client or the contractor without the prior written permission from the designer, or the alterations to non-structural system made such that the weight of each individual floor or the weight of the whole building is altered by more than 10% of design weight of each floor and the total weight.
```

**Proposed after:**

```text
{{ summary.designer_will_not_be_responsible_if_any }}
```

### Item 24 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
The design calculations and derivations are limited to only a minimum to let the concerned people know the methodology adopted. However, the calculations may be provided to the client or concerned authorities when needed, upon request. Hence the building is safe.
```

**Proposed after:**

```text
[review mapping required]
```

### Item 26 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 28 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 30 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 32 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 34 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 36 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 38 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 40 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Er. Anij Bhandari
```

**Proposed after:**

```text
[review mapping required]
```

### Item 42 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
\n
```

**Proposed after:**

```text
[review mapping required]
```

### Item 44 — section_break — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Section break
```

**Proposed after:**

```text
[review mapping required]
```

### Item 46 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 48 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 50 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 52 — field — COMPUTED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
TOC \o \h \z \u
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 53 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586224 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 54 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
A. General Information 4
```

**Proposed after:**

```text
[review mapping required]
```

### Item 55 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586225 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 56 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
B. Features of the Building 1
```

**Proposed after:**

```text
[review mapping required]
```

### Item 57 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586226 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 58 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
B.1 General Information of the Building 1
```

**Proposed after:**

```text
[review mapping required]
```

### Item 59 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586227 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 60 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
B.2 Element sizes 3
```

**Proposed after:**

```text
[review mapping required]
```

### Item 61 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586228 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 62 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
B.3 Structural System and Foundation: 3
```

**Proposed after:**

```text
[review mapping required]
```

### Item 63 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586229 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 64 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
C. Modeling of the Building 4
```

**Proposed after:**

```text
[review mapping required]
```

### Item 65 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586230 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 66 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
C.1 Material Properties (Concrete, Re-bar, Structural Steel) 4
```

**Proposed after:**

```text
[review mapping required]
```

### Item 67 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586231 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 68 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
CONCRETE: 4
```

**Proposed after:**

```text
[review mapping required]
```

### Item 69 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586232 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 70 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
STEEL: 5
```

**Proposed after:**

```text
[review mapping required]
```

### Item 71 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586233 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 72 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
C.2 Stiffness Modifiers 6
```

**Proposed after:**

```text
[review mapping required]
```

### Item 73 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586234 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 74 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
C.3 Slab and Diaphragm 7
```

**Proposed after:**

```text
[review mapping required]
```

### Item 75 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586235 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 76 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
C.4 Accidental Eccentricity 8
```

**Proposed after:**

```text
[review mapping required]
```

### Item 77 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586236 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 78 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
C.5 Support Condition 8
```

**Proposed after:**

```text
[review mapping required]
```

### Item 79 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586237 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 80 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
C.6 Structural Analysis Software Used 8
```

**Proposed after:**

```text
[review mapping required]
```

### Item 81 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586238 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 82 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
D. Adequacy of Actions to the Buildings 9
```

**Proposed after:**

```text
[review mapping required]
```

### Item 83 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586239 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 84 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
D.1 Load Patterns considered 9
```

**Proposed after:**

```text
[review mapping required]
```

### Item 85 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586240 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 86 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Dead Loads: 9
```

**Proposed after:**

```text
[review mapping required]
```

### Item 87 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586241 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 88 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Wall Load: 9
```

**Proposed after:**

```text
[review mapping required]
```

### Item 89 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586242 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 90 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Bricks: 9
```

**Proposed after:**

```text
[review mapping required]
```

### Item 91 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586243 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 92 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Tolerances: 9
```

**Proposed after:**

```text
[review mapping required]
```

### Item 93 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586244 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 94 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Mortar: 9
```

**Proposed after:**

```text
[review mapping required]
```

### Item 95 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586245 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 96 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Plaster: 9
```

**Proposed after:**

```text
[review mapping required]
```

### Item 97 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586246 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 98 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Wall Thicknesses: 9
```

**Proposed after:**

```text
[review mapping required]
```

### Item 99 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586247 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 100 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
FLOOR FINISH 14
```

**Proposed after:**

```text
[review mapping required]
```

### Item 101 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586248 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 102 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
LIVE LOADS 16
```

**Proposed after:**

```text
[review mapping required]
```

### Item 103 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586249 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 104 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Table 6: Live load intensity in different rooms 16
```

**Proposed after:**

```text
[review mapping required]
```

### Item 105 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586250 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 106 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
D.2 Load Cases Considered for Equivalent Frame Analysis 21
```

**Proposed after:**

```text
[review mapping required]
```

### Item 107 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586251 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 108 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
D.3 Mass Source Considered for Seismic Weight 21
```

**Proposed after:**

```text
[review mapping required]
```

### Item 109 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586252 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 110 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
D.4 Detailed Load Calculations 22
```

**Proposed after:**

```text
[review mapping required]
```

### Item 111 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586253 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 112 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
D.5 Seismic Load Calculation Parameters 22
```

**Proposed after:**

```text
[review mapping required]
```

### Item 113 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586254 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 114 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
D.5.1 Base Shear Calculation from Equivalent Static Method 22
```

**Proposed after:**

```text
[review mapping required]
```

### Item 115 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586255 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 116 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Rayleigh method 22
```

**Proposed after:**

```text
[review mapping required]
```

### Item 117 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586256 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 118 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
D.5.2 Base Shear from Modal Response Spectrum 24
```

**Proposed after:**

```text
[review mapping required]
```

### Item 119 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586257 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 120 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Load Combination 25
```

**Proposed after:**

```text
[review mapping required]
```

### Item 121 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586258 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 122 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
E. Analysis of Building 25
```

**Proposed after:**

```text
[review mapping required]
```

### Item 123 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586259 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 124 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
E.1 Modal Analysis Results 25
```

**Proposed after:**

```text
[review mapping required]
```

### Item 125 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586260 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 126 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
F. Adequacy of Member Design 26
```

**Proposed after:**

```text
[review mapping required]
```

### Item 127 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586261 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 128 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
F.1 Check for All Members Passed (for Element Design through Software) 26
```

**Proposed after:**

```text
[review mapping required]
```

### Item 129 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586262 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 130 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
F.2 Check for Max. & Min. Percentage of Reinforcement Provided 26
```

**Proposed after:**

```text
[review mapping required]
```

### Item 131 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586263 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 132 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
F.3 Design of Slabs 27
```

**Proposed after:**

```text
[review mapping required]
```

### Item 133 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586264 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 134 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
F.4 Design of Beams 29
```

**Proposed after:**

```text
[review mapping required]
```

### Item 135 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586265 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 136 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
F.5 Design of Columns 31
```

**Proposed after:**

```text
[review mapping required]
```

### Item 137 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586266 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 138 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
F.6 Check for Ductile Detailing 33
```

**Proposed after:**

```text
[review mapping required]
```

### Item 139 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586267 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 140 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
F.6.1 Detailing of members 33
```

**Proposed after:**

```text
[review mapping required]
```

### Item 141 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586268 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 142 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
F.6.2 Anchorage of Beam Longitudinal Reinforcement 33
```

**Proposed after:**

```text
[review mapping required]
```

### Item 143 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586269 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 144 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
F.7 Design of Foundations 34
```

**Proposed after:**

```text
[review mapping required]
```

### Item 145 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586270 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 146 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
F.8 Design of Staircases 38
```

**Proposed after:**

```text
[review mapping required]
```

### Item 147 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586271 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 149 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586272 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 151 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586273 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 153 — field — TABLE → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586274 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 155 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586275 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 156 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
G.1.3 Torsional Irregularity 46
```

**Proposed after:**

```text
[review mapping required]
```

### Item 157 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586276 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 158 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
G.1.4 Soft Story 47
```

**Proposed after:**

```text
[review mapping required]
```

### Item 159 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586277 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 161 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586278 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 163 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586279 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 164 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
G.1.6 Mass Irregularity 47
```

**Proposed after:**

```text
[review mapping required]
```

### Item 165 — field — VARIABLE → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586280 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 167 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586281 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 168 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
G.1.7 Re-entrant Corner 48
```

**Proposed after:**

```text
[review mapping required]
```

### Item 169 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586282 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 170 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
G.1.8 Diaphragm Discontinuity 48
```

**Proposed after:**

```text
[review mapping required]
```

### Item 171 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586283 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 173 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586284 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 175 — field — IMAGE → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586285 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 177 — field — COMPUTED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
PAGEREF _Toc245586286 \h
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 179 — section_break — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Section break
```

**Proposed after:**

```text
[review mapping required]
```

### Item 181 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
General Information
```

**Proposed after:**

```text
[review mapping required]
```

### Item 183 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 184 — table — FIXED → TABLE

Keys: table.client.general_information.

**Before:**

```text
Table 1: 10 rows × 3 columns; sample headers: ['S.N.', 'General Information:']
```

**Proposed after:**

```text
{{ table.client.general_information }}
```

### Item 185 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 187 — paragraph — FIXED → VARIABLE

Keys: seismic.analysis_design_in_this_report_follow_codes.

**Before:**

```text
The analysis and design in this report follow the codes and references listed below. Seismic loading, analysis and ductile detailing follow NBC 105:2025.
```

**Proposed after:**

```text
{{ seismic.analysis_design_in_this_report_follow_codes }}
```

### Item 189 — table — FIXED → TABLE

Keys: table.codes.references.

**Before:**

```text
Table 2: 6 rows × 4 columns; sample headers: ['S.N.', 'Code / Reference', 'Title', 'Used for']
```

**Proposed after:**

```text
{{ table.codes.references }}
```

### Item 195 — paragraph — FIXED → VARIABLE

Keys: building.storeys_above_grade, building.primary_frame_material.

**Before:**

```text
The building has three floors made of reinforced concrete frames and filled with
```

**Proposed after:**

```text
The building has {{ building.storeys_above_grade }} floors made of {{ building.primary_frame_material }} frames and filled with
```

### Item 196 — paragraph — FIXED → VARIABLE

Keys: building.infill_wall_material, building.span_y_m, building.span_x_m, building.story_height_m.

**Before:**

```text
brick walls. Each floor has a height of 3.175 meters. The building is laid out in a rectangular grid pattern, with a span of 4.216 meters horizontally (X-direction) and 10.058 meters vertically (Y-direction) between columns.
```

**Proposed after:**

```text
{{ building.infill_wall_material }} walls. Each floor has a height of {{ building.story_height_m }} meters. The building is laid out in a rectangular grid pattern, with a span of {{ building.span_x_m }} meters horizontally (X-direction) and {{ building.span_y_m }} meters vertically (Y-direction) between columns.
```

### Item 199 — image — CONDITIONAL → IMAGE

Keys: figure.building.plan_of_building.

**Before:**

```text
Image 3: caption=Figure 1: Plan of Building; size=3.2812 × 6.0489 in
```

**Proposed after:**

```text
{{ figure.building.plan_of_building }}
```

### Item 200 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Figure 1: Plan of Building
```

**Proposed after:**

```text
[review mapping required]
```

### Item 201 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 202 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 206 — image — FIXED → IMAGE

Keys: figure.building.section_of_building.

**Before:**

```text
Image 4: caption=Figure 2: Section of Building; size=6.1318 × 5.3438 in
```

**Proposed after:**

```text
{{ figure.building.section_of_building }}
```

### Item 208 — field — VARIABLE → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 209 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Table 1: General Information of the Building
```

**Proposed after:**

```text
[review mapping required]
```

### Item 210 — field — VARIABLE → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Table \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 212 — table — IMAGE → TABLE

Keys: table.building.general_information.

**Before:**

```text
Table 3: 9 rows × 3 columns; sample headers: ['A.1-01', 'Location of Building', 'Damak']
```

**Proposed after:**

```text
{{ table.building.general_information }}
```

### Item 214 — field — COMPUTED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Table \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 216 — table — FIXED → TABLE

Keys: table.elements.sizes_and_materials.

**Before:**

```text
Table 4: 6 rows × 4 columns; sample headers: ['Element', 'Description', 'Grade of Concrete', 'Remarks']
```

**Proposed after:**

```text
{{ table.elements.sizes_and_materials }}
```

### Item 217 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 218 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Element sizes
```

**Proposed after:**

```text
[review mapping required]
```

### Item 221 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Structural System and Foundation:
```

**Proposed after:**

```text
[review mapping required]
```

### Item 223 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 224 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
The selection and arrangement of major structural elements to efficiently resist gravity and horizontal loads are essential in determining the building's structural form. Several factors influence the choice of structural form, including internal planning, construction materials and methods, external architectural treatment, placement and routing of service systems, magnitude and nature of horizontal loading, as well as the building's height and proportions.
```

**Proposed after:**

```text
[review mapping required]
```

### Item 227 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 228 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 229 — paragraph — FIXED → CONDITIONAL

Keys: foundation.structural_system_foundation.

**Before:**

```text
Table 3: Structural System & Foundation
```

**Proposed after:**

```text
{{ foundation.structural_system_foundation }}
```

### Item 230 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Table \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 232 — table — FIXED → TABLE

Keys: table.design.structural_system_and_foundation.

**Before:**

```text
Table 5: 3 rows × 3 columns; sample headers: ['A.3-01', 'Type of Structural System', 'Moment Resisting Frames']
```

**Proposed after:**

```text
{{ table.design.structural_system_and_foundation }}
```

### Item 238 — paragraph — FIXED → VARIABLE

Keys: codes.clauses.material_properties.

**Before:**

```text
According to NBC105:2020, The material should be taken as per Cl.2.1.
```

**Proposed after:**

```text
According to {{ codes.edition }}, The material should be taken as per Cl.{{ codes.clauses.material_properties }}.
```

### Item 239 — paragraph — FIXED → VARIABLE

Keys: materials.minimum_grade_of_structural_concrete_shall_be.

**Before:**

```text
Minimum grade of structural concrete shall be M20, but M25 for buildings more than 12 m in height.
```

**Proposed after:**

```text
{{ materials.minimum_grade_of_structural_concrete_shall_be }}
```

### Item 240 — paragraph — VARIABLE → VARIABLE

Keys: materials.as_building_is_less_than_12_m.

**Before:**

```text
As the building is less than 12 m in height, M20 concrete has been taken for all the structural components.
```

**Proposed after:**

```text
{{ materials.as_building_is_less_than_12_m }}
```

### Item 242 — image — FIXED → IMAGE

Keys: figure.materials.material_property_concrete.

**Before:**

```text
Image 5: caption=Figure 3: Material Property (Concrete); size=3.3787 × 5.1562 in
```

**Proposed after:**

```text
{{ figure.materials.material_property_concrete }}
```

### Item 244 — field — IMAGE → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 245 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
STEEL:
```

**Proposed after:**

```text
[review mapping required]
```

### Item 247 — paragraph — FIXED → VARIABLE

Keys: materials.grade_fe_415_or_less_or.

**Before:**

```text
Grade Fe 415 or less; or
```

**Proposed after:**

```text
{{ materials.grade_fe_415_or_less_or }}
```

### Item 248 — paragraph — FIXED → VARIABLE

Keys: materials.high_strength_deformed_steel_bars_produced_by.

**Before:**

```text
High strength deformed steel bars produced by thermo-mechanical treatment process having elongation capacity of more than 15 percent; e.g. Grade Fe 500 and Fe 550.
```

**Proposed after:**

```text
{{ materials.high_strength_deformed_steel_bars_produced_by }}
```

### Item 251 — image — IMAGE → IMAGE

Keys: figure.materials.material_property_rebar.

**Before:**

```text
Image 6: caption=Figure 4: Material Property (Rebar); size=3.817 × 4.7241 in
```

**Proposed after:**

```text
{{ figure.materials.material_property_rebar }}
```

### Item 252 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Figure 4: Material Property (Rebar)
```

**Proposed after:**

```text
[review mapping required]
```

### Item 253 — field — COMPUTED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 254 — paragraph — FIXED → VARIABLE

Keys: materials.steel_grade_of_fe500_has_been_in.

**Before:**

```text
Steel Grade of Fe500 has been used in the longitudinal and transverse reinforcement.
```

**Proposed after:**

```text
{{ materials.steel_grade_of_fe500_has_been_in }}
```

### Item 256 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Table 4: Effective stiffness of different components
```

**Proposed after:**

```text
[review mapping required]
```

### Item 257 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Table \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 258 — table — CONDITIONAL → TABLE

Keys: table.modifiers.effective_stiffness.

**Before:**

```text
Table 6: 3 rows × 4 columns; sample headers: ['S No.', 'Component', 'Flexural Stiffness (Ultimate)', 'Flexural Stiffness (Serviceability)']
```

**Proposed after:**

```text
{{ table.modifiers.effective_stiffness }}
```

### Item 268 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
the slab, resulting in minimal bending in the vertical plane. Conventional slab with rigid diaphragm has been assumed.
```

**Proposed after:**

```text
[review mapping required]
```

### Item 270 — paragraph — VARIABLE → VARIABLE

Keys: codes.clauses.5_6.

**Before:**

```text
Due to the eccentricity arising between the center of mass and the center of rigidity at each floor level of the building, code requires increase in shear forces on the lateral force resisting elements caused by the twisting about the vertical axis of the building. Hence design codes prescribe that the actual center of mass shall be shifted by a stipulated value to consider accidental torsional force in the lateral force resisting elements, i.e. columns and shear walls. In this part of the checklist, accidental eccentricity to be considered in x-direction as per the clause 5.6 of NBC 105:2025 is to be listed. As per the clause, the value of accidental eccentricity shall be +0.05*by where by is the floor lateral dimension of the building perpendicular to the direction of lateral force EQx. Thus, the design eccentricity at floor level i, edi,y will be equal to esi,y+0.05*by where esi,y is the actual static eccentricity in y-direction.
```

**Proposed after:**

```text
Due to the eccentricity arising between the center of mass and the center of rigidity at each floor level of the building, code requires increase in shear forces on the lateral force resisting elements caused by the twisting about the vertical axis of the building. Hence design codes prescribe that the actual center of mass shall be shifted by a stipulated value to consider accidental torsional force in the lateral force resisting elements, i.e. columns and shear walls. In this part of the checklist, accidental eccentricity to be considered in x-direction as per the clause {{ codes.clauses.5_6 }} of {{ codes.edition }} is to be listed. As per the clause, the value of accidental eccentricity shall be +0.05*by where by is the floor lateral dimension of the building perpendicular to the direction of lateral force EQx. Thus, the design eccentricity at floor level i, edi,y will be equal to esi,y+0.05*by where esi,y is the actual static eccentricity in y-direction.
```

### Item 274 — image — FIXED → IMAGE

Keys: figure.irregularity.eqxeqxdesign_eccentricity_edi_y_esi_y_0.

**Before:**

```text
Image 7: caption=(none); size=0.5917 × 0.5931 in
```

**Proposed after:**

```text
{{ figure.irregularity.eqxeqxdesign_eccentricity_edi_y_esi_y_0 }}
```

### Item 275 — image — FIXED → IMAGE

Keys: figure.irregularity.eqxeqxdesign_eccentricity_edi_y_esi_y_0_panel_b.

**Before:**

```text
Image 8: caption=(none); size=2.175 × 0.5368 in
```

**Proposed after:**

```text
{{ figure.irregularity.eqxeqxdesign_eccentricity_edi_y_esi_y_0_panel_b }}
```

### Item 277 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 281 — image — FIXED → IMAGE

Keys: figure.irregularity.cresi_ycmedi_ycm_cresi_ycmedi_ycm_5.

**Before:**

```text
Image 9: caption=(none); size=3.1924 × 1.7542 in
```

**Proposed after:**

```text
{{ figure.irregularity.cresi_ycmedi_ycm_cresi_ycmedi_ycm_5 }}
```

### Item 282 — image — FIXED → IMAGE

Keys: figure.irregularity.cresi_ycmedi_ycm_cresi_ycmedi_ycm_5_panel_b.

**Before:**

```text
Image 10: caption=(none); size=0.0889 × 1.741 in
```

**Proposed after:**

```text
{{ figure.irregularity.cresi_ycmedi_ycm_cresi_ycmedi_ycm_5_panel_b }}
```

### Item 283 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 286 — paragraph — COMPUTED → COMPUTED

Keys: foundation.support_condition.

**Before:**

```text
the foundation is assumed to be fixed.
```

**Proposed after:**

```text
{{ foundation.support_condition }}
```

### Item 288 — paragraph — TABLE → CONDITIONAL

Keys: foundation.building_was_modeled_using_etabs_19_0.

**Before:**

```text
The building was modeled using the ETABS 19.0.0 software. ETABS 19.0.0 is a specialized program designed specifically for the analysis and design of building systems. It offers a user-friendly interface and advanced features, making it both sophisticated and easy to use. The software provides intuitive modeling capabilities, powerful analytical tools, efficient design procedures, robust numerical methods, and supports various international design codes. With its ability to handle complex structures and nonlinear behaviors, ETABS 19.0.0 is widely preferred by structural engineers in the building industry. For the design of foundation, manual calculation was done.
```

**Proposed after:**

```text
{{ foundation.building_was_modeled_using_etabs_19_0 }}
```

### Item 293 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 295 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Wall Load:
```

**Proposed after:**

```text
[review mapping required]
```

### Item 298 — paragraph — IMAGE → VARIABLE

Keys: project.standard_rectangular_bricks_are_which_are_well.

**Before:**

```text
Standard rectangular bricks are used, which are well burnt, hand-formed or machine-made, and possess a crushing strength of at least 3.5 N/mm². The preferred brick size is 250 x 100 x 75 mm, with 10 mm thick horizontal and vertical mortar joints.
```

**Proposed after:**

```text
{{ project.standard_rectangular_bricks_are_which_are_well }}
```

### Item 300 — paragraph — COMPUTED → VARIABLE

Keys: project.thick_walls_acceptable_tolerances_are_10_mm.

**Before:**

```text
For thick walls, acceptable tolerances are -10 mm on length, -5 mm on width, and ±3 mm on thickness.
```

**Proposed after:**

```text
{{ project.thick_walls_acceptable_tolerances_are_10_mm }}
```

### Item 302 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Cement-sand mixes of 1:6 and 1:4 are adopted for one-brick and half-brick thick walls, respectively. Adding a small amount of freshly hydrated lime, in a ratio of
```

**Proposed after:**

```text
[review mapping required]
```

### Item 305 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
All plasters should have a cement-sand mix with a minimum ratio of 1:6 and a cube crushing strength of at least 3 N/mm² after 28 days.
```

**Proposed after:**

```text
[review mapping required]
```

### Item 307 — paragraph — FIXED → VARIABLE

Keys: materials.minimum_thickness_is_half_brick_while_maximum.

**Before:**

```text
The minimum thickness is half-brick, while the maximum thickness is one brick. Internal walls have a thickness of up to 115 mm for brick walls or equivalent materials, while external walls have a thickness of up to 230 mm for brick walls or equivalent materials.
```

**Proposed after:**

```text
{{ materials.minimum_thickness_is_half_brick_while_maximum }}
```

### Item 310 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 312 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 316 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Table \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 317 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 318 — table — FIXED → TABLE

Keys: table.loads.load_assessment.

**Before:**

```text
Table 7: 39 rows × 6 columns; sample headers: ['']
```

**Proposed after:**

```text
{{ table.loads.load_assessment }}
```

### Item 319 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 323 — image — FIXED → IMAGE

Keys: figure.loads.wall_load_first_floor_in_kn_m.

**Before:**

```text
Image 11: caption=Figure 6: Wall Load (First Floor in kN/m); size=4.4811 × 9.3747 in
```

**Proposed after:**

```text
{{ figure.loads.wall_load_first_floor_in_kn_m }}
```

### Item 325 — field — VARIABLE → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 328 — image — COMPUTED → IMAGE

Keys: figure.loads.wall_load_second_floor_in_kn_m.

**Before:**

```text
Image 12: caption=Figure 7: Wall Load (Second Floor in kN/m); size=4.7194 × 8.72 in
```

**Proposed after:**

```text
{{ figure.loads.wall_load_second_floor_in_kn_m }}
```

### Item 329 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Figure 7: Wall Load (Second Floor in kN/m)
```

**Proposed after:**

```text
[review mapping required]
```

### Item 330 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 332 — image — IMAGE → IMAGE

Keys: figure.loads.wall_load_third_floor_in_kn_m.

**Before:**

```text
Image 13: caption=Figure 8: Wall Load(Third Floor in kN/m); size=4.6675 × 8.6667 in
```

**Proposed after:**

```text
{{ figure.loads.wall_load_third_floor_in_kn_m }}
```

### Item 335 — field — COMPUTED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 337 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 339 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 340 — image — FIXED → IMAGE

Keys: figure.building.floor_finish_first_floor_in_kn_m2.

**Before:**

```text
Image 14: caption=Figure 9: Floor Finish (First Floor in kN/m2); size=4.7715 × 8.7929 in
```

**Proposed after:**

```text
{{ figure.building.floor_finish_first_floor_in_kn_m2 }}
```

### Item 342 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 344 — section_break — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Section break
```

**Proposed after:**

```text
[review mapping required]
```

### Item 346 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 347 — image — FIXED → IMAGE

Keys: figure.building.floor_finish_second_floor_in_kn_m2.

**Before:**

```text
Image 15: caption=Figure 10: Floor Finish (Second Floor in kN/m2); size=4.6569 × 8.7408 in
```

**Proposed after:**

```text
{{ figure.building.floor_finish_second_floor_in_kn_m2 }}
```

### Item 348 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Figure 10: Floor Finish (Second Floor in kN/m2)
```

**Proposed after:**

```text
[review mapping required]
```

### Item 349 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 350 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 355 — paragraph — IMAGE → VARIABLE

Keys: building.occupancy.

**Before:**

```text
The live loads for the floor and roof are determined using IS 875 part 2, as referenced by the National Building Code. For residential buildings, the appropriate live load values specified in Table 1 of IS 875 Part 2 are considered. Since the building is intended for residential use, the loading intensity for dwelling houses under the residential category is taken into account.
```

**Proposed after:**

```text
{{ building.occupancy }}
```

### Item 358 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Table \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 359 — table — FIXED → TABLE

Keys: table.loads.live_load_intensity.

**Before:**

```text
Table 8: 9 rows × 3 columns; sample headers: ['S.N', 'OCCUPANCY CLASSIFICATION', 'Uniformly distributed load']
```

**Proposed after:**

```text
{{ table.loads.live_load_intensity }}
```

### Item 360 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 361 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 362 — image — IMAGE → IMAGE

Keys: figure.loads.live_load_first_floor_in_kn_m2.

**Before:**

```text
Image 16: caption=Figure 11: Live Load (First Floor in kN/m2); size=4.1073 × 8.3333 in
```

**Proposed after:**

```text
{{ figure.loads.live_load_first_floor_in_kn_m2 }}
```

### Item 364 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Figure 11: Live Load (First Floor in kN/m2)
```

**Proposed after:**

```text
[review mapping required]
```

### Item 365 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 367 — image — FIXED → IMAGE

Keys: figure.loads.live_load_second_floor_in_kn_m2.

**Before:**

```text
Image 17: caption=Figure 12: Live Load (Second Floor in kN/m2); size=4.2818 × 8.7825 in
```

**Proposed after:**

```text
{{ figure.loads.live_load_second_floor_in_kn_m2 }}
```

### Item 369 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 372 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 373 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 374 — image — FIXED → IMAGE

Keys: figure.loads.roof_live_second_floor_in_kn_m2.

**Before:**

```text
Image 18: caption=Figure 13: Roof Live (Second Floor in kN/m2); size=4.7402 × 8.5637 in
```

**Proposed after:**

```text
{{ figure.loads.roof_live_second_floor_in_kn_m2 }}
```

### Item 375 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Figure 13: Roof Live (Second Floor in kN/m2)
```

**Proposed after:**

```text
[review mapping required]
```

### Item 376 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 378 — image — FIXED → IMAGE

Keys: figure.loads.roof_live_top_floor_in_kn_m2.

**Before:**

```text
Image 19: caption=Figure 14: Roof live (Top Floor in kN/m2); size=4.4381 × 8.6991 in
```

**Proposed after:**

```text
{{ figure.loads.roof_live_top_floor_in_kn_m2 }}
```

### Item 379 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Figure 14: Roof live (Top Floor in kN/m2)
```

**Proposed after:**

```text
[review mapping required]
```

### Item 380 — field — VARIABLE → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 381 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 382 — section_break — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Section break
```

**Proposed after:**

```text
[review mapping required]
```

### Item 383 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Load Cases Considered for Equivalent Frame Analysis
```

**Proposed after:**

```text
[review mapping required]
```

### Item 384 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 385 — image — FIXED → IMAGE

Keys: figure.loads.load_cases_considered_in_software.

**Before:**

```text
Image 20: caption=Figure 15: Load Cases considered in the software; size=6.9924 × 3.3 in
```

**Proposed after:**

```text
{{ figure.loads.load_cases_considered_in_software }}
```

### Item 388 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 389 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Table 7: Mass Source
```

**Proposed after:**

```text
[review mapping required]
```

### Item 390 — image — TABLE → IMAGE

Keys: figure.seismic.mass_sources_considered.

**Before:**

```text
Image 21: caption=Figure 15: Mass sources considered; size=4.0195 × 1.7354 in
```

**Proposed after:**

```text
{{ figure.seismic.mass_sources_considered }}
```

### Item 391 — field — COMPUTED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Table \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 392 — image — COMPUTED → IMAGE

Keys: figure.seismic.mass_sources_considered_panel_b.

**Before:**

```text
Image 22: caption=Figure 15: Mass sources considered; size=6.9924 × 3.1375 in
```

**Proposed after:**

```text
{{ figure.seismic.mass_sources_considered_panel_b }}
```

### Item 393 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Figure 15: Mass sources considered
```

**Proposed after:**

```text
[review mapping required]
```

### Item 394 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 395 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 397 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Detailed Load Calculations
```

**Proposed after:**

```text
[review mapping required]
```

### Item 402 — paragraph — FIXED → COMPUTED

Keys: seismic.fundamental_time_period_on_empirical_formula.

**Before:**

```text
Table 8: Fundamental Time Period Based on Empirical Formula
```

**Proposed after:**

```text
{{ seismic.fundamental_time_period_on_empirical_formula }}
```

### Item 403 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Table \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 405 — table — VARIABLE → TABLE

Keys: table.seismic.empirical_period_calculation.

**Before:**

```text
Table 9: 6 rows × 7 columns; sample headers: ['Height of building from foundation or from top of rigid basement (H)', '9.525', 'm']
```

**Proposed after:**

```text
{{ table.seismic.empirical_period_calculation }}
```

### Item 406 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 407 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Rayleigh method
```

**Proposed after:**

```text
[review mapping required]
```

### Item 409 — image — TABLE → IMAGE

Keys: figure.modal.vertical_distribution_of_uls_seismic_forces_nbc.

**Before:**

```text
Image 23: caption=Table 9: Vertical distribution of ULS seismic forces (NBC 105:2025 Cl. 6.3); size=3.6684 × 0.6125 in
```

**Proposed after:**

```text
{{ figure.modal.vertical_distribution_of_uls_seismic_forces_nbc }}
```

### Item 410 — paragraph — FIXED → VARIABLE

Keys: modal.base_shear_etabs_240_02_kn.

**Before:**

```text
Base shear from ETABS 240.02 kN.
```

**Proposed after:**

```text
{{ modal.base_shear_etabs_240_02_kn }}
```

### Item 411 — paragraph — FIXED → VARIABLE

Keys: codes.clauses.vertical_force_distribution.

**Before:**

```text
Table 9: Vertical distribution of ULS seismic forces (NBC 105:2025 Cl. 6.3)
```

**Proposed after:**

```text
Table 9: Vertical distribution of ULS seismic forces ({{ codes.edition }} Cl. {{ codes.clauses.vertical_force_distribution }})
```

### Item 412 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Table \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 413 — table — VARIABLE → TABLE

Keys: table.seismic.vertical_force_distribution.

**Before:**

```text
Table 10: 6 rows × 7 columns; sample headers: ['Level', 'Wi (kg)', 'Elevation hi (m)', 'hi^k', 'Wi·hi^k', 'ULS Fi (kN)', 'Shear Force (kN)']
```

**Proposed after:**

```text
{{ table.seismic.vertical_force_distribution }}
```

### Item 414 — paragraph — FIXED → COMPUTED

Keys: seismic.distribution_exponent_k, seismic.design_period_used_s, seismic.spectral_coefficient_cd, seismic.zone_factor_z, seismic.importance_factor_i, seismic.response_modification_factor_rmu, design.overstrength_factor_ultimate_omega_u, seismic.soil_class.

**Before:**

```text
k = 1.004 (T = 0.508 s); Cd = 0.1458; V = Cd·W, W taken above Base. Z = 0.35, soil C, I = 1.0, Rμ = 4, Ωu = 1.5.
```

**Proposed after:**

```text
k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismic.spectral_coefficient_cd }}; V = Cd·W, W taken above Base. Z = {{ seismic.zone_factor_z }}, soil {{ seismic.soil_class }}, I = {{ seismic.importance_factor_i }}, Rμ = {{ seismic.response_modification_factor_rmu }}, Ωu = {{ design.overstrength_factor_ultimate_omega_u }}.
```

### Item 418 — paragraph — VARIABLE → COMPUTED

Keys: modal.rayleigh_time_period_x_direction_eqx_uls.

**Before:**

```text
Table 10: Rayleigh time period, X-direction (EQX-ULS)
```

**Proposed after:**

```text
{{ modal.rayleigh_time_period_x_direction_eqx_uls }}
```

### Item 419 — field — VARIABLE → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Table \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 420 — table — FIXED → TABLE

Keys: table.modal.rayleigh_x.

**Before:**

```text
Table 11: 7 rows × 8 columns; sample headers: ['Level', 'Wi (kN)', 'di (mm)', 'di (m)', 'di²', 'ULS Fi (kN)', 'Fi·di', 'Wi·di²']
```

**Proposed after:**

```text
{{ table.modal.rayleigh_x }}
```

### Item 421 — paragraph — FIXED → COMPUTED

Keys: modal.rayleigh_time_period_y_direction_eqy_uls.

**Before:**

```text
Table 11: Rayleigh time period, Y-direction (EQY-ULS)
```

**Proposed after:**

```text
{{ modal.rayleigh_time_period_y_direction_eqy_uls }}
```

### Item 422 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Table \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 423 — table — FIXED → TABLE

Keys: table.modal.rayleigh_y.

**Before:**

```text
Table 12: 7 rows × 8 columns; sample headers: ['Level', 'Wi (kN)', 'di (mm)', 'di (m)', 'di²', 'ULS Fi (kN)', 'Fi·di', 'Wi·di²']
```

**Proposed after:**

```text
{{ table.modal.rayleigh_y }}
```

### Item 425 — paragraph — FIXED → COMPUTED

Keys: modal.rayleigh_period_s, modal.empirical_period_s, modal.selected_period_method.

**Before:**

```text
As Empirical time period (0.508 sec) is lesser than the Rayleigh time period (0.531 sec), use empirical time period for the calculation.
```

**Proposed after:**

```text
As Empirical time period ({{ modal.empirical_period_s }} sec) is lesser than the Rayleigh time period ({{ modal.rayleigh_period_s }} sec), use {{ modal.selected_period_method }} time period for the calculation.
```

### Item 427 — paragraph — FIXED → VARIABLE

Keys: codes.clauses.spectral_shape_factor, codes.clauses.seismic_zoning_factor, codes.clauses.importance_factor.

**Before:**

```text
Ch(t)=Spectral Shape factor as per cl.4.1.2 Z= Seismic Zoning Factor as per 4.1.4 I=Importance factor as per 4.1.5
```

**Proposed after:**

```text
Ch(t)=Spectral Shape factor as per cl.{{ codes.clauses.spectral_shape_factor }} of {{ codes.edition }} Z= Seismic Zoning Factor as per {{ codes.clauses.seismic_zoning_factor }} of {{ codes.edition }} I=Importance factor as per {{ codes.clauses.importance_factor }} of {{ codes.edition }}
```

### Item 430 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 433 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 434 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 435 — paragraph — FIXED → VARIABLE

Keys: codes.edition, building.location.

**Before:**

```text
Table 12: Seismic design parameters for the RC moment resisting frame in Damak (NBC 105:2025).
```

**Proposed after:**

```text
Table 12: Seismic design parameters for the RC moment resisting frame in {{ building.location }} ({{ codes.edition }}).
```

### Item 436 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Table \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 437 — table — FIXED → TABLE

Keys: table.seismic.design_parameters.

**Before:**

```text
Table 13: 15 rows × 4 columns; sample headers: ['Fundamental Time Period =', '0.508', 'Sec']
```

**Proposed after:**

```text
{{ table.seismic.design_parameters }}
```

### Item 439 — table — FIXED → TABLE

Keys: table.design.overstrength_factors.

**Before:**

```text
Table 14: 4 rows × 2 columns; sample headers: ['Over strength Factor Ultimate limitState =', '1.5']
```

**Proposed after:**

```text
{{ table.design.overstrength_factors }}
```

### Item 443 — paragraph — IMAGE → VARIABLE

Keys: building.storeys_above_grade, building.story_height_m, codes.clauses.equivalent_static_method, building.total_height_m.

**Before:**

```text
As per Clause 3.2.1 of NBC 105:2025, the Equivalent Static Method may be used for all serviceability limit state calculations regardless of the building characteristics. For the ultimate limit state, the Equivalent Static Method may be used when at least one of the listed criteria is satisfied, including that the height of the structure is less than or equal to 15 m. The total height of the building is 9.525 m (3 stories × 3.175 m), which is less than 15 m. Therefore, the Equivalent Static Method is applicable for both ULS and SLS, and Modal Response Spectrum Analysis is not required.
```

**Proposed after:**

```text
As per Clause {{ codes.clauses.equivalent_static_method }} of {{ codes.edition }}, the Equivalent Static Method may be used for all serviceability limit state calculations regardless of the building characteristics. For the ultimate limit state, the Equivalent Static Method may be used when at least one of the listed criteria is satisfied, including that the height of the structure is less than or equal to 15 m. The total height of the building is {{ building.total_height_m }} m ({{ building.storeys_above_grade }} stories × {{ building.story_height_m }} m), which is less than 15 m. Therefore, the Equivalent Static Method is applicable for both ULS and SLS, and Modal Response Spectrum Analysis is not required.
```

### Item 445 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 448 — paragraph — FIXED → VARIABLE

Keys: codes.clauses.load_combinations.

**Before:**

```text
When lateral load resisting elements are oriented along mutually orthogonal horizontal directions, the structure system is considered to be parallel and load combinations as specified in clause 3.6.1 of NBC 105:2020 is used for design.
```

**Proposed after:**

```text
When lateral load resisting elements are oriented along mutually orthogonal horizontal directions, the structure system is considered to be parallel and load combinations as specified in clause {{ codes.clauses.load_combinations }} of {{ codes.edition }} is used for design.
```

### Item 449 — paragraph — FIXED → VARIABLE

Keys: codes.clauses.load_combinations.

**Before:**

```text
For Parallel System (Cl. 3.6.1)
```

**Proposed after:**

```text
For Parallel System (Cl. {{ codes.clauses.load_combinations }} of {{ codes.edition }})
```

### Item 450 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 454 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 456 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
= 0.3 for other usage
```

**Proposed after:**

```text
[review mapping required]
```

### Item 458 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Analysis of Building
```

**Proposed after:**

```text
[review mapping required]
```

### Item 460 — paragraph — FIXED → VARIABLE

Keys: codes.clauses.modal_mass_participation, codes.limits.modal_mass_participation_pct, modal.modes_included_count.

**Before:**

```text
NBC105:2025 clause 7.3 states that number of modes to be used in the analysis should be such that the sum total of modal masses of all modes considered is at least 90 percent of the total seismic mass of the structure. The analysis was carried out for 12 modes so that the mass participation satisfies this criterion in both orthogonal directions. The table shows time period and mass participation ratio for all modes.
```

**Proposed after:**

```text
{{ codes.edition }} clause {{ codes.clauses.modal_mass_participation }} states that number of modes to be used in the analysis should be such that the sum total of modal masses of all modes considered is at least {{ codes.limits.modal_mass_participation_pct }} percent of the total seismic mass of the structure. The analysis was carried out for {{ modal.modes_included_count }} modes so that the mass participation satisfies this criterion in both orthogonal directions. The table shows time period and mass participation ratio for all modes.
```

### Item 461 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 463 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Table \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 464 — table — FIXED → TABLE

Keys: table.modal.periods_and_mass_participation.

**Before:**

```text
Table 15: 11 rows × 7 columns; sample headers: ['Case', 'Mode', 'Period', 'UX', 'UY', 'Sum UX', 'Sum UY']
```

**Proposed after:**

```text
{{ table.modal.periods_and_mass_participation }}
```

### Item 465 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 467 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 469 — section_break — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Section break
```

**Proposed after:**

```text
[review mapping required]
```

### Item 471 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Check for All Members Passed (for Element Design through Software)
```

**Proposed after:**

```text
[review mapping required]
```

### Item 473 — image — FIXED → IMAGE

Keys: figure.elements.design_for_frames.

**Before:**

```text
Image 24: caption=Figure 16: Design check for frames; size=6.9924 × 7.3882 in
```

**Proposed after:**

```text
{{ figure.elements.design_for_frames }}
```

### Item 475 — field — IMAGE → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 478 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Maximum Percentage of Rebars provided in columns
```

**Proposed after:**

```text
[review mapping required]
```

### Item 480 — paragraph — FIXED → COMPUTED

Keys: design.column.maximum_reinforcement.provided_reinforcement_area_mm2, design.column.maximum_reinforcement.section_width_mm, design.column.maximum_reinforcement.section_depth_mm, design.column.maximum_reinforcement.provided_pct, design.column.maximum_reinforcement.limit_pct, design.column.maximum_reinforcement.status.

**Before:**

```text
= 1557/ (355*355)*100% =1.24% <4% (Ok)
```

**Proposed after:**

```text
= {{ design.column.maximum_reinforcement.provided_reinforcement_area_mm2 }}/({{ design.column.maximum_reinforcement.section_width_mm }}*{{ design.column.maximum_reinforcement.section_depth_mm }})*100% = {{ design.column.maximum_reinforcement.provided_pct }}% < {{ design.column.maximum_reinforcement.limit_pct }}% ({{ design.column.maximum_reinforcement.status }})
```

### Item 484 — paragraph — FIXED → COMPUTED

Keys: design.column.minimum_reinforcement.provided_pct, design.column.minimum_reinforcement.limit_pct, design.column.minimum_reinforcement.status.

**Before:**

```text
= 1.026% > 1% (Ok)
```

**Proposed after:**

```text
= {{ design.column.minimum_reinforcement.provided_pct }}% > {{ design.column.minimum_reinforcement.limit_pct }}% ({{ design.column.minimum_reinforcement.status }})
```

### Item 486 — paragraph — IMAGE → COMPUTED

Keys: design.beam.maximum_reinforcement.provided_reinforcement_area_mm2, design.beam.maximum_reinforcement.section_width_mm, design.beam.maximum_reinforcement.section_depth_mm, design.beam.maximum_reinforcement.provided_pct, design.beam.maximum_reinforcement.limit_pct, design.beam.maximum_reinforcement.status.

**Before:**

```text
= 678.584/ (250*355) = 0.764% <2.5% (Ok)
```

**Proposed after:**

```text
= {{ design.beam.maximum_reinforcement.provided_reinforcement_area_mm2 }}/({{ design.beam.maximum_reinforcement.section_width_mm }}*{{ design.beam.maximum_reinforcement.section_depth_mm }})*100% = {{ design.beam.maximum_reinforcement.provided_pct }}% < {{ design.beam.maximum_reinforcement.limit_pct }}% ({{ design.beam.maximum_reinforcement.status }})
```

### Item 487 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Minimum Percentage of Rebars provided in beams
```

**Proposed after:**

```text
[review mapping required]
```

### Item 488 — paragraph — FIXED → COMPUTED

Keys: design.beam.minimum_reinforcement.provided_pct, design.beam.minimum_reinforcement.limit_pct, design.beam.minimum_reinforcement.status.

**Before:**

```text
= 0.764% >0.26 % (Ok)
```

**Proposed after:**

```text
= {{ design.beam.minimum_reinforcement.provided_pct }}% >{{ design.beam.minimum_reinforcement.limit_pct }}% ({{ design.beam.minimum_reinforcement.status }})
```

### Item 491 — table — FIXED → TABLE

Keys: table.design.slab_design_output.

**Before:**

```text
Table 16: 88 rows × 8 columns; sample headers: ['', '', '', '', '', '', '', '']
```

**Proposed after:**

```text
{{ table.design.slab_design_output }}
```

### Item 493 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Design of Beams
```

**Proposed after:**

```text
[review mapping required]
```

### Item 494 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Table 14: Check for Deflection for beam
```

**Proposed after:**

```text
[review mapping required]
```

### Item 495 — field — COMPUTED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Table \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 497 — table — FIXED → TABLE

Keys: table.design.beam_deflection_check.

**Before:**

```text
Table 17: 14 rows × 2 columns; sample headers: ['Item', 'Value']
```

**Proposed after:**

```text
{{ table.design.beam_deflection_check }}
```

### Item 499 — image — FIXED → IMAGE

Keys: figure.elements.design_of_beams.

**Before:**

```text
Image 25: caption=(none); size=6.2196 × 8.9492 in
```

**Proposed after:**

```text
{{ figure.elements.design_of_beams }}
```

### Item 500 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 501 — image — FIXED → IMAGE

Keys: figure.elements.design_of_beams_panel_b.

**Before:**

```text
Image 26: caption=(none); size=6.7197 × 2.1774 in
```

**Proposed after:**

```text
{{ figure.elements.design_of_beams_panel_b }}
```

### Item 505 — image — FIXED → IMAGE

Keys: figure.elements.design_of_columns.

**Before:**

```text
Image 27: caption=(none); size=5.2005 × 7.4479 in
```

**Proposed after:**

```text
{{ figure.elements.design_of_columns }}
```

### Item 506 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 508 — image — IMAGE → IMAGE

Keys: figure.elements.design_of_columns_panel_b.

**Before:**

```text
Image 28: caption=(none); size=6.125 × 4.5175 in
```

**Proposed after:**

```text
{{ figure.elements.design_of_columns_panel_b }}
```

### Item 512 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Refer to the structural drawing to verify whether proper ductile detailing has been done in the beam, column, joints etc. Verify the other requirements and also the ductile detailing requirements of the building as per Annex A of the code.
```

**Proposed after:**

```text
[review mapping required]
```

### Item 516 — image — FIXED → IMAGE

Keys: figure.foundation.foundation_reaction_1_5dl_1_5ll.

**Before:**

```text
Image 29: caption=Figure 17: Foundation reaction(1.5DL+1.5LL); size=5.971 × 1.925 in
```

**Proposed after:**

```text
{{ figure.foundation.foundation_reaction_1_5dl_1_5ll }}
```

### Item 517 — image — FIXED → IMAGE

Keys: figure.foundation.foundation_reaction_1_5dl_1_5ll_panel_b.

**Before:**

```text
Image 30: caption=Figure 17: Foundation reaction(1.5DL+1.5LL); size=3.0896 × 2.1222 in
```

**Proposed after:**

```text
{{ figure.foundation.foundation_reaction_1_5dl_1_5ll_panel_b }}
```

### Item 518 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 520 — section_break — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Section break
```

**Proposed after:**

```text
[review mapping required]
```

### Item 522 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 523 — image — FIXED → IMAGE

Keys: figure.foundation.foundation_reaction_1_5dl_1_5ll_panel_c.

**Before:**

```text
Image 31: caption=Figure 17: Foundation reaction(1.5DL+1.5LL); size=3.4171 × 5.7716 in
```

**Proposed after:**

```text
{{ figure.foundation.foundation_reaction_1_5dl_1_5ll_panel_c }}
```

### Item 524 — paragraph — FIXED → VARIABLE

Keys: analysis.foundation_reaction_combination.

**Before:**

```text
Figure 17: Foundation reaction(1.5DL+1.5LL)
```

**Proposed after:**

```text
{{ analysis.foundation_reaction_combination }}
```

### Item 525 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 530 — image — FIXED → IMAGE

Keys: figure.foundation.design_of_foundations.

**Before:**

```text
Image 32: caption=(none); size=6.9924 × 5.916 in
```

**Proposed after:**

```text
{{ figure.foundation.design_of_foundations }}
```

### Item 533 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 535 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 536 — image — FIXED → IMAGE

Keys: figure.foundation.design_of_foundations_panel_b.

**Before:**

```text
Image 33: caption=(none); size=6.9924 × 3.991 in
```

**Proposed after:**

```text
{{ figure.foundation.design_of_foundations_panel_b }}
```

### Item 538 — image — FIXED → IMAGE

Keys: figure.foundation.design_of_foundations_panel_c.

**Before:**

```text
Image 34: caption=(none); size=6.9924 × 1.7174 in
```

**Proposed after:**

```text
{{ figure.foundation.design_of_foundations_panel_c }}
```

### Item 542 — image — IMAGE → IMAGE

Keys: figure.foundation.design_of_foundations_panel_d.

**Before:**

```text
Image 35: caption=(none); size=6.7976 × 4.5729 in
```

**Proposed after:**

```text
{{ figure.foundation.design_of_foundations_panel_d }}
```

### Item 548 — image — FIXED → IMAGE

Keys: figure.staircase.design_of_staircases.

**Before:**

```text
Image 36: caption=(none); size=6.9924 × 6.1764 in
```

**Proposed after:**

```text
{{ figure.staircase.design_of_staircases }}
```

### Item 549 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 550 — image — FIXED → IMAGE

Keys: figure.staircase.design_of_staircases_panel_b.

**Before:**

```text
Image 37: caption=(none); size=6.9924 × 3.1194 in
```

**Proposed after:**

```text
{{ figure.staircase.design_of_staircases_panel_b }}
```

### Item 552 — image — FIXED → IMAGE

Keys: figure.staircase.design_of_staircases_panel_c.

**Before:**

```text
Image 38: caption=(none); size=6.9924 × 2.85 in
```

**Proposed after:**

```text
{{ figure.staircase.design_of_staircases_panel_c }}
```

### Item 563 — paragraph — TABLE → VARIABLE

Keys: codes.clauses.serviceability_drift.

**Before:**

```text
5.6.3 of NBC 105:2077 is proposed to be used.
```

**Proposed after:**

```text
{{ codes.clauses.serviceability_drift }} of {{ codes.edition }} is proposed to be used.
```

### Item 565 — paragraph — FIXED → VARIABLE

Keys: codes.clauses.serviceability_drift, codes.limits.maximum_story_deflection_ratio, codes.limits.serviceability_story_drift_ratio, codes.limits.ultimate_story_drift_ratio.

**Before:**

```text
5.6.3 of NBC 105:2077 is applied. The maximum deflection in any story due to the minimum specified design lateral force, with partial load factor of 1.0 shall not exceed 0.006 times the story height. Furthermore, the drift shall not exceed 0.006 in Serviceability Limit State and 0.025 in Ultimate Limit State case.
```

**Proposed after:**

```text
{{ codes.clauses.serviceability_drift }} of {{ codes.edition }} is applied. The maximum deflection in any story due to the minimum specified design lateral force, with partial load factor of 1.0 shall not exceed {{ codes.limits.maximum_story_deflection_ratio }} times the story height. Furthermore, the drift shall not exceed {{ codes.limits.serviceability_story_drift_ratio }} in Serviceability Limit State and {{ codes.limits.ultimate_story_drift_ratio }} in Ultimate Limit State case.
```

### Item 572 — image — FIXED → IMAGE

Keys: figure.drift.displacement_drift.

**Before:**

```text
Image 39: caption=(none); size=6.991 × 2.8264 in
```

**Proposed after:**

```text
{{ figure.drift.displacement_drift }}
```

### Item 575 — paragraph — TABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 579 — table — TABLE → TABLE

Keys: table.drift.uls_displacement_figures_x_y.

**Before:**

```text
Table 18: 2 rows × 2 columns; sample headers: ['', '']
```

**Proposed after:**

```text
{{ table.drift.uls_displacement_figures_x_y }}
```

### Item 584 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 591 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 593 — table — VARIABLE → TABLE

Keys: table.drift.sls_displacement_figures_x_y.

**Before:**

```text
Table 19: 2 rows × 2 columns; sample headers: ['', '']
```

**Proposed after:**

```text
{{ table.drift.sls_displacement_figures_x_y }}
```

### Item 595 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 597 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 600 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 603 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 605 — table — IMAGE → TABLE

Keys: table.drift.uls_story_drift_figures_x_y.

**Before:**

```text
Table 20: 2 rows × 2 columns; sample headers: ['', '']
```

**Proposed after:**

```text
{{ table.drift.uls_story_drift_figures_x_y }}
```

### Item 607 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 608 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 609 — table — FIXED → TABLE

Keys: table.drift.sls_story_drift_figures_x_y.

**Before:**

```text
Table 21: 2 rows × 2 columns; sample headers: ['', '']
```

**Proposed after:**

```text
{{ table.drift.sls_story_drift_figures_x_y }}
```

### Item 610 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 611 — section_break — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Section break
```

**Proposed after:**

```text
[review mapping required]
```

### Item 613 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 614 — image — FIXED → IMAGE

Keys: figure.drift.displacement_drift_panel_b.

**Before:**

```text
Image 40: caption=(none); size=6.991 × 4.1043 in
```

**Proposed after:**

```text
{{ figure.drift.displacement_drift_panel_b }}
```

### Item 615 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 617 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 621 — paragraph — COMPUTED → VARIABLE

Keys: codes.clauses.irregularity_general.

**Before:**

```text
One of the basic virtues of earthquake resistant design of structures is that the structure shall be regular as much as possible. It is observed that the structures with simple and regular configurations suffer much less damage during a large earthquake in comparison to the structures with irregular configurations. At the planning stage itself, the Designer should try to make the structure as regular as possible. Clause 5.5 of NBC 105:2020 has given provisions to check the structural irregularity of structures.
```

**Proposed after:**

```text
One of the basic virtues of earthquake resistant design of structures is that the structure shall be regular as much as possible. It is observed that the structures with simple and regular configurations suffer much less damage during a large earthquake in comparison to the structures with irregular configurations. At the planning stage itself, the Designer should try to make the structure as regular as possible. Clause {{ codes.clauses.irregularity_general }} of {{ codes.edition }} has given provisions to check the structural irregularity of structures.
```

### Item 623 — paragraph — FIXED → VARIABLE

Keys: codes.clauses.torsional_irregularity, codes.limits.torsional_displacement_ratio.

**Before:**

```text
As per the clause 5.5.2.1 of NBC 105:2020, torsion irregularity is considered to exist when the maximum horizontal displacement of any floor in the direction of the lateral force, applied at the centre of mass, at one end of the story is more than 1.5 times its minimum horizontal displacement at the far end of the same story in that direction.
```

**Proposed after:**

```text
As per the clause {{ codes.clauses.torsional_irregularity }} of {{ codes.edition }}, torsion irregularity is considered to exist when the maximum horizontal displacement of any floor in the direction of the lateral force, applied at the centre of mass, at one end of the story is more than {{ codes.limits.torsional_displacement_ratio }} times its minimum horizontal displacement at the far end of the same story in that direction.
```

### Item 624 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 625 — image — COMPUTED → IMAGE

Keys: figure.irregularity.torsional_irregularity.

**Before:**

```text
Image 41: caption=Figure 26: Torsional Irregularity; size=3.0327 × 1.3433 in
```

**Proposed after:**

```text
{{ figure.irregularity.torsional_irregularity }}
```

### Item 627 — field — IMAGE → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 629 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 630 — image — FIXED → IMAGE

Keys: figure.irregularity.soft_story.

**Before:**

```text
Image 42: caption=Figure 27: Soft story check; size=6.991 × 2.2783 in
```

**Proposed after:**

```text
{{ figure.irregularity.soft_story }}
```

### Item 632 — paragraph — VARIABLE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Soft Story
```

**Proposed after:**

```text
[review mapping required]
```

### Item 633 — paragraph — FIXED → VARIABLE

Keys: codes.clauses.soft_storey, codes.limits.soft_storey_adjacent_stiffness_pct, codes.limits.soft_storey_average_stiffness_pct.

**Before:**

```text
As per the clause 5.5.1.2, a soft story is the one whose stiffness of the lateral force resisting system is less than 70% of the lateral force resisting system stiffness in an adjacent story above or below, or less than 80% of the average lateral force resisting system stiffness of the three storys above or below.
```

**Proposed after:**

```text
As per the clause {{ codes.clauses.soft_storey }} of {{ codes.edition }}, a soft story is the one whose stiffness of the lateral force resisting system is less than {{ codes.limits.soft_storey_adjacent_stiffness_pct }}% of the lateral force resisting system stiffness in an adjacent story above or below, or less than {{ codes.limits.soft_storey_average_stiffness_pct }}% of the average lateral force resisting system stiffness of the three storys above or below.
```

### Item 635 — image — IMAGE → IMAGE

Keys: figure.irregularity.soft_story_panel_b.

**Before:**

```text
Image 43: caption=Figure 27: Soft story check; size=1.4007 × 2.1656 in
```

**Proposed after:**

```text
{{ figure.irregularity.soft_story_panel_b }}
```

### Item 637 — field — COMPUTED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 638 — paragraph — FIXED → COMPUTED

Keys: analysis.soft_storey_result.

**Before:**

```text
No soft stoy is observed in the building.
```

**Proposed after:**

```text
{{ analysis.soft_storey_result }}
```

### Item 640 — paragraph — VARIABLE → VARIABLE

Keys: codes.clauses.in_plane_discontinuity.

**Before:**

```text
As per the clause 5.5.1.4 of NBC 105:2020, if there is an in-plane offset of a vertical seismic force-resisting element resulting in overturning demands on supporting structural elements, then there will be in-plane discontinuity in vertical lateral force resisting element type of irregularity.
```

**Proposed after:**

```text
As per the clause {{ codes.clauses.in_plane_discontinuity }} of {{ codes.edition }}, if there is an in-plane offset of a vertical seismic force-resisting element resulting in overturning demands on supporting structural elements, then there will be in-plane discontinuity in vertical lateral force resisting element type of irregularity.
```

### Item 641 — paragraph — FIXED → COMPUTED

Keys: analysis.in_plane_discontinuity_result.

**Before:**

```text
No in-plane discontinuity is present in the structure.
```

**Proposed after:**

```text
{{ analysis.in_plane_discontinuity_result }}
```

### Item 643 — image — FIXED → IMAGE

Keys: figure.irregularity.in_plane_discontinuity.

**Before:**

```text
Image 44: caption=Figure 28: In-Plane Discontinuity; size=2.2966 × 1.9933 in
```

**Proposed after:**

```text
{{ figure.irregularity.in_plane_discontinuity }}
```

### Item 645 — field — IMAGE → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 647 — paragraph — COMPUTED → VARIABLE

Keys: codes.clauses.mass_irregularity, codes.limits.mass_irregularity_effective_mass_difference_pct.

**Before:**

```text
If there is a difference of more than 50% between the effective masses of two consecutive storys, then there will be the existence of mass irregularity in the structural system of the building as per the clause 5.5.1.5 of NBC 105:2020. However, for such checks, light roofs, penthouse and mezzanine floors are not to be considered. The Designer is required to carry out the check for mass irregularity in the structural
```

**Proposed after:**

```text
If there is a difference of more than {{ codes.limits.mass_irregularity_effective_mass_difference_pct }}% between the effective masses of two consecutive storys, then there will be the existence of mass irregularity in the structural system of the building as per the clause {{ codes.clauses.mass_irregularity }} of {{ codes.edition }}. However, for such checks, light roofs, penthouse and mezzanine floors are not to be considered. The Designer is required to carry out the check for mass irregularity in the structural
```

### Item 651 — paragraph — IMAGE → COMPUTED

Keys: analysis.mass_irregularity_result.

**Before:**

```text
No mass irregularity is seen as the stories are nearly identical.
```

**Proposed after:**

```text
{{ analysis.mass_irregularity_result }}
```

### Item 654 — paragraph — IMAGE → VARIABLE

Keys: codes.clauses.reentrant_corner, codes.limits.reentrant_corner_projection_pct.

**Before:**

```text
As per the clause 5.5.2.2 of NBC 105:2020, a structure is said to have re-entrant corner irregularity in a direction if its structural configuration has a projection of greater than 15% of its overall dimensions in that direction.
```

**Proposed after:**

```text
As per the clause {{ codes.clauses.reentrant_corner }} of {{ codes.edition }}, a structure is said to have re-entrant corner irregularity in a direction if its structural configuration has a projection of greater than {{ codes.limits.reentrant_corner_projection_pct }}% of its overall dimensions in that direction.
```

### Item 655 — paragraph — FIXED → COMPUTED

Keys: analysis.reentrant_corner_result.

**Before:**

```text
The building is rectangular in shape with no re-entrant corners.
```

**Proposed after:**

```text
{{ analysis.reentrant_corner_result }}
```

### Item 657 — image — IMAGE → IMAGE

Keys: figure.irregularity.re_entrant_corners.

**Before:**

```text
Image 45: caption=Figure 29: Re-entrant corners; size=2.8173 × 1.9933 in
```

**Proposed after:**

```text
{{ figure.irregularity.re_entrant_corners }}
```

### Item 659 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 662 — paragraph — FIXED → VARIABLE

Keys: codes.clauses.diaphragm_discontinuity, codes.limits.diaphragm_opening_area_pct, codes.limits.diaphragm_stiffness_change_pct.

**Before:**

```text
If the diaphragm of a building has a cutout or open area greater than 50% of the gross enclosed diaphragm area or if the effective diaphragm stiffness changes more than 50% from one story to the next, then as per the clause 5.5.2.3 of NBC 105:2020, the building is said to have diaphragm discontinuity irregularity. The Designer is required to check the existence of such irregularity in the building and provide the details in the structural design report.
```

**Proposed after:**

```text
If the diaphragm of a building has a cutout or open area greater than {{ codes.limits.diaphragm_opening_area_pct }}% of the gross enclosed diaphragm area or if the effective diaphragm stiffness changes more than {{ codes.limits.diaphragm_stiffness_change_pct }}% from one story to the next, then as per the clause {{ codes.clauses.diaphragm_discontinuity }} of {{ codes.edition }}, the building is said to have diaphragm discontinuity irregularity. The Designer is required to check the existence of such irregularity in the building and provide the details in the structural design report.
```

### Item 665 — image — FIXED → IMAGE

Keys: figure.irregularity.diaphragm_discontinuity.

**Before:**

```text
Image 46: caption=Figure 30: Diaphragm Discontinuity; size=3.9852 × 1.2133 in
```

**Proposed after:**

```text
{{ figure.irregularity.diaphragm_discontinuity }}
```

### Item 666 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Figure 30: Diaphragm Discontinuity
```

**Proposed after:**

```text
[review mapping required]
```

### Item 667 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 669 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Out-of-plane Offset
```

**Proposed after:**

```text
[review mapping required]
```

### Item 670 — paragraph — FIXED → VARIABLE

Keys: codes.clauses.out_of_plane_offset.

**Before:**

```text
If there is a discontinuity in a lateral force resisting path such as an out-of-plane of at least one vertical element in the structural system of the building, then as per the clause 5.5.2.4 of NBC 105:2020, the building is said to have out of plane irregularity. No out-of-plane offset can be seen as per the drawings.
```

**Proposed after:**

```text
If there is a discontinuity in a lateral force resisting path such as an out-of-plane of at least one vertical element in the structural system of the building, then as per the clause {{ codes.clauses.out_of_plane_offset }} of {{ codes.edition }}, the building is said to have out of plane irregularity. No out-of-plane offset can be seen as per the drawings.
```

### Item 671 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 674 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 675 — image — FIXED → IMAGE

Keys: figure.irregularity.out_of_plane_offset.

**Before:**

```text
Image 47: caption=Figure 31: Out of plane offset; size=3.5243 × 1.295 in
```

**Proposed after:**

```text
{{ figure.irregularity.out_of_plane_offset }}
```

### Item 676 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
Figure 31: Out of plane offset
```

**Proposed after:**

```text
[review mapping required]
```

### Item 677 — field — FIXED → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 678 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 681 — image — FIXED → IMAGE

Keys: figure.summary.design_summary.

**Before:**

```text
Image 48: caption=(none); size=6.8819 × 1.9896 in
```

**Proposed after:**

```text
{{ figure.summary.design_summary }}
```

### Item 683 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 684 — image — FIXED → IMAGE

Keys: figure.summary.design_summary_panel_b.

**Before:**

```text
Image 49: caption=(none); size=6.8812 × 2.2641 in
```

**Proposed after:**

```text
{{ figure.summary.design_summary_panel_b }}
```

### Item 686 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 687 — image — FIXED → IMAGE

Keys: figure.summary.design_summary_panel_c.

**Before:**

```text
Image 50: caption=(none); size=6.8812 × 1.442 in
```

**Proposed after:**

```text
{{ figure.summary.design_summary_panel_c }}
```

### Item 688 — paragraph — IMAGE → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 690 — paragraph — COMPUTED → FIXED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text

```

**Proposed after:**

```text
[review mapping required]
```

### Item 696 — image — not in previous inventory → IMAGE

Keys: figure.elements.required_longitudinal_reinforcement_mm_in_beams_columns.

**Before:**

```text
Image 51: caption=Figure 32: Required longitudinal reinforcement (mm²) in beams and columns along Grid A.; size=6.9924 × 5.9007 in
```

**Proposed after:**

```text
{{ figure.elements.required_longitudinal_reinforcement_mm_in_beams_columns }}
```

### Item 699 — field — not in previous inventory → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 701 — image — not in previous inventory → IMAGE

Keys: figure.elements.required_longitudinal_reinforcement_mm_in_beams_columns_panel_b.

**Before:**

```text
Image 52: caption=Figure 33: Required longitudinal reinforcement (mm²) in beams and columns along Grid B.; size=6.9924 × 6.2299 in
```

**Proposed after:**

```text
{{ figure.elements.required_longitudinal_reinforcement_mm_in_beams_columns_panel_b }}
```

### Item 704 — field — not in previous inventory → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 706 — image — not in previous inventory → IMAGE

Keys: figure.elements.required_longitudinal_reinforcement_mm_in_beams_at.

**Before:**

```text
Image 53: caption=Figure 34: Required longitudinal reinforcement (mm²) in beams at Story 1.; size=4.5006 × 8.8241 in
```

**Proposed after:**

```text
{{ figure.elements.required_longitudinal_reinforcement_mm_in_beams_at }}
```

### Item 708 — field — not in previous inventory → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 713 — image — not in previous inventory → IMAGE

Keys: figure.elements.required_longitudinal_reinforcement_mm_in_beams_at_panel_b.

**Before:**

```text
Image 54: caption=Figure 35: Required longitudinal reinforcement (mm²) in beams at Story 2.; size=4.5319 × 8.7825 in
```

**Proposed after:**

```text
{{ figure.elements.required_longitudinal_reinforcement_mm_in_beams_at_panel_b }}
```

### Item 716 — field — not in previous inventory → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

### Item 718 — image — not in previous inventory → IMAGE

Keys: figure.elements.required_longitudinal_reinforcement_mm_in_beams_at_panel_c.

**Before:**

```text
Image 55: caption=Figure 36: Required longitudinal reinforcement (mm²) in beams at Story 3.; size=4.6673 × 8.8971 in
```

**Proposed after:**

```text
{{ figure.elements.required_longitudinal_reinforcement_mm_in_beams_at_panel_c }}
```

### Item 720 — field — not in previous inventory → COMPUTED

Keys: (no registry key; Word regenerates this field or content is fixed).

**Before:**

```text
SEQ Figure \* ARABIC
```

**Proposed after:**

```text
Regenerated by Word; excluded from the value registry.
```

## Needs my decision

1. Confirm the NBC 105:2025 target clauses for sample references **NBC 105:2020 Cl. 2.1 (item 208)**, **Cl. 3.6.1 (item 418)**, **Cl. 5.5 (item 591)**, and **Cl. 5.5.2.1 (item 593)**. No target clause was invented.
2. Confirm the correct NBC 105:2025 mapping for **NBC 105:2077 Cl. 5.6.3 (items 533 and 535)**. These remain explicit unresolved `codes.clauses.serviceability_drift` variables.
3. Confirm source/meaning of table 16 (88 × 8, blank sample header) before assigning its final column keys and row-level source schema.
4. Confirm that tables 18–21 are fixed image-layout containers (two directional figure slots each), not conventional data tables.
5. Confirm which report figures will be generated from ETABS and which are engineer-supplied; the registry currently treats figure slots as optional Excel/user-file inputs pending Phase 4.
6. Confirm project input vs ETABS/e2k source for mixed-source tables (especially loads, building geometry, materials, and design schedules). The proposed `source` is a primary source label, not a silent conflict-resolution rule.
7. Confirm the project-specific values shown as examples (including storey count, grades, seismic factors, and reinforcement ratios); examples are copied from the sample and are not engineering recommendations.

## Table row models

- `table.client.general_information` — `fixed` rows; source: Fixed intake labels; values supplied from project/client input.; columns: 3.
- `table.codes.references` — `fixed` rows; source: Applicable code rows are selected from the approved project code list.; columns: 4.
- `table.building.general_information` — `fixed` rows; source: Fixed fields for site, permit/design storey counts, and project facts.; columns: 3.
- `table.elements.sizes_and_materials` — `fixed` rows; source: Fixed element rows populated from ETABS section/material assignments.; columns: 4.
- `table.design.structural_system_and_foundation` — `fixed` rows; source: Fixed three-row owner-defined table; the foundation row depends on the approved selection.; columns: 3.
- `table.modifiers.effective_stiffness` — `fixed` rows; source: Fixed component rows; values require project/code confirmation.; columns: 4.
- `table.loads.load_assessment` — `data-driven` rows; source: Load rows from ETABS tables/.e2k and confirmed user load inputs.; columns: 6.
- `table.loads.live_load_intensity` — `data-driven` rows; source: Rows depend on occupancy/room types and applicable load criteria.; columns: 3.
- `table.seismic.empirical_period_calculation` — `fixed` rows; source: Fixed calculation rows with project-specific inputs/results.; columns: 7.
- `table.seismic.vertical_force_distribution` — `data-driven` rows; source: One row per modeled storey; derived from project seismic weight and elevation.; columns: 7.
- `table.modal.rayleigh_x` — `data-driven` rows; source: One row per storey for the X-direction Rayleigh calculation.; columns: 8.
- `table.modal.rayleigh_y` — `data-driven` rows; source: One row per storey for the Y-direction Rayleigh calculation.; columns: 8.
- `table.seismic.design_parameters` — `fixed` rows; source: Fixed parameter labels; values sourced from approved code/project inputs and calculations.; columns: 4.
- `table.design.overstrength_factors` — `fixed` rows; source: Fixed parameter rows with project/code-dependent values.; columns: 2.
- `table.modal.periods_and_mass_participation` — `data-driven` rows; source: One row per requested ETABS mode; include the mass-adequacy threshold check.; columns: 7.
- `table.design.slab_design_output` — `data-driven` rows; source: ETABS slab design records; column/header semantics are unresolved because the sample header is blank.; columns: 8.
- `table.design.beam_deflection_check` — `fixed` rows; source: Fixed check labels; values/results depend on the project and calculation.; columns: 2.
- `table.drift.uls_displacement_figures_x_y` — `fixed` rows; source: Two directional figure slots in a fixed layout table.; columns: 2.
- `table.drift.sls_displacement_figures_x_y` — `fixed` rows; source: Two directional figure slots in a fixed layout table.; columns: 2.
- `table.drift.uls_story_drift_figures_x_y` — `fixed` rows; source: Two directional figure slots in a fixed layout table.; columns: 2.
- `table.drift.sls_story_drift_figures_x_y` — `fixed` rows; source: Two directional figure slots in a fixed layout table.; columns: 2.

## Source priority and unresolved data

Apply the project rule ETABS API/CSV > `.e2k` > Excel > computed. Record disagreements in a conflict log; do not silently choose. The source counts above are classifications for registry planning, not evidence that sample values have been revalidated.
