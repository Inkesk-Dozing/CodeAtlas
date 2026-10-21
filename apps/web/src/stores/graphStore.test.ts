import { beforeEach, describe, expect, it } from 'vitest';
import { getVisibleEdges, getVisibleNodes, useGraphStore } from './graphStore';

const node = (id: string, type = 'file', name = id, path = `src/${id}.ts`) => ({
  id,
  type,
  name,
  path,
  language: 'typescript',
  metadata: {},
  summary: null,
});

const edge = (id: string, source_id: string, target_id: string) => ({
  id,
  source_id,
  target_id,
  type: 'imports',
  weight: 1,
});

const baseFilters = (nodes: ReturnType<typeof node>[]) => ({
  rawNodes: nodes,
  filterTypes: new Set<string>(),
  searchQuery: '',
});

describe('graphStore', () => {
  beforeEach(() => {
    useGraphStore.setState({
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
    });
  });

  it('setGraph populates nodes, edges and totals', () => {
    const nodes = [node('a'), node('b')];
    const edges = [edge('e1', 'a', 'b')];
    useGraphStore.getState().setGraph(nodes, edges, 42);

    const s = useGraphStore.getState();
    expect(s.rawNodes).toHaveLength(2);
    expect(s.rawEdges).toHaveLength(1);
    expect(s.nodes.get('a')?.id).toBe('a');
    expect(s.totalNodes).toBe(42);
  });

  it('selectNode updates selection', () => {
    useGraphStore.getState().selectNode('a');
    expect(useGraphStore.getState().selectedNodeId).toBe('a');
    useGraphStore.getState().selectNode(null);
    expect(useGraphStore.getState().selectedNodeId).toBeNull();
  });

  it('addHighlight merges unique ids', () => {
    useGraphStore.getState().addHighlight(['a', 'b']);
    useGraphStore.getState().addHighlight(['b', 'c']);
    const ids = useGraphStore.getState().highlightedNodeIds;
    expect([...ids].sort()).toEqual(['a', 'b', 'c']);
  });

  it('toggleFilterType adds and removes types', () => {
    useGraphStore.getState().toggleFilterType('route');
    expect(useGraphStore.getState().filterTypes.has('route')).toBe(true);
    useGraphStore.getState().toggleFilterType('route');
    expect(useGraphStore.getState().filterTypes.has('route')).toBe(false);
  });

  it('clearFilters resets filters and query', () => {
    useGraphStore.getState().toggleFilterType('route');
    useGraphStore.getState().setSearchQuery('login');
    useGraphStore.getState().clearFilters();
    const s = useGraphStore.getState();
    expect(s.filterTypes.size).toBe(0);
    expect(s.searchQuery).toBe('');
  });
});

describe('getVisibleNodes', () => {
  it('returns all nodes when no filters', () => {
    const nodes = [node('a'), node('b')];
    expect(getVisibleNodes(baseFilters(nodes))).toHaveLength(2);
  });

  it('filters by type', () => {
    const nodes = [node('a', 'file'), node('b', 'route')];
    const result = getVisibleNodes({
      rawNodes: nodes,
      filterTypes: new Set(['route']),
      searchQuery: '',
    });
    expect(result.map((n) => n.id)).toEqual(['b']);
  });

  it('filters by search query across name, path and type', () => {
    const nodes = [node('loginPage', 'component', 'LoginPage'), node('api', 'file')];
    const byName = getVisibleNodes({ ...baseFilters(nodes), searchQuery: 'login' });
    expect(byName.map((n) => n.id)).toEqual(['loginPage']);

    const byPath = getVisibleNodes({ ...baseFilters(nodes), searchQuery: 'src/api' });
    expect(byPath.map((n) => n.id)).toEqual(['api']);
  });

  it('is case-insensitive', () => {
    const nodes = [node('LoginPage', 'component')];
    const result = getVisibleNodes({ ...baseFilters(nodes), searchQuery: 'LOGIN' });
    expect(result).toHaveLength(1);
  });
});

describe('getVisibleEdges', () => {
  it('keeps only edges between visible nodes', () => {
    const nodes = [node('a'), node('b'), node('c')];
    const edges = [edge('e1', 'a', 'b'), edge('e2', 'a', 'c')];
    const visible = getVisibleNodes({
      ...baseFilters(nodes),
      filterTypes: new Set(['file']),
      searchQuery: '',
    });
    const result = getVisibleEdges({ rawEdges: edges, visibleNodes: visible });
    expect(result).toHaveLength(2);

    const filtered = getVisibleEdges({
      rawEdges: edges,
      visibleNodes: visible.filter((n) => n.id === 'a'),
    });
    expect(filtered).toHaveLength(0);
  });
});
