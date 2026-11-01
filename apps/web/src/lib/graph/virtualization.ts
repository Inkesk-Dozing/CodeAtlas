export interface ViewportRect {
  x: number;
  y: number;
  zoom: number;
  width: number;
  height: number;
}

export interface NodeBoundingBox {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface VisibleFlowBounds {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
}

/**
 * Calculates the bounding box in Flow coordinate space corresponding to the visible viewport.
 * Adds a buffer margin in pixels to enable seamless panning and prevent visual popping.
 */
export function getVisibleFlowBounds(
  viewport: { x: number; y: number; zoom: number },
  dimensions: { width: number; height: number },
  bufferPx = 200,
): VisibleFlowBounds {
  const zoom = Math.max(viewport.zoom, 0.01);
  const minScreenX = -bufferPx;
  const maxScreenX = dimensions.width + bufferPx;
  const minScreenY = -bufferPx;
  const maxScreenY = dimensions.height + bufferPx;

  return {
    minX: (minScreenX - viewport.x) / zoom,
    maxX: (maxScreenX - viewport.x) / zoom,
    minY: (minScreenY - viewport.y) / zoom,
    maxY: (maxScreenY - viewport.y) / zoom,
  };
}

/**
 * Determines whether a node's bounding box intersects with the visible flow bounds.
 */
export function isNodeInVisibleBounds(
  node: { x: number; y: number; width?: number; height?: number },
  bounds: VisibleFlowBounds,
  defaultWidth = 240,
  defaultHeight = 80,
): boolean {
  const nodeWidth = node.width ?? defaultWidth;
  const nodeHeight = node.height ?? defaultHeight;

  const nodeRight = node.x + nodeWidth;
  const nodeBottom = node.y + nodeHeight;

  return (
    nodeRight >= bounds.minX &&
    node.x <= bounds.maxX &&
    nodeBottom >= bounds.minY &&
    node.y <= bounds.maxY
  );
}

/**
 * Filter an array of node IDs to those that intersect the visible viewport.
 * If total visible count exceeds maxActiveNodes, maintains the most central nodes up to the limit.
 */
export function calculateVisibleNodeIds(
  nodes: Array<{ id: string; position: { x: number; y: number }; width?: number; height?: number }>,
  viewport: { x: number; y: number; zoom: number },
  dimensions: { width: number; height: number },
  options: {
    bufferPx?: number;
    maxActiveNodes?: number;
    defaultWidth?: number;
    defaultHeight?: number;
  } = {},
): Set<string> {
  const {
    bufferPx = 150,
    maxActiveNodes = 300,
    defaultWidth = 240,
    defaultHeight = 80,
  } = options;

  if (nodes.length === 0) {
    return new Set();
  }

  // If container dimensions are not ready yet, keep the first chunk up to maxActiveNodes
  if (dimensions.width <= 0 || dimensions.height <= 0) {
    return new Set(nodes.slice(0, Math.min(nodes.length, maxActiveNodes)).map((n) => n.id));
  }

  const bounds = getVisibleFlowBounds(viewport, dimensions, bufferPx);
  const visible: Array<{ id: string; distSq: number }> = [];

  const flowCenterX = (dimensions.width / 2 - viewport.x) / Math.max(viewport.zoom, 0.01);
  const flowCenterY = (dimensions.height / 2 - viewport.y) / Math.max(viewport.zoom, 0.01);

  for (const node of nodes) {
    const isIntersecting = isNodeInVisibleBounds(
      {
        x: node.position.x,
        y: node.position.y,
        width: node.width,
        height: node.height,
      },
      bounds,
      defaultWidth,
      defaultHeight,
    );

    if (isIntersecting) {
      const centerX = node.position.x + (node.width ?? defaultWidth) / 2;
      const centerY = node.position.y + (node.height ?? defaultHeight) / 2;
      const distSq = (centerX - flowCenterX) ** 2 + (centerY - flowCenterY) ** 2;
      visible.push({ id: node.id, distSq });
    }
  }

  // Enforce DOM element threshold cap under maxActiveNodes (e.g. 300)
  if (visible.length > maxActiveNodes) {
    visible.sort((a, b) => a.distSq - b.distSq);
    return new Set(visible.slice(0, maxActiveNodes).map((v) => v.id));
  }

  return new Set(visible.map((v) => v.id));
}

/**
 * Edge throttling check: returns whether edges should be simplified/skipped when zoomed out.
 * When zoom level is < threshold (0.3), complex bezier curves & animated edge labels are throttled.
 */
export function shouldThrottleEdges(zoom: number, threshold = 0.3): boolean {
  return zoom < threshold;
}

