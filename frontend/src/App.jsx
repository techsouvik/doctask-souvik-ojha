import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatView from './components/ChatView';
import FindingsView from './components/FindingsView';
import PipelineView from './components/PipelineView';
import DocumentsView from './components/DocumentsView';
import RegisterView from './components/RegisterView';
import GraphView from './components/GraphView';
import SettingsModal from './components/SettingsModal';
import SpotlightSearchModal from './components/SpotlightSearchModal';
import CreateProjectModal from './components/CreateProjectModal';
import DocumentDetailModal from './components/DocumentDetailModal';
import { Button } from './components/ui/button';
import { 
  fetchProjects, 
  fetchProjectStatus, 
  fetchDocuments, 
  fetchFindings, 
  runPipeline,
  listSessions,
  deleteSession
} from './services/api';
import { Play, RefreshCw, Search, Settings as SettingsIcon } from 'lucide-react';

export default function App() {
  const [projectId, setProjectId] = useState('proj_greenfield_tech_park');
  const [projectsList, setProjectsList] = useState(['proj_greenfield_tech_park']);
  const [activeTab, setActiveTab] = useState('chat');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Chat sessions state
  const [sessions, setSessions] = useState([]);
  const [activeTreeId, setActiveTreeId] = useState('tree_default');

  // Workspace Pipeline Data
  const [pipelineStatus, setPipelineStatus] = useState('READY');
  const [currentNode, setCurrentNode] = useState('INIT');
  const [pendingCount, setPendingCount] = useState(0);
  const [documents, setDocuments] = useState([]);
  const [findings, setFindings] = useState([]);
  const [isRunningPipeline, setIsRunningPipeline] = useState(false);

  // Modals
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isCreateProjectOpen, setIsCreateProjectOpen] = useState(false);
  const [inspectDocId, setInspectDocId] = useState(null);

  // Toast
  const [toast, setToast] = useState(null);
  const showToast = (msg, type = 'info') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (projectId) {
      refreshProjectData();
      loadProjectSessions();
    }
  }, [projectId]);

  const loadProjects = async () => {
    try {
      const data = await fetchProjects();
      if (data.projects && data.projects.length > 0) {
        setProjectsList(data.projects);
        if (!data.projects.includes(projectId)) {
          setProjectId(data.projects[0]);
        }
      }
    } catch (err) {
      console.error('Error loading projects:', err);
    }
  };

  const loadProjectSessions = async () => {
    try {
      const data = await listSessions(projectId);
      if (data.sessions && data.sessions.length > 0) {
        setSessions(data.sessions);
        if (!data.sessions.some(s => s.tree_id === activeTreeId)) {
          setActiveTreeId(data.sessions[0].tree_id);
        }
      } else {
        const defaultTree = `tree_${Date.now()}`;
        setSessions([{ tree_id: defaultTree, title: 'New Conversation', message_count: 0 }]);
        setActiveTreeId(defaultTree);
      }
    } catch (err) {
      console.error('Sessions load error:', err);
    }
  };

  const handleNewSession = () => {
    const newId = `tree_${Date.now()}`;
    const newSession = { tree_id: newId, title: 'New Conversation', message_count: 0 };
    setSessions(prev => [newSession, ...prev]);
    setActiveTreeId(newId);
    setActiveTab('chat');
  };

  const handleDeleteSession = async (treeId) => {
    try {
      await deleteSession(projectId, treeId);
      const remaining = sessions.filter(s => s.tree_id !== treeId);
      setSessions(remaining);
      if (activeTreeId === treeId && remaining.length > 0) {
        setActiveTreeId(remaining[0].tree_id);
      }
    } catch (err) {
      console.error('Delete session error:', err);
    }
  };

  const refreshProjectData = async () => {
    try {
      const [statusData, docsData, findingsData] = await Promise.all([
        fetchProjectStatus(projectId).catch(() => ({})),
        fetchDocuments(projectId).catch(() => ({ documents: [] })),
        fetchFindings(projectId).catch(() => ({ findings: [] }))
      ]);

      setPipelineStatus(statusData.status || 'READY');
      setCurrentNode(statusData.current_node || 'INIT');
      setPendingCount(statusData.pending_findings_count || 0);
      setDocuments(docsData.documents || []);
      setFindings(findingsData.findings || []);
    } catch (err) {
      console.error('Failed to refresh project data:', err);
    }
  };

  const handleRunPipeline = async () => {
    setIsRunningPipeline(true);
    showToast('Executing LangGraph reconciliation audit...', 'info');
    try {
      const result = await runPipeline(projectId);
      await refreshProjectData();
      showToast(
        `Audit completed! Found ${result.findings_count || 0} findings (${result.pending_findings_count || 0} at Human Gate).`,
        'success'
      );
    } catch (err) {
      showToast('Pipeline execution error: ' + err.message, 'error');
    } finally {
      setIsRunningPipeline(false);
    }
  };

  const tabTitles = {
    chat: 'AI Chat Agent',
    findings: 'Discrepancies & Human Gate',
    documents: 'Document Vault',
    register: 'Reconciled Project Register',
    pipeline: 'LangGraph Pipeline & Time Travel',
    graph: 'Interactive Knowledge Graph'
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground selection:bg-zinc-800">
      {/* Sidebar */}
      <Sidebar
        projectId={projectId}
        projectsList={projectsList}
        onSelectProject={(id) => setProjectId(id)}
        onCreateProjectOpen={() => setIsCreateProjectOpen(true)}
        activeTab={activeTab}
        onSelectTab={(tab) => setActiveTab(tab)}
        activeTreeId={activeTreeId}
        onSelectSession={(treeId) => setActiveTreeId(treeId)}
        sessions={sessions}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        pendingCount={pendingCount}
        docCount={documents.length}
        pipelineStatus={pipelineStatus}
        currentNode={currentNode}
        isRunningPipeline={isRunningPipeline}
        onRunPipeline={handleRunPipeline}
        onOpenSearch={() => setIsSearchOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-12 border-b border-border bg-background/80 backdrop-blur-md px-4 flex items-center justify-between shrink-0 select-none text-xs">
          {/* Breadcrumbs */}
          <div className="flex items-center gap-1.5 text-muted-foreground font-medium truncate">
            <span>Projects</span>
            <span>/</span>
            <span className="text-foreground font-semibold truncate">
              {projectId.replace(/^proj_/, '').replace(/_/g, ' ')}
            </span>
            <span>/</span>
            <span className="text-muted-foreground">{tabTitles[activeTab]}</span>
          </div>

          {/* Quick Header Actions */}
          <div className="flex items-center gap-2">
            <Button
              onClick={handleRunPipeline}
              disabled={isRunningPipeline}
              size="sm"
              variant="default"
              className="h-7 text-xs gap-1 shadow-sm"
            >
              {isRunningPipeline ? (
                <RefreshCw className="w-3 h-3 animate-spin" />
              ) : (
                <Play className="w-3 h-3 fill-current" />
              )}
              <span>{isRunningPipeline ? 'Auditing...' : 'Run Audit'}</span>
            </Button>

            <Button
              onClick={() => setIsSearchOpen(true)}
              variant="outline"
              size="iconSm"
              title="Search (⌘K)"
            >
              <Search className="w-3.5 h-3.5" />
            </Button>

            <Button
              onClick={() => setIsSettingsOpen(true)}
              variant="outline"
              size="iconSm"
              title="LLM Settings"
            >
              <SettingsIcon className="w-3.5 h-3.5" />
            </Button>
          </div>
        </header>

        {/* View Content */}
        <main className="flex-1 flex flex-col overflow-hidden relative">
          {activeTab === 'chat' && (
            <ChatView
              projectId={projectId}
              activeTreeId={activeTreeId}
              onRefreshProject={refreshProjectData}
              onOpenDocDetail={(docId) => setInspectDocId(docId)}
              onSwitchTab={(tab) => setActiveTab(tab)}
            />
          )}

          {activeTab === 'findings' && (
            <FindingsView
              projectId={projectId}
              findings={findings}
              pendingCount={pendingCount}
              onRefreshProject={refreshProjectData}
              onOpenDocDetail={(docId) => setInspectDocId(docId)}
            />
          )}

          {activeTab === 'documents' && (
            <DocumentsView
              projectId={projectId}
              documents={documents}
              onRefreshProject={refreshProjectData}
              onOpenDocDetail={(docId) => setInspectDocId(docId)}
            />
          )}

          {activeTab === 'register' && (
            <RegisterView
              projectId={projectId}
              onRefreshProject={refreshProjectData}
            />
          )}

          {activeTab === 'pipeline' && (
            <PipelineView
              projectId={projectId}
              pipelineStatus={pipelineStatus}
              currentNode={currentNode}
              isRunningPipeline={isRunningPipeline}
              onRefreshProject={refreshProjectData}
            />
          )}

          {activeTab === 'graph' && (
            <GraphView
              projectId={projectId}
              onOpenDocDetail={(docId) => setInspectDocId(docId)}
            />
          )}
        </main>
      </div>

      {/* Global Modals */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSaved={() => showToast('LLM settings saved successfully.', 'success')}
      />

      <SpotlightSearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        projectId={projectId}
        onSelectDoc={(docName) => setInspectDocId(docName)}
      />

      <CreateProjectModal
        isOpen={isCreateProjectOpen}
        onClose={() => setIsCreateProjectOpen(false)}
        onProjectCreated={(newId) => {
          loadProjects();
          setProjectId(newId);
          showToast(`Workspace '${newId}' ready.`, 'success');
        }}
      />

      <DocumentDetailModal
        docId={inspectDocId}
        projectId={projectId}
        onClose={() => setInspectDocId(null)}
      />

      {/* Minimalist Toast */}
      {toast && (
        <div className="fixed bottom-4 right-4 z-50 animate-fade-in">
          <div
            className={`px-3.5 py-2 rounded-lg text-xs font-medium border shadow-lg ${
              toast.type === 'error'
                ? 'bg-rose-950 text-rose-200 border-rose-800'
                : toast.type === 'success'
                ? 'bg-zinc-900 text-zinc-100 border-zinc-700'
                : 'bg-zinc-900 text-zinc-100 border-zinc-800'
            }`}
          >
            {toast.msg}
          </div>
        </div>
      )}
    </div>
  );
}
