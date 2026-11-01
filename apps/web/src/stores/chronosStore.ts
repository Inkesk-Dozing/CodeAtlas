import { create } from 'zustand';
import type {
  ChronosCommit,
  ChronosDiff,
  ChronosSimulation,
  ChronosArchaeologyRecord,
} from '@codeatlas/shared';
import { api } from '@/lib/api/client';
import { useGraphStore } from './graphStore';

interface ChronosState {
  commits: ChronosCommit[];
  currentCommitIndex: number;
  isPlaying: boolean;
  isLoading: boolean;
  activeDiff: ChronosDiff | null;
  simulation: ChronosSimulation | null;
  isSimulating: boolean;
  simulationModalOpen: boolean;
  archaeologyRecord: ChronosArchaeologyRecord | null;
  isArchaeologyLoading: boolean;

  fetchTimeline: (repoId: string) => Promise<void>;
  scrubToIndex: (index: number) => void;
  playTimeline: () => void;
  pauseTimeline: () => void;
  runSimulation: (repoId: string, nodeId: string, change: string) => Promise<void>;
  clearSimulation: () => void;
  setSimulationModalOpen: (open: boolean) => void;
  fetchArchaeology: (repoId: string, nodeId: string) => Promise<void>;
}

export const useChronosStore = create<ChronosState>((set, get) => ({
  commits: [],
  currentCommitIndex: 0,
  isPlaying: false,
  isLoading: false,
  activeDiff: null,
  simulation: null,
  isSimulating: false,
  simulationModalOpen: false,
  archaeologyRecord: null,
  isArchaeologyLoading: false,

  fetchTimeline: async (repoId: string) => {
    set({ isLoading: true });
    try {
      const data = await api.chronos.timeline(repoId, 25);
      set({ commits: data.commits, currentCommitIndex: 0 });
    } catch (err) {
      console.error('Failed to fetch Chronos timeline:', err);
    } finally {
      set({ isLoading: false });
    }
  },

  scrubToIndex: (index: number) => {
    const commits = get().commits;
    if (index >= 0 && index < commits.length) {
      set({ currentCommitIndex: index });
    }
  },

  playTimeline: () => set({ isPlaying: true }),
  pauseTimeline: () => set({ isPlaying: false }),

  runSimulation: async (repoId: string, nodeId: string, change: string) => {
    set({ isSimulating: true });
    try {
      const sim = await api.chronos.simulate(repoId, nodeId, change);
      set({ simulation: sim });

      // Automatically highlight downstream blast radius nodes on the CodeAtlas graph
      const downstreamIds = sim.downstream_nodes.map((n) => n.id);
      useGraphStore.getState().clearHighlight();
      useGraphStore.getState().addHighlight([nodeId, ...downstreamIds]);
    } catch (err) {
      console.error('Failed to run mutation simulation:', err);
    } finally {
      set({ isSimulating: false });
    }
  },

  clearSimulation: () => {
    set({ simulation: null });
    useGraphStore.getState().clearHighlight();
  },

  setSimulationModalOpen: (open: boolean) => set({ simulationModalOpen: open }),

  fetchArchaeology: async (repoId: string, nodeId: string) => {
    set({ isArchaeologyLoading: true, archaeologyRecord: null });
    try {
      const record = await api.chronos.archaeology(repoId, nodeId);
      set({ archaeologyRecord: record });
    } catch (err) {
      console.error('Failed to fetch archaeology record:', err);
    } finally {
      set({ isArchaeologyLoading: false });
    }
  },
}));
