"""Render report/report.md. Run with: uv run --with reportlab --with pypdf scripts/build_report.py."""
from __future__ import annotations

import argparse
import re
from html import escape
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, KeepTogether, Paragraph, Preformatted, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]


def inline(text: str) -> str:
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font face="Courier" size="8">\1</font>', text)
    text = re.sub(r"\[([^]]+)\]\((https?://[^)]+)\)", r'<link href="\2" color="#246a60">\1</link>', text)
    return text


def build(source: Path, output: Path) -> int:
    font_dir = Path("/System/Library/Fonts/Supplemental")
    regular = font_dir / "Arial.ttf"
    bold = font_dir / "Arial Bold.ttf"
    body_font, bold_font = "Helvetica", "Helvetica-Bold"
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("ReportSans", str(regular)))
        pdfmetrics.registerFont(TTFont("ReportSans-Bold", str(bold)))
        pdfmetrics.registerFontFamily("ReportSans", normal="ReportSans", bold="ReportSans-Bold")
        body_font, bold_font = "ReportSans", "ReportSans-Bold"
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("ReportBody", fontName=body_font, fontSize=9.3, leading=13.5,
                              textColor=colors.HexColor("#273b40"), spaceAfter=7))
    styles.add(ParagraphStyle("ReportTitle", fontName=bold_font, fontSize=25, leading=29,
                              textColor=colors.HexColor("#173c38"), spaceAfter=13))
    styles.add(ParagraphStyle("ReportH2", fontName=bold_font, fontSize=13, leading=17,
                              textColor=colors.HexColor("#173c38"), spaceBefore=13,
                              spaceAfter=6, keepWithNext=True))
    styles.add(ParagraphStyle("ReportH3", parent=styles["ReportH2"], fontSize=10.5, leading=14,
                              spaceBefore=9))
    styles.add(ParagraphStyle("ReportCell", parent=styles["ReportBody"], fontSize=8,
                              leading=11, spaceAfter=0))
    styles.add(ParagraphStyle("ReportCode", fontName="Courier", fontSize=7.4, leading=10,
                              textColor=colors.HexColor("#294b46"), spaceAfter=9))
    story = []
    lines = source.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("```"):
            code = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                code.append(lines[index])
                index += 1
            story.append(Preformatted("\n".join(code), styles["ReportCode"], maxLineLength=97))
        elif line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = lines[index].strip().strip("|").split("|")
                if not all(re.fullmatch(r"\s*:?-+:?\s*", cell) for cell in cells):
                    rows.append([Paragraph(inline(cell.strip()), styles["ReportCell"]) for cell in cells])
                index += 1
            if rows:
                count = len(rows[0])
                widths = ([64, 49, 49] if count == 3 else [162 / count] * count)
                table = Table(rows, colWidths=[width * mm for width in widths], repeatRows=1,
                              hAlign="LEFT")
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e4efeb")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f5f8f6"), colors.white]),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#9bb9af")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]))
                story.extend([table, Spacer(1, 8)])
            continue
        elif re.match(r"^#{1,3} ", line):
            level = len(line.split(" ", 1)[0])
            story.append(Paragraph(inline(line[level + 1:]), styles[{1: "ReportTitle", 2: "ReportH2", 3: "ReportH3"}[level]]))
        elif line == "---":
            story.extend([HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#b9cec5")), Spacer(1, 8)])
        else:
            bullet = re.match(r"^(?:[-*]|\d+\.)\s+(.*)", line)
            text = bullet.group(1) if bullet else line
            block = [Paragraph(("&#8226; " if bullet else "") + inline(text), styles["ReportBody"])]
            # Never strand a heading at the bottom of a page: keep it with its first paragraph.
            if story and isinstance(story[-1], Paragraph) and story[-1].style.name.startswith("ReportH"):
                block.insert(0, story.pop())
            story.append(KeepTogether(block))
        index += 1

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#ccdad4"))
        canvas.line(24 * mm, 19 * mm, 186 * mm, 19 * mm)
        canvas.setFont(body_font, 8)
        canvas.setFillColor(colors.HexColor("#627970"))
        canvas.drawString(24 * mm, 14 * mm, "ZENTROMART  /  VOICEOPS 2026")
        canvas.drawRightString(186 * mm, 14 * mm, str(doc.page))
        canvas.restoreState()

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=24 * mm, leftMargin=24 * mm,
                            topMargin=22 * mm, bottomMargin=26 * mm,
                            title="ZentroMart - VoiceOps 2026 capstone", author="VoiceOps project")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    pages = len(PdfReader(output).pages)
    if pages > 4:
        raise SystemExit(f"Report has {pages} pages; shorten report/report.md to meet the 4-page limit.")
    print(f"Created {output} ({pages} pages)")
    return pages


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "report/report.md")
    parser.add_argument("--output", type=Path, default=ROOT / "report.pdf")
    args = parser.parse_args()
    build(args.source, args.output)
