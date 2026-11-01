import { describe, expect, it } from 'vitest';
import {
  buildClusterHierarchy,
  findCollapsedAncestor,
  getDirectoryPrefix,
  layoutClusteredGraph,
} from './clustering';

const sampleNode = (id: string, path: string) => ({
  id,
  type: 'file',
  name: id,
  path,
  language: 'typescript',
  metadata: {},
  summary: null,
});

const sampleEdge = (id: string, source_id: string, target_id: string, type = 'imports') => ({
  id,
  source_id,
  target_id,
  type,
  weight: 1,
});

describe('clustering utils', () => {
  it('extracts directory prefixes up to maxDepth levels', () => {
    expect(getDirectoryPrefix('apps/api/routers/ingestion.py', 4)).toBe('apps/api/routers');
    expect(getDirectoryPrefix('apps/api/routers/sub/deep/file.py', 4)).toBe('apps/api/routers/sub');
    expect(getDirectoryPrefix('packages/shared/src/index.ts', 2)).toBe('packages/shared');
    expect(getDirectoryPrefix('main.py')).toBe(null);
  });

  it('builds nested cluster hierarchy up to 4 levels deep', () => {
    const nodes = [
      sampleNode('n1', 'apps/api/routers/ingestion.py'),
      sampleNode('n2', 'apps/api/routers/auth.py'),
      sampleNode('n3', 'apps/web/src/components/GraphCanvas.tsx'),
      sampleNode('n4', 'packages/shared/index.ts'),
    ];

    const clusters = buildClusterHierarchy(nodes, 4);

    expect(clusters.has('apps')).toBe(true);
    expect(clusters.has('apps/api')).toBe(true);
    expect(clusters.has('apps/api/routers')).toBe(true);
    expect(clusters.get('apps/api/routers')?.depth).toBe(3);
    expect(clusters.get('apps/api/routers')?.fileCount).toBe(2);

    expect(clusters.has('apps/web')).toBe(true);
    expect(clusters.has('packages/shared')).toBe(true);
  });

  it('detects collapsed ancestor prefix correctly', () => {
    const collapsed = new Set(['apps/api']);

    expect(findCollapsedAncestor('apps/api/routers/ingestion.py', collapsed)).toBe('apps/api');
    expect(findCollapsedAncestor('apps/web/page.tsx', collapsed)).toBe(null);
  });

  it('consolidates external edges when cluster is collapsed', () => {
    const nodes = [
      sampleNode('api_1', 'apps/api/routers/ingestion.py'),
      sampleNode('api_2', 'apps/api/tasks/worker.py'),
      sampleNode('web_1', 'apps/web/page.tsx'),
    ];

    const edges = [
      // Internal edge
      sampleEdge('e1', 'api_1', 'api_2'),
      // External edges from web to both api endpoints
      sampleEdge('e2', 'web_1', 'api_1'),
      sampleEdge('e3', 'web_1', 'api_2'),
    ];

    const collapsed = new Set(['apps/api']);
    const result = layoutClusteredGraph(nodes, edges, collapsed);

    // Node count: web_1 and cluster:apps/api
    expect(result.nodes.map((n) => n.id)).toEqual(
      expect.arrayContaining(['web_1', 'cluster:apps/api'])
    );
    expect(result.nodes.find((n) => n.id === 'api_1')).toBeUndefined();
    expect(result.nodes.find((n) => n.id === 'api_2')).toBeUndefined();

    // Internal edge e1 should be removed
    // e2 and e3 should be consolidated into one aggregated edge
    expect(result.edges).toHaveLength(1);
    expect(result.edges[0].source).toBe('web_1');
    expect(result.edges[0].target).toBe('cluster:apps/api');
    expect(result.edges[0].data?.count).toBe(2);
    expect(result.edges[0].data?.isAggregated).toBe(true);
  });
});

