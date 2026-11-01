'use client';

import { ExternalLink, History, Milestone, User, X } from 'lucide-react';
import { useChronosStore } from '@/stores/chronosStore';
import { useUIStore } from '@/stores/uiStore';

export function ChronosArchaeologyModal() {
  const activePanel = useUIStore((s) => s.activePanel);
  const closePanel = useUIStore((s) => s.closePanel);

  const archaeologyRecord = useChronosStore((s) => s.archaeologyRecord);
  const isArchaeologyLoading = useChronosStore((s) => s.isArchaeologyLoading);

  if (activePanel !== 'chronos-archaeology') return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="relative flex max-h-[85vh] w-full max-w-xl flex-col rounded-xl border border-border bg-card shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-4 bg-muted/30">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/20 text-primary">
              <History className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-foreground">Chronos Architectural Archaeology</h2>
              <p className="text-xs text-muted-foreground">
                Understand the historical context, author intent, and evolution of this component
              </p>
            </div>
          </div>
          <button
            onClick={closePanel}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {isArchaeologyLoading ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <p className="text-xs text-muted-foreground">Retrieving historical git blame & PR decisions...</p>
            </div>
          ) : archaeologyRecord ? (
            <div className="space-y-4 text-xs">
              <div className="rounded-lg border border-border bg-muted/30 p-3">
                <span className="text-muted-foreground block text-[11px] mb-1">Target Component:</span>
                <span className="font-mono text-foreground font-semibold block">{archaeologyRecord.node_path}</span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-border bg-card p-3">
                  <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                    <User className="h-3.5 w-3.5 text-primary" />
                    <span>Original Author:</span>
                  </div>
                  <span className="font-semibold text-foreground font-mono">{archaeologyRecord.original_author}</span>
                </div>
                <div className="rounded-lg border border-border bg-card p-3">
                  <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                    <Milestone className="h-3.5 w-3.5 text-primary" />
                    <span>Introduced In:</span>
                  </div>
                  <span className="font-semibold text-foreground font-mono">
                    {archaeologyRecord.created_in_commit.slice(0, 10)}
                  </span>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-foreground mb-1.5">Original Architectural Decision Rationale:</h4>
                <div className="rounded-lg border border-primary/20 bg-primary/5 p-3 text-muted-foreground leading-relaxed">
                  {archaeologyRecord.decision_context}
                </div>
              </div>

              {archaeologyRecord.linked_prs.length > 0 && (
                <div>
                  <h4 className="font-semibold text-foreground mb-1.5">Correlated Pull Requests:</h4>
                  <div className="space-y-1.5">
                    {archaeologyRecord.linked_prs.map((pr, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between rounded-lg border border-border bg-muted/20 px-3 py-2"
                      >
                        <div className="flex items-center gap-2">
                          <span className="rounded bg-primary/10 px-1.5 py-0.5 font-mono text-[11px] font-semibold text-primary">
                            #{pr.number}
                          </span>
                          <span className="text-foreground">{pr.title}</span>
                        </div>
                        {pr.url && (
                          <a
                            href={pr.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary hover:underline inline-flex items-center gap-1"
                          >
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <h4 className="font-semibold text-foreground mb-1">Evolution Summary & Hotspot Velocity:</h4>
                <p className="text-muted-foreground leading-relaxed">{archaeologyRecord.evolution_summary}</p>
                <div className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-emerald-400 font-medium">
                  Hotspot Trend: {archaeologyRecord.hotspot_trend}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">No archaeological record found for this node.</div>
          )}
        </div>

        <div className="flex justify-end border-t border-border px-5 py-3 bg-muted/20">
          <button
            onClick={closePanel}
            className="rounded-lg bg-secondary px-4 py-1.5 text-xs font-medium text-secondary-foreground hover:bg-secondary/80"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
