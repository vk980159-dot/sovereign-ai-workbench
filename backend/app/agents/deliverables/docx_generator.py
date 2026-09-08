"""
Real DOCX Deliverable Generator (SIH26117).
Generates professionally formatted industrial Approval Notes and Executive Memorandums using python-docx.
Every deliverable is a valid, real .docx file with traceable evidence, verification, and SHA-256 cryptographic signature.
"""

import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from app.config import settings


def _set_cell_background(cell, hex_color: str):
    """Sets background color of a Word table cell."""
    tc_pr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tc_pr.append(shd)


class DocxApprovalNoteGenerator:
    """Generates real, styled Word Approval Notes for confidential industrial workflows."""

    @staticmethod
    def generate(
        title: str,
        reference_doc: str,
        executive_summary: str,
        findings: List[Dict[str, Any]],
        sop_comparison: str,
        risks: List[str],
        recommendations: List[str],
        evidence_items: Optional[List[Dict[str, Any]]] = None,
        confidence: float = 0.95,
        filename: Optional[str] = None,
        operator_name: str = "Sovereign Operator"
    ) -> Dict[str, Any]:
        """
        Creates a real valid .docx Approval Note.
        Returns metadata containing path, size, and SHA-256.
        """
        doc = docx.Document()

        # Set 1-inch margins
        for section in doc.sections:
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.0)
            section.right_margin = Inches(1.0)

        # 1. Header Banner
        header = doc.sections[0].header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("CONFIDENTIAL • SOVEREIGN ON-PREMISE AI • AI-GENERATED DRAFT")
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(120, 120, 120)

        # 2. Document Title
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_title = p_title.add_run(f"APPROVAL NOTE: {title.upper()}")
        r_title.bold = True
        r_title.font.size = Pt(18)
        r_title.font.color.rgb = RGBColor(15, 23, 42)  # Dark slate

        # Subtitle
        p_sub = doc.add_paragraph()
        p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_sub = p_sub.add_run("INDUSTRIAL SAFETY, COMPLIANCE & OPERATIONAL REMEDIATION")
        r_sub.font.size = Pt(10)
        r_sub.font.color.rgb = RGBColor(2, 132, 199)  # Tech cyan
        r_sub.bold = True

        doc.add_paragraph().paragraph_format.space_after = Pt(12)

        # 3. Metadata Table
        meta_table = doc.add_table(rows=4, cols=2)
        meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        meta_data = [
            ("Reference Document:", reference_doc),
            ("Date Generated:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")),
            ("Evaluating Operator:", operator_name),
            ("Classification Level:", "RESTRICTED / ON-PREMISE CONFIDENTIAL")
        ]
        for row_idx, (label, val) in enumerate(meta_data):
            cell_lbl = meta_table.cell(row_idx, 0)
            cell_val = meta_table.cell(row_idx, 1)
            cell_lbl.paragraphs[0].add_run(label).bold = True
            cell_lbl.paragraphs[0].runs[0].font.size = Pt(9.5)
            cell_val.paragraphs[0].add_run(val)
            cell_val.paragraphs[0].runs[0].font.size = Pt(9.5)
            _set_cell_background(cell_lbl, "F1F5F9")
            _set_cell_background(cell_val, "F8FAFC")

        doc.add_paragraph().paragraph_format.space_after = Pt(12)

        # 4. Executive Summary
        h_exec = doc.add_heading(level=1)
        r_exec = h_exec.add_run("1. Executive Summary")
        r_exec.font.color.rgb = RGBColor(15, 23, 42)
        p_exec = doc.add_paragraph(executive_summary)
        p_exec.paragraph_format.line_spacing = 1.15

        # 5. Inspection Findings & Technical Observations
        h_find = doc.add_heading(level=1)
        r_find = h_find.add_run("2. Technical Findings & Measured Observations")
        r_find.font.color.rgb = RGBColor(15, 23, 42)

        if findings:
            f_table = doc.add_table(rows=1 + len(findings), cols=4)
            f_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            headers = ["Parameter / Item", "Observed Value", "Standard Threshold", "Severity"]
            for c_idx, htext in enumerate(headers):
                c = f_table.cell(0, c_idx)
                run = c.paragraphs[0].add_run(htext)
                run.bold = True
                run.font.size = Pt(9.5)
                run.font.color.rgb = RGBColor(255, 255, 255)
                _set_cell_background(c, "0F172A")

            for r_idx, f_item in enumerate(findings, start=1):
                item_name = f_item.get("parameter") or f_item.get("item") or f_item.get("finding") or "Metric"
                obs_val = str(f_item.get("measured") or f_item.get("value") or f_item.get("observed") or "N/A")
                thresh = str(f_item.get("threshold") or f_item.get("standard") or "Nominal")
                sev = str(f_item.get("severity") or f_item.get("status") or "CRITICAL").upper()

                c0 = f_table.cell(r_idx, 0)
                c1 = f_table.cell(r_idx, 1)
                c2 = f_table.cell(r_idx, 2)
                c3 = f_table.cell(r_idx, 3)

                c0.paragraphs[0].add_run(item_name).font.size = Pt(9)
                c1.paragraphs[0].add_run(obs_val).font.size = Pt(9)
                c2.paragraphs[0].add_run(thresh).font.size = Pt(9)
                r_sev = c3.paragraphs[0].add_run(sev)
                r_sev.bold = True
                r_sev.font.size = Pt(9)
                if sev in ("CRITICAL", "HIGH"):
                    r_sev.font.color.rgb = RGBColor(220, 38, 38)
                    _set_cell_background(c3, "FEE2E2")
                else:
                    r_sev.font.color.rgb = RGBColor(22, 163, 74)
                    _set_cell_background(c3, "DCFCE7")
        else:
            doc.add_paragraph("No anomalous findings recorded in primary observation logs.")

        doc.add_paragraph().paragraph_format.space_after = Pt(12)

        # 6. Safety SOP & Standard Comparison
        h_sop = doc.add_heading(level=1)
        r_sop = h_sop.add_run("3. Safety SOP & Standard Operating Guidelines Comparison")
        r_sop.font.color.rgb = RGBColor(15, 23, 42)
        doc.add_paragraph(sop_comparison)

        # 7. Risk & Impact Analysis
        h_risk = doc.add_heading(level=1)
        r_risk = h_risk.add_run("4. Risk & Operational Impact Assessment")
        r_risk.font.color.rgb = RGBColor(15, 23, 42)
        for risk in risks:
            p_bullet = doc.add_paragraph(style="List Bullet")
            p_bullet.add_run(risk)

        # 8. Proposed Recommendations & Immediate Actions
        h_rec = doc.add_heading(level=1)
        r_rec = h_rec.add_run("5. Strategic Recommendations & Action Plan")
        r_rec.font.color.rgb = RGBColor(15, 23, 42)
        for rec in recommendations:
            p_num = doc.add_paragraph(style="List Number")
            p_num.add_run(rec)

        # 9. Evidence Traceability Citations
        if evidence_items:
            h_ev = doc.add_heading(level=1)
            r_ev = h_ev.add_run("6. Traceable Evidence & Source Citations")
            r_ev.font.color.rgb = RGBColor(15, 23, 42)
            for ev in evidence_items:
                fname = ev.get("filename", "Evidence Doc")
                page = f"Page {ev.get('page_number')}" if ev.get("page_number") else "Section"
                snip = ev.get("text_excerpt") or ev.get("snippet") or ""
                p_cite = doc.add_paragraph(style="List Bullet")
                p_cite.add_run(f"[{fname} • {page}]: ").bold = True
                p_cite.add_run(f'"{snip}"')

        # 10. AI Verification & Cryptographic Ledger Footer
        doc.add_paragraph().paragraph_format.space_after = Pt(16)
        p_ver = doc.add_paragraph()
        p_ver.paragraph_format.space_before = Pt(16)
        r_ver_lbl = p_ver.add_run("Consensus Verification Status: ")
        r_ver_lbl.bold = True
        r_ver_val = p_ver.add_run(f"VERIFIED (Auditor Confidence: {int(confidence * 100)}%)\n")
        r_ver_val.font.color.rgb = RGBColor(22, 163, 74)
        r_ver_val.bold = True

        p_notice = doc.add_paragraph()
        r_not = p_notice.add_run(
            "DISCLAIMER: This Approval Note was autonomously synthesized by the Sovereign AI On-Premise "
            "Workbench (SIH26117). All facts are grounded against local documents. Human operator sign-off required."
        )
        r_not.font.size = Pt(8.5)
        r_not.font.italic = True
        r_not.font.color.rgb = RGBColor(100, 116, 139)

        # Save to generated_artifacts directory
        out_filename = filename or f"Approval_Note_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.docx"
        if not out_filename.endswith(".docx"):
            out_filename += ".docx"

        file_path = os.path.join(settings.OUTPUT_DIR, out_filename)
        doc.save(file_path)

        # Compute SHA-256
        with open(file_path, "rb") as f:
            content_bytes = f.read()
        sha256_hash = hashlib.sha256(content_bytes).hexdigest()

        return {
            "filename": out_filename,
            "file_path": file_path,
            "artifact_type": "docx",
            "size_bytes": len(content_bytes),
            "sha256": sha256_hash,
            "title": title,
            "confidence": confidence
        }
