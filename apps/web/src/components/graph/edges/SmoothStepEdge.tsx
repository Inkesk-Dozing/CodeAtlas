'use client';

import { memo } from 'react';
import type { EdgeProps } from '@xyflow/react';
import { BaseEdge } from './BaseEdge';

function SmoothStepEdgeInner(props: EdgeProps) {
  return <BaseEdge {...props} />;
}

export const SmoothStepEdge = memo(SmoothStepEdgeInner);
