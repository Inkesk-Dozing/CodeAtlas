'use client';

import { memo } from 'react';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Lock,
  Unlock,
  MapPin,
  MapPinOff,
} from 'lucide-react';

export interface CanvasControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitView: () => void;
  isLocked: boolean;
  onToggleLock: () => void;
  showMinimap: boolean;
  onToggleMinimap: () => void;
  className?: string;
}

export const CanvasControls = memo(function CanvasControls({
  onZoomIn,
  onZoomOut,
  onFitView,
  isLocked,
  onToggleLock,
  showMinimap,
  onToggleMinimap,
  className = '',
}: CanvasControlsProps) {
  return (
    <div
      className={`absolute bottom-6 left-6 z-30 flex items-center gap-1 rounded-xl border border-border/80 bg-card/90 p-1.5 shadow-xl backdrop-blur-md transition-all ${className}`}
      data-testid="canvas-controls"
    >
      <button
        type="button"
        onClick={onZoomIn}
        className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        title="Zoom In"
        aria-label="Zoom in"
        data-testid="canvas-zoom-in"
      >
        <ZoomIn className="h-4 w-4" />
      </button>

      <button
        type="button"
        onClick={onZoomOut}
        className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        title="Zoom Out"
        aria-label="Zoom out"
        data-testid="canvas-zoom-out"
      >
        <ZoomOut className="h-4 w-4" />
      </button>

      <button
        type="button"
        onClick={onFitView}
        className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        title="Zoom to Fit (50px padding)"
        aria-label="Zoom to fit"
        data-testid="canvas-fit-view"
      >
        <Maximize2 className="h-4 w-4" />
      </button>

      <div className="mx-1 h-4 w-[1px] bg-border" />

      <button
        type="button"
        onClick={onToggleLock}
        className={`rounded-lg p-2 transition-colors focus:outline-none focus:ring-1 focus:ring-primary ${
          isLocked
            ? 'bg-amber-500/15 text-amber-400 hover:bg-amber-500/25'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
        }`}
        title={isLocked ? 'Unlock Canvas' : 'Lock Canvas'}
        aria-label={isLocked ? 'Unlock canvas' : 'Lock canvas'}
        data-testid="canvas-lock-toggle"
      >
        {isLocked ? <Lock className="h-4 w-4" /> : <Unlock className="h-4 w-4" />}
      </button>

      <button
        type="button"
        onClick={onToggleMinimap}
        className={`rounded-lg p-2 transition-colors focus:outline-none focus:ring-1 focus:ring-primary ${
          showMinimap
            ? 'bg-primary/15 text-primary hover:bg-primary/25'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
        }`}
        title={showMinimap ? 'Hide Minimap' : 'Show Minimap'}
        aria-label={showMinimap ? 'Hide minimap' : 'Show minimap'}
        data-testid="canvas-minimap-toggle"
      >
        {showMinimap ? <MapPin className="h-4 w-4" /> : <MapPinOff className="h-4 w-4" />}
      </button>
    </div>
  );
});
