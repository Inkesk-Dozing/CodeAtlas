from parsers import get_parser
from parsers.base import ParsedSymbol, ParseResult
from parsers.javascript import JavaScriptParser
from parsers.python import PythonParser

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
