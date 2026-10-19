'use client';

import React, { useState } from 'react';
import { DocumentItem } from '../lib/types';
import { BookOpen, FileText, ChevronRight, ChevronDown, CheckSquare } from 'lucide-react';

interface KnowledgeBaseProps {
  documents: DocumentItem[];
}

export const KnowledgeBase: React.FC<KnowledgeBaseProps> = ({ documents }) => {
  const [selectedDocId, setSelectedDocId] = useState<string>(
    documents[0]?.document_id || ''
  );
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({});

  const activeDoc = documents.find((d) => d.document_id === selectedDocId) || documents[0];

  const toggleSection = (chunkId: string) => {
    setOpenSections((prev) => ({
      ...prev,
      [chunkId]: !prev[chunkId],
    }));
  };

  if (!documents || documents.length === 0) {
    return (
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
        <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Loading plant engineering documents and SOPs...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-blue-400" />
            <span>Plant Engineering Knowledge Base & Standard Operating Procedures</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Internal OEM Manuals, Bearing Replacement SOPs, LOTO Checklist & Historical Incidents
          </p>
        </div>

        <div className="w-full sm:w-auto">
          <select
            value={activeDoc?.document_id}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-2 font-mono focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
          >
            {documents.map((doc) => (
              <option key={doc.document_id} value={doc.document_id}>
                {doc.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Active Document Details */}
      {activeDoc && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3 mb-3">
              <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" />
                <span>{activeDoc.title}</span>
              </h2>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-blue-900/30 text-blue-400 border border-blue-800 font-semibold">
                {activeDoc.document_id}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs font-mono">
              <div>
                <span className="text-slate-400 block text-[10px]">APPLICABILITY</span>
                <span className="text-slate-200 font-medium">{activeDoc.equipment_model}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">DOCUMENT TYPE</span>
                <span className="text-blue-400 font-medium uppercase">{activeDoc.document_type}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">REVISION DATE</span>
                <span className="text-slate-300 font-medium">{activeDoc.revision_date}</span>
              </div>
            </div>
          </div>

          {/* Sections Accordion */}
          <div className="space-y-3">
            {activeDoc.sections.map((section, idx) => {
              const isOpen = openSections[section.chunk_id] ?? (idx === 0);
              return (
                <div
                  key={section.chunk_id}
                  className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden transition"
                >
                  <button
                    onClick={() => toggleSection(section.chunk_id)}
                    className="w-full flex items-center justify-between p-3.5 text-left hover:bg-slate-800/40 transition"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="w-5 h-5 rounded bg-slate-800 text-blue-400 font-mono text-xs flex items-center justify-center font-bold">
                        {idx + 1}
                      </span>
                      <span className="text-xs font-mono font-semibold text-slate-200">
                        {section.section}
                      </span>
                    </div>
                    {isOpen ? (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    )}
                  </button>

                  {isOpen && (
                    <div className="p-4 pt-1 border-t border-slate-800/80 bg-slate-950/60">
                      <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed font-sans bg-transparent">
                        {section.content}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
