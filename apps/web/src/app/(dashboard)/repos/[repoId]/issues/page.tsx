'use client';

import { useEffect, useState, use } from 'react';
import { GitBranch, Loader2, ThumbsUp, ThumbsDown, ExternalLink } from 'lucide-react';
import { api, type CodeMapping } from '@/lib/api/client';

interface Issue {
  id: string;
  number: number;
  title: string;
  body: string | null;
  state: string;
  labels: string[];
  assignees: string[];
  author: string | null;
  url: string | null;
}

export default function IssuesPage({
  params,
}: {
  params: { repoId: string } | Promise<{ repoId: string }>;
}) {
  const { repoId } = use(params as Promise<{ repoId: string }>);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);
  const [mappings, setMappings] = useState<CodeMapping[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState<Record<string, string>>({});

  useEffect(() => {
    api.issues
      .list(repoId)
      .then((data) => setIssues(data as Issue[]))
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [repoId]);

  const handleIssueSelect = async (issue: Issue) => {
    setSelectedIssue(issue);
    setMappings([]);
    setIsAnalyzing(true);

    try {
      await api.issues.analyze(repoId, issue.number);
      // Poll for mapping
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        try {
          const r = await api.issues.mapping(repoId, issue.number);
          if (r?.status === 'completed') {
            setMappings(r.mappings || []);
            setIsAnalyzing(false);
            clearInterval(poll);
          } else if (r?.status === 'failed' || attempts > 30) {
            setIsAnalyzing(false);
            clearInterval(poll);
          }
        } catch {
          if (attempts > 30) {
            setIsAnalyzing(false);
            clearInterval(poll);
          }
        }
      }, 1000);
    } catch {
      setIsAnalyzing(false);
    }
  };

  const handleFeedback = async (nodeId: string, rating: string) => {
    if (!selectedIssue) return;
    try {
      await api.issues.feedback(repoId, selectedIssue.number, nodeId, rating);
      setFeedbackGiven((prev) => ({ ...prev, [nodeId]: rating }));
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }
  };

  const tierColor = (tier: string) => {
    switch (tier) {
      case 'high':
        return 'border-l-green-500';
      case 'medium':
        return 'border-l-amber-500';
      default:
        return 'border-l-red-500';
    }
  };

  return (
    <div className="flex h-full">
      {/* Issues list */}
      <div className="flex w-96 flex-col border-r border-border bg-card">
        <div className="border-b border-border px-4 py-4">
          <h1 className="flex items-center gap-2 text-lg font-bold">
            <GitBranch className="h-5 w-5" />
            Issues
          </h1>
          <p className="text-sm text-muted-foreground">
            Select an issue to see affected code
          </p>
        </div>

        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : issues.length === 0 ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No open issues found
            </div>
          ) : (
            issues.map((issue) => (
              <button
                key={issue.id}
                onClick={() => handleIssueSelect(issue)}
                className={`block w-full border-b border-border px-4 py-3 text-left transition-colors hover:bg-muted ${
                  selectedIssue?.id === issue.id ? 'bg-primary/5 border-l-2 border-l-primary' : ''
                }`}
              >
                <div className="flex items-start gap-2">
                  <span className="mt-0.5 shrink-0 text-xs text-muted-foreground">
                    #{issue.number}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium">{issue.title}</div>
                    {issue.labels.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {issue.labels.map((label) => (
                          <span
                            key={label}
                            className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground"
                          >
                            {label}
                          </span>
                        ))}
                      </div>
                    )}
                    {issue.author && (
                      <div className="mt-1 text-xs text-muted-foreground">
                        by @{issue.author}
                      </div>
                    )}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Mapping detail */}
      <div className="flex-1 overflow-y-auto p-6">
        {!selectedIssue ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <GitBranch className="mb-4 h-12 w-12 text-muted-foreground/50" />
            <h3 className="text-lg font-medium">Select an issue</h3>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              Click on an issue to analyze which files, routes, and components need to be modified.
            </p>
          </div>
        ) : (
          <div className="mx-auto max-w-4xl">
            {/* Issue header */}
            <div className="rounded-xl border border-border bg-card p-6">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-sm text-muted-foreground">Issue #{selectedIssue.number}</span>
                  <h2 className="mt-1 text-xl font-bold">{selectedIssue.title}</h2>
                </div>
                {selectedIssue.url && (
                  <a
                    href={selectedIssue.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-sm text-primary hover:underline"
                  >
                    View on GitHub <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                )}
              </div>
              {selectedIssue.body && (
                <p className="mt-4 whitespace-pre-wrap text-sm text-muted-foreground leading-relaxed">
                  {selectedIssue.body.slice(0, 500)}
                  {selectedIssue.body.length > 500 && '...'}
                </p>
              )}
            </div>

            {/* Analysis */}
            <div className="mt-6">
              <h3 className="mb-3 text-sm font-semibold">Affected Code</h3>

              {isAnalyzing ? (
                <div className="flex items-center gap-3 rounded-lg border border-border bg-card p-6">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  <span className="text-sm text-muted-foreground">
                    Analyzing issue and mapping to code...
                  </span>
                </div>
              ) : mappings.length === 0 ? (
                <div className="rounded-lg border border-border bg-card p-6 text-center text-sm text-muted-foreground">
                  No mappings found for this issue. Try re-analyzing.
                </div>
              ) : (
                <div className="space-y-3">
                  {mappings.map((mapping, i) => (
                    <div
                      key={i}
                      className={`rounded-lg border border-border border-l-4 bg-card p-4 ${tierColor(mapping.confidence_tier)}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="truncate font-medium">{mapping.node.name}</span>
                            <span
                              className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
                                mapping.confidence_tier === 'high'
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                                  : mapping.confidence_tier === 'medium'
                                    ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400'
                                    : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                              }`}
                            >
                              {Math.round(mapping.confidence * 100)}%
                            </span>
                          </div>
                          <div className="mt-1 text-sm text-muted-foreground">{mapping.node.path}</div>

                          {/* Evidence */}
                          <div className="mt-2 flex flex-wrap gap-2">
                            {mapping.evidence.semantic_match && (
                              <span className="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                                semantic match
                              </span>
                            )}
                            {mapping.evidence.structural_match && (
                              <span className="rounded bg-purple-50 px-2 py-0.5 text-xs text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                                structural match
                              </span>
                            )}
                            {mapping.evidence.matched_keywords.slice(0, 5).map((kw) => (
                              <span
                                key={kw}
                                className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                              >
                                {kw}
                              </span>
                            ))}
                          </div>

                          {/* Suggested actions */}
                          {mapping.suggested_actions.length > 0 && (
                            <ul className="mt-3 space-y-1">
                              {mapping.suggested_actions.map((action, j) => (
                                <li key={j} className="flex items-start gap-2 text-sm text-muted-foreground">
                                  <span className="mt-1 text-primary">→</span>
                                  {action}
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>

                        {/* Feedback buttons */}
                        <div className="flex shrink-0 gap-1">
                          <button
                            onClick={() => handleFeedback(mapping.node.id, 'relevant')}
                            className={`rounded-md p-1.5 transition-colors ${
                              feedbackGiven[mapping.node.id] === 'relevant'
                                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                : 'text-muted-foreground hover:bg-muted'
                            }`}
                            title="Relevant"
                          >
                            <ThumbsUp className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleFeedback(mapping.node.id, 'irrelevant')}
                            className={`rounded-md p-1.5 transition-colors ${
                              feedbackGiven[mapping.node.id] === 'irrelevant'
                                ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                                : 'text-muted-foreground hover:bg-muted'
                            }`}
                            title="Not relevant"
                          >
                            <ThumbsDown className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
