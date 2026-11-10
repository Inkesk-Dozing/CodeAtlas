'use client';

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Component, Sparkles } from 'lucide-react';
import { NODE_TYPE_COLORS } from '@codeatlas/shared';
import { useGraphStore } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';
import type { BaseNodeData } from './types';

function ComponentNodeInner({ data }: NodeProps) {
  const { node, isSelected, isHighlighted, isVirtualProxy, onSelect } =
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
  const nodeColor = NODE_TYPE_COLORS.component || '#06B6D4';
  const hooksUsed = Array.isArray(meta.hooks_used) ? meta.hooks_used : [];
  const props = Array.isArray(meta.props) ? meta.props : [];
  const propsCount = props.length > 0 ? props.length : typeof meta.props_count === 'number' ? meta.props_count : undefined;

  const glowClass = isSelected
    ? 'border-primary shadow-[0_0_16px_rgba(14,165,233,0.7)] ring-2 ring-primary ring-offset-2 ring-offset-background'
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
      title={node.name}
      data-testid={`component-node-${node.id}`}
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

      {/* Header: Icon, Component Name & UI Tag */}
      <div className="flex items-center gap-2">
        <div
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border"
          style={{
            backgroundColor: `${nodeColor}20`,
            borderColor: `${nodeColor}40`,
            color: nodeColor,
          }}
        >
          <Component className="h-4 w-4" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <span className="truncate text-xs font-semibold text-foreground font-mono" title={node.name}>
              {node.name}
            </span>
            <span className="shrink-0 rounded bg-cyan-500/15 px-1 py-0.2 font-mono text-[8px] font-bold text-cyan-400 border border-cyan-500/30">
              React
            </span>
          </div>
          <div className="truncate text-[10px] text-muted-foreground" title={node.path}>
            {node.path}
          </div>
        </div>
      </div>

      {/* Hooks Preview Badges */}
      {hooksUsed.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {hooksUsed.slice(0, 3).map((hook, idx) => (
            <span
              key={idx}
              className="rounded bg-muted/60 px-1.5 py-0.5 font-mono text-[8px] text-cyan-400 border border-cyan-500/20"
            >
              {hook}
            </span>
          ))}
          {hooksUsed.length > 3 && (
            <span className="self-center text-[8px] text-muted-foreground font-mono">
              +{hooksUsed.length - 3}
            </span>
          )}
        </div>
      )}

      {/* Footer: Hook Count & Props Count */}
      <div className="mt-2.5 flex flex-wrap items-center gap-1.5 border-t border-border/40 pt-2 text-[10px]">
        <span className="inline-flex items-center gap-1 rounded bg-cyan-500/10 px-1.5 py-0.5 font-medium text-cyan-400 border border-cyan-500/20">
          <Sparkles className="h-2.5 w-2.5" />
          {hooksUsed.length} hook{hooksUsed.length === 1 ? '' : 's'}
        </span>
        {propsCount !== undefined && (
          <span className="rounded bg-muted px-1.5 py-0.5 text-muted-foreground">
            {propsCount} prop{propsCount === 1 ? '' : 's'}
          </span>
        )}
      </div>
    </div>
  );
}

export const ComponentNode = memo(ComponentNodeInner);
