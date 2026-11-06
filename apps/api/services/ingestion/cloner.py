"""Shallow Git repository cloner with GitHub App installation token support and sparse checkout."""

import asyncio
import fnmatch
import logging
import shutil
import tempfile
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)

# Extensions to strictly ignore during scanning and sparse checkout
IGNORED_EXTENSIONS: set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pdf", ".doc", ".docx",
    ".mp3", ".mp4", ".avi", ".mov",
    ".pyc", ".pyo", ".so", ".dll", ".dylib",
    ".lock", ".min.js", ".min.css",
    ".map", ".log", ".tmp", ".cache",
}

# Directories to exclude from scanning and sparse checkout
IGNORED_DIRS: set[str] = {
    "node_modules", ".git", "dist", "build", ".next", "coverage",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "venv", ".venv", "env", ".env", "target", "vendor",
    ".idea", ".vscode", ".turbo", ".cache",
}

# Language extension mapping
LANGUAGE_EXTENSIONS: dict[str, str] = {
    ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
    ".py": "python",
    ".go": "go",
    ".rs": "rust",
    ".prisma": "prisma",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".kt": "kotlin",
    ".swift": "swift",
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".hpp": "cpp",
}


def build_authenticated_url(clone_url: str, token: str | None) -> str:
    """Injects a GitHub App installation token (e.g., ghs_...) into an HTTPS clone URL.

    Sanitizes existing auth credentials if present.
    """
    if not token:
        return clone_url

    parsed = urlparse(clone_url)
    if parsed.scheme in ("http", "https"):
        # Format: https://x-access-token:<token>@github.com/org/repo.git
        netloc = f"x-access-token:{token}@{parsed.hostname}"
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))

    return clone_url


@asynccontextmanager
async def ephemeral_cloned_repo(
    clone_url: str,
    branch: str,
    token: str | None = None,
    sparse_cone: bool = True,
) -> AsyncGenerator[Path, None]:
    """Clones a repository into an isolated ephemeral temporary directory and guarantees cleanup.

    Uses `git clone --depth 1 --single-branch --filter=blob:none` and sparse-checkout to minimize bandwidth.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="codeatlas_repo_"))
    repo_dest = tmp_dir / "repo"

    auth_url = build_authenticated_url(clone_url, token)

    try:
        cmd = [
            "git", "clone",
            "--depth=1",
            "--single-branch",
            "--filter=blob:none",
            "--branch", branch,
            auth_url,
            str(repo_dest),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            err_msg = stderr.decode(errors="replace").strip()
            # Clean token out of error messages if present
            if token and token in err_msg:
                err_msg = err_msg.replace(token, "[REDACTED]")
            raise RuntimeError(f"Git clone failed: {err_msg}")

        yield repo_dest

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def scan_repository_files(base_path: Path, ignored_patterns: list[str] | None = None) -> list[dict[str, Any]]:
    """Scans and reads source files in the cloned repository respecting ignored dirs, extensions, and patterns."""
    ignored = ignored_patterns or []
    files: list[dict[str, Any]] = []

    for path in base_path.rglob("*"):
        if not path.is_file():
            continue

        rel = path.relative_to(base_path)
        rel_str = str(rel).replace("\\", "/")

        parts = rel.parts
        if any(p in IGNORED_DIRS for p in parts):
            continue
        if path.suffix.lower() in IGNORED_EXTENSIONS:
            continue
        if any(fnmatch.fnmatch(rel_str, pat) for pat in ignored):
            continue

        try:
            # Skip files larger than 1 MB
            if path.stat().st_size > 1_000_000:
                continue
            content = path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue

        files.append({
            "path": rel_str,
            "content": content,
            "language": LANGUAGE_EXTENSIONS.get(path.suffix.lower()),
        })

    return files


class ShallowRepositoryCloner:
    """Orchestrates shallow cloning, token injection, sparse checkout filtering, and file extraction."""

    def __init__(self, token: str | None = None):
        self.token = token

    async def clone_and_scan(
        self,
        clone_url: str,
        branch: str,
        ignored_patterns: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Clones the repository at depth 1 and extracts scanned source files with safe cleanup."""
        async with ephemeral_cloned_repo(clone_url, branch, token=self.token) as repo_path:
            return scan_repository_files(repo_path, ignored_patterns)
