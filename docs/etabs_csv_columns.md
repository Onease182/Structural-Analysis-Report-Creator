# ETABS CSV contract used by `ContextBuilder`

The committed `tables/` and `sls_tables/` directories are the hypothetical sample project's fixtures. Validation is strict: a missing file or required column is a failure, never a skipped test or fabricated value.

| File | Required / consumed columns | Purpose |
|---|---|---|
| `03_Base_Reactions.csv` | `OutputCase`, `FX`, `FY`, `FZ`, `MX`, `MY`, `MZ` | Base shear; `EQX-ULS` uses `FX`, `EQY-ULS` uses `FY` |
| `04_Story_Drifts.csv` | `Story`, `OutputCase`, `Direction`, `Drift` | ULS story drifts |
| `05_Story_Forces.csv` | `Story`, `OutputCase`, `VX`, `VY` | Story-force distribution and Rayleigh inputs; not base shear |
| `07_Column_Design.csv` | `Story`, `Label`, `RatioRebar` | Column steel percentage |
| `08_Beam_Design.csv` | `Story`, `Label`, `AsTop`, `AsBot` | Beam reinforcement areas |
| `14_Joint_Coordinates.csv` | `Joint`, `GlobalX`, `GlobalY`, `GlobalZ` | Joint geometry |
| `17_Frame_Assignments.csv` | `Story`, `Label`, `AnalysisSect`, `DesignSect` | Frame section assignments |
| `33_Story_Max_Avg_Displacements.csv` | `Story`, `OutputCase`, `Direction`, `Maximum`, `Average`, `Ratio` | ULS displacements and torsion |
| `S01_Story_Drifts.csv` | `Story`, `OutputCase`, `Direction`, `Drift` | SLS story drifts |
| `S13_Joint_Displacements.csv` | `Story`, `OutputCase`, `Ux`, `Uy` | SLS joint displacement fallback |
| `S14_Story_Max_Avg_Displacements.csv` | `Story`, `OutputCase`, `Direction`, `Maximum`, `Average`, `Ratio` | SLS displacements and torsion |

`etabs_extract_tables.py` produces the ULS/ETABS package; `etabs_extract_sls_drifts.py` produces the SLS package. The report values and golden expectations are independently transcribed from `Chatra Bahadur Ramtel.docx`, not from the implementation under test.
