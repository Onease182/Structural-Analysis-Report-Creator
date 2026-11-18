# Template Replacement Log

Total replacements: **217**.

| # | Location | Old text (preview) | Placeholder |
|---|----------|-------------------|-------------|
| 1 | paragraph idx=0 | Structural report of Residence Building of Chatra Bahadur Ramtel  | `{{ project.report_title }}` |
| 2 | paragraph idx=11 | Civira X  | `{{ client.consultant_name }}` |
| 3 | paragraph idx=12 | Damak | `{{ building.location }}` |
| 4 | paragraph idx=164 (sentence template) | The building has three floors made of reinforced concrete frames and filled with | `The building has {{ building.storeys_above_grade }} floors made of {{ building.primary_frame_materia` |
| 5 | paragraph idx=164 (sentence template) | The building has {{ building.storeys_above_grade }} floors made of {{ building.primary_frame_materia | `The building has {{ building.storeys_above_grade }} floors made of {{ building.primary_frame_materia` |
| 6 | paragraph idx=165 (sentence template) | brick walls. Each floor has a height of 3.175 meters. The building is laid out in a rectangular grid | `{{ building.infill_wall_material }} walls. Each floor has a height of {{ building.story_height_m }} ` |
| 7 | paragraph idx=165 (sentence template) | {{ building.infill_wall_material }} walls. Each floor has a height of {{ building.story_height_m }}  | `{{ building.infill_wall_material }} walls. Each floor has a height of {{ building.story_height_m }} ` |
| 8 | paragraph idx=165 (sentence template) | {{ building.infill_wall_material }} walls. Each floor has a height of {{ building.story_height_m }}  | `{{ building.infill_wall_material }} walls. Each floor has a height of {{ building.story_height_m }} ` |
| 9 | paragraph idx=165 (sentence template) | {{ building.infill_wall_material }} walls. Each floor has a height of {{ building.story_height_m }}  | `{{ building.infill_wall_material }} walls. Each floor has a height of {{ building.story_height_m }} ` |
| 10 | paragraph idx=208 | According to NBC105:2020, The material should be taken as per Cl.2.1. | `{{ codes.clauses.material_properties }}` |
| 11 | paragraph idx=210 (sentence template) | As the building is less than 12 m in height, M20 concrete has been taken for all the structural comp | `As the building is less than 12 m in height, {{ materials.concrete_grade_used }} concrete has been t` |
| 12 | paragraph idx=224 (sentence template) | Steel Grade of Fe500 has been used in the longitudinal and transverse reinforcement. | `Steel Grade of {{ materials.rebar_grade_used }} has been used in the longitudinal and transverse rei` |
| 13 | paragraph idx=240 | Due to the eccentricity arising between the center of mass and the center of rigidity at each floor  | `{{ codes.clauses.eccentricity_intro }}` |
| 14 | paragraph idx=258 (sentence template) | The building was modeled using the ETABS 19.0.0 software. ETABS 19.0.0 is a specialized program desi | `The building was modeled using the {{ foundation.modeling_software }} software. {{ foundation.modeli` |
| 15 | paragraph idx=380 (sentence template) | Base shear from ETABS 240.02 kN.  | `Base shear from ETABS {{ modal.base_shear_etabs }} kN.` |
| 16 | paragraph idx=384 (sentence template) | k = 1.004 (T = 0.508 s); Cd = 0.1458; V = Cd·W, W taken above Base. Z = 0.35, soil C, I = 1.0, Rμ =  | `k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi` |
| 17 | paragraph idx=384 (sentence template) | k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi | `k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi` |
| 18 | paragraph idx=384 (sentence template) | k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi | `k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi` |
| 19 | paragraph idx=384 (sentence template) | k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi | `k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi` |
| 20 | paragraph idx=384 (sentence template) | k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi | `k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi` |
| 21 | paragraph idx=384 (sentence template) | k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi | `k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi` |
| 22 | paragraph idx=384 (sentence template) | k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi | `k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi` |
| 23 | paragraph idx=384 (sentence template) | k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi | `k = {{ seismic.distribution_exponent_k }} (T = {{ seismic.design_period_used_s }} s); Cd = {{ seismi` |
| 24 | paragraph idx=395 (sentence template) | As Empirical time period (0.508 sec) is lesser than the Rayleigh time period (0.531 sec), use empiri | `As Empirical time period ({{ modal.empirical_period_s }} sec) is lesser than the Rayleigh time perio` |
| 25 | paragraph idx=395 (sentence template) | As Empirical time period ({{ modal.empirical_period_s }} sec) is lesser than the Rayleigh time perio | `As Empirical time period ({{ modal.empirical_period_s }} sec) is lesser than the Rayleigh time perio` |
| 26 | paragraph idx=395 (sentence template) | As Empirical time period ({{ modal.empirical_period_s }} sec) is lesser than the Rayleigh time perio | `As Empirical time period ({{ modal.empirical_period_s }} sec) is lesser than the Rayleigh time perio` |
| 27 | paragraph idx=397 | Ch(t)=Spectral Shape factor as per cl.4.1.2 Z= Seismic Zoning Factor as per 4.1.4 I=Importance facto | `{{ codes.clauses.spectral_shape_factor }}` |
| 28 | paragraph idx=413 | As per Clause 3.2.1 of NBC 105:2025, the Equivalent Static Method may be used for all serviceability | `{{ codes.clauses.equivalent_static_method }}` |
| 29 | paragraph idx=413 (sentence template) | As per Clause {{ codes.clauses.equivalent_static_method }} of {{ codes.edition }}, the Equivalent St | `As per Clause {{ codes.clauses.equivalent_static_method }} of {{ codes.edition }}, the Equivalent St` |
| 30 | paragraph idx=418 | When lateral load resisting elements are oriented along mutually orthogonal horizontal directions, t | `{{ codes.clauses.load_combinations }}` |
| 31 | paragraph idx=430 | NBC105:2025 clause 7.3 states that number of modes to be used in the analysis should be such that th | `{{ codes.clauses.modal_mass_participation }}` |
| 32 | paragraph idx=430 (sentence template) | {{ codes.edition }} clause {{ codes.clauses.modal_mass_participation }} states that number of modes  | `{{ codes.edition }} clause {{ codes.clauses.modal_mass_participation }} states that number of modes ` |
| 33 | paragraph idx=430 (sentence template) | {{ codes.edition }} clause {{ codes.clauses.modal_mass_participation }} states that number of modes  | `{{ codes.edition }} clause {{ codes.clauses.modal_mass_participation }} states that number of modes ` |
| 34 | paragraph idx=450 (sentence template) | = 1557/ (355*355)*100% =1.24% <4% (Ok) | `= {{ design.column.max_rebar_area_mm2 }}/({{ design.column.max_section_width_mm }}*{{ design.column.` |
| 35 | paragraph idx=450 (sentence template) | = {{ design.column.max_rebar_area_mm2 }}/({{ design.column.max_section_width_mm }}*{{ design.column. | `= {{ design.column.max_rebar_area_mm2 }}/({{ design.column.max_section_width_mm }}*{{ design.column.` |
| 36 | paragraph idx=450 (sentence template) | = {{ design.column.max_rebar_area_mm2 }}/({{ design.column.max_section_width_mm }}*{{ design.column. | `= {{ design.column.max_rebar_area_mm2 }}/({{ design.column.max_section_width_mm }}*{{ design.column.` |
| 37 | paragraph idx=450 (sentence template) | = {{ design.column.max_rebar_area_mm2 }}/({{ design.column.max_section_width_mm }}*{{ design.column. | `= {{ design.column.max_rebar_area_mm2 }}/({{ design.column.max_section_width_mm }}*{{ design.column.` |
| 38 | paragraph idx=450 (sentence template) | = {{ design.column.max_rebar_area_mm2 }}/({{ design.column.max_section_width_mm }}*{{ design.column. | `= {{ design.column.max_rebar_area_mm2 }}/({{ design.column.max_section_width_mm }}*{{ design.column.` |
| 39 | paragraph idx=450 (sentence template) | = {{ design.column.max_rebar_area_mm2 }}/({{ design.column.max_section_width_mm }}*{{ design.column. | `= {{ design.column.max_rebar_area_mm2 }}/({{ design.column.max_section_width_mm }}*{{ design.column.` |
| 40 | paragraph idx=454 (sentence template) | = 1.026%> 1% (Ok) | `\t= {{ design.column.min_provided_pct }}%\t> {{ design.column.min_limit_pct }}% ({{ design.column.mi` |
| 41 | paragraph idx=454 (sentence template) | \t= {{ design.column.min_provided_pct }}%\t> {{ design.column.min_limit_pct }}% ({{ design.column.mi | `\t= {{ design.column.min_provided_pct }}%\t> {{ design.column.min_limit_pct }}% ({{ design.column.mi` |
| 42 | paragraph idx=454 (sentence template) | \t= {{ design.column.min_provided_pct }}%\t> {{ design.column.min_limit_pct }}% ({{ design.column.mi | `\t= {{ design.column.min_provided_pct }}%\t> {{ design.column.min_limit_pct }}% ({{ design.column.mi` |
| 43 | paragraph idx=456 (sentence template) | = 678.584/ (250*355) = 0.764% <2.5% (Ok) | `= {{ design.beam.max_rebar_area_mm2 }}/({{ design.beam.max_section_width_mm }}*{{ design.beam.max_se` |
| 44 | paragraph idx=456 (sentence template) | = {{ design.beam.max_rebar_area_mm2 }}/({{ design.beam.max_section_width_mm }}*{{ design.beam.max_se | `= {{ design.beam.max_rebar_area_mm2 }}/({{ design.beam.max_section_width_mm }}*{{ design.beam.max_se` |
| 45 | paragraph idx=456 (sentence template) | = {{ design.beam.max_rebar_area_mm2 }}/({{ design.beam.max_section_width_mm }}*{{ design.beam.max_se | `= {{ design.beam.max_rebar_area_mm2 }}/({{ design.beam.max_section_width_mm }}*{{ design.beam.max_se` |
| 46 | paragraph idx=456 (sentence template) | = {{ design.beam.max_rebar_area_mm2 }}/({{ design.beam.max_section_width_mm }}*{{ design.beam.max_se | `= {{ design.beam.max_rebar_area_mm2 }}/({{ design.beam.max_section_width_mm }}*{{ design.beam.max_se` |
| 47 | paragraph idx=456 (sentence template) | = {{ design.beam.max_rebar_area_mm2 }}/({{ design.beam.max_section_width_mm }}*{{ design.beam.max_se | `= {{ design.beam.max_rebar_area_mm2 }}/({{ design.beam.max_section_width_mm }}*{{ design.beam.max_se` |
| 48 | paragraph idx=456 (sentence template) | = {{ design.beam.max_rebar_area_mm2 }}/({{ design.beam.max_section_width_mm }}*{{ design.beam.max_se | `= {{ design.beam.max_rebar_area_mm2 }}/({{ design.beam.max_section_width_mm }}*{{ design.beam.max_se` |
| 49 | paragraph idx=458 (sentence template) | = 0.764% >0.26 % (Ok) | `= {{ design.beam.min_provided_pct }}% >{{ design.beam.min_limit_pct }}% ({{ design.beam.minimum_rein` |
| 50 | paragraph idx=458 (sentence template) | = {{ design.beam.min_provided_pct }}% >{{ design.beam.min_limit_pct }}% ({{ design.beam.minimum_rein | `= {{ design.beam.min_provided_pct }}% >{{ design.beam.min_limit_pct }}% ({{ design.beam.minimum_rein` |
| 51 | paragraph idx=458 (sentence template) | = {{ design.beam.min_provided_pct }}% >{{ design.beam.min_limit_pct }}% ({{ design.beam.minimum_rein | `= {{ design.beam.min_provided_pct }}% >{{ design.beam.min_limit_pct }}% ({{ design.beam.minimum_rein` |
| 52 | paragraph idx=533 | 5.6.3 of NBC 105:2077 is proposed to be used. | `{{ codes.clauses.serviceability_drift }}` |
| 53 | paragraph idx=535 (sentence template) | 5.6.3 of NBC 105:2077 is applied. The maximum deflection in any story due to the minimum specified d | `{{ codes.clauses.serviceability_drift }} of {{ codes.edition }} is applied. The maximum deflection i` |
| 54 | paragraph idx=535 (sentence template) | {{ codes.clauses.serviceability_drift }} of {{ codes.edition }} is applied. The maximum deflection i | `{{ codes.clauses.serviceability_drift }} of {{ codes.edition }} is applied. The maximum deflection i` |
| 55 | paragraph idx=535 (sentence template) | {{ codes.clauses.serviceability_drift }} of {{ codes.edition }} is applied. The maximum deflection i | `{{ codes.clauses.serviceability_drift }} of {{ codes.edition }} is applied. The maximum deflection i` |
| 56 | paragraph idx=591 | One of the basic virtues of earthquake resistant design of structures is that the structure shall be | `{{ codes.clauses.irregularity_general }}` |
| 57 | paragraph idx=593 | As per the clause 5.5.2.1 of NBC 105:2020, torsion irregularity is considered to exist when the maxi | `{{ codes.clauses.torsional_irregularity }}` |
| 58 | paragraph idx=593 (sentence template) | As per the clause {{ codes.clauses.torsional_irregularity }} of {{ codes.edition }}, torsion irregul | `As per the clause {{ codes.clauses.torsional_irregularity }} of {{ codes.edition }}, torsion irregul` |
| 59 | paragraph idx=603 | As per the clause 5.5.1.2, a soft story is the one whose stiffness of the lateral force resisting sy | `{{ codes.clauses.soft_storey }}` |
| 60 | paragraph idx=603 (sentence template) | As per the clause {{ codes.clauses.soft_storey }}, a soft story is the one whose stiffness of the la | `As per the clause {{ codes.clauses.soft_storey }} of {{ codes.edition }}, a soft story is the one wh` |
| 61 | paragraph idx=603 (sentence template) | As per the clause {{ codes.clauses.soft_storey }} of {{ codes.edition }}, a soft story is the one wh | `As per the clause {{ codes.clauses.soft_storey }} of {{ codes.edition }}, a soft story is the one wh` |
| 62 | paragraph idx=617 | If there is a difference of more than 50% between the effective masses of two consecutive storeys, t | `{{ codes.clauses.mass_irregularity }}` |
| 63 | paragraph idx=617 (sentence template) | If there is a difference of more than 50% between the effective masses of two consecutive storeys, t | `If there is a difference of more than {{ codes.limits.mass_irregularity_diff_pct }}% between the eff` |
| 64 | paragraph idx=624 | As per the clause 5.5.2.2 of NBC 105:2020, a structure is said to have re-entrant corner irregularit | `{{ codes.clauses.reentrant_corner }}` |
| 65 | paragraph idx=624 (sentence template) | As per the clause {{ codes.clauses.reentrant_corner }} of {{ codes.edition }}, a structure is said t | `As per the clause {{ codes.clauses.reentrant_corner }} of {{ codes.edition }}, a structure is said t` |
| 66 | paragraph idx=632 | If the diaphragm of a building has a cutout or open area greater than 50% of the gross enclosed diap | `{{ codes.clauses.diaphragm_discontinuity }}` |
| 67 | paragraph idx=632 (sentence template) | If the diaphragm of a building has a cutout or open area greater than 50% of the gross enclosed diap | `If the diaphragm of a building has a cutout or open area greater than {{ codes.limits.diaphragm_open` |
| 68 | paragraph idx=632 (sentence template) | If the diaphragm of a building has a cutout or open area greater than {{ codes.limits.diaphragm_open | `If the diaphragm of a building has a cutout or open area greater than {{ codes.limits.diaphragm_open` |
| 69 | paragraph idx=610 (sentence template) | As per the clause 5.5.1.4 of NBC 105:2020, if there is an in-plane offset of a vertical seismic forc | `{{ codes.clauses.in_plane_discontinuity }}` |
| 70 | paragraph idx=640 (sentence template) | If there is a discontinuity in a lateral force resisting path such as an out-of-plane of at least on | `{{ codes.clauses.out_of_plane_offset }}` |
| 71 | paragraph idx=256 (sentence template) | the foundation is assumed to be fixed. | `{{ foundation.support_condition }}` |
| 72 | paragraph idx=608 (sentence template) | No soft stoy is observed in the building. | `{{ analysis.soft_storey_result }}` |
| 73 | paragraph idx=611 (sentence template) | No in-plane discontinuity is present in the structure. | `{{ analysis.in_plane_discontinuity_result }}` |
| 74 | paragraph idx=621 (sentence template) | No mass irregularity is seen as the stories are nearly identical. | `{{ analysis.mass_irregularity_result }}` |
| 75 | paragraph idx=625 (sentence template) | The building is rectangular in shape with no re-entrant corners. | `{{ analysis.reentrant_corner_result }}` |
| 76 | caption idx=381 (partial) | Table 9:  Vertical distribution of ULS seismic forces (NBC 105:2025 Cl. 6.3) | `Table 9:  Vertical distribution of ULS seismic forces ({{ codes.edition }} {{ codes.clauses.vertical` |
| 77 | caption idx=405 (partial) | Table 12: Seismic design parameters for the RC moment resisting frame in Damak (NBC 105:2025). | `Table 12: Seismic design parameters for the RC moment resisting frame in {{ building.location }} ({{` |
| 78 | style override for analysis.in_plane_discontinuity_result | style: Heading4 | `style: BodyText` |
| 79 | style override for analysis.mass_irregularity_result | style: Heading4 | `style: BodyText` |
| 80 | anchored image idx=2 (preserved) | [anchored image, cx=5274310 cy=6350] | `preserved (use replace_pic with rId=None)` |
| 81 | image idx=5 | [image #5] | `{{ figure.project.report_figure }}` |
| 82 | image idx=168 | [image #168] | `{{ figure.building.plan_of_building }}` |
| 83 | image idx=175 | [image #175] | `{{ figure.building.section_of_building }}` |
| 84 | image idx=212 | [image #212] | `{{ figure.materials.concrete }}` |
| 85 | image idx=221 | [image #221] | `{{ figure.materials.material_property_rebar }}` |
| 86 | anchored image idx=244 (preserved) | [anchored image, cx=541020 cy=542290] | `preserved (use replace_pic with rId=None)` |
| 87 | anchored image idx=245 (preserved) | [anchored image, cx=1988820 cy=490855] | `preserved (use replace_pic with rId=None)` |
| 88 | anchored image idx=251 (preserved) | [anchored image, cx=2919095 cy=1604010] | `preserved (use replace_pic with rId=rId18)` |
| 89 | anchored image idx=252 (preserved) | [anchored image, cx=81280 cy=1591945] | `preserved (use replace_pic with rId=None)` |
| 90 | image idx=293 | [image #293] | `{{ figure.loads.wall_first }}` |
| 91 | image idx=298 | [image #298] | `{{ figure.loads.wall_second }}` |
| 92 | image idx=302 | [image #302] | `{{ figure.loads.wall_third }}` |
| 93 | image idx=310 | [image #310] | `{{ figure.building.finish_first }}` |
| 94 | image idx=317 | [image #317] | `{{ figure.building.finish_second }}` |
| 95 | image idx=332 | [image #332] | `{{ figure.loads.live_first }}` |
| 96 | image idx=337 | [image #337] | `{{ figure.loads.live_second }}` |
| 97 | image idx=344 | [image #344] | `{{ figure.loads.roof_live_second }}` |
| 98 | image idx=348 | [image #348] | `{{ figure.loads.roof_live_top }}` |
| 99 | image idx=355 | [image #355] | `{{ figure.loads.cases }}` |
| 100 | anchored image idx=360 (preserved) | [anchored image, cx=3675398 cy=1586864] | `preserved (use replace_pic with rId=rId34)` |
| 101 | anchored image idx=362 (preserved) | [anchored image, cx=3675398 cy=1586864] | `preserved (use replace_pic with rId=rId34)` |
| 102 | anchored image idx=379 (preserved) | [anchored image, cx=3354372 cy=560070] | `preserved (use replace_pic with rId=rId36)` |
| 103 | image idx=443 | [image #443] | `{{ figure.elements.design_for_frames }}` |
| 104 | image idx=469 | [image #469] | `{{ figure.elements.beams_design }}` |
| 105 | image idx=471 | [image #471] | `{{ figure.elements.beams_design_b }}` |
| 106 | image idx=475 | [image #475] | `{{ figure.elements.columns_design }}` |
| 107 | image idx=478 | [image #478] | `{{ figure.elements.columns_design_b }}` |
| 108 | anchored image idx=486 (preserved) | [anchored image, cx=5459871 cy=1760220] | `preserved (use replace_pic with rId=rId42)` |
| 109 | anchored image idx=487 (preserved) | [anchored image, cx=2825115 cy=1940560] | `preserved (use replace_pic with rId=rId43)` |
| 110 | image idx=493 | [image #493] | `{{ figure.foundation.reaction_uls_c }}` |
| 111 | image idx=500 | [image #500] | `{{ figure.foundation.design_main }}` |
| 112 | image idx=506 | [image #506] | `{{ figure.foundation.design_b }}` |
| 113 | image idx=508 | [image #508] | `{{ figure.foundation.design_c }}` |
| 114 | image idx=512 | [image #512] | `{{ figure.foundation.design_d }}` |
| 115 | image idx=518 | [image #518] | `{{ figure.staircase.design_main }}` |
| 116 | image idx=520 | [image #520] | `{{ figure.staircase.design_b }}` |
| 117 | image idx=522 | [image #522] | `{{ figure.staircase.design_c }}` |
| 118 | image idx=542 | [image #542] | `{{ figure.drift.displacement }}` |
| 119 | image idx=584 | [image #584] | `{{ figure.drift.displacement_b }}` |
| 120 | anchored image idx=595 (preserved) | [anchored image, cx=2773056 cy=1228344] | `preserved (use replace_pic with rId=rId63)` |
| 121 | image idx=600 | [image #600] | `{{ figure.irregularity.soft_story }}` |
| 122 | anchored image idx=605 (preserved) | [anchored image, cx=1280787 cy=1980247] | `preserved (use replace_pic with rId=rId65)` |
| 123 | anchored image idx=613 (preserved) | [anchored image, cx=2099980 cy=1822704] | `preserved (use replace_pic with rId=rId66)` |
| 124 | anchored image idx=627 (preserved) | [anchored image, cx=2576128 cy=1822703] | `preserved (use replace_pic with rId=rId67)` |
| 125 | anchored image idx=635 (preserved) | [anchored image, cx=3644081 cy=1109472] | `preserved (use replace_pic with rId=rId68)` |
| 126 | image idx=645 | [image #645] | `{{ figure.irregularity.out_of_plane_offset }}` |
| 127 | image idx=651 | [image #651] | `{{ figure.summary.design }}` |
| 128 | image idx=654 | [image #654] | `{{ figure.summary.panel_a }}` |
| 129 | image idx=657 | [image #657] | `{{ figure.summary.panel_b }}` |
| 130 | image idx=666 | [image #666] | `{{ figure.elements.rebar_grid_a }}` |
| 131 | image idx=671 | [image #671] | `{{ figure.elements.rebar_grid_b }}` |
| 132 | image idx=676 | [image #676] | `{{ figure.elements.rebar_story1 }}` |
| 133 | image idx=683 | [image #683] | `{{ figure.elements.rebar_story2 }}` |
| 134 | image idx=688 | [image #688] | `{{ figure.elements.rebar_story3 }}` |
| 135 | table T0 cell (1,2) | Mr. Chatra Bahadur Ramtel | `{{ client.owner_name }}` |
| 136 | table T0 cell (2,2) | Damak | `{{ building.location }}` |
| 137 | table T0 cell (3,2) | Residential | `{{ building.occupancy_class }}` |
| 138 | table T0 cell (4,2) | Mr. Sachin KC | `{{ client.designer_name }}` |
| 139 | table T0 cell (5,2) | 131xx”Civil A” | `{{ client.designer_nec_reg }}` |
| 140 | table T0 cell (6,2) | 9841xxxxxxx | `{{ client.designer_contact }}` |
| 141 | table T0 cell (7,2) | CivoraX Infra | `{{ client.consultant_firm }}` |
| 142 | table T0 cell (8,2) | Xxxx | `{{ client.municipality_reg }}` |
| 143 | table T0 cell (9,2) | 2026/xx/xx | `{{ client.application_date }}` |
| 144 | table T2 cell (0,2) | Damak | `{{ building.location }}` |
| 145 | table T2 cell (1,2) | 3 | `{{ building.storeys_above_grade }}` |
| 146 | table T2 cell (2,2) | 3 | `{{ building.num_storeys_analysed }}` |
| 147 | table T2 cell (3,2) | 0 | `{{ building.num_basements }}` |
| 148 | table T2 cell (4,2) | 3.175 meters | `{{ building.height_ground_floor_m }}` |
| 149 | table T2 cell (5,2) | 3.175 meters | `{{ building.height_typical_floor_m }}` |
| 150 | table T2 cell (6,2) | 9.525 meters | `{{ building.total_height_m }}` |
| 151 | table T2 cell (7,2) | 9.525 meters | `{{ building.height_period_m }}` |
| 152 | table T2 cell (8,2) | Residential Building | `{{ building.occupancy_class_building }}` |
| 153 | table T3 cell (1,1) | 355 mm X 355 mm | `{{ table.elements.col_desc }}` |
| 154 | table T3 cell (1,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 155 | table T3 cell (2,1) | 250 mm X 430 mm | `{{ table.elements.beam_desc }}` |
| 156 | table T3 cell (2,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 157 | table T3 cell (3,1) | 150 mm | `{{ table.elements.stair_desc }}` |
| 158 | table T3 cell (3,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 159 | table T3 cell (4,1) | 125 mm | `{{ table.elements.slab_desc }}` |
| 160 | table T3 cell (4,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 161 | table T3 cell (5,1) | Combined Footing | `{{ table.elements.foundation_desc }}` |
| 162 | table T3 cell (5,2) | M20 | `{{ materials.concrete_grade_used }}` |
| 163 | table T3 cell (5,3) | Soil Bearing Capacity is taken as 120 kN/m2 | `{{ foundation.soil_bearing }}` |
| 164 | table T4 cell (0,2) | Moment Resisting Frames | `{{ structural.system_type }}` |
| 165 | table T4 cell (1,2) | Combined Footing | `{{ foundation.type }}` |
| 166 | table T4 cell (2,2) | Conventional | `{{ slab.type }}` |
| 167 | table T8 cell (0,5) | 9.525 | `{{ building.total_height_numeric }}` |
| 168 | table T8 cell (1,1) | Moment Resisting Concrete Frame | `{{ structural.system_type_concrete }}` |
| 169 | table T8 cell (2,1) | 0.075 | `{{ seismic.time_coefficient_kt }}` |
| 170 | table T8 cell (3,4) | 0.407 | `{{ modal.empirical_period_unamplified_s }}` |
| 171 | table T8 cell (5,3) | 0.508 | `{{ modal.empirical_period_s }}` |
| 172 | table T12 cell (0,2) | 0.508 | `{{ modal.empirical_period_s }}` |
| 173 | table T12 cell (2,2) | Very Soft Soil | `{{ seismic.site_soil_category }}` |
| 174 | table T12 cell (3,3) | 1 | `{{ seismic.tc }}` |
| 175 | table T12 cell (4,2) | C | `{{ seismic.soil_class }}` |
| 176 | table T12 cell (5,1) | 2.5 | `{{ seismic.alpha }}` |
| 177 | table T12 cell (5,3) | 1.004 | `{{ seismic.distribution_exponent_k }}` |
| 178 | table T12 cell (6,2) | 2.50 | `{{ seismic.spectral_shape_factor_cht }}` |
| 179 | table T12 cell (7,1) | Damak | `{{ building.location }}` |
| 180 | table T12 cell (7,3) | 0.35 | `{{ seismic.zone_factor_z }}` |
| 181 | table T12 cell (8,2) | Ordinary Structures | `{{ seismic.structural_type }}` |
| 182 | table T12 cell (9,2) | 1 | `{{ seismic.importance_factor_i }}` |
| 183 | table T12 cell (10,3) | 0.875 | `{{ seismic.elastic_site_spectra_c }}` |
| 184 | table T12 cell (11,3) | 0.175 | `{{ seismic.elastic_site_spectra_cs }}` |
| 185 | table T12 cell (13,3) | Reinforced Concrete Moment Resisting Frame | `{{ structural.system_type_full }}` |
| 186 | table T12 cell (14,3) | 4 | `{{ seismic.response_modification_factor_rmu }}` |
| 187 | table T13 cell (0,1) | 1.5 | `{{ design.overstrength_ultimate }}` |
| 188 | table T13 cell (1,1) | 1.25 | `{{ design.overstrength_serviceability }}` |
| 189 | table T13 cell (2,1) | 0.146 | `{{ seismic.hsc_uls }}` |
| 190 | table T13 cell (3,1) | 0.140 | `{{ seismic.hsc_sls }}` |
| 191 | table T16 cell (1,1) | Continuous | `{{ table.design.beam_boundary }}` |
| 192 | table T16 cell (2,1) | 4191 mm | `{{ table.design.beam_effective_span }}` |
| 193 | table T16 cell (3,1) | 430 mm | `{{ table.design.beam_overall_depth }}` |
| 194 | table T16 cell (4,1) | 395 mm | `{{ table.design.beam_effective_depth }}` |
| 195 | table T16 cell (5,1) | 26 | `{{ table.design.beam_basic_ld_ratio }}` |
| 196 | table T16 cell (6,1) | 186 mm² | `{{ table.design.beam_ast_req }}` |
| 197 | table T16 cell (7,1) | 226 mm² | `{{ table.design.beam_ast_prov }}` |
| 198 | table T16 cell (8,1) | 0.229 % | `{{ table.design.beam_pt }}` |
| 199 | table T16 cell (9,1) | 239 N/mm² | `{{ table.design.beam_fs }}` |
| 200 | table T16 cell (10,1) | ≈ 1.68 | `{{ table.design.beam_mod_factor }}` |
| 201 | table T16 cell (11,1) | 43.7 | `{{ table.design.beam_permissible_ld }}` |
| 202 | table T16 cell (12,1) | 10.61 | `{{ table.design.beam_provided_ld }}` |
| 203 | table T16 cell (13,1) | 10.61 < 43.7, OK | `{{ table.design.beam_check_result }}` |
| 204 | table T6 cell (11,1) | 3.175 | `{{ building.story_height_m }}` |
| 205 | table T15 | [88×8 slab design table] | `{{ figure.design.slab_sheet }} (image placeholder)` |
| 206 | hard-coded clause in paragraph | Ch(t)=Spectral Shape factor as per cl.{{ codes.clauses.spectral_shape_factor }}  | `Ch(t)=Spectral Shape factor as per cl.{{ codes.clauses.spectral_shape_factor }} ` |
| 207 | hard-coded clause in paragraph | For Parallel System (Cl. 3.6.1) | `For Parallel System (Cl. {{ codes.clauses.load_combinations }})` |
| 208 | table T9 footer | [row 5] | `placeholders: ['totals.wi_kg', 'totals.wi_hik', 'totals.fi']` |
| 209 | table T9 (loop) | [6 rows → 5 rows] | `for + template + endfor + 1 footer(s)` |
| 210 | table T10 footer | [row 5] | `placeholders: ['totals.fi', 'totals.fi_di_x', 'totals.wi_di2_x']` |
| 211 | table T10 footer | [row 6] | `placeholders: ['modal.rayleigh_period_x_s']` |
| 212 | table T10 (loop) | [7 rows → 6 rows] | `for + template + endfor + 2 footer(s)` |
| 213 | table T11 footer | [row 5] | `placeholders: ['totals.fi', 'totals.fi_di_y', 'totals.wi_di2_y']` |
| 214 | table T11 footer | [row 6] | `placeholders: ['modal.rayleigh_period_y_s']` |
| 215 | table T11 (loop) | [7 rows → 6 rows] | `for + template + endfor + 2 footer(s)` |
| 216 | table T14 (loop) | [11 rows → 5 rows] | `for + template + endfor + 0 footer(s)` |
| 217 | paragraphs idx=370..379 | Design of Staircases block | `{%p if building.has_staircase %}...{%p endif %}` |
