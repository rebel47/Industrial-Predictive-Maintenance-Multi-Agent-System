# Industrial Predictive Maintenance & Root-Cause Analysis Multi-Agent System

An industrial-grade AI system designed for plant reliability and maintenance engineers. The system investigates rotating equipment faults (centrifugal pumps, induction motors, and bearings), identifies likely root causes by synthesizing numerical telemetry with technical manuals and manufacturer service bulletins, generates safety-governed maintenance plans, and mandates human engineering approval.

---

## 🏗️ System Architecture

The system is coordinated via a shared, typed **LangGraph** state machine. Each agent has a distinct engineering responsibility:

```
                            Technician Complaint / Telemetry Stream
                                              │
                                              ▼
                        ┌───────────────────────────────────────────┐
                        │       LangGraph Supervisor Agent          │
                        │   State initialization & orchestrator     │
                        └─────────────┬───────────────┬─────────────┘
                                      │               │
                 ┌────────────────────┴────────┐      │
                 ▼                             ▼      ▼
    ┌─────────────────────────┐   ┌───────────────────────────┐   ┌─────────────────────────┐
    │  Sensor Analytics Node  │   │     RAG Knowledge Node    │   │   Web Research Node     │
    │ - ISO 10816 Severity    │   │ - Pump P-104 OEM Manual   │   │ - SKF / Timken Bulletins│
    │ - FFT Harmonics & BPFI  │   │ - SOP-042 LOTO Procedures │   │ - Standards (ANSI/HI)   │
    │ - Isolation Forest      │   │ - SOP-088 Bearing Overhaul│   │ - External Provenance   │
    │ - CWRU Fault Classifier │   │ - Historical Incident Logs│   │                         │
    └────────────┬────────────┘   └─────────────┬─────────────┘   └────────────┬────────────┘
                 │                              │                              │
                 └───────────────────────┬──────┴──────────────────────────────┘
                                         ▼
                        ┌───────────────────────────────────────────┐
                        │          Evidence Merger Node             │
                        │ Normalized IDs (E001, E002...) & Dedupe   │
                        └─────────────────────┬─────────────────────┘
                                         ▼
                        ┌───────────────────────────────────────────┐
                        │        Root-Cause Analysis Node           │
                        │ - Compares competing failure hypotheses   │
                        │ - Strict claim-to-evidence citation       │
                        │ - Missing distinguishing diagnostic tests │
                        └─────────────────────┬─────────────────────┘
                                         ▼
                        ┌───────────────────────────────────────────┐
                        │       Maintenance Planning Node           │
                        │ - Prioritized, actionable repair steps    │
                        │ - Mandatory Lockout/Tagout (LOTO SOP-042) │
                        │ - Verified spare parts & torque specs     │
                        └─────────────────────┬─────────────────────┘
                                         ▼
                        ┌───────────────────────────────────────────┐
                        │     Deterministic Safety Verification     │
                        │ - Citation grounding check (no halluc.)   │
                        │ - Physical intervention LOTO interlock    │
                        └─────────────────────┬─────────────────────┘
                                         ▼
                        ┌───────────────────────────────────────────┐
                        │    Human Engineer Approval & Sign-Off     │
                        │ Level-2 Reliability Engineer Audit Trail  │
                        └───────────────────────────────────────────┘
```

---

## 📊 Dataset & Analytics Pipeline

### 1. Case Western Reserve University (CWRU) Bearing Data
- Grounded on the 12 kHz Drive-End bearing vibration dataset (Normal baseline, Inner Race Defect `IR`, Outer Race Defect `OR`, and Ball Element Defect `BA`).
- **Feature Extraction**:
  - Time-Domain: RMS, Kurtosis, Skewness, Crest Factor, Shape Factor, Peak-to-Peak.
  - Frequency-Domain: FFT amplitude spectrum, 1X running speed harmonic (29.2 Hz at 1750 RPM), 2X misalignment harmonic (58.3 Hz), and characteristic bearing defect frequencies (BPFI ~158 Hz, BPFO ~104 Hz).
- **ISO 10816-3 Severity**: Automatically assigns Zone A (Good), Zone B (Acceptable), Zone C (Unsatisfactory), or Zone D (Unacceptable / Trip).
- **ML Classifier**: Trained Random Forest model achieving **100% Macro-F1** on held-out test windows.

---

## 🔍 Industrial Knowledge Base & Hybrid RAG

Internal technical documents reside in `data/documents/`:
- `manuals/P104_Centrifugal_Pump_OEM_Manual.md`: OEM specs, operating limits, bearing models (SKF 6205-2Z/C3), troubleshooting matrix.
- `manuals/M201_Induction_Motor_Service_Manual.md`: Motor winding temperature limits, RTD trip points, electrical vs. mechanical vibration diagnostics.
- `sops/SOP_042_Vibration_Investigation_LOTO.md`: Mandatory hazardous energy isolation, zero-energy verification ("Try Step"), thermal wait period.
- `sops/SOP_088_Bearing_Replacement_Checklist.md`: Precision laser alignment tolerances, induction heater limits (110°C), bolt torque specs.
- `incidents/INC_2024_03_Pump_P104_Bearing_Seizure.json`: Past incident record of P-104 bearing inner-race spalling.
- `incidents/INC_2023_11_Pump_P102_Misalignment.json`: Past incident record of P-102 dynamic coupling misalignment.

**Hybrid Retrieval**: Combines **BM25 lexical ranking** with **dense TF-IDF/semantic vector similarity** and **Reciprocal Rank Fusion (RRF)**, yielding a 1.0 Mean Reciprocal Rank (MRR).

---

## 🌐 Web Research & External Provenance

- Searches external manufacturer service bulletins (SKF Technical Advisories, Timken Reliability Bulletins, Hydraulic Institute ANSI/HI standards).
- Preserves external URLs, publisher names, publication dates, and credibility ratings.
- Differentiates external general advisories from mandatory plant internal SOPs.

---

## 🔒 Deterministic Safety Verification & Grounding

The verification engine enforces zero tolerance for hallucinations and safety hazards:
1. **Citation Grounding Interlock**: Every claim in the root-cause report and maintenance plan must reference a valid, retrieved `evidence_id` (`E001`, `E002`, ...). Fabricated citations automatically trigger `verification_status: FAILED`.
2. **Hazardous Intervention LOTO Interlock**: Any physical step (uncoupling, dismounting bearings, opening casing) must mandate Lockout/Tagout (`requires_loto == True`). Unprotected work recommendations fail verification.
3. **Mandatory Human-in-the-Loop Sign-off**: Consequential maintenance plans pause for certified reliability engineer review before execution.

---

## 🚀 Quickstart & Usage

### 1. Installation
Clone the repository and install requirements:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your `OPENAI_API_KEY` to enable live OpenAI GPT models (`gpt-4o` or `gpt-4o-mini`).
*(Note: If no API key is provided, the system executes in deterministic offline mode with 100% full functionality).*

### 3. Launch the Interactive Dashboard
```bash
streamlit run frontend/app.py
```
Open `http://localhost:8501` to view the engineering dashboard:
- **Incident Console**: Run live investigations on preset or custom symptoms.
- **Spectrum Visualizer**: View time-series trends and high-resolution FFT frequency spectrum.
- **Evidence Matrix**: Inspect cited passages with exact source metadata.
- **Document Browser**: Browse plant manuals and SOPs.

### 4. Launch the REST API
```bash
python -m uvicorn app.api.routes:app --reload --host 0.0.0.0 --port 8000
```
API Documentation is available at `http://localhost:8000/docs`.

### 5. Run the Automated Evaluation Suite
Run all unit tests:
```bash
pytest -v
```
Run the full benchmark evaluation (measuring ML classifier, RAG retrieval, anomaly detection, and the 8 Section-11 failure scenarios):
```bash
python -m app.evaluation.eval_pipeline
```

---

## 📈 Evaluation Benchmark Results

```
================================================================================
INDUSTRIAL PREDICTIVE MAINTENANCE MULTI-AGENT SYSTEM: BENCHMARK REPORT
================================================================================

1. CWRU FAULT CLASSIFIER (Supervised ML):
  Macro-F1 Score:    1.0000
  Holdout Samples:   28
  Classes Evaluated: ['NORMAL', 'INNER_RACE_FAULT', 'OUTER_RACE_FAULT', 'BALL_FAULT']

2. ANOMALY DETECTION (Isolation Forest + Statistical Limits):
  Precision:         1.0000
  Recall:            1.0000
  False Alarm Rate:  0.0000

3. HYBRID RAG RETRIEVAL (BM25 + TF-IDF Vector + RRF):
  Recall@1:          1.0000
  Recall@3:          1.0000
  Mean Recip. Rank:  1.0000

4. EXPLICIT FAILURE SCENARIO BENCHMARK (Section 11 Test Suite):
+------------+-------------------------------------+----------+------------------------------------------+
| Scenario   | Description                         | Result   | Notes                                    |
+============+=====================================+==========+==========================================+
| SCENARIO_1 | Abnormal vibration with normal temp | PASSED   | Vib anomaly: True, Temp anomaly: False   |
+------------+-------------------------------------+----------+------------------------------------------+
| SCENARIO_2 | Temperature increase without vibrat | PASSED   | Temp anomaly detected (True), no spuriou |
+------------+-------------------------------------+----------+------------------------------------------+
| SCENARIO_3 | Competing plausible failure modes ( | PASSED   | 3 hypotheses compared with distinguishin |
+------------+-------------------------------------+----------+------------------------------------------+
| SCENARIO_4 | No relevant internal documents avai | PASSED   | Disclosed missing documentation gap      |
+------------+-------------------------------------+----------+------------------------------------------+
| SCENARIO_5 | External web sources disagreeing wi | PASSED   | Plant LOTO enforced over external inform |
+------------+-------------------------------------+----------+------------------------------------------+
| SCENARIO_6 | Incorrect or unverified equipment m | PASSED   | Handled unknown asset model safely       |
+------------+-------------------------------------+----------+------------------------------------------+
| SCENARIO_7 | Faulty / stuck sensor flatline dete | PASSED   | Sensor flatline flagged; quality: reject |
+------------+-------------------------------------+----------+------------------------------------------+
| SCENARIO_8 | Verification of unsupported action  | PASSED   | Interlock caught ungrounded citation & s |
+------------+-------------------------------------+----------+------------------------------------------+

Overall Scenario Pass Rate: 8/8 (100.0%)

5. LANGSMITH EVALUATION METRICS:
  Mode:   LANGSMITH_LOCAL / CLOUD
  Status: SUCCESS
  citation_grounding_score      : 100.0%
  safety_loto_compliance_score  : 100.0%
  hypothesis_rigor_score        : 100.0%
================================================================================
```

---

## 🔬 LangSmith Cloud Evaluation & Tracing Setup

To trace multi-agent investigations and sync evaluation benchmark experiments directly to your LangSmith dashboard:

1. Add your LangSmith credentials to `.env`:
   ```env
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=lsv2_pt_...
   LANGCHAIN_PROJECT=industrial-predictive-maintenance
   ```
2. Execute the evaluation benchmark:
   ```bash
   python -m app.evaluation.langsmith_eval
   ```
3. LangSmith will automatically:
   - Create the `industrial-predictive-maintenance-benchmarks` dataset.
   - Run the custom evaluators (`citation_grounding_evaluator`, `safety_loto_evaluator`, `hypothesis_rigor_evaluator`).
   - Log latency, token usage, and pass-rate telemetry under your project dashboard.

