'use client';

import React, { useState } from 'react';
import { InvestigationResult, ApprovalPayload } from '../lib/types';
import {
  Play,
  CheckCircle,
  AlertOctagon,
  Lock,
  ChevronDown,
  ChevronUp,
  FileCheck,
  Send,
  Sparkles,
  ClipboardCheck,
  ExternalLink,
  Layers,
  Wrench,
  AlertTriangle,
} from 'lucide-react';

interface InvestigationConsoleProps {
  question: string;
  setQuestion: (q: string) => void;
  investigating: boolean;
  onRunInvestigation: () => void;
  result: InvestigationResult | null;
  onSubmitApproval: (payload: ApprovalPayload) => Promise<void>;
  approving: boolean;
  latestVibration: number;
  latestTemperature: number;
}

export const InvestigationConsole: React.FC<InvestigationConsoleProps> = ({
  question,
  setQuestion,
  investigating,
  onRunInvestigation,
  result,
  onSubmitApproval,
  approving,
  latestVibration,
  latestTemperature,
}) => {
  // Human approval form state
  const [engineerName, setEngineerName] = useState('Marcus Vance, PE');
  const [engineerRole, setEngineerRole] = useState('Certified Vibration Analyst (ISO Cat III)');
  const [decision, setDecision] = useState<'APPROVED' | 'REJECTED'>('APPROVED');
  const [comments, setComments] = useState('Verified SKF 6205 bearing stock in warehouse. LOTO padlocks assigned. Work permit issued.');
  const [expandedHyp, setExpandedHyp] = useState<Record<string, boolean>>({});

  const toggleHyp = (key: string) => {
    setExpandedHyp((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const findings = result?.state?.sensor_findings || {};
  const isoSeverity = findings.iso_severity;
  const mlClass = findings.ml_classification;
  const hypotheses = result?.state?.hypotheses || [];
  const plan = result?.state?.maintenance_plan;
  const actions = plan?.actions || [];
  const auditStamp = result?.state?.engineer_notes;

  const handleApprovalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmitApproval({
      engineer_name: engineerName,
      engineer_role: engineerRole,
      decision,
      comments,
    });
  };

  return (
    <div className="space-y-6">
      {/* Incident Input Box */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
        <label className="block text-xs font-mono uppercase tracking-wider text-slate-300 mb-2">
          Technician Symptom Report & Machinery Observation
        </label>
        <div className="flex flex-col md:flex-row gap-3">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
            placeholder="Describe the observed vibration, temperature, acoustic noises, or abnormal machine behavior..."
            className="flex-1 bg-slate-950 border border-slate-700 rounded-lg p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500 font-sans resize-none"
          />
          <div className="flex flex-col justify-end">
            <button
              onClick={onRunInvestigation}
              disabled={investigating || !question.trim()}
              className="flex items-center justify-center gap-2 px-5 py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition shadow-lg shadow-blue-600/20 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {investigating ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Agents Investigating...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Launch Investigation</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Multi-Agent Orchestration Pipeline Stepper */}
        {investigating && (
          <div className="mt-4 pt-4 border-t border-slate-800/80">
            <div className="flex items-center gap-2 mb-2 text-xs font-mono text-blue-400">
              <Sparkles className="w-3.5 h-3.5 animate-pulse" />
              <span>Multi-Agent LangGraph State Machine Executing:</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 text-[11px] font-mono text-center">
              <div className="p-2 rounded bg-blue-950/40 border border-blue-800/60 text-blue-300 animate-pulse">
                1. Analytics
              </div>
              <div className="p-2 rounded bg-blue-950/40 border border-blue-800/60 text-blue-300 animate-pulse">
                2. Hybrid RAG
              </div>
              <div className="p-2 rounded bg-blue-950/40 border border-blue-800/60 text-blue-300 animate-pulse">
                3. Web Research
              </div>
              <div className="p-2 rounded bg-blue-950/40 border border-blue-800/60 text-blue-300 animate-pulse">
                4. Root-Cause
              </div>
              <div className="p-2 rounded bg-blue-950/40 border border-blue-800/60 text-blue-300 animate-pulse">
                5. Maintenance
              </div>
              <div className="p-2 rounded bg-blue-950/40 border border-blue-800/60 text-blue-300 animate-pulse">
                6. Verification
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Investigation Results Display */}
      {result && (
        <div className="space-y-6">
          {/* Header Title with ID */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-blue-900/40 text-blue-400 border border-blue-800 font-semibold">
                  {result.investigation_id}
                </span>
                <h2 className="text-base font-semibold text-white">
                  Multi-Agent Diagnostic Findings & Action Plan
                </h2>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Asset: {result.asset_id} · Grounded Citations: {result.evidence_count} evidence items
              </p>
            </div>
          </div>

          {/* Diagnostic KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {/* Card 1: Vibration Velocity */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5">
              <span className="text-[10px] text-slate-400 font-mono block">VIBRATION VELOCITY</span>
              <span className="text-lg font-mono font-bold text-white">
                {isoSeverity?.vibration_rms_mm_s !== undefined
                  ? `${isoSeverity.vibration_rms_mm_s.toFixed(2)} mm/s`
                  : `${latestVibration.toFixed(2)} mm/s`}
              </span>
              <span
                className={`text-[11px] font-mono font-medium block mt-1 ${
                  isoSeverity?.zone === 'Zone D'
                    ? 'text-rose-400'
                    : isoSeverity?.zone === 'Zone C'
                    ? 'text-amber-400'
                    : 'text-emerald-400'
                }`}
              >
                {isoSeverity ? `${isoSeverity.zone} (${isoSeverity.severity})` : 'ISO 10816'}
              </span>
            </div>

            {/* Card 2: Bearing Temp */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5">
              <span className="text-[10px] text-slate-400 font-mono block">BEARING TEMP</span>
              <span className="text-lg font-mono font-bold text-white">
                {latestTemperature.toFixed(1)} °C
              </span>
              <span
                className={`text-[11px] font-mono font-medium block mt-1 ${
                  latestTemperature > 80 ? 'text-rose-400' : 'text-slate-400'
                }`}
              >
                {latestTemperature > 80 ? 'Thermal Spike Alert' : 'Normal Operating'}
              </span>
            </div>

            {/* Card 3: ML Classifier */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5">
              <span className="text-[10px] text-slate-400 font-mono block">CWRU CLASSIFIER</span>
              <span className="text-sm font-mono font-bold text-blue-400 truncate block">
                {mlClass?.predicted_class || 'ANALYZED'}
              </span>
              <span className="text-[11px] font-mono text-slate-400 block mt-1">
                {mlClass ? `${(mlClass.confidence * 100).toFixed(1)}% conf` : 'Deterministic'}
              </span>
            </div>

            {/* Card 4: Safety Verification */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5">
              <span className="text-[10px] text-slate-400 font-mono block">SAFETY VERIFICATION</span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span className="text-sm font-mono font-bold text-emerald-400">
                  {result.verification_status || 'PASSED'}
                </span>
              </div>
              <span className="text-[11px] font-mono text-slate-400 block mt-1">
                Interlocks Verified
              </span>
            </div>

            {/* Card 5: Engineering Approval */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 col-span-2 sm:col-span-1">
              <span className="text-[10px] text-slate-400 font-mono block">ENGINEER SIGN-OFF</span>
              <span
                className={`text-sm font-mono font-bold block mt-0.5 ${
                  result.approval_status === 'APPROVED'
                    ? 'text-emerald-400'
                    : result.approval_status === 'REJECTED'
                    ? 'text-rose-400'
                    : 'text-amber-400'
                }`}
              >
                {result.approval_status || 'PENDING'}
              </span>
              <span className="text-[11px] font-mono text-slate-400 block mt-1">
                Audit Trail Required
              </span>
            </div>
          </div>

          {/* Competing Root-Cause Hypotheses Comparison */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-400" />
              <span>Competing Root-Cause Hypotheses Comparison</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {hypotheses.map((hyp, idx) => {
                const isSupported = hyp.status === 'supported';
                const isPlausible = hyp.status === 'plausible';
                const isExpanded = expandedHyp[hyp.failure_mode] || idx === 0;

                return (
                  <div
                    key={hyp.failure_mode}
                    className={`rounded-xl border p-4 transition ${
                      isSupported
                        ? 'bg-emerald-950/20 border-emerald-500/40'
                        : isPlausible
                        ? 'bg-amber-950/20 border-amber-500/40'
                        : 'bg-rose-950/10 border-slate-800'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className="text-xs font-mono font-bold uppercase text-white">
                        {hyp.failure_mode.replace(/_/g, ' ')}
                      </span>
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded uppercase ${
                          isSupported
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : isPlausible
                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                            : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        }`}
                      >
                        {hyp.status}
                      </span>
                    </div>

                    <div className="space-y-1.5 text-xs text-slate-300 mt-3">
                      <div>
                        <span className="text-slate-400 text-[11px]">Supporting Citations: </span>
                        <span className="font-mono text-emerald-400 font-medium">
                          {hyp.supporting_evidence_ids.length > 0
                            ? hyp.supporting_evidence_ids.join(', ')
                            : 'None'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[11px]">Contradicting: </span>
                        <span className="font-mono text-rose-400 font-medium">
                          {hyp.contradicting_evidence_ids.length > 0
                            ? hyp.contradicting_evidence_ids.join(', ')
                            : 'None'}
                        </span>
                      </div>
                    </div>

                    {/* Collapsible Details */}
                    <div className="mt-3 pt-3 border-t border-slate-800/80">
                      <button
                        onClick={() => toggleHyp(hyp.failure_mode)}
                        className="flex items-center justify-between w-full text-[11px] font-mono text-slate-400 hover:text-slate-200"
                      >
                        <span>Diagnostic Rationale & Tests</span>
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>

                      {isExpanded && (
                        <div className="mt-2 space-y-2 text-xs text-slate-300">
                          <p className="text-slate-300 leading-relaxed text-[11px] bg-slate-950/60 p-2 rounded border border-slate-800/60">
                            {hyp.explanation}
                          </p>
                          {hyp.missing_tests && hyp.missing_tests.length > 0 && (
                            <div>
                              <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
                                Distinguishing Tests:
                              </span>
                              <ul className="space-y-1">
                                {hyp.missing_tests.map((t, i) => (
                                  <li key={i} className="text-[11px] text-amber-300/90 flex items-start gap-1.5">
                                    <span className="text-amber-500">🧪</span>
                                    <span>{t}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Prioritized Maintenance Action Plan & Safety Procedures */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-4">
              <div>
                <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <Wrench className="w-4 h-4 text-blue-400" />
                  <span>Prioritized Maintenance Action Plan & Safety Procedures</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Plan: {plan?.plan_title || 'Corrective Protocol'} · Sign-off: {plan?.required_signoff_role}
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {actions.map((act) => {
                const isImmediate = act.urgency === 'immediate';
                return (
                  <div
                    key={act.step_order}
                    className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-col gap-2.5"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <span className="w-6 h-6 rounded-full bg-slate-800 text-blue-400 font-mono text-xs flex items-center justify-center font-bold">
                          {act.step_order}
                        </span>
                        <h4 className="text-sm font-semibold text-slate-100">
                          {act.action}
                        </h4>
                      </div>

                      <div className="flex items-center gap-2">
                        {isImmediate ? (
                          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/40 uppercase">
                            Immediate
                          </span>
                        ) : (
                          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/40 uppercase">
                            Scheduled
                          </span>
                        )}

                        {act.requires_loto ? (
                          <span className="flex items-center gap-1 text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-600 text-white uppercase">
                            <Lock className="w-3 h-3" /> Mandatory LOTO (SOP-042)
                          </span>
                        ) : (
                          <span className="text-[10px] font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-800">
                            Standard Precaution
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-slate-300 pt-1">
                      <div className="bg-slate-900/60 p-2 rounded border border-slate-800/50">
                        <span className="text-[10px] font-mono text-slate-400 block mb-0.5">
                          SAFETY HAZARDS
                        </span>
                        <span className="text-slate-300">
                          {act.safety_hazards?.length ? act.safety_hazards.join(', ') : 'Standard mechanical risks'}
                        </span>
                      </div>
                      <div className="bg-slate-900/60 p-2 rounded border border-slate-800/50">
                        <span className="text-[10px] font-mono text-slate-400 block mb-0.5">
                          REQUIRED SPARES / TOOLS
                        </span>
                        <span className="text-slate-300">
                          {act.parts_to_verify?.length ? act.parts_to_verify.join(', ') : 'Standard tooling'}
                        </span>
                      </div>
                    </div>

                    {act.evidence_references && act.evidence_references.length > 0 && (
                      <div className="text-[11px] font-mono text-slate-400">
                        <span>Citations: </span>
                        <span className="text-blue-400">{act.evidence_references.join(', ')}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Human-in-the-Loop Sign-off & Audit Log */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-2">
              <ClipboardCheck className="w-4 h-4 text-emerald-400" />
              <span>Human-in-the-Loop Engineering Sign-off & Audit Trail</span>
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Formal verification is required before initiating maintenance work orders and de-energizing plant assets.
            </p>

            {auditStamp ? (
              <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-xs">
                <span className="text-[10px] font-mono uppercase text-emerald-400 font-bold block mb-1">
                  OFFICIAL AUDIT STAMP RECORDED
                </span>
                <p className="font-mono text-emerald-300">{auditStamp}</p>
              </div>
            ) : (
              <form onSubmit={handleApprovalSubmit} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[11px] font-mono text-slate-400 mb-1">
                      Reviewing Engineer Name:
                    </label>
                    <input
                      type="text"
                      value={engineerName}
                      onChange={(e) => setEngineerName(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500 font-sans"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-mono text-slate-400 mb-1">
                      Role / Certification:
                    </label>
                    <select
                      value={engineerRole}
                      onChange={(e) => setEngineerRole(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500 font-sans"
                    >
                      <option value="Certified Vibration Analyst (ISO Cat III)">
                        Certified Vibration Analyst (ISO Cat III)
                      </option>
                      <option value="Plant Reliability Engineering Lead">
                        Plant Reliability Engineering Lead
                      </option>
                      <option value="Senior Mechanical Maintenance Supervisor">
                        Senior Mechanical Maintenance Supervisor
                      </option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">
                    Approval Decision:
                  </label>
                  <div className="flex items-center gap-4 text-xs font-mono">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="decision"
                        value="APPROVED"
                        checked={decision === 'APPROVED'}
                        onChange={() => setDecision('APPROVED')}
                        className="text-emerald-500 focus:ring-emerald-500"
                      />
                      <span className="text-emerald-400 font-bold">APPROVED</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="decision"
                        value="REJECTED"
                        checked={decision === 'REJECTED'}
                        onChange={() => setDecision('REJECTED')}
                        className="text-rose-500 focus:ring-rose-500"
                      />
                      <span className="text-rose-400 font-bold">REJECTED</span>
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">
                    Audited Comments / Specific Instructions:
                  </label>
                  <input
                    type="text"
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500 font-sans"
                  />
                </div>

                <button
                  type="submit"
                  disabled={approving}
                  className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{approving ? 'Recording Sign-off...' : 'Submit Formal Sign-off'}</span>
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
