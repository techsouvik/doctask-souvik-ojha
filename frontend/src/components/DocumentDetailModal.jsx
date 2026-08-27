import React, { useState, useEffect } from 'react';
import { FileText, RefreshCw } from 'lucide-react';
import { Dialog, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Badge } from './ui/badge';
import { fetchDocumentDetail } from '../services/api';

export default function DocumentDetailModal({
  docId,
  projectId,
  onClose
}) {
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('chunks');

  useEffect(() => {
    if (docId) {
      loadDoc();
    }
  }, [docId, projectId]);

  const loadDoc = async () => {
    setLoading(true);
    try {
      const data = await fetchDocumentDetail(projectId, docId);
      setDoc(data);
    } catch (err) {
      console.error('Failed to load document details:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!docId) return null;

  return (
    <Dialog open={!!docId} onOpenChange={(open) => !open && onClose()}>
      <div className="flex flex-col h-[75vh] -m-5">
        <div className="p-4 border-b border-border flex items-center justify-between bg-card">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-zinc-400" />
            <div>
              <h3 className="text-xs font-semibold text-foreground truncate max-w-sm">
                {doc?.filename || docId}
              </h3>
              <p className="text-[10px] text-muted-foreground font-mono">
                {doc?.doc_type?.value || String(doc?.doc_type || 'N/A')} • {doc?.chunks?.length || 0} chunks
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex bg-background rounded-lg p-0.5 border border-border text-[11px]">
              <button
                onClick={() => setActiveTab('chunks')}
                className={`px-2 py-0.5 rounded-md font-medium transition ${
                  activeTab === 'chunks' ? 'bg-zinc-800 text-foreground' : 'text-muted-foreground'
                }`}
              >
                Chunks
              </button>
              <button
                onClick={() => setActiveTab('text')}
                className={`px-2 py-0.5 rounded-md font-medium transition ${
                  activeTab === 'text' ? 'bg-zinc-800 text-foreground' : 'text-muted-foreground'
                }`}
              >
                Full Text
              </button>
            </div>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-xs ml-1">✕</button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs">
          {loading && (
            <div className="py-20 text-center text-muted-foreground">
              <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-zinc-400" />
              <p>Loading document content...</p>
            </div>
          )}

          {!loading && doc && activeTab === 'chunks' && (
            <div className="space-y-2.5">
              {doc.chunks?.map((chunk, idx) => (
                <div key={chunk.chunk_id || idx} className="p-3 rounded-lg bg-background border border-border space-y-1.5">
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground font-mono">
                    <span className="font-semibold text-zinc-300">
                      Chunk #{idx + 1}: {chunk.section_title || 'Main'}
                    </span>
                    <span>Page {chunk.page_num || 1}</span>
                  </div>
                  <p className="text-foreground leading-relaxed whitespace-pre-wrap font-sans text-xs">
                    {chunk.text}
                  </p>
                </div>
              ))}
            </div>
          )}

          {!loading && doc && activeTab === 'text' && (
            <div className="p-3 rounded-lg bg-background border border-border font-mono text-[11px] text-zinc-300 whitespace-pre-wrap leading-relaxed">
              {doc.extracted_text || 'No text extracted.'}
            </div>
          )}
        </div>
      </div>
    </Dialog>
  );
}
