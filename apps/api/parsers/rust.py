import re

from parsers.base import (
    BaseParser,
    ParsedImport,
    ParsedRoute,
    ParsedSymbol,
    ParseResult,
)

# Mod statements: mod handlers; pub mod models;
MOD_PATTERN = re.compile(
    r"^\s*(pub(?:\([^)]+\))?\s+)?mod\s+([a-zA-Z0-9_]+)\s*;",
    re.MULTILINE,
)

# Use statements: use std::sync::Arc; pub use crate::models::User;
USE_PATTERN = re.compile(
    r"^\s*(pub(?:\([^)]+\))?\s+)?use\s+([^;]+);",
    re.MULTILINE,
)

# Structs: pub struct User { ... } or struct Config(u16, u16);
STRUCT_PATTERN = re.compile(
    r"^\s*(pub(?:\([^)]+\))?\s+)?struct\s+([a-zA-Z0-9_]+)(?:<[^>]+>)?(?:\s*\{([\s\S]*?)\}|\s*\(([\s\S]*?)\)\s*;|\s*;)",
    re.MULTILINE,
)

# Enums: pub enum Event { ... }
ENUM_PATTERN = re.compile(
    r"^\s*(pub(?:\([^)]+\))?\s+)?enum\s+([a-zA-Z0-9_]+)(?:<[^>]+>)?\s*\{([\s\S]*?)\}",
    re.MULTILINE,
)

# Traits: pub trait Repository { ... }
TRAIT_PATTERN = re.compile(
    r"^\s*(pub(?:\([^)]+\))?\s+)?trait\s+([a-zA-Z0-9_]+)(?:<[^>]+>)?(?:\s*:\s*[^{]+)?\s*\{([\s\S]*?)\}",
    re.MULTILINE,
)

# Impl blocks:
# impl Trait for Struct { ... }
# impl<T> Trait for Struct<T> { ... }
# impl Struct { ... }
IMPL_FOR_PATTERN = re.compile(
    r"^\s*impl(?:<[^>]*>)?\s+([a-zA-Z0-9_:]+)(?:<[^>]*>)?\s+for\s+([a-zA-Z0-9_:]+)(?:<[^>]*>)?\s*\{",
    re.MULTILINE,
)
IMPL_SELF_PATTERN = re.compile(
    r"^\s*impl(?:<[^>]*>)?\s+([a-zA-Z0-9_:]+)(?:<[^>]*>)?\s*\{",
    re.MULTILINE,
)

# Functions & Methods:
# pub async fn get_user(id: &str) -> Result<User, Error> { ... }
# fn helper() { ... }
FN_PATTERN = re.compile(
    r"^\s*(pub(?:\([^)]+\))?\s+)?(async\s+)?fn\s+([a-zA-Z0-9_]+)(?:<[^>]*>)?\s*\(([\s\S]*?)\)(?:\s*->\s*([^{]+))?\s*(?:where[^{]+)?\{",
    re.MULTILINE,
)

# Web Routes in Rust (Actix-web, Axum, Rocket):
# Actix: #[get("/api/v1/users")] or #[post("/items")]
# Axum / Router: .route("/api/v1/users", get(handler))
# Rocket: #[get("/<id>")]
ACTIX_ROUTE_PATTERN = re.compile(
    r"""#\[(get|post|put|delete|patch|head|options)\s*\(\s*["']([^"']+)["']\s*\)\]\s*(?:#\[[^\]]+\]\s*)*(?:pub(?:\([^)]+\))?\s+)?(?:async\s+)?fn\s+([a-zA-Z0-9_]+)""",
    re.MULTILINE,
)
AXUM_ROUTE_PATTERN = re.compile(
    r"""\.route\s*\(\s*["']([^"']+)["']\s*,\s*(get|post|put|delete|patch)\s*\(\s*([a-zA-Z0-9_:]+)\s*\)\s*\)""",
    re.MULTILINE,
)


class RustParser(BaseParser):
    def parse(self, content: str, path: str) -> ParseResult:
        result = ParseResult(loc=self._count_loc(content))
        lines = content.splitlines()

        result.imports = self._extract_imports(content, lines)
        result.classes = self._extract_structs_and_enums(content, lines)
        result.interfaces = self._extract_traits(content, lines)
        
        # Extract impl blocks to map methods and trait implementations
        impl_traits, impl_methods = self._extract_impl_blocks(content)
        
        # Link implemented traits to structs in metadata
        self._link_traits_to_structs(result.classes, impl_traits)

        standalone_fns = self._extract_standalone_functions(content, lines)
        result.functions = impl_methods + standalone_fns

        result.routes = self._extract_routes(content, lines)

        # In Rust, pub / pub(...) indicates exports
        result.exports = [
            s.name for s in (result.classes + result.interfaces + result.functions)
            if s.is_exported
        ]

        result.symbols = result.classes + result.interfaces + result.functions
        return result

    def _extract_imports(self, content: str, lines: list[str]) -> list[ParsedImport]:
        imports: list[ParsedImport] = []

        # Mod declarations
        for match in MOD_PATTERN.finditer(content):
            pub_decl = match.group(1) or ""
            mod_name = match.group(2)
            line_no = content[: match.start()].count("\n") + 1
            imports.append(
                ParsedImport(
                    source=f"mod::{mod_name}",
                    names=[mod_name],
                    line=line_no,
                    is_namespace=True,
                )
            )

        # Use declarations: use std::collections::HashMap; use crate::foo::{Bar, Baz};
        for match in USE_PATTERN.finditer(content):
            pub_decl = match.group(1) or ""
            raw_use = match.group(2).strip()
            line_no = content[: match.start()].count("\n") + 1

            if "::{" in raw_use:
                prefix, tail = raw_use.split("::{", 1)
                tail = tail.rstrip("}").strip()
                names = [n.strip() for n in tail.split(",") if n.strip()]
                source = prefix.strip()
            else:
                parts = raw_use.split("::")
                names = [parts[-1].strip()]
                source = "::".join(parts[:-1]) if len(parts) > 1 else raw_use

            imports.append(
                ParsedImport(
                    source=source,
                    names=names,
                    line=line_no,
                )
            )

        return imports

    def _extract_structs_and_enums(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
        symbols: list[ParsedSymbol] = []

        # Structs
        for match in STRUCT_PATTERN.finditer(content):
            pub_decl = (match.group(1) or "").strip()
            name = match.group(2)
            fields_body = match.group(3) or match.group(4) or ""
            line_no = content[: match.start()].count("\n") + 1
            end_line = content[: match.end()].count("\n") + 1

            is_exported = bool(pub_decl.startswith("pub"))
            fields = []
            for raw_line in fields_body.splitlines():
                line = raw_line.strip()
                if line and not line.startswith("//"):
                    col_split = line.split(":")
                    if len(col_split) >= 2:
                        fields.append(col_split[0].replace("pub", "").strip())

            symbols.append(
                ParsedSymbol(
                    name=name,
                    kind="struct",
                    line=line_no,
                    end_line=end_line,
                    signature=f"struct {name}",
                    is_exported=is_exported,
                    visibility=pub_decl or "private",
                    metadata={
                        "fields": fields,
                        "visibility": pub_decl or "private",
                        "implements": [],
                    },
                )
            )

        # Enums
        for match in ENUM_PATTERN.finditer(content):
            pub_decl = (match.group(1) or "").strip()
            name = match.group(2)
            variants_body = match.group(3) or ""
            line_no = content[: match.start()].count("\n") + 1
            end_line = content[: match.end()].count("\n") + 1

            variants = [
                v.strip().split("(")[0].split("{")[0]
                for v in variants_body.split(",")
                if v.strip() and not v.strip().startswith("//")
            ]

            is_exported = bool(pub_decl.startswith("pub"))
            symbols.append(
                ParsedSymbol(
                    name=name,
                    kind="enum",
                    line=line_no,
                    end_line=end_line,
                    signature=f"enum {name}",
                    is_exported=is_exported,
                    visibility=pub_decl or "private",
                    metadata={
                        "variants": variants,
                        "visibility": pub_decl or "private",
                        "implements": [],
                    },
                )
            )

        return symbols

    def _extract_traits(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
        traits: list[ParsedSymbol] = []
        for match in TRAIT_PATTERN.finditer(content):
            pub_decl = (match.group(1) or "").strip()
            name = match.group(2)
            body = match.group(3) or ""
            line_no = content[: match.start()].count("\n") + 1
            end_line = content[: match.end()].count("\n") + 1

            methods = []
            for m in re.finditer(r"(?:async\s+)?fn\s+([a-zA-Z0-9_]+)", body):
                methods.append(m.group(1))

            is_exported = bool(pub_decl.startswith("pub"))
            traits.append(
                ParsedSymbol(
                    name=name,
                    kind="trait",
                    line=line_no,
                    end_line=end_line,
                    signature=f"trait {name}",
                    is_exported=is_exported,
                    visibility=pub_decl or "private",
                    metadata={
                        "methods": methods,
                        "visibility": pub_decl or "private",
                    },
                )
            )
        return traits

    def _extract_impl_blocks(self, content: str) -> tuple[list[dict], list[ParsedSymbol]]:
        # Returns list of (trait_name, struct_name) and list of method ParsedSymbol
        impl_traits: list[dict] = []
        impl_methods: list[ParsedSymbol] = []

        # Find all impl blocks by scanning 'impl' keyword to matching closing brace
        idx = 0
        while True:
            match = re.search(r"^\s*impl\b", content[idx:], re.MULTILINE)
            if not match:
                break

            impl_start = idx + match.start()
            brace_pos = content.find("{", impl_start)
            if brace_pos == -1:
                idx = impl_start + 4
                continue

            header = content[impl_start:brace_pos].strip()
            block_end = self._find_closing_brace(content, brace_pos)
            body = content[brace_pos + 1 : block_end - 1] if block_end != -1 else ""

            # Check if 'impl Trait for Struct'
            for_match = re.search(r"impl(?:<[^>]*>)?\s+([a-zA-Z0-9_:]+)(?:<[^>]*>)?\s+for\s+([a-zA-Z0-9_:]+)", header)
            if for_match:
                trait_name = for_match.group(1).split("::")[-1]
                struct_name = for_match.group(2).split("::")[-1]
                impl_traits.append({"trait": trait_name, "struct": struct_name})
                parent_type = struct_name
                parent_trait = trait_name
            else:
                # 'impl Struct'
                self_match = re.search(r"impl(?:<[^>]*>)?\s+([a-zA-Z0-9_:]+)", header)
                struct_name = self_match.group(1).split("::")[-1] if self_match else ""
                parent_type = struct_name
                parent_trait = None

            # Parse methods within this impl block
            for fn_match in FN_PATTERN.finditer(body):
                pub_decl = (fn_match.group(1) or "").strip()
                is_async = bool(fn_match.group(2))
                fn_name = fn_match.group(3)
                params = (fn_match.group(4) or "").strip()
                returns = (fn_match.group(5) or "").strip()

                line_no = content[: brace_pos + 1 + fn_match.start()].count("\n") + 1
                is_exported = bool(pub_decl.startswith("pub")) or (parent_trait is not None)

                impl_methods.append(
                    ParsedSymbol(
                        name=fn_name,
                        kind="method",
                        line=line_no,
                        signature=f"fn {fn_name}({params}) -> {returns}".strip().rstrip("->").strip(),
                        is_async=is_async,
                        is_exported=is_exported,
                        visibility=pub_decl or ("public" if parent_trait else "private"),
                        parent=parent_type,
                        metadata={
                            "receiver": parent_type,
                            "trait": parent_trait,
                            "params": params,
                            "returns": returns,
                            "visibility": pub_decl or "private",
                        },
                    )
                )

            idx = block_end if block_end != -1 else impl_start + 4

        return impl_traits, impl_methods

    def _extract_standalone_functions(self, content: str, lines: list[str]) -> list[ParsedSymbol]:
        # Extract top-level functions not inside impl or trait blocks
        functions: list[ParsedSymbol] = []
        for match in FN_PATTERN.finditer(content):
            # Check indentation to ensure top-level
            line_start = content.rfind("\n", 0, match.start()) + 1
            leading = content[line_start : match.start()]
            if leading.strip():
                continue

            pub_decl = (match.group(1) or "").strip()
            is_async = bool(match.group(2))
            fn_name = match.group(3)
            params = (match.group(4) or "").strip()
            returns = (match.group(5) or "").strip()

            line_no = content[: match.start()].count("\n") + 1
            is_exported = bool(pub_decl.startswith("pub"))

            functions.append(
                ParsedSymbol(
                    name=fn_name,
                    kind="function",
                    line=line_no,
                    signature=f"fn {fn_name}({params}) -> {returns}".strip().rstrip("->").strip(),
                    is_async=is_async,
                    is_exported=is_exported,
                    visibility=pub_decl or "private",
                    metadata={
                        "params": params,
                        "returns": returns,
                        "visibility": pub_decl or "private",
                    },
                )
            )
        return functions

    def _link_traits_to_structs(self, structs: list[ParsedSymbol], impl_traits: list[dict]):
        for item in impl_traits:
            for s in structs:
                if s.name == item["struct"]:
                    if item["trait"] not in s.metadata["implements"]:
                        s.metadata["implements"].append(item["trait"])

    def _extract_routes(self, content: str, lines: list[str]) -> list[ParsedRoute]:
        routes: list[ParsedRoute] = []

        # Actix attribute routes: #[get("/api/v1/users")]
        for match in ACTIX_ROUTE_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            handler = match.group(3)
            line_no = content[: match.start()].count("\n") + 1
            routes.append(
                ParsedRoute(
                    method=method,
                    path=path,
                    handler=handler,
                    framework="actix-web",
                    line=line_no,
                )
            )

        # Axum router routes: .route("/api/v1/users", get(handler))
        for match in AXUM_ROUTE_PATTERN.finditer(content):
            path = match.group(1)
            method = match.group(2).upper()
            handler = match.group(3).split("::")[-1]
            line_no = content[: match.start()].count("\n") + 1
            routes.append(
                ParsedRoute(
                    method=method,
                    path=path,
                    handler=handler,
                    framework="axum",
                    line=line_no,
                )
            )

        return routes

    def _find_closing_brace(self, content: str, open_brace_idx: int) -> int:
        depth = 0
        in_string = False
        in_char = False
        escape = False

        for idx in range(open_brace_idx, len(content)):
            char = content[idx]

            if escape:
                escape = False
                continue

            if char == "\\":
                escape = True
                continue

            if char == '"' and not in_char:
                in_string = not in_string
                continue

            if char == "'" and not in_string:
                in_char = not in_char
                continue

            if in_string or in_char:
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return idx + 1

        return -1
