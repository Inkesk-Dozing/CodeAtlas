import { describe, it, expect } from 'vitest';
import {
  computeBFSNodeRanks,
  detectRootEntrypoints,
  isRootEntrypoint,
  layoutWithDagre,
  type DagreEdgeItem,
  type DagreNodeItem,
} from './dagreLayout';
import type { GraphEdge, GraphNode } from '@/stores/graphStore';

describe('dagreLayout engine', () => {
  const sampleNodes: GraphNode[] = [
    {
      id: 'node-root-1',
      name: 'main.py',
      path: 'apps/api/main.py',
      type: 'file',
      language: 'python',
      metadata: { is_entrypoint: true },
      summary: null,
    },
    {
      id: 'node-root-2',
      name: 'page.tsx',
      path: 'apps/web/src/app/page.tsx',
      type: 'file',
      language: 'typescript',
      metadata: {},
      summary: null,
    },
    {
      id: 'node-route',
      name: 'ingestionRouter',
      path: 'apps/api/routers/ingestion.py',
      type: 'route',
      language: 'python',
      metadata: { http_method: 'POST', route_path: '/ingest' },
      summary: null,
    },
    {
      id: 'node-service',
      name: 'IngestionService',
      path: 'apps/api/services/ingestion.py',
      type: 'service',
      language: 'python',
      metadata: {},
      summary: null,
    },
    {
      id: 'node-model',
      name: 'RepoRecord',
      path: 'apps/api/models/repo.py',
      type: 'model',
      language: 'python',
      metadata: {},
      summary: null,
    },
  ];

  const sampleEdges: GraphEdge[] = [
    {
      id: 'e1',
      source_id: 'node-root-1',
      target_id: 'node-route',
      type: 'defines',
      weight: 1,
    },
    {
      id: 'e2',
      source_id: 'node-route',
      target_id: 'node-service',
      type: 'calls',
      weight: 1,
    },
    {
      id: 'e3',
      source_id: 'node-service',
      target_id: 'node-model',
      type: 'imports',
      weight: 1,
    },
  ];

  describe('Root Entrypoint Detection', () => {
    it('detects entrypoints via path patterns and metadata', () => {
      const inDegrees = new Map<string, number>([
        ['node-root-1', 0],
        ['node-root-2', 0],
        ['node-route', 1],
        ['node-service', 1],
        ['node-model', 1],
      ]);

      expect(isRootEntrypoint(sampleNodes[0], inDegrees)).toBe(true);
      expect(isRootEntrypoint(sampleNodes[1], inDegrees)).toBe(true);
      expect(isRootEntrypoint(sampleNodes[3], inDegrees)).toBe(false);
    });

    it('identifies roots correctly across the graph', () => {
      const roots = detectRootEntrypoints(sampleNodes, sampleEdges);
      expect(roots).toContain('node-root-1');
      expect(roots).toContain('node-root-2');
      expect(roots).not.toContain('node-route');
    });
  });

  describe('BFS Depth Calculation Engine', () => {
    it('computes correct topological BFS ranks from roots down to models', () => {
      const ranks = computeBFSNodeRanks(sampleNodes, sampleEdges, ['node-root-1']);

      expect(ranks.get('node-root-1')).toBe(0);
      expect(ranks.get('node-route')).toBe(1);
      expect(ranks.get('node-service')).toBe(2);
      expect(ranks.get('node-model')).toBe(3);
    });

    it('assigns architectural layer fallback to disconnected nodes', () => {
      const disconnectedNodes: GraphNode[] = [
        ...sampleNodes,
        {
          id: 'node-util',
          name: 'logger',
          path: 'packages/utils/logger.ts',
          type: 'utility',
          language: 'typescript',
          metadata: {},
          summary: null,
        },
      ];

      const ranks = computeBFSNodeRanks(disconnectedNodes, sampleEdges, ['node-root-1']);
      expect(ranks.get('node-util')).toBe(5);
    });
  });

  describe('Dagre Hierarchical Layout Positioning & Orientations', () => {
    const items: DagreNodeItem[] = [
      { id: 'a', width: 200, height: 80 },
      { id: 'b', width: 200, height: 80 },
      { id: 'c', width: 200, height: 80 },
    ];
    const edges: DagreEdgeItem[] = [
      { source: 'a', target: 'b' },
      { source: 'b', target: 'c' },
    ];

    it('positions nodes in Left-to-Right (LR) orientation', () => {
      const result = layoutWithDagre(items, edges, { orientation: 'LR' });
      const posA = result.positions.get('a')!;
      const posB = result.positions.get('b')!;
      const posC = result.positions.get('c')!;

      expect(posA).toBeDefined();
      expect(posB).toBeDefined();
      expect(posC).toBeDefined();

      // In LR layout, x-coordinates must strictly increase for child nodes
      expect(posB.x).toBeGreaterThan(posA.x);
      expect(posC.x).toBeGreaterThan(posB.x);
    });

    it('positions nodes in Top-to-Bottom (TB) orientation', () => {
      const result = layoutWithDagre(items, edges, { orientation: 'TB' });
      const posA = result.positions.get('a')!;
      const posB = result.positions.get('b')!;
      const posC = result.positions.get('c')!;

      // In TB layout, y-coordinates must strictly increase for child nodes
      expect(posB.y).toBeGreaterThan(posA.y);
      expect(posC.y).toBeGreaterThan(posB.y);
    });

    it('prevents node overlaps with configurable separation margins', () => {
      // 5 siblings sharing 1 parent
      const siblingItems: DagreNodeItem[] = [
        { id: 'parent', width: 260, height: 80 },
        { id: 'child-1', width: 260, height: 80 },
        { id: 'child-2', width: 260, height: 80 },
        { id: 'child-3', width: 260, height: 80 },
      ];
      const siblingEdges: DagreEdgeItem[] = [
        { source: 'parent', target: 'child-1' },
        { source: 'parent', target: 'child-2' },
        { source: 'parent', target: 'child-3' },
      ];

      const result = layoutWithDagre(siblingItems, siblingEdges, {
        orientation: 'LR',
        nodeSep: 60,
        rankSep: 100,
      });

      // Verify no bounding box overlaps between any pair of nodes
      const allNodes = siblingItems.map((item) => {
        const pos = result.positions.get(item.id)!;
        return {
          id: item.id,
          left: pos.x,
          right: pos.x + (item.width || 260),
          top: pos.y,
          bottom: pos.y + (item.height || 80),
        };
      });

      for (let i = 0; i < allNodes.length; i++) {
        for (let j = i + 1; j < allNodes.length; j++) {
          const n1 = allNodes[i];
          const n2 = allNodes[j];

          const hasOverlap =
            n1.left < n2.right &&
            n1.right > n2.left &&
            n1.top < n2.bottom &&
            n1.bottom > n2.top;

          expect(hasOverlap).toBe(false);
        }
      }
    });

    it('computes layout for 1,000 nodes in under 400ms (Acceptance Criteria)', () => {
      // Generate synthetic monorepo execution pipelines with 1,000 nodes (100 pipelines of 10 nodes each)
      const largeItems: DagreNodeItem[] = [];
      const largeEdges: DagreEdgeItem[] = [];

      for (let i = 0; i < 1000; i++) {
        largeItems.push({
          id: `node-${i}`,
          width: 240,
          height: 70,
        });
      }

      for (let p = 0; p < 100; p++) {
        const base = p * 10;
        for (let step = 0; step < 9; step++) {
          largeEdges.push({
            source: `node-${base + step}`,
            target: `node-${base + step + 1}`,
          });
        }
      }

      const result = layoutWithDagre(largeItems, largeEdges, {
        orientation: 'LR',
        nodeSep: 40,
        rankSep: 80,
      });

      expect(result.positions.size).toBe(1000);
      // Acceptance criteria: under 400ms
      expect(result.durationMs).toBeLessThan(400);
    });
  });
});
