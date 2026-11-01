import type { GraphEdge, GraphNode } from '@/stores/graphStore';
import type { Edge, Node } from '@xyflow/react';
import { MarkerType } from '@xyflow/react';

export interface ClusterInfo {
  id: string; // cluster prefix path, e.g., "apps/api"
  directory: string;
  depth: number;
  childNodeIds: Set<string>;
  childClusterIds: Set<string>;
  parentClusterId: string | null;
  fileCount: number;
}

/**
 * Extracts a directory prefix up to maxDepth levels deep from a file path.
 * Examples for maxDepth=4:
 * "apps/api/routers/ingestion.py" -> "apps/api/routers"
 * "packages/shared/src/index.ts" -> "packages/shared/src"
 * "main.py" -> null (root-level, no directory prefix)
 */
export function getDirectoryPrefix(filePath: string, maxDepth = 4): string | null {
  if (!filePath) return null;
  // Normalize windows/posix slashes
  const normalized = filePath.replace(/\\/g, '/').replace(/^\/+/, '');
  const parts = normalized.split('/');
  if (parts.length <= 1) {
    return null; // Root file
  }
  // Remove file name part
  const dirParts = parts.slice(0, -1);
  const cappedParts = dirParts.slice(0, maxDepth);
  return cappedParts.join('/');
}

/**
 * Analyzes nodes and builds directory cluster hierarchy up to maxDepth levels.
 */
export function buildClusterHierarchy(
  nodes: GraphNode[],
  maxDepth = 4,
): Map<string, ClusterInfo> {
  const clusters = new Map<string, ClusterInfo>();

  for (const n of nodes) {
    const dir = getDirectoryPrefix(n.path, maxDepth);
    if (!dir) continue;

    // Create cluster chain for nested directories up to maxDepth
    const segments = dir.split('/');
    let currentPath = '';
    let parentPath: string | null = null;

    for (let depth = 1; depth <= segments.length; depth++) {
      currentPath = segments.slice(0, depth).join('/');

      if (!clusters.has(currentPath)) {
        clusters.set(currentPath, {
          id: currentPath,
          directory: currentPath,
          depth,
          childNodeIds: new Set(),
          childClusterIds: new Set(),
          parentClusterId: parentPath,
          fileCount: 0,
        });
      }

      const cluster = clusters.get(currentPath)!;
      cluster.fileCount += 1;
      cluster.childNodeIds.add(n.id);

      if (parentPath && clusters.has(parentPath)) {
        clusters.get(parentPath)!.childClusterIds.add(currentPath);
      }

      parentPath = currentPath;
    }
  }

  return clusters;
}

/**
 * Finds the topmost collapsed ancestor for a given node path, if any.
 */
export function findCollapsedAncestor(
  nodePath: string,
  collapsedClusters: Set<string>,
  maxDepth = 4,
): string | null {
  const dir = getDirectoryPrefix(nodePath, maxDepth);
  if (!dir) return null;

  const segments = dir.split('/');
  for (let depth = 1; depth <= segments.length; depth++) {
    const prefix = segments.slice(0, depth).join('/');
    if (collapsedClusters.has(prefix)) {
      return prefix;
    }
  }
  return null;
}

export interface ClusteredGraphResult {
  nodes: Node[];
  edges: Edge[];
}

/**
 * Layouts nodes and clusters:
 * - When a cluster is collapsed:
 *   - Its child nodes are hidden.
 *   - A cluster container node is rendered representing the collapsed directory with file count.
 *   - Internal edges are removed.
 *   - External edges that pointed to internal nodes are dynamically consolidated to route to/from the cluster node.
 * - When expanded:
 *   - Nodes are rendered at their computed positions.
 *   - A cluster container/group node can frame them or nodes flow within their layout.
 */
export function layoutClusteredGraph(
  rawNodes: GraphNode[],
  rawEdges: GraphEdge[],
  collapsedClusters: Set<string>,
  maxDepth = 4,
): ClusteredGraphResult {
  const clusters = buildClusterHierarchy(rawNodes, maxDepth);

  // Group raw nodes by whether they fall inside a collapsed cluster
  const activeNodes: GraphNode[] = [];
  const nodeToCollapsedCluster = new Map<string, string>();

  // Determine which raw nodes are directly visible vs hidden inside a collapsed cluster
  for (const n of rawNodes) {
    const collapsedPrefix = findCollapsedAncestor(n.path, collapsedClusters, maxDepth);
    if (collapsedPrefix) {
      nodeToCollapsedCluster.set(n.id, collapsedPrefix);
    } else {
      activeNodes.push(n);
    }
  }

  // Assign layers via BFS across active nodes and collapsed clusters
  const posMap = new Map<string, { x: number; y: number }>();
  const adj = new Map<string, string[]>();
  const inDeg = new Map<string, number>();

  const allItemIds = new Set<string>();
  for (const n of activeNodes) {
    allItemIds.add(n.id);
  }
  for (const [clusterId] of clusters) {
    if (collapsedClusters.has(clusterId)) {
      // Only include top-level collapsed cluster
      const parent = findCollapsedAncestor(clusterId + '/sub', collapsedClusters, maxDepth);
      if (parent === clusterId) {
        allItemIds.add(`cluster:${clusterId}`);
      }
    }
  }

  for (const id of allItemIds) {
    inDeg.set(id, 0);
    adj.set(id, []);
  }

  // Map edges to their effective endpoints (routing to collapsed clusters if target/source is inside)
  const effectiveEdgesMap = new Map<string, { source: string; target: string; type: string; count: number }>();

  for (const e of rawEdges) {
    const effSource = nodeToCollapsedCluster.has(e.source_id)
      ? `cluster:${nodeToCollapsedCluster.get(e.source_id)!}`
      : e.source_id;
    const effTarget = nodeToCollapsedCluster.has(e.target_id)
      ? `cluster:${nodeToCollapsedCluster.get(e.target_id)!}`
      : e.target_id;

    // Skip internal intra-cluster edges
    if (effSource === effTarget) {
      continue;
    }

    if (allItemIds.has(effSource) && allItemIds.has(effTarget)) {
      const key = `${effSource}->${effTarget}:${e.type}`;
      if (effectiveEdgesMap.has(key)) {
        effectiveEdgesMap.get(key)!.count += 1;
      } else {
        effectiveEdgesMap.set(key, {
          source: effSource,
          target: effTarget,
          type: e.type,
          count: 1,
        });
        adj.get(effSource)?.push(effTarget);
        inDeg.set(effTarget, (inDeg.get(effTarget) || 0) + 1);
      }
    }
  }

  // BFS layering
  const layer = new Map<string, number>();
  const queue: string[] = [];
  for (const [id, deg] of inDeg) {
    if (deg === 0) {
      layer.set(id, 0);
      queue.push(id);
    }
  }

  while (queue.length > 0) {
    const current = queue.shift()!;
    const currentLayer = layer.get(current) || 0;
    for (const neighbor of adj.get(current) || []) {
      if (!layer.has(neighbor)) {
        layer.set(neighbor, currentLayer + 1);
        queue.push(neighbor);
      }
    }
  }

  // Position assignment
  const layers = new Map<number, string[]>();
  for (const id of allItemIds) {
    const l = layer.get(id) ?? 0;
    if (!layers.has(l)) layers.set(l, []);
    layers.get(l)!.push(id);
  }

  for (const [l, ids] of layers) {
    ids.forEach((id, idx) => {
      posMap.set(id, { x: l * 340, y: idx * 130 - (ids.length * 65) });
    });
  }

  // Construct React Flow Nodes
  const nodes: Node[] = [];

  // Active individual nodes
  for (const n of activeNodes) {
    const pos = posMap.get(n.id) || { x: 0, y: 0 };
    nodes.push({
      id: n.id,
      type: 'base',
      position: pos,
      data: {
        node: n,
        isSelected: false,
        isHighlighted: false,
      },
    });
  }

  // Collapsed cluster container nodes
  for (const [clusterId, info] of clusters) {
    if (collapsedClusters.has(clusterId)) {
      const parent = findCollapsedAncestor(clusterId + '/sub', collapsedClusters, maxDepth);
      if (parent === clusterId) {
        const id = `cluster:${clusterId}`;
        const pos = posMap.get(id) || { x: 0, y: 0 };
        nodes.push({
          id,
          type: 'cluster',
          position: pos,
          data: {
            clusterId,
            directory: info.directory,
            depth: info.depth,
            fileCount: info.fileCount,
            isCollapsed: true,
          },
        });
      }
    }
  }

  // Construct consolidated React Flow Edges
  const edges: Edge[] = [];
  let edgeIndex = 0;
  for (const [, eff] of effectiveEdgesMap) {
    const isAggregated = eff.count > 1;
    edges.push({
      id: `edge-${edgeIndex++}`,
      source: eff.source,
      target: eff.target,
      type: 'base',
      data: {
        edgeType: eff.type,
        count: eff.count,
        isAggregated,
      },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#9CA3AF' },
    });
  }

  return { nodes, edges };
}

