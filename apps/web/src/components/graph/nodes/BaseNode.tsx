'use client';

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { NODE_TYPE_COLORS } from '@codeatlas/shared';
import { useGraphStore } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';
import type { BaseNodeData } from './types';

export type { BaseNodeData } from './types';

function BaseNodeInner({ data }: NodeProps) {
  const { node, isSelected, isHighlighted, isMapped, isVirtualProxy, onSelect } =
    data as unknown as BaseNodeData;
  const color = NODE_TYPE_COLORS[node.type] || '#6B7280';
  const meta = node.metadata || {};

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    useGraphStore.getState().selectNode(node.id);
    useUIStore.getState().openPanel('node-detail');
    onSelect?.(node.id);
  };

  // If node is unmounted / off-screen proxy, render lightweight proxy bounding box
  if (isVirtualProxy) {
    return (
      <div
        className="relative h-[72px] w-[260px] rounded-lg border border-dashed border-border/40 bg-card/10 opacity-30 pointer-events-none"
        aria-hidden="true"
      >
        <Handle type="target" position={Position.Left} className="opacity-0" isConnectable={false} />
        <Handle type="source" position={Position.Right} className="opacity-0" isConnectable={false} />
        <Handle type="target" position={Position.Top} className="opacity-0" isConnectable={false} />
        <Handle type="source" position={Position.Bottom} className="opacity-0" isConnectable={false} />
      </div>
    );
  }

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
        ${glowClass}
      `}
      data-testid={`base-node-${node.id}`}
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
      <Handle type="target" position={Position.Top} className="opacity-0 pointer-events-none" isConnectable={false} />
      <Handle type="source" position={Position.Bottom} className="opacity-0 pointer-events-none" isConnectable={false} />

      <div className="flex items-center gap-2">
        <div
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border text-[11px] font-bold"
          style={{
            backgroundColor: `${color}20`,
            borderColor: `${color}40`,
            color,
          }}
        >
          {node.type.charAt(0).toUpperCase()}
        </div>

        <div className="min-w-0 flex-1">
          <div className="truncate text-xs font-semibold text-foreground" title={node.name}>
            {node.name}
          </div>
          <div className="truncate text-[10px] text-muted-foreground" title={node.path}>
            {node.path}
          </div>
        </div>
      </div>

      <div className="mt-2.5 flex flex-wrap items-center gap-1.5 border-t border-border/40 pt-2 text-[10px]">
        <span
          className="rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider"
          style={{ backgroundColor: `${color}15`, color }}
        >
          {node.type}
        </span>
        {meta.http_method && (
          <span className="rounded bg-rose-500/10 px-1.5 py-0.5 font-mono text-rose-400 border border-rose-500/20">
            {meta.http_method}
          </span>
        )}
        {meta.loc && (
          <span className="rounded bg-muted px-1.5 py-0.5 text-muted-foreground font-mono">
            {meta.loc} LOC
          </span>
        )}
        {(meta.complexity?.cyclomatic ?? 0) > 10 && (
          <span className="rounded bg-rose-500/15 px-1.5 py-0.5 text-rose-400 border border-rose-500/30">
            complex
          </span>
        )}
        {meta.is_async && (
          <span className="rounded bg-blue-500/15 px-1.5 py-0.5 text-blue-400 border border-blue-500/30">
            async
          </span>
        )}
        {node.type === 'component' && (meta.hooks_used?.length ?? 0) > 0 && (
          <span className="rounded bg-cyan-500/15 px-1.5 py-0.5 text-cyan-400 border border-cyan-500/30">
            {meta.hooks_used?.length} hooks
          </span>
        )}
        {node.type === 'class' && (meta.methods?.length ?? 0) > 0 && (
          <span className="rounded bg-purple-500/15 px-1.5 py-0.5 text-purple-400 border border-purple-500/30">
            {meta.methods?.length} methods
          </span>
        )}
        {node.type === 'model' && (meta.fields?.length ?? 0) > 0 && (
          <span className="rounded bg-pink-500/15 px-1.5 py-0.5 text-pink-400 border border-pink-500/30">
            {meta.fields?.length} fields
          </span>
        )}
      </div>

      {node.summary && (
        <div className="mt-1 hidden max-w-[240px] text-[10px] leading-tight text-muted-foreground group-hover:block">
          {node.summary.slice(0, 80)}...
        </div>
      )}
    </div>
  );
}

export const BaseNode = memo(BaseNodeInner);
