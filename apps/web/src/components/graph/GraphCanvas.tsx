'use client';

import { useCallback, useEffect, useMemo } from 'react';
import {
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { BaseNode } from './nodes/BaseNode';
import { FlowEdge } from './edges/BaseEdge';
import { useGraphStore, getVisibleNodes, getVisibleEdges } from '@/stores/graphStore';
import type { GraphEdge, GraphNode } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';
import { NODE_TYPE_COLORS } from '@codeatlas/shared';

const nodeTypes = { base: BaseNode };
const edgeTypes = { base: FlowEdge };

function layoutNodes(rawNodes: GraphNode[], rawEdges: GraphEdge[]): { nodes: Node[]; edges: Edge[] } {
  const posMap = new Map<string, { x: number; y: number }>();
  const adj = new Map<string, string[]>();
  const inDeg = new Map<string, number>();

  for (const n of rawNodes) {
    inDeg.set(n.id, 0);
    adj.set(n.id, []);
  }

  for (const e of rawEdges) {
    if (adj.has(e.source_id) && inDeg.has(e.target_id)) {
      adj.get(e.source_id)!.push(e.target_id);
      inDeg.set(e.target_id, (inDeg.get(e.target_id) || 0) + 1);
    }
  }

  // BFS layer assignment
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

  // Assign positions: layer = x, index within layer = y
  const layers = new Map<number, string[]>();
  for (const n of rawNodes) {
    const l = layer.get(n.id) ?? 0;
    if (!layers.has(l)) layers.set(l, []);
    layers.get(l)!.push(n.id);
  }

  for (const [l, ids] of layers) {
    ids.forEach((id, idx) => {
      posMap.set(id, { x: l * 320, y: idx * 120 - (ids.length * 60) });
    });
  }

  const nodes: Node[] = rawNodes.map((n) => {
    const pos = posMap.get(n.id) || { x: 0, y: 0 };
    return {
      id: n.id,
      type: 'base',
      position: pos,
      data: {
        node: n,
        isSelected: false,
        isHighlighted: false,
      },
    };
  });

  const edges: Edge[] = rawEdges.map((e) => ({
    id: e.id,
    source: e.source_id,
    target: e.target_id,
    type: 'base',
    data: { edgeType: e.type },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#9CA3AF' },
  }));

  return { nodes, edges };
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

  const visibleNodes = useMemo(
    () => getVisibleNodes({ rawNodes, filterTypes, searchQuery }),
    [rawNodes, filterTypes, searchQuery],
  );

  const visibleEdges = useMemo(
    () => getVisibleEdges({ rawEdges, visibleNodes }),
    [rawEdges, visibleNodes],
  );

  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(
    () => layoutNodes(visibleNodes, visibleEdges),
    [visibleNodes, visibleEdges],
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

  const displayNodes = useMemo(
    () =>
      nodes.map((n) => ({
        ...n,
        data: {
          ...n.data,
          isSelected: n.id === selectedId,
          isHighlighted: highlighted.has(n.id),
        },
      })),
    [nodes, selectedId, highlighted],
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
    <div className="h-full w-full">
      <ReactFlow
        nodes={displayNodes}
        edges={edges}
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
