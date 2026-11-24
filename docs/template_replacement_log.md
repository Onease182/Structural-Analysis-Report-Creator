# Template Replacement Log

Total replacements: **141**.

| # | Location | Old text (preview) | Placeholder |
|---|----------|-------------------|-------------|
| 1 | paragraph idx=0 | Structural report of Residence Building of Chatra Bahadur Ramtel  | `{{ project.report_title }}` |
| 2 | paragraph idx=11 | Swarup Engineering Consultancy  | `{{ client.consultant_name }}` |
| 3 | paragraph idx=12 | Dharan-16, Sunsari | `{{ building.location }}` |
| 4 | paragraph idx=195 (sentence template) | The building has three floors made of reinforced concrete frames and filled with | `The building has {{ building.storeys_above_grade }} floors made of {{ building.primary_frame_materia` |
| 5 | paragraph idx=196 (sentence template) | brick walls. Each floor has a height of 3.175 meters. The building is laid out in a rectangular grid | `{{ building.infill_wall_material }} walls. Each floor has a height of {{ building.story_height_m }} ` |
| 6 | paragraph idx=240 (sentence template) | As the building is less than 12 m in height, M20 concrete has been taken for all the structural comp | `As the building is less than 12 m in height, {{ materials.concrete_grade_used }} concrete has been t` |
| 7 | paragraph idx=254 (sentence template) | Steel Grade of Fe500 has been used in the longitudinal and transverse reinforcement. | `Steel Grade of {{ materials.rebar_grade_used }} has been used in the longitudinal and transverse rei` |
| 8 | paragraph idx=288 (sentence template) | The building was modeled using the ETABS 19.0.0 software. ETABS 19.0.0 is a specialized program desi | `The building was modeled using the {{ foundation.modeling_software }} software. {{ foundation.modeli` |
| 9 | paragraph idx=410 (sentence template) | Base shear from ETABS 240.02 kN.  | `Base shear from ETABS {{ modal.base_shear_etabs }} kN.` |
| 10 | paragraph idx=381 |  | `{{ codes.clauses.vertical_force_dist }}` |
| 11 | paragraph idx=414 (sentence template) | k = 1.004 (T = 0.508 s); Cd = 0.1458; V = Cd·W, W taken above Base. Z = 0.35, soil C, I = 1.0, Rμ =  | `k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi` |
| 12 | paragraph idx=425 (sentence template) | As Empirical time period (0.508 sec) is lesser than the Rayleigh time period (0.531 sec), use empiri | `As Empirical time period ({{ modal.empirical_period_s }} sec) is lesser than the Rayleigh time perio` |
| 13 | paragraph idx=397 | Detailed Load Calculations | `{{ codes.clauses.spectral_shape_factor }}` |
| 14 | paragraph idx=397 | Detailed Load Calculations | `{{ codes.clauses.seismic_zoning_factor }}` |
| 15 | paragraph idx=397 | Detailed Load Calculations | `{{ codes.clauses.importance_factor }}` |
| 16 | paragraph idx=443 | As per Clause 3.2.1 of NBC 105:2025, the Equivalent Static Method may be used for all serviceability | `{{ codes.clauses.equivalent_static_method }}` |
| 17 | paragraph idx=443 (sentence template) | As per Clause {{ codes.clauses.equivalent_static_method }} of {{ codes.edition }}, the Equivalent St | `As per Clause {{ codes.clauses.equivalent_static_method }} of {{ codes.edition }}, the Equivalent St` |
| 18 | paragraph idx=460 | NBC105:2025 clause 7.3 states that number of modes to be used in the analysis should be such that th | `{{ codes.clauses.modal_mass_participation }}` |
| 19 | paragraph idx=460 (sentence template) | {{ codes.edition }} clause {{ codes.clauses.modal_mass_participation }} states that number of modes  | `{{ codes.edition }} clause {{ codes.clauses.modal_mass_participation }} states that number of modes ` |
| 20 | paragraph idx=480 (sentence template) | = 1557/ (355*355)*100% =1.24% <4% (Ok) | `= {{ design.column.max_rebar_area_mm2 }}/ ({{ design.column.max_section_width_mm }}*{{ design.column` |
| 21 | paragraph idx=484 (sentence template) | = 1.026%> 1% (Ok) | `= {{ design.column.min_provided_pct }}% > {{ design.column.min_limit_pct }}% ({{ design.column.min_s` |
| 22 | paragraph idx=486 (sentence template) | = 678.584/ (250*355) = 0.764% <2.5% (Ok) | `= {{ design.beam.max_rebar_area_mm2 }}/ ({{ design.beam.max_section_width_mm }}*{{ design.beam.max_s` |
| 23 | paragraph idx=488 (sentence template) | = 0.764% >0.26 % (Ok) | `= {{ design.beam.min_provided_pct }}% >{{ design.beam.min_limit_pct }} % ({{ design.beam.min_status ` |
| 24 | paragraph idx=533 |  | `{{ codes.clauses.serviceability_drift }}` |
| 25 | paragraph idx=565 (sentence template) | 5.6.3 of NBC 105:2077 is applied. The maximum deflection in any story due to the minimum specified d | `{{ codes.clauses.serviceability_drift }} of {{ codes.edition }} is applied. The maximum deflection i` |
| 26 | paragraph idx=591 |  | `{{ codes.clauses.irregularity_general }}` |
| 27 | paragraph idx=623 | As per the clause 5.5.2.1 of NBC 105:2020, torsion irregularity is considered to exist when the maxi | `{{ codes.clauses.torsional_irregularity }}` |
| 28 | paragraph idx=623 (sentence template) | As per the clause {{ codes.clauses.torsional_irregularity }} of {{ codes.edition }}, torsion irregul | `As per the clause {{ codes.clauses.torsional_irregularity }} of {{ codes.edition }}, torsion irregul` |
| 29 | paragraph idx=633 | As per the clause 5.5.1.2, a soft story is the one whose stiffness of the lateral force resisting sy | `{{ codes.clauses.soft_storey }}` |
| 30 | paragraph idx=633 (sentence template) | As per the clause {{ codes.clauses.soft_storey }}, a soft story is the one whose stiffness of the la | `As per the clause {{ codes.clauses.soft_storey }} of {{ codes.edition }}, a soft story is the one wh` |
| 31 | paragraph idx=647 | If there is a difference of more than 50% between the effective masses of two consecutive storys, th | `{{ codes.clauses.mass_irregularity }}` |
| 32 | paragraph idx=647 (sentence template) | If there is a difference of more than 50% between the effective masses of two consecutive storys, th | `If there is a difference of more than {{ codes.limits.mass_irregularity_diff_pct }}% between the eff` |
| 33 | paragraph idx=654 | As per the clause 5.5.2.2 of NBC 105:2020, a structure is said to have re-entrant corner irregularit | `{{ codes.clauses.reentrant_corner }}` |
| 34 | paragraph idx=654 (sentence template) | As per the clause {{ codes.clauses.reentrant_corner }} of {{ codes.edition }}, a structure is said t | `As per the clause {{ codes.clauses.reentrant_corner }} of {{ codes.edition }}, a structure is said t` |
| 35 | paragraph idx=662 | If the diaphragm of a building has a cutout or open area greater than 50% of the gross enclosed diap | `{{ codes.clauses.diaphragm_discontinuity }}` |
| 36 | paragraph idx=662 (sentence template) | If the diaphragm of a building has a cutout or open area greater than 50% of the gross enclosed diap | `If the diaphragm of a building has a cutout or open area greater than {{ codes.limits.diaphragm_open` |
| 37 | paragraph idx=610 |  | `{{ codes.clauses.in_plane_discontinuity }}` |
| 38 | paragraph idx=640 | As per the clause 5.5.1.4 of NBC 105:2020, if there is an in-plane offset of a vertical seismic forc | `{{ codes.clauses.out_of_plane_offset }}` |
| 39 | paragraph idx=286 | the foundation is assumed to be fixed. | `{{ foundation.support_condition }}` |
| 40 | paragraph idx=638 | No soft stoy is observed in the building. | `{{ analysis.soft_storey_result }}` |
| 41 | paragraph idx=651 | No mass irregularity is seen as the stories are nearly identical. | `{{ analysis.mass_irregularity_result }}` |
| 42 | paragraph idx=40 | Er. Anij Bhandari | `{{ designer.name }}` |
| 43 | paragraph idx=41 | NEC No.13925 Civil “A” Category | `{{ designer.nec_no }}` |
| 44 | caption idx=411 (partial) | Table 9:  Vertical distribution of ULS seismic forces (NBC 105:2025 Cl. 6.3) | `Table 9:  Vertical distribution of ULS seismic forces ({{ codes.edition }} Cl. {{ codes.clauses.vert` |
| 45 | caption idx=435 (partial) | Table 12: Seismic design parameters for the RC moment resisting frame in Damak (NBC 105:2025). | `Table 12: Seismic design parameters for the RC moment resisting frame in {{ building.location }} ({{` |
| 46 | style override for analysis.mass_irregularity_result | style: Heading4 | `style: BodyText` |
| 47 | anchored image idx=2 (preserved) | [anchored image, cx=6048375 cy=45085] | `preserved (use replace_pic with rId=None)` |
| 48 | image idx=5 | [image #5] | `{{ figure.project.report_figure }}` |
| 49 | image idx=251 | [image #251] | `{{ figure.irregularity.acc_eccentricity }}` |
| 50 | image idx=332 | [image #332] | `{{ figure.loads.live_first }}` |
| 51 | image idx=362 | [image #362] | `{{ figure.project.mass_sources_b }}` |
| 52 | image idx=501 | [image #501] | `{{ figure.foundation.design_main }}` |
| 53 | image idx=508 | [image #508] | `{{ figure.foundation.design_c }}` |
| 54 | image idx=522 | [image #522] | `{{ figure.staircase.design_c }}` |
| 55 | image idx=542 | [image #542] | `{{ figure.drift.displacement }}` |
| 56 | image idx=605 | [image #605] | `{{ figure.irregularity.soft_story_panel_b }}` |
| 57 | image idx=613 | [image #613] | `{{ figure.irregularity.in_plane }}` |
| 58 | anchored image idx=635 (preserved) | [anchored image, cx=1280787 cy=1980247] | `preserved (use replace_pic with rId=rId65)` |
| 59 | anchored image idx=657 (preserved) | [anchored image, cx=2576128 cy=1822703] | `preserved (use replace_pic with rId=rId67)` |
| 60 | image idx=683 | [image #683] | `{{ figure.elements.rebar_story2 }}` |
| 61 | table T0 cell (1,2) | Mr. Chatra Bahadur Ramtel | `{{ client.owner_name }}` |
| 62 | table T0 cell (2,2) | Damak | `{{ building.location }}` |
| 63 | table T0 cell (3,2) | Residential | `{{ building.occupancy_class }}` |
| 64 | table T0 cell (4,2) | Mr. Anij Bhandari | `{{ client.designer_name }}` |
| 65 | table T0 cell (5,2) | 13925 ”Civil A” | `{{ client.designer_nec_reg }}` |
| 66 | table T0 cell (6,2) | 9862123845 | `{{ client.designer_contact }}` |
| 67 | table T0 cell (7,2) | Swarup Engineering Consultancy | `{{ client.consultant_name }}` |
| 68 | table T0 cell (8,2) | 123 | `{{ client.municipality_reg }}` |
| 69 | table T0 cell (9,2) | 2026/11/24 | `{{ client.application_date }}` |
| 70 | table T2 cell (0,2) | Damak | `{{ building.location }}` |
| 71 | table T2 cell (1,2) | 3 | `{{ building.storeys_count_numeric }}` |
| 72 | table T2 cell (2,2) | 3 | `{{ building.num_storeys_analysed }}` |
| 73 | table T2 cell (3,2) | 0 | `{{ building.num_basements }}` |
| 74 | table T2 cell (4,2) | 3.175 meters | `{{ building.height_ground_floor_m }} meters` |
| 75 | table T2 cell (5,2) | 3.175 meters | `{{ building.height_typical_floor_m }} meters` |
| 76 | table T2 cell (6,2) | 9.525 meters | `{{ building.total_height_m }} meters` |
| 77 | table T2 cell (7,2) | 9.525 meters | `{{ building.height_period_m }} meters` |
| 78 | table T2 cell (8,2) | Residential Building | `{{ building.occupancy_class }} Building` |
| 79 | table T3 cell (1,1) | 355 mm X 355 mm | `{{ table.elements.col_desc }}` |
| 80 | table T3 cell (1,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 81 | table T3 cell (2,1) | 250 mm X 430 mm | `{{ table.elements.beam_desc }}` |
| 82 | table T3 cell (2,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 83 | table T3 cell (3,1) | 150 mm | `{{ table.elements.stair_desc }}` |
| 84 | table T3 cell (3,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 85 | table T3 cell (4,1) | 125 mm | `{{ table.elements.slab_desc }}` |
| 86 | table T3 cell (4,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 87 | table T3 cell (5,1) | Combined Footing | `{{ table.elements.foundation_desc }}` |
| 88 | table T3 cell (5,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 89 | table T3 cell (5,3) | Soil Bearing Capacity is taken as 120 kN/m2 | `{{ foundation.soil_bearing }}` |
| 90 | table T4 cell (0,2) | Moment Resisting Frames | `{{ structural.system_type_generic }}` |
| 91 | table T4 cell (1,2) | Combined Footing | `{{ foundation.type }}` |
| 92 | table T4 cell (2,2) | Conventional | `{{ slab.type }}` |
| 93 | table T8 cell (0,5) | 9.525 | `{{ building.total_height_m }}` |
| 94 | table T8 cell (1,1) | Moment Resisting Concrete Frame | `{{ structural.system_type_period_category }}` |
| 95 | table T8 cell (2,1) | 0.075 | `{{ seismic.time_coefficient_kt }}` |
| 96 | table T8 cell (3,4) | 0.407 | `{{ modal.empirical_period_unamplified_s }}` |
| 97 | table T8 cell (5,3) | 0.508 | `{{ modal.empirical_period_s }}` |
| 98 | table T12 cell (0,2) | 0.508 | `{{ modal.empirical_period_s }}` |
| 99 | table T12 cell (2,2) | Very Soft Soil | `{{ seismic.site_soil_category }}` |
| 100 | table T12 cell (3,3) | 1 | `{{ seismic.tc }}` |
| 101 | table T12 cell (4,2) | C | `{{ seismic.soil_class }}` |
| 102 | table T12 cell (5,1) | 2.5 | `{{ seismic.alpha }}` |
| 103 | table T12 cell (6,2) | 2.50 | `{{ seismic.spectral_shape_factor_cht }}` |
| 104 | table T12 cell (7,1) | Damak | `{{ building.location }}` |
| 105 | table T12 cell (7,3) | 0.35 | `{{ seismic.zone_factor_z }}` |
| 106 | table T12 cell (8,2) | Ordinary Structures | `{{ seismic.structural_type }}` |
| 107 | table T12 cell (9,2) | 1 | `{{ seismic.importance_factor_i_table }}` |
| 108 | table T12 cell (10,3) | 0.875 | `{{ seismic.elastic_site_spectra_c }}` |
| 109 | table T12 cell (11,3) | 0.175 | `{{ seismic.elastic_site_spectra_cs }}` |
| 110 | table T12 cell (13,3) | Reinforced Concrete Moment Resisting Frame | `{{ structural.system_type_table_5_2 }}` |
| 111 | table T12 cell (14,3) | 4 | `{{ seismic.response_modification_factor_rmu }}` |
| 112 | table T13 cell (0,1) | 1.5 | `{{ design.overstrength_ultimate }}` |
| 113 | table T13 cell (1,1) | 1.25 | `{{ design.overstrength_serviceability }}` |
| 114 | table T13 cell (2,1) | 0.146 | `{{ seismic.hsc_uls }}` |
| 115 | table T13 cell (3,1) | 0.140 | `{{ seismic.hsc_sls }}` |
| 116 | table T16 cell (1,1) | Continuous | `{{ table.design.beam_boundary }}` |
| 117 | table T16 cell (2,1) | 4191 mm | `{{ table.design.beam_effective_span }}` |
| 118 | table T16 cell (3,1) | 430 mm | `{{ table.design.beam_overall_depth }}` |
| 119 | table T16 cell (4,1) | 395 mm | `{{ table.design.beam_effective_depth }}` |
| 120 | table T16 cell (5,1) | 26 | `{{ table.design.beam_basic_ld_ratio }}` |
| 121 | table T16 cell (6,1) | 186 mm² | `{{ table.design.beam_ast_req }}` |
| 122 | table T16 cell (7,1) | 226 mm² | `{{ table.design.beam_ast_prov }}` |
| 123 | table T16 cell (8,1) | 0.229 % | `{{ table.design.beam_pt }}` |
| 124 | table T16 cell (9,1) | 239 N/mm² | `{{ table.design.beam_fs }}` |
| 125 | table T16 cell (10,1) | ≈ 1.68 | `{{ table.design.beam_mod_factor }}` |
| 126 | table T16 cell (11,1) | 43.7 | `{{ table.design.beam_permissible_ld }}` |
| 127 | table T16 cell (12,1) | 10.61 | `{{ table.design.beam_provided_ld }}` |
| 128 | table T16 cell (13,1) | 10.61 < 43.7, OK | `{{ table.design.beam_check_result }}` |
| 129 | table T15 | [88×8 slab design table] | `{{ figure.design.slab_sheet }} (image placeholder)` |
| 130 | hard-coded clause in paragraph | Ch(t)=Spectral Shape factor as per cl.4.1.2 Z= Seismic Zoning Factor as per 4.1. | `Ch(t)=Spectral Shape factor as per cl.4.1.2 Z= Seismic Zoning Factor as per {{ c` |
| 131 | hard-coded clause in paragraph | For Parallel System (Cl. 3.6.1) | `For Parallel System (Cl. {{ codes.clauses.load_combinations }})` |
| 132 | table T9 footer | [row 5] | `placeholders: ['totals.wi_kg', 'totals.wi_hik', 'totals.fi']` |
| 133 | table T9 (loop) | [6 rows → 5 rows] | `for + template + endfor + 1 footer(s)` |
| 134 | table T10 footer | [row 5] | `placeholders: ['totals.fi', 'totals.fi_di_x', 'totals.wi_di2_x']` |
| 135 | table T10 footer | [row 6] | `placeholders: ['modal.rayleigh_period_x_s']` |
| 136 | table T10 (loop) | [7 rows → 6 rows] | `for + template + endfor + 2 footer(s)` |
| 137 | table T11 footer | [row 5] | `placeholders: ['totals.fi', 'totals.fi_di_y', 'totals.wi_di2_y']` |
| 138 | table T11 footer | [row 6] | `placeholders: ['modal.rayleigh_period_y_s']` |
| 139 | table T11 (loop) | [7 rows → 6 rows] | `for + template + endfor + 2 footer(s)` |
| 140 | table T14 (loop) | [11 rows → 5 rows] | `for + template + endfor + 0 footer(s)` |
| 141 | paragraphs idx=400..409 | Design of Staircases block | `{%p if building.has_staircase %}...{%p endif %}` |
