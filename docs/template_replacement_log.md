# Template Replacement Log

Total replacements: **100**.

| # | Location | Old text (preview) | Placeholder |
|---|----------|-------------------|-------------|
| 1 | paragraph idx=0 | Structural report of Residence Building of Chatra Bahadur Ramtel  | `{{ project.report_title }}` |
| 2 | paragraph idx=11 | Civira X  | `{{ client.consultant_name }}` |
| 3 | paragraph idx=12 | Damak | `{{ building.location }}` |
| 4 | paragraph idx=164 | The building has three floors made of reinforced concrete frames and filled with | `{{ building.storeys_above_grade }}` |
| 5 | paragraph idx=208 | According to NBC105:2020, The material should be taken as per Cl.2.1. | `{{ codes.clauses.material_properties }}` |
| 6 | paragraph idx=210 | As the building is less than 12 m in height, M20 concrete has been taken for all the structural comp | `{{ materials.as_building_is_less_than_12_m }}` |
| 7 | paragraph idx=224 | Steel Grade of Fe500 has been used in the longitudinal and transverse reinforcement. | `{{ materials.rebar_grade_used }}` |
| 8 | paragraph idx=240 | Due to the eccentricity arising between the center of mass and the center of rigidity at each floor  | `{{ codes.clauses.eccentricity_intro }}` |
| 9 | paragraph idx=380 | Base shear from ETABS 240.02 kN.  | `{{ modal.base_shear_etabs }}` |
| 10 | paragraph idx=384 | k = 1.004 (T = 0.508 s); Cd = 0.1458; V = Cd·W, W taken above Base. Z = 0.35, soil C, I = 1.0, Rμ =  | `{{ seismic.distribution_exponent_k }}` |
| 11 | paragraph idx=395 | As Empirical time period (0.508 sec) is lesser than the Rayleigh time period (0.531 sec), use empiri | `{{ modal.rayleigh_period_s }}` |
| 12 | paragraph idx=397 | Ch(t)=Spectral Shape factor as per cl.4.1.2 Z= Seismic Zoning Factor as per 4.1.4 I=Importance facto | `{{ codes.clauses.spectral_shape_factor }}` |
| 13 | paragraph idx=413 | As per Clause 3.2.1 of NBC 105:2025, the Equivalent Static Method may be used for all serviceability | `{{ codes.clauses.equivalent_static_method }}` |
| 14 | paragraph idx=418 | When lateral load resisting elements are oriented along mutually orthogonal horizontal directions, t | `{{ codes.clauses.load_combinations }}` |
| 15 | paragraph idx=430 | NBC105:2025 clause 7.3 states that number of modes to be used in the analysis should be such that th | `{{ codes.clauses.modal_mass_participation }}` |
| 16 | paragraph idx=450 | = 1557/ (355*355)*100% =1.24% <4% (Ok) | `{{ design.column.max_rebar_area_mm2 }}` |
| 17 | paragraph idx=454 | = 1.026%> 1% (Ok) | `{{ design.column.min_provided_pct }}` |
| 18 | paragraph idx=456 | = 678.584/ (250*355) = 0.764% <2.5% (Ok) | `{{ design.beam.max_rebar_area_mm2 }}` |
| 19 | paragraph idx=458 | = 0.764% >0.26 % (Ok) | `{{ design.beam.min_provided_pct }}` |
| 20 | paragraph idx=533 | 5.6.3 of NBC 105:2077 is proposed to be used. | `{{ codes.clauses.serviceability_drift }}` |
| 21 | paragraph idx=591 | One of the basic virtues of earthquake resistant design of structures is that the structure shall be | `{{ codes.clauses.irregularity_general }}` |
| 22 | paragraph idx=593 | As per the clause 5.5.2.1 of NBC 105:2020, torsion irregularity is considered to exist when the maxi | `{{ codes.clauses.torsional_irregularity }}` |
| 23 | paragraph idx=603 | As per the clause 5.5.1.2, a soft story is the one whose stiffness of the lateral force resisting sy | `{{ codes.clauses.soft_storey }}` |
| 24 | paragraph idx=617 | If there is a difference of more than 50% between the effective masses of two consecutive storeys, t | `{{ codes.clauses.mass_irregularity }}` |
| 25 | paragraph idx=624 | As per the clause 5.5.2.2 of NBC 105:2020, a structure is said to have re-entrant corner irregularit | `{{ codes.clauses.reentrant_corner }}` |
| 26 | paragraph idx=632 | If the diaphragm of a building has a cutout or open area greater than 50% of the gross enclosed diap | `{{ codes.clauses.diaphragm_discontinuity }}` |
| 27 | paragraph idx=610 | As per the clause 5.5.1.4 of NBC 105:2020, if there is an in-plane offset of a vertical seismic forc | `{{ codes.clauses.in_plane_discontinuity }}` |
| 28 | paragraph idx=640 | If there is a discontinuity in a lateral force resisting path such as an out-of-plane of at least on | `{{ codes.clauses.out_of_plane_offset }}` |
| 29 | paragraph idx=256 | the foundation is assumed to be fixed. | `{{ foundation.support_condition }}` |
| 30 | paragraph idx=608 | No soft stoy is observed in the building. | `{{ analysis.soft_storey_result }}` |
| 31 | paragraph idx=611 | No in-plane discontinuity is present in the structure. | `{{ analysis.in_plane_discontinuity_result }}` |
| 32 | paragraph idx=621 | No mass irregularity is seen as the stories are nearly identical. | `{{ analysis.mass_irregularity_result }}` |
| 33 | paragraph idx=625 | The building is rectangular in shape with no re-entrant corners. | `{{ analysis.reentrant_corner_result }}` |
| 34 | caption idx=381 (partial) | Table 9:  Vertical distribution of ULS seismic forces (NBC 105:2025 Cl. 6.3) | `Table 9:  Vertical distribution of ULS seismic forces ({{ codes.edition }} {{ codes.clauses.vertical` |
| 35 | caption idx=405 (partial) | Table 12: Seismic design parameters for the RC moment resisting frame in Damak (NBC 105:2025). | `Table 12: Seismic design parameters for the RC moment resisting frame in {{ building.location }} ({{` |
| 36 | style override for analysis.in_plane_discontinuity_result | style: Heading4 | `style: BodyText` |
| 37 | style override for analysis.mass_irregularity_result | style: Heading4 | `style: BodyText` |
| 38 | anchored image idx=2 (preserved) | [anchored image, cx=5274310 cy=6350] | `preserved (use replace_pic with rId=None)` |
| 39 | image idx=5 | [image #5] | `{{ figure.project.report_figure }}` |
| 40 | image idx=168 | [image #168] | `{{ figure.building.plan_of_building }}` |
| 41 | image idx=175 | [image #175] | `{{ figure.building.section_of_building }}` |
| 42 | image idx=212 | [image #212] | `{{ figure.materials.concrete }}` |
| 43 | image idx=221 | [image #221] | `{{ figure.materials.material_property_rebar }}` |
| 44 | anchored image idx=244 (preserved) | [anchored image, cx=541020 cy=542290] | `preserved (use replace_pic with rId=None)` |
| 45 | anchored image idx=245 (preserved) | [anchored image, cx=1988820 cy=490855] | `preserved (use replace_pic with rId=None)` |
| 46 | anchored image idx=251 (preserved) | [anchored image, cx=2919095 cy=1604010] | `preserved (use replace_pic with rId=rId18)` |
| 47 | anchored image idx=252 (preserved) | [anchored image, cx=81280 cy=1591945] | `preserved (use replace_pic with rId=None)` |
| 48 | image idx=293 | [image #293] | `{{ figure.loads.wall_first }}` |
| 49 | image idx=298 | [image #298] | `{{ figure.loads.wall_second }}` |
| 50 | image idx=302 | [image #302] | `{{ figure.loads.wall_third }}` |
| 51 | image idx=310 | [image #310] | `{{ figure.building.finish_first }}` |
| 52 | image idx=317 | [image #317] | `{{ figure.building.finish_second }}` |
| 53 | image idx=332 | [image #332] | `{{ figure.loads.live_first }}` |
| 54 | image idx=337 | [image #337] | `{{ figure.loads.live_second }}` |
| 55 | image idx=344 | [image #344] | `{{ figure.loads.roof_live_second }}` |
| 56 | image idx=348 | [image #348] | `{{ figure.loads.roof_live_top }}` |
| 57 | image idx=355 | [image #355] | `{{ figure.loads.cases }}` |
| 58 | anchored image idx=360 (preserved) | [anchored image, cx=3675398 cy=1586864] | `preserved (use replace_pic with rId=rId34)` |
| 59 | anchored image idx=362 (preserved) | [anchored image, cx=3675398 cy=1586864] | `preserved (use replace_pic with rId=rId34)` |
| 60 | anchored image idx=379 (preserved) | [anchored image, cx=3354372 cy=560070] | `preserved (use replace_pic with rId=rId36)` |
| 61 | image idx=443 | [image #443] | `{{ figure.elements.design_for_frames }}` |
| 62 | image idx=469 | [image #469] | `{{ figure.elements.beams_design }}` |
| 63 | image idx=471 | [image #471] | `{{ figure.elements.beams_design_b }}` |
| 64 | image idx=475 | [image #475] | `{{ figure.elements.columns_design }}` |
| 65 | image idx=478 | [image #478] | `{{ figure.elements.columns_design_b }}` |
| 66 | anchored image idx=486 (preserved) | [anchored image, cx=5459871 cy=1760220] | `preserved (use replace_pic with rId=rId42)` |
| 67 | anchored image idx=487 (preserved) | [anchored image, cx=2825115 cy=1940560] | `preserved (use replace_pic with rId=rId43)` |
| 68 | image idx=493 | [image #493] | `{{ figure.foundation.reaction_uls_c }}` |
| 69 | image idx=500 | [image #500] | `{{ figure.foundation.design_main }}` |
| 70 | image idx=506 | [image #506] | `{{ figure.foundation.design_b }}` |
| 71 | image idx=508 | [image #508] | `{{ figure.foundation.design_c }}` |
| 72 | image idx=512 | [image #512] | `{{ figure.foundation.design_d }}` |
| 73 | image idx=518 | [image #518] | `{{ figure.staircase.design_main }}` |
| 74 | image idx=520 | [image #520] | `{{ figure.staircase.design_b }}` |
| 75 | image idx=522 | [image #522] | `{{ figure.staircase.design_c }}` |
| 76 | image idx=542 | [image #542] | `{{ figure.drift.displacement }}` |
| 77 | image idx=584 | [image #584] | `{{ figure.drift.displacement_b }}` |
| 78 | anchored image idx=595 (preserved) | [anchored image, cx=2773056 cy=1228344] | `preserved (use replace_pic with rId=rId63)` |
| 79 | image idx=600 | [image #600] | `{{ figure.irregularity.soft_story }}` |
| 80 | anchored image idx=605 (preserved) | [anchored image, cx=1280787 cy=1980247] | `preserved (use replace_pic with rId=rId65)` |
| 81 | anchored image idx=613 (preserved) | [anchored image, cx=2099980 cy=1822704] | `preserved (use replace_pic with rId=rId66)` |
| 82 | anchored image idx=627 (preserved) | [anchored image, cx=2576128 cy=1822703] | `preserved (use replace_pic with rId=rId67)` |
| 83 | anchored image idx=635 (preserved) | [anchored image, cx=3644081 cy=1109472] | `preserved (use replace_pic with rId=rId68)` |
| 84 | image idx=645 | [image #645] | `{{ figure.irregularity.out_of_plane_offset }}` |
| 85 | image idx=651 | [image #651] | `{{ figure.summary.design }}` |
| 86 | image idx=654 | [image #654] | `{{ figure.summary.panel_a }}` |
| 87 | image idx=657 | [image #657] | `{{ figure.summary.panel_b }}` |
| 88 | image idx=666 | [image #666] | `{{ figure.elements.rebar_grid_a }}` |
| 89 | image idx=671 | [image #671] | `{{ figure.elements.rebar_grid_b }}` |
| 90 | image idx=676 | [image #676] | `{{ figure.elements.rebar_story1 }}` |
| 91 | image idx=683 | [image #683] | `{{ figure.elements.rebar_story2 }}` |
| 92 | image idx=688 | [image #688] | `{{ figure.elements.rebar_story3 }}` |
| 93 | table idx=288 | [table table.loads.load_assessment] | `{%tr for r in rows %}...{%tr endfor %}` |
| 94 | table idx=329 | [table table.loads.live_load_intensity] | `{%tr for r in rows %}...{%tr endfor %}` |
| 95 | table idx=383 | [table table.seismic.vertical_force_dist] | `{%tr for r in rows %}...{%tr endfor %}` |
| 96 | table idx=390 | [table table.modal.rayleigh_x] | `{%tr for r in rows %}...{%tr endfor %}` |
| 97 | table idx=393 | [table table.modal.rayleigh_y] | `{%tr for r in rows %}...{%tr endfor %}` |
| 98 | table idx=434 | [table table.modal.periods_mass_part] | `{%tr for r in rows %}...{%tr endfor %}` |
| 99 | table idx=461 | [table table.design.slab_design_output] | `{%tr for r in rows %}...{%tr endfor %}` |
| 100 | paragraphs idx=370..379 | Design of Staircases block | `{%p if building.has_staircase %}...{%p endif %}` |
