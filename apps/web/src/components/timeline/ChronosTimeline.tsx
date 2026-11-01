'use client';

import { useEffect, useRef } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Database,
  Flame,
  GitCommit,
  History,
  Maximize2,
  Minimize2,
  Pause,
  Play,
  RotateCcw,
  Tag,
  Zap,
} from 'lucide-react';
import { useChronosStore } from '@/stores/chronosStore';
import { useGraphStore } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';
import { ChronosSimulationModal } from './ChronosSimulationModal';
import { ChronosArchaeologyModal } from './ChronosArchaeologyModal';

export function ChronosTimeline({ repoId }: { repoId: string }) {
  const commits = useChronosStore((s) => s.commits);
  const currentCommitIndex = useChronosStore((s) => s.currentCommitIndex);
  const isPlaying = useChronosStore((s) => s.isPlaying);
  const isLoading = useChronosStore((s) => s.isLoading);
  const fetchTimeline = useChronosStore((s) => s.fetchTimeline);
  const scrubToIndex = useChronosStore((s) => s.scrubToIndex);
  const playTimeline = useChronosStore((s) => s.playTimeline);
  const pauseTimeline = useChronosStore((s) => s.pauseTimeline);
  const setSimulationModalOpen = useChronosStore((s) => s.setSimulationModalOpen);
  const fetchArchaeology = useChronosStore((s) => s.fetchArchaeology);

  const timelineOpen = useUIStore((s) => s.timelineOpen);
  const toggleTimeline = useUIStore((s) => s.toggleTimeline);
  const openPanel = useUIStore((s) => s.openPanel);

  const selectedNodeId = useGraphStore((s) => s.selectedNodeId);
  const nodes = useGraphStore((s) => s.nodes);
  const _selectedNode = selectedNodeId ? nodes.get(selectedNodeId) : null;

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetchTimeline(repoId);
  }, [repoId, fetchTimeline]);

  // Handle play/pause animation
  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        const nextIdx = (useChronosStore.getState().currentCommitIndex + 1) % Math.max(1, commits.length);
        scrubToIndex(nextIdx);
        if (nextIdx === commits.length - 1) {
          pauseTimeline();
        }
      }, 1500);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, commits.length, scrubToIndex, pauseTimeline]);

  const activeCommit = commits[currentCommitIndex] || commits[0];

  const handleOpenArchaeology = async () => {
    const targetId = selectedNodeId || 'apps/api/routers/graph.py';
    await fetchArchaeology(repoId, targetId);
    openPanel('chronos-archaeology');
  };

  const getHotspotColor = (score: number) => {
    if (score >= 0.7) return 'text-red-400 bg-red-500/10 border-red-500/30';
    if (score >= 0.4) return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
  };

  if (isLoading && commits.length === 0) {
    return null;
  }

  return (
    <>
      <div className="absolute bottom-3 left-3 right-3 z-30 flex flex-col items-center pointer-events-none">
        <div className="w-full max-w-5xl rounded-2xl border border-border/80 bg-card/95 shadow-2xl backdrop-blur-md pointer-events-auto overflow-hidden transition-all duration-300">
          {/* Header Bar */}
          <div className="flex items-center justify-between border-b border-border/60 px-4 py-2 bg-muted/40 text-xs">
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-semibold text-foreground tracking-wide flex items-center gap-1.5">
                <History className="h-3.5 w-3.5 text-primary" />
                CHRONOS TIME ENGINE
              </span>
              <span className="text-muted-foreground font-mono text-[11px]">
                ({commits.length} historical checkpoints)
              </span>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setSimulationModalOpen(true)}
                className="inline-flex items-center gap-1 rounded-md border border-primary/30 bg-primary/10 px-2.5 py-1 text-[11px] font-medium text-primary hover:bg-primary/20 transition-colors shadow-sm"
                title="Simulate proposed code refactor blast radius"
              >
                <Zap className="h-3 w-3" />
                Simulate Refactor
              </button>

              <button
                onClick={handleOpenArchaeology}
                className="inline-flex items-center gap-1 rounded-md border border-border bg-card px-2.5 py-1 text-[11px] font-medium text-foreground hover:bg-muted transition-colors"
                title="Inspect component creation history & PR rationale"
              >
                <GitCommit className="h-3 w-3 text-primary" />
                Archaeology
              </button>

              <button
                onClick={() => openPanel('omniquery')}
                className="inline-flex items-center gap-1 rounded-md border border-border bg-card px-2.5 py-1 text-[11px] font-medium text-foreground hover:bg-muted transition-colors"
                title="Open OmniQuery Conversational Database Lens"
              >
                <Database className="h-3 w-3 text-cyan-400" />
                OmniQuery
              </button>

              <button
                onClick={toggleTimeline}
                className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                title={timelineOpen ? 'Collapse timeline' : 'Expand timeline'}
              >
                {timelineOpen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
              </button>
            </div>
          </div>

          {/* Expanded Timeline Body */}
          {timelineOpen && (
            <div className="p-3 space-y-2.5">
              {/* Commit info banner */}
              {activeCommit && (
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border/50 bg-muted/20 px-3 py-2 text-xs">
                  <div className="flex items-center gap-2.5 truncate">
                    <span className="rounded bg-primary/15 px-2 py-0.5 font-mono text-[11px] font-bold text-primary">
                      {activeCommit.short_hash}
                    </span>
                    <span className="font-medium text-foreground truncate max-w-md">
                      {activeCommit.message}
                    </span>
                    {activeCommit.tag && (
                      <span className="inline-flex items-center gap-1 rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary">
                        <Tag className="h-2.5 w-2.5" />
                        {activeCommit.tag}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3 shrink-0 text-[11px]">
                    <div className="flex items-center gap-1 font-mono">
                      <span className="text-emerald-400">+{activeCommit.churn_added}</span>
                      <span className="text-muted-foreground">/</span>
                      <span className="text-red-400">-{activeCommit.churn_deleted}</span>
                    </div>

                    <div
                      className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-medium ${getHotspotColor(
                        activeCommit.hotspot_score
                      )}`}
                    >
                      <Flame className="h-2.5 w-2.5" />
                      Hotspot: {Math.round(activeCommit.hotspot_score * 100)}%
                    </div>

                    <span className="text-muted-foreground font-mono">
                      {new Date(activeCommit.date).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              )}

              {/* Scrubber track and controls */}
              <div className="flex items-center gap-3">
                {/* Control buttons */}
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    onClick={() => scrubToIndex(Math.max(0, currentCommitIndex - 1))}
                    disabled={currentCommitIndex === 0}
                    className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-30"
                    title="Previous commit"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>

                  <button
                    onClick={() => (isPlaying ? pauseTimeline() : playTimeline())}
                    className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow hover:bg-primary/90"
                    title={isPlaying ? 'Pause' : 'Play history'}
                  >
                    {isPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5 ml-0.5" />}
                  </button>

                  <button
                    onClick={() => scrubToIndex(Math.min(commits.length - 1, currentCommitIndex + 1))}
                    disabled={currentCommitIndex === commits.length - 1}
                    className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-30"
                    title="Next commit"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>

                  <button
                    onClick={() => scrubToIndex(0)}
                    className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                    title="Reset to HEAD"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                  </button>
                </div>

                {/* Slider bar */}
                <div className="relative flex-1 flex flex-col justify-center">
                  <input
                    type="range"
                    min={0}
                    max={Math.max(0, commits.length - 1)}
                    value={currentCommitIndex}
                    onChange={(e) => scrubToIndex(Number(e.target.value))}
                    className="w-full h-1.5 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                  />

                  {/* Commit checkpoint dots */}
                  <div className="flex justify-between px-1 mt-1.5">
                    {commits.map((c, idx) => (
                      <button
                        key={idx}
                        onClick={() => scrubToIndex(idx)}
                        className={`group relative flex flex-col items-center`}
                        title={`${c.short_hash}: ${c.message}`}
                      >
                        <div
                          className={`h-2 w-2 rounded-full transition-all ${
                            idx === currentCommitIndex
                              ? 'bg-primary ring-2 ring-primary/40 scale-125'
                              : c.architectural_milestone
                              ? 'bg-cyan-400'
                              : 'bg-muted-foreground/40 hover:bg-muted-foreground'
                          }`}
                        />
                        {c.architectural_milestone && (
                          <span className="hidden group-hover:block absolute bottom-4 whitespace-nowrap rounded bg-popover px-1.5 py-0.5 text-[9px] text-popover-foreground shadow border border-border z-40">
                            {c.architectural_milestone}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <ChronosSimulationModal repoId={repoId} />
      <ChronosArchaeologyModal />
    </>
  );
}
