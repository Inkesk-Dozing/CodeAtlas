'use client';

import { useState } from 'react';
import { AlertTriangle, CheckCircle2, GitBranch, ShieldAlert, Users, X, Zap } from 'lucide-react';
import { useChronosStore } from '@/stores/chronosStore';
import { useGraphStore } from '@/stores/graphStore';

export function ChronosSimulationModal({ repoId }: { repoId: string }) {
  const simulationModalOpen = useChronosStore((s) => s.simulationModalOpen);
  const setSimulationModalOpen = useChronosStore((s) => s.setSimulationModalOpen);
  const simulation = useChronosStore((s) => s.simulation);
  const isSimulating = useChronosStore((s) => s.isSimulating);
  const runSimulation = useChronosStore((s) => s.runSimulation);
  const clearSimulation = useChronosStore((s) => s.clearSimulation);

  const selectedNodeId = useGraphStore((s) => s.selectedNodeId);
  const nodes = useGraphStore((s) => s.nodes);
  const selectedNode = selectedNodeId ? nodes.get(selectedNodeId) : null;

  const [proposedChange, setProposedChange] = useState(
    'Refactor function signatures and decouple direct database queries into service layer.'
  );

  if (!simulationModalOpen) return null;

  const handleSimulate = async () => {
    const targetId = selectedNodeId || 'apps/api/routers/graph.py';
    await runSimulation(repoId, targetId, proposedChange);
  };

  const getRiskBadgeColor = (risk: string) => {
    switch (risk) {
      case 'critical':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'high':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'medium':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      default:
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="relative flex max-h-[85vh] w-full max-w-2xl flex-col rounded-xl border border-border bg-card shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-4 bg-muted/30">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/20 text-primary">
              <Zap className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-foreground">Chronos What-If AST Mutation Simulator</h2>
              <p className="text-xs text-muted-foreground">
                Predict downstream blast radius and caller breakage before committing code
              </p>
            </div>
          </div>
          <button
            onClick={() => setSimulationModalOpen(false)}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div>
            <label className="text-xs font-medium text-foreground block mb-1.5">
              Target Component / Node:
            </label>
            <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/40 px-3 py-2 text-xs">
              <GitBranch className="h-3.5 w-3.5 text-primary shrink-0" />
              <span className="font-mono text-foreground font-semibold">
                {selectedNode ? selectedNode.name : 'Target Component'}
              </span>
              <span className="text-muted-foreground font-mono truncate">
                ({selectedNode ? selectedNode.path : 'apps/api/routers/graph.py'})
              </span>
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-foreground block mb-1.5">
              Proposed Refactor or Mutation:
            </label>
            <textarea
              value={proposedChange}
              onChange={(e) => setProposedChange(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              placeholder="Describe what you plan to change, delete, or refactor..."
            />
          </div>

          <div className="flex justify-end gap-2">
            {simulation && (
              <button
                onClick={clearSimulation}
                className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted"
              >
                Clear Results
              </button>
            )}
            <button
              onClick={handleSimulate}
              disabled={isSimulating}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-1.5 text-xs font-medium text-primary-foreground shadow hover:bg-primary/90 disabled:opacity-50"
            >
              <Zap className="h-3.5 w-3.5" />
              {isSimulating ? 'Analyzing Graph...' : 'Simulate Blast Radius'}
            </button>
          </div>

          {/* Results section */}
          {simulation && (
            <div className="space-y-4 rounded-xl border border-border bg-muted/20 p-4 animate-in fade-in duration-200">
              {/* Metric bar */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Calculated Blast Radius:</span>
                  <span className="font-mono text-sm font-bold text-foreground">
                    {simulation.blast_radius_count} nodes affected
                  </span>
                </div>
                <div
                  className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider ${getRiskBadgeColor(
                    simulation.risk_level
                  )}`}
                >
                  <ShieldAlert className="h-3 w-3" />
                  {simulation.risk_level} Risk
                </div>
              </div>

              {/* Downstream Callers */}
              <div>
                <h4 className="text-xs font-semibold text-foreground mb-2 flex items-center gap-1.5">
                  <GitBranch className="h-3.5 w-3.5 text-primary" />
                  Downstream Impacted Callers ({simulation.downstream_nodes.length}):
                </h4>
                <div className="space-y-1.5 max-h-36 overflow-y-auto">
                  {simulation.downstream_nodes.map((dn, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between rounded-lg border border-border/60 bg-card/60 px-3 py-1.5 text-xs"
                    >
                      <div className="flex items-center gap-2 truncate">
                        <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-mono text-primary">
                          depth {dn.depth}
                        </span>
                        <span className="font-semibold text-foreground truncate">{dn.name}</span>
                        <span className="text-muted-foreground font-mono text-[11px] truncate">
                          {dn.path}
                        </span>
                      </div>
                      <span className="text-[10px] text-muted-foreground shrink-0 ml-2">
                        {dn.relation}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Impacted Endpoints */}
              {simulation.impacted_endpoints.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-foreground mb-1.5 flex items-center gap-1.5">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
                    Impacted API Endpoints:
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {simulation.impacted_endpoints.map((ep, idx) => (
                      <span
                        key={idx}
                        className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 font-mono text-[11px] text-amber-300"
                      >
                        {ep}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Reviewers */}
              {simulation.recommended_reviewers.length > 0 && (
                <div className="flex items-center gap-2 text-xs">
                  <Users className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-muted-foreground">Required Reviewers:</span>
                  <div className="flex gap-1.5">
                    {simulation.recommended_reviewers.map((rev, idx) => (
                      <span
                        key={idx}
                        className="rounded bg-muted px-2 py-0.5 font-mono text-[11px] text-foreground font-medium"
                      >
                        {rev}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Remediation suggestions */}
              {simulation.remediation_suggestions.length > 0 && (
                <div className="space-y-1">
                  <span className="text-xs font-semibold text-foreground">
                    Recommended Remediation Plan:
                  </span>
                  <ul className="space-y-1 text-xs text-muted-foreground">
                    {simulation.remediation_suggestions.map((sug, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                        <span>{sug}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-border px-5 py-3 bg-muted/20 text-xs text-muted-foreground">
          <span>Downstream nodes are automatically highlighted in the React Flow canvas.</span>
          <button
            onClick={() => setSimulationModalOpen(false)}
            className="rounded-lg bg-secondary px-3 py-1.5 font-medium text-secondary-foreground hover:bg-secondary/80"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
