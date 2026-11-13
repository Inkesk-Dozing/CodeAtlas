'use client';

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Activity, Code2 } from 'lucide-react';
import { NODE_TYPE_COLORS } from '@codeatlas/shared';
import { useGraphStore } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';
import type { BaseNodeData } from './types';

function extractReturnType(signature?: string): string | null {
  if (!signature) return null;
  // Match `-> Type` (Python) or `: Type` / `: Promise<Type>` at the end (TypeScript)
  const pyMatch = signature.match(/->\s*([^{]+)$/);
  if (pyMatch) return pyMatch[1].trim();
  const tsMatch = signature.match(/\):\s*([^={]+)$/);
  if (tsMatch) return tsMatch[1].trim();
  return null;
}

function FunctionNodeInner({ data }: NodeProps) {
  const { node, isSelected, isHighlighted, isVirtualProxy, isPulsing, onSelect } =
    data as unknown as BaseNodeData;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    useGraphStore.getState().selectNode(node.id);
    useUIStore.getState().openPanel('node-detail');
    onSelect?.(node.id);
  };

  if (isVirtualProxy) {
    return (
      <div
        className="relative h-[72px] w-[260px] rounded-lg border border-dashed border-border/40 bg-card/10 opacity-30 pointer-events-none"
        aria-hidden="true"
      >
        <Handle type="target" position={Position.Left} className="opacity-0" isConnectable={false} />
        <Handle type="source" position={Position.Right} className="opacity-0" isConnectable={false} />
      </div>
    );
  }

  const meta = node.metadata || {};
  const nodeColor = NODE_TYPE_COLORS.function || '#10B981';
  const cyclomatic = meta.complexity?.cyclomatic ?? 1;
  const isAsync = Boolean(meta.is_async);
  const signature = meta.signature || '';
  const returnType = extractReturnType(signature);

  // Complexity pill color logic
  let complexityBadge = 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
  let isComplex = false;
  if (cyclomatic > 10) {
    complexityBadge = 'bg-rose-500/15 text-rose-400 border-rose-500/30';
    isComplex = true;
  } else if (cyclomatic > 5) {
    complexityBadge = 'bg-amber-500/15 text-amber-400 border-amber-500/30';
  }

  const glowClass = isSelected
    ? 'border-primary shadow-[0_0_16px_rgba(14,165,233,0.7)] ring-2 ring-primary ring-offset-2 ring-offset-background'
    : isHighlighted
      ? 'border-amber-400 shadow-[0_0_16px_rgba(245,158,11,0.7)] ring-2 ring-amber-400 ring-offset-1 ring-offset-background'
      : 'border-border/60 hover:border-cyan-400/90 hover:shadow-[0_0_14px_rgba(6,182,212,0.45)]';

  const pulseClass = isPulsing
    ? 'animate-pulse ring-4 ring-cyan-400 shadow-[0_0_24px_rgba(6,182,212,0.9)] scale-[1.03]'
    : '';

  return (
    <div
      onClick={handleClick}
      className={`
        group relative w-[260px] rounded-lg border bg-card/95 p-3 shadow-sm
        transition-all duration-200 cursor-pointer select-none backdrop-blur-sm
        ${glowClass} ${pulseClass}
      `}
      title={signature || node.name}
      data-testid={`function-node-${node.id}`}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!h-2.5 !w-2.5 !rounded-full !border-2 !border-background !bg-muted-foreground/70 transition-colors hover:!bg-primary"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!h-2.5 !w-2.5 !rounded-full !border-2 !border-background !bg-muted-foreground/70 transition-colors hover:!bg-primary"
      />

      {/* Header: Icon, Function Name & Async Badge */}
      <div className="flex items-center gap-2">
        <div
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border"
          style={{
            backgroundColor: `${nodeColor}20`,
            borderColor: `${nodeColor}40`,
            color: nodeColor,
          }}
        >
          <Code2 className="h-4 w-4" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <span className="truncate text-xs font-semibold font-mono text-foreground" title={node.name}>
              {node.name}
            </span>
            {isAsync && (
              <span className="shrink-0 rounded bg-blue-500/15 px-1 py-0.2 font-mono text-[8px] font-medium text-blue-400 border border-blue-500/30">
                async
              </span>
            )}
          </div>
          <div className="truncate text-[10px] text-muted-foreground" title={node.path}>
            {node.path}
          </div>
        </div>
      </div>

      {/* Parameter Signature preview */}
      {signature ? (
        <div
          className="mt-2 rounded bg-muted/50 px-2 py-1 font-mono text-[10px] text-muted-foreground truncate border border-border/30"
          title={signature}
        >
          {signature}
        </div>
      ) : null}

      {/* Footer: Return Type and Complexity Pill */}
      <div className="mt-2.5 flex flex-wrap items-center gap-1.5 border-t border-border/40 pt-2 text-[10px]">
        {returnType && (
          <span
            className="rounded bg-purple-500/15 px-1.5 py-0.5 font-mono text-[9px] text-purple-400 border border-purple-500/30 truncate max-w-[110px]"
            title={returnType}
          >
            &rarr; {returnType}
          </span>
        )}
        <span
          className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[9px] font-medium font-mono ${complexityBadge}`}
        >
          <Activity className="h-2.5 w-2.5" />
          CC {cyclomatic}
        </span>
        {isComplex && (
          <span className="rounded bg-rose-500/20 px-1 py-0.5 text-[8px] font-bold uppercase tracking-wider text-rose-400 border border-rose-500/40">
            complex
          </span>
        )}
      </div>
    </div>
  );
}

export const FunctionNode = memo(FunctionNodeInner);
