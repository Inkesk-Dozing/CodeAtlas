import { describe, expect, it } from 'vitest';
import {
  calculateVisibleNodeIds,
  getVisibleFlowBounds,
  isNodeInVisibleBounds,
  shouldThrottleEdges,
} from './virtualization';

describe('virtualization utils', () => {
  it('correctly calculates visible flow bounds from viewport coordinates', () => {
    const viewport = { x: 100, y: 50, zoom: 1 };
    const dimensions = { width: 1000, height: 800 };
    const buffer = 100;

    const bounds = getVisibleFlowBounds(viewport, dimensions, buffer);
    expect(bounds.minX).toBe(-200); // (-100 - 100) / 1
    expect(bounds.maxX).toBe(1000); // (1000 + 100 - 100) / 1
    expect(bounds.minY).toBe(-150); // (-100 - 50) / 1
    expect(bounds.maxY).toBe(850); // (800 + 100 - 50) / 1
  });

  it('determines whether nodes intersect visible flow bounds', () => {
    const bounds = { minX: 0, maxX: 500, minY: 0, maxY: 400 };

    // Fully inside
    expect(isNodeInVisibleBounds({ x: 50, y: 50, width: 200, height: 80 }, bounds)).toBe(true);

    // Partially overlapping on the right edge
    expect(isNodeInVisibleBounds({ x: 450, y: 50, width: 200, height: 80 }, bounds)).toBe(true);

    // Completely outside to the right
    expect(isNodeInVisibleBounds({ x: 550, y: 50, width: 200, height: 80 }, bounds)).toBe(false);

    // Completely outside to the top
    expect(isNodeInVisibleBounds({ x: 100, y: -200, width: 200, height: 80 }, bounds)).toBe(false);
  });

  it('caps active node count under 300 elements for 2,500 nodes', () => {
    // Generate 2,500 synthetic nodes across a huge grid
    const nodes = Array.from({ length: 2500 }, (_, i) => ({
      id: `node-${i}`,
      position: {
        x: (i % 50) * 100,
        y: Math.floor(i / 50) * 100,
      },
      width: 240,
      height: 80,
    }));

    const viewport = { x: 0, y: 0, zoom: 0.2 };
    const dimensions = { width: 1920, height: 1080 };

    const visibleIds = calculateVisibleNodeIds(nodes, viewport, dimensions, {
      maxActiveNodes: 300,
      bufferPx: 100,
    });

    expect(visibleIds.size).toBeLessThanOrEqual(300);
    expect(visibleIds.size).toBeGreaterThan(0);
  });

  it('correctly throttles edges when zoom < 0.3', () => {
    expect(shouldThrottleEdges(0.2)).toBe(true);
    expect(shouldThrottleEdges(0.29)).toBe(true);
    expect(shouldThrottleEdges(0.3)).toBe(false);
    expect(shouldThrottleEdges(0.5)).toBe(false);
    expect(shouldThrottleEdges(1.0)).toBe(false);
  });
});

