'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  X,
  FileCode,
  Hash,
  Sparkles,
  Zap,
  Database,
  Copy,
  Check,
  ExternalLink,
  Activity,
  ArrowRight,
  Code2,
} from 'lucide-react';
import { useGraphStore, type GraphNode, type GraphEdge } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';
import { useChronosStore } from '@/stores/chronosStore';
import { useOmniQueryStore } from '@/stores/omniQueryStore';
import { NODE_TYPE_COLORS, NODE_TYPE_LABELS } from '@codeatlas/shared';
import { api } from '@/lib/api/client';
import { CodeSnippetPreview } from './CodeSnippetPreview';

export interface NodeDetailPanelProps {
  repoId?: string;
  selectedNode?: GraphNode | null;
  onNavigateNode?: (nodeId: string) => void;
}

export function NodeDetailPanel({ repoId: propRepoId, selectedNode: propSelectedNode, onNavigateNode }: NodeDetailPanelProps) {
  const storeSelectedNodeId = useGraphStore((s) => s.selectedNodeId);
  const storeNodes = useGraphStore((s) => s.nodes);
  const storeEdges = useGraphStore((s) => s.edges);
  const selectNode = useGraphStore((s) => s.selectNode);
  const closePanel = useUIStore((s) => s.closePanel);

  // Support propSelectedNode or fallback to store state
  const selectedNodeId = propSelectedNode ? propSelectedNode.id : storeSelectedNodeId ?? useGraphStore.getState().selectedNodeId;
  const nodes = storeNodes.size > 0 ? storeNodes : useGraphStore.getState().nodes;
  const edges = storeEdges.size > 0 ? storeEdges : useGraphStore.getState().edges;

  const [activeTab, setActiveTab] = useState<'details' | 'callers' | 'dependencies' | 'summary'>('details');

  const [copied, setCopied] = useState(false);
  const [codeSource, setCodeSource] = useState<string | null>(null);
  const [loadingCode, setLoadingCode] = useState(false);
  const [codeError, setCodeError] = useState<string | null>(null);

  const node = propSelectedNode || (selectedNodeId ? nodes.get(selectedNodeId) : null);

  // Determine repository ID from prop, node, or window path
  const effectiveRepoId = useMemo(() => {
    if (propRepoId) return propRepoId;
    if ((node as unknown as { repo_id?: string })?.repo_id) {
      return (node as unknown as { repo_id: string }).repo_id;
    }
    if (typeof window !== 'undefined') {
      const match = window.location.pathname.match(/\/repos\/([^/]+)/);
      if (match) return match[1];
    }
    return '';
  }, [propRepoId, node]);

  // Fetch node code source preview via GET /repos/{repo_id}/nodes/{node_id}
  useEffect(() => {
    if (!node || !effectiveRepoId) return;

    let cancelled = false;
    setLoadingCode(true);
    setCodeError(null);

    api.graph
      .node(effectiveRepoId, node.id)
      .then((data: unknown) => {
        if (cancelled) return;
        const res = data as { code_preview?: string | null };
        if (res?.code_preview) {
          setCodeSource(res.code_preview);
        } else {
          // If code_preview not cached in DB meta, generate snippet from metadata or docstring
          const meta = node.metadata || {};
          if (meta.signature) {
            setCodeSource(`${meta.signature}\n  """\n  ${meta.docstring || 'No documentation provided.'}\n  """`);
          } else if (meta.docstring) {
            setCodeSource(`"""\n${meta.docstring}\n"""`);
          } else {
            setCodeSource(`// Source preview for ${node.name} (${node.path})\nexport ${node.type} ${node.name};`);
          }
        }
      })
      .catch((err) => {
        if (cancelled) return;
        setCodeError(err instanceof Error ? err.message : 'Failed to fetch source');
        // Fallback preview
        const meta = node.metadata || {};
        setCodeSource(meta.signature || `// File: ${node.path}\n${node.type} ${node.name}`);
      })
      .finally(() => {
        if (!cancelled) setLoadingCode(false);
      });

    return () => {
      cancelled = true;
    };
  }, [node, effectiveRepoId]);

  const meta = node?.metadata || {};
  const color = node ? NODE_TYPE_COLORS[node.type] || '#6B7280' : '#6B7280';

  const outgoing = node ? edgesArr(edges, node.id, 'outgoing') : [];
  const incoming = node ? edgesArr(edges, node.id, 'incoming') : [];

  // Cyclomatic complexity score with risk indicator (Low / Moderate / High)
  const complexityScore = meta.complexity?.cyclomatic ?? 1;
  const complexityRisk = useMemo(() => {
    if (complexityScore > 10) {
      return {
        level: 'High',
        color: 'text-rose-400 bg-rose-500/15 border-rose-500/30',
        badge: 'bg-rose-500',
      };
    }
    if (complexityScore > 5) {
      return {
        level: 'Moderate',
        color: 'text-amber-400 bg-amber-500/15 border-amber-500/30',
        badge: 'bg-amber-500',
      };
    }
    return {
      level: 'Low',
      color: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30',
      badge: 'bg-emerald-500',
    };
  }, [complexityScore]);

  // Line range calculation
  const startLine = meta.line || 1;
  const endLine = meta.loc ? startLine + meta.loc - 1 : meta.line ? meta.line + 20 : undefined;
  const lineRangeText = endLine ? `lines ${startLine}-${endLine}` : `line ${startLine}`;

  const handleCopyPath = useCallback(() => {
    if (node && navigator?.clipboard) {
      navigator.clipboard.writeText(node.path);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [node]);

  const handleNavigate = useCallback(
    (targetId: string) => {
      selectNode(targetId);
      onNavigateNode?.(targetId);
    },
    [selectNode, onNavigateNode],
  );

  if (!node) return null;

  return (
    <div
      className="flex h-full w-full flex-col border-l border-border bg-card shadow-2xl transition-all"
      data-testid="node-detail-panel"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3 bg-muted/20">
        <div className="flex items-center gap-2.5 min-w-0">
          <div
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-sm font-bold text-white shadow-sm"
            style={{ backgroundColor: color }}
          >
            {node.type.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold">{node.name}</div>
            <div className="truncate text-xs text-muted-foreground">
              {NODE_TYPE_LABELS[node.type] || node.type} · {lineRangeText}
            </div>
          </div>
        </div>
        <button
          onClick={closePanel}
          className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          aria-label="Close drawer"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Action Bar: Copy path & Open in GitHub */}
      <div className="flex items-center gap-2 border-b border-border px-4 py-2 bg-muted/10 text-xs">
        <button
          onClick={handleCopyPath}
          className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors font-medium"
          title="Copy qualified file path"
          data-testid="node-copy-path-btn"
        >
          {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
          <span>{copied ? 'Copied' : 'Copy Path'}</span>
        </button>

        <a
          href={`https://github.com/Inkesk-Dozing/CodeAtlas/blob/main/${node.path}#L${startLine}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors font-medium"
          title="Open in GitHub repository"
          data-testid="node-github-btn"
        >
          <ExternalLink className="h-3.5 w-3.5" />
          <span>Open in GitHub</span>
        </a>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border bg-card">
        <button
          onClick={() => setActiveTab('details')}
          className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
            activeTab === 'details'
              ? 'border-b-2 border-primary text-primary font-semibold'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          data-testid="tab-details"
        >
          Details
        </button>
        <button
          onClick={() => setActiveTab('callers')}
          className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
            activeTab === 'callers'
              ? 'border-b-2 border-primary text-primary font-semibold'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          data-testid="tab-callers"
        >
          Callers ({incoming.length})
        </button>
        <button
          onClick={() => setActiveTab('dependencies')}
          className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
            activeTab === 'dependencies'
              ? 'border-b-2 border-primary text-primary font-semibold'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          data-testid="tab-dependencies"
        >
          Dependencies ({outgoing.length})
        </button>
        <button
          onClick={() => setActiveTab('summary')}
          className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
            activeTab === 'summary'
              ? 'border-b-2 border-primary text-primary font-semibold'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          data-testid="tab-summary"
        >
          Summary
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'details' && (
          <div className="space-y-4">
            {/* Quick Engine Actions */}
            <div className="flex flex-col gap-2 pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    useChronosStore.getState().setSimulationModalOpen(true);
                  }}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-primary/30 bg-primary/10 px-2.5 py-1.5 text-xs font-semibold text-primary hover:bg-primary/20 transition-colors flex-1 justify-center"
                >
                  <Zap className="h-3.5 w-3.5" />
                  Simulate Refactor
                </button>

                <button
                  onClick={() => {
                    if (effectiveRepoId) {
                      useChronosStore.getState().fetchArchaeology(effectiveRepoId, node.id);
                    }
                    useUIStore.getState().openPanel('chronos-archaeology');
                  }}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 px-2.5 py-1.5 text-xs font-semibold text-amber-400 hover:bg-amber-500/20 transition-colors flex-1 justify-center"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  Archaeology
                </button>
              </div>

              {(node.type === 'model' || node.path.includes('model') || node.path.includes('schema')) && (
                <button
                  onClick={() => {
                    useOmniQueryStore.getState().selectModelByName(node.name);
                    useUIStore.getState().openPanel('omniquery');
                  }}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-pink-500/30 bg-pink-500/10 px-2.5 py-1.5 text-xs font-semibold text-pink-400 hover:bg-pink-500/20 transition-colors w-full justify-center"
                >
                  <Database className="h-3.5 w-3.5" />
                  Open in OmniQuery Database Lens
                </button>
              )}
            </div>

            {/* Cyclomatic Complexity Risk Meter */}
            <div
              className={`rounded-xl border p-3 ${complexityRisk.color}`}
              data-testid="node-complexity-box"
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-1.5 font-semibold text-xs">
                  <Activity className="h-4 w-4" />
                  <span>Cyclomatic Complexity</span>
                </div>
                <span className="font-mono text-sm font-bold">{complexityScore}</span>
              </div>
              <div className="flex items-center justify-between text-xs font-medium">
                <span>Risk Tier:</span>
                <span className="font-bold uppercase tracking-wider">{complexityRisk.level} Risk</span>
              </div>
            </div>

            {/* Syntax-Highlighted Code Snippet Preview */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  <Code2 className="h-3.5 w-3.5" />
                  <span>Source Code Preview ({lineRangeText})</span>
                </div>
                {loadingCode && (
                  <span className="text-[10px] text-muted-foreground animate-pulse">Loading…</span>
                )}
              </div>

              {codeSource ? (
                <CodeSnippetPreview
                  code={codeSource}
                  language={node.language}
                  startLine={startLine}
                />
              ) : (
                <div className="rounded-lg border border-border/80 bg-zinc-950/80 p-4 text-xs font-mono text-muted-foreground text-center">
                  {codeError || 'No source preview available.'}
                </div>
              )}
            </div>

            <InfoRow icon={<FileCode className="h-4 w-4" />} label="Path" value={node.path} mono />
            {node.language && (
              <InfoRow icon={<Hash className="h-4 w-4" />} label="Language" value={node.language} />
            )}

            {meta.loc && <InfoRow label="Lines of Code" value={String(meta.loc)} />}
            {meta.signature && (
              <InfoRow label="Signature" value={meta.signature} mono />
            )}
            {meta.http_method && (
              <InfoRow
                label="Route"
                value={`${meta.http_method} ${meta.route_path || ''}`}
                mono
              />
            )}
            {meta.controller && <InfoRow label="Controller" value={meta.controller} />}
            {meta.framework && <InfoRow label="Framework" value={meta.framework} />}
          </div>
        )}

        {activeTab === 'callers' && (
          <div className="space-y-3" data-testid="tab-callers-content">
            <div className="text-xs font-medium text-muted-foreground">
              Incoming Callers & References ({incoming.length})
            </div>
            {incoming.length === 0 ? (
              <div className="rounded-lg border border-dashed border-border p-6 text-center text-xs text-muted-foreground">
                No incoming callers detected for this node.
              </div>
            ) : (
              <div className="space-y-1.5">
                {incoming.map((edge, i) => {
                  const callerNode = nodes.get(edge.source_id);
                  return (
                    <button
                      key={i}
                      onClick={() => handleNavigate(edge.source_id)}
                      className="flex w-full items-center justify-between rounded-lg border border-border bg-card/60 p-2.5 text-left text-xs hover:border-primary/60 hover:bg-muted/40 transition-colors"
                      data-testid={`caller-node-${edge.source_id}`}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="truncate font-semibold text-foreground">
                          {callerNode?.name || edge.source_id}
                        </div>
                        <div className="truncate font-mono text-[10px] text-muted-foreground">
                          {callerNode?.path || 'External'}
                        </div>
                      </div>
                      <div className="ml-2 flex items-center gap-1">
                        <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">
                          {edge.type}
                        </span>
                        <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {activeTab === 'dependencies' && (
          <div className="space-y-3" data-testid="tab-dependencies-content">
            <div className="text-xs font-medium text-muted-foreground">
              Outgoing Dependencies ({outgoing.length})
            </div>
            {outgoing.length === 0 ? (
              <div className="rounded-lg border border-dashed border-border p-6 text-center text-xs text-muted-foreground">
                No outgoing dependencies detected for this node.
              </div>
            ) : (
              <div className="space-y-1.5">
                {outgoing.map((edge, i) => {
                  const depNode = nodes.get(edge.target_id);
                  return (
                    <button
                      key={i}
                      onClick={() => handleNavigate(edge.target_id)}
                      className="flex w-full items-center justify-between rounded-lg border border-border bg-card/60 p-2.5 text-left text-xs hover:border-primary/60 hover:bg-muted/40 transition-colors"
                      data-testid={`dependency-node-${edge.target_id}`}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="truncate font-semibold text-foreground">
                          {depNode?.name || edge.target_id}
                        </div>
                        <div className="truncate font-mono text-[10px] text-muted-foreground">
                          {depNode?.path || 'External'}
                        </div>
                      </div>
                      <div className="ml-2 flex items-center gap-1">
                        <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">
                          {edge.type}
                        </span>
                        <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {activeTab === 'summary' && (
          <div className="space-y-4" data-testid="tab-summary-content">
            {node.summary ? (
              <div className="rounded-lg border border-border p-3">
                <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                  <Sparkles className="h-3.5 w-3.5 text-amber-400" />
                  AI Summary
                </div>
                <p className="text-sm leading-relaxed">{node.summary}</p>
              </div>
            ) : (
              <div className="py-8 text-center text-sm text-muted-foreground">
                <Sparkles className="mx-auto mb-2 h-8 w-8 opacity-50" />
                <p>No summary available yet.</p>
                <p className="mt-1 text-xs">Run analysis to generate AI summaries.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function InfoRow({
  icon,
  label,
  value,
  mono,
}: {
  icon?: React.ReactNode;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start gap-2">
      {icon && <span className="mt-0.5 text-muted-foreground">{icon}</span>}
      <div className="min-w-0 flex-1">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className={`text-sm break-all ${mono ? 'font-mono' : ''}`}>{value}</div>
      </div>
    </div>
  );
}

function edgesArr(edges: Map<string, GraphEdge>, nodeId: string, direction: 'incoming' | 'outgoing') {
  const result: GraphEdge[] = [];
  edges.forEach((edge) => {
    if (direction === 'outgoing' && edge.source_id === nodeId) result.push(edge);
    if (direction === 'incoming' && edge.target_id === nodeId) result.push(edge);
  });
  return result;
}
