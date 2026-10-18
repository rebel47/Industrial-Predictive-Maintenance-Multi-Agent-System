import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime

from app.graph.workflow import investigation_app
from app.agents.supervisor import SupervisorAgent, ASSET_REGISTRY
from app.analytics.dataset_loader import generate_telemetry_history, generate_cwru_benchmark_signals
from app.rag.ingestion import load_all_industrial_documents, DOCS_DIR

st.set_page_config(
    page_title="Industrial Predictive Maintenance AI",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for industrial engineering aesthetic
st.markdown("""
<style>
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .badge-critical {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85em;
    }
    .badge-warning {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85em;
    }
    .badge-good {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85em;
    }
    .loto-badge {
        background-color: #dc2626;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- Sidebar -----------------
st.sidebar.image("https://img.icons8.com/color/96/engine.png", width=64)
st.sidebar.title("Asset Health Monitor")
st.sidebar.caption("Industrial Rotating Machinery Multi-Agent System")

selected_asset = st.sidebar.selectbox("Select Plant Asset:", list(ASSET_REGISTRY.keys()), index=0)
asset_details = ASSET_REGISTRY[selected_asset]

st.sidebar.markdown(f"""
**Model**: `{asset_details['model']}`  
**Driver**: `{asset_details['driver']}`  
**DE Bearing**: `{asset_details['de_bearing']}`  
**Classification**: `{asset_details['iso_class']}`  
""")

st.sidebar.divider()
st.sidebar.subheader("Incident Scenarios")
scenario = st.sidebar.radio(
    "Load Preset Incident:",
    [
        "Scenario 1: High Vibration & Overheating (Inner Race Defect)",
        "Scenario 2: Dynamic Coupling Misalignment (2X Harmonic)",
        "Scenario 3: Lubrication Starvation (Rapid Thermal Spike)",
        "Scenario 4: Normal Operational Baseline",
        "Custom Incident Query"
    ]
)

# Determine defaults based on scenario
if "Scenario 1" in scenario:
    default_q = "The motor on Pump P-104 is vibrating more than usual, its temperature has increased, and the machine has started making an unusual noise. What is likely wrong, and what should we do?"
    fault_type = "INNER_RACE_FAULT"
elif "Scenario 2" in scenario:
    default_q = "Pump P-102 is vibrating heavily with a deep humming sound. Temperature is within normal limits but vibration has doubled."
    fault_type = "MISALIGNMENT"
elif "Scenario 3" in scenario:
    default_q = "Bearing temperature on P-104 has spiked past 85°C within 30 minutes, but vibration RMS is only moderately elevated."
    fault_type = "LUBRICATION_FAILURE"
elif "Scenario 4" in scenario:
    default_q = "Routine shift health check for Pump P-104. Are all vibration and temperature levels within ISO normal limits?"
    fault_type = "NORMAL"
else:
    default_q = ""
    fault_type = "INNER_RACE_FAULT"

st.sidebar.divider()
openai_key = os.getenv("OPENAI_API_KEY", "").strip()
if openai_key and openai_key != "your_openai_api_key_here":
    st.sidebar.success(f"OpenAI GPT ({os.getenv('OPENAI_MODEL', 'gpt-4o')}) Active")
else:
    st.sidebar.info("Offline / Grounded Industrial Mode (Add OPENAI_API_KEY in .env for live GPT)")

ls_key = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
if ls_key and ls_key.strip() != "your_langsmith_api_key_here":
    st.sidebar.success(f"LangSmith Tracing Active ({os.getenv('LANGCHAIN_PROJECT', 'industrial-predictive-maintenance')})")
else:
    st.sidebar.caption("LangSmith Tracing: Inactive (Add LANGCHAIN_API_KEY in .env)")


# ----------------- Main Interface -----------------
st.title("Industrial Predictive Maintenance & Root-Cause Analysis")
st.caption("Deterministic Numerical Analytics · Hybrid RAG · External Web Research · LangGraph Multi-Agent Orchestration · Safety Verification")

tabs = st.tabs([
    "🔍 Fault Investigation & Planning",
    "📊 Vibration & Telemetry Spectrum",
    "📚 Grounded Evidence Matrix",
    "📑 Industrial Documents & SOPs"
])

# Initialize Session State
if "investigation_result" not in st.session_state:
    st.session_state.investigation_result = None
if "current_telemetry" not in st.session_state:
    st.session_state.current_telemetry = generate_telemetry_history(selected_asset, fault_type=fault_type)

# ----------------- TAB 1: Fault Investigation -----------------
with tabs[0]:
    st.subheader("Technician Incident Console")
    
    col_input, col_meta = st.columns([3, 1])
    with col_input:
        user_question = st.text_area(
            "Reported Fault / Symptoms:",
            value=default_q,
            height=85,
            placeholder="Describe the observed vibration, temperature, acoustic noises, or abnormal machine behavior..."
        )
    with col_meta:
        st.write("")
        st.write("")
        run_btn = st.button("🚀 Launch Multi-Agent Investigation", use_container_width=True, type="primary")
        gen_new_telemetry = st.button("🔄 Refresh Telemetry Stream", use_container_width=True)
        if gen_new_telemetry:
            st.session_state.current_telemetry = generate_telemetry_history(selected_asset, fault_type=fault_type)
            st.toast("Generated fresh 60-minute telemetry stream!")

    if run_btn:
        if not user_question.strip():
            st.warning("Please enter a technician symptom or question.")
        else:
            with st.spinner("Multi-Agent State Machine executing: Analytics -> RAG -> Web -> Root-Cause -> Planning -> Safety Verification..."):
                # Always pass the active telemetry dataframe
                telemetry_data = {"dataframe": st.session_state.current_telemetry}
                initial_state = SupervisorAgent.initialize_investigation(
                    user_question=user_question,
                    asset_id=selected_asset,
                    telemetry_data=telemetry_data
                )
                config = {"configurable": {"thread_id": initial_state["investigation_id"]}}
                result = investigation_app.invoke(initial_state, config=config)
                st.session_state.investigation_result = result
                st.success("Investigation complete! Grounded evidence compiled and verified.")

    # Display Results if Available
    res = st.session_state.investigation_result
    if res:
        st.divider()
        inv_id = res.get("investigation_id")
        verif = res.get("verification_details", {})
        findings = res.get("sensor_findings", {})
        hypotheses = res.get("hypotheses", [])
        plan = res.get("maintenance_plan", {})

        st.subheader(f"Diagnostic Findings: {inv_id}")
        
        # Summary KPI Cards
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            iso = findings.get("iso_severity", {})
            iso_zone = iso.get("zone", "N/A")
            iso_sev = iso.get("severity", "N/A").upper()
            rms_val = iso.get("vibration_rms_mm_s", 0.0)
            st.metric("Vibration Velocity", f"{rms_val:.2f} mm/s", delta=f"{iso_zone} ({iso_sev})", delta_color="inverse" if "D" in iso_zone else "normal")
            
        with col2:
            latest_temp = float(st.session_state.current_telemetry["temperature"].iloc[-1])
            temp_delta = "+15.2°C" if latest_temp > 75 else "+0.8°C"
            st.metric("Bearing Temperature", f"{latest_temp:.1f} °C", delta=temp_delta, delta_color="inverse" if latest_temp > 75 else "normal")

        with col3:
            ml_res = findings.get("ml_classification", {})
            pred_cls = ml_res.get("predicted_class", "NORMAL")
            conf = ml_res.get("confidence", 0.0) * 100
            st.metric("CWRU Classifier", pred_cls, delta=f"{conf:.1f}% conf")

        with col4:
            v_status = res.get("verification_status", "PENDING")
            badge = "✅ PASSED" if v_status == "PASSED" else "⚠️ WARNING"
            st.metric("Safety Verification", badge, delta=f"{len(res.get('merged_evidence', []))} citations")

        with col5:
            app_status = res.get("approval_status", "PENDING")
            st.metric("Engineer Approval", app_status, delta="Sign-off required")

        # Hypotheses Comparison
        st.markdown("### 🧬 Competing Root-Cause Hypotheses Comparison")
        hyp_cols = st.columns(len(hypotheses)) if hypotheses else [st]
        for idx, hyp in enumerate(hypotheses):
            with hyp_cols[idx]:
                status_color = "#dcfce7" if hyp["status"] == "supported" else ("#fef3c7" if hyp["status"] == "plausible" else "#fee2e2")
                st.markdown(f"""
                <div style="background-color: {status_color}; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                    <h4 style="margin: 0; text-transform: uppercase;">{hyp['failure_mode'].replace('_', ' ')}</h4>
                    <p style="margin: 4px 0 0 0; font-weight: bold;">Status: {hyp['status'].upper()}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"**Supporting Evidence:** `{', '.join(hyp['supporting_evidence_ids']) if hyp['supporting_evidence_ids'] else 'None'}`")
                st.markdown(f"**Contradicting Evidence:** `{', '.join(hyp['contradicting_evidence_ids']) if hyp['contradicting_evidence_ids'] else 'None'}`")
                with st.expander("Diagnostic Rationale"):
                    st.write(hyp["explanation"])
                with st.expander("Required Distinguishing Tests"):
                    for t in hyp.get("missing_tests", []):
                        st.markdown(f"- 🧪 {t}")

        # Maintenance Action Plan
        st.markdown("### 🛠️ Prioritized Maintenance Action Plan & Safety Procedures")
        st.caption(f"**Plan Title**: {plan.get('plan_title', 'Action Plan')} | **Sign-off Role**: `{plan.get('required_signoff_role')}`")

        for action in plan.get("actions", []):
            requires_loto = action.get("requires_loto", False)
            loto_html = '<span class="loto-badge">🔒 MANDATORY LOTO (SOP-042)</span>' if requires_loto else '<span style="color: gray;">ℹ️ Standard Precaution</span>'
            urgency_badge = '<span class="badge-critical">IMMEDIATE</span>' if action.get("urgency") == "immediate" else '<span class="badge-warning">SCHEDULED</span>'
            
            with st.container():
                st.markdown(f"""
                **Step {action.get('step_order')}: {action.get('action')}**  
                {urgency_badge} &nbsp; {loto_html} &nbsp; | &nbsp; **Citations:** `{', '.join(action.get('evidence_references', []))}`
                """, unsafe_allow_html=True)
                
                c_haz, c_parts = st.columns([1, 1])
                with c_haz:
                    st.markdown(f"*Safety Hazards:* {', '.join(action.get('safety_hazards', []))}")
                with c_parts:
                    st.markdown(f"*Required Spares / Tools:* {', '.join(action.get('parts_to_verify', []))}")
                st.divider()

        # Human Engineer Approval Sign-off Box
        st.markdown("### ✍️ Human-in-the-Loop Engineering Sign-off & Audit Trail")
        with st.form("approval_form"):
            col_sign1, col_sign2 = st.columns(2)
            with col_sign1:
                eng_name = st.text_input("Reviewing Engineer Name:", value="Marcus Vance, PE")
                eng_role = st.selectbox("Role / Certification:", [
                    "Certified Vibration Analyst (ISO Cat III)",
                    "Plant Reliability Engineering Lead",
                    "Senior Mechanical Maintenance Supervisor"
                ])
            with col_sign2:
                decision = st.radio("Approval Decision:", ["APPROVED", "REJECTED"], horizontal=True)
                comments = st.text_input("Audited Comments / Specific Instructions:", value="Verified SKF 6205 bearing availability in warehouse. LOTO padlocks assigned. Work permit issued.")

            submit_sign = st.form_submit_button("Submit Formal Sign-off")
            if submit_sign:
                res["approval_status"] = decision
                audit_stamp = f"[{decision}] on {datetime.now().strftime('%Y-%m-%d %H:%M')} by {eng_name} ({eng_role}): {comments}"
                res["engineer_notes"] = audit_stamp
                st.session_state.investigation_result = res
                st.success(f"Audit record recorded: {audit_stamp}")

# ----------------- TAB 2: Vibration & Telemetry Spectrum -----------------
with tabs[1]:
    st.subheader("Asset Telemetry Stream & FFT Vibration Spectrum Analysis")
    df_telemetry = st.session_state.current_telemetry

    col_vib_plot, col_temp_plot = st.columns(2)
    with col_vib_plot:
        fig_vib, ax_vib = plt.subplots(figsize=(7, 3.2))
        ax_vib.plot(df_telemetry["vibration_rms"], color="#dc2626", label="Vibration RMS (mm/s)")
        ax_vib.axhline(2.8, color="#f59e0b", linestyle="--", label="ISO Zone C Alert (2.8 mm/s)")
        ax_vib.axhline(4.5, color="#7f1d1d", linestyle="--", label="ISO Zone D Trip (4.5 mm/s)")
        ax_vib.set_title("Vibration Velocity Trend (ISO 10816-3)")
        ax_vib.set_ylabel("mm/s RMS")
        ax_vib.set_xlabel("Time (Minutes)")
        ax_vib.grid(True, alpha=0.3)
        ax_vib.legend(loc="upper left", fontsize=8)
        st.pyplot(fig_vib)

    with col_temp_plot:
        fig_temp, ax_temp = plt.subplots(figsize=(7, 3.2))
        ax_temp.plot(df_telemetry["temperature"], color="#ea580c", label="Bearing Temp (°C)")
        ax_temp.axhline(75.0, color="#f59e0b", linestyle="--", label="Warning (75°C)")
        ax_temp.axhline(85.0, color="#dc2626", linestyle="--", label="Trip Limit (85°C)")
        ax_temp.set_title("Bearing Housing Temperature (°C)")
        ax_temp.set_ylabel("Temperature (°C)")
        ax_temp.set_xlabel("Time (Minutes)")
        ax_temp.grid(True, alpha=0.3)
        ax_temp.legend(loc="upper left", fontsize=8)
        st.pyplot(fig_temp)

    # FFT Spectral Analysis
    st.markdown("#### High-Resolution Vibration Spectrum (FFT)")
    cwru_signals = generate_cwru_benchmark_signals()
    active_waveform = cwru_signals.get(fault_type, cwru_signals["INNER_RACE_FAULT"])
    
    # Compute FFT for display
    fs = 12000
    n = len(active_waveform)
    fft_y = np.abs(np.fft.rfft(active_waveform * np.hanning(n))) * (2.0 / n)
    fft_x = np.fft.rfftfreq(n, 1.0 / fs)
    
    # Zoom in to 0 - 500 Hz
    mask = (fft_x <= 500)
    fig_fft, ax_fft = plt.subplots(figsize=(14, 3.5))
    ax_fft.plot(fft_x[mask], fft_y[mask], color="#2563eb", linewidth=1.2, label="Vibration Spectrum")
    
    # Mark characteristic frequencies
    fr = 1750 / 60.0
    ax_fft.axvline(fr, color="#10b981", linestyle=":", label=f"1X Shaft ({fr:.1f} Hz)")
    ax_fft.axvline(2 * fr, color="#8b5cf6", linestyle=":", label=f"2X Misalignment ({2*fr:.1f} Hz)")
    ax_fft.axvline(5.415 * fr, color="#ef4444", linestyle="--", label=f"BPFI Inner Race ({5.415*fr:.1f} Hz)")
    ax_fft.axvline(3.585 * fr, color="#f97316", linestyle="--", label=f"BPFO Outer Race ({3.585*fr:.1f} Hz)")

    ax_fft.set_title(f"Frequency Spectrum Analysis (0 - 500 Hz) - {selected_asset}")
    ax_fft.set_xlabel("Frequency (Hz)")
    ax_fft.set_ylabel("Amplitude (g)")
    ax_fft.legend(loc="upper right", fontsize=9)
    ax_fft.grid(True, alpha=0.3)
    st.pyplot(fig_fft)

# ----------------- TAB 3: Evidence Matrix -----------------
with tabs[2]:
    st.subheader("Consolidated Multi-Source Evidence Package")
    st.caption("Numerical Telemetry · Internal OEM Manuals & Incident Logs · External Manufacturer Bulletins")

    if res and res.get("merged_evidence"):
        ev_items = res["merged_evidence"]
        for ev in ev_items:
            ev_id = ev["evidence_id"]
            ev_type = ev["source_type"].upper()
            color = "#dbeafe" if ev_type == "SENSOR" else ("#fef9c3" if ev_type == "INTERNAL" else "#f3e8ff")
            
            st.markdown(f"""
            <div style="background-color: {color}; border-left: 5px solid #3b82f6; padding: 12px; border-radius: 4px; margin-bottom: 10px;">
                <span style="font-weight: bold; font-family: monospace;">[{ev_id}]</span> 
                <span style="background-color: #ffffff; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; font-weight: bold;">{ev_type}</span>
                <span style="color: #4b5563; font-size: 0.9em; margin-left: 8px;">Source: <strong>{ev['source_reference']}</strong></span>
                <p style="margin: 6px 0 2px 0;">{ev['claim']}</p>
                <div style="font-size: 0.8em; color: #374151;">
                    <strong>Supports:</strong> <code>{', '.join(ev['supports']) if ev['supports'] else 'None'}</code> &nbsp;|&nbsp;
                    <strong>Contradicts:</strong> <code>{', '.join(ev['contradicts']) if ev['contradicts'] else 'None'}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Run an investigation in Tab 1 to populate the grounded evidence package.")

# ----------------- TAB 4: Documents & SOPs -----------------
with tabs[3]:
    st.subheader("Plant Engineering Knowledge Base & Standard Operating Procedures")
    all_docs = load_all_industrial_documents(DOCS_DIR)
    
    doc_titles = sorted(list({d.title for d in all_docs}))
    selected_doc_title = st.selectbox("Select Technical Document:", doc_titles)
    
    matching_chunks = [d for d in all_docs if d.title == selected_doc_title]
    if matching_chunks:
        first_chunk = matching_chunks[0]
        st.markdown(f"**Document ID**: `{first_chunk.document_id}` | **Type**: `{first_chunk.document_type}` | **Applicability**: `{first_chunk.equipment_model}`")
        st.divider()
        
        for c in matching_chunks:
            with st.expander(f"📌 Section: {c.section}"):
                st.markdown(c.content)
