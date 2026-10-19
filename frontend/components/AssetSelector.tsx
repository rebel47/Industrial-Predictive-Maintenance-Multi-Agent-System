'use client';

import React from 'react';
import { AssetInfo, Scenario } from '../lib/types';
import { Settings, Zap, AlertTriangle, ShieldCheck, HelpCircle } from 'lucide-react';

interface AssetSelectorProps {
  assets: AssetInfo[];
  selectedAssetId: string;
  onSelectAsset: (assetId: string) => void;
  scenarios: Scenario[];
  selectedScenarioId: string;
  onSelectScenario: (scenario: Scenario | null) => void;
}

export const AssetSelector: React.FC<AssetSelectorProps> = ({
  assets,
  selectedAssetId,
  onSelectAsset,
  scenarios,
  selectedScenarioId,
  onSelectScenario,
}) => {
  const currentAsset = assets.find((a) => a.asset_id === selectedAssetId) || assets[0];

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 sm:p-5 mb-6 backdrop-blur">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Asset Selection & Meta */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div>
            <label className="block text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">
              Asset Under Monitoring
            </label>
            <div className="relative">
              <select
                value={selectedAssetId}
                onChange={(e) => onSelectAsset(e.target.value)}
                className="bg-slate-950 border border-slate-700 hover:border-slate-600 text-white font-mono font-semibold text-sm rounded-lg px-3.5 py-2 pr-8 appearance-none focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
              >
                {assets.map((asset) => (
                  <option key={asset.asset_id} value={asset.asset_id}>
                    {asset.asset_id} — {asset.model.split(' ')[0]}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-slate-400">
                <Settings className="w-3.5 h-3.5" />
              </div>
            </div>
          </div>

          {/* Asset details pill cards */}
          {currentAsset && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="bg-slate-950/70 border border-slate-800/80 rounded px-2.5 py-1.5">
                <span className="text-[10px] text-slate-400 font-mono block">MODEL</span>
                <span className="font-medium text-slate-200 truncate block max-w-[150px]" title={currentAsset.model}>
                  {currentAsset.model}
                </span>
              </div>
              <div className="bg-slate-950/70 border border-slate-800/80 rounded px-2.5 py-1.5">
                <span className="text-[10px] text-slate-400 font-mono block">DRIVER</span>
                <span className="font-medium text-slate-200 truncate block max-w-[150px]" title={currentAsset.driver}>
                  {currentAsset.driver}
                </span>
              </div>
              <div className="bg-slate-950/70 border border-slate-800/80 rounded px-2.5 py-1.5">
                <span className="text-[10px] text-slate-400 font-mono block">DE BEARING</span>
                <span className="font-mono text-amber-400 font-semibold truncate block">
                  {currentAsset.de_bearing}
                </span>
              </div>
              <div className="bg-slate-950/70 border border-slate-800/80 rounded px-2.5 py-1.5">
                <span className="text-[10px] text-slate-400 font-mono block">ISO 10816 CLASS</span>
                <span className="font-medium text-blue-400 truncate block">
                  {currentAsset.iso_class}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Preset Incident Scenarios Selector */}
        <div className="flex flex-col">
          <label className="block text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">
            Incident Scenarios Preset
          </label>
          <div className="flex flex-wrap gap-1.5">
            {scenarios.map((sc) => {
              const isSelected = selectedScenarioId === sc.id;
              return (
                <button
                  key={sc.id}
                  onClick={() => onSelectScenario(sc)}
                  className={`text-xs px-2.5 py-1.5 rounded-md font-medium transition-all ${
                    isSelected
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'bg-slate-950 text-slate-300 border border-slate-800 hover:border-slate-700 hover:bg-slate-800/50'
                  }`}
                  title={sc.title}
                >
                  {sc.title.split(':')[0]}
                </button>
              );
            })}
            <button
              onClick={() => onSelectScenario(null)}
              className={`text-xs px-2.5 py-1.5 rounded-md font-medium transition-all ${
                selectedScenarioId === 'custom'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-950 text-slate-300 border border-slate-800 hover:border-slate-700 hover:bg-slate-800/50'
              }`}
            >
              Custom Query
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
