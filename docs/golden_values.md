# Part A golden values

These values are checked by `tests/test_golden_sample.py`. They are anonymised fixture values, not client data. A golden value may only be changed when the source fixture or an owner-approved formula/configuration changes.

| Metric | Source | Tolerance | Computed | Expected |
|---|---|---:|---:|---:|
| Empirical period, unamplified | `tests/fixtures/sample.e2k` story heights; `config/seismic_formulas.yaml` (`Ct=0.075`) | 0.001 s | `0.075 * 9.525^0.75 = 0.406640 s` | 0.407 s |
| Empirical period, amplified | Same as above; configured amplification factor `1.25` | 0.001 s | `0.406640 * 1.25 = 0.508300 s` | 0.508 s |
| Rayleigh period | Synthetic anonymised story force/displacement rows in `test_golden_sample.py` | 0.001 s | `2*pi*sqrt(sum(Wi*di²)/(g*sum(Fi*di))) = 0.411192 s` | 0.411 s |
| `Cd` | `Z=0.35`, `I=1`, `Rmu=4`, Soil C spectrum `C(T)=2.5`, `Omega_s=1.5` | 0.0001 | `2.5*0.35*1/(4*1.5) = 0.145833` | 0.1458 |
| SLS drift limit | `config/formats.yaml`, NBC 105:2025 Cl. 5.5.3 | exact | `0.006` | `0.006` |
| ULS drift limit | `config/formats.yaml` | exact | `0.025` | `0.025` |
| Torsion limit / extreme | `config/formats.yaml` | exact | `1.5 / 1.8` | `1.5 / 1.8` |
| Minimum column steel | `config/formats.yaml`, NBC 105:2025 Cl. 4.2.2b | exact | `1.0%` | `1.0%` |

The repository does not contain the client’s raw ETABS CSV package. Therefore base-shear, scale-factor, story-drift, displacement, torsion, and steel golden values requiring client extraction remain **UNRESOLVED** until an anonymised fixture package is supplied. The builder records this state rather than manufacturing sample values.
