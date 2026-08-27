import * as React from 'react';
import { cva } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-semibold transition-colors focus:outline-none focus:ring-1 focus:ring-ring",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground shadow-sm",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-transparent bg-rose-500/15 text-rose-300 border border-rose-500/30",
        outline: "text-foreground border-border",
        success: "border-transparent bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
        warning: "border-transparent bg-amber-500/15 text-amber-300 border border-amber-500/30",
        info: "border-transparent bg-blue-500/15 text-blue-300 border border-blue-500/30",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

function Badge({ className, variant, ...props }) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
