import React, { useState, useEffect, useRef } from 'react';
import { Search, FileText } from 'lucide-react';
import { Dialog } from './ui/dialog';
import { searchChunks } from '../services/api';

export default function SpotlightSearchModal({
  isOpen,
  onClose,
  projectId,
  onSelectDoc
}) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery('');
      setResults([]);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await searchChunks(projectId, query.trim(), 5);
        setResults(data.results || []);
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setLoading(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [query, projectId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4">
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-50 w-full max-w-xl rounded-xl border border-border bg-card shadow-2xl overflow-hidden animate-fade-in text-xs">
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3 border-b border-border bg-background/50">
          <Search className="w-4 h-4 text-muted-foreground mr-3" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search across all document chunks (e.g. penalty, steel, invoice)..."
            className="w-full bg-transparent text-xs text-foreground placeholder:text-muted-foreground outline-none"
          />
          <kbd className="text-[10px] bg-zinc-800 text-muted-foreground px-1.5 py-0.5 rounded border border-border font-mono">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          {loading && (
            <p className="text-[11px] text-muted-foreground text-center py-6">Searching index...</p>
          )}

          {!loading && query && results.length === 0 && (
            <p className="text-[11px] text-muted-foreground text-center py-6">No matching chunks found.</p>
          )}

          {!query && (
            <p className="text-[11px] text-muted-foreground text-center py-6">Type keywords to search instantly.</p>
          )}

          {results.map((res, idx) => (
            <div
              key={idx}
              onClick={() => {
                onClose();
                onSelectDoc(res.doc_name);
              }}
              className="p-2.5 rounded-lg hover:bg-accent/60 cursor-pointer transition space-y-1"
            >
              <div className="flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-1.5 font-medium text-foreground">
                  <FileText className="w-3.5 h-3.5 text-muted-foreground" />
                  <span>{res.doc_name}</span>
                  <span className="text-muted-foreground font-mono text-[10px]">({res.section_title || 'Section'})</span>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">Score: {res.score}</span>
              </div>
              <p className="text-[11px] text-muted-foreground italic line-clamp-2">
                "{res.text}"
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
