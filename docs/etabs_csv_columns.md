# ETABS CSV contract used by `ContextBuilder`

The builder validates columns before reading values. A missing column is reported in `unresolved.md`; it is never replaced with `0`, `1`, or a sample value.

| File pattern | Required / consumed columns | Purpose |
|---|---|---|
| `02_Modal_Mass_Ratios.csv` or filename containing `modal` and `mass` | `Mode`, `Period`, `UX`, `UY`; cumulative `SumUX`/`SumUY` (or spaced variants) preferred | Modal participation and period inventory |
| `05_Story_Forces.csv` or filename containing `story` and `force` | `Story`; one of `VX`, `VY`, `Base Shear`, `Shear Force`; optional `Displacement`/`UX`/`UY` and `W`/`Weight`/`Wi`/`Story Weight` | Base shear and Rayleigh-period inputs |
| `04_Story_Drifts.csv` or filename containing `story` and `drift` | `Story`; `Drift` or `Drift Ratio`; optional `Displacement`/`U1`/`U2` | ULS/SLS drift inventory |
| `03_Base_Reactions.csv` or filename containing `base` and `reaction` | `OutputCase`; one of `FX`, `FY`, `FZ` | Modal/base-reaction comparison |
| `07_Column_Design.csv` or filename containing `column` and `design` | One of `RatioRebar`, `RebarPct`, `SteelPct`, `% Steel` | Column steel percentage and 1% minimum check |
| SLS displacement CSV | One of `Maximum`, `Displacement`, `UX`, `UY` | SLS displacement |
| SLS torsion / `33_Story_Max_Avg_Displacements.csv` | One of `Ratio`, `delta_max/delta_avg`, `Max/Avg` | Torsional irregularity |

## Extraction-script cross-check

`etabs_extract_tables.py` writes the numbered ETABS tables listed above and records the actual columns in its manifest. `etabs_extract_sls_drifts.py` writes `S01_Story_Drifts.csv`, `S02_Joint_Drifts.csv`, `S13_Joint_Displacements.csv`, and `S14_Story_Max_Avg_Displacements.csv`. The report builder accepts the relevant aliases above, but it does not infer a missing engineering quantity from an unrelated column.

For a project-specific extraction, run `validate_extraction.py` first. Its `EXPECTED_COLUMNS` contract is the authoritative check for the numbered ETABS package; this document describes the narrower subset consumed by `context_builder.py`.
