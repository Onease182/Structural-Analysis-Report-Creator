# Golden Values

Reproduced from the sample project's ETABS tables (`tables/` and `sls_tables/`).
Every value is computed from the CSVs using the documented source.

## Rayleigh Period

| Metric | Sample Value | Computed Value | Tolerance | Result | CSV Source |
|--------|-------------|----------------|-----------|--------|------------|
| Rayleigh T(X) | 0.602 s | 0.602 s | 0.001 | PASS | Wi: 09_Centers_Mass_Rigid.csv MassX×9.81; di: 33_Story_Max_Avg_Displacements.csv Average (EQX-ULS step 1 Dir X); Fi: 05_Story_Forces.csv VX (cumulative differenced top-down, EQX-ULS step 1.0 Location Top) |
| Rayleigh T(Y) | 0.531 s | 0.531 s | 0.001 | PASS | Same as X but EQY-ULS, Direction Y, VY |

Formula: T = 2π√(Σ(Wi·di²) / (g·Σ(Fi·di))), g = 9.81 m/s²

### Data Sources (exact CSV, column, filter)

| Variable | CSV File | Column | Filter |
|----------|----------|--------|--------|
| Wi (story weight, kN) | 09_Centers_Mass_Rigid.csv | MassX | × 9.81 |
| di (avg displacement, m) | 33_Story_Max_Avg_Displacements.csv | Average | OutputCase=EQX-ULS, StepNumber=1, Direction=X |
| Fi (per-story force, kN) | 05_Story_Forces.csv | VX | OutputCase=EQX-ULS, Location=Top, StepNumber=1.0; differenced top-down |

### Computation Detail (X-direction)

| Story | Wi (kN) | di (mm) | Fi (kN) | Wi·di² | Fi·di |
|-------|---------|---------|---------|--------|-------|
| Story3 | 200.93 | 26.295 | 54.61 | 0.138929 | 1.435988 |
| Story2 | 606.33 | 15.770 | 109.68 | 0.150790 | 1.729723 |
| Story1 | 839.53 | 7.316 | 75.73 | 0.044935 | 0.554006 |
| **Total** | | | | **0.3347** | **3.7197** |

T(X) = 2π√(0.3347 / (9.81 × 3.7197)) = 2π√(0.009183) = **0.602 s** ✓

## Base Shear

| Metric | Sample Value | Computed Value | Tolerance | Result | CSV Source |
|--------|-------------|----------------|-----------|--------|------------|
| ESM Base Shear X | 240.02 kN | 240.02 kN | 0.01 | PASS | 03_Base_Reactions.csv FX, OutputCase=EQX-ULS StepNumber=1.0 |
| ESM Base Shear Y | 240.02 kN | 240.02 kN | 0.01 | PASS | 03_Base_Reactions.csv FY, OutputCase=EQY-ULS StepNumber=1.0 |

## Empirical Period

| Metric | Sample Value | Computed Value | Tolerance | Result | Source |
|--------|-------------|----------------|-----------|--------|--------|
| Empirical T (unamplified) | 0.407 s | 0.407 s | 0.001 | PASS | T = Ct × H^0.75, Ct=0.075 (RC frame), H=9.525m |
| Empirical T (amplified ×1.25) | 0.508 s | 0.509 s | 0.001 | PASS | 0.407 × 1.25 = 0.509 (sample rounds to 0.508) |

## Modal Periods

| Metric | Sample Value | Computed Value | Tolerance | Result | CSV Source |
|--------|-------------|----------------|-----------|--------|------------|
| Mode 1 Period | 0.642 s | 0.642 s | 0.001 | PASS | 02_Modal_Mass_Ratios.csv Period, Mode=1 |
| Mode 2 Period | 0.531 s | 0.531 s | 0.001 | PASS | 02_Modal_Mass_Ratios.csv Period, Mode=2 |

## Scale Factor

| Metric | Sample Value | Computed Value | Tolerance | Result | Source |
|--------|-------------|----------------|-----------|--------|--------|
| ESM vs Modal Scale Factor | UNRESOLVED | — | — | UNRESOLVED | No RS (response spectrum) case in 03_Base_Reactions.csv; only LinStatic EQX-ULS/EQY-ULS present |

## SLS Displacement Conflict (20.821 vs 22.377 mm)

| Source | Value | Explanation |
|--------|-------|-------------|
| S13_Joint_Displacements.csv (joint maxima) | 20.821 mm | Maximum joint Ux for EQX-SLS step 2 at Story3 |
| S14_Story_Max_Avg_Displacements.csv (story maxima) | 22.377 mm | Maximum story displacement for EQX-SLS step 2 at Story3 |

The sample report uses the **story maximum** from S14 (22.377 mm). The S13 joint
value (20.821 mm) is a different quantity (a single joint, not the story max).
Both are kept as separate named keys; the conflict is resolved by using S14 for
the report and S13 as a cross-reference.

## Column Steel

| Metric | Sample Value | Computed Value | Tolerance | Result | CSV Source |
|--------|-------------|----------------|-----------|--------|------------|
| Column Max Steel % | 1.24% | UNRESOLVED | — | UNRESOLVED | 07_Column_Design.csv RatioRebar shows 0.8% — does not match sample's 1.24%. The sample may use 07b_Column_PMM_Env.csv. |

## Beam Steel

| Metric | Sample Value | Computed Value | Tolerance | Result | CSV Source |
|--------|-------------|----------------|-----------|--------|------------|
| Beam Max Steel % | 0.764% | UNRESOLVED | — | UNRESOLVED | 08_Beam_Design.csv AsTop/AsBot — needs area calculation from section size |

## unresolved.md

- Scale factor: No RS (response spectrum) case in 03_Base_Reactions.csv; only LinStatic EQX-ULS/EQY-ULS present. Cannot compute ESM vs modal scale factor.
- Column steel: 07_Column_Design.csv RatioRebar = 0.8%, does not match sample's 1.24%. May need 07b_Column_PMM_Env.csv or manual calculation from required steel area.
- Beam steel: Needs area calculation from AsTop/AsBot values and section dimensions.

## conflicts.md

- SLS displacement: S13 joint max (20.821 mm) vs S14 story max (22.377 mm) — different quantities, not a source conflict. S14 (story max) is used for the report.
