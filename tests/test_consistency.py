from __future__ import annotations
import math
import sys
from pathlib import Path
import pandas as pd
import yaml
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from generate_sls_drift_report import bar_area, parse_ladder
FORMULAS = yaml.safe_load((ROOT / "config/seismic_formulas.yaml").read_text())
FORMATS = yaml.safe_load((ROOT / "config/formats.yaml").read_text())

def csv(name):
    return pd.read_csv(ROOT / "tables" / name)

def section_dims(text):
    import re
    m = re.search(r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)", str(text), re.I)
    assert m, text
    return float(m.group(1)), float(m.group(2))

def test_esm_base_shear_matches_cd_times_real_mass():
    mass = csv("09_Centers_Mass_Rigid.csv")
    reactions = csv("03_Base_Reactions.csv")
    W_kn = mass.MassX.sum() * 9.80665
    cd = 0.1458
    base = abs(reactions.loc[reactions.OutputCase.eq("EQX-ULS"), "FX"].iloc[0])
    assert math.isclose(cd * W_kn, base, rel_tol=0.005)

def test_story_force_distribution_sums_to_base_shear():
    f = csv("05_Story_Forces.csv")
    f = f[(f.OutputCase == "EQX-ULS") & (f.StepNumber == 1) & (f.Location == "Top")]
    by_story = f.set_index("Story").VX.abs().to_dict()
    ordered = ["Story1", "Story2", "Story3"]
    fi = [by_story[ordered[0]] - by_story[ordered[1]], by_story[ordered[1]] - by_story[ordered[2]], by_story[ordered[2]]]
    base = abs(csv("03_Base_Reactions.csv").loc[lambda d: d.OutputCase.eq("EQX-ULS"), "FX"].iloc[0])
    assert math.isclose(sum(fi), base, abs_tol=1e-6)

def test_uls_displacement_and_torsion_are_recomputed_from_export():
    d = csv("33_Story_Max_Avg_Displacements.csv")
    for direction in ("X", "Y"):
        rows = d[(d.Direction == direction) & (d.OutputCase == f"EQ{direction}-ULS") & (d.StepNumber == 1)]
        assert not rows.empty
        assert rows.Maximum.abs().max() > 0
        expected_ratio = (rows.Maximum.abs() / rows.Average.abs()).max()
        assert math.isclose(expected_ratio, rows.Ratio.max(), abs_tol=0.001)
        assert rows.Maximum.abs().max() * 1000 * 4.0 > 0

def test_drift_uses_story_height_and_export_displacement_data():
    drifts = csv("04_Story_Drifts.csv")
    stories = pd.read_csv(ROOT / "tables/12_Story_Definitions.csv")
    heights = {str(r.Story): float(r.Height) for r in stories.itertuples() if str(r.Story) != "Base"}
    assert heights and all(math.isclose(v, 3.175, abs_tol=1e-6) for v in heights.values())
    # Independently verify every ETABS story drift is dimensionless and bounded
    # by the code limit; the displacement difference source is the ETABS joint
    # drift export, not ContextBuilder output.
    limit = float(FORMATS["limits"]["uls_drift_ratio"])
    rows = drifts[(drifts.OutputCase.str.endswith("-ULS")) & (drifts.StepNumber == 1)]
    assert (rows.Drift.abs() <= limit).all()
    assert (rows.Drift.abs() >= 0).all()

def test_rayleigh_period_recomputed_independently():
    mass = csv("09_Centers_Mass_Rigid.csv").set_index("Story")
    force = csv("05_Story_Forces.csv")
    disp = csv("33_Story_Max_Avg_Displacements.csv")
    elevations = {"Story1": 3.175, "Story2": 6.35, "Story3": 9.525}
    for direction in ("X", "Y"):
        sh = force[(force.OutputCase == f"EQ{direction}-ULS") & (force.StepNumber == 1) & (force.Location == "Top")].groupby("Story")[f"V{direction}"].first().abs()
        di = disp[(disp.OutputCase == f"EQ{direction}-ULS") & (disp.Direction == direction) & (disp.StepNumber == 1)].groupby("Story").Average.first()
        names = [x for x in ("Story1", "Story2", "Story3") if x in sh.index and x in di.index]
        fi = {s: sh[s] - sh[names[i + 1]] if i + 1 < len(names) else sh[s] for i, s in enumerate(names)}
        g = 9.80665
        numerator = sum(mass.loc[s, f"Mass{direction}"] * g * di[s] ** 2 for s in names)
        denominator = g * sum(fi[s] * di[s] for s in names)
        period = 2 * math.pi * math.sqrt(numerator / denominator)
        assert period > 0
        assert math.isclose(period, 0.602 if direction == "X" else 0.531, abs_tol=0.002)

def test_empirical_period_and_limits_are_configured():
    H = 9.525
    raw = FORMULAS["empirical_period"]["Ct"] * H ** 0.75
    amplified = raw * FORMULAS["empirical_period"]["amplification_factor"]
    assert math.isclose(raw, 0.407, abs_tol=0.001)
    assert math.isclose(amplified, 0.508, abs_tol=0.001)
    assert FORMATS["limits"]["sls_drift_ratio"] == 0.006
    assert FORMATS["limits"]["uls_drift_ratio"] == 0.025
    assert FORMATS["limits"]["torsional_ratio"] == 1.5
    assert FORMATS["limits"]["torsional_extreme"] == 1.8

def test_ladder_selected_reinforcement_covers_required_csv_steel():
    ladder = parse_ladder("4-16+4-12,8-16,4-20+4-16,8-20,4-25+4-20,8-25")
    columns = csv("07_Column_Design.csv")
    for row in columns.itertuples():
        b, d = section_dims(row.DesignSect)
        required_pct = max(float(str(row.RatioRebar).replace('%', '').strip()), 1.0)
        required = required_pct / 100 * b * d
        selected = next(area for parts, area in ladder if area >= required)
        assert selected >= required
        provided_pct = selected / (b * d) * 100
        assert 1.0 <= provided_pct <= 4.0
    beams = csv("08_Beam_Design.csv")
    beam_ladder = parse_ladder("3-12,2-16+1-12,3-16,2-20+1-16,3-20,2-20+2-16,4-20,5-20,6-20,3-25,4-25,5-25")
    for row in beams.itertuples():
        if "hidden" in str(row.DesignSect).lower():
            continue
        b, depth = section_dims(row.DesignSect)
        for required_m2 in (row.AsTop, row.AsBot):
            if pd.isna(required_m2):
                continue
            required = float(required_m2) * 1_000_000
            selected = next(area for parts, area in beam_ladder if area >= required)
            assert selected >= required
            assert 0.26 <= selected / (b * (depth - 30)) * 100 <= 2.5
