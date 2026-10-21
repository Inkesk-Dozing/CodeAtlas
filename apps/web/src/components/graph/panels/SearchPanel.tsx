'use client';

import { useState, useCallback } from 'react';
import { Search, X, Loader2 } from 'lucide-react';
import { api } from '@/lib/api/client';
import { useGraphStore, type GraphNode } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';
import { NODE_TYPE_COLORS, NODE_TYPE_LABELS } from '@codeatlas/shared';

interface SearchResult {
  node: GraphNode;
  score: number;
  match_type: string;
  snippet: string | null;
}

export function SearchPanel({ repoId }: { repoId: string }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tookMs, setTookMs] = useState<number | null>(null);

  const selectNode = useGraphStore((s) => s.selectNode);
  const addHighlight = useGraphStore((s) => s.addHighlight);
  const closePanel = useUIStore((s) => s.closePanel);

  const handleSearch = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault();
      if (!query.trim()) return;

      setIsLoading(true);
      setError(null);

      try {
        const data = await api.search.semantic(repoId, query, 20);
        setResults(data.results as SearchResult[]);
        setTookMs(data.took_ms);

        const nodeIds = (data.results as SearchResult[]).map((r) => r.node.id);
        if (nodeIds.length > 0) {
          addHighlight(nodeIds);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Search failed');
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    },
    [query, repoId, addHighlight],
  );

  const handleResultClick = useCallback(
    (nodeId: string) => {
      selectNode(nodeId);
      useUIStore.getState().openPanel('node-detail');
    },
    [selectNode],
  );

  return (
    <div className="flex h-full w-full flex-col border-l border-border bg-card">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-semibold">Semantic Search</span>
        </div>
        <button
          onClick={closePanel}
          className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="border-b border-border p-4">
        <form onSubmit={handleSearch}>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='e.g. "Where is the auth middleware?"'
              className="w-full rounded-lg border border-border bg-background py-2 pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="mt-2 w-full rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Searching...
              </span>
            ) : (
              'Search'
            )}
          </button>
        </form>

        {error && (
          <div className="mt-2 rounded-lg border border-red-200 bg-red-50 p-2 text-xs text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-400">
            {error}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        {tookMs !== null && results.length > 0 && (
          <div className="border-b border-border px-4 py-2 text-xs text-muted-foreground">
            {results.length} results in {tookMs}ms
          </div>
        )}

        {results.map((result) => (
          <button
            key={result.node.id}
            onClick={() => handleResultClick(result.node.id)}
            className="block w-full border-b border-border px-4 py-3 text-left transition-colors hover:bg-muted"
          >
            <div className="flex items-start gap-2">
              <div
                className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded text-[10px] font-bold text-white"
                style={{ backgroundColor: NODE_TYPE_COLORS[result.node.type] || '#6B7280' }}
              >
                {result.node.type.charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-medium">{result.node.name}</span>
                  <span className="shrink-0 text-[10px] text-muted-foreground">
                    {Math.round(result.score * 100)}%
                  </span>
                </div>
                <div className="truncate text-xs text-muted-foreground">{result.node.path}</div>
                {result.snippet && (
                  <div className="mt-1 text-xs text-muted-foreground/80 line-clamp-2">
                    {result.snippet}
                  </div>
                )}
                <div className="mt-1 flex items-center gap-1.5">
                  <span className="rounded bg-muted px-1 py-0.5 text-[10px] text-muted-foreground">
                    {NODE_TYPE_LABELS[result.node.type] || result.node.type}
                  </span>
                  <span className="rounded bg-muted px-1 py-0.5 text-[10px] text-muted-foreground">
                    {result.match_type}
                  </span>
                </div>
              </div>
            </div>
          </button>
        ))}

        {results.length === 0 && !isLoading && query && (
          <div className="py-8 text-center text-sm text-muted-foreground">
            No results found for &quot;{query}&quot;
          </div>
        )}

        {results.length === 0 && !query && (
          <div className="py-8 text-center text-sm text-muted-foreground">
            <Search className="mx-auto mb-2 h-8 w-8 opacity-50" />
            <p>Ask a natural language question</p>
            <p className="mt-1 text-xs">e.g. &quot;Where is user authentication handled?&quot;</p>
          </div>
        )}
      </div>
    </div>
  );
}
