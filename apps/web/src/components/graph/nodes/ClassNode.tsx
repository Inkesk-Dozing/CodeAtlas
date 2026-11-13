'use client';

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Box } from 'lucide-react';
import { NODE_TYPE_COLORS } from '@codeatlas/shared';
import { useGraphStore } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';
import type { BaseNodeData } from './types';

function ClassNodeInner({ data }: NodeProps) {
  const { node, isSelected, isHighlighted, isMapped, isVirtualProxy, isPulsing, onSelect } =
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
  const nodeColor = NODE_TYPE_COLORS.class || '#3B82F6';
  const bases = Array.isArray(meta.bases) ? meta.bases : [];
  const methods = Array.isArray(meta.methods) ? meta.methods : [];
  const fields = Array.isArray(meta.fields) ? meta.fields : [];
  const inheritance = bases.length > 0 ? `extends ${bases.join(', ')}` : null;

  const pulseClass = isPulsing
    ? 'animate-pulse ring-4 ring-cyan-400 shadow-[0_0_24px_rgba(6,182,212,0.9)] scale-[1.03]'
    : '';

  const glowClass = isSelected
    ? 'border-primary shadow-[0_0_16px_rgba(14,165,233,0.7)] ring-2 ring-primary ring-offset-2 ring-offset-background'
    : isMapped
      ? 'border-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.85)] ring-2 ring-emerald-400 ring-offset-1 ring-offset-background'
      : isHighlighted
        ? 'border-amber-400 shadow-[0_0_16px_rgba(245,158,11,0.7)] ring-2 ring-amber-400 ring-offset-1 ring-offset-background'
        : 'border-border/60 hover:border-cyan-400/90 hover:shadow-[0_0_14px_rgba(6,182,212,0.45)]';

  return (
    <div
      onClick={handleClick}
      className={`
        group relative w-[260px] rounded-lg border bg-card/95 p-3 shadow-sm
        transition-all duration-200 cursor-pointer select-none backdrop-blur-sm
        ${glowClass} ${pulseClass}
      `}
      title={node.name}
      data-testid={`class-node-${node.id}`}
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

      {/* Header: Icon, Class Name & Inheritance indicator */}
      <div className="flex items-center gap-2">
        <div
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border"
          style={{
            backgroundColor: `${nodeColor}20`,
            borderColor: `${nodeColor}40`,
            color: nodeColor,
          }}
        >
          <Box className="h-4 w-4" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="truncate text-xs font-semibold font-mono text-foreground" title={node.name}>
            {node.name}
          </div>
          {inheritance ? (
            <div className="truncate text-[10px] text-blue-400/90 font-mono" title={inheritance}>
              {inheritance}
            </div>
          ) : (
            <div className="truncate text-[10px] text-muted-foreground" title={node.path}>
              {node.path}
            </div>
          )}
        </div>
      </div>

      {/* Methods List Preview */}
      {methods.length > 0 && (
        <div className="mt-2 space-y-0.5 rounded bg-muted/40 p-1.5 text-[10px] font-mono border border-border/30">
          {methods.slice(0, 3).map((m, idx) => {
            const mName = typeof m === 'string' ? m : m.name;
            return (
              <div key={idx} className="flex items-center gap-1.5 truncate text-muted-foreground">
                <span className="text-blue-400 font-bold">&bull;</span>
                <span className="truncate">{mName}()</span>
              </div>
            );
          })}
          {methods.length > 3 && (
            <div className="text-[9px] text-muted-foreground/70 italic pl-2 pt-0.5">
              +{methods.length - 3} more method{methods.length - 3 === 1 ? '' : 's'}
            </div>
          )}
        </div>
      )}

      {/* Footer Badges */}
      <div className="mt-2.5 flex flex-wrap items-center gap-1.5 border-t border-border/40 pt-2 text-[10px]">
        <span className="rounded bg-blue-500/10 px-1.5 py-0.5 font-medium text-blue-400 border border-blue-500/20">
          {methods.length} method{methods.length === 1 ? '' : 's'}
        </span>
        {fields.length > 0 && (
          <span className="rounded bg-muted px-1.5 py-0.5 text-muted-foreground">
            {fields.length} field{fields.length === 1 ? '' : 's'}
          </span>
        )}
        {meta.is_service && (
          <span className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-emerald-400 border border-emerald-500/20">
            service
          </span>
        )}
      </div>
    </div>
  );
}

export const ClassNode = memo(ClassNodeInner);
