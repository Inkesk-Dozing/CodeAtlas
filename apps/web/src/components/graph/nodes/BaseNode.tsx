'use client';

import { memo } from 'react';
import type { NodeProps } from '@xyflow/react';
import type { GraphNode } from '@/stores/graphStore';
import { NODE_TYPE_COLORS } from '@codeatlas/shared';

interface BaseNodeData {
  node: GraphNode;
  isSelected: boolean;
  isHighlighted: boolean;
}

function BaseNodeInner({ data }: NodeProps) {
  const { node, isSelected, isHighlighted } = data as unknown as BaseNodeData;
  const color = NODE_TYPE_COLORS[node.type] || '#6B7280';
  const meta = node.metadata || {};

  const ringClass = isSelected
    ? 'ring-2 ring-primary ring-offset-2 ring-offset-background'
    : isHighlighted
      ? 'ring-2 ring-amber-400 ring-offset-1 ring-offset-background'
      : '';

  return (
    <div
      className={`
        group relative rounded-lg border bg-card px-3 py-2 shadow-sm
        transition-all duration-150 hover:shadow-md
        ${ringClass}
      `}
      style={{ borderColor: isHighlighted ? '#F59E0B' : isSelected ? 'hsl(var(--primary))' : 'hsl(var(--border))' }}
    >
      <div className="flex items-center gap-2">
        <div
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded text-[10px] font-bold text-white"
          style={{ backgroundColor: color }}
        >
          {node.type.charAt(0).toUpperCase()}
        </div>

        <div className="min-w-0">
          <div className="truncate text-xs font-semibold" title={node.name}>
            {node.name}
          </div>
          <div className="truncate text-[10px] text-muted-foreground" title={node.path}>
            {node.path}
          </div>
        </div>
      </div>

      <div className="mt-1 flex flex-wrap gap-1">
        {meta.http_method && (
          <span className="rounded bg-red-100 px-1 py-0.5 text-[9px] font-medium text-red-700 dark:bg-red-900/30 dark:text-red-400">
            {meta.http_method}
          </span>
        )}
        {meta.loc && (
          <span className="rounded bg-muted px-1 py-0.5 text-[9px] text-muted-foreground">
            {meta.loc} LOC
          </span>
        )}
        {(meta.complexity?.cyclomatic ?? 0) > 10 && (
          <span className="rounded bg-amber-100 px-1 py-0.5 text-[9px] font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
            complex
          </span>
        )}
        {meta.is_async && (
          <span className="rounded bg-blue-100 px-1 py-0.5 text-[9px] font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
            async
          </span>
        )}
        {node.type === 'component' && (meta.hooks_used?.length ?? 0) > 0 && (
          <span className="rounded bg-cyan-100 px-1 py-0.5 text-[9px] font-medium text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400">
            {meta.hooks_used?.length} hooks
          </span>
        )}
        {node.type === 'class' && (meta.methods?.length ?? 0) > 0 && (
          <span className="rounded bg-purple-100 px-1 py-0.5 text-[9px] font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
            {meta.methods?.length} methods
          </span>
        )}
        {node.type === 'model' && (meta.fields?.length ?? 0) > 0 && (
          <span className="rounded bg-pink-100 px-1 py-0.5 text-[9px] font-medium text-pink-700 dark:bg-pink-900/30 dark:text-pink-400">
            {meta.fields?.length} fields
          </span>
        )}
      </div>

      {node.summary && (
        <div className="mt-1 hidden max-w-[200px] text-[10px] leading-tight text-muted-foreground group-hover:block">
          {node.summary.slice(0, 80)}...
        </div>
      )}
    </div>
  );
}

export const BaseNode = memo(BaseNodeInner);
