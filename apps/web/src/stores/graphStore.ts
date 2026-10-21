import { create } from 'zustand';

/**
 * Per-node metadata as produced by the ingestion extractors
 * (see apps/api `services/ingestion/extractor.py` and `parsers/*`).
 * Known keys are typed; unknown extras fall through the index signature.
 */
export interface NodeMetadata {
  loc?: number;
  size?: number;
  line?: number;
  signature?: string;
  docstring?: string | null;
  is_async?: boolean;
  is_exported?: boolean;
  is_service?: boolean;
  bases?: string[];
  decorators?: string[];
  methods?: (string | { name: string; type?: string })[];
  fields?: (string | { name: string; type?: string })[];
  hooks_used?: string[];
  http_method?: string;
  route_path?: string;
  controller?: string;
  framework?: string;
  middleware?: string | null;
  exports?: string[];
  imports?: string[];
  complexity?: { cyclomatic?: number; cognitive?: number; maintainability?: number };
  [key: string]: unknown;
}

export interface GraphNode {
  id: string;
  type: string;
  name: string;
  path: string;
  language: string | null;
  metadata: NodeMetadata;
  summary: string | null;
  x?: number;
  y?: number;
}

export interface GraphEdge {
  id: string;
  source_id: string;
  target_id: string;
  type: string;
  weight: number;
}

interface GraphState {
  nodes: Map<string, GraphNode>;
  edges: Map<string, GraphEdge>;
  rawNodes: GraphNode[];
  rawEdges: GraphEdge[];
  selectedNodeId: string | null;
  highlightedNodeIds: Set<string>;
  searchQuery: string;
  filterTypes: Set<string>;
  isLoading: boolean;
  progress: number;
  stage: string | null;
  totalNodes: number;

  setGraph: (nodes: GraphNode[], edges: GraphEdge[], total?: number) => void;
  selectNode: (id: string | null) => void;
  addHighlight: (ids: string[]) => void;
  clearHighlight: () => void;
  setSearchQuery: (q: string) => void;
  toggleFilterType: (type: string) => void;
  clearFilters: () => void;
  setLoading: (loading: boolean) => void;
  setProgress: (progress: number, stage?: string) => void;
}

export const useGraphStore = create<GraphState>((set, get) => ({
  nodes: new Map(),
  edges: new Map(),
  rawNodes: [],
  rawEdges: [],
  selectedNodeId: null,
  highlightedNodeIds: new Set(),
  searchQuery: '',
  filterTypes: new Set(),
  isLoading: false,
  progress: 0,
  stage: null,
  totalNodes: 0,

  setGraph: (nodes, edges, total = 0) => {
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    const edgeMap = new Map(edges.map((e) => [e.id, e]));
    set({
      nodes: nodeMap,
      edges: edgeMap,
      rawNodes: nodes,
      rawEdges: edges,
      totalNodes: total,
    });
  },

  selectNode: (id) => set({ selectedNodeId: id }),

  addHighlight: (ids) =>
    set((state) => ({
      highlightedNodeIds: new Set([...state.highlightedNodeIds, ...ids]),
    })),

  clearHighlight: () => set({ highlightedNodeIds: new Set() }),

  setSearchQuery: (q) => set({ searchQuery: q }),

  toggleFilterType: (type) =>
    set((state) => {
      const next = new Set(state.filterTypes);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return { filterTypes: next };
    }),

  clearFilters: () => set({ filterTypes: new Set(), searchQuery: '' }),

  setLoading: (isLoading) => set({ isLoading }),

  setProgress: (progress, stage) => set({ progress, stage: stage ?? get().stage }),
}));

export interface GraphFilters {
  rawNodes: GraphNode[];
  filterTypes: Set<string>;
  searchQuery: string;
}

export const getVisibleNodes = (state: GraphFilters): GraphNode[] => {
  let nodes = state.rawNodes;

  if (state.filterTypes.size > 0) {
    nodes = nodes.filter((n) => state.filterTypes.has(n.type));
  }

  if (state.searchQuery) {
    const q = state.searchQuery.toLowerCase();
    nodes = nodes.filter(
      (n) =>
        n.name.toLowerCase().includes(q) ||
        n.path.toLowerCase().includes(q) ||
        n.type.toLowerCase().includes(q),
    );
  }

  return nodes;
};

export const getVisibleEdges = (state: {
  rawEdges: GraphEdge[];
  visibleNodes: GraphNode[];
}): GraphEdge[] => {
  const visibleIds = new Set(state.visibleNodes.map((n) => n.id));
  return state.rawEdges.filter((e) => visibleIds.has(e.source_id) && visibleIds.has(e.target_id));
};
