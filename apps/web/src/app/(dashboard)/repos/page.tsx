'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Plus, GitBranch, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api/client';

interface Repo {
  id: string;
  name: string;
  full_name: string;
  owner: string;
  language: string | null;
  description: string | null;
  status: string;
  node_count: number;
  edge_count: number;
  last_analyzed_at: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  analyzing: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  ready: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  disabled: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
};

export default function ReposPage() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRepos = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.repos.list({ limit: 50 });
      setRepos(data as Repo[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load repositories');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRepos();
  }, []);

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border bg-card px-6 py-4">
        <div>
          <h1 className="text-xl font-bold">Repositories</h1>
          <p className="text-sm text-muted-foreground">
            Select a repository to explore its architecture
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchRepos}
            className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm hover:bg-muted"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
            <Plus className="h-4 w-4" />
            Connect Repo
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-44 animate-pulse rounded-xl border border-border bg-card p-5"
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
                <div className="mt-5 h-3 w-40 rounded bg-muted" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="flex flex-col items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-400">
            <span>{error}</span>
            <button
              onClick={fetchRepos}
              className="rounded-md border border-red-300 px-3 py-1 text-xs font-medium hover:bg-red-100 dark:border-red-700 dark:hover:bg-red-900"
            >
              Retry
            </button>
          </div>
        ) : repos.length === 0 ? (
          <div className="flex h-64 flex-col items-center justify-center text-center">
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
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {repos.map((repo) => (
              <Link
                key={repo.id}
                href={`/repos/${repo.id}/graph`}
                className="group rounded-xl border border-border bg-card p-5 transition-all hover:border-primary/50 hover:shadow-md"
              >
                <div className="flex items-start justify-between">
                  <div className="min-w-0">
                    <div className="truncate text-base font-semibold group-hover:text-primary">
                      {repo.name}
                    </div>
                    <div className="truncate text-sm text-muted-foreground">{repo.owner}</div>
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[repo.status] || ''}`}
                  >
                    {repo.status}
                  </span>
                </div>

                {repo.description && (
                  <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">
                    {repo.description}
                  </p>
                )}

                <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground">
                  {repo.language && (
                    <span className="flex items-center gap-1">
                      <span className="h-2 w-2 rounded-full bg-primary" />
                      {repo.language}
                    </span>
                  )}
                  <span>{repo.node_count} nodes</span>
                  <span>{repo.edge_count} edges</span>
                </div>

                {repo.last_analyzed_at && (
                  <div className="mt-2 text-xs text-muted-foreground/70">
                    Analyzed {new Date(repo.last_analyzed_at).toLocaleDateString()}
                  </div>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
