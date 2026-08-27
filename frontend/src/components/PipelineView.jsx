import React, { useState, useEffect } from 'react';
import { 
  Play, 
  RotateCcw, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  RefreshCw, 
  History, 
  GitCommit
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card } from './ui/card';
import { fetchHistory, rewindToNode, runPipeline } from '../services/api';

const PIPELINE_NODES = [
  { id: 'INGEST', name: '1. Ingest', desc: 'Scan directory, SHA-256 deduplication, chunk files' },
  { id: 'CLASSIFY', name: '2. Classify', desc: 'Classify document type & scan prompt injections' },
  { id: 'EXTRACT', name: '3. Extract', desc: 'Extract structured facts with 100% quote grounding' },
  { id: 'RECONCILE', name: '4. Reconcile', desc: 'Cluster entities & align canonical timeline' },
  { id: 'EXAMINE', name: '5. Examine', desc: 'Run arithmetic, cross-doc & contract audit rules' },
  { id: 'GATE', name: '6. Human Gate', desc: 'Pause pipeline for human / MCP approval gate' },
  { id: 'DELIVER', name: '7. Deliver', desc: 'Compile final audited Reconciled Register' },
];

export default function PipelineView({
  projectId,
  pipelineStatus,
  currentNode,
  isRunningPipeline,
  onRefreshProject
}) {
  const [historyList, setHistoryList] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [rewindingNode, setRewindingNode] = useState(null);

  useEffect(() => {
    loadHistory();
  }, [projectId]);

  const loadHistory = async () => {
    setLoadingHistory(true);
    try {
      const data = await fetchHistory(projectId);
      setHistoryList(data.checkpoint_history || []);
    } catch (err) {
      console.error('History error:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleRewind = async (nodeId) => {
    if (!window.confirm(`Rewind state machine back to checkpoint '${nodeId}'? Subsequent steps will be re-evaluated.`)) {
      return;
    }

    setRewindingNode(nodeId);
    try {
      await rewindToNode(projectId, nodeId);
      onRefreshProject();
      loadHistory();
    } catch (err) {
      alert('Rewind error: ' + err.message);
    } finally {
      setRewindingNode(null);
    }
  };

  const getNodeState = (nodeId) => {
    const nodeOrder = PIPELINE_NODES.map(n => n.id);
    const currIdx = nodeOrder.indexOf(currentNode);
    const thisIdx = nodeOrder.indexOf(nodeId);

    if (isRunningPipeline && nodeId === currentNode) return 'RUNNING';
    if (thisIdx < currIdx || pipelineStatus === 'COMPLETED') return 'COMPLETED';
    if (nodeId === currentNode) {
      if (nodeId === 'GATE' && pipelineStatus === 'AWAITING_HUMAN_GATE') return 'GATE_PAUSED';
      return 'ACTIVE';
    }
    return 'PENDING';
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 max-w-5xl mx-auto w-full text-xs">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <GitCommit className="w-4 h-4 text-zinc-400" />
            LangGraph State Machine & Time Travel
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Cyclical 7-node pipeline state serialized into SQLite checkpoints with full state-rewind support.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={() => {
              runPipeline(projectId).then(() => {
                onRefreshProject();
                loadHistory();
              });
            }}
            disabled={isRunningPipeline}
            size="sm"
            variant="default"
            className="gap-1.5"
          >
            {isRunningPipeline ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-current" />
            )}
            <span>{isRunningPipeline ? 'Running...' : 'Run Pipeline'}</span>
          </Button>
        </div>
      </div>

      {/* Stepper Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-2.5">
        {PIPELINE_NODES.map((node, idx) => {
          const state = getNodeState(node.id);
          const isCompleted = state === 'COMPLETED';
          const isActive = state === 'ACTIVE';
          const isGatePaused = state === 'GATE_PAUSED';
          const isRunning = state === 'RUNNING';

          return (
            <Card
              key={node.id}
              className={`p-3.5 flex flex-col justify-between transition-all ${
                isRunning
                  ? 'border-zinc-400 bg-zinc-800/40 ring-1 ring-zinc-400'
                  : isGatePaused
                  ? 'border-amber-500/60 bg-amber-500/10'
                  : isActive
                  ? 'border-zinc-500 bg-card'
                  : isCompleted
                  ? 'border-border bg-card/60'
                  : 'border-border/60 opacity-50 bg-background'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono text-muted-foreground font-semibold">STAGE {idx + 1}</span>
                  {isCompleted && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                  {isGatePaused && <AlertTriangle className="w-3.5 h-3.5 text-amber-400 animate-pulse" />}
                  {isRunning && <RefreshCw className="w-3.5 h-3.5 text-zinc-300 animate-spin" />}
                  {state === 'PENDING' && <Clock className="w-3.5 h-3.5 text-muted-foreground" />}
                </div>
                <h4 className="font-semibold text-xs text-foreground mb-1">{node.name}</h4>
                <p className="text-[11px] text-muted-foreground leading-snug">{node.desc}</p>
              </div>

              {isCompleted && (
                <button
                  onClick={() => handleRewind(node.id)}
                  disabled={rewindingNode === node.id}
                  className="mt-3 py-1 px-2 rounded-md text-[10px] font-medium bg-background hover:bg-zinc-800 text-muted-foreground hover:text-foreground border border-border transition flex items-center justify-center gap-1"
                >
                  <RotateCcw className="w-2.5 h-2.5" />
                  <span>Rewind</span>
                </button>
              )}
            </Card>
          );
        })}
      </div>

      {/* Checkpoint Execution History */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-foreground flex items-center gap-2">
            <History className="w-3.5 h-3.5 text-muted-foreground" />
            <span>Recorded State Checkpoints</span>
          </h3>
          <Button onClick={loadHistory} variant="ghost" size="sm" className="h-7 text-[11px]">
            <RefreshCw className={`w-3 h-3 mr-1 ${loadingHistory ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>
        </div>

        <div className="rounded-xl border border-border bg-card overflow-hidden">
          {historyList.length === 0 ? (
            <p className="p-4 text-muted-foreground text-center">No checkpoints recorded yet.</p>
          ) : (
            <div className="divide-y divide-border/80">
              {historyList.map((cp, idx) => (
                <div key={idx} className="p-3 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono font-semibold text-foreground">{cp.node_name}</span>
                    <span className="text-muted-foreground font-mono text-[11px]">
                      {cp.created_at ? new Date(cp.created_at).toLocaleTimeString() : 'N/A'}
                    </span>
                  </div>
                  <Button
                    onClick={() => handleRewind(cp.node_name)}
                    variant="outline"
                    size="sm"
                    className="h-6 text-[11px] gap-1"
                  >
                    <RotateCcw className="w-2.5 h-2.5" />
                    <span>Rewind Here</span>
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
