export type NodeType =
  | 'directory'
  | 'file'
  | 'module'
  | 'class'
  | 'function'
  | 'interface'
  | 'type'
  | 'variable'
  | 'route'
  | 'component'
  | 'hook'
  | 'model'
  | 'service'
  | 'middleware'
  | 'controller'
  | 'utility'
  | 'config'
  | 'migration'
  | 'test';

export type EdgeType =
  | 'contains'
  | 'exports'
  | 'imports'
  | 're_exports'
  | 'extends'
  | 'implements'
  | 'calls'
  | 'instantiates'
  | 'routes_to'
  | 'renders'
  | 'uses_hook'
  | 'has_model'
  | 'middleware_for'
  | 'reads'
  | 'writes'
  | 'emits'
  | 'listens';

export type RepositoryStatus = 'pending' | 'analyzing' | 'ready' | 'error' | 'disabled';

export type IngestionStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

export type IngestionStage = 'clone' | 'parse' | 'extract' | 'embed' | 'persist';

export type IssueIntent = 'BUG' | 'FEATURE' | 'REFACTOR' | 'DOCS' | 'TEST';

export type ConfidenceTier = 'high' | 'medium' | 'low';

export type UserRole = 'admin' | 'member' | 'viewer';

export type OrgPlan = 'free' | 'pro' | 'enterprise';

export interface ComplexityMetrics {
  cyclomatic: number;
  cognitive: number;
  maintainability: number;
}

export interface CodeNode {
  id: string;
  repoId: string;
  type: NodeType;
  name: string;
  path: string;
  language: string | null;
  metadata: CodeNodeMetadata;
  summary: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CodeNodeMetadata {
  loc?: number;
  complexity?: ComplexityMetrics;
  docstring?: string | null;
  exports?: string[];
  imports?: string[];
  signature?: string;
  httpMethod?: string;
  routePath?: string;
  controller?: string;
  middleware?: string[];
  props?: PropDefinition[];
  hooksUsed?: string[];
  renders?: string[];
  tableName?: string;
  fields?: FieldDefinition[];
  relations?: RelationDefinition[];
  extends?: string | null;
  implements?: string[];
  methods?: MethodDefinition[];
  isAbstract?: boolean;
  isAsync?: boolean;
  isService?: boolean;
  params?: ParameterDefinition[];
  returns?: string;
}

export interface PropDefinition {
  name: string;
  type: string;
  required: boolean;
  defaultValue?: string;
}

export interface FieldDefinition {
  name: string;
  type: string;
  nullable: boolean;
  primaryKey: boolean;
  unique: boolean;
}

export interface RelationDefinition {
  type: 'one_to_one' | 'one_to_many' | 'many_to_one' | 'many_to_many';
  target: string;
  foreignKey?: string;
}

export interface MethodDefinition {
  name: string;
  signature: string;
  isStatic: boolean;
  isAsync: boolean;
  visibility: 'public' | 'private' | 'protected';
}

export interface ParameterDefinition {
  name: string;
  type: string;
  defaultValue?: string;
}

export interface CodeEdge {
  id: string;
  repoId: string;
  sourceId: string;
  targetId: string;
  type: EdgeType;
  weight: number;
  metadata: Record<string, unknown>;
  createdAt: string;
}

export interface GraphData {
  nodes: CodeNode[];
  edges: CodeEdge[];
  pagination?: Pagination;
}

export interface Pagination {
  nextCursor: string | null;
  hasMore: boolean;
  total: number;
}

export interface Repository {
  id: string;
  githubId: number;
  installationId: number;
  orgId: string | null;
  name: string;
  fullName: string;
  owner: string;
  defaultBranch: string;
  isPrivate: boolean;
  language: string | null;
  description: string | null;
  cloneUrl: string;
  settings: RepositorySettings;
  status: RepositoryStatus;
  errorMessage: string | null;
  lastAnalyzedAt: string | null;
  lastAnalyzedSha: string | null;
  nodeCount: number;
  edgeCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface RepositorySettings {
  ignoredPaths: string[];
  analysisDepth: 'full' | 'incremental';
  generateDocs: boolean;
  embeddingModel: string;
}

export interface IssueMappingResult {
  issueNumber: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  mappings: CodeMapping[];
  modelVersion: string;
  generatedAt: string | null;
}

export interface CodeMapping {
  node: CodeNode;
  confidence: number;
  confidenceTier: ConfidenceTier;
  evidence: MappingEvidence;
  suggestedActions: string[];
}

export interface MappingEvidence {
  semanticMatch: boolean;
  structuralMatch: boolean;
  historicalMatch: boolean;
  propagationMatch: boolean;
  matchedKeywords: string[];
  matchedPatterns: string[];
}

export interface SearchRequest {
  query: string;
  limit?: number;
  types?: NodeType[];
  threshold?: number;
}

export interface SearchResult {
  node: CodeNode;
  score: number;
  matchType: 'semantic' | 'keyword' | 'structural';
  snippet: string | null;
}

export interface IngestionTask {
  id: string;
  repoId: string;
  mode: 'full' | 'incremental' | 'webhook';
  status: IngestionStatus;
  currentStage: IngestionStage | null;
  progress: number;
  branch: string | null;
  commitSha: string | null;
  filesTotal: number;
  filesProcessed: number;
  nodesCreated: number;
  edgesCreated: number;
  error: string | null;
  startedAt: string | null;
  completedAt: string | null;
  createdAt: string;
}

export interface Issue {
  id: string;
  repoId: string;
  number: number;
  title: string;
  body: string | null;
  state: 'open' | 'closed';
  labels: string[];
  assignees: string[];
  author: string | null;
  url: string;
  closedAt: string | null;
}

export interface ChatMessage {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations: ChatCitation[];
  createdAt: string;
}

export interface ChatCitation {
  nodeId: string;
  path: string;
  snippet: string;
  relevance: number;
}

export interface NodeSummary {
  nodeId: string;
  summaryType: 'directory' | 'module' | 'class' | 'function' | 'architecture';
  content: string;
  generatedAt: string;
}
