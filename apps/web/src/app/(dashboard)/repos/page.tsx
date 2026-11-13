'use client';

import { useEffect, useState, useCallback } from 'react';
import { Plus, GitBranch, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api/client';
import { RepoCard, type RepositoryItem } from '@/components/panels/RepoCard';

export default function ReposPage() {
  const [repos, setRepos] = useState<RepositoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRepos = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.repos.list({ limit: 50 });
      setRepos(data as RepositoryItem[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load repositories');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRepos();
  }, [fetchRepos]);

  const handleIngestSuccess = useCallback((_repoId: string) => {
    fetchRepos();
  }, [fetchRepos]);

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border bg-card px-6 py-4">
        <div>
          <h1 className="text-xl font-bold">Repositories</h1>
          <p className="text-sm text-muted-foreground">
            Select a repository to explore its architecture or trigger indexing
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchRepos}
            className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm hover:bg-muted transition-colors"
            data-testid="refresh-repos-btn"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors">
            <Plus className="h-4 w-4" />
            Connect Repo
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6" data-testid="repo-explorer-content">
        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-testid="repos-loading-grid">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-48 animate-pulse rounded-xl border border-border bg-card p-5"
              >
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <div className="h-4 w-32 rounded bg-muted" />
                    <div className="h-3 w-20 rounded bg-muted" />
                  </div>
                  <div className="h-5 w-16 rounded-full bg-muted" />
                </div>
                <div className="mt-4 space-y-2">
                  <div className="h-3 w-full rounded bg-muted" />
                  <div className="h-3 w-2/3 rounded bg-muted" />
                </div>
                <div className="mt-6 h-3 w-40 rounded bg-muted" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div
            className="flex flex-col items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-400"
            data-testid="repos-error-state"
          >
            <span>{error}</span>
            <button
              onClick={fetchRepos}
              className="rounded-md border border-red-300 px-3 py-1 text-xs font-medium hover:bg-red-100 dark:border-red-700 dark:hover:bg-red-900"
            >
              Retry
            </button>
          </div>
        ) : repos.length === 0 ? (
          <div
            className="flex h-64 flex-col items-center justify-center text-center"
            data-testid="repos-empty-state"
          >
            <GitBranch className="mb-4 h-12 w-12 text-muted-foreground/50" />
            <h3 className="text-lg font-medium">No repositories yet</h3>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              Install the CodeAtlas GitHub App on your repositories to start analyzing their
              architecture.
            </p>
            <button className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
              Install GitHub App
            </button>
          </div>
        ) : (
          <div
            className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
            data-testid="repos-grid"
          >
            {repos.map((repo) => (
              <RepoCard
                key={repo.id}
                repo={repo}
                onIngestSuccess={handleIngestSuccess}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
