'use client';

import { memo } from 'react';
import { getBezierPath, EdgeLabelRenderer, type EdgeProps } from '@xyflow/react';

const EDGE_STYLES: Record<string, { color: string; dash: string; width: number; animated: boolean }> = {
  imports: { color: '#9CA3AF', dash: '6,4', width: 1.5, animated: false },
  calls: { color: '#3B82F6', dash: 'none', width: 2, animated: true },
  extends: { color: '#8B5CF6', dash: 'none', width: 2, animated: false },
  implements: { color: '#8B5CF6', dash: '6,4', width: 1.5, animated: false },
  routes_to: { color: '#10B981', dash: 'none', width: 2.5, animated: true },
  renders: { color: '#06B6D4', dash: '4,4', width: 1.5, animated: false },
  uses_hook: { color: '#F97316', dash: '4,4', width: 1.5, animated: false },
  contains: { color: '#6B7280', dash: '2,4', width: 1, animated: false },
  middleware_for: { color: '#F59E0B', dash: 'none', width: 2, animated: false },
  has_model: { color: '#EC4899', dash: 'none', width: 1.5, animated: false },
  reads: { color: '#10B981', dash: '6,4', width: 1, animated: false },
  writes: { color: '#EF4444', dash: '6,4', width: 1, animated: false },
};

function BaseEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  markerEnd,
  style,
}: EdgeProps) {
  const edgeType = (data?.edgeType as string | undefined) || 'imports';
  const edgeStyle = EDGE_STYLES[edgeType] || EDGE_STYLES.imports;

  const [path, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    curvature: 0.25,
  });

  return (
    <>
      <path
        id={id}
        d={path}
        stroke={edgeStyle.color}
        strokeWidth={edgeStyle.width}
        strokeDasharray={edgeStyle.dash !== 'none' ? edgeStyle.dash : undefined}
        markerEnd={markerEnd}
        className={edgeStyle.animated ? 'animate-pulse' : ''}
        style={style}
      />
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: 'all',
          }}
          className="nodrag nopan opacity-0 transition-opacity hover:opacity-100"
        >
          <div className="rounded border border-border bg-background px-1.5 py-0.5 text-[9px] font-medium text-muted-foreground shadow-sm">
            {edgeType.replace(/_/g, ' ')}
          </div>
        </div>
      </EdgeLabelRenderer>
    </>
  );
}

export const FlowEdge = memo(BaseEdge);
