# Table Cell Map

Derived from the ROW LABEL (column 1) in the original `Chatra Bahadur Ramtel.docx`,
not from position. Every value cell is mapped to a registry key.

## T0 (Client details, 10×3)

| Row | Label (col 1) | Value (col 2) | Key |
|-----|---------------|---------------|-----|
| 0 | (header) | — | — |
| 1 | Name of the Building Owner: | Mr. Chatra Bahadur Ramtel | `client.owner_name` |
| 2 | Address: | Damak | `building.location` |
| 3 | Occupancy Type of the Building as per byelaws: | Residential | `building.occupancy_class` |
| 4 | Name of the Structural Designer | Mr. Sachin KC | `client.designer_name` |
| 5 | NEC Registration no. of the Structural Designer: | 131xx"Civil A" | `client.designer_nec_reg` |
| 6 | Contact Number of the Structural Designer: | 9841xxxxxxx | `client.designer_contact` |
| 7 | Name of the Consulting Firm (if applicable): | CivoraX Infra | `client.consultant_name` |
| 8 | Municipality Registration No./ Application No.: | Xxxx | `client.municipality_reg` |
| 9 | Date of Application in Municipality: | 2026/xx/xx | `client.application_date` |

## T2 (Building general info, 9×3)

| Row | Code (col 0) | Label (col 1) | Value (col 2) | Key |
|-----|-------------|---------------|---------------|-----|
| 0 | A.1-01 | Location of Building | Damak | `building.location` |
| 1 | A.1-02 | Number of Storys proposed for Building Permit | 3 | `building.storeys_above_grade` |
| 2 | A.1-03 | Number of Storys considered in the Design | 3 | `building.num_storeys_analysed` |
| 3 | A.1-04 | Number of Basements | 0 | `building.num_basements` |
| 4 | A.1-05 | Height of Ground Floor | 3.175 meters | `building.height_ground_floor_m` |
| 5 | A.1-06 | Height of Typical Floor | 3.175 meters | `building.height_typical_floor_m` |
| 6 | A.1-07 | Total Height of the Building | 9.525 meters | `building.total_height_m` |
| 7 | A.1-08 | Height considered for Fundamental Time Period | 9.525 meters | `building.height_period_m` |
| 8 | A.1-09 | Occupancy Type of the Building according to the Building Code | Residential Building | `building.occupancy_class` |

## T3 (Element sizes, 6×4)

| Row | Element (col 0) | Description (col 1) | Key |
|-----|----------------|---------------------|-----|
| 0 | (header) | — | — |
| 1 | Column | 355 mm X 355 mm | `table.elements.col_desc` |
| 2 | Main Beam | 250 mm X 430 mm | `table.elements.beam_desc` |
| 3 | Staircase Slab | 150 mm | `table.elements.stair_desc` |
| 4 | Slab | 125 mm | `table.elements.slab_desc` |
| 5 | Foundation | Combined Footing | `table.elements.foundation_desc` |

Grade column (col 2) for all rows: `materials.concrete_grade_used`
Remarks (col 3) for Foundation row: `foundation.soil_bearing` (extracted from "Soil Bearing Capacity is taken as 120 kN/m2")

## T4 (Structural system & foundation, 3×3)

| Row | Code (col 0) | Label (col 1) | Value (col 2) | Key |
|-----|-------------|---------------|---------------|-----|
| 0 | A.3-01 | Type of Structural System | Moment Resisting Frames | `structural.system_type` |
| 1 | A.3-02 | Type of Foundation | Combined Footing | `foundation.type` |
| 2 | A.3-03 | Type of Slab used | Conventional | `slab.type` |

## T8 (Empirical period, 6×7)

| Row | Label | Value cell | Key |
|-----|-------|-----------|-----|
| 0 | Height of building from foundation... | (5,0) = "9.525" | `building.total_height_m` |
| 1 | Type of lateral resisting System | (1,1) = "Moment Resisting Concrete Frame" | `structural.system_type` |
| 2 | Time Coefficient (kt) | (2,1) = "0.075" | `seismic.time_coefficient_kt` |
| 3 | Approximate fundamental time period | (3,4) = "0.407" | `modal.empirical_period_unamplified_s` |
| 5 | Amplified Approximate Fundamental time period | (5,3) = "0.508" | `modal.empirical_period_s` |

## T12 (Seismic design parameters, 15×4)

| Row | Label | Value cell | Key |
|-----|-------|-----------|-----|
| 0 | Fundamental Time Period = | (0,2) = "0.508" | `modal.empirical_period_s` |
| 2 | Site Soil Category = | (2,2) = "Very Soft Soil" | `seismic.site_soil_category` |
| 3 | Tc = | (3,3) = "1" | `seismic.tc` |
| 4 | Soil Type = | (4,2) = "C" | `seismic.soil_class` |
| 5 | α = / k = | (5,1) = "2.5" / (5,3) = "1.004" | `seismic.alpha` / `seismic.distribution_exponent_k` |
| 6 | Ch(t) = | (6,2) = "2.50" | `seismic.spectral_shape_factor_cht` |
| 7 | Location = / PGA (Z) = | (7,1) = "Damak" / (7,3) = "0.35" | `building.location` / `seismic.zone_factor_z` |
| 8 | Structural Types = | (8,2) = "Ordinary Structures" | `seismic.structural_type` |
| 9 | Importance Factor = | (9,2) = "1" | `seismic.importance_factor_i` |
| 10 | C(t) = | (10,3) = "0.875" | `seismic.elastic_site_spectra_c` |
| 11 | Cs = | (11,3) = "0.175" | `seismic.elastic_site_spectra_cs` |
| 13 | Structural System = | (13,3) = "Reinforced Concrete..." | `structural.system_type` |
| 14 | Ductility Factor = | (14,3) = "4" | `seismic.response_modification_factor_rmu` |

## T13 (Overstrength factors, 4×2)

| Row | Label (col 0) | Value (col 1) | Key |
|-----|---------------|---------------|-----|
| 0 | Over strength Factor Ultimate limit State | 1.5 | `design.overstrength_ultimate` |
| 1 | Over strength Factor Serviceability limit State | 1.25 | `design.overstrength_serviceability` |
| 2 | For Ultimate Limit State = | 0.146 | `seismic.horizontal_seismic_coefficient_uls` |
| 3 | For Serviceability State = | 0.140 | `seismic.horizontal_seismic_coefficient_sls` |

## T16 (Beam deflection check, 14×2)

| Row | Label (col 0) | Value (col 1) | Key |
|-----|---------------|---------------|-----|
| 0 | (header) | — | — |
| 1 | Boundary condition of beam | Continuous | `table.design.beam_boundary` |
| 2 | Effective span, L | 4191 mm | `table.design.beam_effective_span` |
| 3 | Overall depth, D | 430 mm | `table.design.beam_overall_depth` |
| 4 | Effective depth, d | 395 mm | `table.design.beam_effective_depth` |
| 5 | Basic L/d ratio | 26 | `table.design.beam_basic_ld_ratio` |
| 6 | Ast,req (bottom, ETABS) | 186 mm² | `table.design.beam_ast_req` |
| 7 | Ast,prov (2-12φ) | 226 mm² | `table.design.beam_ast_prov` |
| 8 | pt = 100·Ast,prov/(b·d) | 0.229 % | `table.design.beam_pt` |
| 9 | fs = 0.58·fy·(Ast,req/Ast,prov) | 239 N/mm² | `table.design.beam_fs` |
| 10 | Modification factor | ≈ 1.68 | `table.design.beam_mod_factor` |
| 11 | Permissible L/d | 43.7 | `table.design.beam_permissible_ld` |
| 12 | Provided L/d | 10.61 | `table.design.beam_provided_ld` |
| 13 | Check | 10.61 < 43.7, OK | `table.design.beam_check_result` |
