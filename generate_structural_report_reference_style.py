"""
generate_structural_report_reference_style.py

Generate an editable Word structural-analysis report in the visual style of the
provided Puspa.docx reference report.

The generator:
  * loads the reference DOCX as a template so its fonts, colors, numbering,
    margins, and existing Word styles are retained;
  * removes old project content while retaining the template's style definitions;
  * compiles validation/report_data.json into the reference-style structure;
  * inserts real ETABS screenshots from --screenshots when supplied; and
  * generates equivalent plan, elevation, drift, modal, reaction, and design
    figures from extracted CSV files when screenshots are unavailable.

Usage:
  pip install python-docx pandas matplotlib

  python generate_structural_report_reference_style.py \
      --template Puspa.docx \
      --data validation/report_data.json \
      --tables tables \
      --screenshots screenshots \
      --output report/structural_analysis_report.docx

Screenshot naming convention (optional):
  01_key_frame.png
  02_grid_plan.png
  03_sectional_view.png
  04_mode_1.png
  05_mode_2.png
  06_drift_x.png
  07_drift_y.png
  08_moment.png
  09_axial.png
  10_beam_design.png
  11_column_design.png
  12_reinforcement.png

The script uses a screenshot when the matching file exists; otherwise it uses a
Python-generated figure with the same report role.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


BLUE = "1F4E79"
DARK_BLUE = "17365D"
LIGHT_BLUE = "D9EAF7"
LIGHT_GREY = "F2F2F2"
YELLOW = "FFF2CC"


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=Path("validation/report_data.json"))
    parser.add_argument("--tables", type=Path, default=Path("tables"))
    parser.add_argument("--screenshots", type=Path, default=Path("screenshots"))
    parser.add_argument("--figures", type=Path, default=Path("figures"))
    parser.add_argument("--output", type=Path, default=Path("report/structural_analysis_report.docx"))
    parser.add_argument("--project", default=None)
    parser.add_argument("--owner", default="Project Owner")
    parser.add_argument("--consultant", default="SWARUP ENGINEERING CONSULTANCY")
    parser.add_argument("--engineer", default="Responsible Structural Engineer")
    return parser.parse_args()


def safe(value: Any, default: str = "Not available") -> str:
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def number(value: Any, digits: int = 3) -> str:
    try:
        x = float(value)
        if not math.isfinite(x):
            return "Not available"
        return f"{x:.{digits}f}"
    except (TypeError, ValueError):
        return safe(value)


def load_csv(tables: Path, name: str) -> pd.DataFrame | None:
    path = tables / f"{name}.csv"
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def clear_template_body(doc: Document) -> None:
    body = doc._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(0.69)
        section.left_margin = Inches(1.25)
        section.right_margin = Inches(0.58)


def clear_paragraph(paragraph) -> None:
    """Remove inherited template runs/fields before writing new header/footer text."""
    p = paragraph._p
    for child in list(p):
        p.remove(child)


def configure_reference_styles(doc: Document) -> None:
    # These match the styles measured from Puspa.docx. Existing style definitions
    # remain available because the reference document is used as the template.
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(12)
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.line_spacing = 1.08

    if "Heading 1" in doc.styles:
        s = doc.styles["Heading 1"]
        s.font.name = "Arial"
        s.font.size = Pt(16)
        s.font.bold = True
        s.font.color.rgb = RGBColor.from_string("000000")
    if "Heading 2" in doc.styles:
        s = doc.styles["Heading 2"]
        s.font.name = "Arial"
        s.font.size = Pt(14)
        s.font.bold = True
        s.font.italic = True
        s.font.color.rgb = RGBColor.from_string("000000")
    if "Heading 3" in doc.styles:
        s = doc.styles["Heading 3"]
        s.font.name = "Arial"
        s.font.size = Pt(13)
        s.font.bold = True
        s.font.color.rgb = RGBColor.from_string("000000")


def add_field(paragraph, instruction: str) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    text = OxmlElement("w:instrText")
    text.set(qn("xml:space"), "preserve")
    text.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, text, separate, end])


def add_page_number(paragraph) -> None:
    paragraph.add_run("Page ")
    add_field(paragraph, "PAGE")


def add_heading(doc: Document, text: str, level: int = 1):
    p = doc.add_paragraph(text, style=f"Heading {level}")
    p.paragraph_format.keep_with_next = True
    return p


def add_body(doc: Document, text: str, style: str = "Normal") -> None:
    p = doc.add_paragraph(text, style=style)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.08


def add_centered(doc: Document, text: str, size: int = 14, bold: bool = False, color: str = "000000") -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.font.name = "Arial"
    r.font.size = Pt(size)
    r.bold = bold
    r.font.color.rgb = RGBColor.from_string(color)


def add_part_page(doc: Document, part: str, title: str) -> None:
    doc.add_page_break()
    add_centered(doc, part, 16, True, DARK_BLUE)
    doc.add_paragraph()
    add_centered(doc, title.upper(), 18, True, BLUE)
    doc.add_page_break()


def add_note(doc: Document, text: str, fill: str = LIGHT_BLUE) -> None:
    # The reference uses plain narrative paragraphs rather than shaded callout
    # boxes. Keep notices visible without introducing a new visual language.
    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.left_indent = Inches(0.15)
    r = p.add_run("Note: ")
    r.bold = True
    r.italic = True
    r.font.name = "Arial"
    r.font.size = Pt(10)
    r2 = p.add_run(text)
    r2.italic = True
    r2.font.name = "Arial"
    r2.font.size = Pt(10)


def add_kv(doc: Document, rows: list[tuple[str, Any]]) -> None:
    # The reference document primarily uses aligned label/value paragraphs rather
    # than heavy colored tables, so this helper deliberately uses plain text.
    for label, value in rows:
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.left_indent = Inches(0.15)
        r = p.add_run(f"{label:<38}: ")
        r.bold = True
        p.add_run(safe(value))


def add_data_table(doc: Document, title: str, records: list[dict[str, Any]], columns: list[str] | None = None, limit: int = 25) -> None:
    add_heading(doc, title, 3)
    if not records:
        add_note(doc, "No extracted data is available for this section.", YELLOW)
        return
    records = records[:limit]
    if columns is None:
        columns = list(records[0].keys())
    columns = [c for c in columns if any(c in row for row in records)]
    table = doc.add_table(rows=1, cols=len(columns))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, col in enumerate(columns):
        cell = table.rows[0].cells[i]
        cell.text = col
        for run in cell.paragraphs[0].runs:
            run.bold = True
            run.font.name = "Arial"
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor.from_string("000000")
    for n, row in enumerate(records):
        cells = table.add_row().cells
        for i, col in enumerate(columns):
            cells[i].text = safe(row.get(col), "")
            for run in cells[i].paragraphs[0].runs:
                run.font.name = "Arial"
                run.font.size = Pt(8.5)
    if len(records) == limit:
        add_body(doc, f"Showing the first {limit} rows; complete extracted data is retained in the CSV package.")


def add_image_or_note(doc: Document, image: Path | None, caption: str, note: str) -> None:
    if image and image.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(str(image), width=Inches(6.1))
        cap = doc.add_paragraph(caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.style = "Caption" if "Caption" in [s.name for s in doc.styles] else "Normal"
    else:
        add_note(doc, note, YELLOW)


def figure_path(screenshots: Path, figures: Path, key: str) -> Path | None:
    for suffix in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
        candidate = screenshots / f"{key}{suffix}"
        if candidate.exists():
            return candidate
        candidate = figures / f"{key}{suffix}"
        if candidate.exists():
            return candidate
    return None


def save_plot(figures: Path, name: str) -> Path:
    figures.mkdir(parents=True, exist_ok=True)
    path = figures / f"{name}.png"
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def generate_figures(tables: Path, figures: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    if not MATPLOTLIB_AVAILABLE:
        return result
    plt.rcParams.update({"font.family": "Arial", "font.size": 9})

    joints = load_csv(tables, "14_Joint_Coordinates")
    if joints is not None and {"GlobalX", "GlobalY", "GlobalZ"}.issubset(joints.columns):
        fig = plt.figure(figsize=(8, 5.5))
        ax = fig.add_subplot(111, projection="3d")
        ax.scatter(joints["GlobalX"], joints["GlobalY"], joints["GlobalZ"], s=7, c="#1F4E79")
        ax.set_title("ETABS Joint and Structural Model Geometry")
        ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
        result["key_frame"] = save_plot(figures, "01_key_frame")

        fig, ax = plt.subplots(figsize=(7.5, 5))
        ax.scatter(joints["GlobalX"], joints["GlobalY"], s=8, c="#1F4E79")
        ax.set_title("Beam and Column Grid Plan – Extracted Joint Layout")
        ax.set_xlabel("Global X"); ax.set_ylabel("Global Y"); ax.axis("equal"); ax.grid(alpha=.25)
        result["grid_plan"] = save_plot(figures, "02_grid_plan")

        fig, ax = plt.subplots(figsize=(7.5, 5))
        ax.scatter(joints["GlobalX"], joints["GlobalZ"], s=8, c="#1F4E79")
        ax.set_title("Beam and Column Sectional View – Extracted Joint Elevation")
        ax.set_xlabel("Global X"); ax.set_ylabel("Global Z"); ax.grid(alpha=.25)
        result["sectional_view"] = save_plot(figures, "03_sectional_view")

    periods = load_csv(tables, "01_Modal_Periods")
    if periods is not None and {"Mode", "Period"}.issubset(periods.columns):
        p = periods.copy().sort_values("Mode")
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        ax.bar(p["Mode"].astype(str), pd.to_numeric(p["Period"], errors="coerce"), color="#5B9BD5")
        ax.set_title("Modal Periods")
        ax.set_xlabel("Mode"); ax.set_ylabel("Period (s)"); ax.grid(axis="y", alpha=.25)
        result["mode_1"] = save_plot(figures, "04_mode_1")

    drifts = load_csv(tables, "04_Story_Drifts")
    if drifts is not None and {"Story", "Drift", "Direction"}.issubset(drifts.columns):
        for direction, key, title in (("X", "drift_x", "Storey Drift in X Direction"), ("Y", "drift_y", "Storey Drift in Y Direction")):
            subset = drifts[drifts["Direction"].astype(str).str.upper().str.contains(direction)]
            if subset.empty:
                continue
            subset = subset.copy()
            subset["Drift"] = pd.to_numeric(subset["Drift"], errors="coerce")
            fig, ax = plt.subplots(figsize=(7.5, 4.5))
            ax.bar(subset["Story"].astype(str), subset["Drift"], color="#70AD47")
            ax.set_title(title); ax.set_xlabel("Story"); ax.set_ylabel("Drift")
            ax.tick_params(axis="x", rotation=45); ax.grid(axis="y", alpha=.25)
            result[key] = save_plot(figures, f"06_{key}")

    reactions = load_csv(tables, "03_Base_Reactions")
    if reactions is not None and {"OutputCase", "FX", "FY"}.issubset(reactions.columns):
        r = reactions.copy().head(20)
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        x = range(len(r)); width = .38
        ax.bar([i - width/2 for i in x], pd.to_numeric(r["FX"], errors="coerce"), width, label="FX", color="#5B9BD5")
        ax.bar([i + width/2 for i in x], pd.to_numeric(r["FY"], errors="coerce"), width, label="FY", color="#ED7D31")
        ax.set_title("Base Reaction Summary"); ax.set_ylabel("Reaction")
        ax.set_xticks(list(x)); ax.set_xticklabels(r["OutputCase"].astype(str), rotation=45, ha="right")
        ax.legend(); ax.grid(axis="y", alpha=.25)
        result["joint_reaction"] = save_plot(figures, "07_joint_reaction")

    beam = load_csv(tables, "08_Beam_Design")
    if beam is not None and {"AsTop", "AsBot"}.issubset(beam.columns):
        b = beam.copy().head(30)
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        ax.plot(pd.to_numeric(b["AsTop"], errors="coerce").values, label="AsTop", color="#1F4E79")
        ax.plot(pd.to_numeric(b["AsBot"], errors="coerce").values, label="AsBot", color="#C55A11")
        ax.set_title("Beam Reinforcement Demand"); ax.set_xlabel("Extracted beam row"); ax.set_ylabel("Area of steel")
        ax.legend(); ax.grid(alpha=.25)
        result["beam_design"] = save_plot(figures, "10_beam_design")

    column = load_csv(tables, "07_Column_Design")
    if column is not None and "RatioRebar" in column.columns:
        c = column.copy().head(40)
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        ax.bar(range(len(c)), pd.to_numeric(c["RatioRebar"], errors="coerce"), color="#A5A5A5")
        ax.axhline(1.0, color="#C00000", linestyle="--", linewidth=1)
        ax.set_title("Column Reinforcement Ratio Demand"); ax.set_xlabel("Extracted column row"); ax.set_ylabel("RatioRebar")
        ax.grid(axis="y", alpha=.25)
        result["column_design"] = save_plot(figures, "11_column_design")

    return result


def insert_cover(doc: Document, project: str, owner: str, consultant: str, data: dict[str, Any]) -> None:
    for _ in range(4):
        doc.add_paragraph()
    # Match the reference cover: restrained black Arial text, centered, with
    # the same wording rhythm rather than a modern title-card treatment.
    add_centered(doc, "STRUCTURAL MODELING, ANALYSIS", 16, True, "000000")
    add_centered(doc, "&", 16, True, "000000")
    add_centered(doc, "DESIGN REPORT", 16, True, "000000")
    add_centered(doc, "OF", 12, False, "000000")
    add_centered(doc, project.title(), 15, True, "000000")
    add_centered(doc, owner.title(), 14, True, "000000")
    for _ in range(3):
        doc.add_paragraph()
    add_centered(doc, "SUBMITTED BY:", 12, True)
    add_centered(doc, consultant, 12, True, "000000")
    add_centered(doc, "Dharan-12, Sunsari", 11)
    doc.add_page_break()


def insert_declaration(doc: Document, project: str, owner: str, engineer: str) -> None:
    add_centered(doc, "TO WHOM IT MAY CONCERN", 15, True, DARK_BLUE)
    add_body(doc, f"This report comprises the summary of the structural analysis and design of the building for {owner}. The report consists of the design procedures adopted, assumptions made, input data, analysis results, and design output.")
    add_body(doc, "During the design, it is assumed that the client will follow the architectural and structural design and that construction will be supervised by a professional engineer.")
    add_body(doc, "The designer will not be responsible for alterations to the structural system made by the client or contractor without prior written permission from the designer, or for alterations to the non-structural system that materially change the design weight of a floor or the whole building.")
    add_body(doc, "The design calculations and derivations are limited to the information required to communicate the methodology adopted. Detailed calculations and source outputs may be provided to the client or concerned authorities when needed, upon request.")
    for _ in range(5):
        doc.add_paragraph()
    add_centered(doc, "……………………………", 13)
    add_centered(doc, engineer, 12, True)
    if engineer.strip().lower() != "responsible structural engineer":
        add_centered(doc, "Responsible Structural Engineer", 11)
    doc.add_page_break()


def insert_toc(doc: Document) -> None:
    add_centered(doc, "Table of Contents", 15, True, DARK_BLUE)
    p = doc.add_paragraph()
    add_field(p, 'TOC \\o "1-3" \\h \\z \\u')
    add_note(doc, "Update the table of contents in Word by selecting it and pressing F9.")


def build_doc(data: dict[str, Any], template: Path, tables: Path, screenshots: Path, figures: Path, project: str, owner: str, consultant: str, engineer: str) -> Document:
    doc = Document(str(template))
    clear_template_body(doc)
    configure_reference_styles(doc)

    insert_cover(doc, project, owner, consultant, data)
    insert_declaration(doc, project, owner, engineer)
    insert_toc(doc)

    geometry = data.get("geometry", {})
    inputs = data.get("inputs", {})
    analysis = data.get("analysis", {})
    design = data.get("design", {})
    validation = data.get("validation", {})
    extraction = data.get("extraction", {})
    generated = generate_figures(tables, figures)

    # Header/footer are intentionally simple and compatible with the reference.
    for section in doc.sections:
        header = section.header.paragraphs[0]
        header.text = f"Initial Structural Modeling, Analysis & Design Report for {project}"
        header.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in header.runs:
            run.font.name = "Arial"; run.font.size = Pt(9); run.italic = True
        footer = section.footer.paragraphs[0]
        clear_paragraph(footer)
        footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        add_page_number(footer)

    add_part_page(doc, "Part 1", "Introduction")
    add_heading(doc, "1.0 Background", 2)
    add_body(doc, f"This report summarizes the structural analysis and design of the {project}. The analysis and design have been based on the prevailing codes and standards adopted for the project, including the National Building Code of Nepal and relevant IS codes.")
    add_heading(doc, "2.0 Salient Features", 2)
    add_heading(doc, "2.1 Project Information", 3)
    add_kv(doc, [("Owner", owner), ("Building type", "Residential / as defined by project input"), ("Model file", extraction.get("model_filename")), ("Validation status", validation.get("overall_status"))])
    add_heading(doc, "2.2 Building Features", 3)
    add_kv(doc, [("Stories extracted", geometry.get("stories", {}).get("rows")), ("Joint coordinates", geometry.get("joints", {}).get("rows")), ("Story-definition records", geometry.get("story_table") and len(geometry.get("story_table", [])))])
    add_heading(doc, "2.3 Structural Features", 3)
    add_kv(doc, [("Beam connectivity rows", geometry.get("beams", {}).get("rows")), ("Column connectivity rows", geometry.get("columns", {}).get("rows")), ("Floor connectivity rows", geometry.get("floors", {}).get("rows")), ("Diaphragm assignments", geometry.get("diaphragm_assignments", {}).get("rows"))])
    add_heading(doc, "2.4 Site Condition", 3)
    add_body(doc, "Site soil parameters, allowable bearing pressure, and foundation criteria are not independently contained in the extracted report_data.json and must be inserted from the approved geotechnical information.")
    add_heading(doc, "2.5 Material Properties", 3)
    add_data_table(doc, "Material Properties", inputs.get("materials", {}).get("records", []), ["Material", "Type", "Grade", "Notes"], 15)
    add_heading(doc, "2.6 Design Basis", 3)
    add_body(doc, "The extracted concrete design tables are identified by ETABS as IS 456-2000. NBC 100, NBC 102, NBC 103, NBC 105, and other project standards should be confirmed in the final design-basis statement.")

    add_heading(doc, "3.0 Loading", 2)
    add_heading(doc, "3.1 Dead Loads", 3)
    add_data_table(doc, "Load Pattern Definitions", inputs.get("load_patterns", {}).get("records", []), ["Name", "Type", "SelfWtMult", "AutoLoad"], 25)
    add_heading(doc, "3.2 Live Loads", 3)
    add_body(doc, "Live-load values should be confirmed from the project load schedule and architectural use. The extracted load patterns and load-case definitions are reproduced in Appendix C.")
    add_heading(doc, "3.2.1 Load Assessment", 3)
    add_data_table(doc, "Load Case Definitions", inputs.get("load_cases", {}).get("records", []), ["Name", "LoadType", "LoadName", "LoadSF", "MassSource"], 25)
    add_heading(doc, "3.3 Earthquake Loads", 3)
    add_kv(doc, [("Seismic cases configured", data.get("extraction", {}).get("configuration", {}).get("seismic_cases")), ("Fundamental period T1", f"{number(analysis.get('modal', {}).get('fundamental_period_s'))} s"), ("90% modal mass in X", f"Mode {safe(analysis.get('modal_mass_participation', {}).get('SumUX_90_percent_mode'))}"), ("90% modal mass in Y", f"Mode {safe(analysis.get('modal_mass_participation', {}).get('SumUY_90_percent_mode'))}")])
    add_heading(doc, "3.4 Load Cases and Combinations", 3)
    add_data_table(doc, "Load Combination Definitions", inputs.get("load_combinations", {}).get("records", []), ["Name", "Type", "LoadName", "SF"], 40)
    add_heading(doc, "3.5 Analysis and Design", 3)
    add_body(doc, "The analysis data was extracted from the ETABS database tables. The source model contains modal results and equivalent-static seismic cases EQX-ULS and EQY-ULS. No response-spectrum function table or RSX/RSY result was available.")
    add_heading(doc, "3.5.1 Level of Design", 3)
    add_body(doc, "The report is intended to support professional engineering review of the extracted model and design output.")
    add_heading(doc, "3.5.2 Method of Seismic Analysis", 3)
    add_body(doc, "The available extracted cases indicate equivalent-static seismic analysis. This classification must be confirmed against the ETABS load-case definitions and project design brief.")
    add_heading(doc, "3.5.3 Design and Detailing", 3)
    add_body(doc, "Beam and column concrete-design envelopes are available. Slab, wall, staircase, and footing design outputs were not present in the current extracted package.")

    add_heading(doc, "4.0 Key Frame Diagram", 2)
    add_image_or_note(doc, figure_path(screenshots, figures, "01_key_frame") or generated.get("key_frame"), "Figure 4.0: ETABS key frame / extracted structural model geometry", "ETABS key-frame screenshot not supplied and no joint-geometry plot could be generated.")
    add_heading(doc, "5.0 Beam and Column Grid Plan", 2)
    add_image_or_note(doc, figure_path(screenshots, figures, "02_grid_plan") or generated.get("grid_plan"), "Figure 5.0: Beam and column grid plan", "Grid-plan screenshot not supplied and no joint-coordinate plot could be generated.")
    add_heading(doc, "6.0 Beam and Column Sectional View", 2)
    add_image_or_note(doc, figure_path(screenshots, figures, "03_sectional_view") or generated.get("sectional_view"), "Figure 6.0: Beam and column sectional view", "Sectional-view screenshot not supplied and no elevation plot could be generated.")

    add_part_page(doc, "Sample Design Calculations", "Analysis and Design Results")
    add_heading(doc, "1.0 Load Calculation", 2)
    add_body(doc, "The following load-pattern, load-case, and combination tables are extracted from the source ETABS model. Detailed manual load calculations should be appended where required by the approving authority.")
    add_data_table(doc, "Load Patterns", inputs.get("load_patterns", {}).get("records", []), ["Name", "Type", "SelfWtMult", "AutoLoad"], 30)
    add_heading(doc, "2.0 Time Period and Base Shear Calculation", 2)
    add_kv(doc, [("Number of modes", analysis.get("modal", {}).get("number_of_modes")), ("T1", f"{number(analysis.get('modal', {}).get('fundamental_period_s'))} s"), ("Maximum base FX", analysis.get("base_reactions", {}).get("maximum_abs_FX")), ("Maximum base FY", analysis.get("base_reactions", {}).get("maximum_abs_FY")), ("Maximum base FZ", analysis.get("base_reactions", {}).get("maximum_abs_FZ"))])
    add_image_or_note(doc, figure_path(screenshots, figures, "04_mode_1") or generated.get("mode_1"), "Figure 2.0: Modal period summary", "Modal-period screenshot not supplied and no modal-period plot could be generated.")
    add_heading(doc, "3.0 Joint Reaction", 2)
    add_image_or_note(doc, figure_path(screenshots, figures, "07_joint_reaction") or generated.get("joint_reaction"), "Figure 3.0: Joint/base reaction summary", "Joint-reaction screenshot not supplied and no reaction plot could be generated.")
    add_data_table(doc, "Joint Reaction Records", load_csv(tables, "11_Joint_Reactions").fillna("").to_dict("records") if load_csv(tables, "11_Joint_Reactions") is not None else [], ["Story", "Label", "OutputCase", "FX", "FY", "FZ", "MX", "MY", "MZ"], 35)
    add_heading(doc, "4.0 Moment Diagram", 2)
    add_image_or_note(doc, figure_path(screenshots, figures, "08_moment") or figure_path(screenshots, figures, "08_moment_diagram"), "Figure 4.0: ETABS moment diagram", "Provide an ETABS moment-diagram screenshot in the screenshots folder to populate this page.")
    add_heading(doc, "5.0 Axial Force Diagram", 2)
    add_image_or_note(doc, figure_path(screenshots, figures, "09_axial") or figure_path(screenshots, figures, "09_axial_force"), "Figure 5.0: ETABS axial-force diagram", "Provide an ETABS axial-force screenshot in the screenshots folder to populate this page.")
    add_heading(doc, "6.0 Design of Member", 2)
    add_heading(doc, "6.1 Design of Beam and Column", 3)
    add_kv(doc, [("Maximum beam AsTop", design.get("beams", {}).get("maximum_AsTop")), ("Maximum beam AsBot", design.get("beams", {}).get("maximum_AsBot")), ("Maximum column RatioRebar", design.get("columns", {}).get("maximum_RatioRebar")), ("Column rows over RatioRebar 1.0", design.get("columns", {}).get("rows_over_1_0"))])
    add_image_or_note(doc, figure_path(screenshots, figures, "10_beam_design") or generated.get("beam_design"), "Figure 6.1: Beam reinforcement/design summary", "Beam-design screenshot not supplied and no beam-design plot could be generated.")
    add_image_or_note(doc, figure_path(screenshots, figures, "11_column_design") or generated.get("column_design"), "Figure 6.1: Column reinforcement/design summary", "Column-design screenshot not supplied and no column-design plot could be generated.")
    add_heading(doc, "6.2 Design of Floor Slab", 3)
    add_body(doc, "No slab-design result table was included in the extracted package. Insert the approved slab design calculation or ETABS slab-design output here before issue.")
    add_heading(doc, "6.3 Design of Footing", 3)
    add_body(doc, "Detailed footing design is outside the current automated scope. Joint reactions are provided for subsequent foundation design.")
    add_heading(doc, "6.4 Design of Staircase", 3)
    add_body(doc, "No separate staircase-design output was included in the extracted package.")
    add_heading(doc, "6.5 ETABS Concrete Frame Design — Column Section", 3)
    add_data_table(doc, "Column Design Summary", load_csv(tables, "07_Column_Design").fillna("").to_dict("records") if load_csv(tables, "07_Column_Design") is not None else [], ["Story", "Label", "DesignSect", "P", "MMajor", "MMinor", "PMMCombo", "RatioRebar"], 40)
    add_heading(doc, "6.6 ETABS Concrete Frame Design — Beam Section", 3)
    add_data_table(doc, "Beam Design Summary", load_csv(tables, "08_Beam_Design").fillna("").to_dict("records") if load_csv(tables, "08_Beam_Design") is not None else [], ["Story", "Label", "DesignSect", "Location", "MomentTop", "AsTop", "MomentBot", "AsBot"], 45)
    add_heading(doc, "7.0 Reinforcement Details", 2)
    add_image_or_note(doc, figure_path(screenshots, figures, "12_reinforcement"), "Figure 7.0: Reinforcement details", "Provide reinforcement-detail screenshots or drawings in the screenshots folder to populate this page.")
    add_body(doc, "Reinforcement areas in the extracted ETABS design envelopes are not a substitute for final bar detailing, anchorage, lap, confinement, and constructability drawings.")

    add_part_page(doc, "Appendices", "Extracted Data and Validation")
    add_heading(doc, "A.0 Validation Summary", 2)
    add_kv(doc, [("Overall validation", validation.get("overall_status")), ("Tables inspected", len(validation.get("tables", {}))), ("Read errors", len(validation.get("read_errors", {}))), ("Response-spectrum table", validation.get("tables", {}).get("27_Response_Spectrum", {}).get("status", "Not assessed"))])
    add_heading(doc, "B.0 Model Geometry Inventory", 2)
    add_kv(doc, [(k.replace("_", " ").title(), v.get("rows")) for k, v in geometry.items() if isinstance(v, dict) and "rows" in v])
    add_heading(doc, "C.0 Materials, Sections, and Loads", 2)
    for key in ("materials", "frame_sections", "area_sections", "load_patterns", "load_cases", "load_combinations", "mass_sources"):
        section = inputs.get(key, {})
        add_data_table(doc, key.replace("_", " ").title(), section.get("records", []), None, 35)
    add_heading(doc, "D.0 Modal, Drift, and Global Analysis Data", 2)
    add_body(doc, json.dumps(analysis, indent=2, ensure_ascii=False))
    add_heading(doc, "E.0 Member Design Data", 2)
    add_body(doc, json.dumps(design, indent=2, ensure_ascii=False))

    return doc


def main() -> int:
    cfg = args()
    if not cfg.template.exists():
        raise SystemExit(f"Template does not exist: {cfg.template}")
    if not cfg.data.exists():
        raise SystemExit(f"report_data.json does not exist: {cfg.data}")
    data = json.loads(cfg.data.read_text(encoding="utf-8"))
    project = cfg.project or Path(str(data.get("extraction", {}).get("model_filename") or "Residential Building")).stem
    cfg.figures.mkdir(parents=True, exist_ok=True)
    cfg.output.parent.mkdir(parents=True, exist_ok=True)
    document = build_doc(data, cfg.template, cfg.tables, cfg.screenshots, cfg.figures, project, cfg.owner, cfg.consultant, cfg.engineer)
    document.save(cfg.output)
    print(f"Saved: {cfg.output.resolve()}")
    print(f"Generated figures directory: {cfg.figures.resolve()}")
    print("Open the DOCX in Word and update the Table of Contents with Ctrl+A, F9.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
