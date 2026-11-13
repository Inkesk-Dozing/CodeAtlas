import type { GraphNode } from '@/stores/graphStore';

export interface BaseNodeData {
  node: GraphNode;
  isSelected?: boolean;
  isHighlighted?: boolean;
  isMapped?: boolean;
  isVirtualProxy?: boolean;
  onSelect?: (nodeId: string) => void;
}
