'use client';

import React, { useState } from 'react';
import { EvidenceItem } from '../lib/types';
import { Database, Filter, Cpu, BookOpen, Globe, CheckCircle2, XCircle } from 'lucide-react';

interface EvidenceMatrixProps {
  evidence: EvidenceItem[];
}

export const EvidenceMatrix: React.FC<EvidenceMatrixProps> = ({ evidence }) => {
  const [filter, setFilter] = useState<'all' | 'sensor' | 'internal' | 'web'>('all');

  const filteredEvidence = evidence.filter((ev) => {
    if (filter === 'all') return true;
    return ev.source_type.toLowerCase() === filter;
  });

  return (
    <div className="space-y-6">
      {/* Header and Filter Buttons */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
        <div>
          <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200 flex items-center gap-2">
            <Database className="w-4 h-4 text-blue-400" />
            <span>Consolidated Multi-Source Evidence Package</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Numerical Telemetry · Internal OEM Manuals & Incident Logs · External Manufacturer Bulletins
          </p>
        </div>

        <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800">
          {(['all', 'sensor', 'internal', 'web'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`text-xs px-2.5 py-1 rounded-md font-mono transition uppercase ${
                filter === type
                  ? 'bg-blue-600 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Evidence Cards */}
      {filteredEvidence.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
          <Database className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No evidence items matching this filter.</p>
          <p className="text-xs text-slate-500 mt-1">Run an investigation to compile grounded evidence.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredEvidence.map((ev) => {
            const type = ev.source_type.toLowerCase();
            const isSensor = type === 'sensor';
            const isInternal = type === 'internal';
            const isWeb = type === 'web';

            const badgeBg = isSensor
              ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
              : isInternal
              ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
              : 'bg-purple-500/10 text-purple-400 border-purple-500/30';

            const Icon = isSensor ? Cpu : isInternal ? BookOpen : Globe;

            return (
              <div
                key={ev.evidence_id}
                className="bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 rounded-xl p-4 transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-200 px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700">
                        {ev.evidence_id}
                      </span>
                      <span className={`flex items-center gap-1 text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${badgeBg}`}>
                        <Icon className="w-3 h-3" />
                        <span>{ev.source_type}</span>
                      </span>
                    </div>

                    <span className="text-[11px] text-slate-400 truncate max-w-[200px]" title={ev.source_reference}>
                      {ev.source_reference}
                    </span>
                  </div>

                  <p className="text-xs text-slate-200 leading-relaxed bg-slate-950/70 p-3 rounded-lg border border-slate-800/60 mb-3">
                    {ev.claim}
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono">
                  <div className="flex items-center gap-1.5 text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Supports: {ev.supports && ev.supports.length > 0 ? ev.supports.join(', ') : 'None'}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-rose-400">
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Contradicts: {ev.contradicts && ev.contradicts.length > 0 ? ev.contradicts.join(', ') : 'None'}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
