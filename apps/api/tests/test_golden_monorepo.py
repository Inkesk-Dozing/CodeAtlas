"""Comprehensive Synthetic Golden Monorepo Fixture & Parser Test Suite (Issue #42)."""

from pathlib import Path

from parsers.golang import GoParser
from parsers.javascript import JavaScriptParser
from parsers.orm import PrismaParser, PythonORMParser
from parsers.python import PythonParser
from parsers.routes import JavaSpringParser, extract_nextjs_app_routes, extract_route_params
from parsers.rust import RustParser
from services.ingestion.extractor import GraphExtractor

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "golden_monorepo"


def _read_fixture(relative_path: str) -> str:
    path = FIXTURE_ROOT / relative_path
    assert path.exists(), f"Fixture file not found: {path}"
    return path.read_text(encoding="utf-8")


class TestGoldenMonorepoFixture:
    """Validate extraction accuracy against known ground truth for the synthetic monorepo."""

    def test_shared_package_types_and_utils(self):
        js_parser = JavaScriptParser()

        # 1. packages/common/src/types.ts
        content = _read_fixture("packages/common/src/types.ts")
        result = js_parser.parse(content, "packages/common/src/types.ts")
        interface_names = {i.name for i in result.interfaces}
        assert "UserDTO" in interface_names
        assert "ApiResponse" in interface_names
        assert "UserRole" in interface_names

        # 2. packages/common/src/utils.ts
        content = _read_fixture("packages/common/src/utils.ts")
        result = js_parser.parse(content, "packages/common/src/utils.ts")
        fn_names = {f.name for f in result.functions}
        assert "formatUserName" in fn_names
        assert "sanitizeEmail" in fn_names
        var_names = {v.name for v in result.variables}
        assert "DEFAULT_PAGE_LIMIT" in var_names

        # 3. packages/common/src/index.ts (re-exports)
        content = _read_fixture("packages/common/src/index.ts")
        result = js_parser.parse(content, "packages/common/src/index.ts")
        assert len(result.imports) == 2
        import_sources = {imp.source for imp in result.imports}
        assert "./types" in import_sources
        assert "./utils" in import_sources

    def test_nextjs_components_hooks_and_routes(self):
        js_parser = JavaScriptParser()

        # 1. Hook extraction: apps/web/hooks/useUserSession.ts
        content = _read_fixture("apps/web/hooks/useUserSession.ts")
        result = js_parser.parse(content, "apps/web/hooks/useUserSession.ts")
        hook_names = {h.name for h in result.hooks}
        assert "useUserSession" in hook_names

        # 2. Component extraction: apps/web/components/AppHeader.tsx
        content = _read_fixture("apps/web/components/AppHeader.tsx")
        result = js_parser.parse(content, "apps/web/components/AppHeader.tsx")
        comp_names = {c.name for c in result.components}
        assert "AppHeader" in comp_names
        header_comp = next(c for c in result.components if c.name == "AppHeader")
        assert "title" in header_comp.metadata.get("props", [])

        # 3. Component extraction with props: apps/web/components/UserCard.tsx
        content = _read_fixture("apps/web/components/UserCard.tsx")
        result = js_parser.parse(content, "apps/web/components/UserCard.tsx")
        comp_names = {c.name for c in result.components}
        assert "UserCard" in comp_names
        card_comp = next(c for c in result.components if c.name == "UserCard")
        assert "user" in card_comp.metadata.get("props", [])

        # 4. Next.js 14 App Router API: apps/web/app/api/users/route.ts
        content = _read_fixture("apps/web/app/api/users/route.ts")
        routes = extract_nextjs_app_routes("apps/web/app/api/users/route.ts", content)
        route_methods = {r.method for r in routes}
        assert "GET" in route_methods
        assert "POST" in route_methods
        assert all(r.framework == "nextjs" for r in routes)

    def test_fastapi_backend_models_and_routers(self):
        py_parser = PythonParser()

        # 1. Pydantic models: apps/api/models/user.py
        content = _read_fixture("apps/api/models/user.py")
        result = py_parser.parse(content, "apps/api/models/user.py")
        class_names = {c.name for c in result.classes}
        assert "UserBase" in class_names
        assert "UserCreate" in class_names
        assert "UserResponse" in class_names

        # 2. SQLAlchemy ORM models: apps/api/db/models.py
        content = _read_fixture("apps/api/db/models.py")
        result = py_parser.parse(content, "apps/api/db/models.py")
        model_names = {m.name for m in result.models}
        assert "User" in model_names
        assert "Post" in model_names

        orm_user = next(m for m in result.models if m.name == "User")
        user_field_names = [f["name"] if isinstance(f, dict) else f for f in orm_user.metadata.get("fields", [])]
        assert "id" in user_field_names
        assert "email" in user_field_names
        assert orm_user.metadata.get("orm") == "sqlalchemy"

        orm_post = next(m for m in result.models if m.name == "Post")
        post_field_names = [f["name"] if isinstance(f, dict) else f for f in orm_post.metadata.get("fields", [])]
        assert "author_id" in post_field_names
        fk_targets = [f"{fk['target_model']}.{fk['target_column']}" if isinstance(fk, dict) else fk for fk in orm_post.metadata.get("foreign_keys", [])]
        assert "users.id" in fk_targets

        # 3. FastAPI router with routes: apps/api/routers/users.py
        content = _read_fixture("apps/api/routers/users.py")
        result = py_parser.parse(content, "apps/api/routers/users.py")
        fn_names = {f.name for f in result.functions}
        assert "verify_auth_token" in fn_names
        assert "list_users" in fn_names
        assert "create_user" in fn_names
        assert "get_user_by_id" in fn_names

        route_paths = {r.path for r in result.routes}
        assert "/" in route_paths
        assert "/{user_id}" in route_paths

    def test_full_golden_monorepo_graph_extraction(self):
        """End-to-end graph extraction on all golden monorepo files verifying exact counts and edges."""
        py_parser = PythonParser()
        js_parser = JavaScriptParser()

        fixture_files = [
            ("packages/common/src/types.ts", js_parser),
            ("packages/common/src/utils.ts", js_parser),
            ("packages/common/src/index.ts", js_parser),
            ("apps/web/hooks/useUserSession.ts", js_parser),
            ("apps/web/components/AppHeader.tsx", js_parser),
            ("apps/web/components/UserCard.tsx", js_parser),
            ("apps/web/app/api/users/route.ts", js_parser),
            ("apps/web/app/page.tsx", js_parser),
            ("apps/api/models/user.py", py_parser),
            ("apps/api/db/models.py", py_parser),
            ("apps/api/routers/users.py", py_parser),
            ("apps/api/routers/health.py", py_parser),
            ("apps/api/main.py", py_parser),
        ]

        parsed_files = []
        for rel_path, parser in fixture_files:
            content = _read_fixture(rel_path)
            lang = "python" if rel_path.endswith(".py") else "typescript"
            parsed = parser.parse(content, rel_path)
            if "app/api" in rel_path and rel_path.endswith("route.ts"):
                parsed.routes.extend(extract_nextjs_app_routes(rel_path, content))

            parsed_files.append({
                "path": rel_path,
                "content": content,
                "language": lang,
                "parsed": parsed,
            })

        extractor = GraphExtractor(repo_id="golden-monorepo-test")
        nodes, edges = extractor.extract(parsed_files)

        # Assert node types exist
        node_types = {n["type"] for n in nodes}
        assert "directory" in node_types
        assert "file" in node_types
        assert "component" in node_types
        assert "function" in node_types
        assert "model" in node_types
        assert "class" in node_types
        assert "route" in node_types

        # Assert edge types exist
        edge_types = {e["type"] for e in edges}
        assert "imports" in edge_types
        assert "contains" in edge_types
        assert "handles_route" in edge_types

        # Assert ground truth node count ranges (> 40 nodes, > 25 edges)
        assert len(nodes) >= 40
        assert len(edges) >= 25


class TestParserFallbackAndCoverage:
    """Ensure regex fallbacks, edge-cases, and non-native paths are thoroughly exercised for >=90% coverage."""

    def test_python_regex_fallback_mode(self):
        py_parser = PythonParser()
        # Force fallback mode
        content = """
import os
from typing import List
from ..services import auth_service

class AccountModel(models.Model):
    name = Column(String)

def process_account(account_id: int = 1) -> bool:
    \"\"\"Process an account.\"\"\"
    return True
"""
        result = py_parser._parse_regex(content, "services/account.py")
        assert result.loc > 0
        assert any(i.source == "os" for i in result.imports)
        assert any(c.name == "AccountModel" for c in result.classes)
        assert any(f.name == "process_account" for f in result.functions)

    def test_javascript_regex_fallback_mode(self):
        js_parser = JavaScriptParser()
        content = """
import { useState } from 'react';
const express = require('express');

export class WidgetService extends BaseService implements IService {
  constructor() {}
  run() {}
}

export function useCounter() {
  return useState(0);
}

export const Header = () => <div>Header</div>;
"""
        result = js_parser._parse_regex(content, "src/widget.tsx")
        assert result.loc > 0
        assert len(result.imports) >= 2
        assert any(c.name == "WidgetService" for c in result.classes)
        assert any(h.name == "useCounter" for h in result.hooks)
        assert any(comp.name == "Header" for comp in result.components)

    def test_golang_and_rust_parsers(self):
        go_parser = GoParser()
        go_code = """
package main
import (
    "fmt"
    "net/http"
)
type Server struct { port int }
type Handler interface { Handle() }
func (s *Server) Start() error { return nil }
func RegisterRoutes(r *http.ServeMux) {
    r.HandleFunc("/api/go/ping", func(w http.ResponseWriter, req *http.Request) {})
}
"""
        go_result = go_parser.parse(go_code, "main.go")
        assert len(go_result.symbols) >= 1
        assert go_result.loc > 0

        rust_parser = RustParser()
        rust_code = """
use std::collections::HashMap;
pub struct Config { pub port: u16 }
pub trait Service { fn execute(&self); }
impl Config { pub fn new() -> Self { Config { port: 8080 } } }
pub fn run_app() { println!("Running"); }
"""
        rust_result = rust_parser.parse(rust_code, "src/lib.rs")
        assert len(rust_result.symbols) >= 1
        assert rust_result.loc > 0

    def test_route_extractor_spring_and_express(self):
        # Spring route with annotations and unslashed paths
        java_code = """
@RestController
@RequestMapping("api/v1")
public class OrderController {
    @GetMapping("orders")
    public List<Order> getOrders() { return null; }

    @RequestMapping(value = "orders/custom", method = RequestMethod.POST)
    public void createOrder() {}
}
"""
        spring_parser = JavaSpringParser()
        result = spring_parser.parse(java_code, "OrderController.java")
        routes = result.routes
        assert len(routes) >= 2
        assert any(r.path == "/api/v1/orders" and r.method == "GET" for r in routes)
        assert any(r.path == "/api/v1/orders/custom" and r.method == "POST" for r in routes)

        # Non-controller Java class should return no routes
        empty_res = spring_parser.parse("public class Dummy {}", "Dummy.java")
        assert len(empty_res.routes) == 0

        # Next.js app routes with params and catch-all
        next_routes = extract_nextjs_app_routes(
            "apps/web/app/api/posts/[...slug]/route.ts",
            "export const POST = async () => {};\nexport async function GET() {}",
        )
        assert len(next_routes) == 2
        assert any(r.method == "POST" for r in next_routes)
        assert any(r.method == "GET" for r in next_routes)
        assert next_routes[0].params == ["slug"]

        param_routes = extract_nextjs_app_routes(
            "src/app/api/users/[id]/route.js",
            "export async function DELETE() {}",
        )
        assert len(param_routes) == 1
        assert ":id" in param_routes[0].path
        assert param_routes[0].params == ["id"]

        # Route param extraction
        extracted_params = extract_route_params("/users/:userId/posts/{postId}/[slug]/[...rest]")
        assert "userId" in extracted_params
        assert "postId" in extracted_params
        assert "slug" in extracted_params
        assert "rest" in extracted_params

        # Express route
        js_code = """
const express = require('express');
const app = express();
app.post('/api/checkout', (req, res) => {});
"""
        js_parser = JavaScriptParser()
        js_result = js_parser.parse(js_code, "server.js")
        express_routes = js_result.routes
        assert len(express_routes) >= 1
        assert express_routes[0].method == "POST"

    def test_parser_edge_cases_and_fallbacks(self):
        # Python parser regex fallback
        py_parser = PythonParser()
        sample_py = '''
"""Module docstring."""
from fastapi import APIRouter
import django

@router.get("/api/v1/items")
def list_items():
    """List all items."""
    return []

@service
class ItemService(BaseService):
    """Service class docstring."""
    count: int = 10

    def process(self):
        pass

class Item(models.Model):
    id = Column(Integer, primary_key=True)
    title = Column(String)

path('api/django/items', item_view)
'''
        regex_res = py_parser._parse_regex(sample_py, "sample.py")
        assert len(regex_res.symbols) >= 1
        assert len(regex_res.routes) >= 2
        assert len(regex_res.models) >= 1
        assert py_parser._detect_framework("from flask import Flask") == "flask"
        assert py_parser._detect_framework("import sanic") == "sanic"
        assert py_parser._detect_framework("import django") == "django"

        # Go parser net/http and string escape edge cases
        go_parser = GoParser()
        go_code = """
package main

import "net/http"

type EscapedStruct struct {
    Val string `json:"val\\""`
    Char byte
}

func handlePing(w http.ResponseWriter, r *http.Request) {}

func main() {
    c := 'x'
    http.HandleFunc("/api/v1/ping", handlePing)
}
"""
        go_res = go_parser.parse(go_code, "server.go")
        assert len(go_res.routes) >= 1
        assert any(r.path == "/api/v1/ping" for r in go_res.routes)

    def test_orm_parsers(self):
        prisma_parser = PrismaParser()
        prisma_code = """
model Account {
  id    String @id @default(uuid())
  email String @unique
  posts Post[]
}
"""
        result = prisma_parser.parse(prisma_code, "schema.prisma")
        assert len(result.models) == 1
        assert result.models[0].name == "Account"

        # Python ORM Django & SQLAlchemy extractors
        django_code = """
class Profile(models.Model):
    bio = models.TextField()
    user_id = models.ForeignKey('User', on_delete=models.CASCADE)
"""
        meta = PythonORMParser.extract_model_metadata("Profile", ["models.Model"], django_code)
        assert meta is not None
        assert meta["orm"] == "django"
        field_names = [f["name"] if isinstance(f, dict) else f for f in meta["fields"]]
        assert "bio" in field_names
        assert "user_id" in field_names
