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

// -----------------------------------------------------------------------------
// Chronos (Software Time Machine & Archaeology) Types
// -----------------------------------------------------------------------------

export interface ChronosCommit {
  hash: string;
  short_hash: string;
  shortHash?: string;
  author: string;
  author_avatar?: string;
  authorAvatar?: string;
  date: string;
  message: string;
  tag?: string;
  churn_added: number;
  churnAdded?: number;
  churn_deleted: number;
  churnDeleted?: number;
  hotspot_score: number;
  hotspotScore?: number;
  architectural_milestone?: string;
  architecturalMilestone?: string;
}

export interface ChronosDiff {
  from_commit: string;
  fromCommit?: string;
  to_commit: string;
  toCommit?: string;
  added_nodes: string[];
  addedNodes?: string[];
  removed_nodes: string[];
  removedNodes?: string[];
  modified_nodes: string[];
  modifiedNodes?: string[];
  dependency_changes: {
    source: string;
    target: string;
    action: 'added' | 'removed';
  }[];
  dependencyChanges?: {
    source: string;
    target: string;
    action: 'added' | 'removed';
  }[];
  summary: string;
}

export interface ChronosDownstreamNode {
  id: string;
  name: string;
  path: string;
  depth: number;
  relation: string;
}

export interface ChronosSimulation {
  target_node_id: string;
  targetNodeId?: string;
  target_path: string;
  targetPath?: string;
  proposed_change: string;
  proposedChange?: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical' | string;
  riskLevel?: 'low' | 'medium' | 'high' | 'critical' | string;
  blast_radius_count: number;
  blastRadiusCount?: number;
  downstream_nodes: ChronosDownstreamNode[];
  downstreamNodes?: ChronosDownstreamNode[];
  impacted_endpoints: string[];
  impactedEndpoints?: string[];
  recommended_reviewers: string[];
  recommendedReviewers?: string[];
  remediation_suggestions: string[];
  remediationSuggestions?: string[];
}

export interface ChronosArchaeologyRecord {
  node_id: string;
  nodeId?: string;
  node_path: string;
  nodePath?: string;
  created_in_commit: string;
  createdInCommit?: string;
  created_at: string;
  createdAt?: string;
  original_author: string;
  originalAuthor?: string;
  decision_context: string;
  decisionContext?: string;
  linked_prs: { number: number; title: string; url?: string }[];
  linkedPRs?: { number: number; title: string; url?: string }[];
  evolution_summary: string;
  evolutionSummary?: string;
  hotspot_trend: 'stable' | 'accelerating' | 'cooling' | string;
  hotspotTrend?: 'stable' | 'accelerating' | 'cooling' | string;
}

// -----------------------------------------------------------------------------
// OmniQuery (Conversational Database Time Machine) Types
// -----------------------------------------------------------------------------

export interface OmniQuerySchemaField {
  name: string;
  type: string;
  is_primary?: boolean;
  isPrimary?: boolean;
  is_nullable?: boolean;
  isNullable?: boolean;
  foreign_key?: string;
  foreignKey?: string;
}

export interface OmniQuerySchemaModel {
  name: string;
  table_name: string;
  tableName?: string;
  file_path: string;
  filePath?: string;
  fields: OmniQuerySchemaField[];
  connected_endpoints: string[];
  connectedEndpoints?: string[];
}

export interface OmniQueryCodeDependency {
  endpoint: string;
  method: string;
  path: string;
  impact: 'breaking' | 'compatible' | 'none' | string;
}

export interface OmniQueryExplanation {
  intent: string;
  operation_type: 'SELECT' | 'INSERT' | 'UPDATE' | 'DELETE' | 'MIGRATION' | string;
  operationType?: 'SELECT' | 'INSERT' | 'UPDATE' | 'DELETE' | 'MIGRATION' | string;
  translated_sql: string;
  translatedSql?: string;
  explanation: string;
  risk_level: 'safe' | 'medium' | 'destructive' | string;
  riskLevel?: 'safe' | 'medium' | 'destructive' | string;
  estimated_affected_rows: number;
  estimatedAffectedRows?: number;
  safety_check_passed: boolean;
  safetyCheckPassed?: boolean;
  code_dependencies: OmniQueryCodeDependency[];
  codeDependencies?: OmniQueryCodeDependency[];
}

export interface OmniQuerySimulation {
  success: boolean;
  preview_rows: Record<string, unknown>[];
  previewRows?: Record<string, unknown>[];
  rollback_plan: string;
  rollbackPlan?: string;
  execution_time_ms: number;
  executionTimeMs?: number;
  warnings?: string[];
}

export interface OmniQueryExecutionRecord {
  id: string;
  timestamp: string;
  prompt: string;
  sql: string;
  status: 'simulated' | 'executed' | 'rolled_back' | string;
  affected_rows: number;
  affectedRows?: number;
}



// -----------------------------------------------------------------------------
// Active Telemetry (WakaTime-Style Focus & Cognitive Friction) Types
// -----------------------------------------------------------------------------

export interface TelemetryHeartbeat {
  entity: string;
  type?: 'file' | 'domain' | 'url';
  time: number;
  project?: string;
  branch?: string;
  language?: string;
  is_write?: boolean;
  cursorpos?: { line: number; column: number };
}

export interface NodeTelemetryStat {
  node_id: string;
  nodeId?: string;
  file_path: string;
  filePath?: string;
  active_minutes: number;
  activeMinutes?: number;
  loc_churn: number;
  locChurn?: number;
  cognitive_friction_index: number;
  cognitiveFrictionIndex?: number;
  friction_tier: 'low' | 'moderate' | 'high' | 'critical';
  frictionTier?: 'low' | 'moderate' | 'high' | 'critical';
}

export interface TelemetrySummary {
  repo_id: string;
  repoId?: string;
  total_focus_hours: number;
  totalFocusHours?: number;
  hotspots: NodeTelemetryStat[];
}

// -----------------------------------------------------------------------------
// GitReverse & AI Prompt Packager Types
// -----------------------------------------------------------------------------

export interface PromptPackRequest {
  node_id?: string;
  nodeId?: string;
  depth?: number;
  token_budget?: number;
  tokenBudget?: number;
}

export interface PromptPackResponse {
  prompt_token_count: number;
  promptTokenCount?: number;
  system_prompt: string;
  systemPrompt?: string;
  interface_contracts: string;
  interfaceContracts?: string;
  caller_context: string[];
  callerContext?: string[];
}

// -----------------------------------------------------------------------------
// Flight Simulator Types
// -----------------------------------------------------------------------------

export interface FlightMission {
  id: string;
  title: string;
  track: 'beginner' | 'intermediate' | 'advanced';
  difficulty: string;
  reward_badge_tier: string;
  rewardBadgeTier?: string;
  description: string;
  completed?: boolean;
}

export interface VirtualGitCommandRequest {
  command: string;
}

export interface VirtualGitCommandResponse {
  stdout: string;
  stderr?: string;
  current_branch: string;
  currentBranch?: string;
  dag_state: {
    head: string;
    branches: string[];
  };
}

export interface PRReviewComment {
  file: string;
  line: number;
  message: string;
}

export interface PRReviewResponse {
  pr_number: number;
  status: 'passed' | 'changes_requested' | 'failed';
  ci_checks: Record<string, 'pending' | 'passed' | 'failed'>;
  bot_comments: PRReviewComment[];
}

// -----------------------------------------------------------------------------
// Verifiable Badges & Credentials Types
// -----------------------------------------------------------------------------

export type BadgeTier =
  | 'Git Flight Certified'
  | 'Conflict Master'
  | 'Architectural Contributor'
  | 'Core Maintainer'
  | 'Blast Containment Expert';

export interface BadgeCredential {
  cert_id: string;
  certId?: string;
  recipient: string;
  tier: BadgeTier | string;
  repository: string;
  issued_at: number;
  issuedAt?: number;
  signature?: string;
}

export interface BadgeVerificationResult {
  cert_id: string;
  certId?: string;
  recipient: string;
  tier: string;
  repository: string;
  issued_at: number;
  issuedAt?: number;
  signature_valid: boolean;
  signatureValid?: boolean;
  algorithm: string;
  signer_public_key: string;
  signerPublicKey?: string;
  proof_replay_url: string;
  proofReplayUrl?: string;
}

// -----------------------------------------------------------------------------
// GitHub Achievement Tracker & AI Context Types (GitBadgeCheck Compatible)
// -----------------------------------------------------------------------------

export interface AchievementTierProgress {
  tier: string;
  threshold: number;
  multiplier: string;
  unlocked: boolean;
}

export interface UserAchievementItem {
  id: string;
  name: string;
  category: 'active' | 'legacy';
  icon: string;
  description: string;
  unlocked: boolean;
  current_tier?: string;
  currentTier?: string;
  current_multiplier?: string;
  currentMultiplier?: string;
  current_count: number;
  currentCount?: number;
  next_tier?: string;
  nextTier?: string;
  next_threshold?: number;
  nextThreshold?: number;
  remaining_for_next_tier: number;
  remainingForNextTier?: number;
  progress_percentage: number;
  progressPercentage?: number;
  tips: string;
  tiers: AchievementTierProgress[];
}

export interface UserAchievementsSummary {
  username: string;
  total_unlocked: number;
  totalUnlocked?: number;
  total_achievements: number;
  totalAchievements?: number;
  completion_rate: number;
  completionRate?: number;
  active_badges: number;
  activeBadges?: number;
  legacy_badges: number;
  legacyBadges?: number;
  highest_rank_badge: string;
  highestRankBadge?: string;
  estimated_xp: number;
  estimatedXp?: number;
  achievements: UserAchievementItem[];
}

export interface AIAchievementContextResponse {
  prompt_context: string;
  promptContext?: string;
  markdown_card: string;
  markdownCard?: string;
  raw_stats: Record<string, unknown>;
  rawStats?: Record<string, unknown>;
  actionable_next_steps: string[];
  actionableNextSteps?: string[];
}
