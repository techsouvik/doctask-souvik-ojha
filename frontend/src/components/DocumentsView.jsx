import React, { useState, useRef } from 'react';
import { 
  FileText, 
  UploadCloud, 
  Search, 
  CheckCircle, 
  AlertTriangle, 
  RefreshCw, 
  Eye,
  Plus
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { uploadDocument } from '../services/api';

export default function DocumentsView({
  projectId,
  documents,
  onRefreshProject,
  onOpenDocDetail
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const fileInputRef = useRef(null);

  const handleFiles = async (files) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        await uploadDocument(projectId, file);
      }
      onRefreshProject();
    } catch (err) {
      alert('Upload error: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  const filteredDocs = documents.filter(d => 
    d.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (d.doc_type && String(d.doc_type).toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 max-w-5xl mx-auto w-full text-xs">
      {/* Top Header with Upload Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <FileText className="w-4 h-4 text-zinc-400" />
            Document Vault
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Ingested multi-format document pile with automatic classification and 100% quote grounding verification.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => handleFiles(e.target.files)}
            multiple
            accept=".docx,.pdf,.txt"
            className="hidden"
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            size="sm"
            variant="default"
            className="gap-1.5"
          >
            {uploading ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Plus className="w-3.5 h-3.5" />
            )}
            <span>{uploading ? 'Uploading...' : 'Upload Files'}</span>
          </Button>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
        className={`p-6 rounded-xl border border-dashed text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-zinc-400 bg-zinc-800/40'
            : 'border-border hover:border-zinc-700 bg-card/40'
        }`}
      >
        <div className="max-w-xs mx-auto space-y-1">
          <UploadCloud className="w-5 h-5 mx-auto text-muted-foreground" />
          <p className="font-medium text-foreground">Drop files to ingest into project</p>
          <p className="text-[11px] text-muted-foreground">Supports contracts, status reports, invoices (.docx, .pdf, .txt)</p>
        </div>
      </div>

      {/* Search & Document List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter documents..."
              className="w-full pl-8 pr-3 py-1 rounded-lg bg-background border border-border text-xs text-foreground placeholder:text-muted-foreground outline-none focus:border-zinc-500"
            />
          </div>

          <span className="text-[11px] text-muted-foreground font-mono">
            {filteredDocs.length} files
          </span>
        </div>

        {/* Minimalist Document Table / Card List */}
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-border bg-background/50 text-muted-foreground text-[10px] uppercase font-mono">
              <tr>
                <th className="p-3">File Name</th>
                <th className="p-3">Classification</th>
                <th className="p-3">Indexed Chunks</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/80">
              {filteredDocs.map((doc) => {
                const ext = doc.filename.split('.').pop()?.toUpperCase() || 'FILE';
                const isQuarantined = doc.quarantined;
                const docTypeStr = doc.doc_type?.value || String(doc.doc_type || 'UNCLASSIFIED');

                return (
                  <tr key={doc.doc_id || doc.filename} className="hover:bg-accent/40 transition">
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300 font-bold">
                          {ext}
                        </span>
                        <span className="font-medium text-foreground truncate max-w-xs" title={doc.filename}>
                          {doc.filename}
                        </span>
                      </div>
                    </td>
                    <td className="p-3">
                      <Badge variant="outline" className="text-[10px]">
                        {docTypeStr}
                      </Badge>
                    </td>
                    <td className="p-3 text-muted-foreground font-mono">
                      {doc.chunks?.length || 0} chunks
                    </td>
                    <td className="p-3">
                      {isQuarantined ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-rose-400">
                          <AlertTriangle className="w-3 h-3" /> Quarantined
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400">
                          <CheckCircle className="w-3 h-3" /> Active
                        </span>
                      )}
                    </td>
                    <td className="p-3 text-right">
                      <Button
                        onClick={() => onOpenDocDetail(doc.doc_id || doc.filename)}
                        variant="ghost"
                        size="sm"
                        className="h-7 text-[11px] text-muted-foreground hover:text-foreground"
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        Inspect
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
