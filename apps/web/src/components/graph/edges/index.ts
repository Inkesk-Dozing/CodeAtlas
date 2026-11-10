export * from './types';
export * from './BaseEdge';
export * from './BezierEdge';
export * from './SmoothStepEdge';

import { BaseEdge, FlowEdge } from './BaseEdge';
import { BezierEdge } from './BezierEdge';
import { SmoothStepEdge } from './SmoothStepEdge';

export const customEdgeTypes = {
  base: FlowEdge,
  bezier: BezierEdge,
  smoothstep: SmoothStepEdge,
  flow: FlowEdge,
  typed: BaseEdge,
};
