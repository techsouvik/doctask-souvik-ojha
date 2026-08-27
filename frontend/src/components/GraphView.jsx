import React, { useState, useEffect, useRef } from 'react';
import { 
  Network, 
  RefreshCw, 
  ZoomIn, 
  ZoomOut, 
  RotateCcw,
  Eye,
  FileText,
  AlertTriangle
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { fetchKnowledgeGraph } from '../services/api';

export default function GraphView({
  projectId,
  onOpenDocDetail
}) {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [scale, setScale] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [startPan, setStartPan] = useState({ x: 0, y: 0 });

  const containerRef = useRef(null);

  useEffect(() => {
    loadGraph();
  }, [projectId]);

  const loadGraph = async () => {
    setLoading(true);
    try {
      const data = await fetchKnowledgeGraph(projectId);
      setGraphData(data);
    } catch (err) {
      console.error('Graph fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const docNodes = graphData.nodes.filter(n => n.type === 'DOCUMENT');
  const findingNodes = graphData.nodes.filter(n => n.type === 'FINDING');

  const width = 800;
  const height = 500;
  const cx = width / 2;
  const cy = height / 2;

  const positions = {};
  docNodes.forEach((node, i) => {
    const total = docNodes.length || 1;
    const angle = (i / total) * 2 * Math.PI;
    const r = 160;
    positions[node.id] = {
      x: cx + r * Math.cos(angle) - 40,
      y: cy + r * Math.sin(angle)
    };
  });

  findingNodes.forEach((node, i) => {
    const total = findingNodes.length || 1;
    const angle = (i / total) * 2 * Math.PI + Math.PI / (total * 2);
    const r = 240;
    positions[node.id] = {
      x: cx + r * Math.cos(angle) + 40,
      y: cy + r * Math.sin(angle)
    };
  });

  const handleMouseDown = (e) => {
    if (e.target.tagName === 'svg' || e.target.tagName === 'rect') {
      setIsPanning(true);
      setStartPan({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e) => {
    if (isPanning) {
      setPan({ x: e.clientX - startPan.x, y: e.clientY - startPan.y });
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-background overflow-hidden p-6 space-y-4 max-w-6xl mx-auto w-full text-xs">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <div>
          <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Network className="w-4 h-4 text-zinc-400" />
            Knowledge Graph Visualizer
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            {docNodes.length} Documents, {findingNodes.length} Discrepancies, {graphData.edges.length} Conflict Edges
          </p>
        </div>

        <div className="flex items-center gap-1.5">
          <Button onClick={() => setScale(s => Math.min(s + 0.15, 2.2))} size="iconSm" variant="outline">
            <ZoomIn className="w-3.5 h-3.5" />
          </Button>
          <Button onClick={() => setScale(s => Math.max(s - 0.15, 0.5))} size="iconSm" variant="outline">
            <ZoomOut className="w-3.5 h-3.5" />
          </Button>
          <Button onClick={() => { setScale(1); setPan({ x: 0, y: 0 }); }} size="iconSm" variant="outline">
            <RotateCcw className="w-3.5 h-3.5" />
          </Button>
          <Button onClick={loadGraph} size="sm" variant="ghost" className="h-7 text-xs ml-1">
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? 'animate-spin' : ''}`} />
            <span>Reload</span>
          </Button>
        </div>
      </div>

      {/* Canvas Area */}
      <div className="flex-1 flex rounded-xl border border-border bg-card overflow-hidden relative">
        <div
          ref={containerRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          className="flex-1 h-full cursor-grab active:cursor-grabbing overflow-hidden"
        >
          <svg
            width="100%"
            height="100%"
            viewBox={`0 0 ${width} ${height}`}
            className="w-full h-full"
          >
            <rect width={width} height={height} fill="#09090b" />

            <g transform={`translate(${pan.x}, ${pan.y}) scale(${scale})`}>
              {/* Conflict Edges */}
              {graphData.edges.map((edge, idx) => {
                const src = positions[edge.from || edge.source];
                const tgt = positions[edge.to || edge.target];
                if (!src || !tgt) return null;

                return (
                  <line
                    key={idx}
                    x1={src.x}
                    y1={src.y}
                    x2={tgt.x}
                    y2={tgt.y}
                    stroke="#f43f5e"
                    strokeWidth="1.5"
                    strokeDasharray="3 2"
                    opacity="0.7"
                  />
                );
              })}

              {/* Document Nodes */}
              {docNodes.map((node) => {
                const pos = positions[node.id];
                if (!pos) return null;
                const isSelected = selectedNode?.id === node.id;

                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    onClick={() => setSelectedNode(node)}
                    className="cursor-pointer"
                  >
                    <circle
                      r={isSelected ? 22 : 18}
                      fill="#18181b"
                      stroke={isSelected ? '#fafafa' : '#3f3f46'}
                      strokeWidth={isSelected ? 2.5 : 1.5}
                      className="transition-all"
                    />
                    <text
                      y={3.5}
                      textAnchor="middle"
                      fill="#e4e4e7"
                      fontSize="9"
                      fontWeight="bold"
                      fontFamily="JetBrains Mono"
                    >
                      DOC
                    </text>
                    <text
                      y={28}
                      textAnchor="middle"
                      fill="#a1a1aa"
                      fontSize="9"
                      fontWeight="500"
                    >
                      {node.label?.slice(0, 16)}
                    </text>
                  </g>
                );
              })}

              {/* Finding Nodes */}
              {findingNodes.map((node) => {
                const pos = positions[node.id];
                if (!pos) return null;
                const isSelected = selectedNode?.id === node.id;
                const isCrit = node.severity === 'CRITICAL';

                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    onClick={() => setSelectedNode(node)}
                    className="cursor-pointer"
                  >
                    <circle
                      r={isSelected ? 18 : 15}
                      fill={isCrit ? '#271014' : '#27190e'}
                      stroke={isCrit ? '#f43f5e' : '#f59e0b'}
                      strokeWidth={isSelected ? 2.5 : 1.5}
                      className="transition-all"
                    />
                    <text
                      y={3.5}
                      textAnchor="middle"
                      fill={isCrit ? '#fda4af' : '#fde68a'}
                      fontSize="8"
                      fontWeight="bold"
                      fontFamily="JetBrains Mono"
                    >
                      {node.id}
                    </text>
                    <text
                      y={25}
                      textAnchor="middle"
                      fill="#a1a1aa"
                      fontSize="9"
                      fontWeight="500"
                    >
                      {node.label?.slice(0, 14)}
                    </text>
                  </g>
                );
              })}
            </g>
          </svg>
        </div>

        {/* Selected Node Inspector Sidebar */}
        {selectedNode && (
          <div className="w-72 border-l border-border bg-card p-4 space-y-3 shrink-0 overflow-y-auto">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-mono text-muted-foreground font-semibold">
                {selectedNode.type} Details
              </span>
              <button onClick={() => setSelectedNode(null)} className="text-muted-foreground hover:text-foreground">✕</button>
            </div>

            <div>
              <h3 className="font-semibold text-foreground text-xs">{selectedNode.label || selectedNode.id}</h3>
              {selectedNode.doc_type && (
                <Badge variant="outline" className="mt-1 text-[10px]">
                  {selectedNode.doc_type}
                </Badge>
              )}
            </div>

            {selectedNode.type === 'FINDING' && (
              <div className="space-y-2 text-xs">
                <div>
                  <span className="text-muted-foreground block text-[10px]">Severity:</span>
                  <span className="font-semibold text-rose-400">{selectedNode.severity}</span>
                </div>
                {selectedNode.description && (
                  <div>
                    <span className="text-muted-foreground block text-[10px]">Description:</span>
                    <p className="text-foreground italic text-[11px] leading-relaxed">{selectedNode.description}</p>
                  </div>
                )}
                {selectedNode.resolution_action && (
                  <div className="p-2 rounded bg-background border border-border text-[11px] text-zinc-300">
                    <strong className="text-zinc-400">Action:</strong> {selectedNode.resolution_action}
                  </div>
                )}
              </div>
            )}

            {selectedNode.type === 'DOCUMENT' && (
              <div className="space-y-3 pt-2">
                <p className="text-muted-foreground text-[11px]">
                  Chunks: <strong className="text-foreground">{selectedNode.chunks_count || 1}</strong>
                </p>
                <Button
                  onClick={() => onOpenDocDetail(selectedNode.id)}
                  size="sm"
                  variant="default"
                  className="w-full text-xs"
                >
                  <Eye className="w-3.5 h-3.5 mr-1" />
                  <span>Inspect Chunks</span>
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
