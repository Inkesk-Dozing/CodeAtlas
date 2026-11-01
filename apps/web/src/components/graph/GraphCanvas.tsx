'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  useOnViewportChange,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
  type Viewport,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { BaseNode } from './nodes/BaseNode';
import { ClusterNode } from './nodes/ClusterNode';
import { FlowEdge } from './edges/BaseEdge';
import { useGraphStore, getVisibleNodes } from '@/stores/graphStore';
import type { GraphEdge, GraphNode } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';
import { NODE_TYPE_COLORS } from '@codeatlas/shared';
import { calculateVisibleNodeIds, shouldThrottleEdges } from '@/lib/graph/virtualization';
import { layoutClusteredGraph } from '@/lib/graph/clustering';

const nodeTypes = {
  base: BaseNode,
  cluster: ClusterNode,
};
const edgeTypes = { base: FlowEdge };

interface ViewportInterceptorProps {
  onViewportChange: (viewport: Viewport) => void;
}

function ViewportInterceptor({ onViewportChange }: ViewportInterceptorProps) {
  useOnViewportChange({
    onChange: onViewportChange,
  });
  return null;
}

function layoutNodes(
  rawNodes: GraphNode[],
  rawEdges: GraphEdge[],
  collapsedClusters: Set<string>,
): { nodes: Node[]; edges: Edge[] } {
  return layoutClusteredGraph(rawNodes, rawEdges, collapsedClusters, 4);
}

interface GraphCanvasProps {
  onNodeClick?: (nodeId: string) => void;
}

export function GraphCanvas({ onNodeClick }: GraphCanvasProps) {
  const rawNodes = useGraphStore((s) => s.rawNodes);
  const rawEdges = useGraphStore((s) => s.rawEdges);
  const filterTypes = useGraphStore((s) => s.filterTypes);
  const searchQuery = useGraphStore((s) => s.searchQuery);
  const isLoading = useGraphStore((s) => s.isLoading);
  const stage = useGraphStore((s) => s.stage);
  const progress = useGraphStore((s) => s.progress);

  const [collapsedClusters, setCollapsedClusters] = useState<Set<string>>(new Set());

  const toggleCluster = useCallback((clusterId: string) => {
    setCollapsedClusters((prev) => {
      const next = new Set(prev);
      if (next.has(clusterId)) {
        next.delete(clusterId);
      } else {
        next.add(clusterId);
      }
      return next;
    });
  }, []);

  const visibleNodes = useMemo(
    () => getVisibleNodes({ rawNodes, filterTypes, searchQuery }),
    [rawNodes, filterTypes, searchQuery],
  );

  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(
    () => layoutNodes(visibleNodes, rawEdges, collapsedClusters),
    [visibleNodes, rawEdges, collapsedClusters],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges);

  useEffect(() => {
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [layoutedNodes, layoutedEdges, setNodes, setEdges]);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const nodeId = node.id;
      useGraphStore.getState().selectNode(nodeId);
      useUIStore.getState().openPanel('node-detail');
      onNodeClick?.(nodeId);
    },
    [onNodeClick],
  );

  const handlePaneClick = useCallback(() => {
    useGraphStore.getState().selectNode(null);
    useUIStore.getState().closePanel();
  }, []);

  const handleNodesChange = useCallback(
    (changes: NodeChange[]) => {
      onNodesChange(changes);
    },
    [onNodesChange],
  );

  const handleEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      onEdgesChange(changes);
    },
    [onEdgesChange],
  );

  const selectedId = useGraphStore((s) => s.selectedNodeId);
  const highlighted = useGraphStore((s) => s.highlightedNodeIds);

  const containerRef = useRef<HTMLDivElement>(null);
  const [containerDimensions, setContainerDimensions] = useState({ width: 0, height: 0 });
  const [viewport, setViewport] = useState<Viewport>({ x: 0, y: 0, zoom: 1 });

  // Measure container dimensions for visible viewport bounds
  useEffect(() => {
    if (!containerRef.current) return;

    const updateDimensions = () => {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current;
        setContainerDimensions({ width: clientWidth, height: clientHeight });
      }
    };

    updateDimensions();

    const resizeObserver = new ResizeObserver(() => {
      updateDimensions();
    });

    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  const handleViewportChange = useCallback((vp: Viewport) => {
    setViewport(vp);
  }, []);

  // Compute visible node set based on intercepted viewport bounds
  const activeVisibleNodeIds = useMemo(() => {
    if (nodes.length <= 100) {
      return null; // For small graphs, no virtualization needed
    }

    return calculateVisibleNodeIds(
      nodes.map((n) => ({
        id: n.id,
        position: n.position,
        width: 240,
        height: 72,
      })),
      viewport,
      containerDimensions,
      {
        bufferPx: 250,
        maxActiveNodes: 300,
        defaultWidth: 240,
        defaultHeight: 72,
      },
    );
  }, [nodes, viewport, containerDimensions]);

  const isEdgeThrottled = useMemo(() => shouldThrottleEdges(viewport.zoom, 0.3), [viewport.zoom]);

  const displayNodes = useMemo(
    () =>
      nodes.map((n) => {
        if (n.type === 'cluster') {
          return {
            ...n,
            data: {
              ...n.data,
              onToggleCollapse: toggleCluster,
            },
          };
        }

        const isSelected = n.id === selectedId;
        const isHighlighted = highlighted.has(n.id);
        // Off-screen node unmounting: if virtualization active and node not in viewport/selected/highlighted
        const isVirtualProxy =
          activeVisibleNodeIds !== null &&
          !activeVisibleNodeIds.has(n.id) &&
          !isSelected &&
          !isHighlighted;

        return {
          ...n,
          data: {
            ...n.data,
            isSelected,
            isHighlighted,
            isVirtualProxy,
          },
        };
      }),
    [nodes, selectedId, highlighted, activeVisibleNodeIds, toggleCluster],
  );

  const displayEdges = useMemo(
    () =>
      edges.map((e) => ({
        ...e,
        data: {
          ...e.data,
          isThrottled: isEdgeThrottled,
        },
      })),
    [edges, isEdgeThrottled],
  );

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">
            {stage || 'Loading'}... {progress}%
          </p>
          <div className="mt-2 h-2 w-64 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>
    );
  }

  if (visibleNodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center text-muted-foreground">
          <p className="text-lg font-medium">No nodes found</p>
          <p className="mt-1 text-sm">
            {rawNodes.length > 0
              ? 'Try adjusting your filters or search query'
              : 'Analyze this repository to see its architecture graph'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="h-full w-full">
      <ReactFlow
        nodes={displayNodes}
        edges={displayEdges}
        onlyRenderVisibleElements
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{ type: 'base' }}
        proOptions={{ hideAttribution: false }}
        nodesDraggable
        nodesConnectable={false}
        elementsSelectable
        zoomOnDoubleClick={false}
      >
        <ViewportInterceptor onViewportChange={handleViewportChange} />
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="hsl(var(--muted-foreground) / 0.2)" />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(n) => {
            const type = (n.data as { node?: GraphNode }).node?.type;
            return (type ? NODE_TYPE_COLORS[type] : undefined) || '#6B7280';
          }}
          maskColor="hsl(var(--muted) / 0.5)"
          style={{ width: 180, height: 120 }}
        />
      </ReactFlow>
    </div>
  );
}
