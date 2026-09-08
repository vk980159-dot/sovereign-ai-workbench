# STANDARD OPERATING PROCEDURE: SOP-IND-702
## Turbomachinery Operating Thresholds & Critical Safety Standard
**Document ID**: SOP-IND-702  
**Revision**: 4.2  
**Governing Asset Class**: Industrial Turbomachinery (High-Pressure Turbine Units 1-6)  
**Security Classification**: CONFIDENTIAL • SOVEREIGN ON-PREMISE  

---

### 1. Purpose & Scope
This Standard Operating Procedure establishes deterministic operating limits, thermal thresholds, and vibration tolerances for all operational industrial gas and steam turbine units, with specific governance over bearing assemblies, rotor alignment, and lube oil delivery subsystems.

---

### 2. Governing Thermal Thresholds (Bearing Subsystems)
All radial and thrust bearing assemblies must operate within strictly controlled thermal boundaries:

1. **Nominal Operating Range**: 65.0°C to 72.0°C under full continuous rated load.
2. **Standard Continuous Threshold Limit**: **75.0°C**. Any bearing temperature sustained at or above 75.0°C constitutes a Level 1 Operational Non-Conformance.
3. **Critical Trip & Damage Threshold**: **85.0°C**. Sustained operation above 85.0°C accelerates babbitt metal fatigue, causes lube oil breakdown, and risks catastrophic rotor seizure.
4. **Immediate Emergency Isolation Limit**: Any bearing temperature observed at or above **88.0°C** requires immediate controlled shutdown and unit isolation within 12 hours.

---

### 3. Vibration & Dynamic Stability Limits (ISO-10816-3 Alignment)
1. **Nominal Vibration**: <= 2.2 mm/s RMS velocity.
2. **Warning Vibration Threshold**: **3.5 mm/s RMS velocity**. Exceeding 3.5 mm/s mandates high-resolution spectral vibration analysis.
3. **Critical Alarm Level**: **4.5 mm/s RMS velocity**. Operating at >= 4.5 mm/s requires immediate load shedding.

---

### 4. Severity Classification Rules
- **NORMAL**: Temperature < 75.0°C and Vibration < 3.5 mm/s.
- **ELEVATED**: Temperature between 75.0°C and 80.0°C OR Vibration between 3.5 mm/s and 4.2 mm/s. Requires maintenance monitoring.
- **CRITICAL (Level 1)**: Temperature > 80.0°C (especially >= 85.0°C) OR Vibration >= 4.5 mm/s. Mandates emergency controlled isolation, root-cause investigation, and formal Approval Note.

---

### 5. Mandatory Deliverable & Approval Workflow
Whenever an inspection reveals a **CRITICAL (Level 1)** exceedance:
1. A formal written **Approval Note** (.docx) must be generated and submitted to the Chief Plant Engineer.
2. The Approval Note must detail:
   - Specific Asset & Component ID (e.g., Turbine Unit 4, Bearing #3)
   - Baseline vs Observed Sensor Telemetry
   - Exact mathematical deviation from the SOP-IND-702 threshold (75.0°C)
   - Root-cause risk assessment
   - Recommended remediation actions (controlled shutdown within 12 hours)
   - Verifiable source citations and cryptographic SHA-256 seal.
3. Equipment restart is strictly prohibited without signed engineering authorization.
