# Structural Analysis Report Creator

A Windows/Python toolkit for extracting ETABS model data, validating exported tables, producing structural-analysis figures and drift/reinforcement summaries, and progressively building a report workflow aligned with Nepal’s NBC 105:2025. The master sample, `Chatra Bahadur Ramtel.docx`, is a reference template and must not be modified in place.

> **Engineering safety:** This software does not replace engineering judgment, ETABS review, or verification against the applicable code edition. It must not invent missing values. Unknown or conflicting inputs must be reported for engineer resolution; never silently select a value.

## Project status

The current repository contains ETABS table and SLS drift extractors, CSV validation, figure/report utilities, a legacy DOCX report generator, and a DOCX inventory tool. The placeholder registry and report-generation pipeline are being repaired in phases. The curated registry is subject to an owner review gate before it is used to create a master template. Do not treat the legacy generator as a final NBC 105:2025 report builder.

## Requirements and setup

The ETABS extraction scripts require Windows, an installed ETABS version with its COM/API available, and a Python installation whose architecture is compatible with ETABS. The project dependencies are listed in `requirements.txt`.

From PowerShell, quote the project path because it contains a space:

```powershell
Set-Location "E:\Apps\structural report"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The repository scripts use modern Python type annotations; use Python 3.12 or later unless your checked-out revision documents a different tested version. ETABS COM operations must run on Windows with ETABS installed. The extraction scripts attach to the currently open ETABS model; they do not launch or select a model file for you.

## Existing workflow components

1. Open and analyze the project model in ETABS. Confirm units, load cases, combinations, and design results.
2. Extract general ETABS tables and geometry:

   ```powershell
   python "etabs_extract_tables.py"
   ```

   Outputs are written to `tables\` beside the script, including CSV tables, an Excel workbook when data is available, geometry CSVs, an `.e2k` export when supported, and `extraction_manifest.json`.

3. Extract serviceability drift data (case names can be overridden):

   ```powershell
   python "etabs_extract_sls_drifts.py" --case-x "EQX-SLS" --case-y "EQY-SLS"
   ```

   Outputs are written to `sls_tables\` by default.

4. Validate exported tables:

   ```powershell
   python "validate_extraction.py" --input "tables" --output "validation"
   ```

5. Generate ETABS figures or legacy drift/design summaries when appropriate:

   ```powershell
   python "generate_etabs_figures.py" --tables "tables" --output "figures"
   python "generate_sls_drift_report.py" --tables "sls_tables" --output "report\SLS_Drift_Check.jpg"
   ```

   Review every result and its input case/unit provenance. The reports are not a substitute for verifying the governing code checks.

6. Inventory the unchanged sample DOCX when working on the template tooling:

   ```powershell
   python "tools\inventory_template.py" --input "Chatra Bahadur Ramtel.docx" --help
   ```

   Use output paths that do not overwrite the original sample or the curated registry. The inventory tool is being updated to route generated registry output to a separate `*.generated.yaml` file.

The legacy `generate_structural_report.py` remains in the repository for compatibility and analysis only; it is not deleted, and the planned report builder will supersede it after its own validation and review.

## Tests

Run the automated tests from the repository root:

```powershell
python -m pytest -q
```

The ETABS COM extractors require Windows and a live ETABS model for integration testing. Unit tests should not require access to a live engineering model; use small fixtures and clearly marked test data.

## Data and provenance rules

- Source priority: ETABS API/CSV, then `.e2k`, then engineer-entered Excel values, then computed values.
- Record source, units, and conflicts. Do not silently resolve conflicting values.
- Do not substitute example values for project inputs. Missing values belong in an explicit unresolved list.
- Keep project-specific case names, response factors, limits, units, and optional sections in project configuration; do not hard-code the sample’s storey count or case names into reusable calculations.
- Do not overwrite or edit the original `Chatra Bahadur Ramtel.docx` sample.
