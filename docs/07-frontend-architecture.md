# CodeAtlas - Frontend Architecture Specification

## Overview
Next.js 14 (App Router) + React Flow + TypeScript. Server components for initial load, client components for interactive graph.

---

## Project Structure
```
apps/web/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (auth)/             # Auth layout group
│   │   │   ├── login/
│   │   │   └── callback/
│   │   ├── (dashboard)/        # Authenticated layout group
│   │   │   ├── repos/
│   │   │   │   ├── [repoId]/
│   │   │   │   │   ├── graph/
│   │   │   │   │   ├── issues/
│   │   │   │   │   ├── search/
│   │   │   │   │   ├── chat/
│   │   │   │   │   └── settings/
│   │   │   │   └── page.tsx    # Repository list
│   │   │   ├── layout.tsx      # Dashboard layout with sidebar
│   │   │   └── page.tsx        # Dashboard home
│   │   ├── api/                # API routes (proxy, webhooks)
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx            # Landing page
│   ├── components/
│   │   ├── graph/              # React Flow graph components
│   │   │   ├── GraphCanvas.tsx
│   │   │   ├── nodes/
│   │   │   │   ├── BaseNode.tsx
│   │   │   │   ├── FileNode.tsx
│   │   │   │   ├── DirectoryNode.tsx
│   │   │   │   ├── FunctionNode.tsx
│   │   │   │   ├── ClassNode.tsx
│   │   │   │   ├── RouteNode.tsx
│   │   │   │   ├── ComponentNode.tsx
│   │   │   │   ├── ModelNode.tsx
│   │   │   │   └── index.ts
│   │   │   ├── edges/
│   │   │   │   ├── BaseEdge.tsx
│   │   │   │   ├── ImportEdge.tsx
│   │   │   │   ├── CallEdge.tsx
│   │   │   │   └── index.ts
│   │   │   ├── controls/
│   │   │   │   ├── Toolbar.tsx
│   │   │   │   ├── Minimap.tsx
│   │   │   │   ├── ZoomControls.tsx
│   │   │   │   ├── FilterPanel.tsx
│   │   │   │   ├── SearchBar.tsx
│   │   │   │   └── LayoutSelector.tsx
│   │   │   ├── panels/
│   │   │   │   ├── NodeDetailPanel.tsx
│   │   │   │   ├── IssueMappingPanel.tsx
│   │   │   │   ├── SearchResultsPanel.tsx
│   │   │   │   └── ChatPanel.tsx
│   │   │   └── hooks/
│   │   │       ├── useGraph.ts
│   │   │       ├── useNodeSelection.ts
│   │   │       └── useViewport.ts
│   │   ├── ui/                 # shadcn/ui components
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Breadcrumbs.tsx
│   │   └── providers/
│   │       ├── QueryProvider.tsx
│   │       ├── AuthProvider.tsx
│   │       └── WebSocketProvider.tsx
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts       # Axios/Fetch wrapper
│   │   │   ├── endpoints.ts    # API endpoint constants
│   │   │   └── types.ts        # API response types
│   │   ├── auth/
│   │   │   ├── nextauth.ts
│   │   │   └── github.ts
│   │   ├── graph/
│   │   │   ├── layout.ts       # Layout algorithms
│   │   │   ├── clustering.ts   # Graph clustering
│   │   │   ├── virtualization.ts
│   │   │   └── styles.ts       # Node/edge styles
│   │   ├── utils/
│   │   │   ├── format.ts
│   │   │   ├── debounce.ts
│   │   │   └── color.ts
│   │   └── constants.ts
│   ├── stores/
│   │   ├── graphStore.ts       # Zustand: graph state
│   │   ├── uiStore.ts          # Zustand: UI state
│   │   └── repoStore.ts        # Zustand: repo selection
│   ├── hooks/
│   │   ├── useRepos.ts
│   │   ├── useGraph.ts
│   │   ├── useSearch.ts
│   │   ├── useIssueMapping.ts
│   │   ├── useChat.ts
│   │   └── useWebSocket.ts
│   └── types/
│       ├── graph.ts
│       ├── api.ts
│       └── ui.ts
├── public/
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
└── dockerfile
```

---

## Core Components

### GraphCanvas.tsx
Main React Flow container with virtualization for 2000+ nodes.

```typescript
interface GraphCanvasProps {
  nodes: CodeNode[];
  edges: CodeEdge[];
  onNodeClick: (node: CodeNode) => void;
  onEdgeClick: (edge: CodeEdge) => void;
  selectedNodeId?: string;
  highlightedNodeIds: string[];
  viewport: Viewport;
  onViewportChange: (viewport: Viewport) => void;
}
```

**Features**:
- Virtualized rendering (only render visible nodes)
- WebGL renderer option for >1000 nodes
- Custom node/edge types registered via `nodeTypes`/`edgeTypes`
- Event handlers: `onNodeClick`, `onNodeDoubleClick`, `onPaneClick`, `onSelectionChange`
- Keyboard navigation (arrow keys, enter to focus)

### Node Components

#### BaseNode.tsx
Common functionality for all nodes:
- Selection highlight (ring)
- Hover tooltip with name/type/path
- Context menu (right-click)
- Drag handle for repositioning
- Expand/collapse for directories

```typescript
interface BaseNodeProps {
  data: {
    node: CodeNode;
    isSelected: boolean;
    isHighlighted: boolean;
    isCollapsed?: boolean;
  };
}
```

#### Type-Specific Nodes

| Node Type | Visual | Key Props |
|-----------|--------|-----------|
| `directory` | Folder icon, collapsible | `childrenCount`, `isCollapsed` |
| `file` | Document icon, language color | `language`, `loc` |
| `function` | ⚡ icon, async badge | `isAsync`, `params`, `returns` |
| `class` | 📦 icon, extends badge | `extends`, `implements[]` |
| `route` | 🌐 icon, method badge | `method`, `path`, `controller` |
| `component` | ⚛️ icon, props badge | `props[]`, `hooks[]` |
| `model` | 🗄️ icon, table badge | `tableName`, `fields[]` |

**Color Coding by Language**:
- TypeScript: `#3178C6`
- JavaScript: `#F7DF1E`
- Python: `#3776AB`
- Go: `#00ADD8`
- Rust: `#DEA584`
- Java: `#ED8B00`

### Edge Components

#### BaseEdge.tsx
- Animated flow for `calls`/`dataflow` edges
- Label for edge type
- Curved bezier for clarity
- Hover highlight

#### Edge Types Visual Mapping
| Edge Type | Style | Color | Animation |
|-----------|-------|-------|-----------|
| `imports` | Dashed | Gray | No |
| `calls` | Solid | Blue | Flow (→) |
| `extends` | Solid | Purple | No |
| `routes_to` | Bold | Green | Flow (→) |
| `renders` | Dotted | Orange | No |
| `reads`/`writes` | Dashed | Red/Green | Pulse |

---

## State Management (Zustand)

### graphStore.ts
```typescript
interface GraphState {
  // Data
  nodes: Map<string, CodeNode>;
  edges: Map<string, CodeEdge>;
  nodeIndex: Map<string, string[]>; // adjacency list
  
  // UI State
  selectedNodeId: string | null;
  highlightedNodeIds: Set<string>;
  filteredNodeIds: Set<string>;
  viewport: Viewport;
  
  // Loading
  isLoading: boolean;
  loadingStage: 'clone' | 'parse' | 'extract' | 'embed' | 'persist';
  progress: number;
  
  // Actions
  setGraph: (nodes: CodeNode[], edges: CodeEdge[]) => void;
  updateNode: (id: string, data: Partial<CodeNode>) => void;
  addHighlight: (ids: string[]) => void;
  clearHighlight: () => void;
  selectNode: (id: string | null) => void;
  setViewport: (viewport: Viewport) => void;
  setFilter: (filter: GraphFilter) => void;
}
```

### repoStore.ts
```typescript
interface RepoState {
  repos: Repository[];
  currentRepoId: string | null;
  currentRepo: Repository | null;
  
  fetchRepos: () => Promise<void>;
  selectRepo: (id: string) => void;
  triggerIngestion: (mode: 'full' | 'incremental') => Promise<string>;
  getIngestionStatus: (taskId: string) => Promise<IngestionStatus>;
}
```

### uiStore.ts
```typescript
interface UIState {
  sidebarOpen: boolean;
  rightPanel: 'node-detail' | 'issue-mapping' | 'search' | 'chat' | null;
  searchQuery: string;
  searchResults: SearchResult[];
  chatHistory: ChatMessage[];
  theme: 'light' | 'dark' | 'system';
  
  toggleSidebar: () => void;
  openPanel: (panel: UIState['rightPanel']) => void;
  closePanel: () => void;
  setTheme: (theme: UIState['theme']) => void;
}
```

---

## Data Fetching (React Query)

### Query Keys
```typescript
export const queryKeys = {
  repos: () => ['repos'] as const,
  repo: (id: string) => ['repos', id] as const,
  repoStats: (id: string) => ['repos', id, 'stats'] as const,
  graph: (repoId: string, params: GraphParams) => ['graph', repoId, params] as const,
  subgraph: (repoId: string, centerId: string, radius: number) => 
    ['graph', repoId, 'subgraph', centerId, radius] as const,
  node: (repoId: string, nodeId: string) => ['node', repoId, nodeId] as const,
  search: (repoId: string, query: SearchQuery) => ['search', repoId, query] as const,
  issueMapping: (repoId: string, issueNumber: number) => 
    ['issue-mapping', repoId, issueNumber] as const,
  summaries: {
    directory: (repoId: string, path: string) => ['summary', 'dir', repoId, path] as const,
    node: (repoId: string, nodeId: string) => ['summary', 'node', repoId, nodeId] as const,
    architecture: (repoId: string) => ['summary', 'arch', repoId] as const,
  },
  onboarding: (repoId: string) => ['onboarding', repoId] as const,
};
```

### Hooks
```typescript
// useGraph.ts
export function useGraph(repoId: string, params: GraphParams) {
  return useQuery({
    queryKey: queryKeys.graph(repoId, params),
    queryFn: () => api.graph.get(repoId, params),
    staleTime: 5 * 60 * 1000,
    enabled: !!repoId,
  });
}

// useInfiniteGraph for pagination
export function useInfiniteGraph(repoId: string, params: GraphParams) {
  return useInfiniteQuery({
    queryKey: queryKeys.graph(repoId, params),
    queryFn: ({ pageParam }) => api.graph.get(repoId, { ...params, cursor: pageParam }),
    getNextPageParam: (lastPage) => lastPage.pagination.next_cursor,
    staleTime: 5 * 60 * 1000,
  });
}
```

---

## Graph Algorithms

### Layout Algorithms (`lib/graph/layout.ts`)

```typescript
type LayoutAlgorithm = 
  | 'dagre'           // Hierarchical (default for directories)
  | 'force-directed'  // ForceAtlas2 for code graphs
  | 'circular'        // Circular for small subgraphs
  | 'grid'            // Grid for file listings
  | 'preserve';       // Keep manual positions

interface LayoutOptions {
  algorithm: LayoutAlgorithm;
  direction: 'TB' | 'LR' | 'RL' | 'BT';
  nodeSep: number;
  rankSep: number;
  edgeSep: number;
  animate: boolean;
  duration: number;
}

export async function computeLayout(
  nodes: CodeNode[],
  edges: CodeEdge[],
  options: LayoutOptions
): Promise<Map<string, { x: number; y: number }>>;
```

### Clustering (`lib/graph/clustering.ts`)

```typescript
interface ClusterOptions {
  by: 'directory' | 'module' | 'language' | 'type';
  minClusterSize: number;
  maxClusterSize: number;
}

export function clusterGraph(
  nodes: CodeNode[],
  edges: CodeEdge[],
  options: ClusterOptions
): { clusters: Cluster[]; clusteredNodes: CodeNode[]; clusteredEdges: CodeEdge[] };
```

**Cluster Node**: Single node representing multiple nodes, expands on click.

---

## Virtualization (`lib/graph/virtualization.ts`)

For 2000+ nodes, only render viewport-visible elements.

```typescript
interface VirtualizationConfig {
  viewport: Viewport;
  nodePositions: Map<string, { x: number; y: number }>;
  nodeDimensions: Map<string, { width: number; height: number }>;
  padding: number; // Extra pixels around viewport
}

export function getVisibleNodes(
  config: VirtualizationConfig
): Set<string> {
  const { x, y, zoom } = config.viewport;
  const viewportBounds = {
    left: -x / zoom - config.padding,
    right: (-x + window.innerWidth) / zoom + config.padding,
    top: -y / zoom - config.padding,
    bottom: (-y + window.innerHeight) / zoom + config.padding,
  };
  
  // Check each node position against viewport bounds
  // Return Set of visible node IDs
}
```

---

## Real-time Updates (WebSocket)

### Connection Management (`hooks/useWebSocket.ts`)
```typescript
export function useWebSocket(url: string, options: {
  onMessage: (event: MessageEvent) => void;
  onOpen?: () => void;
  onClose?: () => void;
  reconnect?: boolean;
  reconnectInterval?: number;
}) {
  // Auto-reconnect with exponential backoff
  // Heartbeat ping every 30s
  // Message queue for offline support
}
```

### Event Types
```typescript
type WSMessage = 
  | { type: 'ingestion_progress'; payload: IngestionProgress }
  | { type: 'node_updated'; payload: CodeNode }
  | { type: 'edge_added'; payload: CodeEdge }
  | { type: 'edge_removed'; payload: { source: string; target: string; type: string } }
  | { type: 'analysis_complete'; payload: IssueMappingResult }
  | { type: 'error'; payload: { code: string; message: string } };
```

---

## Performance Optimization

### Memoization
- `React.memo` for all node/edge components
- `useMemo` for derived graph data (adjacency lists, filtered nodes)
- `useCallback` for event handlers passed to React Flow

### Code Splitting
```typescript
// Dynamic imports for heavy components
const NodeDetailPanel = dynamic(() => import('@/components/graph/panels/NodeDetailPanel'), {
  loading: () => <Skeleton />,
  ssr: false,
});

const ChatPanel = dynamic(() => import('@/components/graph/panels/ChatPanel'), {
  loading: () => <Skeleton />,
  ssr: false,
});
```

### Bundle Analysis
- Target: < 200KB initial JS (gzipped)
- Graph components lazy-loaded
- React Flow tree-shaken (import only used)

---

## Accessibility (WCAG 2.1 AA)

- Keyboard navigation for all graph interactions
- ARIA labels on all interactive elements
- Focus indicators (visible outline)
- Color contrast ratios > 4.5:1
- Screen reader announcements for graph changes
- Reduced motion support (`prefers-reduced-motion`)

---

## Theming

### CSS Variables (`globals.css`)
```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96.1%;
  --secondary-foreground: 222.2 47.4% 11.2%;
  --muted: 210 40% 96.1%;
  --muted-foreground: 215.4 16.3% 46.9%;
  --accent: 210 40% 96.1%;
  --accent-foreground: 222.2 47.4% 11.2%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 210 40% 98%;
  --border: 214.3 31.8% 91.4%;
  --ring: 221.2 83.2% 53.3%;
  --radius: 0.5rem;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  /* ... */
}
```

---

## Testing Strategy

### Unit Tests (Vitest)
- Node/edge components rendering
- Graph store actions
- Layout algorithms
- Utility functions

### Integration Tests (React Testing Library)
- Graph canvas interactions
- Panel open/close flows
- Search and filter

### E2E Tests (Playwright)
- Full graph load → filter → select node → view details
- Issue mapping flow
- Chat Q&A flow
- Authentication flow

### Visual Regression (Chromatic)
- Node types in light/dark mode
- Graph layouts
- Panel states

---

## Build & Deploy

### Dockerfile
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
```

### Next.js Config
```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    serverActions: true,
  },
  transpilePackages: ['@codeatlas/shared'],
  webpack: (config) => {
    config.externals.push({
      'utf-8-validate': 'commonjs utf-8-validate',
      'bufferutil': 'commonjs bufferutil',
    });
    return config;
  },
};
```