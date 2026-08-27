import React, { useState } from 'react';
import { 
  AlertTriangle, 
  Check, 
  X, 
  FileText, 
  CheckCircle2, 
  Sparkles,
  Filter,
  RotateCcw,
  Clock
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card } from './ui/card';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './ui/dialog';
import { approveFinding, batchApproveFindings } from '../services/api';

export default function FindingsView({
  projectId,
  findings,
  pendingCount,
  onRefreshProject,
  onOpenDocDetail
}) {
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL'); // ALL, PRESENTED, APPROVED, REJECTED
  const [rejectModalFinding, setRejectModalFinding] = useState(null);
  const [rejectFeedback, setRejectFeedback] = useState('');
  const [processingId, setProcessingId] = useState(null);

  const approvedCount = findings.filter(f => f.status === 'APPROVED' || f.status?.value === 'APPROVED').length;
  const rejectedCount = findings.filter(f => f.status === 'REJECTED' || f.status?.value === 'REJECTED').length;
  const presentedCount = findings.filter(f => f.status === 'PRESENTED' || f.status?.value === 'PRESENTED').length;

  const filteredFindings = findings.filter(f => {
    const sev = (typeof f.severity === 'object' ? f.severity?.value : f.severity)?.toUpperCase() || '';
    const st = (typeof f.status === 'object' ? f.status?.value : f.status)?.toUpperCase() || '';
    if (filterSeverity !== 'ALL' && sev !== filterSeverity) return false;
    if (filterStatus !== 'ALL' && st !== filterStatus) return false;
    return true;
  });

  const handleApprove = async (findingId) => {
    setProcessingId(findingId);
    try {
      await approveFinding(projectId, findingId, true);
      onRefreshProject();
    } catch (err) {
      alert('Approval error: ' + err.message);
    } finally {
      setProcessingId(null);
    }
  };

  const handleRejectConfirm = async () => {
    if (!rejectModalFinding) return;
    setProcessingId(rejectModalFinding.finding_id);
    try {
      await approveFinding(projectId, rejectModalFinding.finding_id, false, rejectFeedback);
      setRejectModalFinding(null);
      setRejectFeedback('');
      onRefreshProject();
    } catch (err) {
      alert('Reject error: ' + err.message);
    } finally {
      setProcessingId(null);
    }
  };

  const handleBatchApproveAll = async () => {
    try {
      await batchApproveFindings(projectId, true);
      onRefreshProject();
    } catch (err) {
      alert('Batch approve error: ' + err.message);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 max-w-5xl mx-auto w-full text-xs">
      {/* Top Header & Fast Batch Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Human Gate & Discrepancy Audit Records
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Permanent decision log for cross-document contradictions. Approvals and rejections are preserved permanently in SQLite checkpoints.
          </p>
        </div>

        {presentedCount > 0 && (
          <Button
            onClick={handleBatchApproveAll}
            size="sm"
            variant="default"
            className="gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm"
          >
            <Check className="w-3.5 h-3.5" />
            <span>Approve All Pending ({presentedCount})</span>
          </Button>
        )}
      </div>

      {/* Filter Tabs with Live Status Counts */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-card p-2.5 rounded-xl border border-border">
        {/* Status Category Tabs */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setFilterStatus('ALL')}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
              filterStatus === 'ALL'
                ? 'bg-zinc-800 text-foreground font-semibold shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            All Records ({findings.length})
          </button>
          <button
            onClick={() => setFilterStatus('PRESENTED')}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
              filterStatus === 'PRESENTED'
                ? 'bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/30'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Pending ({presentedCount})
          </button>
          <button
            onClick={() => setFilterStatus('APPROVED')}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
              filterStatus === 'APPROVED'
                ? 'bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Approved ({approvedCount})
          </button>
          <button
            onClick={() => setFilterStatus('REJECTED')}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
              filterStatus === 'REJECTED'
                ? 'bg-rose-500/20 text-rose-300 font-semibold border border-rose-500/30'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Rejected ({rejectedCount})
          </button>
        </div>

        {/* Severity Filters */}
        <div className="flex items-center gap-1">
          <span className="text-[11px] text-muted-foreground mr-1">Severity:</span>
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-2 py-0.5 rounded-md text-[11px] font-medium transition ${
                filterSeverity === sev
                  ? 'bg-zinc-800 text-foreground font-semibold'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-3.5">
        {filteredFindings.length === 0 ? (
          <div className="py-16 text-center border border-border rounded-xl bg-card/40 space-y-1">
            <CheckCircle2 className="w-6 h-6 text-muted-foreground mx-auto" />
            <p className="font-medium text-foreground">No records matching your filter</p>
            <p className="text-muted-foreground text-[11px]">Select another filter tab above to view other discrepancy records.</p>
          </div>
        ) : (
          filteredFindings.map((f) => {
            const sevStr = (typeof f.severity === 'object' ? f.severity?.value : f.severity)?.toUpperCase();
            const stStr = (typeof f.status === 'object' ? f.status?.value : f.status)?.toUpperCase();
            const isCritical = sevStr === 'CRITICAL';
            const isHigh = sevStr === 'HIGH';
            const isApproved = stStr === 'APPROVED';
            const isRejected = stStr === 'REJECTED';
            const isPending = stStr === 'PRESENTED';

            return (
              <Card
                key={f.finding_id}
                className={`transition-all space-y-3 p-4 ${
                  isApproved
                    ? 'border-emerald-500/30 bg-emerald-500/5'
                    : isRejected
                    ? 'border-rose-500/30 bg-rose-500/5'
                    : isCritical
                    ? 'border-rose-500/40 bg-card/80'
                    : 'border-border bg-card/80'
                }`}
              >
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-zinc-400 font-bold">[{f.finding_id}]</span>
                    <span className="font-semibold text-foreground text-xs sm:text-sm">{f.title}</span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <Badge variant={isCritical ? 'destructive' : isHigh ? 'warning' : 'secondary'}>
                      {sevStr}
                    </Badge>
                    <Badge variant={isApproved ? 'success' : isRejected ? 'destructive' : 'warning'}>
                      {stStr}
                    </Badge>
                  </div>
                </div>

                <p className="text-muted-foreground text-xs leading-relaxed">
                  {f.description}
                </p>

                {/* Side-by-side Diffs */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 pt-1">
                  {f.source_a && (
                    <div className="p-3 rounded-lg bg-background/90 border border-border space-y-1">
                      <div className="flex items-center justify-between text-[11px] text-muted-foreground font-mono">
                        <span>Source A</span>
                        {f.source_a.filename && (
                          <button
                            onClick={() => onOpenDocDetail(f.source_a.filename)}
                            className="hover:underline text-zinc-300 truncate max-w-xs"
                          >
                            {f.source_a.filename} ({f.source_a.location})
                          </button>
                        )}
                      </div>
                      <p className="text-foreground italic text-xs">
                        "{f.source_a.exact_quote}"
                      </p>
                    </div>
                  )}

                  {f.source_b && (
                    <div className="p-3 rounded-lg bg-background/90 border border-border space-y-1">
                      <div className="flex items-center justify-between text-[11px] text-muted-foreground font-mono">
                        <span className="text-amber-400">Source B (Conflict)</span>
                        {f.source_b.filename && (
                          <button
                            onClick={() => onOpenDocDetail(f.source_b.filename)}
                            className="hover:underline text-zinc-300 truncate max-w-xs"
                          >
                            {f.source_b.filename} ({f.source_b.location})
                          </button>
                        )}
                      </div>
                      <p className="text-foreground italic text-xs">
                        "{f.source_b.exact_quote}"
                      </p>
                    </div>
                  )}
                </div>

                {f.resolution_action && (
                  <div className="p-2.5 rounded-lg bg-zinc-900/60 border border-zinc-800 text-[11px] text-zinc-300 flex items-center gap-2">
                    <Sparkles className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
                    <div>
                      <strong className="text-zinc-200">Remediation Action:</strong> {f.resolution_action}
                    </div>
                  </div>
                )}

                {/* Permanent Decision Record & Controls */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-2 border-t border-border/80">
                  <div className="text-[11px]">
                    {isApproved && (
                      <span className="text-emerald-400 font-medium flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Approved by {f.decided_by || 'Human Reviewer'}{f.decided_at ? ` on ${new Date(f.decided_at).toLocaleString()}` : ''}</span>
                      </span>
                    )}
                    {isRejected && (
                      <span className="text-rose-400 font-medium flex items-center gap-1">
                        <X className="w-3.5 h-3.5" />
                        <span>Rejected: <em>"{f.feedback || 'Disallowed'}"</em>{f.decided_at ? ` (${new Date(f.decided_at).toLocaleTimeString()})` : ''}</span>
                      </span>
                    )}
                    {isPending && (
                      <span className="text-amber-400 font-mono text-[10px] flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        <span>Awaiting Human Gate Decision</span>
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {/* Pending Actions */}
                    {isPending && (
                      <>
                        <Button
                          onClick={() => setRejectModalFinding(f)}
                          disabled={processingId === f.finding_id}
                          variant="outline"
                          size="sm"
                          className="h-7 text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 border-border"
                        >
                          <X className="w-3 h-3 mr-1" />
                          Reject
                        </Button>
                        <Button
                          onClick={() => handleApprove(f.finding_id)}
                          disabled={processingId === f.finding_id}
                          size="sm"
                          className="h-7 text-xs bg-emerald-600 hover:bg-emerald-500 text-white"
                        >
                          <Check className="w-3 h-3 mr-1" />
                          Approve Finding
                        </Button>
                      </>
                    )}

                    {/* Change / Re-evaluate Decision */}
                    {isApproved && (
                      <Button
                        onClick={() => setRejectModalFinding(f)}
                        disabled={processingId === f.finding_id}
                        variant="ghost"
                        size="sm"
                        className="h-6 text-[11px] text-muted-foreground hover:text-rose-400"
                      >
                        <RotateCcw className="w-2.5 h-2.5 mr-1" />
                        <span>Change to Reject</span>
                      </Button>
                    )}

                    {isRejected && (
                      <Button
                        onClick={() => handleApprove(f.finding_id)}
                        disabled={processingId === f.finding_id}
                        variant="ghost"
                        size="sm"
                        className="h-6 text-[11px] text-muted-foreground hover:text-emerald-400"
                      >
                        <RotateCcw className="w-2.5 h-2.5 mr-1" />
                        <span>Change to Approve</span>
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            );
          })
        )}
      </div>

      {/* Reject Reason Dialog */}
      <Dialog open={!!rejectModalFinding} onOpenChange={(open) => !open && setRejectModalFinding(null)}>
        {rejectModalFinding && (
          <>
            <DialogHeader>
              <DialogTitle>Reject Finding [{rejectModalFinding.finding_id}]</DialogTitle>
              <DialogDescription>
                Provide a reviewer reason or corrective instruction for rejecting this finding.
              </DialogDescription>
            </DialogHeader>

            <div className="py-3">
              <textarea
                value={rejectFeedback}
                onChange={(e) => setRejectFeedback(e.target.value)}
                placeholder="e.g. Verified on site with signed delivery pass..."
                rows={3}
                className="w-full bg-background border border-border rounded-lg p-2.5 text-xs text-foreground outline-none focus:border-zinc-500 resize-none"
              />
            </div>

            <DialogFooter>
              <Button onClick={() => setRejectModalFinding(null)} variant="ghost" size="sm">
                Cancel
              </Button>
              <Button onClick={handleRejectConfirm} variant="destructive" size="sm">
                Confirm Reject
              </Button>
            </DialogFooter>
          </>
        )}
      </Dialog>
    </div>
  );
}
