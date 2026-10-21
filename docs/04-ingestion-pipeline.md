# CodeAtlas - Ingestion Pipeline Specification

## Overview
The ingestion pipeline clones a repository, parses source code into an AST, extracts semantic relationships, generates embeddings, and persists a queryable graph to PostgreSQL+pgvector.

## Pipeline Stages

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Clone     │──▶│   Parse     │──▶│  Extract    │──▶│  Embed      │──▶│  Persist    │
│   (Shallow) │   │  (Tree-sitter)│  │  (Graph)    │   │  (Batch)    │   │  (Upsert)   │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
      │               │               │               │               │
      ▼               ▼               ▼               ▼               ▼
  - Sparse       - Multi-lang    - Nodes:        - 384-dim      - Upsert
  - Shallow      - Incremental     files, dirs,    vectors        - HNSW
  - Token auth   - Cache ASTs      classes, funcs,               index
  - Progress     - Error tolerant  routes, comps               - Transaction
                                            - Edges:
                                              imports, calls
```

## Stage 1: Clone

### Strategy
- **Shallow clone**: `git clone --depth=1 --branch=<default> --filter=blob:none`
- **Sparse checkout**: For monorepos, only checkout relevant packages (`packages/*`, `apps/*`)
- **Authentication**: GitHub App installation token (short-lived, 1hr)
- **Storage**: Clone to S3/MinIO temporary path, cleanup after parsing

### Configuration
```yaml
# repo-settings.yaml
clone:
  depth: 1
  sparse_paths:
    - "packages/**"
    - "apps/**"
    - "libs/**"
    - "*.json"
    - "*.yaml"
    - "*.toml"
    - "*.lock"
  ignore_patterns:
    - "node_modules/**"
    - ".git/**"
    - "dist/**"
    - "build/**"
    - ".next/**"
    - "*.log"
    - "coverage/**"
```

### Progress Tracking
```python
class CloneProgress(BaseModel):
    stage: Literal["cloning", "checking_out", "complete", "failed"]
    bytes_downloaded: int
    total_bytes: int | None
    files_checked_out: int
    error: str | None
```

---

## Stage 2: Parse (Tree-sitter)

### Language Support Matrix
| Language | Grammar | Queries | Extractors |
|----------|---------|---------|------------|
| TypeScript | tree-sitter-typescript | imports, exports, classes, functions, interfaces, types, decorators | ✅ |
| JavaScript | tree-sitter-javascript | Same as TS | ✅ |
| Python | tree-sitter-python | imports, classes, functions, decorators, async | ✅ |
| Go | tree-sitter-go | imports, structs, interfaces, functions, methods | ✅ |
| Rust | tree-sitter-rust | use, structs, enums, traits, fns, macros | ✅ |
| Java | tree-sitter-java | imports, classes, interfaces, methods, annotations | 🔄 |
| C# | tree-sitter-c-sharp | using, classes, interfaces, methods, attributes | 🔄 |

### Parser Architecture
```python
class CodeParser:
    def __init__(self):
        self.parsers: dict[str, Parser] = {}
        self.queries: dict[str, Query] = {}
        self._load_grammars()
    
    def parse_file(self, path: Path, content: bytes) -> ParseResult:
        lang = self._detect_language(path)
        tree = self.parsers[lang].parse(content)
        captures = self.queries[lang].captures(tree.root_node)
        return self._build_result(path, tree, captures)
```

### Incremental Parsing
- Cache parsed trees by file hash (SHA256)
- On push: diff changed files → re-parse only modified
- Reuse unchanged subtrees via Tree-sitter's `edit()` API

### Query Patterns (TypeScript Example)
```scm
; Imports
(import_statement) @import
(import_clause (identifier) @imported_name)
(named_imports (import_specifier (identifier) @imported_name))

; Exports
(export_statement) @export
(export_clause (export_specifier (identifier) @exported_name))

; Classes
(class_declaration name: (type_identifier) @class.name) @class.def

; Functions
(function_declaration name: (identifier) @func.name) @func.def
(arrow_function) @arrow_fn
(method_definition name: (property_identifier) @method.name) @method.def

; Decorators (NestJS, Angular)
(decorator (call_expression (identifier) @decorator.name)) @decorator

; React Components
(jsx_element (jsx_opening_element (jsx_identifier) @component.name)) @component
```

---

## Stage 3: Extract (Graph Building)

### Node Types
```python
class NodeType(Enum):
    # Structural
    DIRECTORY = "directory"
    FILE = "file"
    MODULE = "module"          # package.json, pyproject.toml, go.mod
    
    # Code
    CLASS = "class"
    FUNCTION = "function"
    INTERFACE = "interface"
    TYPE = "type"
    VARIABLE = "variable"
    
    # Framework-specific
    ROUTE = "route"            # API endpoints
    COMPONENT = "component"    # React/Vue/Svelte
    HOOK = "hook"              # Custom hooks
    MODEL = "model"            # ORM models
    SERVICE = "service"        # Business logic classes
    MIDDLEWARE = "middleware"  # Express/FastAPI middleware
    CONTROLLER = "controller"  # Route handlers
    UTILITY = "utility"        # Helper functions
    
    # Config
    CONFIG = "config"
    MIGRATION = "migration"
    TEST = "test"
```

### Node Metadata Schema
```python
class NodeMetadata(BaseModel):
    # Universal
    language: str
    loc: int                    # Lines of code
    complexity: ComplexityMetrics
    docstring: str | None
    exports: list[str]          # Exported symbols
    imports: list[str]          # Imported symbols
    
    # Type-specific
    # ROUTE
    http_method: str | None
    route_path: str | None
    controller: str | None
    
    # COMPONENT
    props: list[PropType]
    hooks_used: list[str]
    renders: list[str]          # Child components
    
    # MODEL
    table_name: str | None
    fields: list[FieldDef]
    relations: list[RelationDef]
    
    # CLASS
    extends: str | None
    implements: list[str]
    methods: list[MethodDef]
    is_abstract: bool
    is_service: bool            # @Injectable, @Service, etc.
```

### Edge Types
```python
class EdgeType(Enum):
    # Structural
    CONTAINS = "contains"           # dir → file, file → class
    EXPORTS = "exports"             # file → symbol
    
    # Dependencies
    IMPORTS = "imports"             # file → file/module
    RE_EXPORTS = "re_exports"       # barrel files
    
    # Code relationships
    EXTENDS = "extends"             # class → class
    IMPLEMENTS = "implements"       # class → interface
    CALLS = "calls"                 # function → function
    INSTANTIATES = "instantiates"   # class → class (new)
    
    # Framework
    ROUTES_TO = "routes_to"         # route → controller
    RENDERS = "renders"             # component → component
    USES_HOOK = "uses_hook"         # component → hook
    HAS_MODEL = "has_model"         # service → model
    MIDDLEWARE_FOR = "middleware_for" # middleware → route
    
    # Data flow
    READS = "reads"                 # function → model/table
    WRITES = "writes"               # function → model/table
    EMITS = "emits"                 # event emitter → event
    LISTENS = "listens"             # handler → event
```

### Extraction Rules (Examples)

#### API Routes (Express/FastAPI/Next.js)
```python
def extract_routes(tree: Tree, lang: str) -> list[RouteNode]:
    patterns = {
        "typescript": {
            "express": r"(app|router)\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]",
            "nextjs": r"export\s+(async\s+)?(GET|POST|PUT|DELETE|PATCH)",
            "nestjs": r"@(Get|Post|Put|Delete|Patch)\(['\"]([^'\"]*)['\"]\)",
        },
        "python": {
            "fastapi": r"@(app|router)\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]\)",
            "flask": r"@app\.route\(['\"]([^'\"]+)['\"]",
            "django": r"path\(['\"]([^'\"]+)['\"],\s*(\w+)",
        }
    }
```

#### React Components
```python
def extract_components(tree: Tree) -> list[ComponentNode]:
    # Function components
    (function_declaration
        name: (identifier) @name
        (#match? @name "^[A-Z]"))
    
    # Arrow components
    (variable_declarator
        name: (identifier) @name
        value: (arrow_function) @fn
        (#match? @name "^[A-Z]"))
    
    # Class components
    (class_declaration
        name: (type_identifier) @name
        extends: (class_heritage (identifier) @base)
        (#any-of? @base "Component" "PureComponent" "React.Component"))
```

#### Database Models (Prisma/SQLAlchemy/Django/GORM)
```python
def extract_models(tree: Tree, lang: str) -> list[ModelNode]:
    patterns = {
        "prisma": r"model\s+(\w+)\s*\{",
        "sqlalchemy": r"class\s+(\w+)\(.*Base.*\):",
        "django": r"class\s+(\w+)\(models\.Model\):",
        "gorm": r"type\s+(\w+)\s+struct\s*\{",
    }
```

---

## Stage 4: Embeddings

### Model
- **Primary**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, 22ms CPU)
- **Fallback**: `nomic-ai/nomic-embed-text-v1.5` (768-dim, better code)
- **Local**: Ollama `nomic-embed-text` for privacy

### Text Construction for Embedding
```python
def build_embedding_text(node: CodeNode) -> str:
    parts = [
        f"Type: {node.type.value}",
        f"Name: {node.name}",
        f"Path: {node.path}",
    ]
    
    if node.metadata.docstring:
        parts.append(f"Doc: {node.metadata.docstring}")
    
    if node.metadata.exports:
        parts.append(f"Exports: {', '.join(node.metadata.exports)}")
    
    if node.type == NodeType.FUNCTION:
        sig = node.metadata.signature or ""
        parts.append(f"Signature: {sig}")
    
    if node.type == NodeType.CLASS:
        methods = [m.name for m in node.metadata.methods[:10]]
        parts.append(f"Methods: {', '.join(methods)}")
    
    if node.type == NodeType.ROUTE:
        parts.append(f"Route: {node.metadata.http_method} {node.metadata.route_path}")
    
    return " | ".join(parts)
```

### Batching Strategy
```python
async def generate_embeddings(nodes: list[CodeNode], batch_size: int = 32):
    # Sort by text length for efficient padding
    nodes.sort(key=lambda n: len(build_embedding_text(n)))
    
    for batch in chunks(nodes, batch_size):
        texts = [build_embedding_text(n) for n in batch]
        vectors = await embedder.encode(texts)
        
        for node, vector in zip(batch, vectors):
            node.embedding = vector.tolist()
```

---

## Stage 5: Persist

### Database Operations
```python
async def upsert_graph(repo_id: UUID, graph: CodeGraph):
    async with db.transaction():
        # 1. Upsert nodes (batch)
        await db.execute_many(
            """
            INSERT INTO code_nodes (id, repo_id, type, name, path, language, metadata, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (repo_id, path, name, type) DO UPDATE SET
                metadata = EXCLUDED.metadata,
                embedding = EXCLUDED.embedding,
                updated_at = NOW()
            """,
            [(n.id, repo_id, n.type, n.name, n.path, n.language, n.metadata, n.embedding)
             for n in graph.nodes]
        )
        
        # 2. Upsert edges (batch)
        await db.execute_many(
            """
            INSERT INTO code_edges (id, repo_id, source_id, target_id, type, weight, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (repo_id, source_id, target_id, type) DO UPDATE SET
                weight = EXCLUDED.weight,
                metadata = EXCLUDED.metadata
            """,
            [(e.id, repo_id, e.source_id, e.target_id, e.type, e.weight, e.metadata)
             for e in graph.edges]
        )
        
        # 3. Refresh materialized views / HNSW index
        await db.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY repo_node_stats")
```

### Incremental Update Algorithm
```python
async def incremental_update(repo_id: UUID, changed_files: list[ChangedFile]):
    # 1. Parse changed files → new subgraph
    new_nodes, new_edges = await parse_files(changed_files)
    
    # 2. Identify affected nodes (old versions)
    old_node_ids = await db.fetch(
        "SELECT id FROM code_nodes WHERE repo_id = $1 AND path = ANY($2)",
        repo_id, [f.path for f in changed_files]
    )
    
    # 3. Delete old nodes + edges (cascade)
    await db.execute(
        "DELETE FROM code_nodes WHERE repo_id = $1 AND id = ANY($2)",
        repo_id, old_node_ids
    )
    
    # 4. Insert new
    await upsert_graph(repo_id, CodeGraph(new_nodes, new_edges))
    
    # 5. Update dependent embeddings (neighbors within 2 hops)
    neighbor_ids = await get_neighbors(repo_id, new_nodes, hops=2)
    await regenerate_embeddings(neighbor_ids)
```

---

## Error Handling & Resilience

### Retry Policy
```python
INGESTION_RETRY_POLICY = {
    "max_retries": 3,
    "base_delay": 5,      # seconds
    "max_delay": 300,
    "exponential_base": 2,
    "retry_on": [ConnectionError, TimeoutError, RateLimitError]
}
```

### Dead Letter Queue
- Failed files → stored in `ingestion_failures` table
- Manual retry endpoint
- Alert after 10+ failures in single repo

### Monitoring Metrics
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Ingestion duration (median) | < 5 min | > 15 min |
| Ingestion success rate | > 99% | < 95% |
| Embedding generation latency | < 100ms/batch | > 500ms |
| Graph upsert latency | < 10s | > 60s |
| Incremental update latency | < 30s | > 2 min |

---

## Testing Strategy

### Unit Tests
- Each extractor: fixtures with expected nodes/edges
- Embedding text builder: snapshot tests
- Graph persistence: round-trip verification

### Integration Tests
- Sample repos per language (in `test-fixtures/`)
- Full pipeline: clone → parse → embed → persist → query
- Incremental update: modify fixture → verify diff

### Performance Tests
- 10k file monorepo: < 10 min full ingestion
- 100 file change: < 30s incremental
- Memory usage: < 2GB peak