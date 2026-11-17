# Needs My Decision

This file is the single owner decision log. The previous generated copy at `docs/needs_my_decision.generated.md` has been removed and merged here.

## Applied owner decisions

- TOC entries for B.3, F.7, and the irregularity checks are `FIXED`; F.8 is fixed but controlled by `building.has_staircase`.
- When `has_staircase` is false, remove the staircase heading and the sample content range through the empty Heading 5; do not alter the DOCX during inventory.
- Foundation support wording is sourced from .e2k point restraints (`foundation.support_condition`, `etabs_table_or_e2k_section=$POINTRESTRAINTS`).
- Clause citations are variables: the sample 2020 clauses map to NBC 105:2025 clauses recorded in the registry. Six mappings remain unresolved (see below).
- In-plane and mass-irregularity conclusion paragraphs are computed variants and restyled to Body Text; the re-entrant conclusion has rectangular/no-re-entrant variants.
- The foundation reaction image is retained; only its combination text is variable.

## Unresolved NBC 105:2025 clause mappings

Do not invent target clauses. Answer the question for each entry; the curated registry will then be updated and the corresponding `codes.clauses.*` entry will receive a `target_clause_2025` value.

- **Item 208 — `codes.clauses.material_properties` (sample Cl. 2.1)**
  - Sample sentence: "According to NBC105:2020, The material should be taken as per Cl.2.1."
  - Question for the owner: Which NBC 105:2025 clause replaces the sample's Cl. 2.1 (material properties)?

- **Item 418 — `codes.clauses.load_combinations` (sample Cl. 3.6.1)**
  - Sample sentence: "When lateral load resisting elements are oriented along mutually orthogonal horizontal directions, the structure system is considered to be parallel and load combinations as specified in clause 3.6.1 of NBC 105:2020 is used for design."
  - Question for the owner: Which NBC 105:2025 clause replaces the sample's Cl. 3.6.1 (parallel-system load combinations)?

- **Item 533 — `codes.clauses.serviceability_drift` (sample Cl. 5.6.3)**
  - Sample sentence: "5.6.3 of NBC 105:2077 is proposed to be used."
  - Question for the owner: Which NBC 105:2025 clause replaces the sample's NBC 105:2077 Cl. 5.6.3 (serviceability drift)?

- **Item 535 — `codes.clauses.serviceability_drift` (sample Cl. 5.6.3)**
  - Sample sentence: "5.6.3 of NBC 105:2077 is applied. The maximum deflection in any story due to the minimum specified design lateral force, with partial load factor of 1.0 shall not exceed 0.006 times the story height. Furthermore, the drift shall not exceed 0.006 in Serviceability and 0.010 in Ultimate limit states."
  - Question for the owner: Which NBC 105:2025 clause replaces the sample's NBC 105:2077 Cl. 5.6.3 (applied drift limit)?

- **Item 591 — `codes.clauses.irregularity_general` (sample Cl. 5.5)**
  - Sample sentence: "One of the basic virtues of earthquake resistant design of structures is that the structure shall be regular as much as possible. It is observed that the structures with simple and regular configurations suffer much less damage during a la…"
  - Question for the owner: Which NBC 105:2025 clause replaces the sample's Cl. 5.5 (general structural irregularity)?

- **Item 593 — `codes.clauses.torsional_irregularity` (sample Cl. 5.5.2.1)**
  - Sample sentence: "As per the clause 5.5.2.1 of NBC 105:2020, torsion irregularity is considered to exist when the maximum horizontal displacement of any floor in the direction of the lateral force, applied at the centre of mass, at one end of the storey is…"
  - Question for the owner: Which NBC 105:2025 clause replaces the sample's Cl. 5.5.2.1 (torsional irregularity)?

## Classification policy

The tool classifies headings and general method/boilerplate as `FIXED`, project facts as `VARIABLE`, data-driven tables as `TABLE`, replacement figures as `IMAGE`, derived results as `COMPUTED`, and condition-specific content as `CONDITIONAL`. Review all non-FIXED items before using the registry to drive report generation.
