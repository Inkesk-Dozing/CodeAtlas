import { describe, it, expect, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { CanvasControls } from './CanvasControls';
import { useGraphStore } from '@/stores/graphStore';

describe('CanvasControls and Navigation Integration', () => {
  it('renders floating controls toolbar with all action buttons', () => {
    const html = renderToStaticMarkup(
      <CanvasControls
        onZoomIn={vi.fn()}
        onZoomOut={vi.fn()}
        onFitView={vi.fn()}
        isLocked={false}
        onToggleLock={vi.fn()}
        showMinimap={true}
        onToggleMinimap={vi.fn()}
      />,
    );

    expect(html).toContain('data-testid="canvas-controls"');
    expect(html).toContain('data-testid="canvas-zoom-in"');
    expect(html).toContain('data-testid="canvas-zoom-out"');
    expect(html).toContain('data-testid="canvas-fit-view"');
    expect(html).toContain('data-testid="canvas-lock-toggle"');
    expect(html).toContain('data-testid="canvas-minimap-toggle"');
    expect(html).toContain('Zoom to Fit');
  });

  it('reflects lock state accurately in button styling and title', () => {
    const unlockedHtml = renderToStaticMarkup(
      <CanvasControls
        onZoomIn={vi.fn()}
        onZoomOut={vi.fn()}
        onFitView={vi.fn()}
        isLocked={false}
        onToggleLock={vi.fn()}
        showMinimap={true}
        onToggleMinimap={vi.fn()}
      />,
    );
    expect(unlockedHtml).toContain('title="Lock Canvas"');

    const lockedHtml = renderToStaticMarkup(
      <CanvasControls
        onZoomIn={vi.fn()}
        onZoomOut={vi.fn()}
        onFitView={vi.fn()}
        isLocked={true}
        onToggleLock={vi.fn()}
        showMinimap={true}
        onToggleMinimap={vi.fn()}
      />,
    );
    expect(lockedHtml).toContain('title="Unlock Canvas"');
    expect(lockedHtml).toContain('bg-amber-500/15');
  });

  it('reflects minimap visibility toggle state', () => {
    const visibleHtml = renderToStaticMarkup(
      <CanvasControls
        onZoomIn={vi.fn()}
        onZoomOut={vi.fn()}
        onFitView={vi.fn()}
        isLocked={false}
        onToggleLock={vi.fn()}
        showMinimap={true}
        onToggleMinimap={vi.fn()}
      />,
    );
    expect(visibleHtml).toContain('title="Hide Minimap"');
    expect(visibleHtml).toContain('bg-primary/15');

    const hiddenHtml = renderToStaticMarkup(
      <CanvasControls
        onZoomIn={vi.fn()}
        onZoomOut={vi.fn()}
        onFitView={vi.fn()}
        isLocked={false}
        onToggleLock={vi.fn()}
        showMinimap={false}
        onToggleMinimap={vi.fn()}
      />,
    );
    expect(hiddenHtml).toContain('title="Show Minimap"');
  });

  it('supports pulseNode state in graphStore for search centering highlights', () => {
    expect(useGraphStore.getState().pulsingNodeId).toBeNull();

    useGraphStore.getState().setPulseNode('node-hit-123');
    expect(useGraphStore.getState().pulsingNodeId).toBe('node-hit-123');

    useGraphStore.getState().setPulseNode(null);
    expect(useGraphStore.getState().pulsingNodeId).toBeNull();
  });
});
