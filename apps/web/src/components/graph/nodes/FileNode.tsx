'use client';

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { FileCode, Hash } from 'lucide-react';
import { LANGUAGE_COLORS, NODE_TYPE_COLORS } from '@codeatlas/shared';
import { useGraphStore } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';
import type { BaseNodeData } from './types';

function FileNodeInner({ data }: NodeProps) {
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
  const langKey = node.language?.toLowerCase() || 'unknown';
  const langColor = LANGUAGE_COLORS[langKey] || '#6B7280';
  const nodeColor = NODE_TYPE_COLORS.file || '#6B7280';
  const loc = typeof meta.loc === 'number' ? meta.loc : typeof meta.size === 'number' ? meta.size : undefined;
  const exportsCount = Array.isArray(meta.exports) ? meta.exports.length : 0;

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
      title={node.path}
      data-testid={`file-node-${node.id}`}
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

      {/* Header: Icon, Name & Language Tag */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <div
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border"
            style={{
              backgroundColor: `${nodeColor}20`,
              borderColor: `${nodeColor}40`,
              color: nodeColor,
            }}
          >
            <FileCode className="h-4 w-4" />
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

        {node.language && (
          <span
            className="shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-white shadow-sm"
            style={{ backgroundColor: langColor }}
          >
            {node.language.slice(0, 4).toUpperCase()}
          </span>
        )}
      </div>

      {/* Details: Line Count & Exports Badges */}
      <div className="mt-2.5 flex flex-wrap items-center gap-1.5 border-t border-border/40 pt-2 text-[10px]">
        {loc !== undefined && (
          <span className="inline-flex items-center gap-1 rounded bg-muted/80 px-1.5 py-0.5 font-mono text-muted-foreground">
            <Hash className="h-2.5 w-2.5" />
            {loc} LOC
          </span>
        )}
        {exportsCount > 0 && (
          <span className="rounded bg-primary/10 px-1.5 py-0.5 text-primary border border-primary/20">
            {exportsCount} export{exportsCount === 1 ? '' : 's'}
          </span>
        )}
        {Boolean(meta.is_monorepo) && (
          <span className="rounded bg-violet-500/10 px-1.5 py-0.5 text-violet-400 border border-violet-500/20">
            workspace
          </span>
        )}
      </div>
    </div>
  );
}

export const FileNode = memo(FileNodeInner);
