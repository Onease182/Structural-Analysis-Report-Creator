# Template Replacement Log

Total replacements: **185**.

| # | Location | Old text (preview) | Placeholder |
|---|----------|-------------------|-------------|
| 1 | paragraph idx=0 | Structural report of Residence Building of Chatra Bahadur Ramtel  | `{{ project.report_title }}` |
| 2 | paragraph idx=11 | Civira X  | `{{ client.consultant_name }}` |
| 3 | paragraph idx=12 | Damak | `{{ building.location }}` |
| 4 | paragraph idx=164 (sentence template) | The building has three floors made of reinforced concrete frames and filled with | `The building has {{ building.storeys_above_grade }} floors made of {{ building.primary_frame_materia` |
| 5 | paragraph idx=165 (sentence template) | brick walls. Each floor has a height of 3.175 meters. The building is laid out in a rectangular grid | `{{ building.infill_wall_material }} walls. Each floor has a height of {{ building.story_height_m }} ` |
| 6 | paragraph idx=208 | According to NBC105:2020, The material should be taken as per Cl.2.1. | `{{ codes.clauses.material_properties }}` |
| 7 | paragraph idx=210 (sentence template) | As the building is less than 12 m in height, M20 concrete has been taken for all the structural comp | `As the building is less than 12 m in height, {{ materials.concrete_grade_used }} concrete has been t` |
| 8 | paragraph idx=224 (sentence template) | Steel Grade of Fe500 has been used in the longitudinal and transverse reinforcement. | `Steel Grade of {{ materials.rebar_grade_used }} has been used in the longitudinal and transverse rei` |
| 9 | paragraph idx=240 | Due to the eccentricity arising between the center of mass and the center of rigidity at each floor  | `{{ codes.clauses.eccentricity_intro }}` |
| 10 | paragraph idx=258 (sentence template) | The building was modeled using the ETABS 19.0.0 software. ETABS 19.0.0 is a specialized program desi | `The building was modeled using the {{ foundation.modeling_software }} software. {{ foundation.modeli` |
| 11 | paragraph idx=380 (sentence template) | Base shear from ETABS 240.02 kN.  | `Base shear from ETABS {{ modal.base_shear_etabs }} kN.` |
| 12 | paragraph idx=384 (sentence template) | k = 1.004 (T = 0.508 s); Cd = 0.1458; V = Cd·W, W taken above Base. Z = 0.35, soil C, I = 1.0, Rμ =  | `k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi` |
| 13 | paragraph idx=395 (sentence template) | As Empirical time period (0.508 sec) is lesser than the Rayleigh time period (0.531 sec), use empiri | `As Empirical time period ({{ modal.empirical_period_s }} sec) is lesser than the Rayleigh time perio` |
| 14 | paragraph idx=397 | Ch(t)=Spectral Shape factor as per cl.4.1.2 Z= Seismic Zoning Factor as per 4.1.4 I=Importance facto | `{{ codes.clauses.spectral_shape_factor }}` |
| 15 | paragraph idx=413 | As per Clause 3.2.1 of NBC 105:2025, the Equivalent Static Method may be used for all serviceability | `{{ codes.clauses.equivalent_static_method }}` |
| 16 | paragraph idx=413 (sentence template) | As per Clause {{ codes.clauses.equivalent_static_method }} of {{ codes.edition }}, the Equivalent St | `As per Clause {{ codes.clauses.equivalent_static_method }} of {{ codes.edition }}, the Equivalent St` |
| 17 | paragraph idx=418 | When lateral load resisting elements are oriented along mutually orthogonal horizontal directions, t | `{{ codes.clauses.load_combinations }}` |
| 18 | paragraph idx=430 | NBC105:2025 clause 7.3 states that number of modes to be used in the analysis should be such that th | `{{ codes.clauses.modal_mass_participation }}` |
| 19 | paragraph idx=430 (sentence template) | {{ codes.edition }} clause {{ codes.clauses.modal_mass_participation }} states that number of modes  | `{{ codes.edition }} clause {{ codes.clauses.modal_mass_participation }} states that number of modes ` |
| 20 | paragraph idx=450 (sentence template) | = 1557/ (355*355)*100% =1.24% <4% (Ok) | `= {{ design.column.max_rebar_area_mm2 }}/ ({{ design.column.max_section_width_mm }}*{{ design.column` |
| 21 | paragraph idx=454 (sentence template) | = 1.026%> 1% (Ok) | `= {{ design.column.min_provided_pct }}% > {{ design.column.min_limit_pct }}% ({{ design.column.min_s` |
| 22 | paragraph idx=456 (sentence template) | = 678.584/ (250*355) = 0.764% <2.5% (Ok) | `= {{ design.beam.max_rebar_area_mm2 }}/ ({{ design.beam.max_section_width_mm }}*{{ design.beam.max_s` |
| 23 | paragraph idx=458 (sentence template) | = 0.764% >0.26 % (Ok) | `= {{ design.beam.min_provided_pct }}% >{{ design.beam.min_limit_pct }} % ({{ design.beam.min_status ` |
| 24 | paragraph idx=533 | 5.6.3 of NBC 105:2077 is proposed to be used. | `{{ codes.clauses.serviceability_drift }}` |
| 25 | paragraph idx=535 (sentence template) | 5.6.3 of NBC 105:2077 is applied. The maximum deflection in any story due to the minimum specified d | `{{ codes.clauses.serviceability_drift }} of {{ codes.edition }} is applied. The maximum deflection i` |
| 26 | paragraph idx=591 | One of the basic virtues of earthquake resistant design of structures is that the structure shall be | `{{ codes.clauses.irregularity_general }}` |
| 27 | paragraph idx=593 | As per the clause 5.5.2.1 of NBC 105:2020, torsion irregularity is considered to exist when the maxi | `{{ codes.clauses.torsional_irregularity }}` |
| 28 | paragraph idx=593 (sentence template) | As per the clause {{ codes.clauses.torsional_irregularity }} of {{ codes.edition }}, torsion irregul | `As per the clause {{ codes.clauses.torsional_irregularity }} of {{ codes.edition }}, torsion irregul` |
| 29 | paragraph idx=603 | As per the clause 5.5.1.2, a soft story is the one whose stiffness of the lateral force resisting sy | `{{ codes.clauses.soft_storey }}` |
| 30 | paragraph idx=603 (sentence template) | As per the clause {{ codes.clauses.soft_storey }}, a soft story is the one whose stiffness of the la | `As per the clause {{ codes.clauses.soft_storey }} of {{ codes.edition }}, a soft story is the one wh` |
| 31 | paragraph idx=617 | If there is a difference of more than 50% between the effective masses of two consecutive storeys, t | `{{ codes.clauses.mass_irregularity }}` |
| 32 | paragraph idx=617 (sentence template) | If there is a difference of more than 50% between the effective masses of two consecutive storeys, t | `If there is a difference of more than {{ codes.limits.mass_irregularity_diff_pct }}% between the eff` |
| 33 | paragraph idx=624 | As per the clause 5.5.2.2 of NBC 105:2020, a structure is said to have re-entrant corner irregularit | `{{ codes.clauses.reentrant_corner }}` |
| 34 | paragraph idx=624 (sentence template) | As per the clause {{ codes.clauses.reentrant_corner }} of {{ codes.edition }}, a structure is said t | `As per the clause {{ codes.clauses.reentrant_corner }} of {{ codes.edition }}, a structure is said t` |
| 35 | paragraph idx=632 | If the diaphragm of a building has a cutout or open area greater than 50% of the gross enclosed diap | `{{ codes.clauses.diaphragm_discontinuity }}` |
| 36 | paragraph idx=632 (sentence template) | If the diaphragm of a building has a cutout or open area greater than 50% of the gross enclosed diap | `If the diaphragm of a building has a cutout or open area greater than {{ codes.limits.diaphragm_open` |
| 37 | paragraph idx=610 | As per the clause 5.5.1.4 of NBC 105:2020, if there is an in-plane offset of a vertical seismic forc | `{{ codes.clauses.in_plane_discontinuity }}` |
| 38 | paragraph idx=640 | If there is a discontinuity in a lateral force resisting path such as an out-of-plane of at least on | `{{ codes.clauses.out_of_plane_offset }}` |
| 39 | paragraph idx=256 | the foundation is assumed to be fixed. | `{{ foundation.support_condition }}` |
| 40 | paragraph idx=608 | No soft stoy is observed in the building. | `{{ analysis.soft_storey_result }}` |
| 41 | paragraph idx=611 | No in-plane discontinuity is present in the structure. | `{{ analysis.in_plane_discontinuity_result }}` |
| 42 | paragraph idx=621 | No mass irregularity is seen as the stories are nearly identical. | `{{ analysis.mass_irregularity_result }}` |
| 43 | paragraph idx=625 | The building is rectangular in shape with no re-entrant corners. | `{{ analysis.reentrant_corner_result }}` |
| 44 | caption idx=381 (partial) | Table 9:  Vertical distribution of ULS seismic forces (NBC 105:2025 Cl. 6.3) | `Table 9:  Vertical distribution of ULS seismic forces ({{ codes.edition }} Cl. {{ codes.clauses.vert` |
| 45 | caption idx=405 (partial) | Table 12: Seismic design parameters for the RC moment resisting frame in Damak (NBC 105:2025). | `Table 12: Seismic design parameters for the RC moment resisting frame in {{ building.location }} ({{` |
| 46 | style override for analysis.in_plane_discontinuity_result | style: Heading4 | `style: BodyText` |
| 47 | style override for analysis.mass_irregularity_result | style: Heading4 | `style: BodyText` |
| 48 | anchored image idx=2 (preserved) | [anchored image, cx=5274310 cy=6350] | `preserved (use replace_pic with rId=None)` |
| 49 | image idx=5 | [image #5] | `{{ figure.project.report_figure }}` |
| 50 | image idx=168 | [image #168] | `{{ figure.building.plan_of_building }}` |
| 51 | image idx=175 | [image #175] | `{{ figure.building.section_of_building }}` |
| 52 | image idx=212 | [image #212] | `{{ figure.materials.concrete }}` |
| 53 | image idx=221 | [image #221] | `{{ figure.materials.material_property_rebar }}` |
| 54 | anchored image idx=244 (preserved) | [anchored image, cx=541020 cy=542290] | `preserved (use replace_pic with rId=None)` |
| 55 | anchored image idx=245 (preserved) | [anchored image, cx=1988820 cy=490855] | `preserved (use replace_pic with rId=None)` |
| 56 | anchored image idx=251 (preserved) | [anchored image, cx=2919095 cy=1604010] | `preserved (use replace_pic with rId=rId18)` |
| 57 | anchored image idx=252 (preserved) | [anchored image, cx=81280 cy=1591945] | `preserved (use replace_pic with rId=None)` |
| 58 | image idx=293 | [image #293] | `{{ figure.loads.wall_first }}` |
| 59 | image idx=298 | [image #298] | `{{ figure.loads.wall_second }}` |
| 60 | image idx=302 | [image #302] | `{{ figure.loads.wall_third }}` |
| 61 | image idx=310 | [image #310] | `{{ figure.building.finish_first }}` |
| 62 | image idx=317 | [image #317] | `{{ figure.building.finish_second }}` |
| 63 | image idx=332 | [image #332] | `{{ figure.loads.live_first }}` |
| 64 | image idx=337 | [image #337] | `{{ figure.loads.live_second }}` |
| 65 | image idx=344 | [image #344] | `{{ figure.loads.roof_live_second }}` |
| 66 | image idx=348 | [image #348] | `{{ figure.loads.roof_live_top }}` |
| 67 | image idx=355 | [image #355] | `{{ figure.loads.cases }}` |
| 68 | anchored image idx=360 (preserved) | [anchored image, cx=3675398 cy=1586864] | `preserved (use replace_pic with rId=rId34)` |
| 69 | anchored image idx=362 (preserved) | [anchored image, cx=3675398 cy=1586864] | `preserved (use replace_pic with rId=rId34)` |
| 70 | anchored image idx=379 (preserved) | [anchored image, cx=3354372 cy=560070] | `preserved (use replace_pic with rId=rId36)` |
| 71 | image idx=443 | [image #443] | `{{ figure.elements.design_for_frames }}` |
| 72 | image idx=469 | [image #469] | `{{ figure.elements.beams_design }}` |
| 73 | image idx=471 | [image #471] | `{{ figure.elements.beams_design_b }}` |
| 74 | image idx=475 | [image #475] | `{{ figure.elements.columns_design }}` |
| 75 | image idx=478 | [image #478] | `{{ figure.elements.columns_design_b }}` |
| 76 | anchored image idx=486 (preserved) | [anchored image, cx=5459871 cy=1760220] | `preserved (use replace_pic with rId=rId42)` |
| 77 | anchored image idx=487 (preserved) | [anchored image, cx=2825115 cy=1940560] | `preserved (use replace_pic with rId=rId43)` |
| 78 | image idx=493 | [image #493] | `{{ figure.foundation.reaction_uls_c }}` |
| 79 | image idx=500 | [image #500] | `{{ figure.foundation.design_main }}` |
| 80 | image idx=506 | [image #506] | `{{ figure.foundation.design_b }}` |
| 81 | image idx=508 | [image #508] | `{{ figure.foundation.design_c }}` |
| 82 | image idx=512 | [image #512] | `{{ figure.foundation.design_d }}` |
| 83 | image idx=518 | [image #518] | `{{ figure.staircase.design_main }}` |
| 84 | image idx=520 | [image #520] | `{{ figure.staircase.design_b }}` |
| 85 | image idx=522 | [image #522] | `{{ figure.staircase.design_c }}` |
| 86 | image idx=542 | [image #542] | `{{ figure.drift.displacement }}` |
| 87 | image idx=584 | [image #584] | `{{ figure.drift.displacement_b }}` |
| 88 | anchored image idx=595 (preserved) | [anchored image, cx=2773056 cy=1228344] | `preserved (use replace_pic with rId=rId63)` |
| 89 | image idx=600 | [image #600] | `{{ figure.irregularity.soft_story }}` |
| 90 | anchored image idx=605 (preserved) | [anchored image, cx=1280787 cy=1980247] | `preserved (use replace_pic with rId=rId65)` |
| 91 | anchored image idx=613 (preserved) | [anchored image, cx=2099980 cy=1822704] | `preserved (use replace_pic with rId=rId66)` |
| 92 | anchored image idx=627 (preserved) | [anchored image, cx=2576128 cy=1822703] | `preserved (use replace_pic with rId=rId67)` |
| 93 | anchored image idx=635 (preserved) | [anchored image, cx=3644081 cy=1109472] | `preserved (use replace_pic with rId=rId68)` |
| 94 | image idx=645 | [image #645] | `{{ figure.irregularity.out_of_plane_offset }}` |
| 95 | image idx=651 | [image #651] | `{{ figure.summary.design }}` |
| 96 | image idx=654 | [image #654] | `{{ figure.summary.panel_a }}` |
| 97 | image idx=657 | [image #657] | `{{ figure.summary.panel_b }}` |
| 98 | image idx=666 | [image #666] | `{{ figure.elements.rebar_grid_a }}` |
| 99 | image idx=671 | [image #671] | `{{ figure.elements.rebar_grid_b }}` |
| 100 | image idx=676 | [image #676] | `{{ figure.elements.rebar_story1 }}` |
| 101 | image idx=683 | [image #683] | `{{ figure.elements.rebar_story2 }}` |
| 102 | image idx=688 | [image #688] | `{{ figure.elements.rebar_story3 }}` |
| 103 | table T0 cell (1,2) | Mr. Chatra Bahadur Ramtel | `{{ client.owner_name }}` |
| 104 | table T0 cell (2,2) | Damak | `{{ building.location }}` |
| 105 | table T0 cell (3,2) | Residential | `{{ building.occupancy_class }}` |
| 106 | table T0 cell (4,2) | Mr. Sachin KC | `{{ client.designer_name }}` |
| 107 | table T0 cell (5,2) | 131xx”Civil A” | `{{ client.designer_nec_reg }}` |
| 108 | table T0 cell (6,2) | 9841xxxxxxx | `{{ client.designer_contact }}` |
| 109 | table T0 cell (7,2) | CivoraX Infra | `{{ client.consultant_name }}` |
| 110 | table T0 cell (8,2) | Xxxx | `{{ client.municipality_reg }}` |
| 111 | table T0 cell (9,2) | 2026/xx/xx | `{{ client.application_date }}` |
| 112 | table T2 cell (0,2) | Damak | `{{ building.location }}` |
| 113 | table T2 cell (1,2) | 3 | `{{ building.storeys_count_numeric }}` |
| 114 | table T2 cell (2,2) | 3 | `{{ building.num_storeys_analysed }}` |
| 115 | table T2 cell (3,2) | 0 | `{{ building.num_basements }}` |
| 116 | table T2 cell (4,2) | 3.175 meters | `{{ building.height_ground_floor_m }} meters` |
| 117 | table T2 cell (5,2) | 3.175 meters | `{{ building.height_typical_floor_m }} meters` |
| 118 | table T2 cell (6,2) | 9.525 meters | `{{ building.total_height_m }} meters` |
| 119 | table T2 cell (7,2) | 9.525 meters | `{{ building.height_period_m }} meters` |
| 120 | table T2 cell (8,2) | Residential Building | `{{ building.occupancy_class }} Building` |
| 121 | table T3 cell (1,1) | 355 mm X 355 mm | `{{ table.elements.col_desc }}` |
| 122 | table T3 cell (1,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 123 | table T3 cell (2,1) | 250 mm X 430 mm | `{{ table.elements.beam_desc }}` |
| 124 | table T3 cell (2,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 125 | table T3 cell (3,1) | 150 mm | `{{ table.elements.stair_desc }}` |
| 126 | table T3 cell (3,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 127 | table T3 cell (4,1) | 125 mm | `{{ table.elements.slab_desc }}` |
| 128 | table T3 cell (4,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 129 | table T3 cell (5,1) | Combined Footing | `{{ table.elements.foundation_desc }}` |
| 130 | table T3 cell (5,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 131 | table T3 cell (5,3) | Soil Bearing Capacity is taken as 120 kN/m2 | `{{ foundation.soil_bearing }}` |
| 132 | table T4 cell (0,2) | Moment Resisting Frames | `{{ structural.system_type_generic }}` |
| 133 | table T4 cell (1,2) | Combined Footing | `{{ foundation.type }}` |
| 134 | table T4 cell (2,2) | Conventional | `{{ slab.type }}` |
| 135 | table T8 cell (0,5) | 9.525 | `{{ building.total_height_m }}` |
| 136 | table T8 cell (1,1) | Moment Resisting Concrete Frame | `{{ structural.system_type_period_category }}` |
| 137 | table T8 cell (2,1) | 0.075 | `{{ seismic.time_coefficient_kt }}` |
| 138 | table T8 cell (3,4) | 0.407 | `{{ modal.empirical_period_unamplified_s }}` |
| 139 | table T8 cell (5,3) | 0.508 | `{{ modal.empirical_period_s }}` |
| 140 | table T12 cell (0,2) | 0.508 | `{{ modal.empirical_period_s }}` |
| 141 | table T12 cell (2,2) | Very Soft Soil | `{{ seismic.site_soil_category }}` |
| 142 | table T12 cell (3,3) | 1 | `{{ seismic.tc }}` |
| 143 | table T12 cell (4,2) | C | `{{ seismic.soil_class }}` |
| 144 | table T12 cell (5,1) | 2.5 | `{{ seismic.alpha }}` |
| 145 | table T12 cell (5,3) | 1.004 | `{{ seismic.distribution_exponent_k }}` |
| 146 | table T12 cell (6,2) | 2.50 | `{{ seismic.spectral_shape_factor_cht }}` |
| 147 | table T12 cell (7,1) | Damak | `{{ building.location }}` |
| 148 | table T12 cell (7,3) | 0.35 | `{{ seismic.zone_factor_z }}` |
| 149 | table T12 cell (8,2) | Ordinary Structures | `{{ seismic.structural_type }}` |
| 150 | table T12 cell (9,2) | 1 | `{{ seismic.importance_factor_i_table }}` |
| 151 | table T12 cell (10,3) | 0.875 | `{{ seismic.elastic_site_spectra_c }}` |
| 152 | table T12 cell (11,3) | 0.175 | `{{ seismic.elastic_site_spectra_cs }}` |
| 153 | table T12 cell (13,3) | Reinforced Concrete Moment Resisting Frame | `{{ structural.system_type_table_5_2 }}` |
| 154 | table T12 cell (14,3) | 4 | `{{ seismic.response_modification_factor_rmu }}` |
| 155 | table T13 cell (0,1) | 1.5 | `{{ design.overstrength_ultimate }}` |
| 156 | table T13 cell (1,1) | 1.25 | `{{ design.overstrength_serviceability }}` |
| 157 | table T13 cell (2,1) | 0.146 | `{{ seismic.hsc_uls }}` |
| 158 | table T13 cell (3,1) | 0.140 | `{{ seismic.hsc_sls }}` |
| 159 | table T16 cell (1,1) | Continuous | `{{ table.design.beam_boundary }}` |
| 160 | table T16 cell (2,1) | 4191 mm | `{{ table.design.beam_effective_span }}` |
| 161 | table T16 cell (3,1) | 430 mm | `{{ table.design.beam_overall_depth }}` |
| 162 | table T16 cell (4,1) | 395 mm | `{{ table.design.beam_effective_depth }}` |
| 163 | table T16 cell (5,1) | 26 | `{{ table.design.beam_basic_ld_ratio }}` |
| 164 | table T16 cell (6,1) | 186 mm² | `{{ table.design.beam_ast_req }}` |
| 165 | table T16 cell (7,1) | 226 mm² | `{{ table.design.beam_ast_prov }}` |
| 166 | table T16 cell (8,1) | 0.229 % | `{{ table.design.beam_pt }}` |
| 167 | table T16 cell (9,1) | 239 N/mm² | `{{ table.design.beam_fs }}` |
| 168 | table T16 cell (10,1) | ≈ 1.68 | `{{ table.design.beam_mod_factor }}` |
| 169 | table T16 cell (11,1) | 43.7 | `{{ table.design.beam_permissible_ld }}` |
| 170 | table T16 cell (12,1) | 10.61 | `{{ table.design.beam_provided_ld }}` |
| 171 | table T16 cell (13,1) | 10.61 < 43.7, OK | `{{ table.design.beam_check_result }}` |
| 172 | table T6 cell (11,1) | 3.175 | `{{ building.story_height_m }}` |
| 173 | table T15 | [88×8 slab design table] | `{{ figure.design.slab_sheet }} (image placeholder)` |
| 174 | hard-coded clause in paragraph | Ch(t)=Spectral Shape factor as per cl.{{ codes.clauses.spectral_shape_factor }}  | `Ch(t)=Spectral Shape factor as per cl.{{ codes.clauses.spectral_shape_factor }} ` |
| 175 | hard-coded clause in paragraph | For Parallel System (Cl. 3.6.1) | `For Parallel System (Cl. {{ codes.clauses.load_combinations }})` |
| 176 | table T9 footer | [row 5] | `placeholders: ['totals.wi_kg', 'totals.wi_hik', 'totals.fi']` |
| 177 | table T9 (loop) | [6 rows → 5 rows] | `for + template + endfor + 1 footer(s)` |
| 178 | table T10 footer | [row 5] | `placeholders: ['totals.fi', 'totals.fi_di_x', 'totals.wi_di2_x']` |
| 179 | table T10 footer | [row 6] | `placeholders: ['modal.rayleigh_period_x_s']` |
| 180 | table T10 (loop) | [7 rows → 6 rows] | `for + template + endfor + 2 footer(s)` |
| 181 | table T11 footer | [row 5] | `placeholders: ['totals.fi', 'totals.fi_di_y', 'totals.wi_di2_y']` |
| 182 | table T11 footer | [row 6] | `placeholders: ['modal.rayleigh_period_y_s']` |
| 183 | table T11 (loop) | [7 rows → 6 rows] | `for + template + endfor + 2 footer(s)` |
| 184 | table T14 (loop) | [11 rows → 5 rows] | `for + template + endfor + 0 footer(s)` |
| 185 | paragraphs idx=370..379 | Design of Staircases block | `{%p if building.has_staircase %}...{%p endif %}` |
