# Needs My Decision

This file records heuristic classifications that should be confirmed before a production placeholder map is implemented.

- **Item 156 (VARIABLE)**: The analysis and design in this report follow the codes and references listed below. Seismic loading, analysis and ductile detailing follow NBC 105:2025.
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 199 (CONDITIONAL)**: Table 3: Structural System & Foundation
  - Suggestion: Include this section/table only when its configured content applies.
- **Item 208 (VARIABLE)**: According to NBC105:2020, The material should be taken as per Cl.2.1.
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 240 (VARIABLE)**: Due to the eccentricity arising between the center of mass and the center of rigidity at each floor level of the building, code requires increase in shear forces on the lateral force resisting elements caused by the twisting about the vert…
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 258 (CONDITIONAL)**: The building was modeled using the ETABS 19.0.0 software. ETABS 19.0.0 is a specialized program designed specifically for the analysis and design of building systems. It offers a user-friendly interface and advanced features, making it bot…
  - Suggestion: The software/version narrative is project-specific and may be omitted.
- **Item 381 (VARIABLE)**: Table 9: Vertical distribution of ULS seismic forces (NBC 105:2025 Cl. 6.3)
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 397 (VARIABLE)**: Ch(t)=Spectral Shape factor as per cl.4.1.2 Z= Seismic Zoning Factor as per 4.1.4 I=Importance factor as per 4.1.5
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 413 (VARIABLE)**: As per Clause 3.2.1 of NBC 105:2025, the Equivalent Static Method may be used for all serviceability limit state calculations regardless of the building characteristics. For the ultimate limit state, the Equivalent Static Method may be use…
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 418 (VARIABLE)**: When lateral load resisting elements are oriented along mutually orthogonal horizontal directions, the structure system is considered to be parallel and load combinations as specified in clause 3.6.1 of NBC 105:2020 is used for design.
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 419 (VARIABLE)**: For Parallel System (Cl. 3.6.1)
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 430 (VARIABLE)**: NBC105:2025 clause 7.3 states that number of modes to be used in the analysis should be such that the sum total of modal masses of all modes considered is at least 90 percent of the total seismic mass of the structure. The analysis was car…
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 533 (VARIABLE)**: 5.6.3 of NBC 105:2077 is proposed to be used.
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 535 (VARIABLE)**: 5.6.3 of NBC 105:2077 is applied. The maximum deflection in any story due to the minimum specified design lateral force, with partial load factor of 1.0 shall not exceed 0.006 times the story height. Furthermore, the drift shall not exceed…
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 591 (VARIABLE)**: One of the basic virtues of earthquake resistant design of structures is that the structure shall be regular as much as possible. It is observed that the structures with simple and regular configurations suffer much less damage during a la…
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 593 (VARIABLE)**: As per the clause 5.5.2.1 of NBC 105:2020, torsion irregularity is considered to exist when the maximum horizontal displacement of any floor in the direction of the lateral force, applied at the centre of mass, at one end of the storey is…
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 603 (VARIABLE)**: As per the clause 5.5.1.2, a soft story is the one whose stiffness of the lateral force resisting system is less than 70% of the lateral force resisting system stiffness in an adjacent story above or below, or less than 80% of the average…
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 610 (VARIABLE)**: As per the clause 5.5.1.4 of NBC 105:2020, if there is an in-plane offset of a vertical seismic force-resisting element resulting in overturning demands on supporting structural elements, then there will be in-plane discontinuity in vertic…
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 617 (VARIABLE)**: If there is a difference of more than 50% between the effective masses of two consecutive storeys, then there will be the existence of mass irregularity in the structural system of the building as per the clause 5.5.1.5 of NBC 105:2020. Ho…
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 624 (VARIABLE)**: As per the clause 5.5.2.2 of NBC 105:2020, a structure is said to have re-entrant corner irregularity in a direction if its structural configuration has a projection of greater than 15% of its overall dimensions in that direction.
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 632 (VARIABLE)**: If the diaphragm of a building has a cutout or open area greater than 50% of the gross enclosed diaphragm area or if the effective diaphragm stiffness changes more than 50% from one story to the next, then as per the clause 5.5.2.3 of NBC…
  - Suggestion: Clause edition/number requires the owner-approved mapping.
- **Item 640 (VARIABLE)**: If there is a discontinuity in a lateral force resisting path such as an out-of-plane of at least one vertical element in the structural system of the building, then as per the clause 5.5.2.4 of NBC 105:2020, the building is said to have o…
  - Suggestion: Clause edition/number requires the owner-approved mapping.

## Applied owner decisions

- TOC entries for B.3, F.7, and the irregularity checks are `FIXED`; F.8 is fixed but controlled by `building.has_staircase`.
- When `has_staircase` is false, remove the staircase heading and the sample content range through the empty Heading 5; do not alter the DOCX during inventory.
- Foundation support wording is computed from `foundation.type` and `foundation.soil_class`.
- Clause citations are variables: the sample 2020 clauses map to NBC 105:2025 §5.4 clauses recorded in the registry.
- In-plane and mass-irregularity conclusion paragraphs are computed variants and restyled to Body Text; the re-entrant conclusion has rectangular/no-re-entrant variants.
- The foundation reaction image is retained; only its combination text is variable.

## Classification policy

The tool classifies headings and general method/boilerplate as `FIXED`, project facts as `VARIABLE`, data-driven tables as `TABLE`, replacement figures as `IMAGE`, derived results as `COMPUTED`, and condition-specific content as `CONDITIONAL`. Review all non-FIXED items before using the registry to drive report generation.
