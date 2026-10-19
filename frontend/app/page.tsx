'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Navbar } from '../components/Navbar';
import { AssetSelector } from '../components/AssetSelector';
import { InvestigationConsole } from '../components/InvestigationConsole';
import { TelemetryCharts } from '../components/TelemetryCharts';
import { EvidenceMatrix } from '../components/EvidenceMatrix';
import { KnowledgeBase } from '../components/KnowledgeBase';
import {
  getHealth,
  getAssets,
  getScenarios,
  getTelemetry,
  getDocuments,
  runInvestigation,
  submitApproval,
} from '../lib/api';
import {
  AssetInfo,
  Scenario,
  TelemetryResponse,
  InvestigationResult,
  DocumentItem,
  ApprovalPayload,
} from '../lib/types';
import { AlertCircle, CheckCircle } from 'lucide-react';

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<'console' | 'telemetry' | 'evidence' | 'knowledge'>('console');
  const [systemHealthy, setSystemHealthy] = useState<boolean | null>(null);

  const [assets, setAssets] = useState<AssetInfo[]>([]);
  const [selectedAssetId, setSelectedAssetId] = useState<string>('P-104');

  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('scenario_1');
  const [userQuestion, setUserQuestion] = useState<string>('');

  const [telemetryData, setTelemetryData] = useState<TelemetryResponse | null>(null);
  const [loadingTelemetry, setLoadingTelemetry] = useState<boolean>(false);

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [investigating, setInvestigating] = useState<boolean>(false);
  const [investigationResult, setInvestigationResult] = useState<InvestigationResult | null>(null);
  const [approving, setApproving] = useState<boolean>(false);

  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4500);
  };

  // 1. Initial Load of Assets, Scenarios, Health, Documents
  useEffect(() => {
    async function initData() {
      try {
        const [healthRes, assetsRes, scenariosRes, docsRes] = await Promise.allSettled([
          getHealth(),
          getAssets(),
          getScenarios(),
          getDocuments(),
        ]);

        if (healthRes.status === 'fulfilled') {
          setSystemHealthy(healthRes.value.status === 'healthy');
        } else {
          setSystemHealthy(false);
        }

        if (assetsRes.status === 'fulfilled' && assetsRes.value.length > 0) {
          setAssets(assetsRes.value);
        }

        if (scenariosRes.status === 'fulfilled' && scenariosRes.value.length > 0) {
          setScenarios(scenariosRes.value);
          const firstSc = scenariosRes.value[0];
          setSelectedScenarioId(firstSc.id);
          setUserQuestion(firstSc.question);
        }

        if (docsRes.status === 'fulfilled') {
          setDocuments(docsRes.value);
        }
      } catch (err) {
        console.error('Failed to initialize dashboard:', err);
      }
    }

    initData();
  }, []);

  // Current fault type helper
  const getCurrentFaultType = useCallback(() => {
    const sc = scenarios.find((s) => s.id === selectedScenarioId);
    return sc ? sc.fault_type : 'INNER_RACE_FAULT';
  }, [scenarios, selectedScenarioId]);

  // 2. Fetch Telemetry whenever Asset or Scenario changes
  const fetchTelemetryData = useCallback(async () => {
    setLoadingTelemetry(true);
    try {
      const faultType = getCurrentFaultType();
      const res = await getTelemetry(selectedAssetId, faultType);
      setTelemetryData(res);
    } catch (err: any) {
      console.error('Telemetry fetch error:', err);
      showToast(`Telemetry fetch error: ${err.message}`, 'error');
    } finally {
      setLoadingTelemetry(false);
    }
  }, [selectedAssetId, getCurrentFaultType]);

  useEffect(() => {
    fetchTelemetryData();
  }, [fetchTelemetryData]);

  // Handle Scenario Selection
  const handleSelectScenario = (scenario: Scenario | null) => {
    if (scenario) {
      setSelectedScenarioId(scenario.id);
      setSelectedAssetId(scenario.asset_id);
      setUserQuestion(scenario.question);
    } else {
      setSelectedScenarioId('custom');
      setUserQuestion('');
    }
  };

  // Launch Multi-Agent Investigation
  const handleRunInvestigation = async () => {
    if (!userQuestion.trim()) {
      showToast('Please provide a symptom description.', 'error');
      return;
    }

    setInvestigating(true);
    try {
      const faultType = getCurrentFaultType();
      const res = await runInvestigation(selectedAssetId, userQuestion, faultType);
      setInvestigationResult(res);
      showToast('Investigation complete! Grounded evidence compiled and verified.', 'success');
    } catch (err: any) {
      console.error('Investigation error:', err);
      showToast(`Investigation failed: ${err.message}`, 'error');
    } finally {
      setInvestigating(false);
    }
  };

  // Submit Human Sign-off
  const handleSubmitApproval = async (payload: ApprovalPayload) => {
    if (!investigationResult) return;
    setApproving(true);
    try {
      const res = await submitApproval(investigationResult.investigation_id, payload);
      setInvestigationResult((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          approval_status: res.approval_status,
          state: {
            ...prev.state,
            approval_status: res.approval_status,
            engineer_notes: res.audit_entry,
          },
        };
      });
      showToast(`Sign-off recorded: [${payload.decision}] by ${payload.engineer_name}`, 'success');
    } catch (err: any) {
      console.error('Approval submission error:', err);
      showToast(`Approval failed: ${err.message}`, 'error');
    } finally {
      setApproving(false);
    }
  };

  const latestVib = telemetryData?.telemetry.slice(-1)[0]?.vibration_rms || 1.8;
  const latestTemp = telemetryData?.telemetry.slice(-1)[0]?.temperature || 62.5;

  return (
    <div className="min-h-screen flex flex-col bg-[#090d16] text-slate-100 industrial-grid">
      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 rounded-xl bg-slate-900 border border-slate-700 shadow-xl text-xs font-mono animate-in fade-in slide-in-from-bottom-2">
          {toast.type === 'success' ? (
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-400" />
          )}
          <span className="text-slate-100">{toast.message}</span>
        </div>
      )}

      {/* Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        systemHealthy={systemHealthy}
        activeAssetId={selectedAssetId}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Asset & Scenario Switcher Bar */}
        <AssetSelector
          assets={assets}
          selectedAssetId={selectedAssetId}
          onSelectAsset={setSelectedAssetId}
          scenarios={scenarios}
          selectedScenarioId={selectedScenarioId}
          onSelectScenario={handleSelectScenario}
        />

        {/* Dynamic Tab Views */}
        {activeTab === 'console' && (
          <InvestigationConsole
            question={userQuestion}
            setQuestion={setUserQuestion}
            investigating={investigating}
            onRunInvestigation={handleRunInvestigation}
            result={investigationResult}
            onSubmitApproval={handleSubmitApproval}
            approving={approving}
            latestVibration={latestVib}
            latestTemperature={latestTemp}
          />
        )}

        {activeTab === 'telemetry' && (
          <TelemetryCharts
            data={telemetryData}
            loading={loadingTelemetry}
            onRefresh={fetchTelemetryData}
          />
        )}

        {activeTab === 'evidence' && (
          <EvidenceMatrix
            evidence={investigationResult?.state?.merged_evidence || []}
          />
        )}

        {activeTab === 'knowledge' && (
          <KnowledgeBase documents={documents} />
        )}
      </main>

      {/* Subtle Engineering Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/80 py-4 px-6 text-center text-slate-500 text-xs font-mono">
        ApexReliability Multi-Agent System · ISO 10816-3 · OSHA 1910.147 LOTO Interlocks · CWRU Benchmarked
      </footer>
    </div>
  );
}
