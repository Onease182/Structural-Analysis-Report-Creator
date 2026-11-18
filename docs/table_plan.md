# Table Plan

One row per table (T0-T20): fixed / cell-placeholders / data-driven loop.

| Table | Rows×Cols | Caption | Classification | Reason |
|-------|-----------|---------|----------------|--------|
| T0 | 10×3 | Client details | **cell-placeholders** | Fixed labels (S.N., field name), variable values (owner name, address, etc.) |
| T1 | 6×7 | Codes and References | **fixed** (with `{{ codes.edition }}`) | Code reference list; only the edition year is variable |
| T2 | 9×3 | Table 1: General Information of the Building | **cell-placeholders** | Fixed labels (A.1-01, etc.), variable values (location, storeys, etc.) |
| T3 | 6×4 | Table 2: General Information on Structural Elements | **cell-placeholders** | Fixed labels (Column, Beam, etc.), variable values (sizes, grades) |
| T4 | 3×3 | Table 3: Structural System & Foundation | **cell-placeholders** | Fixed labels (A.3-01, etc.), variable values (system type, foundation, slab) |
| T5 | 3×4 | Table 4: Effective stiffness | **fixed** | Code-defined stiffness modifiers; not project-specific |
| T6 | 39×6 | Table 5: Load Assessment | **irregular** (needs owner decision) | Merged cells, mixed structure; too irregular for simple loop |
| T7 | 9×3 | Table 6: Live load intensity | **fixed** | IS 875 Part 2 reference values; not project-specific |
| T8 | 6×7 | Table 8: Fundamental Time Period (Empirical) | **cell-placeholders** | Fixed labels, variable values (height, system type, period) |
| T9 | 6×7 | Table 9: Vertical distribution of ULS seismic forces | **data-driven loop** | One row per storey; already templated |
| T10 | 7×8 | Table 10: Rayleigh time period, X-direction | **data-driven loop** | One row per storey; already templated |
| T11 | 7×8 | Table 11: Rayleigh time period, Y-direction | **data-driven loop** | One row per storey; already templated |
| T12 | 15×4 | Table 12: Seismic design parameters | **cell-placeholders** | Fixed labels, variable values (period, Cd, Z, I, Rμ, Ωu, k, soil) |
| T13 | 4×2 | Table 12 (cont.): Overstrength factors | **cell-placeholders** | Fixed labels, variable values (Ωu, Ωs) |
| T14 | 11×7 | Table 13: Time period and mass participation | **data-driven loop** | One row per mode; already templated |
| T15 | 88×8 | Design of Slabs | **irregular** (needs owner decision) | ETABS slab design output; blank headers, 88 rows; too irregular for simple loop |
| T16 | 14×2 | Table 14: Check for Deflection for beam | **cell-placeholders** | Fixed labels, variable values (boundary, span, deflection) |
| T17 | 2×2 | Drift figures (ULS displacement) | **fixed** | Image layout containers; not data tables |
| T18 | 2×2 | Drift figures (SLS displacement) | **fixed** | Image layout containers; not data tables |
| T19 | 2×2 | Drift figures (ULS story drift) | **fixed** | Image layout containers; not data tables |
| T20 | 2×2 | Drift figures (SLS story drift) | **fixed** | Image layout containers; not data tables |

## Cell-placeholder tables: key mapping

### T0 (Client details)
| Row | Col 0 (S.N.) | Col 1 (Label) | Col 2 (Value) → Key |
|-----|-------------|---------------|---------------------|
| 0 | — | "General Information:" | — |
| 1 | 1 | "Name of the Building Owner:" | `{{ client.owner_name }}` |
| 2 | 2 | "Address:" | `{{ building.location }}` |
| 3 | 3 | "Occupancy Type of the Building:" | `{{ building.occupancy }}` |
| 4 | 4 | "Number of Storys proposed for Design:" | `{{ building.storeys_above_grade }}` |
| 5-8 | ... | (designer/consultant info) | `{{ client.designer_name }}`, `{{ client.consultant_name }}`, etc. |

### T2 (Building general info)
| Row | Col 0 (Code) | Col 1 (Label) | Col 2 (Value) → Key |
|-----|-------------|---------------|---------------------|
| 0 | A.1-01 | "Location of Building" | `{{ building.location }}` |
| 1 | A.1-02 | "Number of Storys..." | `{{ building.storeys_above_grade }}` |
| 2 | A.1-03 | "Occupancy Type" | `{{ building.occupancy }}` |
| 3+ | ... | (heights, spans, etc.) | `{{ building.story_height_m }}`, `{{ building.span_x_m }}`, etc. |

### T3 (Element sizes)
| Row | Col 0 (Element) | Col 1 (Description) → Key | Col 2 (Grade) → Key | Col 3 (Remarks) |
|-----|----------------|---------------------------|---------------------|-----------------|
| 1 | "Column" | `{{ table.elements.col_desc }}` | `{{ materials.concrete_grade_used }}` | — |
| 2 | "Beam" | `{{ table.elements.beam_desc }}` | `{{ materials.concrete_grade_used }}` | — |
| ... | ... | ... | ... | — |

### T4 (Structural system & foundation)
| Row | Col 0 | Col 1 (Label) | Col 2 (Value) → Key |
|-----|--------|---------------|---------------------|
| 0 | A.3-01 | "Type of Structural System" | `{{ structural.system_type }}` |
| 1 | A.3-02 | "Type of Foundation" | `{{ foundation.type }}` |
| 2 | A.3-03 | "Type of Slab used" | `{{ slab.type }}` |

### T8 (Empirical period)
Variable cells: height (→ `{{ building.total_height_m }}`), system type (→ `{{ structural.system_type }}`), period result (→ `{{ modal.empirical_period_s }}`).

### T12 (Seismic design parameters)
Variable cells: period (→ `{{ modal.empirical_period_s }}`), Cd (→ `{{ seismic.spectral_coefficient_cd }}`), Z (→ `{{ seismic.zone_factor_z }}`), I (→ `{{ seismic.importance_factor_i }}`), Rμ (→ `{{ seismic.response_modification_factor_rmu }}`), Ωu (→ `{{ design.overstrength_ultimate }}`), k (→ `{{ seismic.distribution_exponent_k }}`), soil (→ `{{ seismic.soil_class }}`).

### T13 (Overstrength factors)
| Row | Col 0 (Label) | Col 1 (Value) → Key |
|-----|---------------|---------------------|
| 0 | "Over strength Factor Ultimate" | `{{ design.overstrength_ultimate }}` |
| 1 | "Over strength Factor Serviceability" | `{{ design.overstrength_serviceability }}` |
| 2+ | ... | ... |

### T16 (Beam deflection check)
Variable cells: boundary condition, span, deflection values, pass/fail status.

## Irregular tables (need owner decision)

### T6 (Load Assessment, 39×6)
Merged cells, mixed structure (wall loads, floor finish, live loads, load cases, mass sources all in one table). Too irregular for a simple `{%tr for %}` loop.

**Options** (listed in docs/needs_my_decision.md):
1. **docxtpl Subdoc**: build the table as a separate DOCX fragment and insert via `Subdoc`.
2. **Code-built table**: build the table programmatically using python-docx, reusing the sample's cell formatting.
3. **Split into multiple tables**: break the load assessment into separate tables (wall loads, live loads, load cases, mass sources) each with its own loop.

### T15 (Slab Design, 88×8)
ETABS slab design output with blank headers. 88 rows of raw ETABS data.

**Options** (listed in docs/needs_my_decision.md):
1. **Code-built table**: build programmatically from ETABS CSV data.
2. **Keep as image**: replace the table with a screenshot of the ETABS slab design output.
3. **Skip entirely**: omit the slab design table if the data is not available.

## Loop tag balance
Each data-driven loop table must have balanced `{%tr for %}` / `{%tr endfor %}` tags. Verified by test.
