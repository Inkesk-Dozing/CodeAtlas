'use client';

import { useCallback, useEffect, use, useState } from 'react';
import { ErrorBoundary } from '@/components/feedback/ErrorBoundary';
import { GraphCanvas } from '@/components/graph/GraphCanvas';
import { GraphToolbar } from '@/components/graph/GraphToolbar';
import { NodeDetailPanel } from '@/components/graph/panels/NodeDetailPanel';
import { SearchPanel } from '@/components/graph/panels/SearchPanel';
import { IssueMappingPanel } from '@/components/panels/IssueMappingPanel';
import { api } from '@/lib/api/client';
import { useGraphStore } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';

export default function GraphPage({ params }: { params: { repoId: string } | Promise<{ repoId: string }> }) {
  const { repoId } = use(params as Promise<{ repoId: string }>);
  const [repoName, setRepoName] = useState<string>('');
  const [loadError, setLoadError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const isLoading = useGraphStore((s) => s.isLoading);
  const progress = useGraphStore((s) => s.progress);
  const stage = useGraphStore((s) => s.stage);
  const nodeCount = useGraphStore((s) => s.rawNodes.length);
  const edgeCount = useGraphStore((s) => s.rawEdges.length);

  const setGraph = useGraphStore((s) => s.setGraph);
  const setLoading = useGraphStore((s) => s.setLoading);
  const setProgress = useGraphStore((s) => s.setProgress);

  const activePanel = useUIStore((s) => s.activePanel);
  const rightPanelOpen = useUIStore((s) => s.rightPanelOpen);

  const fetchGraph = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    setProgress(10, 'Loading');

    try {
      const [graphData, repoData] = await Promise.all([
        api.graph.get(repoId, { limit: 1000 }),
        api.repos.get(repoId),
      ]);

      setProgress(80, 'Rendering');
      setGraph(graphData.nodes as never[], graphData.edges as never[], graphData.total);

      if (repoData && typeof repoData === 'object' && 'name' in repoData) {
        setRepoName(((repoData as Record<string, string>).full_name || (repoData as Record<string, string>).name) ?? '');
      }

      setProgress(100, 'Done');
    } catch (err) {
      console.error('Failed to load graph:', err);
      setLoadError(err instanceof Error ? err.message : 'Failed to load the dependency graph');
      setGraph([], [], 0);
    } finally {
      setLoading(false);
    }
  }, [repoId, setGraph, setLoading, setProgress]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await api.ingestion.trigger(repoId, 'incremental');
      const poll = setInterval(async () => {
        try {
          const status = await api.ingestion.status(repoId);
          if (status && typeof status === 'object' && 'progress' in status) {
            const s = status as Record<string, unknown>;
            if (s.status === 'completed' || s.status === 'failed') {
              clearInterval(poll);
              setRefreshing(false);
              if (s.status === 'completed') fetchGraph();
            }
          }
        } catch {
          clearInterval(poll);
          setRefreshing(false);
        }
      }, 2000);
    } catch (err) {
      console.error('Failed to trigger re-analysis:', err);
      setRefreshing(false);
    }
  }, [repoId, fetchGraph]);

  return (
    <div className="flex h-full">
      <div className="flex flex-1 flex-col overflow-hidden">
        <GraphToolbar repoId={repoId} repoName={repoName} onRefresh={handleRefresh} refreshing={refreshing} />

        <div className="relative flex-1">
          <ErrorBoundary>
            <GraphCanvas />
          </ErrorBoundary>

          {isLoading && (
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-3 bg-background/70 backdrop-blur-sm">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <div className="text-sm text-muted-foreground">
                {stage ? `${stage}…` : 'Loading graph…'}
              </div>
              <div className="h-1.5 w-56 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {loadError && !isLoading && (
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-3">
              <div className="text-sm font-medium text-destructive">Failed to load graph</div>
              <div className="max-w-md text-center text-xs text-muted-foreground">{loadError}</div>
              <button
                onClick={fetchGraph}
                className="rounded-md border border-border bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted"
              >
                Retry
              </button>
            </div>
          )}

          {!isLoading && !loadError && (
            <div className="absolute bottom-3 left-3 z-10 rounded-lg border border-border bg-card/90 px-3 py-1.5 text-xs text-muted-foreground backdrop-blur">
              {nodeCount} nodes · {edgeCount} edges
              {refreshing && <span className="ml-2 text-primary">re-analyzing…</span>}
            </div>
          )}
        </div>
      </div>

      {rightPanelOpen && activePanel === 'node-detail' && (
        <div className="w-96 shrink-0">
          <ErrorBoundary>
            <NodeDetailPanel />
          </ErrorBoundary>
        </div>
      )}
      {rightPanelOpen && activePanel === 'search' && (
        <div className="w-96 shrink-0">
          <ErrorBoundary>
            <SearchPanel repoId={repoId} />
          </ErrorBoundary>
        </div>
      )}
      {rightPanelOpen && activePanel === 'issue-mapping' && (
        <div className="w-96 shrink-0">
          <ErrorBoundary>
            <IssueMappingPanel repoId={repoId} />
          </ErrorBoundary>
        </div>
      )}
    </div>
  );
}
