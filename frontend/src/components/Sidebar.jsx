import React, { useState } from 'react';
import { 
  MessageSquare, 
  FileText, 
  AlertTriangle, 
  FileCheck, 
  GitCommit, 
  Network, 
  Plus, 
  Search, 
  Settings as SettingsIcon, 
  Play, 
  RefreshCw, 
  ChevronDown, 
  Trash2,
  Layers,
  CheckCircle2,
  Clock,
  Sparkles,
  PanelLeftClose,
  PanelLeftOpen
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

export default function Sidebar({
  projectId,
  projectsList,
  onSelectProject,
  onCreateProjectOpen,
  activeTab,
  onSelectTab,
  activeTreeId,
  onSelectSession,
  sessions,
  onNewSession,
  onDeleteSession,
  pendingCount,
  docCount,
  pipelineStatus,
  currentNode,
  isRunningPipeline,
  onRunPipeline,
  onOpenSearch,
  onOpenSettings,
  collapsed,
  onToggleCollapse
}) {
  const [projectDropdownOpen, setProjectDropdownOpen] = useState(false);

  const getStatusDot = () => {
    if (isRunningPipeline) {
      return <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping shrink-0" />;
    }
    if (pipelineStatus === 'AWAITING_HUMAN_GATE') {
      return <span className="w-2 h-2 rounded-full bg-amber-400 shrink-0" />;
    }
    if (pipelineStatus === 'COMPLETED' || pipelineStatus === 'GATE_APPROVED') {
      return <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0" />;
    }
    return <span className="w-2 h-2 rounded-full bg-zinc-500 shrink-0" />;
  };

  const navItems = [
    {
      id: 'chat',
      label: 'AI Chat Agent',
      icon: MessageSquare,
      badge: null,
    },
    {
      id: 'findings',
      label: 'Discrepancies & Gate',
      icon: AlertTriangle,
      badge: pendingCount > 0 ? (
        <Badge variant="warning" className="h-4 px-1.5 text-[9px] font-mono">
          {pendingCount}
        </Badge>
      ) : null,
    },
    {
      id: 'documents',
      label: 'Document Vault',
      icon: FileText,
      badge: docCount > 0 ? (
        <span className="text-[10px] font-mono text-zinc-500">
          {docCount}
        </span>
      ) : null,
    },
    {
      id: 'register',
      label: 'Project Register',
      icon: FileCheck,
      badge: null,
    },
    {
      id: 'pipeline',
      label: 'Pipeline & Rewind',
      icon: GitCommit,
      badge: null,
    },
    {
      id: 'graph',
      label: 'Knowledge Graph',
      icon: Network,
      badge: null,
    },
  ];

  if (collapsed) {
    return (
      <aside className="w-14 border-r border-sidebar-border bg-sidebar flex flex-col items-center py-3 justify-between shrink-0 select-none">
        <div className="flex flex-col items-center gap-4">
          <button
            onClick={onToggleCollapse}
            title="Expand Sidebar"
            className="p-2 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition"
          >
            <PanelLeftOpen className="w-4 h-4" />
          </button>
          <div className="w-7 h-7 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-100 font-bold text-xs">
            D
          </div>
          <div className="w-full h-px bg-zinc-800" />
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                title={item.label}
                className={`p-2 rounded-lg transition relative ${
                  isActive ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60'
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.id === 'findings' && pendingCount > 0 && (
                  <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-amber-400" />
                )}
              </button>
            );
          })}
        </div>

        <div className="flex flex-col items-center gap-2">
          <button
            onClick={onOpenSettings}
            title="Settings"
            className="p-2 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition"
          >
            <SettingsIcon className="w-4 h-4" />
          </button>
        </div>
      </aside>
    );
  }

  return (
    <aside className="w-64 border-r border-sidebar-border bg-sidebar flex flex-col justify-between shrink-0 select-none text-xs">
      {/* Top Header: Workspace Selector & Collapse */}
      <div className="p-3 border-b border-sidebar-border/80">
        <div className="flex items-center justify-between gap-1 mb-2">
          {/* Workspace Menu Button */}
          <div className="relative flex-1">
            <button
              onClick={() => setProjectDropdownOpen(!projectDropdownOpen)}
              className="w-full flex items-center justify-between p-1.5 rounded-lg hover:bg-zinc-800/80 transition text-left"
            >
              <div className="flex items-center gap-2 truncate">
                <div className="w-5 h-5 rounded-md bg-zinc-800 border border-zinc-700 flex items-center justify-center text-[10px] font-bold text-zinc-200">
                  {projectId.replace('proj_', '').charAt(0).toUpperCase()}
                </div>
                <span className="font-semibold text-zinc-200 truncate">
                  {projectId.replace(/^proj_/, '').replace(/_/g, ' ')}
                </span>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-zinc-500 shrink-0 ml-1" />
            </button>

            {/* Dropdown Menu */}
            {projectDropdownOpen && (
              <div className="absolute top-full left-0 mt-1 w-full bg-zinc-900 border border-zinc-800 rounded-xl shadow-xl py-1 z-50">
                <div className="px-2.5 py-1 text-[10px] font-mono uppercase text-zinc-500">
                  Projects / Workspaces
                </div>
                <div className="max-h-48 overflow-y-auto">
                  {projectsList.map((p) => (
                    <button
                      key={p}
                      onClick={() => {
                        onSelectProject(p);
                        setProjectDropdownOpen(false);
                      }}
                      className={`w-full px-2.5 py-1.5 text-left text-xs truncate flex items-center justify-between hover:bg-zinc-800 transition ${
                        p === projectId ? 'text-zinc-100 font-semibold bg-zinc-800/50' : 'text-zinc-400'
                      }`}
                    >
                      <span className="truncate">{p.replace(/^proj_/, '').replace(/_/g, ' ')}</span>
                      {p === projectId && <span className="w-1.5 h-1.5 rounded-full bg-zinc-400" />}
                    </button>
                  ))}
                </div>
                <div className="border-t border-zinc-800 mt-1 pt-1 px-1">
                  <button
                    onClick={() => {
                      setProjectDropdownOpen(false);
                      onCreateProjectOpen();
                    }}
                    className="w-full px-2 py-1 text-left text-xs text-zinc-300 hover:text-white hover:bg-zinc-800 rounded-md flex items-center gap-1.5 transition"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>New Project</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          <button
            onClick={onToggleCollapse}
            title="Collapse Sidebar"
            className="p-1.5 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition"
          >
            <PanelLeftClose className="w-4 h-4" />
          </button>
        </div>

        {/* Quick Search Shortcut */}
        <button
          onClick={onOpenSearch}
          className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-zinc-900/80 border border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-zinc-300 transition text-[11px]"
        >
          <div className="flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-zinc-500" />
            <span>Search chunks...</span>
          </div>
          <kbd className="text-[10px] bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded border border-zinc-700 font-mono">⌘K</kbd>
        </button>
      </div>

      {/* Main Navigation Section */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-4">
        {/* Core Views */}
        <div className="space-y-0.5">
          <div className="px-2 py-1 text-[10px] uppercase font-mono tracking-wider text-zinc-500">
            Navigation
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg font-medium transition text-xs ${
                  isActive
                    ? 'bg-zinc-800 text-zinc-100 shadow-sm'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-zinc-100' : 'text-zinc-500'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge}
              </button>
            );
          })}
        </div>

        {/* Chat Sessions Sub-List */}
        <div className="space-y-1">
          <div className="flex items-center justify-between px-2 py-1">
            <span className="text-[10px] uppercase font-mono tracking-wider text-zinc-500">
              Chats ({sessions.length})
            </span>
            <button
              onClick={onNewSession}
              title="New Chat Session"
              className="p-1 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded transition"
            >
              <Plus className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-0.5 max-h-44 overflow-y-auto pr-0.5">
            {sessions.map((s) => {
              const isCurrent = s.tree_id === activeTreeId;
              return (
                <div
                  key={s.tree_id}
                  onClick={() => {
                    onSelectSession(s.tree_id);
                    if (activeTab !== 'chat') onSelectTab('chat');
                  }}
                  className={`group flex items-center justify-between px-2.5 py-1.5 rounded-lg cursor-pointer transition text-xs ${
                    isCurrent && activeTab === 'chat'
                      ? 'bg-zinc-800/80 text-zinc-200 font-semibold border border-zinc-700/50'
                      : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-850'
                  }`}
                >
                  <span className="truncate pr-1 text-[11px]">
                    {s.title || 'Conversation'}
                  </span>
                  {sessions.length > 1 && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(s.tree_id);
                      }}
                      title="Delete Chat"
                      className="opacity-0 group-hover:opacity-100 p-0.5 text-zinc-500 hover:text-rose-400 rounded transition"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer Controls: Pipeline Status, Run Action & Settings */}
      <div className="p-3 border-t border-sidebar-border/80 space-y-2 bg-sidebar">
        {/* Status indicator */}
        <div className="flex items-center justify-between px-1 text-[11px] text-zinc-400">
          <div className="flex items-center gap-2">
            {getStatusDot()}
            <span className="font-mono text-[10px]">
              {isRunningPipeline ? 'RUNNING' : pipelineStatus}
            </span>
          </div>
          <span className="font-mono text-[10px] text-zinc-500">
            {currentNode || 'INIT'}
          </span>
        </div>

        {/* Action Button */}
        <Button
          onClick={onRunPipeline}
          disabled={isRunningPipeline}
          size="sm"
          variant="outline"
          className="w-full justify-center gap-1.5 text-xs bg-zinc-900 hover:bg-zinc-800 border-zinc-800 text-zinc-200"
        >
          {isRunningPipeline ? (
            <RefreshCw className="w-3 h-3 animate-spin" />
          ) : (
            <Play className="w-3 h-3 fill-current" />
          )}
          <span>{isRunningPipeline ? 'Auditing...' : 'Run Audit Pipeline'}</span>
        </Button>

        {/* Settings button */}
        <button
          onClick={onOpenSettings}
          className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60 transition text-xs"
        >
          <div className="flex items-center gap-2">
            <SettingsIcon className="w-3.5 h-3.5 text-zinc-500" />
            <span>LLM & Providers</span>
          </div>
          <span className="text-[10px] text-zinc-500 font-mono">Config</span>
        </button>
      </div>
    </aside>
  );
}
