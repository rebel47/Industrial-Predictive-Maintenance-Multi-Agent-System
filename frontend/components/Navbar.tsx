'use client';

import React from 'react';
import { Activity, ShieldAlert, Cpu, Database, BookOpen, Layers } from 'lucide-react';

interface NavbarProps {
  activeTab: 'console' | 'telemetry' | 'evidence' | 'knowledge';
  setActiveTab: (tab: 'console' | 'telemetry' | 'evidence' | 'knowledge') => void;
  systemHealthy: boolean | null;
  activeAssetId: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  systemHealthy,
  activeAssetId,
}) => {
  const tabs = [
    { id: 'console', label: 'Fault Investigation', icon: Cpu },
    { id: 'telemetry', label: 'Telemetry & Spectrum', icon: Activity },
    { id: 'evidence', label: 'Evidence Matrix', icon: Database },
    { id: 'knowledge', label: 'Knowledge Base & SOPs', icon: BookOpen },
  ] as const;

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm tracking-wide text-white uppercase">
                  ApexReliability AI
                </span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-blue-400 border border-slate-700">
                  v1.0 Multi-Agent
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Predictive Maintenance & Root-Cause Engineering
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-1 bg-slate-950/60 p-1 rounded-lg border border-slate-800">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Status Indicator */}
          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300 font-mono">
              <span className="text-slate-400">Target:</span>
              <span className="text-emerald-400 font-semibold">{activeAssetId}</span>
            </div>

            <div className="flex items-center gap-1.5 text-xs font-mono">
              <span
                className={`w-2 h-2 rounded-full ${
                  systemHealthy === null
                    ? 'bg-amber-400 animate-pulse'
                    : systemHealthy
                    ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]'
                    : 'bg-rose-500'
                }`}
              />
              <span className="text-slate-400 text-[11px] hidden sm:inline">
                {systemHealthy === null
                  ? 'Connecting...'
                  : systemHealthy
                  ? 'API Online'
                  : 'API Offline'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
