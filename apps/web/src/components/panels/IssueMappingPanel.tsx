'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api/client';
import { useGraphStore } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';

interface IssueSummary {
  number: number;
  title: string;
  labels: string[];
  state: string;
}

interface MappingEntry {
  node?: { id?: string; name?: string; path?: string; type?: string };
  confidence?: number;
  confidence_tier?: 'high' | 'medium' | 'low';
  evidence?: { matched_keywords?: string[]; semantic_match?: boolean; structural_match?: boolean };
  suggested_actions?: string[];
}

interface MappingResult {
  status: string;
  mappings: MappingEntry[];
  generated_at?: string | null;
}

const TIER_STYLES: Record<string, string> = {
  high: '#10B981',
  medium: '#F59E0B',
  low: '#EF4444',
};

const POLL_INTERVAL_MS = 1500;
const POLL_TIMEOUT_MS = 60_000;

export function IssueMappingPanel({ repoId }: { repoId: string }) {
  const [issues, setIssues] = useState<IssueSummary[]>([]);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [selectedIssue, setSelectedIssue] = useState<number | null>(null);
  const [mapping, setMapping] = useState<MappingResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const closePanel = useUIStore((s) => s.closePanel);
  const addHighlight = useGraphStore((s) => s.addHighlight);
  const clearHighlight = useGraphStore((s) => s.clearHighlight);
  const selectNode = useGraphStore((s) => s.selectNode);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    setListLoading(true);
    api.issues
      .list(repoId)
      .then((data) => {
        if (!cancelled) setIssues((data as IssueSummary[]) || []);
      })
      .catch((err) => {
        if (!cancelled) setListError(err.message || 'Failed to load issues');
      })
      .finally(() => {
        if (!cancelled) setListLoading(false);
      });
    return () => {
      cancelled = true;
      stopPolling();
      clearHighlight();
    };
  }, [repoId, stopPolling, clearHighlight]);

  const applyMapping = useCallback(
    (result: MappingResult) => {
      setMapping(result);
      const nodeIds = (result.mappings || []).map((m) => m.node?.id).filter(Boolean) as string[];
      if (nodeIds.length > 0) {
        clearHighlight();
        addHighlight(nodeIds);
        selectNode(nodeIds[0]);
      }
    },
    [addHighlight, clearHighlight, selectNode],
  );

  const pollMapping = useCallback(
    (issueNumber: number, startedAt: number) => {
      stopPolling();
      pollRef.current = setInterval(async () => {
        if (Date.now() - startedAt > POLL_TIMEOUT_MS) {
          stopPolling();
          setIsAnalyzing(false);
          setAnalysisError('Analysis timed out — try again.');
          return;
        }
        try {
          const result = (await api.issues.mapping(repoId, issueNumber)) as MappingResult | null;
          if (result && (result.status === 'completed' || result.status === 'failed')) {
            stopPolling();
            setIsAnalyzing(false);
            if (result.status === 'failed') {
              setAnalysisError('Analysis failed. Check API logs.');
            } else {
              setAnalysisError(null);
              applyMapping(result);
            }
          }
        } catch (err) {
          stopPolling();
          setIsAnalyzing(false);
          setAnalysisError(err instanceof Error ? err.message : 'Failed to fetch mapping');
        }
      }, POLL_INTERVAL_MS);
    },
    [repoId, stopPolling, applyMapping],
  );

  const handleIssueClick = useCallback(
    async (issueNumber: number) => {
      setSelectedIssue(issueNumber);
      setMapping(null);
      setAnalysisError(null);
      setIsAnalyzing(true);

      const startedAt = Date.now();
      try {
        await api.issues.analyze(repoId, issueNumber);
        pollMapping(issueNumber, startedAt);
      } catch (err) {
        setIsAnalyzing(false);
        setAnalysisError(err instanceof Error ? err.message : 'Failed to start analysis');
      }
    },
    [repoId, pollMapping],
  );

  return (
    <div className="flex h-full w-full flex-col border-l border-border bg-card">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <span className="text-sm font-semibold">Issue Mapping</span>
        <button
          onClick={closePanel}
          aria-label="Close panel"
          className="rounded-md p-1 text-muted-foreground hover:bg-muted"
        >
          ✕
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {listLoading && <PanelSpinner label="Loading issues…" />}

        {listError && (
          <div className="p-4 text-center text-sm text-destructive">{listError}</div>
        )}

        {!listLoading && !listError && issues.length === 0 && (
          <div className="py-8 text-center text-sm text-muted-foreground">
            No open issues found
          </div>
        )}

        <div>
          {issues.map((issue) => (
            <button
              key={issue.number}
              onClick={() => handleIssueClick(issue.number)}
              disabled={isAnalyzing}
              className={`block w-full border-b border-border px-4 py-3 text-left transition-colors hover:bg-muted disabled:opacity-60 ${
                selectedIssue === issue.number ? 'bg-primary/5' : ''
              }`}
            >
              <div className="flex items-start gap-2">
                <span className="mt-0.5 shrink-0 text-xs text-muted-foreground">
                  #{issue.number}
                </span>
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium">{issue.title}</div>
                  {issue.labels?.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {issue.labels.slice(0, 3).map((l) => (
                        <span
                          key={l}
                          className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground"
                        >
                          {l}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>

        {isAnalyzing && <PanelSpinner label="Analyzing issue…" />}

        {analysisError && (
          <div className="border-t border-border p-4 text-sm text-destructive">
            {analysisError}
          </div>
        )}

        {!isAnalyzing && mapping && mapping.mappings?.length === 0 && (
          <div className="border-t border-border p-4 text-sm text-muted-foreground">
            No relevant code locations found for this issue.
          </div>
        )}

        {!isAnalyzing && mapping && mapping.mappings?.length > 0 && (
          <div className="border-t border-border p-4">
            <div className="mb-3 flex items-center justify-between text-xs font-medium text-muted-foreground">
              <span>Mapped Files ({mapping.mappings.length})</span>
              <span className="rounded bg-muted px-1.5 py-0.5">{mapping.status}</span>
            </div>
            <div className="space-y-2">
              {mapping.mappings.map((m, i) => {
                const tier = m.confidence_tier || 'low';
                const color = TIER_STYLES[tier] || TIER_STYLES.low;
                const pct = Math.round((m.confidence || 0) * 100);
                return (
                  <div
                    key={m.node?.id || i}
                    className="rounded-lg border border-border p-3 transition-colors hover:border-primary/40"
                    style={{ borderLeftColor: color, borderLeftWidth: 3 }}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate text-sm font-medium">{m.node?.name}</span>
                      <span className="shrink-0 text-xs text-muted-foreground">{pct}%</span>
                    </div>
                    <div className="truncate text-xs text-muted-foreground">{m.node?.path}</div>

                    <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-muted">
                      <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
                    </div>

                    {m.evidence?.matched_keywords && m.evidence.matched_keywords.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {m.evidence.matched_keywords.slice(0, 5).map((k) => (
                          <span
                            key={k}
                            className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground"
                          >
                            {k}
                          </span>
                        ))}
                      </div>
                    )}

                    {m.suggested_actions && m.suggested_actions.length > 0 && (
                      <ul className="mt-2 space-y-1">
                        {m.suggested_actions.slice(0, 3).map((a, j) => (
                          <li key={j} className="text-xs text-muted-foreground">
                            • {a}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function PanelSpinner({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center gap-2 p-4 text-sm text-muted-foreground">
      <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      {label}
    </div>
  );
}
