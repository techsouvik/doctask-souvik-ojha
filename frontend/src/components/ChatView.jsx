import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Send, 
  Paperclip, 
  GitBranch, 
  FileText, 
  Check, 
  X, 
  AlertTriangle, 
  RefreshCw, 
  Sparkles,
  Bot,
  User,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  ArrowRight
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { 
  fetchSession, 
  streamChatResponse, 
  branchSession, 
  approveFinding, 
  batchApproveFindings, 
  uploadDocument 
} from '../services/api';

export default function ChatView({
  projectId,
  activeTreeId,
  onRefreshProject,
  onOpenDocDetail,
  onSwitchTab
}) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [thinkingStage, setThinkingStage] = useState('');
  const [activeTool, setActiveTool] = useState(null);
  const [thinkingOpen, setThinkingOpen] = useState(true);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [branchModalNode, setBranchModalNode] = useState(null);
  const [branchInput, setBranchInput] = useState('');
  const [uploadingDoc, setUploadingDoc] = useState(false);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (activeTreeId && projectId) {
      loadSessionThread(activeTreeId);
    }
  }, [activeTreeId, projectId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, thinkingStage, isStreaming]);

  const loadSessionThread = async (treeId) => {
    try {
      const data = await fetchSession(projectId, treeId);
      if (data.thread && data.thread.length > 0) {
        setMessages(data.thread);
      } else {
        setMessages([
          {
            id: 'm_welcome',
            role: 'assistant',
            content: `### Welcome to DocuMesh 👋\n\nI am your **Document Reconciliation Assistant** for **\`${projectId.replace(/^proj_/, '').replace(/_/g, ' ')}\`**.\n\n• Ask questions grounded across your ingested document pile.\n• Type **"run reconciliation audit"** to execute the multi-stage LangGraph pipeline.\n• Request discrepancy breakdowns, contract terms, or billing verifications.`,
            metadata: {}
          }
        ]);
      }
    } catch (err) {
      console.error('Failed to load thread:', err);
    }
  };

  const handleSendMessage = async (textToSend = null) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || isStreaming) return;

    setInputMessage('');
    const tempUserNode = {
      id: `u_${Date.now()}`,
      role: 'user',
      content: text,
      metadata: {}
    };

    const tempAiNode = {
      id: `ai_${Date.now()}`,
      role: 'assistant',
      content: '',
      metadata: {}
    };

    setMessages(prev => [...prev, tempUserNode, tempAiNode]);
    setIsStreaming(true);
    setThinkingStage('Analyzing query intent & checking document indices...');

    let accumulatedContent = '';

    await streamChatResponse(
      projectId,
      activeTreeId,
      text,
      null,
      {
        onStage: (stage) => {
          setThinkingStage(stage);
        },
        onToolCall: (data) => {
          setActiveTool(data.tool);
          setThinkingStage(`Invoking tool: ${data.tool}...`);
        },
        onToolResult: (data) => {
          setActiveTool(null);
        },
        onChunk: (chunk) => {
          accumulatedContent += chunk;
          setMessages(prev => {
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
              updated[lastIdx] = {
                ...updated[lastIdx],
                content: accumulatedContent
              };
            }
            return updated;
          });
        },
        onAction: (actionPayload) => {
          setMessages(prev => {
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
              updated[lastIdx] = {
                ...updated[lastIdx],
                metadata: {
                  ...updated[lastIdx].metadata,
                  action_payload: actionPayload
                }
              };
            }
            return updated;
          });
          onRefreshProject();
        },
        onDone: (doneData) => {
          setIsStreaming(false);
          setThinkingStage('');
          if (doneData.assistant_node) {
            setMessages(prev => {
              const updated = [...prev];
              const lastIdx = updated.length - 1;
              if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
                updated[lastIdx] = doneData.assistant_node;
              }
              return updated;
            });
          }
          onRefreshProject();
        },
        onError: (err) => {
          setIsStreaming(false);
          setThinkingStage('');
          setMessages(prev => {
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
              updated[lastIdx] = {
                ...updated[lastIdx],
                content: accumulatedContent + `\n\n⚠️ *Streaming error: ${err}*`
              };
            }
            return updated;
          });
        }
      }
    );
  };

  const handleApproveFindingInChat = async (findingId, approved, feedback = null) => {
    try {
      await approveFinding(projectId, findingId, approved, feedback);
      onRefreshProject();
      handleSendMessage(`${approved ? 'Approve' : 'Reject'} finding ${findingId}`);
    } catch (err) {
      alert('Decision error: ' + err.message);
    }
  };

  const handleBatchApproveInChat = async () => {
    try {
      await batchApproveFindings(projectId, true);
      onRefreshProject();
      handleSendMessage('batch approve all findings');
    } catch (err) {
      alert('Batch approve error: ' + err.message);
    }
  };

  const handleBranchSubmit = async () => {
    if (!branchModalNode || !branchInput.trim()) return;
    try {
      await branchSession(projectId, activeTreeId, branchModalNode.id, branchInput.trim());
      setBranchModalNode(null);
      setBranchInput('');
      loadSessionThread(activeTreeId);
      onRefreshProject();
    } catch (err) {
      alert('Branch error: ' + err.message);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingDoc(true);
    try {
      const res = await uploadDocument(projectId, file);
      onRefreshProject();
      handleSendMessage(`I uploaded \`${res.filename}\`. Ingested ${res.chunks_count || 0} chunks.`);
    } catch (err) {
      alert('Upload error: ' + err.message);
    } finally {
      setUploadingDoc(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const suggestions = [
    "Run reconciliation audit",
    "What is the penalty clause rate in the master plan?",
    "Why does Invoice INV-2024-003 conflict with Q2 report?",
    "Show documents"
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-background overflow-hidden relative">
      {/* Scrollable Conversation Thread */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 space-y-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            const actionPayload = msg.metadata?.action_payload;
            const citations = msg.metadata?.citations || [];

            return (
              <div
                key={msg.id || idx}
                className={`flex gap-3 text-xs leading-relaxed ${
                  isUser ? 'justify-end' : 'justify-start'
                }`}
              >
                {!isUser && (
                  <div className="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700/80 flex items-center justify-center text-zinc-300 shrink-0 mt-0.5">
                    <Bot className="w-3.5 h-3.5" />
                  </div>
                )}

                <div className={`flex flex-col gap-1.5 max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
                  {/* Bubble / Prose */}
                  <div
                    className={`rounded-2xl px-4 py-2.5 shadow-sm transition-all ${
                      isUser
                        ? 'bg-zinc-800 text-zinc-100 rounded-br-sm'
                        : 'bg-zinc-900/60 border border-border text-zinc-200 rounded-bl-sm w-full'
                    }`}
                  >
                    {isUser ? (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <div className="prose-minimal">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content || (isStreaming && idx === messages.length - 1 ? '...' : '')}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>

                  {/* Branch button on user message */}
                  {isUser && (
                    <button
                      onClick={() => setBranchModalNode(msg)}
                      className="flex items-center gap-1 text-[10px] text-zinc-500 hover:text-zinc-300 transition pr-1"
                    >
                      <GitBranch className="w-3 h-3" />
                      <span>Branch</span>
                    </button>
                  )}

                  {/* Inline Action Payload: GATE FINDINGS */}
                  {actionPayload?.type === 'GATE_FINDINGS' && actionPayload.findings?.length > 0 && (
                    <div className="w-full mt-2 rounded-xl border border-border bg-card p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-amber-400" />
                          <span className="font-semibold text-xs text-zinc-200">
                            Human Gate Findings ({actionPayload.findings.length})
                          </span>
                        </div>
                        <Button
                          onClick={handleBatchApproveInChat}
                          size="sm"
                          variant="default"
                          className="h-7 text-[11px] bg-emerald-600 hover:bg-emerald-500 text-white"
                        >
                          <Check className="w-3 h-3 mr-1" />
                          Approve All
                        </Button>
                      </div>

                      <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                        {actionPayload.findings.map((f) => (
                          <div
                            key={f.finding_id}
                            className="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800 space-y-2 text-xs"
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="font-mono font-bold text-zinc-300">[{f.finding_id}]</span>
                                <span className="font-semibold text-zinc-200">{f.title}</span>
                              </div>
                              <Badge
                                variant={
                                  f.severity === 'CRITICAL' ? 'destructive' :
                                  f.severity === 'HIGH' ? 'warning' : 'secondary'
                                }
                              >
                                {f.severity}
                              </Badge>
                            </div>

                            {/* Diffs */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                              {f.source_a && (
                                <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                                  <span className="font-mono text-zinc-500 text-[10px] block">
                                    Source A: {f.source_a.filename} ({f.source_a.location})
                                  </span>
                                  <p className="text-zinc-300 italic mt-0.5">"{f.source_a.exact_quote}"</p>
                                </div>
                              )}
                              {f.source_b && (
                                <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                                  <span className="font-mono text-zinc-500 text-[10px] block">
                                    Source B: {f.source_b.filename} ({f.source_b.location})
                                  </span>
                                  <p className="text-zinc-300 italic mt-0.5">"{f.source_b.exact_quote}"</p>
                                </div>
                              )}
                            </div>

                            {f.resolution_action && (
                              <div className="text-[11px] text-zinc-300 bg-zinc-900 px-2.5 py-1 rounded border border-zinc-800">
                                <strong className="text-zinc-400">Action:</strong> {f.resolution_action}
                              </div>
                            )}

                            <div className="flex items-center justify-end gap-2 pt-1">
                              <Button
                                onClick={() => handleApproveFindingInChat(f.finding_id, false, 'Rejected via chat')}
                                variant="outline"
                                size="sm"
                                className="h-6 text-[11px] text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 border-zinc-800"
                              >
                                Reject
                              </Button>
                              <Button
                                onClick={() => handleApproveFindingInChat(f.finding_id, true)}
                                size="sm"
                                className="h-6 text-[11px] bg-emerald-600 hover:bg-emerald-500 text-white"
                              >
                                Approve
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Inline Action Payload: SHOW REGISTER */}
                  {actionPayload?.type === 'SHOW_REGISTER' && actionPayload.register && (
                    <div className="w-full mt-2 p-3.5 rounded-xl border border-border bg-card flex items-center justify-between text-xs">
                      <div>
                        <div className="font-semibold text-zinc-200">
                          Reconciled Register v{actionPayload.register.version}
                        </div>
                        <p className="text-[11px] text-zinc-500 mt-0.5">
                          {actionPayload.register.entries?.length || 0} canonical metrics reconciled.
                        </p>
                      </div>
                      <Button
                        onClick={() => onSwitchTab('register')}
                        size="sm"
                        variant="subtle"
                        className="gap-1 text-xs"
                      >
                        <span>View Table</span>
                        <ArrowRight className="w-3 h-3" />
                      </Button>
                    </div>
                  )}

                  {/* Citation pills */}
                  {citations.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      <span className="text-[10px] font-mono uppercase text-zinc-500">Citations:</span>
                      {citations.map((c, cIdx) => (
                        <button
                          key={cIdx}
                          onClick={() => setSelectedCitation(c)}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-300 transition"
                        >
                          <FileText className="w-3 h-3 text-zinc-500" />
                          <span>{c.doc_name}</span>
                          <span className="text-zinc-500 font-mono text-[10px]">({c.section})</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center text-zinc-300 shrink-0 mt-0.5">
                    <User className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>
            );
          })}

          {/* Thinking Disclosure (Minimalist accordion) */}
          {isStreaming && thinkingStage && (
            <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/40 p-3 max-w-3xl mx-auto space-y-1">
              <div
                onClick={() => setThinkingOpen(!thinkingOpen)}
                className="flex items-center justify-between cursor-pointer text-xs text-zinc-400 select-none"
              >
                <div className="flex items-center gap-2">
                  {activeTool ? (
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-200 border border-zinc-700 text-[10px] font-mono font-semibold animate-pulse">
                      ⚡ Tool: {activeTool}
                    </span>
                  ) : (
                    <Sparkles className="w-3.5 h-3.5 text-zinc-400 animate-spin" />
                  )}
                  <span className="font-mono text-[11px]">{thinkingStage}</span>
                </div>
                {thinkingOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Floating Bottom Composer */}
      <div className="p-4 border-t border-border bg-background/80 backdrop-blur-md">
        <div className="max-w-3xl mx-auto space-y-2">
          {/* Subtle suggestions when thread is small */}
          {messages.length <= 2 && !isStreaming && (
            <div className="flex flex-wrap items-center gap-1.5 pb-1">
              {suggestions.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(s)}
                  className="px-2.5 py-1 rounded-full text-[11px] bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-zinc-200 transition"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Textbox container */}
          <div className="relative flex items-end gap-2 bg-card border border-border rounded-xl p-2 focus-within:border-zinc-500 transition-all shadow-sm">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              className="hidden"
              accept=".docx,.pdf,.txt"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadingDoc || isStreaming}
              title="Attach document"
              className="p-1.5 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-lg transition disabled:opacity-50"
            >
              {uploadingDoc ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Paperclip className="w-4 h-4" />
              )}
            </button>

            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              rows={1}
              placeholder="Ask about contracts, verify invoices, or type 'run audit'..."
              className="flex-1 bg-transparent text-xs text-foreground placeholder:text-muted-foreground resize-none outline-none py-1.5 px-1 max-h-32 min-h-[34px]"
            />

            <Button
              onClick={() => handleSendMessage()}
              disabled={!inputMessage.trim() || isStreaming}
              size="iconSm"
              variant="default"
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {isStreaming ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Send className="w-3.5 h-3.5" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Citation Preview Modal */}
      {selectedCitation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-card border border-border rounded-xl max-w-lg w-full p-5 space-y-3 shadow-2xl text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-semibold text-foreground">
                <FileText className="w-4 h-4 text-zinc-400" />
                <span>{selectedCitation.doc_name}</span>
              </div>
              <button onClick={() => setSelectedCitation(null)} className="text-muted-foreground hover:text-foreground">✕</button>
            </div>

            <div className="space-y-1">
              <span className="text-[11px] text-muted-foreground font-mono">Location: {selectedCitation.section}</span>
              <div className="p-3 bg-background rounded-lg border border-border italic text-foreground leading-relaxed">
                "{selectedCitation.quote}"
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button
                onClick={() => {
                  const doc = selectedCitation.doc_name;
                  setSelectedCitation(null);
                  onOpenDocDetail(doc);
                }}
                size="sm"
                variant="default"
              >
                Inspect Document
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Branch Modal */}
      {branchModalNode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-card border border-border rounded-xl max-w-md w-full p-5 space-y-3 shadow-2xl text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-semibold text-foreground">
                <GitBranch className="w-4 h-4 text-zinc-400" />
                <span>Branch Conversation</span>
              </div>
              <button onClick={() => setBranchModalNode(null)} className="text-muted-foreground hover:text-foreground">✕</button>
            </div>

            <p className="text-muted-foreground">
              Forking from: <span className="italic text-foreground">"{branchModalNode.content.slice(0, 50)}..."</span>
            </p>

            <textarea
              value={branchInput}
              onChange={(e) => setBranchInput(e.target.value)}
              placeholder="What would you like to ask in this branch?"
              rows={3}
              className="w-full bg-background border border-border rounded-lg p-2.5 text-xs text-foreground outline-none focus:border-zinc-500"
            />

            <div className="flex justify-end gap-2 pt-2">
              <Button onClick={() => setBranchModalNode(null)} variant="ghost" size="sm">
                Cancel
              </Button>
              <Button onClick={handleBranchSubmit} disabled={!branchInput.trim()} size="sm">
                Fork Branch
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
