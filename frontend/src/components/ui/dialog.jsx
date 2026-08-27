import * as React from 'react';
import { cn } from '../../lib/utils';
import { X } from 'lucide-react';

function Dialog({ open, onOpenChange, children }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
        onClick={() => onOpenChange?.(false)}
      />
      {/* Content */}
      <div className="relative z-50 w-full max-w-lg rounded-xl border border-border bg-card p-5 shadow-2xl animate-fade-in text-card-foreground">
        {children}
      </div>
    </div>
  );
}

function DialogHeader({ className, children, ...props }) {
  return (
    <div className={cn("flex flex-col space-y-1.5 pb-4 border-b border-border/80", className)} {...props}>
      {children}
    </div>
  );
}

function DialogTitle({ className, children, ...props }) {
  return (
    <h2 className={cn("text-sm font-semibold leading-none tracking-tight text-foreground", className)} {...props}>
      {children}
    </h2>
  );
}

function DialogDescription({ className, children, ...props }) {
  return (
    <p className={cn("text-xs text-muted-foreground", className)} {...props}>
      {children}
    </p>
  );
}

function DialogFooter({ className, children, ...props }) {
  return (
    <div className={cn("flex items-center justify-end gap-2 pt-4 border-t border-border/80", className)} {...props}>
      {children}
    </div>
  );
}

export { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter };
