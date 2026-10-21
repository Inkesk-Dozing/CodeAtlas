'use client';

import { useCallback } from 'react';
import {
  Search,
  Filter,
  RefreshCw,
  GitBranch,
  MessageSquare,
  AlertCircle,
} from 'lucide-react';
import { useGraphStore } from '@/stores/graphStore';
import { useUIStore } from '@/stores/uiStore';
import { NODE_TYPE_LABELS } from '@codeatlas/shared';

interface GraphToolbarProps {
  repoId: string;
  repoName?: string;
  refreshing?: boolean;
  onRefresh?: () => void;
}

export function GraphToolbar({ repoName, refreshing = false, onRefresh }: GraphToolbarProps) {
  const { filterTypes, toggleFilterType, clearFilters, searchQuery, setSearchQuery, rawNodes, isLoading } =
    useGraphStore();
  const activePanel = useUIStore((s) => s.activePanel);
  const openPanel = useUIStore((s) => s.openPanel);
  const closePanel = useUIStore((s) => s.closePanel);

  const availableTypes = Array.from(
    new Set(rawNodes.map((n) => n.type)),
  ).sort();

  const handlePanelToggle = useCallback(
    (panel: 'search' | 'issue-mapping' | 'chat') => {
      if (activePanel === panel) {
        closePanel();
      } else {
        openPanel(panel);
      }
    },
    [activePanel, openPanel, closePanel],
  );

  return (
    <div className="flex items-center gap-2 border-b border-border bg-card px-4 py-2">
      {repoName && (
        <div className="hidden shrink-0 items-center gap-1.5 text-sm font-medium md:flex">
          <GitBranch className="h-4 w-4 text-muted-foreground" />
          <span className="max-w-48 truncate">{repoName}</span>
        </div>
      )}

      {/* Search */}
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Filter nodes..."
          className="w-full rounded-md border border-border bg-background py-1.5 pl-8 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </div>

      {/* Filter dropdown */}
      <div className="relative group">
        <button className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-muted">
          <Filter className="h-4 w-4" />
          <span className="hidden sm:inline">Filter</span>
          {filterTypes.size > 0 && (
            <span className="rounded-full bg-primary px-1.5 text-[10px] font-medium text-primary-foreground">
              {filterTypes.size}
            </span>
          )}
        </button>

        <div className="invisible absolute left-0 top-full z-50 mt-1 w-56 rounded-lg border border-border bg-card p-2 opacity-0 shadow-lg transition-all group-hover:visible group-hover:opacity-100">
          <div className="mb-1 px-2 py-1 text-xs font-medium text-muted-foreground">
            Node Types
          </div>
          {availableTypes.map((type) => (
            <label
              key={type}
              className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-muted"
            >
              <input
                type="checkbox"
                checked={filterTypes.has(type)}
                onChange={() => toggleFilterType(type)}
                className="h-3.5 w-3.5 rounded border-border"
              />
              <span>{NODE_TYPE_LABELS[type] || type}</span>
            </label>
          ))}
          {filterTypes.size > 0 && (
            <button
              onClick={clearFilters}
              className="mt-1 w-full rounded px-2 py-1.5 text-left text-xs text-muted-foreground hover:bg-muted"
            >
              Clear all filters
            </button>
          )}
        </div>
      </div>

      <div className="flex-1" />

      {/* Panel toggles */}
      <button
        onClick={() => handlePanelToggle('search')}
        className={`flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm transition-colors ${
          activePanel === 'search'
            ? 'border-primary bg-primary/10 text-primary'
            : 'border-border hover:bg-muted'
        }`}
        title="Semantic Search"
      >
        <MessageSquare className="h-4 w-4" />
        <span className="hidden sm:inline">Search</span>
      </button>

      <button
        onClick={() => handlePanelToggle('issue-mapping')}
        className={`flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm transition-colors ${
          activePanel === 'issue-mapping'
            ? 'border-primary bg-primary/10 text-primary'
            : 'border-border hover:bg-muted'
        }`}
        title="Issue Mapping"
      >
        <AlertCircle className="h-4 w-4" />
        <span className="hidden sm:inline">Issues</span>
      </button>

      {/* Refresh */}
      <button
        onClick={onRefresh}
        disabled={isLoading || refreshing}
        className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-muted disabled:opacity-50"
        title="Re-analyze repository"
      >
        <RefreshCw className={`h-4 w-4 ${isLoading || refreshing ? 'animate-spin' : ''}`} />
        <span className="hidden sm:inline">{refreshing ? 'Analyzing…' : 'Refresh'}</span>
      </button>
    </div>
  );
}
