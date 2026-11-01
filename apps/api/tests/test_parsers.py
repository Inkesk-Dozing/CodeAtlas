from parsers import get_parser
from parsers.base import ParsedSymbol, ParseResult
from parsers.golang import GoParser
from parsers.javascript import JavaScriptParser
from parsers.python import PythonParser
from parsers.rust import RustParser

JS_SAMPLE = """
import React from 'react';
import { useState } from 'react';

export interface User { id: string; }

export function LoginPage() {
  const [name, setName] = useState('');
  return <div>{name}</div>;
}

export const api = {
  getUsers: async () => fetch('/api/users'),
};

class BaseService {
  run() {}
}

export default LoginPage;
"""

PY_SAMPLE = """
import os
from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
def list_users():
    \"\"\"List all users.\"\"\"
    return []

class UserService:
    def create(self, name: str):
        pass

def helper_function():
    return 1
"""


class TestParserRegistry:
    def test_known_languages(self):
        assert isinstance(get_parser("typescript"), JavaScriptParser)
        assert isinstance(get_parser("javascript"), JavaScriptParser)
        assert isinstance(get_parser("python"), PythonParser)
        assert isinstance(get_parser("go"), GoParser)
        assert isinstance(get_parser("golang"), GoParser)
        assert isinstance(get_parser("rust"), RustParser)
        assert isinstance(get_parser("rs"), RustParser)

    def test_unknown_language(self):
        assert get_parser("cobol") is None


class TestJavaScriptParser:
    def setup_method(self):
        self.parser = JavaScriptParser()

    def test_extracts_functions(self):
        result = self.parser.parse(JS_SAMPLE, "src/LoginPage.tsx")
        assert isinstance(result, ParseResult)
        fn_names = [f.name for f in result.functions]
        assert "LoginPage" in fn_names

    def test_extracts_classes(self):
        result = self.parser.parse(JS_SAMPLE, "src/service.ts")
        class_names = [c.name for c in result.classes]
        assert "BaseService" in class_names

    def test_extracts_imports(self):
        result = self.parser.parse(JS_SAMPLE, "src/a.tsx")
        sources = [i.source for i in result.imports]
        assert any("react" in s for s in sources)

    def test_extracts_express_routes(self):
        code = """
        app.get('/api/users', (req, res) => {});
        app.post('/api/login', handler);
        """
        result = self.parser.parse(code, "server.js")
        assert len(result.routes) >= 2
        methods = {r.method for r in result.routes}
        assert "GET" in methods and "POST" in methods

    def test_loc_counted(self):
        result = self.parser.parse(JS_SAMPLE, "a.ts")
        assert result.loc > 0


class TestPythonParser:
    def setup_method(self):
        self.parser = PythonParser()

    def test_extracts_functions_and_classes(self):
        result = self.parser.parse(PY_SAMPLE, "app/routes.py")
        fn_names = [f.name for f in result.functions]
        cls_names = [c.name for c in result.classes]
        assert "list_users" in fn_names
        assert "helper_function" in fn_names
        assert "UserService" in cls_names

    def test_extracts_route(self):
        result = self.parser.parse(PY_SAMPLE, "app/routes.py")
        assert len(result.routes) >= 1
        assert result.routes[0].path == "/users"
        assert result.routes[0].method in ("GET", "get")

    def test_extracts_imports(self):
        result = self.parser.parse(PY_SAMPLE, "app/routes.py")
        sources = [i.source for i in result.imports]
        assert any("fastapi" in s for s in sources)

    def test_docstring_captured(self):
        result = self.parser.parse(PY_SAMPLE, "app/routes.py")
        fn = next(f for f in result.functions if f.name == "list_users")
        assert "List all users" in (fn.docstring or "")

    def test_parsed_symbol_defaults(self):
        s = ParsedSymbol(name="x", kind="function", line=1)
        assert s.metadata == {}
        assert s.is_exported is False


GO_SAMPLE = """
package main

import (
    "context"
    "fmt"
    gin "github.com/gin-gonic/gin"
)

type Config struct {
    Port int
}

type UserService struct {
    Config
    db string
}

type UserReader interface {
    Get(ctx context.Context, id string) (string, error)
}

func (s *UserService) GetUser(ctx context.Context, id string) (string, error) {
    return "user", nil
}

func RegisterRoutes(r *gin.Engine, s *UserService) {
    r.GET("/api/v1/users", s.GetUser)
    r.POST("/api/v1/users", nil)
}
"""


class TestGoParser:
    def setup_method(self):
        self.parser = GoParser()

    def test_extracts_package_and_imports(self):
        result = self.parser.parse(GO_SAMPLE, "main.go")
        sources = [i.source for i in result.imports]
        assert "context" in sources
        assert "fmt" in sources
        assert "github.com/gin-gonic/gin" in sources

    def test_extracts_structs_and_embedded(self):
        result = self.parser.parse(GO_SAMPLE, "main.go")
        struct_names = [s.name for s in result.classes]
        assert "Config" in struct_names
        assert "UserService" in struct_names

        user_svc = next(s for s in result.classes if s.name == "UserService")
        assert "Config" in user_svc.metadata.get("embedded", [])
        assert user_svc.is_exported is True

    def test_extracts_interfaces(self):
        result = self.parser.parse(GO_SAMPLE, "main.go")
        iface_names = [i.name for i in result.interfaces]
        assert "UserReader" in iface_names
        reader = next(i for i in result.interfaces if i.name == "UserReader")
        assert reader.is_exported is True

    def test_extracts_receiver_methods_and_functions(self):
        result = self.parser.parse(GO_SAMPLE, "main.go")
        fn_names = [f.name for f in result.functions]
        assert "GetUser" in fn_names
        assert "RegisterRoutes" in fn_names

        method = next(f for f in result.functions if f.name == "GetUser")
        assert method.kind == "method"
        assert method.parent == "UserService"
        assert method.metadata["receiver"] == "UserService"
        assert method.is_exported is True

        pkg_fn = next(f for f in result.functions if f.name == "RegisterRoutes")
        assert pkg_fn.kind == "function"
        assert pkg_fn.parent == "main"

    def test_extracts_gin_routes(self):
        result = self.parser.parse(GO_SAMPLE, "main.go")
        assert len(result.routes) >= 2
        paths = [r.path for r in result.routes]
        assert "/api/v1/users" in paths
        methods = [r.method for r in result.routes]
        assert "GET" in methods and "POST" in methods


RUST_SAMPLE = """
pub mod handlers;
use std::sync::Arc;
use crate::models::{User, Account};

pub struct Config {
    pub port: u16,
}

pub enum Status {
    Active,
    Inactive,
}

pub trait Repository {
    async fn find_by_id(&self, id: &str) -> Option<User>;
}

pub struct UserRepository {
    config: Arc<Config>,
}

impl Repository for UserRepository {
    async fn find_by_id(&self, id: &str) -> Option<User> {
        None
    }
}

impl UserRepository {
    pub fn new(config: Arc<Config>) -> Self {
        Self { config }
    }
}

#[get("/api/v1/users")]
pub async fn list_users_handler() -> String {
    "users".to_string()
}
"""


class TestRustParser:
    def setup_method(self):
        self.parser = RustParser()

    def test_extracts_mods_and_imports(self):
        result = self.parser.parse(RUST_SAMPLE, "src/lib.rs")
        sources = [i.source for i in result.imports]
        assert "mod::handlers" in sources
        assert "std::sync" in sources
        assert "crate::models" in sources

    def test_extracts_structs_and_enums(self):
        result = self.parser.parse(RUST_SAMPLE, "src/lib.rs")
        struct_names = [s.name for s in result.classes if s.kind == "struct"]
        assert "Config" in struct_names
        assert "UserRepository" in struct_names

        enum_names = [s.name for s in result.classes if s.kind == "enum"]
        assert "Status" in enum_names

        config = next(s for s in result.classes if s.name == "Config")
        assert config.is_exported is True

    def test_extracts_traits(self):
        result = self.parser.parse(RUST_SAMPLE, "src/lib.rs")
        trait_names = [t.name for t in result.interfaces]
        assert "Repository" in trait_names
        repo_trait = next(t for t in result.interfaces if t.name == "Repository")
        assert repo_trait.is_exported is True
        assert "find_by_id" in repo_trait.metadata["methods"]

    def test_links_trait_implementation_to_struct(self):
        result = self.parser.parse(RUST_SAMPLE, "src/lib.rs")
        user_repo = next(s for s in result.classes if s.name == "UserRepository")
        assert "Repository" in user_repo.metadata.get("implements", [])

    def test_extracts_methods_and_standalone_functions(self):
        result = self.parser.parse(RUST_SAMPLE, "src/lib.rs")
        fn_names = [f.name for f in result.functions]
        assert "find_by_id" in fn_names
        assert "new" in fn_names
        assert "list_users_handler" in fn_names

        find_fn = next(f for f in result.functions if f.name == "find_by_id")
        assert find_fn.kind == "method"
        assert find_fn.parent == "UserRepository"
        assert find_fn.metadata["trait"] == "Repository"

        new_fn = next(f for f in result.functions if f.name == "new")
        assert new_fn.kind == "method"
        assert new_fn.parent == "UserRepository"
        assert new_fn.is_exported is True

    def test_extracts_actix_and_axum_routes(self):
        result = self.parser.parse(RUST_SAMPLE, "src/lib.rs")
        routes = result.routes
        assert any(r.path == "/api/v1/users" and r.method == "GET" and r.framework == "actix-web" for r in routes)

        axum_code = """
        let app = Router::new()
            .route("/health", get(health_check))
            .route("/items", post(create_item));
        """
        axum_result = self.parser.parse(axum_code, "src/main.rs")
        assert len(axum_result.routes) >= 2
        paths = [r.path for r in axum_result.routes]
        assert "/health" in paths
        assert "/items" in paths


