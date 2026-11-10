'use client';

import React, { memo } from 'react';
import {
  EdgeLabelRenderer,
  getBezierPath,
  getSmoothStepPath,
  type EdgeProps,
} from '@xyflow/react';
import { getEdgeStyle, type CustomEdgeData } from './types';

export interface EdgeTooltipProps {
  id: string;
  edgeType: string;
  count: number;
  isHighlighted: boolean;
  isDimmed: boolean;
  sourceName: string;
  targetName: string;
  edgeColor: string;
  labelX: number;
  labelY: number;
}

export function EdgeTooltip({
  id,
  edgeType,
  count,
  isHighlighted,
  isDimmed,
  sourceName,
  targetName,
  edgeColor,
  labelX,
  labelY,
}: EdgeTooltipProps) {
  return (
    <div
      style={{
        position: 'absolute',
        transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
        pointerEvents: 'all',
      }}
      className={`nodrag nopan group/edge transition-opacity duration-150 ${
        isDimmed
          ? 'opacity-20'
          : isHighlighted
            ? 'opacity-100 z-30'
            : 'opacity-85 hover:opacity-100 z-10'
      }`}
      data-testid={`edge-label-${id}`}
    >
      {/* Badge Label */}
      <div
        className={`
          flex items-center gap-1.5 rounded-full border bg-background/95 px-2 py-0.5 text-[9px] font-mono shadow-sm
          transition-all duration-150 backdrop-blur-md cursor-pointer select-none
          ${
            isHighlighted
              ? 'border-primary ring-1 ring-primary shadow-[0_0_10px_rgba(14,165,233,0.4)]'
              : 'border-border/80 hover:border-primary/80 hover:shadow-md'
          }
        `}
      >
        <span
          className="h-1.5 w-1.5 shrink-0 rounded-full"
          style={{ backgroundColor: edgeColor }}
        />
        <span className="font-semibold uppercase tracking-wider text-muted-foreground">
          {edgeType.replace(/_/g, ' ').toUpperCase()}
        </span>
        {count > 1 && (
          <span className="font-bold text-primary">({count})</span>
        )}
      </div>

      {/* Hover Tooltip: Caller / Callee Context */}
      <div
        className={`
          pointer-events-none absolute left-1/2 top-full z-50 mt-1.5 hidden -translate-x-1/2 flex-col gap-1.5
          rounded-lg border border-border/90 bg-popover/95 p-2.5 shadow-xl backdrop-blur-md
          group-hover/edge:flex min-w-[200px] max-w-[280px]
        `}
        data-testid={`edge-tooltip-${id}`}
      >
        <div className="flex items-center justify-between border-b border-border/50 pb-1 text-[9px] font-mono">
          <span
            className="font-bold uppercase tracking-wider"
            style={{ color: edgeColor }}
          >
            {edgeType.replace(/_/g, ' ').toUpperCase()}
          </span>
          {count > 1 && (
            <span className="text-muted-foreground font-semibold">
              {count} connections
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5 text-[11px] font-mono">
          <span className="truncate font-semibold text-foreground" title={sourceName}>
            {sourceName}
          </span>
          <span className="text-muted-foreground shrink-0">&rarr;</span>
          <span className="truncate font-semibold text-foreground" title={targetName}>
            {targetName}
          </span>
        </div>

        <div className="space-y-0.5 border-t border-border/40 pt-1 text-[9px] text-muted-foreground">
          <div>
            <span className="font-semibold text-foreground/80">Caller:</span>{' '}
            <span className="font-mono">{sourceName}</span>
          </div>
          <div>
            <span className="font-semibold text-foreground/80">Callee:</span>{' '}
            <span className="font-mono">{targetName}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function BaseEdgeInner({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  style,
}: EdgeProps) {
  const edgeData = (data || {}) as CustomEdgeData;
  const edgeType = edgeData.edgeType || 'imports';
  const isThrottled = Boolean(edgeData.isThrottled);
  const isAggregated = Boolean(edgeData.isAggregated);
  const isDimmed = Boolean(edgeData.isDimmed);
  const isHighlighted = Boolean(edgeData.isHighlighted);
  const count = typeof edgeData.count === 'number' ? edgeData.count : 1;
  const edgeStyle = getEdgeStyle(edgeType);

  const sourceName = edgeData.sourceName || 'Source';
  const targetName = edgeData.targetName || 'Target';

  // Opacity & styling based on dimming / highlighting
  const opacity = isDimmed ? 0.15 : isHighlighted ? 1.0 : 0.75;
  const strokeWidth = isHighlighted
    ? edgeStyle.width + 1.5
    : isAggregated
      ? Math.min(edgeStyle.width + 1.2, 4)
      : edgeStyle.width;

  // When throttled at zoom < 0.3, render a fast straight line without bezier calculations or label DOM
  if (isThrottled) {
    return (
      <line
        id={id}
        x1={sourceX}
        y1={sourceY}
        x2={targetX}
        y2={targetY}
        stroke={edgeStyle.color}
        strokeWidth={strokeWidth}
        opacity={opacity}
        style={style}
        data-testid={`edge-throttled-${id}`}
      />
    );
  }

  // Choose between smooth step and bezier path based on edge specification
  const pathParams = {
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  };

  const [path, labelX, labelY] =
    edgeStyle.pathType === 'smoothstep'
      ? getSmoothStepPath({ ...pathParams, borderRadius: 8 })
      : getBezierPath({ ...pathParams, curvature: edgeType === 'renders' ? 0.35 : 0.25 });

  const markerId = `arrow-${edgeType}-${id}`;
  const showParticles = edgeStyle.hasParticles || isHighlighted;

  return (
    <>
      <svg className="overflow-visible pointer-events-none" style={{ position: 'absolute' }}>
        <defs>
          <marker
            id={markerId}
            viewBox="0 0 10 10"
            refX="8"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path
              d="M 0 1.5 L 10 5 L 0 8.5 z"
              fill={edgeStyle.color}
              opacity={opacity}
            />
          </marker>
        </defs>
      </svg>

      {/* Main Edge Path */}
      <path
        id={id}
        d={path}
        stroke={edgeStyle.color}
        strokeWidth={strokeWidth}
        strokeDasharray={edgeStyle.dash !== 'none' ? edgeStyle.dash : undefined}
        markerEnd={`url(#${markerId})`}
        opacity={opacity}
        className={`transition-all duration-150 ${
          isHighlighted ? 'filter drop-shadow-[0_0_5px_currentColor]' : ''
        }`}
        style={style}
        data-testid={`edge-path-${id}`}
      />

      {/* Subtle particle animation along active data flow */}
      {showParticles && !isDimmed && (
        <circle
          r={isAggregated ? 3 : 2}
          fill={edgeStyle.color}
          opacity={0.85}
          className="filter drop-shadow-[0_0_4px_currentColor] pointer-events-none"
          dangerouslySetInnerHTML={{
            __html: `<animateMotion dur="${isAggregated ? '1.8s' : '2.5s'}" repeatCount="indefinite" path="${path}" />`,
          }}
        />
      )}

      {/* Interactive Tooltip & Context Label */}
      {typeof document === 'undefined' ? (
        <EdgeTooltip
          id={id}
          edgeType={edgeType}
          count={count}
          isHighlighted={isHighlighted}
          isDimmed={isDimmed}
          sourceName={sourceName}
          targetName={targetName}
          edgeColor={edgeStyle.color}
          labelX={labelX}
          labelY={labelY}
        />
      ) : (
        <EdgeLabelRenderer>
          <EdgeTooltip
            id={id}
            edgeType={edgeType}
            count={count}
            isHighlighted={isHighlighted}
            isDimmed={isDimmed}
            sourceName={sourceName}
            targetName={targetName}
            edgeColor={edgeStyle.color}
            labelX={labelX}
            labelY={labelY}
          />
        </EdgeLabelRenderer>
      )}
    </>
  );
}

export const BaseEdge = memo(BaseEdgeInner);
export const FlowEdge = BaseEdge;
