export interface EdgeStyleConfig {
  color: string;
  dash: string;
  width: number;
  animated: boolean;
  hasParticles: boolean;
  pathType: 'bezier' | 'smoothstep';
}

export const EDGE_STYLES: Record<string, EdgeStyleConfig> = {
  imports: {
    color: '#64748B', // Subtle slate gray solid line
    dash: 'none',
    width: 1.5,
    animated: false,
    hasParticles: false,
    pathType: 'smoothstep',
  },
  calls: {
    color: '#0EA5E9', // Electric blue directional arrow with subtle particle animation
    dash: 'none',
    width: 2.0,
    animated: true,
    hasParticles: true,
    pathType: 'bezier',
  },
  extends: {
    color: '#10B981', // Emerald green dashed line
    dash: '6,4',
    width: 2.0,
    animated: false,
    hasParticles: false,
    pathType: 'smoothstep',
  },
  implements: {
    color: '#8B5CF6',
    dash: '6,4',
    width: 1.5,
    animated: false,
    hasParticles: false,
    pathType: 'smoothstep',
  },
  handles_route: {
    color: '#A855F7', // Purple thick edge linking route to handler
    dash: 'none',
    width: 3.0,
    animated: true,
    hasParticles: true,
    pathType: 'bezier',
  },
  routes_to: {
    color: '#A855F7', // Alias for handles_route
    dash: 'none',
    width: 3.0,
    animated: true,
    hasParticles: true,
    pathType: 'bezier',
  },
  renders: {
    color: '#F59E0B', // Amber curved edge linking parent to child component
    dash: '4,4',
    width: 2.0,
    animated: false,
    hasParticles: false,
    pathType: 'bezier',
  },
  uses_hook: {
    color: '#F97316',
    dash: '4,4',
    width: 1.5,
    animated: false,
    hasParticles: false,
    pathType: 'bezier',
  },
  contains: {
    color: '#6B7280',
    dash: '2,4',
    width: 1.0,
    animated: false,
    hasParticles: false,
    pathType: 'smoothstep',
  },
  middleware_for: {
    color: '#F59E0B',
    dash: 'none',
    width: 2.0,
    animated: false,
    hasParticles: false,
    pathType: 'bezier',
  },
  has_model: {
    color: '#EC4899',
    dash: 'none',
    width: 1.5,
    animated: false,
    hasParticles: false,
    pathType: 'smoothstep',
  },
  reads: {
    color: '#10B981',
    dash: '6,4',
    width: 1.0,
    animated: false,
    hasParticles: false,
    pathType: 'bezier',
  },
  writes: {
    color: '#EF4444',
    dash: '6,4',
    width: 1.0,
    animated: false,
    hasParticles: false,
    pathType: 'bezier',
  },
};

export function getEdgeStyle(edgeType?: string): EdgeStyleConfig {
  if (!edgeType) return EDGE_STYLES.imports;
  return EDGE_STYLES[edgeType] || EDGE_STYLES.imports;
}

export interface CustomEdgeData {
  edgeType?: string;
  isThrottled?: boolean;
  isAggregated?: boolean;
  isDimmed?: boolean;
  isHighlighted?: boolean;
  isMapped?: boolean;
  count?: number;
  sourceName?: string;
  targetName?: string;
  [key: string]: unknown;
}
