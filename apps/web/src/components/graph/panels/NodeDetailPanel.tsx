'use client';

import { useState } from 'react';
import { X, FileCode, Hash, Link2, Sparkles } from 'lucide-react';
import { useGraphStore, type GraphNode, type GraphEdge } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';
import { NODE_TYPE_COLORS, NODE_TYPE_LABELS } from '@codeatlas/shared';

export function NodeDetailPanel() {
  const { selectedNodeId, nodes, edges } = useGraphStore();
  const closePanel = useUIStore((s) => s.closePanel);
  const [activeTab, setActiveTab] = useState<'details' | 'relations' | 'summary'>('details');

  const node = selectedNodeId ? nodes.get(selectedNodeId) : null;

  if (!node) return null;

  const meta = node.metadata || {};
  const color = NODE_TYPE_COLORS[node.type] || '#6B7280';

  const outgoing = edgesArr(edges, node.id, 'outgoing');
  const incoming = edgesArr(edges, node.id, 'incoming');

  return (
    <div className="flex h-full w-full flex-col border-l border-border bg-card">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2 min-w-0">
          <div
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-sm font-bold text-white"
            style={{ backgroundColor: color }}
          >
            {node.type.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold">{node.name}</div>
            <div className="truncate text-xs text-muted-foreground">
              {NODE_TYPE_LABELS[node.type] || node.type}
            </div>
          </div>
        </div>
        <button
          onClick={closePanel}
          className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        {(['details', 'relations', 'summary'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 px-3 py-2 text-xs font-medium capitalize transition-colors ${
              activeTab === tab
                ? 'border-b-2 border-primary text-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'details' && (
          <div className="space-y-4">
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

            {meta.complexity && (
              <div className="rounded-lg border border-border p-3">
                <div className="mb-2 text-xs font-medium text-muted-foreground">Complexity</div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <div className="text-lg font-bold">{meta.complexity.cyclomatic || 0}</div>
                    <div className="text-[10px] text-muted-foreground">Cyclomatic</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold">{meta.complexity.cognitive || 0}</div>
                    <div className="text-[10px] text-muted-foreground">Cognitive</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold">{meta.complexity.maintainability || 0}</div>
                    <div className="text-[10px] text-muted-foreground">Maintainability</div>
                  </div>
                </div>
              </div>
            )}

            {meta.docstring && (
              <div className="rounded-lg border border-border p-3">
                <div className="mb-1 text-xs font-medium text-muted-foreground">Documentation</div>
                <p className="text-sm leading-relaxed">{meta.docstring}</p>
              </div>
            )}

            {meta.exports && meta.exports.length > 0 && (
              <div>
                <div className="mb-1 text-xs font-medium text-muted-foreground">Exports</div>
                <div className="flex flex-wrap gap-1">
                  {meta.exports.slice(0, 20).map((exp) => (
                    <span key={exp} className="rounded bg-muted px-1.5 py-0.5 font-mono text-[11px]">
                      {exp}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {meta.imports && meta.imports.length > 0 && (
              <div>
                <div className="mb-1 text-xs font-medium text-muted-foreground">Imports</div>
                <div className="flex flex-wrap gap-1">
                  {meta.imports.slice(0, 20).map((imp) => (
                    <span key={imp} className="rounded bg-muted px-1.5 py-0.5 font-mono text-[11px]">
                      {imp}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {meta.methods && meta.methods.length > 0 && (
              <div>
                <div className="mb-1 text-xs font-medium text-muted-foreground">Methods ({meta.methods.length})</div>
                <div className="space-y-1">
                  {meta.methods.slice(0, 15).map((m) => (
                    <div key={typeof m === 'string' ? m : m.name} className="rounded bg-muted px-2 py-1 font-mono text-[11px]">
                      {typeof m === 'string' ? m : m.name}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {meta.fields && meta.fields.length > 0 && (
              <div>
                <div className="mb-1 text-xs font-medium text-muted-foreground">Fields ({meta.fields.length})</div>
                <div className="space-y-1">
                  {meta.fields.slice(0, 20).map((f) => {
                    const label = typeof f === 'string' ? f : f.name;
                    const fieldType = typeof f === 'string' ? undefined : f.type;
                    return (
                      <div
                        key={label}
                        className="flex items-center justify-between rounded bg-muted px-2 py-1 font-mono text-[11px]"
                      >
                        <span>{label}</span>
                        {fieldType && <span className="text-muted-foreground">{fieldType}</span>}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'relations' && (
          <div className="space-y-4">
            <RelationSection title="Outgoing (depends on)" items={outgoing} nodes={nodes} />
            <RelationSection title="Incoming (used by)" items={incoming} nodes={nodes} />
          </div>
        )}

        {activeTab === 'summary' && (
          <div className="space-y-4">
            {node.summary ? (
              <div className="rounded-lg border border-border p-3">
                <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                  <Sparkles className="h-3.5 w-3.5" />
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

function RelationSection({
  title,
  items,
  nodes,
}: {
  title: string;
  items: { target_id: string; source_id: string; type: string }[];
  nodes: Map<string, GraphNode>;
}) {
  if (items.length === 0) return null;

  return (
    <div>
      <div className="mb-2 text-xs font-medium text-muted-foreground">
        <Link2 className="mr-1 inline h-3 w-3" />
        {title} ({items.length})
      </div>
      <div className="space-y-1">
        {items.slice(0, 20).map((edge, i) => {
          const otherId = edge.source_id === edge.target_id ? '' : edge.target_id;
          const other = nodes.get(otherId);
          return (
            <div
              key={i}
              className="flex items-center justify-between rounded bg-muted px-2 py-1.5 text-xs"
            >
              <span className="truncate font-medium">{other?.name || 'Unknown'}</span>
              <span className="ml-2 shrink-0 rounded bg-background px-1 text-[10px] text-muted-foreground">
                {edge.type}
              </span>
            </div>
          );
        })}
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
