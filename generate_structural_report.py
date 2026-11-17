"""
generate_structural_report.py

Compile report_data.json, produced by validate_extraction.py, into an editable
professional Word report with the agreed structural-analysis report structure.

Usage:
    python generate_structural_report.py \
        --input validation/report_data.json \
        --output report/structural_analysis_report.docx \
        --title "Structural Analysis and Design Report"

Requirements:
    pip install python-docx

The generated document contains a live Word Table of Contents field. Open the
DOCX in Microsoft Word or LibreOffice, select the table of contents, and update
fields (Ctrl+A, then F9 in Word) to populate page numbers.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


NAVY = "17365D"
BLUE = "1F4E79"
LIGHT_BLUE = "D9EAF7"
LIGHT_GREY = "F2F4F6"
DARK_GREY = "404040"
GREEN = "E2F0D9"
YELLOW = "FFF2CC"
RED = "FCE4D6"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("validation/report_data.json"))
    parser.add_argument("--output", type=Path, default=Path("report/structural_analysis_report.docx"))
    parser.add_argument("--title", default="Structural Analysis and Design Report")
    parser.add_argument("--project", default=None, help="Project name; defaults to the model filename stem.")
    parser.add_argument("--author", default="Structural Engineering Consultancy")
    return parser.parse_args()


def safe(value: Any, default: str = "Not available") -> str:
    if value is None or value == "":
        return default
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return default
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def fmt(value: Any, digits: int = 3) -> str:
    if value is None or value == "":
        return "Not available"
    try:
        number = float(value)
        if not math.isfinite(number):
            return "Not available"
        return f"{number:.{digits}f}"
    except (TypeError, ValueError):
        return safe(value)


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_text(cell, text: Any, bold: bool = False, color: str | None = None) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run(safe(text, ""))
    run.bold = bold
    run.font.name = "Aptos"
    run.font.size = Pt(9)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_table_borders(table, color: str = "B7C9D6") -> None:
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def add_field(paragraph, instruction: str) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(separate)
    run._r.append(end)


def add_page_number(paragraph) -> None:
    paragraph.add_run("Page ")
    add_field(paragraph, "PAGE")
    paragraph.add_run(" of ")
    add_field(paragraph, "NUMPAGES")


def add_heading(doc: Document, text: str, level: int = 1):
    paragraph = doc.add_heading(text, level=level)
    paragraph.paragraph_format.keep_with_next = True
    return paragraph


def add_body(doc: Document, text: str, bold_prefix: str | None = None) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.line_spacing = 1.15
    if bold_prefix and text.startswith(bold_prefix):
        paragraph.add_run(bold_prefix).bold = True
        paragraph.add_run(text[len(bold_prefix):])
    else:
        paragraph.add_run(text)


def add_note(doc: Document, text: str, fill: str = LIGHT_BLUE) -> None:
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_shading(cell, fill)
    set_cell_text(cell, text)
    cell.paragraphs[0].paragraph_format.space_after = Pt(0)
    set_table_borders(table, color=fill)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def add_kv_table(doc: Document, rows: Iterable[tuple[str, Any]], title: str | None = None) -> None:
    if title:
        add_heading(doc, title, level=3)
    data = [(key, safe(value)) for key, value in rows]
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0]
    set_cell_text(hdr.cells[0], "Item", bold=True, color="FFFFFF")
    set_cell_text(hdr.cells[1], "Value", bold=True, color="FFFFFF")
    set_cell_shading(hdr.cells[0], NAVY)
    set_cell_shading(hdr.cells[1], NAVY)
    set_repeat_table_header(hdr)
    for key, value in data:
        cells = table.add_row().cells
        set_cell_text(cells[0], key, bold=True)
        set_cell_text(cells[1], value)
    set_table_borders(table)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def add_records_table(
    doc: Document,
    title: str,
    records: list[dict[str, Any]],
    columns: list[str] | None = None,
    max_rows: int = 30,
) -> None:
    add_heading(doc, title, level=3)
    if not records:
        add_note(doc, "No extracted records are available for this section.", YELLOW)
        return
    if columns is None:
        columns = list(records[0].keys())
    columns = [column for column in columns if any(column in record for record in records)]
    if not columns:
        add_note(doc, "The extracted table has no displayable columns.", YELLOW)
        return
    shown = records[:max_rows]
    table = doc.add_table(rows=1, cols=len(columns))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    header = table.rows[0]
    for index, column in enumerate(columns):
        set_cell_text(header.cells[index], column, bold=True, color="FFFFFF")
        set_cell_shading(header.cells[index], NAVY)
    set_repeat_table_header(header)
    for record in shown:
        cells = table.add_row().cells
        for index, column in enumerate(columns):
            set_cell_text(cells[index], record.get(column, ""))
            if len(table.rows) % 2 == 0:
                set_cell_shading(cells[index], LIGHT_GREY)
    set_table_borders(table)
    if len(records) > max_rows:
        add_body(doc, f"Showing {max_rows} of {len(records)} extracted records. The complete table is preserved in report_data.json.")


def add_status_table(doc: Document, validation: dict[str, Any]) -> None:
    rows = [
        ("Overall validation status", validation.get("overall_status")),
        ("Validation checks", len(validation.get("checks", []))),
        ("Tables inspected", len(validation.get("tables", {}))),
        ("Read errors", len(validation.get("read_errors", {}))),
    ]
    add_kv_table(doc, rows, "Validation Status")
    checks = validation.get("checks", [])
    if checks:
        records = [
            {"Status": item.get("severity"), "Table": item.get("table", ""), "Message": item.get("message", "")}
            for item in checks
        ]
        add_records_table(doc, "Validation Checks", records, ["Status", "Table", "Message"], max_rows=60)


def add_toc(doc: Document) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_field(paragraph, 'TOC \\o "1-3" \\h \\z \\u')
    add_note(doc, "Update the table of contents in Word by selecting it and pressing F9. Page numbers are populated by Word when fields are updated.")


def add_appendix_table(doc: Document, title: str, data: dict[str, Any], max_rows: int = 25) -> None:
    records = data.get("records", []) if isinstance(data, dict) else []
    if records:
        columns = list(records[0].keys())
        add_records_table(doc, title, records, columns, max_rows=max_rows)
    else:
        add_heading(doc, title, level=3)
        add_note(doc, "No records are available for this appendix.", YELLOW)


def setup_document(doc: Document) -> None:
    section = doc.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.75)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(DARK_GREY)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15

    for style_name, size, color in (("Title", 26, NAVY), ("Heading 1", 18, NAVY), ("Heading 2", 14, BLUE), ("Heading 3", 11.5, BLUE)):
        style = styles[style_name]
        style.font.name = "Aptos Display" if style_name in {"Title", "Heading 1"} else "Aptos"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.space_before = Pt(14 if style_name == "Heading 1" else 9)
        style.paragraph_format.space_after = Pt(5)
        style.paragraph_format.keep_with_next = True

    if "Caption" not in styles:
        caption = styles.add_style("Caption", WD_STYLE_TYPE.PARAGRAPH)
    else:
        caption = styles["Caption"]
    caption.font.name = "Aptos"
    caption.font.size = Pt(9)
    caption.font.italic = True
    caption.font.color.rgb = RGBColor.from_string(DARK_GREY)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = header.add_run("STRUCTURAL ANALYSIS AND DESIGN REPORT")
    run.font.name = "Aptos"
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor.from_string("6B7280")

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run("Confidential engineering document  |  ")
    run.font.name = "Aptos"
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor.from_string("6B7280")
    add_page_number(footer)


def add_cover(doc: Document, title: str, project: str, author: str, data: dict[str, Any]) -> None:
    for _ in range(3):
        doc.add_paragraph()
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(title)
    run.bold = True
    run.font.name = "Aptos Display"
    run.font.size = Pt(27)
    run.font.color.rgb = RGBColor.from_string(NAVY)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(project)
    run.font.name = "Aptos"
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor.from_string(BLUE)

    doc.add_paragraph()
    cover_rows = [
        ("Document type", "Professional structural analysis and design report"),
        ("Project", project),
        ("Model file", data.get("extraction", {}).get("model_filename")),
        ("Revision", "R0"),
        ("Prepared by", author),
        ("Report date", datetime.now().strftime("%d %B %Y")),
    ]
    add_kv_table(doc, cover_rows)
    doc.add_paragraph()
    add_note(doc, "This report is generated from extracted ETABS data. Results, assumptions, code interpretations, and scope limitations require review by the responsible structural engineer before issue or construction use.", YELLOW)
    doc.add_page_break()


def build_report(data: dict[str, Any], title: str, project: str, author: str) -> Document:
    doc = Document()
    setup_document(doc)
    add_cover(doc, title, project, author, data)

    add_heading(doc, "Table of Contents", level=1)
    add_toc(doc)
    doc.add_page_break()

    add_heading(doc, "List of Tables and Figures", level=1)
    add_body(doc, "Tables and figures are inserted with chapter-based headings and captions as the report is expanded. Detailed extracted data remains available in report_data.json and the source CSV package.")
    doc.add_page_break()

    extraction = data.get("extraction", {})
    validation = data.get("validation", {})
    geometry = data.get("geometry", {})
    inputs = data.get("inputs", {})
    analysis = data.get("analysis", {})
    design = data.get("design", {})

    # Executive Summary
    add_heading(doc, "Executive Summary", level=1)
    status = validation.get("overall_status", "Not available")
    add_body(doc, f"This report presents the extracted structural-analysis and concrete-design information for {project}. The current validation status is {status}.")
    modal = analysis.get("modal", {})
    mass = analysis.get("modal_mass_participation", {})
    drifts = analysis.get("storey_drifts", {})
    col = design.get("columns", {})
    beam = design.get("beams", {})
    add_kv_table(doc, [
        ("Validation status", status),
        ("Fundamental period T1", f"{fmt(modal.get('fundamental_period_s'))} s"),
        ("90% modal mass in X", f"Mode {safe(mass.get('SumUX_90_percent_mode'))}"),
        ("90% modal mass in Y", f"Mode {safe(mass.get('SumUY_90_percent_mode'))}"),
        ("Maximum extracted storey drift", fmt(drifts.get("maximum_absolute_drift"))),
        ("Maximum column reinforcement ratio", fmt(col.get("maximum_RatioRebar"))),
        ("Column rows over ratio 1.0", col.get("rows_over_1_0", "Not available")),
        ("Maximum beam top reinforcement area", fmt(beam.get("maximum_AsTop"))),
    ], "Executive Summary Indicators")
    add_note(doc, "The extracted data package indicates equivalent-static seismic cases EQX-ULS and EQY-ULS. No response-spectrum table or RSX/RSY result was available in the source model. This is reported as a data limitation, not treated as a failed design check.", YELLOW)

    # Chapter 1
    add_heading(doc, "1. Introduction and Scope", level=1)
    add_heading(doc, "1.1 General", level=2)
    add_body(doc, f"This document compiles structural-model inputs, analysis results, and concrete-member design outputs extracted from the ETABS model associated with {project}.")
    add_heading(doc, "1.2 Purpose of the Report", level=2)
    add_body(doc, "The purpose is to provide a traceable engineering record of the extracted model, loading definitions, global response, member actions, and available design results.")
    add_heading(doc, "1.3 Scope of Work", level=2)
    add_body(doc, "The automated scope includes ETABS table extraction, data validation, summary calculations, and report compilation. Professional engineering review remains required before issue.")
    add_heading(doc, "1.4 Structural System Overview", level=2)
    add_kv_table(doc, [("Stories extracted", geometry.get("stories", {}).get("rows")), ("Beam rows", geometry.get("beams", {}).get("rows")), ("Column rows", geometry.get("columns", {}).get("rows")), ("Area rows", geometry.get("areas", {}).get("rows"))])
    add_heading(doc, "1.5 Applicable Codes and Standards", level=2)
    add_body(doc, "The extracted model includes concrete design tables identified by ETABS as IS 456-2000. Project-specific NBC provisions, including NBC 100, NBC 102, NBC 103, and NBC 105 where applicable, must be confirmed against the design brief and responsible-engineer criteria.")
    add_heading(doc, "1.6 Limitations and Responsibilities", level=2)
    add_note(doc, "This automated report does not independently reanalyse the structure, verify every load path, or certify code compliance. Missing sections are identified explicitly and must be completed or accepted by the responsible engineer.", YELLOW)

    # Chapter 2
    add_heading(doc, "2. Basis of Design and Material Properties", level=1)
    add_heading(doc, "2.1 Model and Units", level=2)
    add_kv_table(doc, [("Source model", extraction.get("model_filename")), ("Present units enum", extraction.get("present_units_enum")), ("Analysis rerun during extraction", extraction.get("analysis_ran")), ("Concrete design rerun during extraction", extraction.get("concrete_design_ran"))])
    add_heading(doc, "2.2 Materials", level=2)
    add_appendix_table(doc, "Material Property Inventory", inputs.get("materials", {}), 20)
    add_heading(doc, "2.3 Frame and Area Section Properties", level=2)
    add_appendix_table(doc, "Frame Section Inventory", inputs.get("frame_sections", {}), 25)
    add_appendix_table(doc, "Area Section Inventory", inputs.get("area_sections", {}), 25)
    add_heading(doc, "2.4 Soil and Foundation Parameters", level=2)
    add_body(doc, "No independent geotechnical report or footing-design calculation is contained in the extracted CSV package. Soil parameters and foundation design criteria should be inserted from the approved geotechnical information before issue.")

    # Chapter 3
    add_heading(doc, "3. Structural Geometry and Modelling", level=1)
    add_heading(doc, "3.1 Grid, Storeys, and Coordinates", level=2)
    add_kv_table(doc, [("Story definitions", geometry.get("stories", {}).get("rows")), ("Grid lines", geometry.get("grid_lines", {}).get("rows")), ("Joint coordinates", geometry.get("joints", {}).get("rows")), ("Diaphragm assignments", geometry.get("diaphragm_assignments", {}).get("rows")), ("Joint restraints", geometry.get("restraints", {}).get("rows"))])
    add_appendix_table(doc, "Storey Definitions", inputs.get("story_definitions", {}), 20)
    add_heading(doc, "3.2 Structural Object Connectivity", level=2)
    add_body(doc, "The extracted object-connectivity tables provide the source identifiers used to trace beams, columns, areas, floors, and joints through the ETABS model.")
    add_heading(doc, "3.3 Model Verification Inputs", level=2)
    add_body(doc, "Model verification should include connectivity, section assignment, diaphragm assignment, support restraint, mass-source, and load-path review. The validation status and table inventory in this report identify the automated checks performed.")

    # Chapter 4
    add_heading(doc, "4. Loading and Load Combinations", level=1)
    add_heading(doc, "4.1 Load Patterns", level=2)
    add_appendix_table(doc, "Load Pattern Definitions", inputs.get("load_patterns", {}), 25)
    add_heading(doc, "4.2 Load Cases", level=2)
    add_appendix_table(doc, "Load Case Definitions", inputs.get("load_cases", {}), 25)
    add_heading(doc, "4.3 Load Combinations", level=2)
    add_appendix_table(doc, "Load Combination Definitions", inputs.get("load_combinations", {}), 40)
    add_heading(doc, "4.4 Mass Source", level=2)
    add_appendix_table(doc, "Mass Source Definition", inputs.get("mass_sources", {}), 20)
    add_heading(doc, "4.5 Seismic Analysis Data", level=2)
    add_body(doc, "The extracted case inventory contains EQX-ULS and EQY-ULS. No response-spectrum function table or RSX/RSY result was available in the source ETABS table catalog.")
    add_note(doc, "Response-spectrum analysis is not documented as performed by this automated report unless the source model is updated with identifiable response-spectrum cases and functions.", YELLOW)

    # Chapter 5
    add_heading(doc, "5. Analysis Methodology and Design Procedures", level=1)
    add_heading(doc, "5.1 Automated Extraction Procedure", level=2)
    add_body(doc, "The source ETABS model was queried through the ETABS database-table interface. Extracted tables were written to CSV and Excel, then validated independently by validate_extraction.py before this Word report was compiled.")
    add_heading(doc, "5.2 Modal and Seismic Procedure", level=2)
    add_body(doc, "The available modal results contain 12 modes. Equivalent-static seismic result cases EQX-ULS and EQY-ULS were identified in the extracted package. Response-spectrum results were not available.")
    add_heading(doc, "5.3 Concrete Design Procedure", level=2)
    add_body(doc, "The concrete design outputs were identified by ETABS as IS 456-2000 design tables. The report reproduces extracted design summaries and reinforcement-demand values; it does not replace review of ETABS design settings, overwrites, detailing rules, or governing code clauses.")

    # Chapter 6
    add_heading(doc, "6. Global Analysis Results", level=1)
    add_heading(doc, "6.1 Modal Analysis", level=2)
    add_kv_table(doc, [("Number of modes", modal.get("number_of_modes")), ("Fundamental period T1", f"{fmt(modal.get('fundamental_period_s'))} s"), ("90% cumulative SumUX", f"Mode {safe(mass.get('SumUX_90_percent_mode'))}"), ("90% cumulative SumUY", f"Mode {safe(mass.get('SumUY_90_percent_mode'))}"), ("Final SumUX", mass.get("SumUX_final")), ("Final SumUY", mass.get("SumUY_final"))])
    add_records_table(doc, "Modal Periods", modal.get("periods", []), ["Case", "Mode", "Period", "Frequency"], 20)
    add_heading(doc, "6.2 Storey Drift", level=2)
    add_kv_table(doc, [("Maximum absolute drift", drifts.get("maximum_absolute_drift")), ("Governing row", drifts.get("governing_row"))])
    add_records_table(doc, "Storey Drift by Direction", drifts.get("by_direction", []), ["Direction", "Drift"], 20)
    add_heading(doc, "6.3 Storey Forces and Base Reactions", level=2)
    forces = analysis.get("storey_forces", {})
    reactions = analysis.get("base_reactions", {})
    add_kv_table(doc, [("Maximum absolute storey VX", forces.get("maximum_VX")), ("Maximum absolute storey VY", forces.get("maximum_VY")), ("Maximum absolute base FX", reactions.get("maximum_abs_FX")), ("Maximum absolute base FY", reactions.get("maximum_abs_FY")), ("Maximum absolute base FZ", reactions.get("maximum_abs_FZ"))])
    add_heading(doc, "6.4 Centre of Mass and Rigidity", level=2)
    add_records_table(doc, "Centre of Mass and Rigidity", analysis.get("centers_of_mass_and_rigidity", []), ["Story", "Diaphragm", "XCM", "YCM", "XCR", "YCR"], 20)
    add_heading(doc, "6.5 Torsion and Stability", level=2)
    add_body(doc, "The torsional displacement table was intentionally excluded from the extraction scope. Torsional response should therefore be reviewed from the appropriate ETABS diaphragm or drift outputs before final issue.")

    # Chapter 7
    add_heading(doc, "7. Member Forces and Structural Response", level=1)
    add_heading(doc, "7.1 Beam and Column Response", level=2)
    add_body(doc, "Detailed member-force diagrams and envelopes remain in the extracted ETABS result package. The current report presents governing design summaries and retains the source table identifiers for traceability.")
    add_heading(doc, "7.2 Foundation Reactions", level=2)
    add_body(doc, "Joint reactions were extracted for the configured gravity, envelope, and seismic combinations. Detailed footing design is outside the automated report scope unless separately provided.")

    # Chapter 8
    add_heading(doc, "8. Structural Member Design and Code Checks", level=1)
    add_heading(doc, "8.1 Beam Design", level=2)
    add_kv_table(doc, [("Extracted beam rows", beam.get("members_or_rows")), ("Maximum AsTop", beam.get("maximum_AsTop")), ("Maximum AsBot", beam.get("maximum_AsBot")), ("Rows with missing reinforcement", beam.get("rows_with_missing_rebar"))])
    add_records_table(doc, "Governing Beam Top Reinforcement", [beam.get("governing_AsTop_row")] if beam.get("governing_AsTop_row") else [], None, 1)
    add_records_table(doc, "Governing Beam Bottom Reinforcement", [beam.get("governing_AsBot_row")] if beam.get("governing_AsBot_row") else [], None, 1)
    add_heading(doc, "8.2 Column Design", level=2)
    add_kv_table(doc, [("Extracted column rows", col.get("members_or_rows")), ("Maximum RatioRebar", col.get("maximum_RatioRebar")), ("Rows with RatioRebar > 1.0", col.get("rows_over_1_0")), ("Rows with RatioRebar > 0.9", col.get("rows_over_0_9"))])
    add_records_table(doc, "Governing Column Design Row", [col.get("governing_row")] if col.get("governing_row") else [], None, 1)
    add_heading(doc, "8.3 Shear Design", level=2)
    add_kv_table(doc, [("Maximum column VMajor", design.get("column_shear", {}).get("maximum_VMajor")), ("Maximum column VMinor", design.get("column_shear", {}).get("maximum_VMinor")), ("Maximum beam shear", design.get("beam_shear", {}).get("maximum_Shear"))])
    add_heading(doc, "8.4 Slab, Wall, Staircase, and Foundation Design", level=2)
    add_body(doc, "No complete slab-design, wall-design, staircase-design, or footing-design result set was present in report_data.json. These items are therefore not certified by this report and require separate design output or explicit scope confirmation.")
    add_note(doc, "Foundation design is outside the current automated scope. Support and joint reactions are reported for subsequent foundation design.", YELLOW)

    # Chapter 9
    add_heading(doc, "9. Reinforcement and Detailing", level=1)
    add_heading(doc, "9.1 Beam Reinforcement", level=2)
    add_body(doc, "Beam longitudinal reinforcement demands are summarized from the Concrete Beam Flexure Envelope - IS 456-2000 table. Detailed bar arrangement, anchorage, curtailment, laps, and ductile detailing must be reviewed separately.")
    add_heading(doc, "9.2 Column Reinforcement", level=2)
    add_body(doc, "Column reinforcement demand is summarized from the Concrete Column PMM Envelope - IS 456-2000 table. Confinement, lap-splice, joint, and seismic detailing require independent review.")
    add_heading(doc, "9.3 Reinforcement by Grid and Storey", level=2)
    add_body(doc, "The current extracted design tables are organized by story, label, and design section. Grid-based reinforcement schedules can be added when the required grid/member mapping is defined in the project data model.")

    # Chapter 10
    add_heading(doc, "10. Design Summary", level=1)
    add_status_table(doc, validation)
    add_kv_table(doc, [("Beam design data", "Available" if "beams" in design else "Not available"), ("Column design data", "Available" if "columns" in design else "Not available"), ("Storey drift data", "Available" if "storey_drifts" in analysis else "Not available"), ("Joint reactions", "Available" if "11_Joint_Reactions" in validation.get("tables", {}) and validation["tables"]["11_Joint_Reactions"].get("status") == "ok" else "Not available"), ("Response-spectrum data", "Not available"), ("Footing design", "Outside current scope")])

    # Chapter 11
    add_heading(doc, "11. Conclusions and Recommendations", level=1)
    add_heading(doc, "11.1 Conclusions", level=2)
    add_body(doc, f"The extracted ETABS package for {project} contains the principal model, loading, modal, global-response, joint-reaction, beam-design, and column-design tables required for a structured review. The automated validation result is {status}.")
    add_heading(doc, "11.2 Recommendations", level=2)
    recommendations = [
        "Confirm the applicable NBC design criteria and project-specific acceptance limits.",
        "Review the equivalent-static seismic cases and confirm whether response-spectrum analysis is required.",
        "Review the governing beam and column design rows in ETABS, including design preferences and overwrites.",
        "Complete or attach slab, wall, staircase, and foundation design calculations where applicable.",
        "Review accidental torsion and diaphragm response using the appropriate ETABS output tables.",
        "Perform an independent engineering review before issuing the report for construction or approval.",
    ]
    for item in recommendations:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.add_run(item)

    # Appendices
    add_heading(doc, "Appendices", level=1)
    appendix_map = [
        ("Appendix A — Extraction and Validation Manifest", "validation"),
        ("Appendix B — Model Geometry Inventory", "geometry"),
        ("Appendix C — Materials, Sections, and Loading Inputs", "inputs"),
        ("Appendix D — Modal and Global Analysis Summary", "analysis"),
        ("Appendix E — Member Design Summary", "design"),
    ]
    for heading, key in appendix_map:
        add_heading(doc, heading, level=2)
        section_data = data.get(key, {})
        if key == "validation":
            add_status_table(doc, section_data)
        elif key == "geometry":
            add_kv_table(doc, [(name, value.get("rows")) for name, value in section_data.items() if isinstance(value, dict) and "rows" in value])
            if section_data.get("story_table"):
                add_records_table(doc, "Story Table", section_data["story_table"], None, 20)
        elif key == "inputs":
            for name, value in section_data.items():
                if isinstance(value, dict):
                    add_appendix_table(doc, name.replace("_", " ").title(), value, 40)
        elif key in {"analysis", "design"}:
            add_body(doc, json.dumps(section_data, indent=2, ensure_ascii=False))

    return doc


def main() -> int:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Input report_data.json does not exist: {args.input}")
    data = json.loads(args.input.read_text(encoding="utf-8"))
    project = args.project or Path(str(data.get("extraction", {}).get("model_filename") or "Structural Project")).stem
    args.output.parent.mkdir(parents=True, exist_ok=True)
    document = build_report(data, args.title, project, args.author)
    document.save(args.output)
    print(f"Saved: {args.output.resolve()}")
    print("Open the DOCX in Word and update the Table of Contents field with Ctrl+A, F9.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
