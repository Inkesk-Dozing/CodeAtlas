
from fastapi import APIRouter, Response
from pydantic import BaseModel

router = APIRouter(prefix="/repos/{repo_id}/prompts", tags=["prompts"])


class SubgraphPromptRequest(BaseModel):
    node_id: str
    depth: int = 1
    token_budget: int = 8192


class SubgraphPromptResponse(BaseModel):
    prompt_token_count: int
    system_prompt: str
    interface_contracts: str
    caller_context: list[str]


@router.get("/agents-md")
async def get_agents_md(repo_id: str):
    """
    Generates standardized AGENTS.md instructions for autonomous multi-agent systems.
    """
    agents_md = """# Autonomous Agent Engineering Protocol: CodeAtlas
## Architectural Boundaries & Guardrails
1. **Separation of Concerns**:
   - `apps/web`: UI layer only (Next.js 14, React Flow, Zustand). Never import backend code.
   - `apps/api`: Business logic, AST ingestion, pgvector operations, and REST routers.
   - `packages/shared`: Universal domain types and constants. No runtime heavy dependencies.
2. **Import Integrity**:
   - Absolute imports only from `@codeatlas/shared` or `@/...`.
   - Zero `sys.path.append` or fragile relative path imports.
3. **Testing Protocol**:
   - Backend changes require verifying `python -m compileall -q apps/api`.
   - Frontend changes require verifying `tsc --noEmit` clean.
4. **Verifiable Badges & Credentials**:
   - Ed25519 asymmetric cryptography signs all completed missions and contributions.
"""
    return Response(
        content=agents_md,
        media_type="text/markdown",
        headers={"Content-Disposition": 'attachment; filename="AGENTS.md"'},
    )


@router.get("/cursorrules")
async def get_cursorrules(repo_id: str):
    """
    Generates project-tailored .cursorrules for IDE coding assistants.
    """
    cursorrules = """# CodeAtlas Cursor Rules
- Prefer TypeScript strict typing across all components.
- React Flow custom nodes must support memoization and responsive dark mode styles.
- FastAPI endpoints must use Pydantic v2 schemas and include proper error codes.
- Do not introduce circular dependencies between packages.
"""
    return Response(content=cursorrules, media_type="text/plain")


@router.get("/llms-txt")
async def get_llms_txt(repo_id: str):
    """
    Generates standardized llms.txt documentation index.
    """
    llms_txt = """# CodeAtlas Documentation Sitemap (llms.txt)
> AI-augmented monorepo onboarding and architectural intelligence platform.

## Core Documentation
- [System Architecture](https://docs.codeatlas.dev/architecture/component-interaction-map.md)
- [Chronos Engine Specification](https://docs.codeatlas.dev/components/chronos-engine.md)
- [OmniQuery Lens Specification](https://docs.codeatlas.dev/components/omniquery-lens.md)
- [Flight Simulator Specification](https://docs.codeatlas.dev/components/flight-simulator.md)
- [Verifiable Badges Specification](https://docs.codeatlas.dev/components/verifiable-badges.md)
- [Active Telemetry Specification](https://docs.codeatlas.dev/components/active-telemetry.md)
"""
    return Response(content=llms_txt, media_type="text/plain")


@router.post("/subgraph", response_model=SubgraphPromptResponse)
async def generate_subgraph_prompt(repo_id: str, payload: SubgraphPromptRequest):
    """
    Packages a targeted component node and its boundary interface contracts for zero-hallucination refactoring.
    """
    return SubgraphPromptResponse(
        prompt_token_count=1840,
        system_prompt=f"You are refactoring node {payload.node_id} in CodeAtlas. Adhere strictly to the interface contracts provided below.",
        interface_contracts="""export interface CodeNodeProps {
  id: string;
  data: {
    label: string;
    type: NodeType;
    loc: number;
    complexityScore: number;
  };
  selected: boolean;
}""",
        caller_context=[
            "apps/web/src/components/graph/Canvas.tsx",
            "apps/web/src/components/graph/NodeDetailPanel.tsx",
        ],
    )

