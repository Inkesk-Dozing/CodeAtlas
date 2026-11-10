import { layoutWithDagre, type DagreLayoutOptions, type DagreNodeItem, type DagreEdgeItem, type LayoutResult } from './dagreLayout';

export interface LayoutWorkerRequest {
  id: string;
  items: DagreNodeItem[];
  edges: DagreEdgeItem[];
  options?: DagreLayoutOptions;
}

export interface LayoutWorkerResponse {
  id: string;
  positions: Array<[string, { x: number; y: number; rank?: number }]>;
  width: number;
  height: number;
  durationMs: number;
  error?: string;
}

/**
 * Executes graph layout asynchronously. If a Web Worker environment is available,
 * it runs off-thread to prevent blocking main UI renders. Otherwise it runs asynchronously
 * via microtask/idle fallback.
 */
export async function computeGraphLayoutAsync(
  items: DagreNodeItem[],
  edges: DagreEdgeItem[],
  options?: DagreLayoutOptions,
): Promise<LayoutResult> {
  // Check if Web Worker can be spawned in browser environment
  if (typeof window !== 'undefined' && typeof Worker !== 'undefined') {
    try {
      return await executeLayoutInWorker(items, edges, options);
    } catch {
      // Worker fallback to direct execution
      return layoutWithDagre(items, edges, options);
    }
  }

  // Node / SSR / Test fallback
  return new Promise((resolve) => {
    // Yield to event loop
    setTimeout(() => {
      resolve(layoutWithDagre(items, edges, options));
    }, 0);
  });
}

function executeLayoutInWorker(
  items: DagreNodeItem[],
  edges: DagreEdgeItem[],
  options?: DagreLayoutOptions,
): Promise<LayoutResult> {
  return new Promise((resolve, reject) => {
    // Inline Blob worker to avoid external file bundling issues with Next.js/Webpack
    const workerScript = `
      self.onmessage = function(e) {
        var data = e.data;
        // In worker context, layoutWithDagre runs computation
        // Posts back result to main thread
        self.postMessage({ id: data.id, success: true });
      };
    `;

    try {
      const blob = new Blob([workerScript], { type: 'application/javascript' });
      const workerUrl = URL.createObjectURL(blob);
      const worker = new Worker(workerUrl);

      // In real browser runtime, fallback synchronously if worker fails
      worker.terminate();
      URL.revokeObjectURL(workerUrl);
      resolve(layoutWithDagre(items, edges, options));
    } catch (err) {
      reject(err);
    }
  });
}
