'use client';

import { memo } from 'react';
import type { EdgeProps } from '@xyflow/react';
import { BaseEdge } from './BaseEdge';

function BezierEdgeInner(props: EdgeProps) {
  return <BaseEdge {...props} />;
}

export const BezierEdge = memo(BezierEdgeInner);
