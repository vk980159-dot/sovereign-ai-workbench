"""
Synthetic Industrial Demo Data Generator (SIH26117).
MRPL Sovereign AI Workbench.

Generates realistic synthetic industrial documents, telemetry datasets,
inspection photos, and maintenance spreadsheets for the 5 demo scenarios.

PROMINENT CONFIDENTIALITY COMPLIANCE LABEL:
"SYNTHETIC DEMONSTRATION DATA – NOT REAL MRPL DATA (SIH 2026 PROTOTYPE)"
"""

import os
import csv
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

BASE_DIR = Path(__file__).resolve().parent.parent
DEMO_DIR = BASE_DIR / "demo_data"
DEMO_DIR.mkdir(parents=True, exist_ok=True)

DISCLAIMER_HEADER = "SYNTHETIC DEMONSTRATION DATA – NOT REAL MRPL DATA"
DISCLAIMER_SUB = "SIH 2026 Prototype (SIH26117) | Sovereign On-Premise AI Workbench"


def create_pdf_report(filename: str, title: str, subtitle: str, sections: list):
    """Generates a multi-page PDF document using ReportLab."""
    filepath = DEMO_DIR / filename
    c = canvas.Canvas(str(filepath), pagesize=letter)
    width, height = letter

    def draw_banner(p_num: int):
        # Header banner
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(0, height - 50, width, 50, fill=True, stroke=False)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(30, height - 25, DISCLAIMER_HEADER)
        c.setFont("Helvetica", 8)
        c.drawString(30, height - 40, DISCLAIMER_SUB)

        # Footer
        c.setFillColor(colors.HexColor("#64748b"))
        c.setFont("Helvetica", 8)
        c.drawString(30, 25, f"MRPL Sovereign AI Workbench (SIH26117) | {filename}")
        c.drawRightString(width - 30, 25, f"Page {p_num}")
        c.setStrokeColor(colors.HexColor("#cbd5e1"))
        c.line(30, 38, width - 30, 38)

    page_num = 1
    draw_banner(page_num)

    # Document Header
    y = height - 90
    c.setFillColor(colors.HexColor("#0369a1"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(30, y, title)
    
    y -= 22
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica", 11)
    c.drawString(30, y, subtitle)

    y -= 30
    c.setStrokeColor(colors.HexColor("#0284c7"))
    c.setLineWidth(2)
    c.line(30, y, width - 30, y)
    y -= 25

    for sec_title, paragraphs in sections:
        if y < 140:
            c.showPage()
            page_num += 1
            draw_banner(page_num)
            y = height - 80

        c.setFillColor(colors.HexColor("#0f172a"))
        c.setFont("Helvetica-Bold", 13)
        c.drawString(30, y, sec_title)
        y -= 18

        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#334155"))
        for p in paragraphs:
            # Word wrap simulation
            words = p.split()
            line = []
            for w in words:
                line.append(w)
                if len(" ".join(line)) > 90:
                    c.drawString(35, y, " ".join(line[:-1]))
                    y -= 14
                    line = [w]
                    if y < 60:
                        c.showPage()
                        page_num += 1
                        draw_banner(page_num)
                        y = height - 80
            if line:
                c.drawString(35, y, " ".join(line))
                y -= 16
        y -= 10

    c.save()
    print(f"  [+] Generated PDF: {filepath.name}")


def generate_compressor_report():
    """Generates synthetic compressor maintenance and vibration inspection report."""
    sections = [
        ("1. Equipment Identification & Operating Conditions", [
            "Equipment Tag: K-101 Centrifugal Gas Compressor. Location: Hydrocracking Unit 2.",
            "Service Fluid: Light Hydrocarbon Mixture. Design Suction Pressure: 24.5 bar, Discharge Pressure: 72.0 bar.",
            "Normal Operating Speed: 10,450 RPM. Primary Drive: High-pressure condensing steam turbine."
        ]),
        ("2. Observed Vibration Excursions & Telemetry Analysis", [
            "During routine seismic accelerometer survey on Drive End (DE) bearing housing, overall radial vibration was recorded at 6.4 mm/s RMS (Velocity).",
            "This reading represents a 70% increase above the baseline benchmark (3.2 mm/s RMS) and exceeds the ISO 10816-3 Zone C (Unrestricted Operation Limit) threshold of 4.5 mm/s RMS.",
            "Spectrum FFT analysis shows dominant 1X running frequency component with prominent 2X harmonics, indicative of angular shaft misalignment and early bearing race spalling.",
            "Non-drive end (NDE) bearing recorded moderate vibration at 3.9 mm/s RMS with elevated lube oil return temperature (68°C vs 55°C standard)."
        ]),
        ("3. Mechanical Seal & Lube Oil Inspection", [
            "Dry gas seal leakage rate increased from 1.2 Nm3/hr to 3.8 Nm3/hr on the primary vent line, indicating secondary O-ring elastomer degradation.",
            "Lube oil spectrochemical analysis revealed elevated tin (Sn: 18 ppm) and copper (Cu: 12 ppm) particulate concentrations, confirming babbitt bearing wear.",
            "Oil particle count: ISO 4406 cleanliness rating degraded to 21/18/15."
        ]),
        ("4. Required Corrective Actions & Preventive Maintenance", [
            "IMMEDIATE ACTION: Reduce compressor load by 15% to maintain vibration below 5.5 mm/s until shutdown.",
            "SCHEDULED OUTAGE: Execute laser shaft realignment between turbine driver and compressor coupling.",
            "REPLACEMENT: Disassemble DE journal bearing, inspect tilting pads for babbitt wipe, and install refurbished dry gas seal cartridge (Part #DGS-K101-REV4).",
            "HUMAN VERIFICATION: Final alignment tolerances must be signed off by Lead Rotating Equipment Engineer."
        ])
    ]
    create_pdf_report(
        "compressor_maintenance_report.pdf",
        "K-101 Centrifugal Compressor Maintenance & Vibration Report",
        "Confidential Industrial Diagnostics • Mangalore Refinery Hydrocracker Complex",
        sections
    )


def generate_pump_report():
    """Generates synthetic crude unit boiler feed pump inspection report."""
    sections = [
        ("1. Asset Overview & Service History", [
            "Equipment Tag: P-204A Multi-Stage Boiler Feed Water Pump. Location: Crude Distillation Unit (CDU).",
            "Design Flow Rate: 320 m3/hr. Total Dynamic Head: 850 meters. Operating Temperature: 165°C.",
            "Last Overhaul: 14 months prior. Cumulative Run Hours: 12,480 hrs."
        ]),
        ("2. Inspection Findings & Cavitation Diagnostics", [
            "Field operators reported audible rattling and cracking sound resembling gravel passing through first-stage impeller casing.",
            "High-frequency acoustic emission testing confirmed active hydraulic cavitation during minimum-flow recirculation operations.",
            "Suction strainer differential pressure reached 0.85 bar (normal limit: 0.25 bar), causing severe Net Positive Suction Head Available (NPSHa) deficit.",
            "Thrust bearing axial displacement sensor recorded +0.32 mm excursion toward drive end."
        ]),
        ("3. Visual Casing & Seal Examination", [
            "External visual inspection revealed localized crystallization and dried condensate seepage around mechanical seal gland packing.",
            "Thermographic imaging indicated hot spot on outboard thrust bearing housing reaching 84.5°C (Alarm threshold: 80°C).",
            "Coupling disc pack showed slight fretting corrosion on intermediate spacer bolts."
        ]),
        ("4. Engineering Recommendations", [
            "1. Clean suction duplex strainer immediately during off-peak window to restore NPSHa.",
            "2. Switch operating duty to standby pump P-204B.",
            "3. Conduct ultrasonic casing thickness inspection on suction spool to check for cavitation erosion.",
            "4. Drain and replenish ISO VG 46 synthetic turbine lube oil."
        ])
    ]
    create_pdf_report(
        "pump_inspection_report.pdf",
        "P-204A Boiler Feed Water Pump NDT & Vibration Survey",
        "Confidential Maintenance Inspection • Boiler & Utilities Section",
        sections
    )


def generate_equipment_manual():
    """Generates synthetic refinery multistage pump operating and maintenance manual."""
    sections = [
        ("1. Scope & Equipment Specification", [
            "This technical manual governs the operational limits, alignment tolerances, and preventive overhaul cycles for API 610 BB3 Heavy-Duty Multistage Centrifugal Pumps deployed in refinery fluid transport.",
            "Design Pressure Rating: Class 600 RF. Casing Metallurgy: ASTM A216 WCB with 12% Chrome internals (API Material Class S-6).",
            "Bearings: Hydrodynamic radial sleeve bearings with double-direction tilting pad thrust bearing."
        ]),
        ("2. Vibration Severity Standards (ISO 10816 / API 610)", [
            "Zone A (Newly commissioned machinery): < 2.3 mm/s RMS.",
            "Zone B (Acceptable for unrestricted long-term operation): 2.3 to 4.5 mm/s RMS.",
            "Zone C (Dissatisfactory - initiate maintenance plan): 4.5 to 7.1 mm/s RMS.",
            "Zone D (Severe damage imminent - immediate trip): > 7.1 mm/s RMS.",
            "Alarm threshold must be configured in DCS at 4.8 mm/s RMS; automatic trip threshold at 7.5 mm/s RMS."
        ]),
        ("3. Lube Oil System Operational Boundaries", [
            "Oil Reservoir Temperature: Maintain between 40°C and 55°C. Maximum allowable bearing drain temperature: 75°C.",
            "Oil Supply Pressure to bearings: 1.5 to 2.2 bar(g). Cleanliness requirement: ISO 4406 code 17/15/12 maximum.",
            "Lubricant grade: High-grade rust- and oxidation-inhibited (R&O) circulating oil ISO VG 46 or VG 68."
        ]),
        ("4. Overhaul Inspection Sequence", [
            "Check impeller ring diametral clearances against baseline: Replace wear rings if clearance exceeds 1.5x design.",
            "Rotor dynamic balance: Balance to ISO 1940 Grade G1.0 or better.",
            "Hydrostatic pressure test: Test casing at 1.5 times maximum allowable working pressure for minimum 30 minutes."
        ])
    ]
    create_pdf_report(
        "refinery_equipment_manual.pdf",
        "API 610 Multistage Centrifugal Pumps - Technical Manual",
        "Manufacturer Technical Guidance • Operational Boundaries & Maintenance Standards",
        sections
    )


def generate_safety_sop():
    """Generates synthetic hazardous hydrocarbon handling and emergency shutdown SOP."""
    sections = [
        ("1. Objective & Regulatory Compliance", [
            "Standard Operating Procedure: Refinery Hazardous Hydrocarbon Isolation and Emergency Shutdown (ESD-01).",
            "Applies to all operating units handling Class 1 flammable gases, toxic hydrogen sulfide (H2S), and high-pressure steam.",
            "Compliance standard: OISD-STD-105 (Work Permit System) and Petroleum Rules."
        ]),
        ("2. Mandatory Personal Protective Equipment (PPE)", [
            "Level 1 Areas: Flame-retardant anti-static overalls, safety helmet, steel-toed boots, impact goggles, H2S personal multi-gas detector.",
            "Level 2 (Active Breaking of Containment): Air-purifying escape respirator or positive-pressure SCBA unit.",
            "No personal electronic devices, non-intrinsically safe radios, or portable laptops permitted inside battery limit without hot work permit."
        ]),
        ("3. Emergency Shutdown (ESD) Initiation Protocol", [
            "Immediate ESD push-button activation is MANDATORY upon detection of:",
            "• Flammable gas concentration exceeding 20% LEL (Lower Explosive Limit) at unit perimeter.",
            "• Major hydrocarbon leak > 10 kg/min with potential for ignition.",
            "• Compressor unbalance resulting in vibration exceeding 8.0 mm/s RMS.",
            "• Loss of cooling water circulation or instrument air header pressure dropping below 3.5 bar."
        ]),
        ("4. Autonomous AI & Digital Safety Guardrail", [
            "CRITICAL SAFETY RULE: Under no circumstances shall an AI system, automated agent, or machine learning algorithm be connected to trigger, suppress, or modify Emergency Shutdown (ESD) interlocks or safety relief valves.",
            "All recommendations generated by AI workbenches are advisory decision-support tools only.",
            "Physical human authorization by the Shift Superintendent is strictly required before any field equipment actuation."
        ])
    ]
    create_pdf_report(
        "safety_sop.pdf",
        "Refinery Safety Standard Operating Procedure (SOP-HSE-042)",
        "Hazardous Fluid Containment & Emergency Isolation Protocol • Safety First",
        sections
    )


def generate_failure_csv():
    """Generates 100 realistic synthetic maintenance and equipment failure records."""
    filepath = DEMO_DIR / "equipment_failure_history.csv"
    headers = [
        "Record_ID", "Equipment_Tag", "Equipment_Name", "Unit", "Event_Date",
        "Failure_Mode", "Vibration_mms", "Bearing_Temp_C", "MTBF_Days",
        "Downtime_Hours", "Root_Cause", "Corrective_Action", "Risk_Level", "Classification"
    ]

    equipment_pool = [
        ("K-101", "Centrifugal Gas Compressor", "Hydrocracker Unit-2"),
        ("K-102", "Hydrogen Recycle Compressor", "Hydrocracker Unit-2"),
        ("P-201A", "Crude Charge Pump", "Crude Distillation Unit"),
        ("P-201B", "Crude Charge Pump (Standby)", "Crude Distillation Unit"),
        ("P-204A", "Boiler Feed Water Pump", "Utilities & Power"),
        ("P-204B", "Boiler Feed Water Pump", "Utilities & Power"),
        ("C-301", "Fluid Catalytic Cracker Blower", "FCC Unit"),
        ("E-401A", "Pre-Flash Column Heat Exchanger", "Crude Distillation Unit"),
        ("V-502", "High Pressure Hydrocarbon Separator", "Hydrocracker Unit-1"),
        ("P-302", "Slurry Circulation Pump", "FCC Unit")
    ]

    failure_modes = [
        ("Vibration Excursion", 6.2, 78.0, 42, "Shaft Misalignment & Soft Foot", "Precision laser alignment performed", "HIGH"),
        ("Mechanical Seal Leak", 3.8, 65.0, 68, "Elastomer O-ring hardening from heat", "Installed Silicon Carbide seal cartridge", "MEDIUM"),
        ("Bearing Babbit Spalling", 5.9, 84.0, 31, "Lube oil particle contamination", "Flushed lube oil system, replaced bearing", "HIGH"),
        ("Impeller Cavitation Wear", 4.8, 62.0, 85, "Low suction head (NPSHa deficit)", "Cleaned duplex suction strainer", "MEDIUM"),
        ("Lube Oil Temperature Spike", 3.1, 89.0, 110, "Shell-and-tube oil cooler fouling", "Acid chemical descaling of cooler", "HIGH"),
        ("Dry Gas Seal Vent Pressure High", 5.2, 71.0, 54, "Primary seal face particulate wear", "Purged N2 barrier gas, replaced face rings", "HIGH"),
        ("Coupling Disc Pack Fatigue", 4.6, 58.0, 95, "Cyclic torsional resonance", "Replaced flexible stainless disc pack", "MEDIUM"),
        ("Motor Winding Overheat", 2.9, 92.0, 130, "Cooling fan shroud blockage", "Cleared debris and replaced air filters", "MEDIUM")
    ]

    rows = []
    for i in range(1, 101):
        eq = equipment_pool[(i - 1) % len(equipment_pool)]
        fm = failure_modes[(i - 1) % len(failure_modes)]
        
        # Add slight variation
        vib = round(fm[1] + ((i % 5) * 0.2 - 0.4), 2)
        temp = round(fm[2] + ((i % 7) * 1.5 - 4.0), 1)
        downtime = round(4.0 + (i % 8) * 2.5, 1)

        row = {
            "Record_ID": f"REC-MRPL-{1000 + i}",
            "Equipment_Tag": eq[0],
            "Equipment_Name": eq[1],
            "Unit": eq[2],
            "Event_Date": f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
            "Failure_Mode": fm[0],
            "Vibration_mms": vib,
            "Bearing_Temp_C": temp,
            "MTBF_Days": fm[3],
            "Downtime_Hours": downtime,
            "Root_Cause": fm[4],
            "Corrective_Action": fm[5],
            "Risk_Level": fm[6],
            "Classification": "SYNTHETIC_CONFIDENTIAL"
        }
        rows.append(row)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  [+] Generated CSV: {filepath.name} (100 synthetic industrial records)")


def generate_maintenance_excel():
    """Generates a professional multi-sheet maintenance analysis Excel workbook."""
    filepath = DEMO_DIR / "maintenance_history.xlsx"
    wb = openpyxl.Workbook()

    # Styling colors
    navy_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    sky_fill = PatternFill(start_color="0284C7", end_color="0284C7", fill_type="solid")
    light_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    white_font_bold = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    bold_font = Font(name="Arial", size=10, bold=True)
    regular_font = Font(name="Arial", size=10)
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # Sheet 1: Incident Log
    ws1 = wb.active
    ws1.title = "Equipment_Incidents"
    ws1.append([DISCLAIMER_HEADER])
    ws1.merge_cells("A1:H1")
    ws1["A1"].font = Font(name="Arial", size=12, bold=True, color="0284C7")

    headers1 = ["Incident ID", "Equipment Tag", "Unit", "Failure Mode", "Vibration (mm/s)", "Severity", "Downtime (hrs)", "Action Taken"]
    ws1.append(headers1)
    for col_num, h in enumerate(headers1, 1):
        cell = ws1.cell(row=2, column=col_num)
        cell.fill = navy_fill
        cell.font = white_font_bold
        cell.alignment = Alignment(horizontal="center")

    incidents = [
        ("INC-01", "K-101", "Hydrocracker", "Vibration Excursion (6.4 mm/s)", 6.4, "HIGH", 18.5, "Emergency rotor balancing and coupling alignment"),
        ("INC-02", "P-204A", "Utilities", "Bearing Overheat & Seal Leak", 4.8, "MEDIUM", 8.0, "Replaced mechanical seal and flushed lube oil"),
        ("INC-03", "K-102", "Hydrocracker", "Dry Gas Seal Failure", 5.7, "HIGH", 24.0, "Replaced seal cartridge and inspected O-rings"),
        ("INC-04", "P-201A", "CDU", "Impeller Cavitation Wear", 4.2, "LOW", 4.5, "Cleaned suction strainer mesh"),
        ("INC-05", "C-301", "FCC", "Bearing Babbitt Pitting", 6.8, "HIGH", 32.0, "Re-babbitted journal pads and dynamic balancing"),
        ("INC-06", "P-302", "FCC", "Shaft Misalignment", 5.1, "MEDIUM", 12.0, "Precision laser alignment"),
        ("INC-07", "K-101", "Hydrocracker", "High Thrust Bearing Temp", 5.9, "HIGH", 14.0, "Cleaned lube oil cooler tube bundle"),
        ("INC-08", "P-204B", "Utilities", "Mechanical Seal Gland Seepage", 3.4, "LOW", 2.0, "Tightened gland studs to torque spec")
    ]

    for r_idx, inc in enumerate(incidents, 3):
        ws1.append(list(inc))
        for c_idx in range(1, len(inc) + 1):
            cell = ws1.cell(row=r_idx, column=c_idx)
            cell.font = regular_font
            cell.border = thin_border
            if c_idx == 6 and inc[5] == "HIGH":
                cell.font = Font(name="Arial", size=10, bold=True, color="DC2626")

    # Sheet 2: Component Breakdown
    ws2 = wb.create_sheet(title="Component_Reliability")
    ws2.append(["RELIABILITY COMPONENT SUMMARY (SYNTHETIC BENCHMARK)"])
    ws2.append(["Component", "Incident Count", "Avg Downtime (hrs)", "Risk Category", "Recommended Action"])
    for col_num in range(1, 6):
        cell = ws2.cell(row=2, column=col_num)
        cell.fill = sky_fill
        cell.font = white_font_bold

    components = [
        ("Bearings (Radial & Thrust)", 24, 18.2, "CRITICAL", "Implement continuous online vibration monitoring"),
        ("Mechanical Seals & Cartridges", 19, 12.5, "HIGH", "Upgrade elastomer compound to high-temp fluoroelastomer"),
        ("Impellers & Volutes", 8, 8.0, "MEDIUM", "Periodic ultrasonic casing thickness survey"),
        ("Shaft Couplings", 11, 6.4, "MEDIUM", "Laser alignment checks every 6 months"),
        ("Lube Oil Coolers", 6, 14.0, "HIGH", "Chemical descaling and differential pressure alarms")
    ]
    for r_idx, comp in enumerate(components, 3):
        ws2.append(list(comp))
        for c_idx in range(1, len(comp) + 1):
            ws2.cell(row=r_idx, column=c_idx).border = thin_border

    # Adjust column widths
    for sheet in [ws1, ws2]:
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    wb.save(str(filepath))
    print(f"  [+] Generated Excel: {filepath.name} (Multi-sheet Maintenance Workbook)")


def generate_inspection_image():
    """Generates synthetic visual inspection photograph asset with diagram overlays."""
    filepath = DEMO_DIR / "inspection_image.png"
    img = Image.new("RGB", (900, 650), color=(30, 41, 59))
    draw = ImageDraw.Draw(img)

    # Top banner
    draw.rectangle([0, 0, 900, 50], fill=(15, 23, 42))
    draw.text((20, 15), f"{DISCLAIMER_HEADER} • EQUIPMENT INSPECTION ASSET", fill=(56, 189, 248))

    # Draw industrial pump / compressor representation
    # Baseplate
    draw.rectangle([100, 480, 800, 520], fill=(71, 85, 105), outline=(148, 163, 184), width=3)
    draw.text((120, 495), "REINFORCED STRUCTURAL STEEL BASEPLATE", fill=(203, 213, 225))

    # Motor driver housing
    draw.rectangle([140, 260, 360, 480], fill=(51, 65, 85), outline=(2, 132, 199), width=3)
    draw.text((160, 350), "ELECTRIC MOTOR DRIVER\n(350 kW, 2980 RPM)", fill=(241, 245, 249))

    # Coupling
    draw.rectangle([360, 340, 440, 420], fill=(100, 116, 139), outline=(226, 232, 240), width=2)
    draw.text((365, 370), "COUPLING", fill=(255, 255, 255))

    # Centrifugal Pump Casing
    draw.ellipse([440, 220, 720, 480], fill=(51, 65, 85), outline=(14, 165, 233), width=4)
    draw.text((500, 340), "PUMP CASING (P-204A)\nAPI 610 MULTISTAGE", fill=(241, 245, 249))

    # Bearing Housing & Seal (Anomaly zone)
    draw.rectangle([440, 300, 500, 420], fill=(185, 28, 28), outline=(239, 68, 68), width=3)
    draw.text((370, 250), "ANOMALY: SEAL LEAK & VIBRATION", fill=(248, 113, 113))
    draw.line([(420, 270), (470, 310)], fill=(239, 68, 68), width=2)

    # Telemetry Callout Box
    draw.rectangle([580, 80, 870, 200], fill=(15, 23, 42), outline=(245, 158, 11), width=2)
    draw.text((595, 95), "LIVE TELEMETRY CALLOUT", fill=(245, 158, 11))
    draw.text((595, 120), "• Vib DE Radial: 6.4 mm/s [ALARM]", fill=(239, 68, 68))
    draw.text((595, 140), "• Bearing Temp: 84.5°C [HIGH]", fill=(239, 68, 68))
    draw.text((595, 160), "• Seal Pressure: -0.4 bar [DROP]", fill=(251, 191, 36))
    draw.text((595, 180), "• Status: Human Verification Required", fill=(56, 189, 248))

    # Calibration scale footer
    draw.rectangle([0, 600, 900, 650], fill=(15, 23, 42))
    draw.text((20, 615), "SIH26117 SYNTHETIC MULTIMODAL EVIDENCE • ON-PREMISE AIR-GAPPED INFERENCE", fill=(148, 163, 184))

    img.save(str(filepath))
    print(f"  [+] Generated Image: {filepath.name} (Industrial Telemetry Visual Asset)")


def main():
    print("=" * 70)
    print(" [GENERATING SYNTHETIC INDUSTRIAL DEMO DATASETS - SIH26117]")
    print(f" [DISCLAIMER]: {DISCLAIMER_HEADER}")
    print("=" * 70)

    generate_compressor_report()
    generate_pump_report()
    generate_equipment_manual()
    generate_safety_sop()
    generate_failure_csv()
    generate_maintenance_excel()
    generate_inspection_image()

    print("=" * 70)
    print(" [ALL 7 SYNTHETIC DEMO ASSETS GENERATED IN /demo_data]")
    print("=" * 70)


if __name__ == "__main__":
    main()
