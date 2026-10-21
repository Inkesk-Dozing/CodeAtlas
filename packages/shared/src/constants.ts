export const NODE_TYPE_LABELS: Record<string, string> = {
  directory: 'Directory',
  file: 'File',
  module: 'Module',
  class: 'Class',
  function: 'Function',
  interface: 'Interface',
  type: 'Type',
  variable: 'Variable',
  route: 'Route',
  component: 'Component',
  hook: 'Hook',
  model: 'Model',
  service: 'Service',
  middleware: 'Middleware',
  controller: 'Controller',
  utility: 'Utility',
  config: 'Config',
  migration: 'Migration',
  test: 'Test',
};

export const EDGE_TYPE_LABELS: Record<string, string> = {
  contains: 'Contains',
  exports: 'Exports',
  imports: 'Imports',
  re_exports: 'Re-exports',
  extends: 'Extends',
  implements: 'Implements',
  calls: 'Calls',
  instantiates: 'Instantiates',
  routes_to: 'Routes to',
  renders: 'Renders',
  uses_hook: 'Uses hook',
  has_model: 'Has model',
  middleware_for: 'Middleware for',
  reads: 'Reads',
  writes: 'Writes',
  emits: 'Emits',
  listens: 'Listens',
};

export const LANGUAGE_COLORS: Record<string, string> = {
  typescript: '#3178C6',
  javascript: '#F7DF1E',
  python: '#3776AB',
  go: '#00ADD8',
  rust: '#DEA584',
  java: '#ED8B00',
  csharp: '#178600',
  ruby: '#CC342D',
  php: '#777BB4',
  swift: '#F05138',
  kotlin: '#7F52FF',
  unknown: '#6B7280',
};

export const NODE_TYPE_COLORS: Record<string, string> = {
  directory: '#8B5CF6',
  file: '#6B7280',
  module: '#F59E0B',
  class: '#3B82F6',
  function: '#10B981',
  interface: '#8B5CF6',
  type: '#8B5CF6',
  variable: '#6B7280',
  route: '#EF4444',
  component: '#06B6D4',
  hook: '#F97316',
  model: '#EC4899',
  service: '#10B981',
  middleware: '#F59E0B',
  controller: '#EF4444',
  utility: '#6B7280',
  config: '#9CA3AF',
  migration: '#F59E0B',
  test: '#84CC16',
};

export const CONFIDENCE_TIER_COLORS: Record<string, string> = {
  high: '#10B981',
  medium: '#F59E0B',
  low: '#EF4444',
};

export const CONFIDENCE_THRESHOLDS = {
  high: 0.8,
  medium: 0.5,
  low: 0.3,
} as const;

export const API_ROUTES = {
  repos: '/api/v1/repos',
  repo: (id: string) => `/api/v1/repos/${id}`,
  repoGraph: (id: string) => `/api/v1/repos/${id}/graph`,
  repoSubgraph: (id: string) => `/api/v1/repos/${id}/graph/subgraph`,
  repoNode: (repoId: string, nodeId: string) => `/api/v1/repos/${repoId}/nodes/${nodeId}`,
  repoNodeNeighbors: (repoId: string, nodeId: string) =>
    `/api/v1/repos/${repoId}/nodes/${nodeId}/neighbors`,
  repoStats: (id: string) => `/api/v1/repos/${id}/stats`,
  searchSemantic: (id: string) => `/api/v1/repos/${id}/search/semantic`,
  searchStructural: (id: string) => `/api/v1/repos/${id}/search/structural`,
  searchHybrid: (id: string) => `/api/v1/repos/${id}/search/hybrid`,
  issueMapping: (repoId: string, issueNumber: number) =>
    `/api/v1/repos/${repoId}/issues/${issueNumber}/mapping`,
  issueAnalyze: (repoId: string, issueNumber: number) =>
    `/api/v1/repos/${repoId}/issues/${issueNumber}/analyze`,
  issueFeedback: (repoId: string, issueNumber: number) =>
    `/api/v1/repos/${repoId}/issues/${issueNumber}/feedback`,
  ingestTrigger: (id: string) => `/api/v1/repos/${id}/ingest/trigger`,
  ingestStatus: (id: string) => `/api/v1/repos/${id}/ingest/status`,
  directorySummary: (id: string) => `/api/v1/repos/${id}/summaries/directory`,
  nodeSummary: (repoId: string, nodeId: string) =>
    `/api/v1/repos/${repoId}/summaries/node/${nodeId}`,
  architecture: (id: string) => `/api/v1/repos/${id}/architecture`,
  chat: (id: string) => `/api/v1/repos/${id}/chat`,
  onboarding: (id: string) => `/api/v1/repos/${id}/onboarding`,
  webhooks: '/api/v1/webhooks/github',
} as const;

export const RATE_LIMITS = {
  default: { limit: 1000, window: 60 },
  graph: { limit: 100, window: 60 },
  search: { limit: 60, window: 60 },
  ingestion: { limit: 10, window: 3600 },
} as const;
