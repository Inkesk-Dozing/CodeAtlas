'use client';

import { useEffect, useState } from 'react';
import {
  Database,
  X,
  Play,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  Table,
  Link2,
  Clock,
  Send,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  Code2,
  Layers,
  Sparkles,
} from 'lucide-react';
import { useOmniQueryStore } from '@/stores/omniQueryStore';
import { useUIStore } from '@/stores/uiStore';
import type { OmniQuerySchemaModel } from '@codeatlas/shared';

interface OmniQueryDrawerProps {
  repoId: string;
}

export function OmniQueryDrawer({ repoId }: OmniQueryDrawerProps) {
  const activePanel = useUIStore((s) => s.activePanel);
  const closePanel = useUIStore((s) => s.closePanel);

  const {
    models,
    selectedModel,
    queryPrompt,
    explanation,
    simulation,
    executionHistory,
    currentStep,
    isLoadingModels,
    isExplaining,
    isSimulating,
    isExecuting,
    error,
    fetchModels,
    selectModel,
    setQueryPrompt,
    explainQuery,
    simulateQuery,
    executeQuery,
    resetPipeline,
  } = useOmniQueryStore();

  const [activeTab, setActiveTab] = useState<'console' | 'schema' | 'history'>('console');

  useEffect(() => {
    if (models.length === 0) {
      fetchModels(repoId);
    }
  }, [repoId, models.length, fetchModels]);

  if (activePanel !== 'omniquery') return null;

  const quickPrompts = [
    'Find all inactive users from last year and set their status to archived',
    'Add an index on tenant_id column to optimize API route queries',
    'Calculate total revenue and subscriber churn grouped by pricing tier',
    "Rename subscription_status to plan_state and backfill all nulls with 'free'",
  ];

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'destructive':
        return (
          <span className="flex items-center gap-1 rounded-full border border-rose-500/30 bg-rose-500/10 px-2 py-0.5 text-[10px] font-semibold text-rose-400">
            <ShieldAlert className="h-3 w-3" />
            Destructive
          </span>
        );
      case 'medium':
        return (
          <span className="flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold text-amber-400">
            <AlertTriangle className="h-3 w-3" />
            Medium Risk
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
            <ShieldCheck className="h-3 w-3" />
            Safe (Read-Only / Sandboxed)
          </span>
        );
    }
  };

  return (
    <div className="flex h-full w-full flex-col border-l border-border bg-card">
      {/* Drawer Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3 bg-muted/20">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-pink-500/20 text-pink-400">
            <Database className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-foreground">OmniQuery Database Time Machine</h2>
              <span className="rounded bg-pink-500/10 px-1.5 py-0.5 text-[10px] font-medium text-pink-400 border border-pink-500/20">
                Data Lens
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Natural-language database queries, dry-run previews, and safe migrations
            </p>
          </div>
        </div>

        <button
          onClick={closePanel}
          className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          title="Close Drawer"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border bg-muted/10 text-xs">
        <button
          onClick={() => setActiveTab('console')}
          className={`flex-1 py-2 text-center font-medium transition-colors ${
            activeTab === 'console'
              ? 'border-b-2 border-primary text-primary bg-background/50'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Conversational Console
        </button>
        <button
          onClick={() => setActiveTab('schema')}
          className={`flex-1 py-2 text-center font-medium transition-colors ${
            activeTab === 'schema'
              ? 'border-b-2 border-primary text-primary bg-background/50'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Schema Models ({models.length})
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`flex-1 py-2 text-center font-medium transition-colors ${
            activeTab === 'history'
              ? 'border-b-2 border-primary text-primary bg-background/50'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Audit History ({executionHistory.length})
        </button>
      </div>

      {/* Tab: Conversational Console */}
      {activeTab === 'console' && (
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Model Scope Selector */}
          <div>
            <label className="block text-[11px] font-medium text-muted-foreground mb-1.5">
              Target Database Model / Table:
            </label>
            <div className="flex flex-wrap gap-1.5">
              {models.map((m) => {
                const isSelected = selectedModel?.name === m.name;
                return (
                  <button
                    key={m.name}
                    onClick={() => selectModel(m)}
                    className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs transition-colors ${
                      isSelected
                        ? 'bg-pink-500/20 text-pink-300 border border-pink-500/40 font-medium'
                        : 'bg-muted/50 text-muted-foreground border border-border/60 hover:bg-muted hover:text-foreground'
                    }`}
                  >
                    <Table className="h-3 w-3" />
                    <span>{m.name}</span>
                    <span className="text-[10px] opacity-60">({m.table_name})</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Workflow Pipeline Stepper */}
          <div className="flex items-center justify-between rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-[10px] font-medium text-muted-foreground">
            <div className={`flex items-center gap-1 ${currentStep === 'ask' ? 'text-primary font-bold' : ''}`}>
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-muted border border-border">1</span>
              <span>Ask</span>
            </div>
            <ArrowRight className="h-3 w-3 opacity-40" />
            <div className={`flex items-center gap-1 ${currentStep === 'preview' ? 'text-primary font-bold' : ''}`}>
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-muted border border-border">2</span>
              <span>Preview</span>
            </div>
            <ArrowRight className="h-3 w-3 opacity-40" />
            <div className={`flex items-center gap-1 ${currentStep === 'approved' ? 'text-primary font-bold' : ''}`}>
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-muted border border-border">3</span>
              <span>Simulate</span>
            </div>
            <ArrowRight className="h-3 w-3 opacity-40" />
            <div className={`flex items-center gap-1 ${currentStep === 'executed' ? 'text-emerald-500 font-bold' : ''}`}>
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-muted border border-border">4</span>
              <span>Execute</span>
            </div>
          </div>

          {/* Prompt Input Box */}
          <div className="space-y-2">
            <div className="relative">
              <textarea
                value={queryPrompt}
                onChange={(e) => setQueryPrompt(e.target.value)}
                placeholder="Ask your database in plain English, e.g. 'Show all active subscriptions expiring this week' or 'Mark test accounts as archived'..."
                rows={3}
                className="w-full rounded-lg border border-border bg-background p-3 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-pink-500"
              />
              <button
                onClick={() => explainQuery(repoId)}
                disabled={!queryPrompt.trim() || isExplaining}
                className="absolute bottom-2.5 right-2.5 flex items-center gap-1.5 rounded-md bg-pink-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-pink-500 disabled:opacity-40 transition-colors shadow-sm"
              >
                {isExplaining ? (
                  <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : (
                  <Send className="h-3.5 w-3.5" />
                )}
                <span>Analyze & Preview</span>
              </button>
            </div>

            {/* Quick Prompts */}
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground">Example prompts:</span>
              <div className="flex flex-col gap-1">
                {quickPrompts.slice(0, 2).map((qp, idx) => (
                  <button
                    key={idx}
                    onClick={() => setQueryPrompt(qp)}
                    className="text-left text-[11px] text-muted-foreground hover:text-pink-400 truncate hover:underline"
                  >
                    • {qp}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Error notice */}
          {error && (
            <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-400">
              {error}
            </div>
          )}

          {/* Step 1: Explanation / Preview */}
          {explanation && (
            <div className="space-y-3 rounded-xl border border-border bg-muted/15 p-4 animate-in fade-in duration-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="rounded bg-muted px-2 py-0.5 font-mono text-[11px] font-bold text-foreground">
                    {explanation.operation_type}
                  </span>
                  {getRiskBadge(explanation.risk_level || 'safe')}
                </div>
                <span className="text-[11px] text-muted-foreground">
                  ~{explanation.estimated_affected_rows} rows affected
                </span>
              </div>

              {/* Natural Language Explanation */}
              <div className="text-xs text-foreground bg-background/60 p-2.5 rounded-md border border-border/60">
                <p className="leading-relaxed">{explanation.explanation}</p>
              </div>

              {/* Translated SQL */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-medium text-muted-foreground flex items-center gap-1">
                    <Code2 className="h-3 w-3" />
                    Translated SQL Statement:
                  </span>
                </div>
                <pre className="rounded-lg border border-border bg-background p-3 font-mono text-xs text-pink-300 overflow-x-auto whitespace-pre-wrap">
                  {explanation.translated_sql}
                </pre>
              </div>

              {/* Cross-Engine Code Dependencies (CodeAtlas Blast Radius) */}
              {explanation.code_dependencies && explanation.code_dependencies.length > 0 && (
                <div className="rounded-lg border border-border/80 bg-background/50 p-3">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground mb-2">
                    <Link2 className="h-3.5 w-3.5 text-primary" />
                    <span>Affected CodeAtlas API Endpoints & Routes</span>
                  </div>
                  <div className="space-y-1.5">
                    {explanation.code_dependencies.map((dep, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between rounded bg-muted/60 px-2.5 py-1.5 text-xs"
                      >
                        <div className="flex items-center gap-2 font-mono">
                          <span className="font-bold text-primary">{dep.method}</span>
                          <span className="text-foreground">{dep.endpoint}</span>
                        </div>
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                            dep.impact === 'breaking'
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : 'bg-emerald-500/20 text-emerald-400'
                          }`}
                        >
                          {dep.impact === 'breaking' ? 'Breaking Change' : 'Compatible'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Simulation Action */}
              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/60">
                <button
                  onClick={resetPipeline}
                  className="rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted hover:text-foreground"
                >
                  Clear
                </button>
                <button
                  onClick={() => simulateQuery(repoId)}
                  disabled={isSimulating}
                  className="flex items-center gap-1.5 rounded-md bg-amber-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-amber-500 disabled:opacity-40 transition-colors shadow-sm"
                >
                  {isSimulating ? (
                    <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  ) : (
                    <Sparkles className="h-3.5 w-3.5" />
                  )}
                  <span>Simulate in Safe Sandbox</span>
                </button>
              </div>
            </div>
          )}

          {/* Step 2: Simulation Results */}
          {simulation && (
            <div className="space-y-3 rounded-xl border border-amber-500/40 bg-amber-500/5 p-4 animate-in fade-in duration-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  <span className="text-xs font-semibold text-foreground">Sandboxed Dry-Run Succeeded</span>
                </div>
                <span className="text-[11px] font-mono text-muted-foreground">
                  {simulation.execution_time_ms} ms
                </span>
              </div>

              {/* Preview Table */}
              {simulation.preview_rows && simulation.preview_rows.length > 0 ? (
                <div className="overflow-x-auto rounded-lg border border-border bg-background">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-border bg-muted/40 font-mono text-[10px] text-muted-foreground">
                      <tr>
                        {Object.keys(simulation.preview_rows[0]).map((key) => (
                          <th key={key} className="px-3 py-1.5 font-semibold">
                            {key}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60 font-mono text-[11px]">
                      {simulation.preview_rows.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-muted/20">
                          {Object.values(row).map((val, cIdx) => (
                            <td key={cIdx} className="px-3 py-1.5 text-foreground whitespace-nowrap">
                              {String(val ?? 'NULL')}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="rounded-lg border border-border bg-background p-3 text-center text-xs text-muted-foreground">
                  Dry-run completed with zero rows affected.
                </div>
              )}

              {/* Rollback Plan Capsule */}
              {simulation.rollback_plan && (
                <div className="rounded-lg border border-border bg-background/60 p-3 text-xs space-y-1">
                  <span className="text-[10px] font-semibold text-muted-foreground flex items-center gap-1">
                    <RotateCcw className="h-3 w-3 text-primary" />
                    Automated Rollback Plan (Zero-Downtime Guarantee):
                  </span>
                  <pre className="font-mono text-[11px] text-emerald-400 whitespace-pre-wrap">
                    {simulation.rollback_plan}
                  </pre>
                </div>
              )}

              {/* Execute / Rollback Button */}
              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/60">
                <button
                  onClick={() => executeQuery(repoId)}
                  disabled={isExecuting || currentStep === 'executed'}
                  className="flex items-center gap-1.5 rounded-md bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-40 transition-colors shadow-sm"
                >
                  {isExecuting ? (
                    <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  ) : (
                    <Play className="h-3.5 w-3.5" />
                  )}
                  <span>
                    {currentStep === 'executed' ? 'Executed Successfully' : 'Approve & Run Transaction'}
                  </span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab: Schema Models */}
      {activeTab === 'schema' && (
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {isLoadingModels ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <p className="text-xs text-muted-foreground">Extracting database models from AST...</p>
            </div>
          ) : (
            models.map((m) => (
              <div
                key={m.name}
                className={`rounded-xl border p-4 space-y-3 transition-colors ${
                  selectedModel?.name === m.name ? 'border-pink-500/50 bg-pink-500/5' : 'border-border bg-muted/10'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
                      <Table className="h-4 w-4 text-pink-400" />
                      {m.name}
                    </h3>
                    <div className="text-[11px] text-muted-foreground font-mono">
                      Table: {m.table_name} · {m.file_path}
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      selectModel(m);
                      setActiveTab('console');
                    }}
                    className="rounded-md border border-border bg-card px-2.5 py-1 text-xs font-medium text-pink-400 hover:bg-pink-500/10"
                  >
                    Query Table
                  </button>
                </div>

                {/* Fields Table */}
                <div className="rounded-lg border border-border bg-background overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-border bg-muted/40 font-mono text-[10px] text-muted-foreground">
                      <tr>
                        <th className="px-3 py-1.5">Field</th>
                        <th className="px-3 py-1.5">Type</th>
                        <th className="px-3 py-1.5">Flags</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60 font-mono text-[11px]">
                      {m.fields.map((f) => (
                        <tr key={f.name} className="hover:bg-muted/20">
                          <td className="px-3 py-1.5 font-medium text-foreground">{f.name}</td>
                          <td className="px-3 py-1.5 text-primary">{f.type}</td>
                          <td className="px-3 py-1.5 space-x-1">
                            {f.is_primary && (
                              <span className="rounded bg-amber-500/20 px-1 py-0.5 text-[9px] text-amber-400">
                                PK
                              </span>
                            )}
                            {!f.is_nullable && (
                              <span className="rounded bg-muted px-1 py-0.5 text-[9px] text-muted-foreground">
                                NOT NULL
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Tab: Audit History */}
      {activeTab === 'history' && (
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {executionHistory.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center text-xs text-muted-foreground">
              <Clock className="h-8 w-8 mb-2 opacity-40" />
              <p>No queries executed in this session yet.</p>
              <p className="mt-1 text-[11px]">
                Simulate and run queries in the console to record transactional snapshots.
              </p>
            </div>
          ) : (
            executionHistory.map((rec) => (
              <div
                key={rec.id}
                className="rounded-xl border border-border bg-muted/20 p-3.5 text-xs space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-foreground">{rec.prompt}</span>
                  <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
                    {rec.affectedRows} rows
                  </span>
                </div>
                <pre className="rounded bg-background p-2 font-mono text-[11px] text-pink-300 overflow-x-auto">
                  {rec.sql}
                </pre>
                <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1">
                  <span>{new Date(rec.timestamp).toLocaleTimeString()}</span>
                  <button
                    onClick={() => {
                      alert(`Emergency Rollback triggered for record ${rec.id}!`);
                    }}
                    className="flex items-center gap-1 text-amber-500 hover:underline"
                  >
                    <RotateCcw className="h-3 w-3" />
                    <span>Rollback Changes</span>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
