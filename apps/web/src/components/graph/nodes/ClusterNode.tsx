'use client';

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

export interface ClusterNodeData {
  clusterId: string;
  directory: string;
  depth: number;
  fileCount: number;
  isCollapsed: boolean;
  onToggleCollapse?: (clusterId: string) => void;
}

function ClusterNodeInner({ data }: NodeProps) {
  const { clusterId, directory, depth, fileCount, isCollapsed, onToggleCollapse } =
    data as unknown as ClusterNodeData;

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggleCollapse?.(clusterId);
  };

  return (
    <div
      onDoubleClick={handleToggle}
      className={`
        group relative min-w-[260px] rounded-xl border-2 border-primary/40 bg-card/95 p-3 shadow-md
        transition-all duration-200 hover:border-primary hover:shadow-lg
        cursor-pointer select-none
      `}
      title="Double-click to expand or collapse"
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!h-2.5 !w-2.5 !rounded-full !border-2 !border-background !bg-primary/80 transition-colors hover:!bg-primary"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!h-2.5 !w-2.5 !rounded-full !border-2 !border-background !bg-primary/80 transition-colors hover:!bg-primary"
      />
      <Handle type="target" position={Position.Top} className="opacity-0 pointer-events-none" isConnectable={false} />
      <Handle type="source" position={Position.Bottom} className="opacity-0 pointer-events-none" isConnectable={false} />

      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 overflow-hidden">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary font-mono text-xs font-bold">
            📁
          </div>
          <div className="min-w-0">
            <div className="truncate font-mono text-xs font-bold text-foreground">
              {directory}
            </div>
            <div className="text-[10px] text-muted-foreground">
              Depth level {depth}
            </div>
          </div>
        </div>

        <button
          onClick={handleToggle}
          type="button"
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded border border-border bg-muted/60 text-xs font-bold text-muted-foreground transition hover:bg-primary hover:text-primary-foreground"
          aria-label={isCollapsed ? 'Expand directory' : 'Collapse directory'}
        >
          {isCollapsed ? '+' : '−'}
        </button>
      </div>

      <div className="mt-2.5 flex items-center justify-between border-t border-border/60 pt-2 text-[10px]">
        <span className="font-medium text-muted-foreground">
          {fileCount} {fileCount === 1 ? 'file' : 'files'} bundled
        </span>
        <span className="rounded-full bg-primary/15 px-2 py-0.5 font-semibold text-primary">
          {isCollapsed ? 'Collapsed' : 'Expanded'}
        </span>
      </div>
    </div>
  );
}

export const ClusterNode = memo(ClusterNodeInner);

