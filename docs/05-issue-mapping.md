# CodeAtlas - Issue-to-Code Mapping Specification

## Overview
Maps GitHub Issues to relevant code nodes using semantic similarity, structural heuristics, and graph propagation. Returns ranked list of files/components with confidence scores.

## Pipeline Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  GitHub      │────▶│  Issue Analyzer  │────▶│  Candidate      │
│  Issue       │     │  (NLP + Heuristics)│   │  Generator      │
└──────────────┘     └──────────────────┘     └────────┬────────┘
                                                        │
                        ┌──────────────────┐            │
                        │  Ranker &        │◀───────────┘
                        │  Confidence      │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Graph           │
                        │  Propagation     │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Final Results   │
                        │  (Top-K + Scores)│
                        └──────────────────┘
```

## Stage 1: Issue Analysis

### Input
```python
class GitHubIssue(BaseModel):
    number: int
    title: str
    body: str | None
    labels: list[str]
    assignees: list[str]
    comments: list[IssueComment]  # First 10 comments
    repository: RepositoryContext  # Language, frameworks, structure
```

### Analysis Output
```python
class IssueAnalysis(BaseModel):
    # Extracted entities
    mentioned_files: list[str]           # "src/auth/middleware.ts"
    mentioned_routes: list[str]          # "/api/users", "GET /users"
    mentioned_models: list[str]          # "User", "Post", "Order"
    mentioned_components: list[str]      # "LoginForm", "UserProfile"
    mentioned_functions: list[str]       # "hashPassword", "validateToken"
    
    # Intent classification
    intent: IssueIntent                  # BUG, FEATURE, REFACTOR, DOCS, TEST
    intent_confidence: float
    
    # Keywords for search
    keywords: list[str]                  # Weighted keywords
    semantic_query: str                  # Full text for embedding
    
    # Context
    urgency: Literal[low, medium, high, critical]
    area_hints: list[str]                # "auth", "payments", "ui"
```

### NLP Pipeline
```python
class IssueAnalyzer:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.code_patterns = CodePatternExtractor()
        self.intent_classifier = IntentClassifier()
    
    async def analyze(self, issue: GitHubIssue) -> IssueAnalysis:
        text = f"{issue.title}\n\n{issue.body or ''}"
        
        # 1. Extract code references via regex + NER
        code_refs = self.code_patterns.extract(text)
        
        # 2. Classify intent
        intent, confidence = self.intent_classifier.predict(text)
        
        # 3. Extract keywords (TF-IDF + domain terms)
        keywords = self._extract_keywords(text, code_refs)
        
        # 4. Build semantic query
        semantic_query = self._build_semantic_query(issue, code_refs, keywords)
        
        return IssueAnalysis(
            mentioned_files=code_refs.files,
            mentioned_routes=code_refs.routes,
            mentioned_models=code_refs.models,
            mentioned_components=code_refs.components,
            mentioned_functions=code_refs.functions,
            intent=intent,
            intent_confidence=confidence,
            keywords=keywords,
            semantic_query=semantic_query,
            urgency=self._assess_urgency(issue),
            area_hints=self._infer_areas(code_refs, keywords)
        )
```

### Code Pattern Extraction
```python
class CodePatternExtractor:
    PATTERNS = {
        "file_path": r"(?:src|lib|app|packages?)/[\w\-/]+\.(ts|tsx|js|jsx|py|go|rs|java|kt)",
        "route": r"(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+/[\w\-\/{}:]*",
        "route_named": r"['\"](/[\w\-\/{}:]*?)['\"]",
        "model": r"(?:model|table|entity|schema)\s+(\w+)",
        "component": r"(?:<|component\s+)([A-Z][a-zA-Z0-9]*)",
        "function": r"(?:function|def|fn|func)\s+(\w+)",
        "class": r"(?:class|interface|type)\s+(\w+)",
        "import": r"(?:import|from)\s+[\w\-\./]+\s+import\s+\{?\s*(\w+)",
        "error": r"(?:error|exception|fail|crash|bug):?\s*([^\n]+)",
    }
    
    def extract(self, text: str) -> CodeReferences:
        refs = CodeReferences()
        for pattern_name, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            getattr(refs, pattern_name + "s").extend(matches)
        return refs
```

---

## Stage 2: Candidate Generation

### Strategy 1: Semantic Search (Vector)
```python
async def semantic_candidates(
    repo_id: UUID, 
    query: str, 
    top_k: int = 50
) -> list[CandidateNode]:
    query_vector = await embedder.encode(query)
    
    # Hybrid: vector + keyword (pgvector + tsvector)
    results = await db.fetch("""
        SELECT 
            n.*,
            1 - (n.embedding <=> $1) AS vector_score,
            ts_rank_cd(n.search_vector, plainto_tsquery('english', $2)) AS keyword_score
        FROM code_nodes n
        WHERE n.repo_id = $3
        ORDER BY 
            (0.7 * (1 - (n.embedding <=> $1))) + 
            (0.3 * ts_rank_cd(n.search_vector, plainto_tsquery('english', $2)))
        DESC
        LIMIT $4
    """, query_vector, query, repo_id, top_k)
    
    return [CandidateNode.from_row(r, source="semantic") for r in results]
```

### Strategy 2: Structural Heuristics
```python
async def structural_candidates(
    repo_id: UUID,
    analysis: IssueAnalysis,
    top_k: int = 30
) -> list[CandidateNode]:
    candidates = []
    
    # Direct file mentions
    for file_path in analysis.mentioned_files:
        nodes = await db.fetch("""
            SELECT * FROM code_nodes 
            WHERE repo_id = $1 AND path ILIKE $2
        """, repo_id, f"%{file_path}%")
        candidates.extend(nodes)
    
    # Route matching
    for route in analysis.mentioned_routes:
        method, path = parse_route(route)
        nodes = await db.fetch("""
            SELECT * FROM code_nodes 
            WHERE repo_id = $1 
            AND type = 'route' 
            AND metadata->>'http_method' = $2
            AND metadata->>'route_path' ILIKE $3
        """, repo_id, method, f"%{path}%")
        candidates.extend(nodes)
    
    # Model matching
    for model in analysis.mentioned_models:
        nodes = await db.fetch("""
            SELECT * FROM code_nodes 
            WHERE repo_id = $1 
            AND type = 'model' 
            AND name ILIKE $2
        """, repo_id, f"%{model}%")
        candidates.extend(nodes)
    
    # Component matching
    for comp in analysis.mentioned_components:
        nodes = await db.fetch("""
            SELECT * FROM code_nodes 
            WHERE repo_id = $1 
            AND type = 'component' 
            AND name ILIKE $2
        """, repo_id, f"%{comp}%")
        candidates.extend(nodes)
    
    # Area-based (directory matching)
    for area in analysis.area_hints:
        nodes = await db.fetch("""
            SELECT * FROM code_nodes 
            WHERE repo_id = $1 
            AND path ILIKE $2
            AND type IN ('file', 'directory', 'module')
        """, repo_id, f"%{area}%")
        candidates.extend(nodes)
    
    return deduplicate(candidates)[:top_k]
```

### Strategy 3: Historical Patterns (Learning)
```python
async def historical_candidates(
    repo_id: UUID,
    analysis: IssueAnalysis,
    top_k: int = 20
) -> list[CandidateNode]:
    # Find similar past issues and their validated mappings
    similar_issues = await db.fetch("""
        SELECT im.affected_nodes, im.confidence_scores
        FROM issue_mappings im
        JOIN issues i ON im.issue_id = i.id
        WHERE i.repo_id = $1 
        AND im.validated = true
        AND 1 - (i.embedding <=> $2) > 0.75
        ORDER BY 1 - (i.embedding <=> $2) DESC
        LIMIT 10
    """, repo_id, analysis.semantic_query_vector)
    
    # Aggregate node frequencies
    node_scores = defaultdict(float)
    for issue in similar_issues:
        for node_id, score in zip(issue.affected_nodes, issue.confidence_scores):
            node_scores[node_id] += score
    
    # Fetch top nodes
    top_node_ids = sorted(node_scores, key=node_scores.get, reverse=True)[:top_k]
    nodes = await db.fetch("""
        SELECT * FROM code_nodes WHERE id = ANY($1)
    """, top_node_ids)
    
    return [CandidateNode.from_row(n, source="historical", prior_score=node_scores[n.id]) 
            for n in nodes]
```

---

## Stage 3: Ranking & Confidence

### Feature Vector per Candidate
```python
@dataclass
class RankingFeatures:
    # Semantic
    vector_similarity: float        # 0-1
    keyword_overlap: float          # 0-1
    
    # Structural
    direct_file_match: bool         # Exact path mentioned
    direct_route_match: bool        # Exact route mentioned
    direct_model_match: bool        # Exact model mentioned
    direct_component_match: bool    # Exact component mentioned
    
    # Graph-based
    centrality_score: float         # PageRank in repo graph
    neighbor_relevance: float       # Avg score of 1-hop neighbors
    dependency_depth: int           # Distance from entry points
    
    # Code quality
    complexity_score: float         # Normalized (0-1, lower=better)
    test_coverage: float | None     # If available
    recency: float                  # Days since last change (0-1)
    
    # Historical
    prior_mapping_score: float      # From historical patterns
    
    # Intent alignment
    intent_match: float             # Bug→test, Feature→route/model, etc.
```

### Scoring Function
```python
def compute_confidence(features: RankingFeatures) -> float:
    # Base weights (tuned via validation set)
    weights = {
        "vector_similarity": 0.25,
        "keyword_overlap": 0.10,
        "direct_file_match": 0.30,
        "direct_route_match": 0.20,
        "direct_model_match": 0.15,
        "direct_component_match": 0.15,
        "centrality_score": 0.05,
        "neighbor_relevance": 0.10,
        "prior_mapping_score": 0.10,
        "intent_match": 0.05,
        # Negative weights
        "complexity_score": -0.05,
        "recency": -0.02,
    }
    
    score = sum(
        getattr(features, k) * w 
        for k, w in weights.items()
    )
    
    # Sigmoid normalization
    return 1 / (1 + math.exp(-score * 5))
```

### Graph Propagation
```python
def propagate_scores(
    candidates: list[CandidateNode], 
    graph: CodeGraph,
    hops: int = 2,
    decay: float = 0.5
) -> list[CandidateNode]:
    """Propagate confidence to neighbors in dependency graph"""
    scores = {c.node_id: c.confidence for c in candidates}
    
    for hop in range(hops):
        new_scores = scores.copy()
        for node_id, score in scores.items():
            if score < 0.3:  # Don't propagate weak signals
                continue
            for neighbor_id in graph.neighbors(node_id):
                edge_weight = graph.edge_weight(node_id, neighbor_id)
                propagated = score * decay * edge_weight
                if propagated > new_scores.get(neighbor_id, 0):
                    new_scores[neighbor_id] = propagated
        scores = new_scores
    
    # Update candidates with propagated scores
    for c in candidates:
        c.confidence = max(c.confidence, scores.get(c.node_id, 0))
    
    # Add newly discovered high-confidence neighbors
    for node_id, score in scores.items():
        if score > 0.4 and node_id not in {c.node_id for c in candidates}:
            node = graph.get_node(node_id)
            candidates.append(CandidateNode(node, score, source="propagation"))
    
    return sorted(candidates, key=lambda c: c.confidence, reverse=True)
```

---

## Stage 4: Final Results

### Output Format
```python
class IssueMappingResult(BaseModel):
    issue_number: int
    mappings: list[CodeMapping]
    generated_at: datetime
    model_version: str
    
class CodeMapping(BaseModel):
    node: CodeNode
    confidence: float                    # 0-1
    confidence_tier: Literal[high, medium, low]
    evidence: MappingEvidence
    suggested_actions: list[str]         # "Modify this route handler", "Update this model"
    
class MappingEvidence(BaseModel):
    semantic_match: bool
    structural_match: bool
    historical_match: bool
    propagation_match: bool
    matched_keywords: list[str]
    matched_patterns: list[str]
```

### Confidence Tiers
| Tier | Threshold | Meaning |
|------|-----------|---------|
| High | ≥ 0.8 | Direct match + semantic confirmation |
| Medium | 0.5 - 0.8 | Strong signal from multiple sources |
| Low | 0.3 - 0.5 | Weak signal, needs verification |

### API Response
```json
{
  "issue_number": 1234,
  "mappings": [
    {
      "node": {
        "id": "uuid",
        "type": "route",
        "name": "POST /api/auth/login",
        "path": "src/routes/auth.ts",
        "language": "typescript"
      },
      "confidence": 0.92,
      "confidence_tier": "high",
      "evidence": {
        "semantic_match": true,
        "structural_match": true,
        "historical_match": false,
        "propagation_match": true,
        "matched_keywords": ["auth", "login", "token", "jwt"],
        "matched_patterns": ["route: POST /api/auth/login"]
      },
      "suggested_actions": [
        "Modify login route handler in src/routes/auth.ts",
        "Update JWT token generation in src/services/auth.ts",
        "Add rate limiting middleware"
      ]
    }
  ],
  "generated_at": "2026-10-05T10:30:00Z",
  "model_version": "v1.2.0"
}
```

---

## Feedback Loop

### User Feedback Collection
```python
class MappingFeedback(BaseModel):
    issue_number: int
    node_id: UUID
    rating: Literal[relevant, partially_relevant, irrelevant]
    comment: str | None
    user_id: UUID
```

### Retraining Signal
```python
async def collect_training_data():
    """Generate training pairs for ranker fine-tuning"""
    feedback = await db.fetch("""
        SELECT im.*, mf.rating
        FROM issue_mappings im
        JOIN mapping_feedback mf ON im.id = mf.mapping_id
        WHERE mf.created_at > NOW() - INTERVAL '30 days'
    """)
    
    # Positive: rating=relevant, confidence > 0.5
    # Negative: rating=irrelevant, confidence > 0.3
    # Hard negative: rating=irrelevant, confidence > 0.7
    return prepare_ranker_dataset(feedback)
```

---

## Evaluation Metrics

### Offline Evaluation
| Metric | Target | Measurement |
|--------|--------|-------------|
| Precision@1 | > 0.70 | First result is relevant |
| Precision@5 | > 0.50 | Top 5 contains relevant |
| Recall@10 | > 0.80 | Relevant files in top 10 |
| MRR | > 0.65 | Mean Reciprocal Rank |
| NDCG@10 | > 0.75 | Normalized Discounted Cumulative Gain |

### Online Evaluation
| Metric | Target | Measurement |
|--------|--------|-------------|
| Click-through rate | > 40% | User clicks mapped file |
| Time to first fix | -50% | vs baseline |
| Feedback positive rate | > 75% | Thumbs up / (up + down) |
| Mapping regeneration rate | < 10% | User requests re-analysis |

---

## Testing

### Golden Set
Curated set of 100 issues across 10 repos with manually verified mappings.

### Test Cases
```python
TEST_CASES = [
    # Bug: Null pointer in user service
    {
        "title": "Fix NPE in UserService.getProfile",
        "body": "NullPointerException when user not found",
        "expected": ["src/services/user.ts", "src/models/user.ts"]
    },
    # Feature: Add password reset
    {
        "title": "Add password reset flow",
        "body": "Need forgot password page, reset token, email template",
        "expected": ["src/routes/auth.ts", "src/components/ForgotPassword.tsx", "src/services/email.ts"]
    },
    # Refactor: Extract payment logic
    {
        "title": "Refactor payment processing",
        "body": "Move Stripe logic to separate service",
        "expected": ["src/services/payment.ts", "src/routes/checkout.ts"]
    },
]
```

### Regression Testing
- Run golden set on every PR
- Alert if Precision@5 drops > 5%
- Automated bisect to find regression commit