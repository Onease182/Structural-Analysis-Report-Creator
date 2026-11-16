# Needs My Decision

This file records heuristic classifications that should be confirmed before a production placeholder map is implemented.

- **Item 199 (CONDITIONAL)**: Table 3: Structural System & Foundation
  - Suggestion: The text mentions a condition-specific building element or check; confirm whether it should be included by project configuration.
- **Item 258 (CONDITIONAL)**: The building was modeled using the ETABS 19.0.0 software. ETABS 19.0.0 is a specialized program designed specifically for the analysis and design of building systems. It offers a user-friendly interface and advanced features, making it bot…
  - Suggestion: The text mentions a condition-specific building element or check; confirm whether it should be included by project configuration.

## Applied owner decisions

- TOC entries for B.3, F.7, and the irregularity checks are `FIXED`; F.8 is fixed but controlled by `building.has_staircase`.
- When `has_staircase` is false, remove the staircase heading and the sample content range through the empty Heading 5; do not alter the DOCX during inventory.
- Foundation support wording is computed from `foundation.type` and `foundation.soil_class`.
- Clause citations are variables: the sample 2020 clauses map to NBC 105:2025 §5.4 clauses recorded in the registry.
- In-plane and mass-irregularity conclusion paragraphs are computed variants and restyled to Body Text; the re-entrant conclusion has rectangular/no-re-entrant variants.
- The foundation reaction image is retained; only its combination text is variable.

## Classification policy

The tool classifies headings and general method/boilerplate as `FIXED`, project facts as `VARIABLE`, data-driven tables as `TABLE`, replacement figures as `IMAGE`, derived results as `COMPUTED`, and condition-specific content as `CONDITIONAL`. Review all non-FIXED items before using the registry to drive report generation.
