import { create } from 'zustand';
import type {
  OmniQuerySchemaModel,
  OmniQueryExplanation,
  OmniQuerySimulation,
  OmniQueryExecutionRecord,
} from '@codeatlas/shared';
import { api } from '@/lib/api/client';

export type OmniQueryStep = 'ask' | 'understand' | 'preview' | 'simulate' | 'approved' | 'executed' | 'rolled_back';

interface OmniQueryState {
  models: OmniQuerySchemaModel[];
  selectedModel: OmniQuerySchemaModel | null;
  queryPrompt: string;
  explanation: OmniQueryExplanation | null;
  simulation: OmniQuerySimulation | null;
  executionHistory: OmniQueryExecutionRecord[];
  currentStep: OmniQueryStep;
  isLoadingModels: boolean;
  isExplaining: boolean;
  isSimulating: boolean;
  isExecuting: boolean;
  error: string | null;

  fetchModels: (repoId: string) => Promise<void>;
  selectModel: (model: OmniQuerySchemaModel | null) => void;
  selectModelByName: (name: string) => void;
  setQueryPrompt: (prompt: string) => void;
  explainQuery: (repoId: string) => Promise<void>;
  simulateQuery: (repoId: string) => Promise<void>;
  executeQuery: (repoId: string) => Promise<void>;
  resetPipeline: () => void;
}

export const useOmniQueryStore = create<OmniQueryState>((set, get) => ({
  models: [],
  selectedModel: null,
  queryPrompt: '',
  explanation: null,
  simulation: null,
  executionHistory: [],
  currentStep: 'ask',
  isLoadingModels: false,
  isExplaining: false,
  isSimulating: false,
  isExecuting: false,
  error: null,

  fetchModels: async (repoId: string) => {
    set({ isLoadingModels: true });
    try {
      const res = await api.omniquery.models(repoId);
      set({
        models: res.models,
        selectedModel: get().selectedModel ?? (res.models[0] || null),
      });
    } catch (err) {
      console.error('Failed to fetch OmniQuery models:', err);
    } finally {
      set({ isLoadingModels: false });
    }
  },

  selectModel: (model) => set({ selectedModel: model }),

  selectModelByName: (name) => {
    const found = get().models.find(
      (m) =>
        m.name.toLowerCase() === name.toLowerCase() ||
        m.table_name.toLowerCase() === name.toLowerCase()
    );
    if (found) set({ selectedModel: found });
  },

  setQueryPrompt: (prompt) => set({ queryPrompt: prompt, error: null }),

  explainQuery: async (repoId: string) => {
    const { queryPrompt, selectedModel } = get();
    if (!queryPrompt.trim()) return;

    set({ isExplaining: true, error: null, currentStep: 'understand' });
    try {
      const exp = await api.omniquery.explain(repoId, queryPrompt, selectedModel?.name);
      set({ explanation: exp, currentStep: 'preview' });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to analyze query';
      set({ error: msg, currentStep: 'ask' });
    } finally {
      set({ isExplaining: false });
    }
  },

  simulateQuery: async (repoId: string) => {
    const { explanation, selectedModel } = get();
    if (!explanation) return;

    set({ isSimulating: true, error: null, currentStep: 'simulate' });
    try {
      const sim = await api.omniquery.simulate(repoId, explanation.translated_sql, selectedModel?.name);
      set({ simulation: sim, currentStep: 'approved' });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Simulation failed';
      set({ error: msg, currentStep: 'preview' });
    } finally {
      set({ isSimulating: false });
    }
  },

  executeQuery: async (repoId: string) => {
    const { explanation, simulation, selectedModel, executionHistory } = get();
    if (!explanation) return;

    set({ isExecuting: true, error: null });
    try {
      const res = await api.omniquery.execute(
        repoId,
        explanation.translated_sql,
        selectedModel?.name,
        simulation?.rollback_plan
      );
      set({
        currentStep: 'executed',
        executionHistory: [
          {
            id: res.id,
            timestamp: res.timestamp,
            prompt: explanation.intent,
            sql: explanation.translated_sql,
            status: 'executed',
            affected_rows: res.affected_rows,
            affectedRows: res.affected_rows,
          },
          ...executionHistory,
        ],
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Execution failed';
      set({ error: msg });
    } finally {
      set({ isExecuting: false });
    }
  },

  resetPipeline: () =>
    set({
      queryPrompt: '',
      explanation: null,
      simulation: null,
      currentStep: 'ask',
      error: null,
    }),
}));
