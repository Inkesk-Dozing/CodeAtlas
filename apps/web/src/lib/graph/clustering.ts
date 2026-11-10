import type { GraphEdge, GraphNode } from '@/stores/graphStore';
import type { Edge, Node } from '@xyflow/react';
import { MarkerType } from '@xyflow/react';
import { layoutWithDagre, type LayoutOrientation } from './dagreLayout';

export interface ClusterInfo {
  id: string; // cluster prefix path, e.g., "apps/api"
  directory: string;
  depth: number;
  childNodeIds: Set<string>;
  childClusterIds: Set<string>;
  parentClusterId: string | null;
  fileCount: number;
}

export function getNodeRendererType(nodeType: string): string {
  switch (nodeType) {
    case 'file':
      return 'file';
    case 'function':
    case 'method':
      return 'function';
    case 'class':
    case 'model':
    case 'service':
    case 'controller':
      return 'class';
    case 'route':
      return 'route';
    case 'component':
      return 'component';
    default:
      return 'base';
  }
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
  orientation: LayoutOrientation = 'LR',
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
      }
    }
  }

  // Prepare items and edges for Dagre hierarchical layout
  const dagreItems: Array<{ id: string; width: number; height: number }> = [];

  for (const n of activeNodes) {
    dagreItems.push({ id: n.id, width: 260, height: 80 });
  }

  for (const [clusterId] of clusters) {
    if (collapsedClusters.has(clusterId)) {
      const parent = findCollapsedAncestor(clusterId + '/sub', collapsedClusters, maxDepth);
      if (parent === clusterId) {
        dagreItems.push({ id: `cluster:${clusterId}`, width: 280, height: 90 });
      }
    }
  }

  const dagreEdges = Array.from(effectiveEdgesMap.values()).map((eff) => ({
    source: eff.source,
    target: eff.target,
  }));

  const dagreResult = layoutWithDagre(dagreItems, dagreEdges, {
    orientation,
    nodeWidth: 260,
    nodeHeight: 80,
    nodeSep: 50,
    rankSep: 90,
  });

  const posMap = dagreResult.positions;

  // Construct React Flow Nodes
  const nodes: Node[] = [];

  // Active individual nodes
  for (const n of activeNodes) {
    const pos = posMap.get(n.id) || { x: 0, y: 0 };
    nodes.push({
      id: n.id,
      type: getNodeRendererType(n.type),
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

