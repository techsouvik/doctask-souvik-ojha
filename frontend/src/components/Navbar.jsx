import React, { useState } from 'react';
import { 
  Layers, 
  Play, 
  Search, 
  Settings as SettingsIcon, 
  Plus, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  RefreshCw 
} from 'lucide-react';

export default function Navbar({
  projectId,
  projectsList,
  onSelectProject,
  onCreateProjectOpen,
  pipelineStatus,
  currentNode,
  pendingCount,
  isRunningPipeline,
  onRunPipeline,
  onOpenSearch,
  onOpenSettings,
  activeTab,
  onSelectTab
}) {
  const getStatusBadge = () => {
    if (isRunningPipeline) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
          <RefreshCw className="w-3 h-3 animate-spin text-indigo-400" />
          Processing ({currentNode})
        </span>
      );
    }
    if (pipelineStatus === 'AWAITING_HUMAN_GATE') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">
          <AlertTriangle className="w-3 h-3 text-amber-400" />
          Gate Paused ({pendingCount} Pending)
        </span>
      );
    }
    if (pipelineStatus === 'COMPLETED' || pipelineStatus === 'GATE_APPROVED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          Reconciled (Deliverable Ready)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
        <Clock className="w-3 h-3 text-slate-400" />
        {currentNode || 'Ready'}
      </span>
    );
  };

  const tabs = [
    { id: 'chat', label: 'AI Agent Chat' },
    { id: 'findings', label: `Gate Findings ${pendingCount > 0 ? `(${pendingCount})` : ''}` },
    { id: 'pipeline', label: 'LangGraph Pipeline' },
    { id: 'documents', label: 'Document Pile' },
    { id: 'register', label: 'Reconciled Register' },
    { id: 'graph', label: 'Knowledge Graph' },
  ];

  return (
    <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800/80 px-4 py-2.5 transition-all">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Brand & Project Switcher */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25 border border-indigo-400/30">
              <Layers className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-100 text-base tracking-tight">DocuMesh</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-indigo-500/15 text-indigo-400 border border-indigo-500/25">v1.2</span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">Agentic Document Reconciliation Engine</p>
            </div>
          </div>

          <div className="h-6 w-px bg-slate-800 mx-1 hidden sm:block" />

          {/* Project Workspace Selector */}
          <div className="flex items-center gap-1.5 bg-slate-950/80 border border-slate-800 rounded-lg p-1">
            <select
              value={projectId}
              onChange={(e) => onSelectProject(e.target.value)}
              className="bg-transparent text-xs text-slate-200 font-medium px-2 py-1 outline-none cursor-pointer border-none"
            >
              {projectsList.map((p) => (
                <option key={p} value={p} className="bg-slate-900 text-slate-200">
                  {p.replace(/^proj_/, '').replace(/_/g, ' ').toUpperCase()}
                </option>
              ))}
            </select>
            <button
              onClick={onCreateProjectOpen}
              title="Create New Workspace"
              className="p-1 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded transition"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="hidden lg:block">
            {getStatusBadge()}
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto py-1 scrollbar-none">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onSelectTab(tab.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Actions (Run Pipeline, Cmd+K, Settings) */}
        <div className="flex items-center gap-2">
          <button
            onClick={onRunPipeline}
            disabled={isRunningPipeline}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white transition shadow-sm shadow-emerald-600/20"
          >
            {isRunningPipeline ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-current" />
            )}
            <span>{isRunningPipeline ? 'Running...' : 'Run Audit'}</span>
          </button>

          <button
            onClick={onOpenSearch}
            className="hidden sm:flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs bg-slate-800/80 hover:bg-slate-800 text-slate-300 border border-slate-700/60 transition"
          >
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <span>Search</span>
            <kbd className="text-[10px] bg-slate-900 text-slate-400 px-1 py-0.5 rounded border border-slate-700 font-mono">⌘K</kbd>
          </button>

          <button
            onClick={onOpenSettings}
            title="Configure LLM & Providers"
            className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700/60 transition"
          >
            <SettingsIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
