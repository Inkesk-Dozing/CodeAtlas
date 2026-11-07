"""Route extraction helpers and parsers for Next.js, Express/NestJS, Spring Boot, and FastAPI."""

import re

from parsers.base import BaseParser, ParsedRoute, ParsedSymbol, ParseResult


def extract_route_params(path: str) -> list[str]:
    """Extract path parameters from express-style (:id), openapi-style ({id}), or nextjs-style ([id] / [...slug]) paths."""
    colon_params = re.findall(r":([a-zA-Z0-9_]+)", path)
    brace_params = re.findall(r"\{([a-zA-Z0-9_]+)\}", path)
    bracket_params = re.findall(r"\[(?:\.\.\.)?([a-zA-Z0-9_]+)\]", path)
    return list(dict.fromkeys(colon_params + brace_params + bracket_params))


def extract_nextjs_app_routes(path: str, content: str) -> list[ParsedRoute]:
    """Detect Next.js 14 App Router endpoints (e.g. app/**/route.ts, src/app/**/route.js).

    Maps filesystem directories to REST URL paths and extracts exported HTTP method handlers.
    Example: `app/api/users/[id]/route.ts` -> `/api/users/:id` or `/api/users/{id}`
    """
    normalized_path = path.replace("\\", "/")
    if not re.search(r"(?:^|/)(?:app|src/app)/(.+)/route\.(?:ts|js|tsx|jsx)$", normalized_path):
        return []

    m = re.search(r"(?:^|/)(?:app|src/app)/(.+)/route\.(?:ts|js|tsx|jsx)$", normalized_path)
    if not m:
        return []

    route_subpath = m.group(1)
    # Convert [param] to :param or {param}
    # Standardize to /path/:param or /path/{param}
    segments = route_subpath.split("/")
    clean_segments = []
    params = []
    for seg in segments:
        if seg.startswith("[...") and seg.endswith("]"):
            p_name = seg[4:-1]
            params.append(p_name)
            clean_segments.append(f"*{p_name}")
        elif seg.startswith("[") and seg.endswith("]"):
            p_name = seg[1:-1]
            params.append(p_name)
            clean_segments.append(f":{p_name}")
        else:
            clean_segments.append(seg)

    url_path = "/" + "/".join(clean_segments)

    routes: list[ParsedRoute] = []
    # Search for exported HTTP handlers: export async function GET(request) {...} or export const POST = ...
    export_fn_regex = re.compile(
        r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*\(",
        re.MULTILINE,
    )
    export_const_regex = re.compile(
        r"export\s+const\s+(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*=",
        re.MULTILINE,
    )

    for match in export_fn_regex.finditer(content):
        method = match.group(1)
        line_num = content[:match.start()].count("\n") + 1
        routes.append(
            ParsedRoute(
                method=method,
                path=url_path,
                handler=method,
                framework="nextjs",
                line=line_num,
                params=params,
            )
        )

    for match in export_const_regex.finditer(content):
        method = match.group(1)
        line_num = content[:match.start()].count("\n") + 1
        # Avoid duplicate if both matched
        if not any(r.method == method for r in routes):
            routes.append(
                ParsedRoute(
                    method=method,
                    path=url_path,
                    handler=method,
                    framework="nextjs",
                    line=line_num,
                    params=params,
                )
            )

    return routes


class JavaSpringParser(BaseParser):
    """Parser for Java Spring Boot controllers (@RestController, @RequestMapping, @GetMapping, etc.)."""

    CONTROLLER_ANNOTATIONS = ("@RestController", "@Controller")
    MAPPING_ANNOTATIONS = {
        "GetMapping": "GET",
        "PostMapping": "POST",
        "PutMapping": "PUT",
        "DeleteMapping": "DELETE",
        "PatchMapping": "PATCH",
        "RequestMapping": "REQUEST",
    }

    def parse(self, content: str, path: str) -> ParseResult:
        result = ParseResult(loc=self._count_loc(content))

        # Check if file has controller annotations
        has_controller = any(ann in content for ann in self.CONTROLLER_ANNOTATIONS)
        if not has_controller and "@RequestMapping" not in content and "@GetMapping" not in content:
            return result

        # Extract base path from class level @RequestMapping
        base_path = ""
        class_rm = re.search(r"@RequestMapping\s*\(\s*(?:value\s*=\s*)?[\"']([^\"']*)[\"']", content)
        if class_rm:
            base_path = class_rm.group(1)
            if not base_path.startswith("/") and base_path:
                base_path = "/" + base_path
            base_path = base_path.rstrip("/")

        # Extract classes
        class_regex = re.compile(r"public\s+class\s+(\w+)", re.MULTILINE)
        class_name = ""
        for m in class_regex.finditer(content):
            class_name = m.group(1)
            line_num = content[:m.start()].count("\n") + 1
            result.classes.append(
                ParsedSymbol(
                    name=class_name,
                    kind="controller" if has_controller else "class",
                    line=line_num,
                    metadata={"framework": "spring", "base_path": base_path},
                )
            )

        # Extract method endpoints
        # e.g. @GetMapping("/users/{id}") public ResponseEntity<User> getUser(@PathVariable Long id)
        method_regex = re.compile(
            r"@([A-Z]\w*Mapping)\s*(?:\(\s*(?:value\s*=\s*|path\s*=\s*)?[\"']([^\"']*)[\"'](?:\s*,\s*method\s*=\s*RequestMethod\.([A-Z]+))?[^)]*\))?\s*"
            r"(?:@\w+(?:\([^)]*\))?\s*)*"
            r"(?:public|protected|private)?\s*(?:static\s+)?[\w\<\>\[\],\s]+\s+(\w+)\s*\(",
            re.MULTILINE,
        )

        for match in method_regex.finditer(content):
            mapping_type = match.group(1)
            sub_path = match.group(2) or ""
            req_method_attr = match.group(3)
            handler_name = match.group(4)
            line_num = content[:match.start()].count("\n") + 1

            if mapping_type not in self.MAPPING_ANNOTATIONS:
                continue

            method = self.MAPPING_ANNOTATIONS[mapping_type]
            if method == "REQUEST":
                method = req_method_attr if req_method_attr else "GET"

            if sub_path and not sub_path.startswith("/"):
                sub_path = "/" + sub_path

            full_path = f"{base_path}{sub_path}" if (base_path or sub_path) else "/"
            if not full_path.startswith("/"):
                full_path = "/" + full_path

            params = extract_route_params(full_path)

            result.routes.append(
                ParsedRoute(
                    method=method,
                    path=full_path,
                    handler=handler_name,
                    framework="spring",
                    line=line_num,
                    params=params,
                )
            )
            result.functions.append(
                ParsedSymbol(
                    name=handler_name,
                    kind="controller_action",
                    line=line_num,
                    parent=class_name or None,
                    metadata={"framework": "spring", "route_path": full_path, "http_method": method},
                )
            )

        result.symbols = result.classes + result.functions
        return result
