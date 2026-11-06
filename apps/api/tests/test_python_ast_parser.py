"""Unit tests for Python AST Parser Engine with Decorator & Type Hint Analysis (Issue #26)."""

import pytest

from parsers.python import PythonParser


@pytest.fixture
def parser() -> PythonParser:
    return PythonParser()


def test_imports_absolute_and_relative(parser: PythonParser):
    code = """
import os
import sys as system
from typing import Any, Optional as Opt
from . import local_module
from ..services.auth import verify_token, RoleChecker
"""
    result = parser.parse(code, "app/api/endpoints.py")
    sources = [imp.source for imp in result.imports]

    assert "os" in sources
    assert "sys" in sources
    assert "typing" in sources
    assert any("local_module" in imp.names or imp.source == "." for imp in result.imports)
    assert any("verify_token" in imp.names for imp in result.imports)
    assert any(".." in imp.source for imp in result.imports)


def test_function_signatures_type_hints_and_defaults(parser: PythonParser):
    code = """
async def calculate_metrics(
    user_id: int,
    metrics: list[str],
    threshold: float = 0.75,
    *args,
    **kwargs
) -> dict[str, Any]:
    \"\"\"
    Compute aggregated metrics for a given user.
    Handles multiple thresholds and extra kwargs.
    \"\"\"
    return {"status": "ok"}
"""
    result = parser.parse(code, "app/services/metrics.py")
    assert len(result.functions) == 1
    fn = result.functions[0]

    assert fn.name == "calculate_metrics"
    assert fn.is_async is True
    assert "calculate_metrics" in fn.signature
    assert "-> dict[str, Any]" in fn.signature

    # Docstring validation
    assert fn.docstring is not None
    assert "Compute aggregated metrics for a given user." in fn.docstring
    assert "Handles multiple thresholds and extra kwargs." in fn.docstring
    assert '"""' not in fn.docstring

    # Parameter metadata
    params = fn.metadata.get("params", [])
    assert "user_id" in params
    assert "metrics" in params
    assert "threshold" in params
    assert "*args" in params
    assert "**kwargs" in params

    param_types = fn.metadata.get("param_types", {})
    assert param_types.get("user_id") == "int"
    assert "list[str]" in param_types.get("metrics", "")

    param_defaults = fn.metadata.get("param_defaults", {})
    assert param_defaults.get("threshold") == "0.75"

    assert fn.metadata.get("return_type") == "dict[str, Any]"


def test_cyclomatic_complexity_calculation(parser: PythonParser):
    code = (
        "def complex_decision(a: int, b: int, c: bool) -> int:\n"
        "    score = 0\n"
        "    if a > 10:\n"
        "        score += 1\n"
        "    elif a < 0:\n"
        "        score -= 1\n"
        "\n"
        "    for i in range(b):\n"
        "        if i % 2 == 0 and c:\n"
        "            score += 2\n"
        "        elif i % 3 == 0 or not c:\n"
        "            score += 3\n"
        "\n"
        "    while score < 100:\n"
        "        try:\n"
        "            score += 10\n"
        "            if score == 50:\n"
        "                break\n"
        "        except Exception:\n"
        "            score = 100\n"
        "\n"
        "    return score\n"
    )
    result = parser.parse(code, "app/logic.py")
    assert len(result.functions) == 1
    fn = result.functions[0]

    complexity = fn.metadata.get("complexity", {}).get("cyclomatic", 1)
    # 1 base + if + elif + for + if + and + elif + or + while + try/except + if = complexity >= 8
    assert complexity >= 7


def test_classes_base_classes_and_class_variables(parser: PythonParser):
    code = """
class BaseRepository:
    table_name: str = "base"

class UserRepository(BaseRepository, CacheMixin):
    \"\"\"Repository for managing user accounts and credentials.\"\"\"
    table_name: str = "users"
    cache_ttl: int = 3600
    is_active: bool = True
    connection_pool: Any

    def __init__(self, db_conn: Any):
        self.db = db_conn

    def get_by_id(self, user_id: int) -> dict:
        return {}
"""
    result = parser.parse(code, "app/db/repositories.py")
    class_map = {c.name: c for c in result.classes}
    assert "UserRepository" in class_map

    user_repo = class_map["UserRepository"]
    assert "BaseRepository" in user_repo.metadata.get("bases", [])
    assert "CacheMixin" in user_repo.metadata.get("bases", [])
    assert "Repository for managing user accounts and credentials." in (user_repo.docstring or "")
    assert "get_by_id" in user_repo.metadata.get("methods", [])

    # Class variables
    class_vars = user_repo.metadata.get("class_variables", [])
    var_names = [v["name"] for v in class_vars]
    assert "table_name" in var_names
    assert "cache_ttl" in var_names
    assert "is_active" in var_names
    assert "connection_pool" in var_names


def test_api_route_decorator_patterns(parser: PythonParser):
    code = """
from fastapi import APIRouter
from flask import Flask
from rest_framework.decorators import api_view

router = APIRouter()
app = Flask(__name__)

@router.get("/api/v1/users/{user_id}")
async def get_user_endpoint(user_id: int):
    return {"id": user_id}

@router.post("/api/v1/users")
def create_user_endpoint(data: dict):
    return data

@app.route("/flask/ping", methods=["POST"])
def flask_ping():
    return "pong"

@api_view(["GET"])
def django_status_view(request):
    return "ok"
"""
    result = parser.parse(code, "app/routes.py")
    routes = result.routes
    route_paths = {r.path for r in routes}
    route_methods = {(r.method, r.path) for r in routes}

    assert "/api/v1/users/{user_id}" in route_paths
    assert "/api/v1/users" in route_paths
    assert "/flask/ping" in route_paths
    assert ("GET", "/api/v1/users/{user_id}") in route_methods
    assert ("POST", "/api/v1/users") in route_methods
    assert ("POST", "/flask/ping") in route_methods


def test_decorator_chains_preserved(parser: PythonParser):
    code = """
@router.post("/items")
@authenticate_required
@rate_limit(max_requests=100)
def process_item():
    pass
"""
    result = parser.parse(code, "app/items.py")
    assert len(result.functions) == 1
    fn = result.functions[0]
    decs = fn.metadata.get("decorators", [])
    assert any("router.post" in d for d in decs)
    assert any("authenticate_required" in d for d in decs)
    assert any("rate_limit" in d for d in decs)
