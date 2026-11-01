'use client';

import { useEffect, useRef } from 'react';
import {
  Clock,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  Zap,
  Tag,
  ChevronUp,
  ChevronDown,
} from 'lucide-react';
import { useChronosStore } from '@/stores/chronosStore';
import { useUIStore } from '@/stores/uiStore';

interface ChronosTimelineBarProps {
  repoId: string;
}

export function ChronosTimelineBar({ repoId }: ChronosTimelineBarProps) {
  const {
    commits,
    currentCommitIndex,
    isPlaying,
    isLoading,
    fetchTimeline,
    scrubToIndex,
    playTimeline,
    pauseTimeline,
    setSimulationModalOpen,
  } = useChronosStore();

  const timelineOpen = useUIStore((s) => s.timelineOpen);
  const toggleTimeline = useUIStore((s) => s.toggleTimeline);

  const containerRef = useRef<HTMLDivElement>(null);
  const playTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Initial fetch of git timeline
  useEffect(() => {
    if (commits.length === 0) {
      fetchTimeline(repoId);
    }
  }, [repoId, commits.length, fetchTimeline]);

  // Automated timeline playback loop
  useEffect(() => {
    if (isPlaying) {
      playTimerRef.current = setInterval(() => {
        const nextIdx = currentCommitIndex + 1;
        if (nextIdx < commits.length) {
          scrubToIndex(nextIdx);
        } else {
          pauseTimeline();
        }
      }, 2200);
    } else {
      if (playTimerRef.current) {
        clearInterval(playTimerRef.current);
        playTimerRef.current = null;
      }
    }
    return () => {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
    };
  }, [isPlaying, currentCommitIndex, commits.length, scrubToIndex, pauseTimeline]);

  const activeCommit = commits[currentCommitIndex] || null;

  const handleStepBack = () => {
    if (currentCommitIndex < commits.length - 1) {
      scrubToIndex(currentCommitIndex + 1);
    }
  };

  const handleStepForward = () => {
    if (currentCommitIndex > 0) {
      scrubToIndex(currentCommitIndex - 1);
    }
  };

  const handleResetHead = () => {
    scrubToIndex(0);
    pauseTimeline();
  };

  if (!timelineOpen) {
    return (
      <div className="absolute bottom-3 right-4 z-30">
        <button
          onClick={toggleTimeline}
          className="flex items-center gap-2 rounded-full border border-primary/30 bg-card/90 px-3.5 py-2 text-xs font-semibold text-primary shadow-lg backdrop-blur-md transition-all hover:bg-card hover:border-primary"
        >
          <Clock className="h-4 w-4 animate-pulse text-primary" />
          <span>Open Chronos Time Machine</span>
          <ChevronUp className="h-3.5 w-3.5" />
        </button>
      </div>
    );
  }

  return (
    <div className="absolute bottom-3 left-4 right-4 z-30 flex flex-col rounded-xl border border-border/80 bg-card/90 shadow-2xl backdrop-blur-md overflow-hidden transition-all duration-300">
      {/* Top Status & Controls Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 px-4 py-2 bg-muted/20">
        {/* Left: Brand & Active Commit info */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 rounded-md bg-primary/10 px-2 py-1 text-xs font-semibold text-primary">
            <Clock className="h-3.5 w-3.5" />
            <span>Chronos Time Machine</span>
          </div>

          {activeCommit ? (
            <div className="flex items-center gap-2 text-xs">
              <span className="font-mono font-bold text-foreground">
                {activeCommit.shortHash}
              </span>
              <span className="max-w-xs md:max-w-md truncate text-muted-foreground">
                {activeCommit.message}
              </span>
              {activeCommit.architecturalMilestone && (
                <span className="flex items-center gap-1 rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium text-amber-500 border border-amber-500/20">
                  <Tag className="h-2.5 w-2.5" />
                  {activeCommit.architecturalMilestone}
                </span>
              )}
            </div>
          ) : (
            <span className="text-xs text-muted-foreground">
              {isLoading ? 'Loading commit history...' : 'Initial HEAD State'}
            </span>
          )}
        </div>

        {/* Right: Quick Actions */}
        <div className="flex items-center gap-2">
          {/* Refactor Simulator Trigger */}
          <button
            onClick={() => setSimulationModalOpen(true)}
            className="flex items-center gap-1.5 rounded-md border border-primary/30 bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary hover:bg-primary/20 transition-colors"
            title="Simulate proposed AST refactors and blast radius"
          >
            <Zap className="h-3.5 w-3.5 text-primary" />
            <span>Simulate Refactor</span>
          </button>

          {/* Reset to HEAD */}
          {currentCommitIndex !== 0 && (
            <button
              onClick={handleResetHead}
              className="flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              title="Fast-forward to latest HEAD"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Jump to HEAD</span>
            </button>
          )}

          {/* Minimize */}
          <button
            onClick={toggleTimeline}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            title="Minimize Chronos Timeline"
          >
            <ChevronDown className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Main Scrubber Ribbon */}
      <div className="flex items-center gap-3 px-4 py-2.5">
        {/* Playback Controls */}
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={handleStepBack}
            disabled={currentCommitIndex >= commits.length - 1}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-40 transition-colors"
            title="Step Back in Time (Older Commit)"
          >
            <SkipBack className="h-4 w-4" />
          </button>

          <button
            onClick={isPlaying ? pauseTimeline : playTimeline}
            disabled={commits.length === 0}
            className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50 transition-opacity"
            title={isPlaying ? 'Pause Playback' : 'Replay Architectural Evolution'}
          >
            {isPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5 ml-0.5" />}
          </button>

          <button
            onClick={handleStepForward}
            disabled={currentCommitIndex <= 0}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-40 transition-colors"
            title="Step Forward in Time (Newer Commit)"
          >
            <SkipForward className="h-4 w-4" />
          </button>
        </div>

        {/* Visual Commit Node Strip */}
        <div
          ref={containerRef}
          className="flex-1 flex items-center gap-2 overflow-x-auto py-1 scrollbar-none"
        >
          {commits.map((commit, idx) => {
            const isSelected = idx === currentCommitIndex;
            const isHead = idx === 0;

            return (
              <button
                key={commit.hash || idx}
                onClick={() => scrubToIndex(idx)}
                className={`group relative flex flex-col items-center shrink-0 px-2 py-1 rounded-lg text-left transition-all ${
                  isSelected
                    ? 'bg-primary/15 border border-primary/50 shadow-sm'
                    : 'border border-transparent hover:bg-muted/50 hover:border-border/50'
                }`}
              >
                {/* Node Dot / Marker */}
                <div className="flex items-center gap-1.5 mb-1">
                  <div
                    className={`h-2.5 w-2.5 rounded-full transition-transform ${
                      isSelected
                        ? 'bg-primary ring-4 ring-primary/20 scale-125'
                        : isHead
                          ? 'bg-emerald-500'
                          : commit.architecturalMilestone
                            ? 'bg-amber-500'
                            : 'bg-muted-foreground/60 group-hover:bg-foreground'
                    }`}
                  />
                  <span
                    className={`font-mono text-[11px] ${
                      isSelected ? 'font-bold text-primary' : 'text-muted-foreground'
                    }`}
                  >
                    {isHead ? 'HEAD' : commit.shortHash}
                  </span>
                </div>

                {/* Churn indicators */}
                <div className="flex items-center gap-1 text-[9px] font-mono">
                  <span className="text-emerald-500">+{commit.churnAdded}</span>
                  <span className="text-rose-500">-{commit.churnDeleted}</span>
                </div>

                {/* Milestone pill below dot if present */}
                {commit.architecturalMilestone && (
                  <div className="mt-0.5 max-w-[90px] truncate text-[9px] font-medium text-amber-500/90">
                    {commit.architecturalMilestone}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Temporal Stats Capsule */}
        {activeCommit && (
          <div className="hidden lg:flex shrink-0 items-center gap-3 border-l border-border/60 pl-3 text-xs">
            <div>
              <div className="text-[10px] text-muted-foreground">Author</div>
              <div className="font-medium text-foreground">{activeCommit.author}</div>
            </div>
            <div>
              <div className="text-[10px] text-muted-foreground">Hotspot Index</div>
              <div className="font-medium text-amber-500">
                {(((activeCommit.hotspot_score ?? activeCommit.hotspotScore ?? 0) * 100)).toFixed(0)}%
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
