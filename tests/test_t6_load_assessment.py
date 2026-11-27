from __future__ import annotations

import math

from src.input_workbook import InputWorkbook


def sample_ctx():
    return {"loads": {
        "wall_unit_weight": 19.625,
        "plaster_unit_weight": 20.4,
        "wall_height_m": 3.175,
        "floor_finish_thickness_mm": 20,
        "floor_finish_unit_weight": 24.0,
        "slab_thickness_mm": 125,
        "slab_unit_weight": 24.0,
        "live_load_corridor": 3.0,
        "roof_live_load": 1.5,
    }}


def test_t6_matches_sample_structure():
    rows = InputWorkbook().build_t6_load_assessment(sample_ctx())
    assert len(rows) == 39
    assert all(len(row) == 6 for row in rows)
    assert rows[1][0] == "Wall Load"
    assert rows[25][0] == "FLOOR FINISH"
    assert rows[31][0] == "ROOF LIVE"


def test_t6_wall_and_finish_arithmetic_is_independent():
    rows = InputWorkbook().build_t6_load_assessment(sample_ctx())
    avg_uw = (19.625 + 20.4) / 2
    expected_250 = 0.250 * 3.175 * avg_uw
    assert math.isclose(float(rows[18][3]), expected_250, abs_tol=0.005)
    assert math.isclose(float(rows[22][3]), expected_250 * 0.7, abs_tol=0.05)
    assert math.isclose(float(rows[27][4]), 0.020 * 24.0, abs_tol=0.001)
    assert math.isclose(float(rows[28][4]), 0.125 * 24.0, abs_tol=0.001)


def test_t6_does_not_invent_missing_values():
    rows = InputWorkbook().build_t6_load_assessment({"loads": {"wall_height_m": 3.175}})
    assert rows[3][1] == "UNRESOLVED"
    assert rows[17][3] == "UNRESOLVED"
    assert rows[34][1] == "UNRESOLVED"
