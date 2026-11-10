'use client';

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Globe } from 'lucide-react';
import { NODE_TYPE_COLORS } from '@codeatlas/shared';
import { useGraphStore } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';
import type { BaseNodeData } from './types';

const HTTP_METHOD_STYLES: Record<string, string> = {
  GET: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  POST: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  PUT: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  PATCH: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
  DELETE: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
  ALL: 'bg-slate-500/15 text-slate-300 border-slate-500/30',
};

function RouteNodeInner({ data }: NodeProps) {
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
  const nodeColor = NODE_TYPE_COLORS.route || '#EF4444';
  const httpMethod = (typeof meta.http_method === 'string' ? meta.http_method : 'GET').toUpperCase();
  const verbClass = HTTP_METHOD_STYLES[httpMethod] || HTTP_METHOD_STYLES.GET;
  const routePath = typeof meta.route_path === 'string' ? meta.route_path : node.name;
  const handlerName =
    typeof meta.controller === 'string'
      ? meta.controller
      : typeof meta.handler === 'string'
        ? meta.handler
        : node.name;
  const framework = typeof meta.framework === 'string' ? meta.framework : '';
  const params = Array.isArray(meta.params) ? meta.params : [];

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
      title={`${httpMethod} ${routePath}`}
      data-testid={`route-node-${node.id}`}
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

      {/* Header: Icon, HTTP Verb Pill & Route Path */}
      <div className="flex items-center gap-2">
        <div
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border"
          style={{
            backgroundColor: `${nodeColor}20`,
            borderColor: `${nodeColor}40`,
            color: nodeColor,
          }}
        >
          <Globe className="h-4 w-4" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 min-w-0">
            <span
              className={`shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold font-mono border ${verbClass}`}
            >
              {httpMethod}
            </span>
            <span
              className="truncate text-xs font-semibold font-mono text-foreground"
              title={routePath}
            >
              {routePath}
            </span>
          </div>
          <div className="truncate text-[10px] text-muted-foreground mt-0.5" title={handlerName}>
            handler: <span className="font-mono text-foreground/80">{handlerName}</span>
          </div>
        </div>
      </div>

      {/* Footer: Framework & Params Badges */}
      <div className="mt-2.5 flex flex-wrap items-center gap-1.5 border-t border-border/40 pt-2 text-[10px]">
        {framework && (
          <span className="rounded bg-muted px-1.5 py-0.5 text-muted-foreground capitalize">
            {framework}
          </span>
        )}
        {params.length > 0 && (
          <span className="rounded bg-rose-500/10 px-1.5 py-0.5 font-mono text-rose-400 border border-rose-500/20">
            {params.length} param{params.length > 1 ? 's' : ''}
          </span>
        )}
        {meta.middleware && (
          <span className="rounded bg-amber-500/10 px-1.5 py-0.5 text-amber-400 border border-amber-500/20">
            auth
          </span>
        )}
      </div>
    </div>
  );
}

export const RouteNode = memo(RouteNodeInner);
