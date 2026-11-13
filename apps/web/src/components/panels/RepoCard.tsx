'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Star,
  Layers,
  ArrowRight,
  Play,
  AlertCircle,
  Loader2,
  Clock,
  Sparkles,
} from 'lucide-react';
import { api, type IngestionStatusResponse } from '@/lib/api/client';

export interface RepositoryItem {
  id: string;
  name: string;
  full_name: string;
  owner: string;
  language: string | null;
  description: string | null;
  status: string;
  node_count: number;
  edge_count: number;
  star_count?: number;
  last_analyzed_at: string | null;
}

export interface RepoCardProps {
  repo: RepositoryItem;
  onIngestSuccess?: (repoId: string) => void;
}

export const STATUS_PILL_CONFIG: Record<
  string,
  { label: string; bg: string; text: string; border: string; animate?: boolean }
> = {
  ready: {
    label: 'Ready',
    bg: 'bg-emerald-500/15',
    text: 'text-emerald-400',
    border: 'border-emerald-500/30',
  },
  cloning: {
    label: 'Cloning',
    bg: 'bg-blue-500/15',
    text: 'text-blue-400',
    border: 'border-blue-500/30',
    animate: true,
  },
  parsing: {
    label: 'Parsing',
    bg: 'bg-indigo-500/15',
    text: 'text-indigo-400',
    border: 'border-indigo-500/30',
    animate: true,
  },
  extracting: {
    label: 'Extracting',
    bg: 'bg-purple-500/15',
    text: 'text-purple-400',
    border: 'border-purple-500/30',
    animate: true,
  },
  embedding: {
    label: 'Embedding',
    bg: 'bg-cyan-500/15',
    text: 'text-cyan-400',
    border: 'border-cyan-500/30',
    animate: true,
  },
  analyzing: {
    label: 'Analyzing',
    bg: 'bg-blue-500/15',
    text: 'text-blue-400',
    border: 'border-blue-500/30',
    animate: true,
  },
  queued: {
    label: 'Queued',
    bg: 'bg-amber-500/15',
    text: 'text-amber-400',
    border: 'border-amber-500/30',
    animate: true,
  },
  running: {
    label: 'Running',
    bg: 'bg-sky-500/15',
    text: 'text-sky-400',
    border: 'border-sky-500/30',
    animate: true,
  },
  failed: {
    label: 'Failed',
    bg: 'bg-rose-500/15',
    text: 'text-rose-400',
    border: 'border-rose-500/30',
  },
  error: {
    label: 'Failed',
    bg: 'bg-rose-500/15',
    text: 'text-rose-400',
    border: 'border-rose-500/30',
  },
  pending: {
    label: 'Pending',
    bg: 'bg-muted',
    text: 'text-muted-foreground',
    border: 'border-border',
  },
};

export function RepoCard({ repo, onIngestSuccess }: RepoCardProps) {
  const router = useRouter();
  const [currentStatus, setCurrentStatus] = useState(repo.status.toLowerCase());
  const [activeStage, setActiveStage] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isTriggering, setIsTriggering] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const isIngesting = [
    'cloning',
    'parsing',
    'extracting',
    'embedding',
    'analyzing',
    'queued',
    'running',
  ].includes(currentStatus);

  // Poll status when ingestion is active
  useEffect(() => {
    if (!isIngesting) return;

    let isMounted = true;
    const interval = setInterval(async () => {
      try {
        const res = (await api.ingestion.status(repo.id, taskId || undefined)) as IngestionStatusResponse | null;
        if (!isMounted || !res) return;

        const newStatus = (res.status || '').toLowerCase();
        setCurrentStatus(newStatus);
        setProgress(res.progress || 0);
        if (res.current_stage) {
          setActiveStage(res.current_stage);
        }

        if (newStatus === 'ready' || newStatus === 'completed') {
          setCurrentStatus('ready');
          clearInterval(interval);
          onIngestSuccess?.(repo.id);
          // Navigate to graph upon successful completion
          router.push(`/repos/${repo.id}/graph`);
        } else if (newStatus === 'failed' || newStatus === 'error') {
          setCurrentStatus('failed');
          setErrorMsg(res.error || 'Ingestion task encountered an error');
          clearInterval(interval);
        }
      } catch {
        // Continue polling or log
      }
    }, 2000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [isIngesting, repo.id, taskId, onIngestSuccess, router]);

  const handleTriggerIngest = useCallback(
    async (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();

      setIsTriggering(true);
      setErrorMsg(null);

      try {
        const res = await api.ingestion.trigger(repo.id, 'full');
        if (res?.id) {
          setTaskId(res.id);
        }
        setCurrentStatus((res?.status || 'queued').toLowerCase());
      } catch (err) {
        setErrorMsg(err instanceof Error ? err.message : 'Failed to trigger ingestion');
      } finally {
        setIsTriggering(false);
      }
    },
    [repo.id],
  );

  const statusConfig = STATUS_PILL_CONFIG[currentStatus] || {
    label: currentStatus,
    bg: 'bg-muted',
    text: 'text-muted-foreground',
    border: 'border-border',
  };

  const displayStage = activeStage
    ? activeStage.charAt(0).toUpperCase() + activeStage.slice(1)
    : statusConfig.label;

  return (
    <div
      className="group relative flex flex-col justify-between rounded-xl border border-border bg-card p-5 transition-all hover:border-primary/50 hover:shadow-lg"
      data-testid={`repo-card-${repo.id}`}
    >
      {/* Top Header */}
      <div>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <Link
              href={`/repos/${repo.id}/graph`}
              className="block truncate text-base font-semibold text-foreground transition-colors group-hover:text-primary"
              title={repo.name}
            >
              {repo.name}
            </Link>
            <div className="truncate text-xs text-muted-foreground">{repo.full_name || repo.owner}</div>
          </div>

          {/* Status Indicator Pill */}
          <span
            className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${statusConfig.bg} ${statusConfig.text} ${statusConfig.border}`}
            data-testid={`status-pill-${repo.id}`}
          >
            {statusConfig.animate && <Loader2 className="h-3 w-3 animate-spin" />}
            {displayStage}
          </span>
        </div>

        {/* Description */}
        <p className="mt-3 line-clamp-2 min-h-[2.5rem] text-xs text-muted-foreground leading-relaxed">
          {repo.description || 'No description provided for this repository.'}
        </p>

        {/* Live Progress Bar if Ingesting */}
        {isIngesting && (
          <div className="mt-3">
            <div className="flex items-center justify-between text-[11px] text-muted-foreground mb-1">
              <span className="font-mono flex items-center gap-1">
                <Sparkles className="h-3 w-3 text-cyan-400" />
                {displayStage}...
              </span>
              <span className="font-mono font-medium">{progress}%</span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-primary transition-all duration-300"
                style={{ width: `${Math.max(progress, 5)}%` }}
              />
            </div>
          </div>
        )}

        {/* Error Alert if failed */}
        {errorMsg && (
          <div className="mt-2.5 flex items-center gap-1.5 rounded-md border border-rose-500/30 bg-rose-500/10 px-2 py-1 text-xs text-rose-400">
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            <span className="truncate">{errorMsg}</span>
          </div>
        )}
      </div>

      {/* Metrics & Bottom Actions */}
      <div className="mt-5 border-t border-border/60 pt-3">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-3">
            {/* Primary Language */}
            {repo.language && (
              <span className="flex items-center gap-1 font-medium text-foreground">
                <span className="h-2 w-2 rounded-full bg-primary" />
                {repo.language}
              </span>
            )}

            {/* Stars */}
            {typeof repo.star_count === 'number' && (
              <span className="flex items-center gap-1" title="GitHub Stars">
                <Star className="h-3.5 w-3.5 text-amber-400 fill-amber-400" />
                {repo.star_count.toLocaleString()}
              </span>
            )}

            {/* AST Nodes */}
            <span className="flex items-center gap-1" title="AST Nodes Count">
              <Layers className="h-3.5 w-3.5" />
              {repo.node_count.toLocaleString()} nodes
            </span>
          </div>

          {/* Timestamp */}
          {repo.last_analyzed_at && (
            <div className="hidden sm:flex items-center gap-1 text-[11px] text-muted-foreground/80">
              <Clock className="h-3 w-3" />
              <span>{new Date(repo.last_analyzed_at).toLocaleDateString()}</span>
            </div>
          )}
        </div>

        {/* Action Button Bar */}
        <div className="mt-3.5 flex items-center gap-2">
          <button
            onClick={handleTriggerIngest}
            disabled={isIngesting || isTriggering}
            className={`inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-all ${
              isIngesting || isTriggering
                ? 'cursor-not-allowed border-border/40 bg-muted/50 text-muted-foreground'
                : 'border-border bg-card hover:border-primary/60 hover:bg-muted text-foreground'
            }`}
            data-testid={`ingest-btn-${repo.id}`}
          >
            {isIngesting || isTriggering ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                <span>Ingesting...</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 text-emerald-400 fill-emerald-400" />
                <span>Ingest Repository</span>
              </>
            )}
          </button>

          <Link
            href={`/repos/${repo.id}/graph`}
            className="inline-flex items-center justify-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm"
            data-testid={`explore-graph-btn-${repo.id}`}
          >
            <span>Explore</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
