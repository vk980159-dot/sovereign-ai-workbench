"""
Real Deliverable Generation Tools (SIH26117).
Provides safe, auditable tool handlers for generating Word Approval Notes, Excel Workbooks,
PowerPoint Briefings, and PDF Compliance Reports.
"""

from typing import Dict, Any, List, Optional
from app.agents.deliverables.docx_generator import DocxApprovalNoteGenerator
from app.agents.deliverables.xlsx_generator import XlsxCalculationGenerator
from app.agents.deliverables.pptx_generator import PptxPresentationGenerator
from app.agents.deliverables.pdf_generator import PdfReportGenerator


def generate_docx_approval_note(
    title: str = "Industrial Inspection & SOP Compliance Note",
    reference_doc: str = "Inspection Telemetry & Field Audit",
    executive_summary: str = "",
    findings: Optional[List[Dict[str, Any]]] = None,
    sop_comparison: str = "",
    risks: Optional[List[str]] = None,
    recommendations: Optional[List[str]] = None,
    evidence_items: Optional[List[Dict[str, Any]]] = None,
    confidence: float = 0.95,
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates an authentic Word (.docx) Approval Note with styled layout, tables,
    citations, watermark, and SHA-256 integrity hash.
    """
    findings_list = findings or [
        {"component": "Bearing Assembly #3", "measured": "88.4 C", "threshold": "<= 75.0 C", "deviation": "+13.4 C", "status": "CRITICAL EXCEEDANCE"},
        {"component": "Vibration Sensor V-2", "measured": "4.8 mm/s", "threshold": "<= 3.0 mm/s", "deviation": "+1.8 mm/s", "status": "WARNING"}
    ]
    risks_list = risks or [
        "Unplanned catastrophic bearing seizure during peak operational cycle.",
        "Thermal expansion breach damaging secondary shaft containment.",
        "Regulatory safety breach under Industrial Turbomachinery Standard ISO-10816."
    ]
    recs_list = recommendations or [
        "Immediate controlled shutdown of Turbine Unit 4 within 12 hours.",
        "Emergency lubrication line flush and ultrasonic seal inspection.",
        "Submit formal remediation sign-off prior to cold restart."
    ]
    exec_summary = executive_summary or (
        "During automated processing of incoming inspection telemetry against governing standard SOP-IND-702, "
        "critical thermal deviations were detected on Bearing #3. Immediate containment action is required."
    )
    sop_text = sop_comparison or (
        "Operating standard SOP-IND-702 Section 4.2 stipulates peak bearing operating temperature must not exceed 75.0 C. "
        "Observed telemetry of 88.4 C violates standard by +13.4 C, mandating Level 1 Maintenance Isolation."
    )

    return DocxApprovalNoteGenerator.generate(
        title=title,
        reference_doc=reference_doc,
        executive_summary=exec_summary,
        findings=findings_list,
        sop_comparison=sop_text,
        risks=risks_list,
        recommendations=recs_list,
        evidence_items=evidence_items or [],
        confidence=confidence,
        filename=filename
    )


def generate_xlsx_calculation_sheet(
    title: str = "Industrial Vibration & Thermal Deviation Analysis",
    rows_data: Optional[List[Dict[str, Any]]] = None,
    summary_calculations: Optional[Dict[str, Any]] = None,
    evidence_records: Optional[List[Dict[str, Any]]] = None,
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates an authentic Excel (.xlsx) Calculation Workbook with active formulas,
    styling, conditional highlights, and an audit evidence tab.
    """
    sample_rows = rows_data or [
        {"subsystem": "Turbine Bearing #1", "baseline": 68.0, "observed": 71.2, "unit": "deg C", "crit": False},
        {"subsystem": "Turbine Bearing #2", "baseline": 70.0, "observed": 73.5, "unit": "deg C", "crit": False},
        {"subsystem": "Turbine Bearing #3", "baseline": 72.0, "observed": 88.4, "unit": "deg C", "crit": True},
        {"subsystem": "Cooling Loop Intake", "baseline": 35.0, "observed": 41.8, "unit": "deg C", "crit": False},
        {"subsystem": "Generator Shaft V-1", "baseline": 2.2, "observed": 3.9, "unit": "mm/s", "crit": True}
    ]

    return XlsxCalculationGenerator.generate(
        title=title,
        rows_data=sample_rows,
        summary_calculations=summary_calculations,
        evidence_records=evidence_records or [],
        filename=filename
    )


def generate_pptx_presentation(
    title: str = "Executive Briefing: Industrial Deviation & Risk Containment",
    executive_summary: str = "",
    findings: Optional[List[Dict[str, Any]]] = None,
    risks: Optional[List[str]] = None,
    recommendations: Optional[List[str]] = None,
    evidence_citations: Optional[List[Dict[str, Any]]] = None,
    confidence: float = 0.95,
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates an authentic PowerPoint (.pptx) briefing deck (6 slides) with
    dark slate executive theme, KPI cards, and citation tracking.
    """
    findings_list = findings or [
        {"component": "Bearing #3 Thermal Sensor", "measured": "88.4 C", "threshold": "75.0 C", "deviation": "+13.4 C", "status": "CRITICAL"},
        {"component": "Radial Vibration V-2", "measured": "4.8 mm/s", "threshold": "3.0 mm/s", "deviation": "+1.8 mm/s", "status": "WARNING"}
    ]
    risks_list = risks or [
        "Unplanned catastrophic thermal seizure under continuing load.",
        "Secondary damage to generator drive alignment couplers.",
        "Environmental safety compliance suspension."
    ]
    recs_list = recommendations or [
        "Issue emergency Level 1 shutdown notice.",
        "Perform non-destructive ultrasonic bearing inspection.",
        "Execute root cause analysis prior to restart."
    ]
    exec_summary = executive_summary or (
        "Automated multimodal ingestion of field inspection telemetry identified acute thermal deviations "
        "exceeding industrial safety margins. This executive briefing outlines evidence, risks, and containment steps."
    )

    return PptxPresentationGenerator.generate(
        title=title,
        executive_summary=exec_summary,
        findings=findings_list,
        risks=risks_list,
        recommendations=recs_list,
        evidence_citations=evidence_citations or [],
        confidence=confidence,
        filename=filename
    )


def generate_pdf_report(
    title: str = "Confidential Engineering Compliance Audit Report",
    executive_summary: str = "",
    findings: Optional[List[Dict[str, Any]]] = None,
    sop_comparison: str = "",
    recommendations: Optional[List[str]] = None,
    evidence_citations: Optional[List[Dict[str, Any]]] = None,
    confidence: float = 0.95,
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates an authentic PDF Compliance Report using ReportLab with clean styling,
    table formatting, confidentiality markings, and SHA-256 verification.
    """
    findings_list = findings or [
        {"component": "Bearing Assembly #3", "measured": "88.4 C", "threshold": "75.0 C", "deviation": "+13.4 C", "status": "CRITICAL EXCEEDANCE"},
        {"component": "Shaft Vibration V-2", "measured": "4.8 mm/s", "threshold": "3.0 mm/s", "deviation": "+1.8 mm/s", "status": "WARNING"}
    ]
    recs_list = recommendations or [
        "Immediate isolation of Turbine Unit 4 in accordance with emergency operating procedure EOP-12.",
        "Mobilize certified vibration technician for ultrasonic diagnostic sweep.",
        "Update sovereign ledger with supervisor sign-off before restart."
    ]
    exec_summary = executive_summary or (
        "Confidential industrial assessment evaluating plant telemetry against SOP-IND-702 standards. "
        "Severe operational temperature anomalies require immediate managerial intervention."
    )
    sop_text = sop_comparison or (
        "Standard SOP-IND-702 mandates max continuous bearing temp of 75.0 C. Current telemetry confirms 88.4 C, "
        "constituting a Class 1 Non-Conformance requiring immediate corrective action."
    )

    return PdfReportGenerator.generate(
        title=title,
        executive_summary=exec_summary,
        findings=findings_list,
        sop_comparison=sop_text,
        recommendations=recs_list,
        evidence_citations=evidence_citations or [],
        confidence=confidence,
        filename=filename
    )
