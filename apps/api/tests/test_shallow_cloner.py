import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from services.ingestion.cloner import (
    build_authenticated_url,
    ephemeral_cloned_repo,
    scan_repository_files,
)


class TestBuildAuthenticatedUrl:
    def test_injects_github_app_installation_token(self):
        token = "ghs_test1234567890abcdef"
        raw_url = "https://github.com/org/repo.git"
        auth_url = build_authenticated_url(raw_url, token)
        assert auth_url == f"https://x-access-token:{token}@github.com/org/repo.git"

    def test_preserves_url_without_token(self):
        raw_url = "https://github.com/org/repo.git"
        assert build_authenticated_url(raw_url, None) == raw_url

    def test_handles_port_in_url(self):
        token = "ghs_token"
        raw_url = "https://git.internal.corp:8443/team/project.git"
        auth_url = build_authenticated_url(raw_url, token)
        assert auth_url == f"https://x-access-token:{token}@git.internal.corp:8443/team/project.git"


class TestEphemeralClonedRepo:
    @pytest.mark.asyncio
    async def test_ephemeral_clone_cleans_up_on_success(self):
        created_dirs = []

        # Mock git clone subprocess success
        async def mock_communicate():
            return b"", b""

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = mock_communicate

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            async with ephemeral_cloned_repo("https://github.com/org/repo.git", "main") as repo_path:
                assert repo_path.name == "repo"
                parent_tmp = repo_path.parent
                created_dirs.append(parent_tmp)
                assert parent_tmp.exists()

        # Check cleanup after context exit
        for d in created_dirs:
            assert not d.exists()

    @pytest.mark.asyncio
    async def test_ephemeral_clone_cleans_up_on_exception(self):
        created_dirs = []

        async def mock_communicate():
            return b"", b""

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = mock_communicate

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_proc),
            pytest.raises(ValueError, match="Unhandled parsing failure"),
        ):
            async with ephemeral_cloned_repo("https://github.com/org/repo.git", "main") as repo_path:
                created_dirs.append(repo_path.parent)
                raise ValueError("Unhandled parsing failure")

        for d in created_dirs:
            assert not d.exists()

    @pytest.mark.asyncio
    async def test_redacts_token_on_clone_failure(self):
        token = "ghs_secret_app_token"
        async def mock_communicate():
            return b"", f"fatal: Authentication failed for 'https://x-access-token:{token}@github.com/org/repo.git'".encode()

        mock_proc = AsyncMock()
        mock_proc.returncode = 128
        mock_proc.communicate = mock_communicate

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with pytest.raises(RuntimeError) as exc_info:
                async with ephemeral_cloned_repo("https://github.com/org/repo.git", "main", token=token):
                    pass

            assert token not in str(exc_info.value)
            assert "[REDACTED]" in str(exc_info.value)


class TestScanRepositoryFiles:
    def test_scans_source_files_and_ignores_binaries_and_build_dirs(self):
        tmp_dir = Path(tempfile.mkdtemp(prefix="test_scan_"))
        try:
            # Create valid source files
            (tmp_dir / "src").mkdir()
            (tmp_dir / "src" / "index.ts").write_text("console.log('hello');", encoding="utf-8")
            (tmp_dir / "src" / "App.py").write_text("print('python')", encoding="utf-8")

            # Create ignored directories and files
            (tmp_dir / "node_modules").mkdir()
            (tmp_dir / "node_modules" / "pkg.js").write_text("// vendor", encoding="utf-8")
            (tmp_dir / "dist").mkdir()
            (tmp_dir / "dist" / "bundle.js").write_text("// dist", encoding="utf-8")
            (tmp_dir / "assets").mkdir()
            (tmp_dir / "assets" / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            (tmp_dir / "assets" / "video.mp4").write_bytes(b"video data")
            (tmp_dir / "package-lock.json").write_text("{}", encoding="utf-8")

            files = scan_repository_files(tmp_dir, ignored_patterns=["package-lock.json"])

            paths = [f["path"] for f in files]
            assert "src/index.ts" in paths
            assert "src/App.py" in paths

            # Verify ignored paths are absent
            assert not any("node_modules" in p for p in paths)
            assert not any("dist" in p for p in paths)
            assert not any("logo.png" in p for p in paths)
            assert not any("video.mp4" in p for p in paths)
            assert "package-lock.json" not in paths

            ts_file = next(f for f in files if f["path"] == "src/index.ts")
            assert ts_file["language"] == "typescript"
            assert ts_file["content"] == "console.log('hello');"

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
