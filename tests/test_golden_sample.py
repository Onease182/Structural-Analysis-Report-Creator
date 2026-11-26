from __future__ import annotations
import subprocess, sys, tempfile
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.context_builder import ContextBuilder

def get(ctx, key):
    value = ctx
    for part in key.split('.'):
        value = value.get(part) if isinstance(value, dict) else None
    return value

def test_golden_config_has_report_locations_and_precision():
    spec = yaml.safe_load((ROOT / 'config/golden_report_values.yaml').read_text())
    assert spec['values']
    assert all(item.get('location') and item.get('precision') is not None for item in spec['values'])
    assert 'word/media/image51.jpeg' in {item['location'] for item in spec['values']}

def test_generated_golden_table_has_no_fail_or_unresolved_rows():
    result = subprocess.run([sys.executable, 'tools/generate_golden_values.py'], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    table = (ROOT / 'docs/golden_values.md').read_text()
    assert '| FAIL |' not in table
    assert '| UNRESOLVED |' not in table

def test_shared_computable_context_values_have_provenance():
    with tempfile.TemporaryDirectory() as td:
        builder = ContextBuilder()
        ctx = builder.build(ROOT/'tables', ROOT/'sls_tables', ROOT/'tables/Chatra Bahadur Ramel_ULS.e2k', ROOT/'inputs/Project_Input.xlsx', Path(td))
    for key in ('modal.rayleigh_period_s', 'modal.selected_period_method', 'totals.wi_kg', 'totals.wi_hik', 'totals.fi', 'seismic.alpha', 'seismic.tc', 'seismic.time_coefficient_kt', 'seismic.hsc_uls', 'seismic.hsc_sls', 'materials.as_building_is_less_than_12_m', 'structural.system_type', 'slab.type'):
        assert get(ctx, key) is not None, key
        assert key in builder.source_details, key
        assert builder.source_details[key]['file']
        assert builder.source_details[key]['column']
        assert builder.source_details[key]['filter']
