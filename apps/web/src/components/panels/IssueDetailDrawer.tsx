'use client';

import { useState, useCallback, useEffect, useMemo } from 'react';
import {
  ExternalLink,
  ThumbsUp,
  ThumbsDown,
  ChevronDown,
  ChevronRight,
  FileCode,
  ArrowRight,
} from 'lucide-react';
import { api, type CodeMapping, type IssueResponse } from '@/lib/api/client';
import { useGraphStore } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';

export interface IssueDetailDrawerProps {
  repoId: string;
  issue: IssueResponse;
  mappings: CodeMapping[];
  isLoading?: boolean;
  onClose?: () => void;
  onCenterFile?: (nodeId: string) => void;
}

export function IssueDetailDrawer({
  repoId,
  issue,
  mappings,
  isLoading = false,
  onClose,
  onCenterFile,
}: IssueDetailDrawerProps) {
  // Initialize with the top node expanded by default
  const [expandedFileIds, setExpandedFileIds] = useState<Set<string>>(() => {
    const initial = new Set<string>();
    if (mappings.length > 0 && mappings[0].node?.id) {
      initial.add(mappings[0].node.id);
    }
    return initial;
  });
  const [feedback, setFeedback] = useState<Record<string, 'relevant' | 'irrelevant'>>({});
  const [feedbackLoading, setFeedbackLoading] = useState<Record<string, boolean>>({});

  const selectNode = useGraphStore((s) => s.selectNode);
  const setMappedNodes = useGraphStore((s) => s.setMappedNodes);
  const clearMappedNodes = useGraphStore((s) => s.clearMappedNodes);
  const closePanel = useUIStore((s) => s.closePanel);

  // Automatically expand the highest-confidence file when mappings change
  useEffect(() => {
    if (mappings.length > 0) {
      const topNodeId = mappings[0].node?.id;
      if (topNodeId) {
        setExpandedFileIds((prev) => new Set([...prev, topNodeId]));
      }
    }
  }, [mappings]);

  // Highlight mapped subgraph in < 100ms
  useEffect(() => {
    const startTime = performance.now();
    const mappedIds = mappings.map((m) => m.node.id).filter(Boolean);

    setMappedNodes(mappedIds);

    const elapsed = performance.now() - startTime;
    if (process.env.NODE_ENV !== 'production') {
      // Diagnostic check: verify subgraph highlighting satisfies < 100ms criteria
      if (elapsed > 100) {
        console.warn(`Subgraph highlighting took ${elapsed.toFixed(1)}ms (> 100ms)`);
      }
    }

    return () => {
      clearMappedNodes();
    };
  }, [mappings, setMappedNodes, clearMappedNodes]);

  const toggleExpand = useCallback((nodeId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedFileIds((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }, []);

  const handleFileClick = useCallback(
    (nodeId: string) => {
      const startTime = performance.now();
      selectNode(nodeId);
      setMappedNodes([nodeId]);
      onCenterFile?.(nodeId);
      const elapsed = performance.now() - startTime;
      if (process.env.NODE_ENV !== 'production' && elapsed > 100) {
        console.warn(`Center and highlight took ${elapsed.toFixed(1)}ms (> 100ms)`);
      }
    },
    [selectNode, setMappedNodes, onCenterFile],
  );

  const handleFeedback = useCallback(
    async (nodeId: string, rating: 'relevant' | 'irrelevant', e: React.MouseEvent) => {
      e.stopPropagation();
      setFeedbackLoading((prev) => ({ ...prev, [nodeId]: true }));
      try {
        await api.issues.feedback(repoId, issue.number, nodeId, rating);
        setFeedback((prev) => ({ ...prev, [nodeId]: rating }));
      } catch (err) {
        console.error('Failed to submit mapping feedback:', err);
      } finally {
        setFeedbackLoading((prev) => ({ ...prev, [nodeId]: false }));
      }
    },
    [repoId, issue.number],
  );

  // Compute Intent Pill from labels or title
  const intentPill = useMemo(() => {
    const labels: string[] = issue.labels || [];
    const bug = labels.find((l: string) => /bug|fix|error|fault/i.test(l));
    if (bug) return { label: 'Bug Fix', color: 'bg-rose-500/15 text-rose-400 border-rose-500/30' };

    const feat = labels.find((l: string) => /feat|enhancement|feature/i.test(l));
    if (feat) return { label: 'Feature', color: 'bg-primary/15 text-primary border-primary/30' };

    const refactor = labels.find((l: string) => /refactor|cleanup|perf/i.test(l));
    if (refactor) return { label: 'Refactor', color: 'bg-amber-500/15 text-amber-400 border-amber-500/30' };

    return { label: 'Issue', color: 'bg-muted text-muted-foreground border-border' };
  }, [issue.labels]);

  return (
    <div
      className="flex h-full w-full flex-col border-l border-border bg-card shadow-2xl transition-transform duration-300 ease-out"
      data-testid="issue-detail-drawer"
    >
      {/* Header */}
      <div className="flex flex-col gap-2.5 border-b border-border p-4 bg-muted/20">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${intentPill.color}`}
            >
              {intentPill.label}
            </span>
            <span className="text-xs font-mono text-muted-foreground">#{issue.number}</span>
          </div>

          <button
            onClick={onClose || closePanel}
            aria-label="Close drawer"
            className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            ✕
          </button>
        </div>

        <h2 className="text-base font-semibold leading-snug text-foreground break-words line-clamp-2">
          {issue.title}
        </h2>

        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
          {issue.author && (
            <span>
              by <span className="font-medium text-foreground">{issue.author}</span>
            </span>
          )}

          {issue.url && (
            <a
              href={issue.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-primary hover:underline"
              data-testid="issue-github-link"
            >
              <span>GitHub</span>
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
      </div>

      {/* Mapped Files Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
          <span>Mapped Files ({mappings.length})</span>
          <span className="text-[11px] text-emerald-400 flex items-center gap-1 font-mono">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Active Green Subgraph
          </span>
        </div>

        {isLoading ? (
          <div className="py-8 text-center text-sm text-muted-foreground">
            <div className="mx-auto mb-2 h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            Mapping files...
          </div>
        ) : mappings.length === 0 ? (
          <div className="py-8 text-center text-sm text-muted-foreground border border-dashed border-border rounded-lg p-6">
            No mapped files found for this issue.
          </div>
        ) : (
          <div className="space-y-2.5">
            {mappings.map((mapping, idx) => {
              const node = mapping.node;
              const isExpanded = expandedFileIds.has(node.id);
              const pct = Math.round((mapping.confidence || 0) * 100);
              const tier = mapping.confidence_tier || 'low';
              const isHigh = tier === 'high' || pct >= 80;
              const isMedium = tier === 'medium' || (pct >= 50 && pct < 80);

              const badgeColor = isHigh
                ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                : isMedium
                  ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                  : 'bg-rose-500/15 text-rose-400 border-rose-500/30';

              const currentRating = feedback[node.id];
              const isSubmitting = feedbackLoading[node.id];

              return (
                <div
                  key={node.id || idx}
                  onClick={() => handleFileClick(node.id)}
                  className="group rounded-xl border border-border bg-card/90 p-3 shadow-sm transition-all hover:border-emerald-500/50 hover:bg-muted/30 cursor-pointer"
                  data-testid={`mapped-file-${node.id}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2 min-w-0 flex-1">
                      <button
                        type="button"
                        onClick={(e) => toggleExpand(node.id, e)}
                        className="mt-0.5 rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                        aria-label={isExpanded ? 'Collapse' : 'Expand'}
                      >
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </button>

                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5 font-medium text-sm text-foreground truncate">
                          <FileCode className="h-3.5 w-3.5 shrink-0 text-emerald-400" />
                          <span className="truncate">{node.name}</span>
                        </div>
                        <div className="text-xs text-muted-foreground font-mono truncate">
                          {node.path}
                        </div>
                      </div>
                    </div>

                    {/* Confidence Badge */}
                    <span
                      className={`inline-flex shrink-0 items-center rounded-md border px-2 py-0.5 text-xs font-mono font-bold ${badgeColor}`}
                    >
                      {pct}% {tier.toUpperCase()}
                    </span>
                  </div>

                  {/* Expandable Reasoning Section */}
                  {isExpanded && (
                    <div
                      className="mt-3 space-y-2.5 border-t border-border/60 pt-2.5 text-xs animate-in fade-in duration-200"
                      data-testid={`expanded-reasoning-${node.id}`}
                    >
                      {/* Evidence Tags */}
                      <div>
                        <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                          Evidence Tags
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {mapping.evidence?.semantic_match && (
                            <span className="rounded bg-sky-500/15 border border-sky-500/30 px-2 py-0.5 text-[10px] text-sky-400 font-mono">
                              Semantic Match
                            </span>
                          )}
                          {mapping.evidence?.structural_match && (
                            <span className="rounded bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 text-[10px] text-emerald-400 font-mono">
                              Structural Match: {node.name}
                            </span>
                          )}
                          {mapping.evidence?.propagation_match && (
                            <span className="rounded bg-purple-500/15 border border-purple-500/30 px-2 py-0.5 text-[10px] text-purple-400 font-mono">
                              Topological: 1-hop from route
                            </span>
                          )}
                          {mapping.evidence?.historical_match && (
                            <span className="rounded bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 text-[10px] text-amber-400 font-mono">
                              Historical Reviewer Verified
                            </span>
                          )}
                          {mapping.evidence?.matched_keywords?.slice(0, 4).map((kw) => (
                            <span
                              key={kw}
                              className="rounded bg-muted border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground font-mono"
                            >
                              kw: {kw}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Suggested Actions Reasoning */}
                      {mapping.suggested_actions && mapping.suggested_actions.length > 0 && (
                        <div>
                          <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                            Suggested Actions
                          </div>
                          <ul className="space-y-1 rounded-lg bg-background/50 p-2.5 border border-border/50">
                            {mapping.suggested_actions.map((action, aIdx) => (
                              <li
                                key={aIdx}
                                className="flex items-start gap-1.5 text-xs text-foreground/90 font-medium"
                              >
                                <ArrowRight className="h-3 w-3 mt-0.5 shrink-0 text-emerald-400" />
                                <span>{action}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Thumbs Up / Thumbs Down Feedback Buttons */}
                      <div className="flex items-center justify-between border-t border-border/40 pt-2">
                        <span className="text-[11px] text-muted-foreground">
                          Was this mapping accurate?
                        </span>

                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            disabled={isSubmitting}
                            onClick={(e) => handleFeedback(node.id, 'relevant', e)}
                            className={`flex items-center gap-1 rounded-md px-2 py-1 text-xs transition-colors ${
                              currentRating === 'relevant'
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-semibold'
                                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                            }`}
                            title="Relevant"
                            aria-label="Thumbs up"
                            data-testid={`feedback-relevant-${node.id}`}
                          >
                            <ThumbsUp className="h-3.5 w-3.5" />
                            <span>Helpful</span>
                          </button>

                          <button
                            type="button"
                            disabled={isSubmitting}
                            onClick={(e) => handleFeedback(node.id, 'irrelevant', e)}
                            className={`flex items-center gap-1 rounded-md px-2 py-1 text-xs transition-colors ${
                              currentRating === 'irrelevant'
                                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40 font-semibold'
                                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                            }`}
                            title="Irrelevant"
                            aria-label="Thumbs down"
                            data-testid={`feedback-irrelevant-${node.id}`}
                          >
                            <ThumbsDown className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
