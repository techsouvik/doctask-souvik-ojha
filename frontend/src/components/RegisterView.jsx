import React, { useState, useEffect } from 'react';
import { 
  FileCheck, 
  Download, 
  ExternalLink, 
  Search, 
  RefreshCw, 
  ChevronDown, 
  ChevronRight,
  AlertTriangle
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card } from './ui/card';
import { fetchRegister, exportReportUrl } from '../services/api';

export default function RegisterView({
  projectId,
  onRefreshProject
}) {
  const [register, setRegister] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedKey, setExpandedKey] = useState(null);
  const [searchFilter, setSearchFilter] = useState('');

  useEffect(() => {
    loadRegister();
  }, [projectId]);

  const loadRegister = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRegister(projectId);
      setRegister(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredEntries = register?.entries?.filter(e => 
    e.title.toLowerCase().includes(searchFilter.toLowerCase()) ||
    e.entity_key.toLowerCase().includes(searchFilter.toLowerCase()) ||
    String(e.reconciled_value).toLowerCase().includes(searchFilter.toLowerCase())
  ) || [];

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 max-w-5xl mx-auto w-full text-xs">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-emerald-400" />
              Reconciled Project Register
            </h2>
            {register && (
              <Badge variant="outline" className="font-mono text-[10px]">
                v{register.version}
              </Badge>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Single reconciled source of truth compiling all corroborated figures, amendments, and gate decisions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={loadRegister}
            variant="outline"
            size="sm"
            className="h-8"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </Button>

          <a
            href={exportReportUrl(projectId)}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button size="sm" variant="default" className="gap-1.5 h-8">
              <Download className="w-3.5 h-3.5" />
              <span>Export Executive Report</span>
              <ExternalLink className="w-3 h-3 text-muted-foreground" />
            </Button>
          </a>
        </div>
      </div>

      {loading && (
        <div className="py-16 text-center text-muted-foreground">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-zinc-400 mb-2" />
          <p>Loading register...</p>
        </div>
      )}

      {error && !loading && (
        <div className="py-16 text-center border border-border rounded-xl bg-card/40 space-y-1">
          <AlertTriangle className="w-6 h-6 text-amber-400 mx-auto" />
          <p className="font-medium text-foreground">Project Register Not Finalized</p>
          <p className="text-muted-foreground text-[11px] max-w-sm mx-auto">
            {error}. Execute the reconciliation pipeline and approve gate findings to compile this register.
          </p>
        </div>
      )}

      {register && !loading && (
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="relative w-full sm:w-64">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Search metrics..."
                className="w-full pl-8 pr-3 py-1 rounded-lg bg-background border border-border text-xs text-foreground placeholder:text-muted-foreground outline-none focus:border-zinc-500"
              />
            </div>
            <span className="text-[11px] text-muted-foreground font-mono">
              {filteredEntries.length} reconciled metrics
            </span>
          </div>

          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-border bg-background/50 text-muted-foreground text-[10px] uppercase font-mono">
                <tr>
                  <th className="p-3">Entity Metric</th>
                  <th className="p-3">Reconciled Value</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Primary Citation</th>
                  <th className="p-3 text-right">Audit History</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/80">
                {filteredEntries.map((entry) => {
                  const isExpanded = expandedKey === entry.entity_key;
                  const isCorroborated = entry.status === 'CORROBORATED';
                  const isContradicted = entry.status === 'CONTRADICTED';

                  return (
                    <React.Fragment key={entry.entity_key}>
                      <tr className="hover:bg-accent/40 transition">
                        <td className="p-3">
                          <div className="font-semibold text-foreground">{entry.title}</div>
                          <div className="text-[10px] font-mono text-muted-foreground">{entry.entity_key}</div>
                        </td>
                        <td className="p-3 font-semibold text-foreground">
                          {entry.reconciled_value} {entry.unit ? `(${entry.unit})` : ''}
                        </td>
                        <td className="p-3">
                          <Badge variant={isCorroborated ? 'success' : isContradicted ? 'warning' : 'secondary'}>
                            {entry.status}
                          </Badge>
                        </td>
                        <td className="p-3 max-w-xs truncate text-muted-foreground">
                          {entry.primary_citation ? (
                            <div>
                              <span className="font-mono text-[10px] text-zinc-300 block truncate">
                                {entry.primary_citation.filename} ({entry.primary_citation.location})
                              </span>
                              <span className="italic text-[11px] truncate block text-muted-foreground">
                                "{entry.primary_citation.exact_quote}"
                              </span>
                            </div>
                          ) : (
                            <span className="italic text-[11px]">N/A</span>
                          )}
                        </td>
                        <td className="p-3 text-right">
                          {entry.history && entry.history.length > 0 ? (
                            <button
                              onClick={() => setExpandedKey(isExpanded ? null : entry.entity_key)}
                              className="inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground font-medium"
                            >
                              <span>{entry.history.length} sources</span>
                              {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                            </button>
                          ) : (
                            <span className="text-muted-foreground text-[11px]">1</span>
                          )}
                        </td>
                      </tr>

                      {/* Audit History Expansion */}
                      {isExpanded && entry.history && (
                        <tr className="bg-background/80">
                          <td colSpan={5} className="p-3.5 space-y-1.5 border-t border-border">
                            <span className="text-[10px] font-mono uppercase text-muted-foreground font-semibold block mb-1">
                              Document Timeline Lineage:
                            </span>
                            {entry.history.map((hist, hIdx) => (
                              <div key={hIdx} className="p-2 rounded bg-card border border-border text-xs flex items-center justify-between">
                                <div>
                                  <span className="font-semibold text-foreground">{hist.doc_name}</span>
                                  <span className="text-muted-foreground text-[11px] ml-1 font-mono">({hist.location})</span>
                                  <p className="text-muted-foreground italic text-[11px]">"{hist.quote}"</p>
                                </div>
                                <span className="font-mono font-semibold text-foreground text-xs ml-3">
                                  {hist.raw_value}
                                </span>
                              </div>
                            ))}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
