# OEM Operating & Maintenance Manual: FlowMax P-104 Centrifugal Slurry Pump
**Document ID**: OEM-MAN-P104-REV4  
**Asset Applicability**: FlowMax P-100 Series (Specifically P-104, P-105, P-106)  
**Equipment Type**: Horizontal End-Suction Centrifugal Pump  
**Revision Date**: 2023-08-15  
**Manufacturer**: FlowMax Industrial Dynamics GmbH  

---

## Section 1: Equipment Specifications & Operating Parameters
- **Nominal Operating Speed**: 1750 RPM (Motor coupled direct drive)
- **Design Flow Rate**: 450 m³/h at 65 m head
- **Bearings Installed**:
  - Drive-End (DE) Bearing: Deep Groove Ball Bearing **SKF 6205-2Z/C3** (or approved Timken equivalent)
  - Non-Drive-End (NDE) Bearing: Cylindrical Roller Bearing **SKF NU 205 ECP**
- **Lubrication**: Polyurea-based synthetic grease (Mobil Polyrex EM or Shell Gadus S5 V100 2). Re-greasing interval: 2,500 operating hours (15 grams per bearing housing).
- **Mechanical Seal**: Cartridge dual mechanical seal with Plan 53A barrier fluid.

---

## Section 2: Vibration & Temperature Operating Limits (ISO 10816-3 Class II)
Per ISO 10816-3 Group 2 (Medium-sized industrial machines 15 kW to 300 kW, rigid foundation):
- **Zone A (Newly commissioned / Good)**: Overall Vibration Velocity RMS < 1.4 mm/s.
- **Zone B (Acceptable for long-term continuous operation)**: 1.4 mm/s to 2.8 mm/s RMS.
- **Zone C (Unsatisfactory / Alert Threshold)**: 2.8 mm/s to 4.5 mm/s RMS. Maintenance planning required within 7 days.
- **Zone D (Unacceptable / Danger Shutdown Threshold)**: > 4.5 mm/s RMS. Immediate trip / manual shutdown required to prevent catastrophic shaft deflection or casing breach.
- **Bearing Temperature Thresholds**:
  - Normal Operating: 55°C – 70°C.
  - High Temperature Warning: > 75°C.
  - Emergency High Trip Limit: > 85°C.

---

## Section 3: Bearing Fault Frequencies & Characteristic Vibration Signatures
At nominal 1750 RPM (Shaft frequency $f_r = 29.17\text{ Hz}$):
- **Ball Pass Frequency Outer Race (BPFO)**: $3.58 \times f_r \approx 104.4\text{ Hz}$. Characteristic sharp impact peaks with harmonic sidebands indicating localized spalling or raceway fatigue.
- **Ball Pass Frequency Inner Race (BPFI)**: $5.42 \times f_r \approx 158.1\text{ Hz}$. Modulated by $1\times$ shaft rotational frequency. High crest factor (> 4.5) and elevated kurtosis (> 3.5).
- **Ball Spin Frequency (BSF)**: $2.32 \times f_r \approx 67.7\text{ Hz}$. Indicates rolling element ball defect.
- **Fundamental Train Frequency (FTF)**: $0.40 \times f_r \approx 11.7\text{ Hz}$. Cage damage or instability.

---

## Section 4: Troubleshooting Guide: Common Failure Modes
| Observed Symptoms | Primary Hypotheses | Distinguishing Diagnostic Check |
| :--- | :--- | :--- |
| High vibration (> 4.5 mm/s), high temperature (> 75°C), acoustic grinding | Bearing Raceway Defect (BPFI/BPFO) or Inadequate Lubrication | Spectral peak matching BPFI (158 Hz) or BPFO (104 Hz); high kurtosis (> 4.0); grease inspection for metallic particles |
| High vibration at $1\times$ RPM, normal temperature | Rotor Dynamic Unbalance | Spectral peak strictly at 29.2 Hz ($1\times$); phase angle steady; no high frequency bearing defect peaks |
| High vibration at $2\times$ RPM, axial vibration elevated | Shaft / Coupling Misalignment | High $2\times$ (58.3 Hz) peak, elevated axial vibration (> 50% of radial); thermal imaging of coupling reveals hot spot |
| Random broadband vibration, fluctuating discharge pressure | Hydraulic Cavitation or Suction Starvation | Broadband acoustic noise ("gravel noise"), suction pressure gauge below NPSHr (Net Positive Suction Head required) |

---

## Section 5: Mandatory Safety Constraints
- **WARNING**: Never open the bearing housing or remove the coupling guard while the pump driver is energized.
- Adhere strictly to plant Lockout/Tagout Standard Operating Procedure (SOP-042).
- Prior to mechanical inspection, de-energize the motor at the Motor Control Center (MCC), verify zero energy state, and lock the suction/discharge isolation valves.
