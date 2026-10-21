const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

let accessToken: string | null = null;

export interface Citation {
  path: string;
  snippet: string;
}

export interface CodeMapping {
  node: { id: string; type: string; name: string; path: string };
  confidence: number;
  confidence_tier: string;
  evidence: {
    semantic_match: boolean;
    structural_match: boolean;
    historical_match?: boolean;
    propagation_match?: boolean;
    matched_keywords: string[];
    matched_patterns?: string[];
  };
  suggested_actions: string[];
}

export interface IssueMappingStatus {
  issue_number: number;
  status: string;
  mappings: CodeMapping[];
  model_version: string;
  generated_at: string | null;
}

export function setAccessToken(token: string | null) {
  accessToken = token;
  if (token) {
    localStorage.setItem('access_token', token);
  } else {
    localStorage.removeItem('access_token');
  }
}

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return accessToken;
  if (!accessToken) {
    accessToken = localStorage.getItem('access_token');
  }
  return accessToken;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = getAccessToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/api/v1${path}`, {
    method: options.method || 'GET',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
  });

  if (res.status === 401) {
    setAccessToken(null);
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const error = await res.json().catch(() => null);
    const message =
      error?.error?.message || error?.detail || `API error: ${res.status}`;
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Auth
  auth: {
    callback: (code: string) =>
      request<{ access_token: string; refresh_token: string }>('/auth/callback', {
        method: 'POST',
        body: { code },
      }),
    me: () => request<unknown>('/auth/me'),
    refresh: (refreshToken: string) =>
      request<{ access_token: string; refresh_token: string }>('/auth/refresh', {
        method: 'POST',
        body: { refresh_token: refreshToken },
      }),
  },

  // Repositories
  repos: {
    list: (params?: { status?: string; limit?: number }) => {
      const qs = params ? `?${new URLSearchParams(params as Record<string, string>)}` : '';
      return request<unknown[]>(`/repos${qs}`);
    },
    get: (id: string) => request<unknown>(`/repos/${id}`),
    create: (data: unknown) => request<unknown>('/repos', { method: 'POST', body: data }),
    update: (id: string, data: unknown) =>
      request<unknown>(`/repos/${id}`, { method: 'PATCH', body: data }),
    delete: (id: string) => request<void>(`/repos/${id}`, { method: 'DELETE' }),
    stats: (id: string) => request<unknown>(`/repos/${id}/stats`),
  },

  // Graph
  graph: {
    get: (repoId: string, params?: { limit?: number; cursor?: string; types?: string; languages?: string }) => {
      const qs = params ? `?${new URLSearchParams(params as Record<string, string>)}` : '';
      return request<{ nodes: unknown[]; edges: unknown[]; next_cursor: string | null; has_more: boolean; total: number }>(
        `/repos/${repoId}/graph${qs}`,
      );
    },
    subgraph: (repoId: string, params: { center_node_id: string; radius?: number; max_nodes?: number }) =>
      request<{ nodes: unknown[]; edges: unknown[]; total: number }>(`/repos/${repoId}/graph/subgraph`, {
        method: 'POST',
        body: params,
      }),
    node: (repoId: string, nodeId: string) => request<unknown>(`/repos/${repoId}/nodes/${nodeId}`),
    neighbors: (repoId: string, nodeId: string, params?: { direction?: string; limit?: number }) => {
      const qs = params ? `?${new URLSearchParams(params as Record<string, string>)}` : '';
      return request<{ nodes: unknown[]; edges: unknown[] }>(
        `/repos/${repoId}/nodes/${nodeId}/neighbors${qs}`,
      );
    },
  },

  // Search
  search: {
    semantic: (repoId: string, query: string, limit = 10) =>
      request<{ results: unknown[]; took_ms: number }>(`/repos/${repoId}/search/semantic`, {
        method: 'POST',
        body: { query, limit },
      }),
    structural: (repoId: string, query: string, limit = 10) =>
      request<{ results: unknown[]; took_ms: number }>(`/repos/${repoId}/search/structural`, {
        method: 'POST',
        body: { query, limit },
      }),
    hybrid: (repoId: string, query: string, limit = 10) =>
      request<{ results: unknown[]; took_ms: number }>(`/repos/${repoId}/search/hybrid`, {
        method: 'POST',
        body: { query, limit },
      }),
  },

  // Issues
  issues: {
    list: (repoId: string, state = 'open', limit = 30) =>
      request<unknown[]>(`/repos/${repoId}/issues?state=${state}&limit=${limit}`),
    analyze: (repoId: string, issueNumber: number) =>
      request<{ task_id: string; status: string }>(`/repos/${repoId}/issues/${issueNumber}/analyze`, {
        method: 'POST',
        body: {},
      }),
    mapping: (repoId: string, issueNumber: number) =>
      request<IssueMappingStatus | null>(`/repos/${repoId}/issues/${issueNumber}/mapping`),
    feedback: (repoId: string, issueNumber: number, nodeId: string, rating: string) =>
      request<{ status: string }>(`/repos/${repoId}/issues/${issueNumber}/feedback`, {
        method: 'POST',
        body: { node_id: nodeId, rating },
      }),
  },

  // Ingestion
  ingestion: {
    trigger: (repoId: string, mode: 'full' | 'incremental' = 'full') =>
      request<{ id: string; status: string }>(`/repos/${repoId}/ingest/trigger`, {
        method: 'POST',
        body: { mode },
      }),
    status: (repoId: string, taskId?: string) =>
      request<unknown>(`/repos/${repoId}/ingest/status${taskId ? `?task_id=${taskId}` : ''}`),
  },

  // Summaries
  summaries: {
    repo: (repoId: string, regenerate = false) =>
      request<unknown>(`/repos/${repoId}/summary?regenerate=${regenerate}`),
    node: (repoId: string, nodeId: string, regenerate = false) =>
      request<unknown>(`/repos/${repoId}/nodes/${nodeId}/summary?regenerate=${regenerate}`),
    architecture: (repoId: string, format: 'markdown' | 'mermaid' = 'markdown') =>
      request<unknown>(`/repos/${repoId}/architecture?format=${format}`),
  },

  // Chat
  chat: {
    ask: (repoId: string, question: string, sessionId?: string, history?: unknown[]) =>
      request<{ answer: string; citations: Citation[]; session_id: string }>(`/repos/${repoId}/chat`, {
        method: 'POST',
        body: { question, session_id: sessionId, history: history || [] },
      }),
    sessions: (repoId: string) =>
      request<{ id: string; title: string | null; created_at: string }[]>(
        `/repos/${repoId}/chat/sessions`,
      ),
    session: (repoId: string, sessionId: string) =>
      request<{ id: string; role: string; content: string; citations: Citation[] }[]>(
        `/repos/${repoId}/chat/sessions/${sessionId}`,
      ),
    deleteSession: (repoId: string, sessionId: string) =>
      request<void>(`/repos/${repoId}/chat/sessions/${sessionId}`, { method: 'DELETE' }),
  },
};
