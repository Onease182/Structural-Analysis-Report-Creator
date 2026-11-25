# ULS/SLS Model Comparison

Computed from parsed real ULS and SLS e2k records. Every difference is listed by parsed section; SLS remains restricted to serviceability use.

- `frame_sections` `Beam 250 x 430.I2MOD`: ULS='0.35'; SLS='0.7'
- `frame_sections` `Beam 250 x 430.I3MOD`: ULS='0.35'; SLS='0.7'
- `frame_sections` `Column 355 x 355.I2MOD`: ULS='0.7'; SLS='0.9'
- `frame_sections` `Column 355 x 355.I3MOD`: ULS='0.7'; SLS='0.9'
- `frame_sections` `Hidden Beam 125 x 125.I2MOD`: ULS='0.35'; SLS='0.7'
- `frame_sections` `Hidden Beam 125 x 125.I3MOD`: ULS='0.35'; SLS='0.7'
- `frame_sections` `S. Beam 250X250.I2MOD`: ULS='0.35'; SLS='0.7'
- `frame_sections` `S. Beam 250X250.I3MOD`: ULS='0.35'; SLS='0.7'
- `frame_modifiers` `Beam 250 x 430.I2MOD`: ULS='0.35'; SLS='0.7'
- `frame_modifiers` `Beam 250 x 430.I3MOD`: ULS='0.35'; SLS='0.7'
- `frame_modifiers` `Column 355 x 355.I2MOD`: ULS='0.7'; SLS='0.9'
- `frame_modifiers` `Column 355 x 355.I3MOD`: ULS='0.7'; SLS='0.9'
- `frame_modifiers` `Hidden Beam 125 x 125.I2MOD`: ULS='0.35'; SLS='0.7'
- `frame_modifiers` `Hidden Beam 125 x 125.I3MOD`: ULS='0.35'; SLS='0.7'
- `frame_modifiers` `S. Beam 250X250.I2MOD`: ULS='0.35'; SLS='0.7'
- `frame_modifiers` `S. Beam 250X250.I3MOD`: ULS='0.35'; SLS='0.7'
- `load_patterns` `EQX-SLS`: ULS=missing; SLS=present
- `load_patterns` `EQX-ULS`: ULS=present; SLS=missing
- `load_patterns` `EQY-SLS`: ULS=missing; SLS=present
- `load_patterns` `EQY-ULS`: ULS=present; SLS=missing
- `load_combinations` `0.9DL+EQX.load_cases`: ULS=[{'LoadCase': 'Dead', 'SF': '0.9'}, {'LoadCase': 'EQX-ULS', 'SF': '1'}]; SLS=[{'LoadCase': 'Dead', 'SF': '0.9'}, {'LoadCase': 'EQX-SLS', 'SF': '1'}]
- `load_combinations` `0.9DL+EQY.load_cases`: ULS=[{'LoadCase': 'Dead', 'SF': '0.9'}, {'LoadCase': 'EQY-ULS', 'SF': '1'}]; SLS=[{'LoadCase': 'Dead', 'SF': '0.9'}, {'LoadCase': 'EQY-SLS', 'SF': '1'}]
- `load_combinations` `0.9DL-EQX.load_cases`: ULS=[{'LoadCase': 'Dead', 'SF': '0.9'}, {'LoadCase': 'EQX-ULS', 'SF': '-1'}]; SLS=[{'LoadCase': 'Dead', 'SF': '0.9'}, {'LoadCase': 'EQX-SLS', 'SF': '-1'}]
- `load_combinations` `0.9DL-EQY.load_cases`: ULS=[{'LoadCase': 'Dead', 'SF': '0.9'}, {'LoadCase': 'EQY-ULS', 'SF': '-1'}]; SLS=[{'LoadCase': 'Dead', 'SF': '0.9'}, {'LoadCase': 'EQY-SLS', 'SF': '-1'}]
- `load_combinations` `1.2DL+0.3LL+EQX.load_cases`: ULS=[{'LoadCase': 'Dead', 'SF': '1.2'}, {'LoadCase': 'Live', 'SF': '0.3'}, {'LoadCase': 'EQX-ULS', 'SF': '1'}]; SLS=[{'LoadCase': 'Dead', 'SF': '1.2'}, {'LoadCase': 'Live', 'SF': '0.3'}, {'LoadCase': 'EQX-SLS', 'SF': '1'}]
- `load_combinations` `1.2DL+0.3LL+EQY.load_cases`: ULS=[{'LoadCase': 'Dead', 'SF': '1.2'}, {'LoadCase': 'Live', 'SF': '0.3'}, {'LoadCase': 'EQY-ULS', 'SF': '1'}]; SLS=[{'LoadCase': 'Dead', 'SF': '1.2'}, {'LoadCase': 'Live', 'SF': '0.3'}, {'LoadCase': 'EQY-SLS', 'SF': '1'}]
- `load_combinations` `1.2DL+0.3LL-EQX.load_cases`: ULS=[{'LoadCase': 'Dead', 'SF': '1.2'}, {'LoadCase': 'Live', 'SF': '0.3'}, {'LoadCase': 'EQX-ULS', 'SF': '-1'}]; SLS=[{'LoadCase': 'Dead', 'SF': '1.2'}, {'LoadCase': 'Live', 'SF': '0.3'}, {'LoadCase': 'EQX-SLS', 'SF': '-1'}]
- `load_combinations` `1.2DL+0.3LL-EQY.load_cases`: ULS=[{'LoadCase': 'Dead', 'SF': '1.2'}, {'LoadCase': 'Live', 'SF': '0.3'}, {'LoadCase': 'EQY-ULS', 'SF': '-1'}]; SLS=[{'LoadCase': 'Dead', 'SF': '1.2'}, {'LoadCase': 'Live', 'SF': '0.3'}, {'LoadCase': 'EQY-SLS', 'SF': '-1'}]
