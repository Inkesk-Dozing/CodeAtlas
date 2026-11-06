
from parsers import get_parser
from parsers.javascript import JavaScriptParser
from parsers.python import PythonParser
from parsers.routes import JavaSpringParser, extract_nextjs_app_routes, extract_route_params
from services.ingestion.extractor import GraphExtractor

FASTAPI_SAMPLE = """
from fastapi import APIRouter

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user_detail(user_id: int):
    return {"id": user_id}

@router.post("/items")
def create_item(name: str):
    return {"name": name}
"""

EXPRESS_SAMPLE = """
const express = require('express');
const app = express();

app.get('/api/v1/projects/:projectId/issues', authenticate, listIssues);
app.delete('/api/v1/projects/:projectId', authorize, deleteProject);
"""

NEXTJS_APP_ROUTE = """
import { NextResponse } from 'next/server';

export async function GET(request: Request, { params }: { params: { id: string } }) {
    return NextResponse.json({ id: params.id });
}

export async function POST(request: Request) {
    const body = await request.json();
    return NextResponse.json(body);
}
"""

SPRING_SAMPLE = """
package com.example.demo.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    @GetMapping("/{orderId}")
    public ResponseEntity<Order> getOrder(@PathVariable String orderId) {
        return ResponseEntity.ok(new Order(orderId));
    }

    @PostMapping
    public ResponseEntity<Order> createOrder(@RequestBody OrderRequest req) {
        return ResponseEntity.ok(new Order());
    }
}
"""


class TestRouteParamExtraction:
    def test_extracts_colon_and_brace_params(self):
        params1 = extract_route_params("/users/:userId/books/:bookId")
        assert params1 == ["userId", "bookId"]

        params2 = extract_route_params("/items/{item_id}/comments/{comment_id}")
        assert params2 == ["item_id", "comment_id"]

        params3 = extract_route_params("/app/[slug]/[...subpath]")
        assert params3 == ["slug", "subpath"]


class TestNextjsAppRouterExtraction:
    def test_parses_app_router_endpoints_and_http_verbs(self):
        routes = extract_nextjs_app_routes("src/app/api/users/[id]/route.ts", NEXTJS_APP_ROUTE)
        assert len(routes) == 2

        methods = {r.method for r in routes}
        assert methods == {"GET", "POST"}

        for r in routes:
            assert r.path == "/api/users/:id"
            assert r.framework == "nextjs"
            assert "id" in r.params

    def test_javascript_parser_integrates_nextjs_routes(self):
        js_parser = JavaScriptParser()
        result = js_parser.parse(NEXTJS_APP_ROUTE, "app/api/auth/[provider]/route.js")

        methods = {r.method for r in result.routes}
        assert "GET" in methods
        assert "POST" in methods
        assert any(r.path == "/api/auth/:provider" for r in result.routes)


class TestExpressRouteExtraction:
    def test_extracts_express_routes_middleware_and_params(self):
        js_parser = JavaScriptParser()
        result = js_parser.parse(EXPRESS_SAMPLE, "src/server.js")

        assert len(result.routes) >= 2
        get_route = next(r for r in result.routes if r.method == "GET")
        assert get_route.path == "/api/v1/projects/:projectId/issues"
        assert get_route.handler == "listIssues"
        assert "authenticate" in get_route.middleware
        assert "projectId" in get_route.params


class TestFastAPIRouteExtraction:
    def test_extracts_fastapi_routes_and_params(self):
        py_parser = PythonParser()
        result = py_parser.parse(FASTAPI_SAMPLE, "app/routers/users.py")

        assert len(result.routes) >= 2
        get_route = next(r for r in result.routes if r.method == "GET")
        assert get_route.path == "/users/{user_id}"
        assert get_route.handler == "get_user_detail"
        assert "user_id" in get_route.params


class TestSpringControllerExtraction:
    def test_extracts_spring_boot_controller_and_mappings(self):
        spring_parser = JavaSpringParser()
        result = spring_parser.parse(SPRING_SAMPLE, "src/main/java/com/example/OrderController.java")

        assert len(result.routes) == 2
        methods = {r.method for r in result.routes}
        assert methods == {"GET", "POST"}

        get_route = next(r for r in result.routes if r.method == "GET")
        assert get_route.path == "/api/v1/orders/{orderId}"
        assert get_route.handler == "getOrder"
        assert "orderId" in get_route.params

    def test_registry_resolves_java_and_spring(self):
        parser = get_parser("java")
        assert isinstance(parser, JavaSpringParser)


class TestGraphExtractorRouteEdges:
    def test_creates_routes_to_and_handles_route_edges(self):
        py_parser = PythonParser()
        parsed_py = py_parser.parse(FASTAPI_SAMPLE, "routes.py")

        files = [
            {"path": "routes.py", "language": "python", "content": FASTAPI_SAMPLE, "parsed": parsed_py}
        ]

        extractor = GraphExtractor(repo_id="repo-routes")
        nodes, edges = extractor.extract(files)

        # 1. Verify RouteNode created
        route_nodes = [n for n in nodes if n["type"] == "route"]
        assert len(route_nodes) >= 2
        r_get = next(n for n in route_nodes if n["name"] == "GET /users/{user_id}")
        assert r_get["metadata"]["http_method"] == "GET"
        assert r_get["metadata"]["params"] == ["user_id"]

        # 2. Verify routes_to edge and handles_route edge
        routes_to = [e for e in edges if e["type"] == "routes_to"]
        handles_route = [e for e in edges if e["type"] == "handles_route"]

        assert any("GET /users/{user_id}::route" in e["source_key"] and "get_user_detail::function" in e["target_key"] for e in routes_to)
        assert any("get_user_detail::function" in e["source_key"] and "GET /users/{user_id}::route" in e["target_key"] for e in handles_route)
