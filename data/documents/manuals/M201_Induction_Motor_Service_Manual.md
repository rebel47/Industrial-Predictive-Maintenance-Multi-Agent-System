# Service Manual: ApexDrive 75 kW Three-Phase Induction Motor (Driver for Pump P-104)
**Document ID**: OEM-MAN-M201-REV2  
**Asset Applicability**: ApexDrive M-200 Series (M-201, M-202, M-203)  
**Equipment Type**: Squirrel-Cage Induction Motor, 400V, 50 Hz, 4-Pole  
**Revision Date**: 2022-11-10  
**Manufacturer**: ApexDrive Electric Systems Corp  

---

## Section 1: Electrical & Mechanical Specifications
- **Rated Power**: 75 kW (100 HP)
- **Rated Speed**: 1485 RPM at 50 Hz (or 1750 RPM on 60 Hz VFD drive)
- **Full Load Amperage (FLA)**: 135 A at 400 VAC
- **Bearings**:
  - Drive End (DE): Deep Groove Ball Bearing **6310-C3**
  - Non-Drive End (NDE): Deep Groove Ball Bearing **6210-C3**
- **Winding Insulation Class**: Class H ($180^\circ\text{C}$ maximum allowable hot-spot)

---

## Section 2: Temperature Limits & Thermal Protection
- **Stator Winding RTD Warning**: $> 130^\circ\text{C}$
- **Stator Winding RTD Emergency Trip**: $> 145^\circ\text{C}$
- **Motor Bearing Housing Temperature Limit**:
  - Normal: 60°C – 75°C
  - Warning Threshold: 80°C
  - Shutdown Threshold: 90°C

---

## Section 3: Electrical vs. Mechanical Vibration Diagnostics
- **Twice Line Frequency ($2f_L = 100\text{ Hz}$ or $120\text{ Hz}$)**: High $2f_L$ vibration that collapses immediately when power is cut indicates an electromagnetic problem (stator core looseness, dynamic air gap eccentricity, or phase voltage unbalance).
- **Broken Rotor Bars**: Sidebands around $1\times$ running speed spaced at twice slip frequency ($2 s f_L$). Motor current signature analysis (MCSA) reveals sidebands $> -35\text{ dB}$ below the fundamental current carrier.
- **Mechanical Soft Foot**: High $1\times$ vibration that reduces markedly when individual hold-down bolts are loosened sequentially.
