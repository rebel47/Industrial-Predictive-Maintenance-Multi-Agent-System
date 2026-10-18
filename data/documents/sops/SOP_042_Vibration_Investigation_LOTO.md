# Standard Operating Procedure: Vibration Fault Investigation & Lockout/Tagout (LOTO)
**Document ID**: SOP-042-REV5  
**Title**: Machinery Health Diagnostics & Hazardous Energy Isolation  
**Effective Date**: 2024-01-10  
**Target Personnel**: Mechanical Maintenance Technicians, Reliability Engineers  
**Applicability**: All rotating pump, compressor, and motor trains in Process Area 1  

---

## Section 1: Non-Invasive Online Diagnostics (Machine Energized)
1. **Permitted Online Activities**:
   - Surface accelerometer measurement on bearing housing diagnostic test points.
   - Infrared thermal camera sweep of bearing housings, motor casing, and coupling guard.
   - Acoustic stethoscope / ultrasound listening at bearing points.
   - Stroboscopic inspection of visible shaft coupling through approved mesh viewing windows.
2. **Prohibited Online Activities**:
   - NEVER touch rotating shafts, open coupling guards, or open electrical terminal boxes while the machine is energized.
   - NEVER apply mechanical force or pry bars to rotating components.
   - If vibration velocity exceeds 7.1 mm/s RMS (ISO 10816 Zone D upper band), evacuate non-essential personnel immediately and execute controlled plant DCS stop.

---

## Section 2: Mandatory Lockout / Tagout (LOTO) Procedure (Before Disassembly)
Prior to loosening bearing housings, dismounting sensors, decoupling couplings, or opening casing bolts:
1. **Notify Control Room Operator**: Log impending maintenance on Asset P-104.
2. **Isolate Electrical Power**:
   - Trip motor breaker at MCC-02, Cubicle 4B.
   - Apply physical padlock and technician personal danger tag.
   - Attempt local push-button start to verify zero motion / test for dead circuit ("Try Step").
3. **Isolate Process Fluids**:
   - Close suction gate valve V-104-SUC and discharge valve V-104-DIS.
   - Lock valves in closed position with cable lockouts.
   - Open casing drain valve into collection bucket to verify zero residual hydraulic pressure.
4. **Thermal Dissipation Wait Period**:
   - If bearing housing temperature was recorded above 75°C, allow a minimum of 20 minutes cooling time before handling to prevent severe skin burn hazards.
